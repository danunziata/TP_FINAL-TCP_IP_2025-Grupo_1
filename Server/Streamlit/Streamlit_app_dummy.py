import streamlit as st
import pandas as pd
import plotly.express as px

# Ruta al CSV con datos dummy
# Asegúrate de que este archivo exista en el mismo directorio
data_file = "datos_fake_powerlogic.csv"

@st.cache_data
def load_dummy_data() -> pd.DataFrame:
    try:
        # Lectura robusta: usar motor Python y omitir líneas mal formadas
        df = pd.read_csv(data_file, engine='python', on_bad_lines='skip')
    except Exception as e:
        st.error(f"Error al leer '{data_file}': {e}")
        st.stop()

    # Determinar columna de fecha
    if "_time" in df.columns:
        df["_time"] = pd.to_datetime(df["_time"], errors='coerce')
        df = df.rename(columns={"_time": "time"})
    elif "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors='coerce')
    else:
        st.error(f"No encontré una columna de fecha ('_time' o 'time') en '{data_file}'. Columnas disponibles: {df.columns.tolist()}")
        st.stop()

    # Eliminar filas sin fecha válida
    df = df.dropna(subset=["time"]).set_index("time")
    return df

# Configuración de la página
st.set_page_config(page_title="Monitor PowerLogic 4000 (Dummy)", layout="wide")

# Título y descripción
st.title("Monitor PowerLogic 4000 (modo dummy)")
st.markdown("Visualización de datos de prueba desde CSV local")

# Carga de datos
df = load_dummy_data()

# Selección de rango de fechas
min_date = df.index.min().date()
max_date = df.index.max().date()
start_date = st.date_input("Fecha Inicio", value=min_date, min_value=min_date, max_value=max_date)
end_date = st.date_input("Fecha Fin", value=max_date, min_value=min_date, max_value=max_date)

if start_date >= end_date:
    st.error("La fecha de inicio debe ser anterior a la fecha de fin.")
    st.stop()

# Filtrar DataFrame por rango de fechas
df_filt = df.loc[start_date:end_date]

if df_filt.empty:
    st.warning("No hay datos en el rango seleccionado.")
else:
    # Graficas
    st.subheader("Corriente")
    currents = [c for c in df_filt.columns if c.startswith('current_')]
    fig_i = px.line(df_filt, y=currents, labels={'value': 'Corriente (A)', 'time': 'Tiempo'}, title='Corriente por fase')
    st.plotly_chart(fig_i, use_container_width=True)

    st.subheader("Tensión")
    voltages = [v for v in df_filt.columns if v.startswith('voltage_')]
    fig_v = px.line(df_filt, y=voltages, labels={'value': 'Tensión (V)', 'time': 'Tiempo'}, title='Tensión por fase')
    st.plotly_chart(fig_v, use_container_width=True)

    st.subheader("Potencia")
    power_fields = ["power_active", "power_reactive", "power_apparent"]
    fig_p = px.line(df_filt, y=power_fields, labels={'value': 'Potencia (W/VAR/VA)', 'time': 'Tiempo'}, title='Potencias')
    st.plotly_chart(fig_p, use_container_width=True)

    st.subheader("Factor de Potencia")
    pf_fields = ["pf_r", "pf_s", "pf_t"]
    fig_pf = px.line(df_filt, y=pf_fields, labels={'value': 'Factor de Potencia', 'time': 'Tiempo'}, title='Factor de Potencia (R, S, T)')
    st.plotly_chart(fig_pf, use_container_width=True)

    # Botón para descarga
    csv = df_filt.reset_index().to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar CSV",
        data=csv,
        file_name=f"powerlogic_dummy_{start_date}_{end_date}.csv",
        mime='text/csv'
    )

st.sidebar.info("Este modo lee desde 'datos_fake_powerlogic.csv'.")
