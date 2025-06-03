import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
import os

# Configurar la página
st.set_page_config(
    page_title="Dashboard IPSEP",
    layout="wide"
)

# ---------- Leer configuración desde config.yaml ----------
with open("config.yaml", encoding='utf-8') as file:
    config = yaml.load(file, Loader=SafeLoader)

    if not config or 'credentials' not in config or 'usernames' not in config['credentials']:
        st.error("❌ ERROR: Archivo config.yaml mal formado o incompleto.")
        st.stop()

    st.write("🔍 DEBUG - Config cargado:", config)
# ---------- Autenticador ----------
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    cookie=None,
    preauthorized=None,
    hashed=False  # 👈 IMPORTANTE: aceptar texto plano
)
# ---------- Login ----------
authenticator.login(location="main")

if st.session_state.get("authentication_status"):
    authenticator.logout("🔓 Cerrar sesión", location="sidebar")
    st.sidebar.success(f"Conectado como: {st.session_state['name']}")

    # ---------- Dashboard ----------
    st.title("⚡ Dashboard de Energía Eléctrica")
    st.caption("💡 Podés cambiar el tema en ☰ > Settings")

    # Cargar datos
    meses_disponibles = ["marzo", "abril", "mayo"]
    mes_seleccionado = st.selectbox("📅 Seleccioná un mes:", meses_disponibles, index=2)

    @st.cache_data
    def cargar_datos(mes):
        archivo = f"datos_completos_{mes}_2025.csv"
        if os.path.exists(archivo):
            return pd.read_csv(archivo, parse_dates=['Timestamp'])
        return pd.DataFrame()

    df = cargar_datos(mes_seleccionado)

    if df.empty:
        st.error("No se encontraron datos para ese mes.")
        st.stop()

    # Visualización
    variables_disponibles = [
        "Potencia Real (kW)", "Potencia Reactiva (kVAR)", "Potencia Aparente (kVA)",
        "Tensión (V)", "Corriente (A)", "Frecuencia (Hz)", "Factor de Potencia",
        "THD Corriente (%)", "THD Voltaje (%)", "Temperatura Interna (°C)"
    ]

    with st.sidebar:
        st.header("📊 Visualización")
        variable = st.radio("Seleccioná una variable:", variables_disponibles)

    st.subheader(f"{variable} durante {mes_seleccionado.capitalize()} 2025")
    st.line_chart(df.set_index("Timestamp")[[variable]])

    media = df[variable].mean()
    desv = df[variable].std()
    st.markdown(f"**Valor medio:** `{media:.2f}` — **Desviación estándar:** `{desv:.2f}`")

    # Exportación (solo admin)
    if st.session_state["username"] == "admin_user":
        st.divider()
        st.subheader("📥 Exportación")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"⬇️ Descargar CSV ({mes_seleccionado} 2025)",
            data=csv,
            file_name=f"mediciones_{mes_seleccionado}_2025.csv",
            mime="text/csv"
        )

elif st.session_state.get("authentication_status") is False:
    st.error("❌ Usuario o contraseña incorrectos.")

elif st.session_state.get("authentication_status") is None:
    st.warning("👈 Ingrese sus credenciales.")
