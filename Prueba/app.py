import yaml # Importa la librería yaml
from yaml.loader import SafeLoader # Importa SafeLoader para cargar el archivo yaml
from pathlib import Path

import pandas as pd  # pip install pandas openpyxl
import plotly.express as px  # pip install plotly-express
import streamlit as st  # pip install streamlit
import streamlit_authenticator as stauth  # pip install streamlit-authenticator


# emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
st.set_page_config(page_title="Sales Dashboard", page_icon=":bar_chart:", layout="wide")


# --- USER AUTHENTICATION ---
# Carga el archivo de configuración YAML
file_path = Path(__file__).parent / "config.yaml"
with file_path.open("r", encoding="utf-8") as file: # Abre el archivo en modo lectura ('r') con codificación utf-8
    config = yaml.load(file, Loader=SafeLoader) # Carga el contenido del archivo YAML

# Crea una instancia del autenticador con la configuración cargada
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    auto_hash=False
)

# Intenta loguear al usuario.
# Si la ubicación es 'main' o 'sidebar', este método renderiza el formulario
# y ACTUALIZA st.session_state. No devuelve nada (None).
authenticator.login(location="main")

# Verifica el estado de autenticación usando st.session_state
# La información de autenticación ahora SIEMPRE se lee desde st.session_state
if st.session_state["authentication_status"]:
    # ---- SIDEBAR ----
    # El botón de logout usa el estado de autenticación de st.session_state automáticamente
    authenticator.logout("Logout", "sidebar")
    
    """
    INSERTAR AQUI EL CODIGO PARA LA APLICACION
    """

# Si la autenticación falla
elif st.session_state["authentication_status"] is False:
    st.error("Username/password is incorrect")

# Si el estado de autenticación es None (formulario no enviado, o cookie no válida)
elif st.session_state["authentication_status"] is None:
    st.warning("Please enter your username and password")