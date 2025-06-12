import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
from influxdb_client import InfluxDBClient

def main():
    # Configuración de InfluxDB desde variables de entorno
    INFLUX_URL    = os.getenv('INFLUXDB_URL',    'http://192.168.5.131:9000')
    INFLUX_TOKEN  = os.getenv('INFLUXDB_TOKEN',  'token_telegraf')
    INFLUX_ORG    = os.getenv('INFLUXDB_ORG',    'power_logic')
    INFLUX_BUCKET = os.getenv('INFLUXDB_BUCKET', 'mensualx6')

    # Configuración de la aplicación

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
            'voltage_l1n': 'Voltaje L1N (V)',
            'voltage_l2n': 'Voltaje L2N (V)', 
            'voltage_l3n': 'Voltaje L3N (V)',
            'voltaje': 'Voltaje General (V)',
            'voltaje_l2n': 'Voltaje L2N Alt (V)',
            'voltaje_l3n': 'Voltaje L3N Alt (V)',
            'current_l1': 'Corriente L1 (A)',
            'current_l2': 'Corriente L2 (A)',
            'current_l3': 'Corriente L3 (A)',
            'active_power': 'Potencia Activa (W)'
        }
        
        df = result.rename(columns=field_mapping)
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)

        # Convertir escala si necesario (dividir entre 10 para tensiones y corrientes)
        scale_columns = [
            'Voltaje L1N (V)', 'Voltaje L2N (V)', 'Voltaje L3N (V)',
            'Voltaje General (V)', 'Voltaje L2N Alt (V)', 'Voltaje L3N Alt (V)',
            'Corriente L1 (A)', 'Corriente L2 (A)', 'Corriente L3 (A)'
        ]
        
        for col in scale_columns:
            if col in df.columns:
                df[col] = df[col] / 10.0

        return df

    # Función para crear gráfico de múltiples series
    def create_multi_series_chart(data, title, y_columns, y_title, colors=None):
        fig = go.Figure()
        
        if colors is None:
            colors = ['#FF4B4B', '#0068C9', '#00C39F', '#FF8C00', '#9467BD', '#8C564B', '#E377C2']
        
        for i, col in enumerate(y_columns):
            if col in data.columns and not data[col].isna().all():
                color = colors[i % len(colors)]
                fig.add_trace(go.Scatter(
                    x=data['timestamp'], 
                    y=data[col],
                    mode='lines', 
                    name=col,
                    line=dict(width=2, color=color),
                    hovertemplate=f'{col}<br>%{{x|%d-%m-%Y %H:%M}}<br>%{{y:.2f}}<extra></extra>'
                ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Fecha y Hora',
            yaxis_title=y_title,
            template='plotly_white', 
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=500
        )
        return fig

    # Función para crear gráfico de potencia activa
    def create_power_chart(data, title='Potencia Activa'):
        fig = go.Figure()
        
        if 'Potencia Activa (W)' in data.columns and not data['Potencia Activa (W)'].isna().all():
            fig.add_trace(go.Scatter(
                x=data['timestamp'], 
                y=data['Potencia Activa (W)'],
                mode='lines', 
                name='Potencia Activa',
                line=dict(width=3, color='#FF6B35'),
                fill='tozeroy',
                fillcolor='rgba(255, 107, 53, 0.1)',
                hovertemplate='Potencia Activa<br>%{x|%d-%m-%Y %H:%M}<br>%{y:.2f} W<extra></extra>'
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Fecha y Hora',
            yaxis_title='Potencia (W)',
            template='plotly_white', 
            hovermode='x unified',
            height=400
        )
        return fig

    # Función para crear dashboard de métricas
    def create_metrics_dashboard(data):
        col1, col2, col3, col4 = st.columns(4)
        
        # Métricas de voltaje
        voltage_cols = [col for col in data.columns if 'Voltaje' in col and col != 'timestamp']
        if voltage_cols:
            avg_voltage = data[voltage_cols].mean().mean()
            col1.metric("Voltaje Promedio", f"{avg_voltage:.1f} V")
        
        # Métricas de corriente
        current_cols = [col for col in data.columns if 'Corriente' in col]
        if current_cols:
            avg_current = data[current_cols].mean().mean()
            col2.metric("Corriente Promedio", f"{avg_current:.2f} A")
        
        # Métricas de potencia
        if 'Potencia Activa (W)' in data.columns:
            avg_power = data['Potencia Activa (W)'].mean()
            max_power = data['Potencia Activa (W)'].max()
            col3.metric("Potencia Promedio", f"{avg_power:.0f} W")
            col4.metric("Potencia Máxima", f"{max_power:.0f} W")

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
        show_power = st.checkbox("Potencia Activa", value=True)
        
        # Información de campos disponibles
        st.subheader("📋 Campos disponibles:")
        available_fields = [col for col in df.columns if col != 'timestamp']
        for field in available_fields:
            st.caption(f"• {field}")

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
            create_metrics_dashboard(filtered_df)
            st.divider()
            
            # Gráficos de voltajes
            if show_voltages:
                st.subheader("⚡ Voltajes")
                voltage_columns = [col for col in filtered_df.columns if 'Voltaje' in col]
                if voltage_columns:
                    voltage_chart = create_multi_series_chart(
                        filtered_df, 
                        "Voltajes por Fase y Medición", 
                        voltage_columns, 
                        "Voltaje (V)"
                    )
                    st.plotly_chart(voltage_chart, use_container_width=True)
                else:
                    st.info("No hay datos de voltaje disponibles")
            
            # Gráficos de corrientes
            if show_currents:
                st.subheader("🔌 Corrientes")
                current_columns = [col for col in filtered_df.columns if 'Corriente' in col]
                if current_columns:
                    current_chart = create_multi_series_chart(
                        filtered_df, 
                        "Corrientes por Fase", 
                        current_columns, 
                        "Corriente (A)",
                        colors=['#FF4B4B', '#0068C9', '#00C39F']
                    )
                    st.plotly_chart(current_chart, use_container_width=True)
                else:
                    st.info("No hay datos de corriente disponibles")
            
            # Gráfico de potencia activa
            if show_power:
                st.subheader("🔋 Potencia Activa")
                if 'Potencia Activa (W)' in filtered_df.columns:
                    power_chart = create_power_chart(filtered_df)
                    st.plotly_chart(power_chart, use_container_width=True)
                else:
                    st.info("No hay datos de potencia activa disponibles")
            
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
                            
                            # Hoja de voltajes solo
                            voltage_cols = [col for col in data_copy.columns if 'Voltaje' in col]
                            if voltage_cols:
                                voltage_cols_with_time = ['timestamp'] + voltage_cols
                                voltage_cols_with_time = [col for col in voltage_cols_with_time if col in data_copy.columns]
                                if len(voltage_cols_with_time) > 1:
                                    voltage_data = data_copy[voltage_cols_with_time].copy()
                                    voltage_data = clean_datetime_columns(voltage_data)
                                    voltage_data.to_excel(writer, sheet_name='Voltajes', index=False)
                            
                            # Hoja de corrientes solo
                            current_cols = [col for col in data_copy.columns if 'Corriente' in col]
                            if current_cols:
                                current_cols_with_time = ['timestamp'] + current_cols
                                current_cols_with_time = [col for col in current_cols_with_time if col in data_copy.columns]
                                if len(current_cols_with_time) > 1:
                                    current_data = data_copy[current_cols_with_time].copy()
                                    current_data = clean_datetime_columns(current_data)
                                    current_data.to_excel(writer, sheet_name='Corrientes', index=False)
                            
                            # Hoja de potencia solo
                            power_cols = [col for col in data_copy.columns if 'Potencia' in col]
                            if power_cols:
                                power_cols_with_time = ['timestamp'] + power_cols
                                power_cols_with_time = [col for col in power_cols_with_time if col in data_copy.columns]
                                if len(power_cols_with_time) > 1:
                                    power_data = data_copy[power_cols_with_time].copy()
                                    power_data = clean_datetime_columns(power_data)
                                    power_data.to_excel(writer, sheet_name='Potencia', index=False)
                    
                    except Exception as e:
                        st.error(f"Error al crear Excel avanzado: {str(e)}")
                        # Crear Excel simple como fallback - solo datos con timestamp como string
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
                        help="Excel con múltiples hojas: datos completos, resumen estadístico y datos por categoría",
                        use_container_width=True
                    )
                else:
                    st.error("No se pudo generar el archivo Excel")
                    # Botón de Excel simple como alternativa
                    simple_data = filtered_df.copy()
                    for col in simple_data.columns:
                        if pd.api.types.is_datetime64_any_dtype(simple_data[col]):
                            simple_data[col] = simple_data[col].astype(str)
                    
                    simple_buffer = BytesIO()
                    simple_data.to_excel(simple_buffer, index=False, engine='openpyxl')
                    simple_buffer.seek(0)
                    
                    st.download_button(
                        "📋 Excel Básico (Fallback)", 
                        data=simple_buffer.getvalue(), 
                        file_name=f"powerlogic_basico_{start}_{end}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        help="Versión básica del Excel con fechas como texto",
                        use_container_width=True
                    )
            
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
    st.caption(f"© {datetime.today().year} Schneider Electric - Power Monitoring System | v2.0 | Datos de InfluxDB")

    # Información de debug (solo en modo desarrollo)
    if st.sidebar.checkbox("🔧 Modo Debug"):
        st.sidebar.subheader("Debug Info")
        st.sidebar.json({
            "URL": INFLUX_URL,
            "Bucket": INFLUX_BUCKET,
            "Org": INFLUX_ORG,
            "Columnas disponibles": list(df.columns) if df is not None else []
        })