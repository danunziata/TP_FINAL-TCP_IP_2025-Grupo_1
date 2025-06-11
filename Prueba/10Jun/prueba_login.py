import yaml # Importa la librería yaml
from yaml.loader import SafeLoader # Importa SafeLoader para cargar el archivo yaml
from pathlib import Path

import pandas as pd  # pip install pandas openpyxl
import plotly.express as px  # pip install plotly-express
import streamlit as st  # pip install streamlit
import streamlit_authenticator as stauth  # pip install streamlit-authenticator


# emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
st.set_page_config(page_title="Prueba de LogIn", page_icon=":bar_chart:", layout="wide")


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
    auto_hash=False #No intenta hashear la información de credentials, ya que ya lo estan
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
    st.error(f"Usuario/Contraseña incorrecta.")

# Si el estado de autenticación es None (formulario no enviado, o cookie no válida)
elif st.session_state["authentication_status"] is None:
    st.warning("Por favor, ingresá tu Usuario y Contraseña")
    
    # Opción para registrar nuevos usuarios
    st.markdown("---") # Separador visual
    st.subheader("Registrar nuevo usuario")

    # Inicializa las variables para el registro de usuario
    email_of_registered_user, username_of_registered_user, name_of_registered_user = None, None, None

    try:
        # El widget de registro de usuario
        # register_user() devuelve los datos del nuevo usuario si el registro es exitoso.
        email_of_registered_user, username_of_registered_user, name_of_registered_user = authenticator.register_user(
            location='main',
            pre_authorized=None,
            fields={'First name': 'Nombre', 'Last name': 'Apellido','Form name': 'Formulario de Registro', 'Email': 'Correo Electrónico',
                    'Username': 'Nombre de Usuario', 'Password': 'Contraseña',
                    'Repeat password': 'Repetir Contraseña', 'Password hint': 'Ayuda en caso de olvidar contraseña', 'Register': 'Registrarse'},
            clear_on_submit=True
        )
    except Exception as e:
        st.error(e)
    
    # Mueve el checkbox fuera del bloque try-except para que siempre se muestre
    recibir_notificaciones = st.checkbox("Deseo recibir notificaciones por email")

    if email_of_registered_user:
        # Verifica el dominio del correo electrónico
        if not email_of_registered_user.endswith('@ing.unrc.edu.ar'):
            # Si el dominio no es el permitido, elimina al usuario del diccionario config
            # (streamlit_authenticator ya lo habrá añadido si el registro "inicial" fue exitoso)
            del config['credentials']['usernames'][username_of_registered_user]
            st.error("Error: Solo se permiten registros con correos electrónicos de '@ing.unrc.edu.ar'.")
        else:
            # Si el dominio es válido, procede a guardar la información adicional y el usuario
            config['credentials']['usernames'][username_of_registered_user]['notificaciones'] = recibir_notificaciones
            st.success('Usuario registrado exitosamente. Ahora puedes iniciar sesión.')
            # Guardar la configuración actualizada con el nuevo usuario
            with file_path.open("w", encoding="utf-8") as file:
                yaml.dump(config, file, default_flow_style=False)