
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import time
from tzlocal import get_localzone

# Configuración de InfluxDB desde variables de entorno
INFLUX_URL = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
INFLUX_TOKEN = os.getenv('INFLUXDB_TOKEN', 'token_telegraf')
INFLUX_ORG = os.getenv('INFLUXDB_ORG', 'power_logic')
INFLUX_BUCKET = os.getenv('INFLUXDB_BUCKET', 'mensualx6')

# Configuración de la aplicación
st.set_page_config(
    page_title="PowerLogic 4000 Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Mensaje informativo sobre la frecuencia de actualización
st.info("⚡ Los datos se actualizan cada 15 minutos. No es posible ver datos en tiempo real.")

def get_influx_client():
    """Crea y retorna un cliente de InfluxDB"""
    return InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    )

def load_data():
    """Carga datos desde InfluxDB"""
    try:
        client = get_influx_client()
        query_api = client.query_api()
        
        # Consulta Flux para obtener los datos
        query = f'''
        from(bucket: "{INFLUX_BUCKET}")
            |> range(start: -30d)
            |> filter(fn: (r) => r["_measurement"] == "modbus")
            |> filter(fn: (r) => r["host"] == "telegraf")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        
        # Ejecutar consulta
        result = query_api.query_data_frame(query)
        
        if result.empty:
            st.error("❌ No se encontraron datos en la base de datos InfluxDB. Por favor, verifica la conexión y los datos.")
            return None
        
        # Renombrar columnas y preparar el DataFrame
        df = result.rename(columns={
            '_time': 'timestamp',
            'current_l1': 'Corriente L1 (A)',
            'current_l2': 'Corriente L2 (A)',
            'current_l3': 'Corriente L3 (A)',
            'voltaje': 'Voltaje L1N (V)',
            'voltaje_l2n': 'Voltaje L2N (V)',
            'voltaje_l3n': 'Voltaje L3N (V)',
            'active_power': 'Potencia Activa (W)'
        })
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['timestamp'] = df['timestamp'].dt.tz_localize(None)

        # Obtener la zona horaria local
        local_tz = get_localzone()

        # Si tus timestamps están en UTC, conviértelos a la zona local
        if df['timestamp'].dt.tz is None:
            # Si no tienen zona, primero localiza como UTC
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        df['timestamp'] = df['timestamp'].dt.tz_convert(local_tz)
        df['timestamp'] = df['timestamp'].dt.tz_localize(None)  # Si quieres quitar la info de zona y trabajar como naive local

        return df
        
    except Exception as e:
        st.error(f"❌ Error al conectar con InfluxDB: {str(e)}")
        return None

def create_phase_chart(data, title, yaxis_title):
    """Crea gráfico con datos por fase"""
    fig = go.Figure()
    colors = {'R': '#FF4B4B', 'S': '#0068C9', 'T': '#00C39F'}
    
    for phase in ['R', 'S', 'T']:
        phase_data = data[data['phase'] == phase]
        if not phase_data.empty:
            fig.add_trace(go.Scatter(
                x=phase_data['timestamp'],
                y=phase_data[yaxis_title],
                mode='lines',
                name=f'Fase {phase}',
                line=dict(width=2, color=colors[phase]),
                hovertemplate=f'Fase {phase}<br>%{{x|%d-%m-%Y %H:%M}}<br>%{{y:.2f}}<extra></extra>'
            ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Fecha y Hora',
        yaxis_title=yaxis_title,
        template='plotly_white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    return fig

# Diseño de la interfaz
st.title("📊 Sistema de Monitoreo PowerLogic 4000")
st.markdown("**Visualización de parámetros eléctricos** | Schneider Electric™")
st.divider()

# Cargar datos
df = load_data()

if df is None or df.empty:
    st.error("❌ No se pudieron cargar los datos. Por favor, verifica la configuración.")
    st.stop()

# Sidebar para controles
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Selector de fechas: por defecto, mostrar solo el día de hoy
    hoy = datetime.now().date()
    min_date = df['timestamp'].min().date()
    max_date = df['timestamp'].max().date()
    
    date_range = st.date_input(
        "Seleccionar rango de fechas:",
        value=(hoy, hoy),
        min_value=min_date,
        max_value=max_date
    )
    
    # Selector de fases (ahora por columna)
    phase_options = {
        'L1': ['Corriente L1 (A)', 'Voltaje L1N (V)'],
        'L2': ['Corriente L2 (A)', 'Voltaje L2N (V)'],
        'L3': ['Corriente L3 (A)', 'Voltaje L3N (V)']
    }
    selected_phases = st.multiselect(
        "Fases a mostrar:",
        options=['L1', 'L2', 'L3'],
        default=['L1', 'L2', 'L3']
    )
    
    st.divider()
    st.info("💡 Seleccione un rango de fechas y presione 'Actualizar Datos'")
    if st.button("🔄 Actualizar Datos", type="primary", use_container_width=True):
        st.rerun()

# Obtener el rango de fechas seleccionado
if len(date_range) == 2:
    start_date, end_date = date_range
    hoy = datetime.now().date()
    if start_date == end_date == hoy:
        # Solo mostrar desde las 00:00 hasta la última medición de hoy
        start_dt = pd.Timestamp(hoy)
        ultimo_dato_hoy = df[df['timestamp'].dt.date == hoy]['timestamp'].max()
        if pd.isna(ultimo_dato_hoy):
            filtered_df = df.iloc[0:0]
        else:
            filtered_df = df[(df['timestamp'] >= start_dt) & (df['timestamp'] <= ultimo_dato_hoy)]
    else:
        # Si el usuario seleccionó otro rango, usar ese rango completo
        start_dt = pd.Timestamp(start_date)
        end_dt = pd.Timestamp(end_date) + timedelta(days=1)
        filtered_df = df[(df['timestamp'] >= start_dt) & (df['timestamp'] < end_dt)]

if not filtered_df.empty:
    # Gráficos por fase seleccionada
    st.subheader("Gráficos por Fase")
    for phase in selected_phases:
        col_corr, col_volt = phase_options[phase]
        st.markdown(f"### Fase {phase}")
        # Gráfica de Corriente con zoom
        fig_corr = px.line(filtered_df, x='timestamp', y=col_corr, title=f"{col_corr} - {phase}")
        st.plotly_chart(fig_corr, use_container_width=True)
        # Gráfica de Voltaje con zoom
        fig_volt = px.line(filtered_df, x='timestamp', y=col_volt, title=f"{col_volt} - {phase}")
        st.plotly_chart(fig_volt, use_container_width=True)
    
    st.subheader("Datos Crudos")
    st.dataframe(filtered_df, height=400)
    
    # Exportación de datos
    st.divider()
    st.subheader("Exportar Datos")
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name=f"power_data_{start_date}_{end_date}.csv",
        mime='text/csv',
        use_container_width=True
    )
    from io import BytesIO
    excel_buffer = BytesIO()
    filtered_df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    st.download_button(
        label="💾 Descargar Excel",
        data=excel_buffer.getvalue(),
        file_name=f"power_data_{start_date}_{end_date}.xlsx",
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        use_container_width=True
    )
    st.metric("Registros encontrados", len(filtered_df))
    st.info(f"Datos del {start_date} al {end_date} (fases: {', '.join(selected_phases)})")
else:
    st.warning("⚠️ No se encontraron datos para el rango seleccionado")

# Footer
st.divider()
st.caption(f"© {datetime.today().year} Schneider Electric - Power Monitoring System | v1.0")