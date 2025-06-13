import streamlit as st
import pandas as pd
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import plotly.express as px

# Configuración de conexión a InfluxDB
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "YOUR_INFLUXDB_TOKEN"
INFLUX_ORG = "YOUR_ORG"
INFLUX_BUCKET = "YOUR_BUCKET"

@st.cache_resource
def get_influx_client():
    return InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)

@st.cache_data
def query_data(start: str, end: str) -> pd.DataFrame:
    client = get_influx_client()
    query_api = client.query_api()
    flux_query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: {start}, stop: {end})
      |> filter(fn: (r) => r._measurement == "powerlogic_4000")
      |> filter(fn: (r) => r._field == "current" or r._field == "voltage" or r._field == "power_active" or r._field == "power_reactive" or r._field == "power_apparent" or r._field == "pf_r" or r._field == "pf_s" or r._field == "pf_t")
      |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    result = query_api.query_data_frame(flux_query)
    if "result" in result.columns:
        result = result.drop(columns=["result", "table"])
    result = result.rename(columns={"_time": "time"})
    result["time"] = pd.to_datetime(result["time"])
    result = result.set_index("time")
    return result

# Título y descripción
st.title("Monitor PowerLogic 4000")
st.markdown("Visualización de datos de corriente, tensión, potencias y factor de potencia")

# Selección de rango de fechas
start_date = st.date_input("Fecha Inicio", value=pd.to_datetime("2025-01-01"))
end_date = st.date_input("Fecha Fin", value=pd.to_datetime("today"))

if start_date >= end_date:
    st.error("La fecha de inicio debe ser anterior a la fecha de fin.")
    st.stop()

# Botón para cargar datos
if st.button("Cargar Datos"):
    with st.spinner("Consultando InfluxDB..."):
        df = query_data(start_date.isoformat(), end_date.isoformat())
    if df.empty:
        st.warning("No hay datos en el rango seleccionado.")
    else:
        # Graficas
        st.subheader("Corriente")
        fig_i = px.line(df, y=[col for col in df.columns if col.startswith('current')], labels={'value': 'Corriente (A)', 'time': 'Tiempo'}, title='Corriente por fase')
        st.plotly_chart(fig_i, use_container_width=True)

        st.subheader("Tensión")
        fig_v = px.line(df, y=[col for col in df.columns if col.startswith('voltage')], labels={'value': 'Tensión (V)', 'time': 'Tiempo'}, title='Tensión por fase')
        st.plotly_chart(fig_v, use_container_width=True)

        st.subheader("Potencia")
        fig_p = px.line(df, y=["power_active", "power_reactive", "power_apparent"], labels={'value': 'Potencia (W/VAR/VA)', 'time': 'Tiempo'}, title='Potencias')
        st.plotly_chart(fig_p, use_container_width=True)

        st.subheader("Factor de Potencia")
        fig_pf = px.line(df, y=["pf_r", "pf_s", "pf_t"], labels={'value': 'Factor de Potencia', 'time': 'Tiempo'}, title='Factor de Potencia (R, S, T)')
        st.plotly_chart(fig_pf, use_container_width=True)

        # Botón para descargar
        csv = df.reset_index().to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name=f"powerlogic_data_{start_date}_{end_date}.csv",
            mime='text/csv'
        )

# Instrucciones de configuración
st.sidebar.header("Configuración")
st.sidebar.text("Configurar las variables de InfluxDB en el código fuente.")
