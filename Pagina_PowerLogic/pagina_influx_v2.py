import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
from influxdb_client import InfluxDBClient

# Configuración de InfluxDB desde variables de entorno
#INFLUX_URL    = os.getenv('INFLUXDB_URL',    'http://192.168.5.131:9000')
INFLUX_URL    = os.getenv('INFLUXDB_URL',    '127.0.0.1:8086')
INFLUX_TOKEN  = os.getenv('INFLUXDB_TOKEN',  'token_telegraf')
INFLUX_ORG    = os.getenv('INFLUXDB_ORG',    'power_logic')
INFLUX_BUCKET = os.getenv('INFLUXDB_BUCKET', 'mensualx6')

# Configuración de la aplicación
st.set_page_config(
    page_title="PowerLogic 4000 Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session state
if 'data_version' not in st.session_state:
    st.session_state.data_version = 0

# Cliente de InfluxDB
def get_influx_client():
    return InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    )

@st.cache_data
def load_data(_file_mod=None, data_version=0):
    """Carga datos reales desde InfluxDB"""
    client    = get_influx_client()
    query_api = client.query_api()
    flux = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -30d)
      |> filter(fn: (r) => r["_measurement"] == "modbus")
      |> filter(fn: (r) => r["host"] == "telegraf")
      |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
    '''
    result = query_api.query_data_frame(flux)
    if result.empty:
        return None
    
    # Mapeo de campos de InfluxDB a nombres legibles
    field_mapping = {
        '_time': 'timestamp',
        'corriente_a': 'Corriente A (A)',
        'corriente_b': 'Corriente B (A)',
        'corriente_c': 'Corriente C (A)',
        'voltaje_a_n': 'Voltaje A-N (V)',
        'voltaje_b_n': 'Voltaje B-N (V)',
        'voltaje_c_n': 'Voltaje C-N (V)',
        'potencia_activa_a': 'Potencia Activa A (W)',
        'potencia_activa_b': 'Potencia Activa B (W)',
        'potencia_activa_c': 'Potencia Activa C (W)',
        'potencia_activa_total': 'Potencia Activa Total (W)',
        'potencia_reactiva_a': 'Potencia Reactiva A (VAR)',
        'potencia_reactiva_b': 'Potencia Reactiva B (VAR)',
        'potencia_reactiva_c': 'Potencia Reactiva C (VAR)',
        'potencia_reactiva_total': 'Potencia Reactiva Total (VAR)',
        'potencia_aparente_a': 'Potencia Aparente A (VA)',
        'potencia_aparente_b': 'Potencia Aparente B (VA)',
        'potencia_aparente_c': 'Potencia Aparente C (VA)',
        'potencia_aparente_total': 'Potencia Aparente Total (VA)',
        'demanda_potencia_real_3_fases_running': 'Demanda Potencia Real (W)'
    }
    
    df = result.rename(columns=field_mapping)
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)

    # Convertir escala si necesario (dividir entre 10 para tensiones y corrientes)
    scale_columns = [
        'Voltaje A-N (V)', 'Voltaje B-N (V)', 'Voltaje C-N (V)',
        'Corriente A (A)', 'Corriente B (A)', 'Corriente C (A)'
    ]
    
    for col in scale_columns:
        if col in df.columns:
            df[col] = df[col] / 10.0

    return df

# Función para detectar columnas automáticamente
def detect_columns(df):
    """Detecta las columnas disponibles en el DataFrame"""
    if df is None:
        return {}, {}
    
    columns = df.columns.tolist()
    
    # Detectar columnas por patrones
    detected = {
        'voltage': [col for col in columns if any(pattern in col.lower() for pattern in ['voltaje', 'voltage', 'volt'])],
        'current': [col for col in columns if any(pattern in col.lower() for pattern in ['corriente', 'current', 'amp'])],
        'active_power': [col for col in columns if any(pattern in col.lower() for pattern in ['potencia_activa', 'active_power', 'potencia activa'])],
        'reactive_power': [col for col in columns if any(pattern in col.lower() for pattern in ['potencia_reactiva', 'reactive_power', 'potencia reactiva'])],
        'apparent_power': [col for col in columns if any(pattern in col.lower() for pattern in ['potencia_aparente', 'apparent_power', 'potencia aparente'])],
        'demand': [col for col in columns if any(pattern in col.lower() for pattern in ['demanda', 'demand'])]
    }
    
    # Crear mapeo de nombres amigables
    friendly_names = {}
    for col in columns:
        if col != 'timestamp':
            friendly_names[col] = col  # Usar el nombre original como amigable
    
    return detected, friendly_names

# Función para crear gráfico de múltiples series - CORREGIDA
def create_multi_series_chart(data, title, y_columns, y_title, colors=None):
    fig = go.Figure()
    
    if colors is None:
        colors = ['#FF4B4B', '#0068C9', '#00C39F', '#FF8C00', '#9467BD', '#8C564B', '#E377C2']
    
    series_added = 0
    for i, col in enumerate(y_columns):
        if col in data.columns:
            # Verificar que la columna tenga datos válidos
            col_data = data[col].dropna()
            if len(col_data) > 0:
                color = colors[i % len(colors)]
                fig.add_trace(go.Scatter(
                    x=data['timestamp'], 
                    y=data[col],
                    mode='lines', 
                    name=col,
                    line=dict(width=2, color=color),
                    hovertemplate=f'{col}<br>%{{x|%d-%m-%Y %H:%M}}<br>%{{y:.2f}}<extra></extra>'
                ))
                series_added += 1
    
    # Solo actualizar layout si se agregaron series
    if series_added > 0:
        fig.update_layout(
            title=title,
            xaxis_title='Fecha y Hora',
            yaxis_title=y_title,
            template='plotly_white', 
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=500
        )
    
    return fig, series_added

# Función para crear dashboard de métricas - CORREGIDA
def create_metrics_dashboard(data, detected_columns):
    col1, col2, col3, col4 = st.columns(4)
    
    # Métricas de voltaje
    if detected_columns['voltage']:
        voltage_data = data[detected_columns['voltage']].select_dtypes(include=[np.number])
        if not voltage_data.empty:
            avg_voltage = voltage_data.mean().mean()
            col1.metric("Voltaje Promedio", f"{avg_voltage:.1f} V")
    
    # Métricas de corriente
    if detected_columns['current']:
        current_data = data[detected_columns['current']].select_dtypes(include=[np.number])
        if not current_data.empty:
            avg_current = current_data.mean().mean()
            col2.metric("Corriente Promedio", f"{avg_current:.2f} A")
    
    # Métricas de potencia activa
    if detected_columns['active_power']:
        power_data = data[detected_columns['active_power']].select_dtypes(include=[np.number])
        if not power_data.empty:
            avg_power = power_data.mean().mean()
            max_power = power_data.max().max()
            col3.metric("Potencia Activa Prom", f"{avg_power:.0f} W")
            col4.metric("Potencia Activa Máx", f"{max_power:.0f} W")
    
    # Nueva fila para otras métricas
    col5, col6, col7, col8 = st.columns(4)
    
    # Métricas de demanda
    if detected_columns['demand']:
        demand_data = data[detected_columns['demand']].select_dtypes(include=[np.number])
        if not demand_data.empty:
            max_demand = demand_data.max().max()
            col5.metric("Demanda Máxima", f"{max_demand:.0f} W")
    
    # Métricas de potencia reactiva
    if detected_columns['reactive_power']:
        reactive_data = data[detected_columns['reactive_power']].select_dtypes(include=[np.number])
        if not reactive_data.empty:
            avg_reactive = reactive_data.mean().mean()
            col6.metric("Pot Reactiva Prom", f"{avg_reactive:.0f} VAR")
    
    # Métricas de potencia aparente
    if detected_columns['apparent_power']:
        apparent_data = data[detected_columns['apparent_power']].select_dtypes(include=[np.number])
        if not apparent_data.empty:
            avg_apparent = apparent_data.mean().mean()
            col7.metric("Pot Aparente Prom", f"{avg_apparent:.0f} VA")
    
    # Métricas de registros
    col8.metric("Registros", f"{len(data)}")

# Interfaz principal
st.title("📊 Sistema de Monitoreo PowerLogic 4000")
st.markdown("**Visualización completa de parámetros eléctricos** | Schneider Electric™")
st.divider()

# Cargar datos con indicador de actualización
with st.spinner('Cargando datos desde InfluxDB...'):
    df = load_data(None, st.session_state.data_version)

if df is None or df.empty:
    st.error("❌ No se pudieron cargar los datos de InfluxDB.")
    st.info("Verifica la conexión a InfluxDB y que el bucket 'mensualx6' contenga datos.")
    
    # Información de troubleshooting
    with st.expander("🔧 Información de Troubleshooting"):
        st.code(f"""
        URL de InfluxDB: {INFLUX_URL}
        Token: {INFLUX_TOKEN[:10]}...
        Organización: {INFLUX_ORG}
        Bucket: {INFLUX_BUCKET}
        """)
        
        if st.button("🔄 Reintentar conexión"):
            st.rerun()
    
    st.stop()

# Detectar columnas automáticamente
detected_columns, friendly_names = detect_columns(df)

# Actualizar timestamp de última carga
st.session_state.last_update = datetime.now()

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Botón de refrescar datos con indicador de estado
    if st.button("🔄 Actualizar Datos", use_container_width=True, help="Recargar datos desde InfluxDB"):
        with st.spinner('Actualizando datos desde InfluxDB...'):
            st.session_state.data_version += 1
            load_data.clear()
            st.success("¡Datos actualizados exitosamente!")
            st.rerun()
    
    # Mostrar última actualización
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()
    
    st.caption(f"🕒 Última actualización: {st.session_state.last_update.strftime('%H:%M:%S')}")

    st.divider()
    
    # Información de datos disponibles
    min_d = df['timestamp'].min().date()
    max_d = df['timestamp'].max().date()
    st.info(f"📅 Datos del {min_d} al {max_d}")
    st.info(f"📊 {len(df)} registros totales")
    
    # Selector de rango de fechas
    date_range = st.date_input(
        "Seleccionar rango de fechas:", 
        value=(min_d, max_d), 
        min_value=min_d, 
        max_value=max_d
    )
    
    # Selectores de métricas a mostrar
    st.subheader("Métricas a visualizar:")
    
    show_voltages = st.checkbox("Voltajes", value=True)
    show_currents = st.checkbox("Corrientes", value=True)
    show_powers = st.checkbox("Potencias", value=True)
    show_demand = st.checkbox("Demanda", value=True)
    
    # DEBUG: Mostrar columnas detectadas
    if st.checkbox("🔧 Mostrar Debug de Columnas"):
        st.subheader("🔍 Columnas detectadas:")
        for category, columns in detected_columns.items():
            if columns:
                st.write(f"**{category.title()}:**")
                for col in columns:
                    st.caption(f"• {col}")
        
        st.subheader("📋 Todas las columnas:")
        for col in df.columns:
            st.caption(f"• {col}")

# Filtrado por fechas
if len(date_range) == 2:
    start, end = date_range
    mask = (
        (df['timestamp'] >= pd.Timestamp(start)) & 
        (df['timestamp'] < pd.Timestamp(end) + timedelta(days=1))
    )
    filtered_df = df[mask]
    
    if filtered_df.empty:
        st.warning("⚠️ No hay datos para el rango de fechas seleccionado")
    else:
        # Dashboard de métricas principales
        st.subheader("📈 Resumen de Métricas")
        create_metrics_dashboard(filtered_df, detected_columns)
        st.divider()
        
        # Gráficos de voltajes - CORREGIDO
        if show_voltages:
            st.subheader("⚡ Voltajes")
            if detected_columns['voltage']:
                voltage_chart, series_count = create_multi_series_chart(
                    filtered_df, 
                    "Voltajes por Fase", 
                    detected_columns['voltage'], 
                    "Voltaje (V)",
                    colors=['#FF4B4B', '#0068C9', '#00C39F']
                )
                if series_count > 0:
                    st.plotly_chart(voltage_chart, use_container_width=True)
                else:
                    st.info("No hay datos de voltaje válidos para mostrar")
            else:
                st.info("No se detectaron columnas de voltaje")
        
        # Gráficos de corrientes - CORREGIDO
        if show_currents:
            st.subheader("🔌 Corrientes")
            if detected_columns['current']:
                current_chart, series_count = create_multi_series_chart(
                    filtered_df, 
                    "Corrientes por Fase", 
                    detected_columns['current'], 
                    "Corriente (A)",
                    colors=['#FF4B4B', '#0068C9', '#00C39F']
                )
                if series_count > 0:
                    st.plotly_chart(current_chart, use_container_width=True)
                else:
                    st.info("No hay datos de corriente válidos para mostrar")
            else:
                st.info("No se detectaron columnas de corriente")
        
        # Gráficos de potencia - CORREGIDO
        if show_powers:
            # Potencia Activa
            if detected_columns['active_power']:
                st.subheader("🔋 Potencia Activa")
                active_chart, series_count = create_multi_series_chart(
                    filtered_df, 
                    "Potencia Activa por Fase y Total", 
                    detected_columns['active_power'], 
                    "Potencia (W)",
                    colors=['#FF4B4B', '#0068C9', '#00C39F', '#FF8C00']
                )
                if series_count > 0:
                    st.plotly_chart(active_chart, use_container_width=True)
                else:
                    st.info("No hay datos de potencia activa válidos para mostrar")
            
            # Potencia Reactiva
            if detected_columns['reactive_power']:
                st.subheader("🔄 Potencia Reactiva")
                reactive_chart, series_count = create_multi_series_chart(
                    filtered_df, 
                    "Potencia Reactiva por Fase y Total", 
                    detected_columns['reactive_power'], 
                    "Potencia (VAR)",
                    colors=['#9467BD', '#8C564B', '#E377C2', '#7F7F7F']
                )
                if series_count > 0:
                    st.plotly_chart(reactive_chart, use_container_width=True)
                else:
                    st.info("No hay datos de potencia reactiva válidos para mostrar")
            
            # Potencia Aparente
            if detected_columns['apparent_power']:
                st.subheader("🔌 Potencia Aparente")
                apparent_chart, series_count = create_multi_series_chart(
                    filtered_df, 
                    "Potencia Aparente por Fase y Total", 
                    detected_columns['apparent_power'], 
                    "Potencia (VA)",
                    colors=['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728']
                )
                if series_count > 0:
                    st.plotly_chart(apparent_chart, use_container_width=True)
                else:
                    st.info("No hay datos de potencia aparente válidos para mostrar")
        
        # Gráfico de demanda - CORREGIDO
        if show_demand:
            st.subheader("📈 Demanda de Potencia")
            if detected_columns['demand']:
                demand_col = detected_columns['demand'][0]  # Tomar la primera columna de demanda
                if demand_col in filtered_df.columns:
                    demand_data = filtered_df[demand_col].dropna()
                    if len(demand_data) > 0:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=filtered_df['timestamp'], 
                            y=filtered_df[demand_col],
                            mode='lines', 
                            name='Demanda',
                            line=dict(width=3, color='#17BECF'),
                            fill='tozeroy',
                            fillcolor='rgba(23, 190, 207, 0.1)',
                            hovertemplate=f'Demanda<br>%{{x|%d-%m-%Y %H:%M}}<br>%{{y:.2f}} W<extra></extra>'
                        ))
                        fig.update_layout(
                            title='Demanda de Potencia Real',
                            xaxis_title='Fecha y Hora',
                            yaxis_title='Potencia (W)',
                            template='plotly_white', 
                            hovermode='x unified',
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No hay datos de demanda válidos para mostrar")
                else:
                    st.info("Columna de demanda no encontrada en datos")
            else:
                st.info("No se detectaron columnas de demanda")

        # Tabla de datos y exportación
        st.divider()
        st.subheader("📊 Datos Detallados")
        
        # Mostrar tabla con scroll
        st.dataframe(filtered_df, height=400, use_container_width=True)
        
        # Botones de exportación mejorados
        st.subheader("📥 Exportar Datos")
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            # Preparar CSV con fechas en formato string
            csv_data = filtered_df.copy()
            if 'timestamp' in csv_data.columns:
                csv_data['timestamp'] = csv_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            csv = csv_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📄 Descargar CSV", 
                data=csv, 
                file_name=f"powerlogic_data_{start}_{end}.csv",
                mime="text/csv",
                help="Descargar datos en formato CSV",
                use_container_width=True
            )
        
        with col2:
            # Crear Excel con múltiples hojas
            from io import BytesIO
            import pandas as pd
            
            def create_excel_file(data):
                # Crear una copia profunda de los datos para no modificar el original
                data_copy = data.copy(deep=True)
                
                # Función para limpiar timezone de cualquier columna datetime
                def clean_datetime_columns(df):
                    for col in df.columns:
                        if pd.api.types.is_datetime64_any_dtype(df[col]):
                            # Si la columna es datetime, convertir a string y luego a datetime sin timezone
                            try:
                                # Convertir a string primero para eliminar cualquier timezone
                                df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d %H:%M:%S')
                                df[col] = pd.to_datetime(df[col])
                            except Exception as e:
                                # Si falla, convertir directamente a string
                                df[col] = df[col].astype(str)
                    return df
                
                # Limpiar todas las columnas datetime
                data_copy = clean_datetime_columns(data_copy)
                
                buffer = BytesIO()
                try:
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        # Hoja principal con todos los datos
                        data_copy.to_excel(writer, sheet_name='Datos Completos', index=False)
                        
                        # Hoja de resumen estadístico
                        summary_data = []
                        for col in data_copy.columns:
                            if col != 'timestamp' and pd.api.types.is_numeric_dtype(data_copy[col]):
                                col_data = data_copy[col].dropna()  # Eliminar NaN para estadísticas
                                if len(col_data) > 0:
                                    stats = {
                                        'Campo': col,
                                        'Promedio': round(float(col_data.mean()), 3),
                                        'Máximo': round(float(col_data.max()), 3),
                                        'Mínimo': round(float(col_data.min()), 3),
                                        'Desviación Estándar': round(float(col_data.std()), 3),
                                        'Registros': int(col_data.count())
                                    }
                                    summary_data.append(stats)
                        
                        if summary_data:
                            summary_df = pd.DataFrame(summary_data)
                            summary_df.to_excel(writer, sheet_name='Resumen Estadístico', index=False)
                
                except Exception as e:
                    st.error(f"Error al crear Excel avanzado: {str(e)}")
                    # Crear Excel simple como fallback
                    try:
                        buffer = BytesIO()  # Reiniciar buffer
                        fallback_data = data.copy()
                        
                        # Convertir TODAS las columnas datetime a string
                        for col in fallback_data.columns:
                            if pd.api.types.is_datetime64_any_dtype(fallback_data[col]):
                                fallback_data[col] = fallback_data[col].astype(str)
                        
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            fallback_data.to_excel(writer, sheet_name='Datos', index=False)
                        
                        st.warning("Se creó un Excel simplificado debido a problemas con las fechas.")
                        
                    except Exception as e2:
                        st.error(f"Error crítico al crear Excel: {str(e2)}")
                        return None
                
                buffer.seek(0)
                return buffer.getvalue()
            
            excel_data = create_excel_file(filtered_df)
            
            if excel_data is not None:
                st.download_button(
                    "📊 Descargar Excel Completo", 
                    data=excel_data, 
                    file_name=f"powerlogic_completo_{start}_{end}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Excel con múltiples hojas: datos completos y resumen estadístico",
                    use_container_width=True
                )
            else:
                st.error("No se pudo generar el archivo Excel")
        
        with col3:
            st.metric("Total de registros", len(filtered_df))
            
            # Botón adicional para exportar solo el rango visible en la tabla
            if st.button("📋 Copiar datos al portapapeles", use_container_width=True):
                # Convertir a formato de texto tab-separated para clipboard
                clipboard_data = filtered_df.copy()
                if 'timestamp' in clipboard_data.columns:
                    clipboard_data['timestamp'] = clipboard_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                clipboard_text = clipboard_data.to_csv(sep='\t', index=False)
                st.code(clipboard_text[:500] + "..." if len(clipboard_text) > 500 else clipboard_text, 
                       language=None)
                st.success("¡Datos listos para copiar! Selecciona el texto de arriba y cópialo.")

else:
    st.error("❌ Por favor selecciona un rango de fechas válido")

# Footer
st.divider()
st.caption(f"© {datetime.today().year} Schneider Electric - Power Monitoring System | v2.1 | Datos de InfluxDB")

# Información de debug (solo en modo desarrollo)
if st.sidebar.checkbox("🔧 Modo Debug Avanzado"):
    st.sidebar.subheader("Debug Info")
    st.sidebar.json({
        "URL": INFLUX_URL,
        "Bucket": INFLUX_BUCKET,
        "Org": INFLUX_ORG,
        "Columnas disponibles": list(df.columns) if df is not None else [],
        "Columnas detectadas": detected_columns
    })