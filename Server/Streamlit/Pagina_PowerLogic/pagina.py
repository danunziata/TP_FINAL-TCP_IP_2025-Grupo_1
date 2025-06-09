import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Configuración de la aplicación
st.set_page_config(
    page_title="PowerLogic 4000 Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simulación de datos si el archivo no existe
DATA_FILE = "powerlogic_simulated_data.csv"

def generate_simulated_data():
    """Genera datos simulados si no existe el archivo CSV"""
    try:
        st.info("Generando datos simulados... Esto puede tomar unos segundos")
        start_date = datetime(2025, 5, 20)
        end_date = start_date + timedelta(days=14)
        interval = timedelta(minutes=15)
        date_range = pd.date_range(start=start_date, end=end_date, freq=interval)
        num_records = len(date_range)
        phases = ['R', 'S', 'T']
        
        # Función para patrones diarios
        def daily_pattern(base_value, peak_multiplier, noise_factor=0.1, hour_peak=14):
            hour = date_range.hour + date_range.minute/60
            pattern = base_value * (1 + (peak_multiplier - 1) * np.exp(-(hour - hour_peak)**2/8))
            noise = np.random.normal(1, noise_factor, num_records)
            return pattern * noise
        
        # Crear datos base
        active_power = daily_pattern(50, 2.5)
        reactive_power = daily_pattern(20, 2.0)
        apparent_power = np.sqrt(active_power**2 + reactive_power**2)
        
        records = []
        for i, dt in enumerate(date_range):
            for phase in phases:
                phase_factor = np.random.uniform(0.95, 1.05)
                voltage = 220 * (1 + np.random.normal(0, 0.02)) * phase_factor
                current = (apparent_power[i] * 1000 / 3) / voltage * phase_factor
                power_factor = np.clip(active_power[i] / (apparent_power[i]/3) * phase_factor, 0.8, 1.0)
                
                records.append({
                    'timestamp': dt,
                    'phase': phase,
                    'Active_Power': active_power[i] / 3,
                    'Reactive_Power': reactive_power[i] / 3,
                    'Apparent_Power': apparent_power[i] / 3,
                    'Voltage': voltage,
                    'Current': current,
                    'Power_Factor': power_factor
                })
        
        # Crear DataFrame y calcular demanda
        df = pd.DataFrame(records)
        df['Active_Power_Demand'] = df.groupby('phase')['Active_Power'].transform(
            lambda x: x.rolling(4, min_periods=1).mean()  # Demanda como promedio de 1 hora
        )
        
        # Guardar el archivo CSV
        df.to_csv(DATA_FILE, index=False)
        st.success("Datos simulados generados exitosamente!")
        return df
        
    except Exception as e:
        st.error(f"Error generando datos simulados: {str(e)}")
        return None

@st.cache_data
def load_data():
    """Carga datos desde el archivo CSV simulado"""
    try:
        # Si el archivo no existe, generar datos
        if not os.path.exists(DATA_FILE):
            df = generate_simulated_data()
            if df is None:
                return None
        else:
            # Intentar cargar el archivo existente
            try:
                df = pd.read_csv(DATA_FILE, parse_dates=['timestamp'])
            except (ValueError, KeyError) as e:
                # Si hay error con el archivo existente, regenerar
                st.warning("Archivo CSV corrupto o con formato incorrecto. Regenerando datos...")
                if os.path.exists(DATA_FILE):
                    os.remove(DATA_FILE)
                df = generate_simulated_data()
                if df is None:
                    return None
        
        # Verificar que el DataFrame tenga las columnas necesarias
        required_columns = ['timestamp', 'phase', 'Active_Power', 'Reactive_Power', 
                          'Apparent_Power', 'Voltage', 'Current', 'Power_Factor']
        
        if not all(col in df.columns for col in required_columns):
            st.warning("Columnas faltantes en el archivo. Regenerando datos...")
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            df = generate_simulated_data()
            if df is None:
                return None
        
        # Renombrar columnas a español
        df = df.rename(columns={
            'Active_Power': 'Potencia Activa (kW)',
            'Reactive_Power': 'Potencia Reactiva (kVAR)',
            'Apparent_Power': 'Potencia Aparente (kVA)',
            'Voltage': 'Tensión (V)',
            'Current': 'Corriente (A)',
            'Power_Factor': 'Factor de Potencia',
            'Active_Power_Demand': 'Demanda Activa (kW)'
        })
        
        return df
        
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
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
    
    # Selector de fechas
    min_date = df['timestamp'].min().date()
    max_date = df['timestamp'].max().date()
    
    date_range = st.date_input(
        "Seleccionar rango de fechas:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Selector de fases
    selected_phases = st.multiselect(
        "Fases a mostrar:",
        options=['R', 'S', 'T'],
        default=['R', 'S', 'T']
    )
    
    st.divider()
    st.info("💡 Seleccione un rango de fechas y presione 'Actualizar Datos'")
    if st.button("🔄 Actualizar Datos", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("🗑️ Regenerar Datos", use_container_width=True):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.cache_data.clear()
        st.rerun()

# Filtrar datos por fecha y fase
if len(date_range) == 2:
    start_date, end_date = date_range
    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date) + timedelta(days=1)
    
    filtered_df = df[
        (df['timestamp'] >= start_dt) & 
        (df['timestamp'] <= end_dt) &
        (df['phase'].isin(selected_phases))
    ]
    
    if not filtered_df.empty:
        # Crear versión diaria para promedios
        daily_df = filtered_df.copy()
        daily_df['date'] = daily_df['timestamp'].dt.date
        daily_df = daily_df.groupby(['date', 'phase']).mean(numeric_only=True).reset_index()
        
        # Sección de gráficos
        tab1, tab2, tab3 = st.tabs(["📈 Potencia", "⚡ Energía", "📥 Datos"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(create_phase_chart(
                    filtered_df,
                    "Potencia Activa",
                    "Potencia Activa (kW)"
                ), use_container_width=True)
                
                st.plotly_chart(create_phase_chart(
                    filtered_df,
                    "Potencia Reactiva",
                    "Potencia Reactiva (kVAR)"
                ), use_container_width=True)
                
            with col2:
                st.plotly_chart(create_phase_chart(
                    filtered_df,
                    "Potencia Aparente",
                    "Potencia Aparente (kVA)"
                ), use_container_width=True)
                
                st.plotly_chart(create_phase_chart(
                    filtered_df,
                    "Demanda de Potencia Activa",
                    "Demanda Activa (kW)"
                ), use_container_width=True)
        
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(create_phase_chart(
                    filtered_df,
                    "Tensión por Fase",
                    "Tensión (V)"
                ), use_container_width=True)
                
            with col2:
                st.plotly_chart(create_phase_chart(
                    filtered_df,
                    "Corriente por Fase",
                    "Corriente (A)"
                ), use_container_width=True)
                
            st.plotly_chart(create_phase_chart(
                filtered_df,
                "Factor de Potencia",
                "Factor de Potencia"
            ), use_container_width=True)
        
        with tab3:
            st.subheader("Datos Crudos")
            st.dataframe(filtered_df, height=400)
            
            # Exportación de datos
            st.divider()
            st.subheader("Exportar Datos")
            
            col_exp1, col_exp2 = st.columns(2)
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            
            with col_exp1:
                st.download_button(
                    label="📥 Descargar CSV",
                    data=csv,
                    file_name=f"power_data_{start_date}_{end_date}.csv",
                    mime='text/csv',
                    use_container_width=True
                )
                
            with col_exp2:
                # Para Excel necesitamos usar BytesIO
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
            st.info(f"Datos del {start_date} al {end_date} ({len(selected_phases)} fases)")
    else:
        st.warning("⚠️ No se encontraron datos para el rango seleccionado")
else:
    st.error("Por favor seleccione un rango de fechas válido")

# Footer
st.divider()
st.caption(f"© {datetime.today().year} Schneider Electric - Power Monitoring System | v1.0")