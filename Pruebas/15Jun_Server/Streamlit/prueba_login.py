print("DEBUG: Script prueba_login.py iniciando...")

import os
import json
import yaml
from yaml.loader import SafeLoader
from pathlib import Path
import streamlit as st
import streamlit_authenticator as stauth
from pagina import main as app_final # Importamos la función main de pagina.py
from emailsender import enviar_alerta # Importamos la función para enviar correos
import secrets # Para generar tokens seguros
from datetime import datetime, timedelta
import bcrypt # Para hashear contraseñas en el formulario manual de reset

# Nombres de los archivos
RESET_TOKENS_FILE = "reset_tokens.json"
CONFIG_FILE_PATH = Path(__file__).parent / "config.yaml" # Ruta del archivo de configuración
USUARIOS_FILE = "usuarios.json" # Para la función de registro

# --- Funciones locales para cargar/guardar config.yaml (para uso en prueba_login.py) ---
def load_config_local():
    """Carga el archivo config.yaml."""
    try:
        with CONFIG_FILE_PATH.open("r", encoding="utf-8") as f:
            return yaml.load(f, Loader=SafeLoader)
    except Exception as e:
        print(f"ERROR: Error al cargar config.yaml localmente: {e}") # Usar print para logs de Docker
        return None

def save_config_local(config_data):
    """Guarda el archivo config.yaml."""
    try:
        with CONFIG_FILE_PATH.open("w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False)
        return True
    except Exception as e:
        print(f"ERROR: Error al guardar config.yaml localmente: {e}") # Usar print para logs de Docker
        return False

# --- Funciones para cargar/guardar tokens de restablecimiento ---
def load_reset_tokens():
    """
    Carga los tokens de restablecimiento desde el archivo JSON,
    limpiando los que ya han expirado.
    """
    if os.path.exists(RESET_TOKENS_FILE):
        try:
            with open(RESET_TOKENS_FILE, "r", encoding="utf-8") as f:
                tokens_data = json.load(f)
            
            now = datetime.now()
            valid_tokens = {}
            for token, info in tokens_data.items():
                try:
                    expiry_dt = datetime.fromisoformat(info['expiry'])
                    if expiry_dt > now:
                        valid_tokens[token] = {
                            'username': info['username'],
                            'email': info['email'],
                            'expiry': expiry_dt
                        }
                except (ValueError, KeyError):
                    print(f"DEBUG: Token con formato incorrecto en {RESET_TOKENS_FILE}: {token}: {info}")
                    continue
            return valid_tokens
        except (json.JSONDecodeError, FileNotFoundError) as e:
            st.warning(f"Error al cargar el archivo de tokens de restablecimiento '{RESET_TOKENS_FILE}': {e}. Se iniciará con tokens vacíos.")
            return {}
    return {}

def save_reset_tokens(tokens_dict):
    """
    Guarda los tokens de restablecimiento en el archivo JSON.
    Convierte los objetos datetime a formato ISO para su serialización.
    """
    serializable_tokens = {
        token: {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in info.items()}
        for token, info in tokens_dict.items()
    }
    try:
        with open(RESET_TOKENS_FILE, "w", encoding="utf-8") as f:
            json.dump(serializable_tokens, f, indent=4)
        print(f"DEBUG: Tokens de restablecimiento guardados en {RESET_TOKENS_FILE}")
    except Exception as e:
        st.error(f"Error al guardar los tokens de restablecimiento en '{RESET_TOKENS_FILE}': {e}")


st.set_page_config(
    page_title="PowerLogic 4000 Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Carga inicial de configuración ---
if not CONFIG_FILE_PATH.exists():
    st.error(f"Error: El archivo '{CONFIG_FILE_PATH.name}' no se encontró en el directorio Streamlit.")
    st.stop()

# Cargar la configuración global (este `config` es el objeto global que `authenticator` modificará)
try:
    config = load_config_local() # Usar la función local para la carga inicial
    if config:
        print(f"DEBUG: Configuración cargada desde {CONFIG_FILE_PATH}")
        if 'credentials' in config and 'usernames' in config['credentials']:
            print("DEBUG: Credenciales cargadas para Authenticator initialization:")
            for uname, udata in config['credentials']['usernames'].items():
                if 'password' in udata:
                    print(f"DEBUG:   '{uname}': {udata['password']}")
                else:
                    print(f"DEBUG:   '{uname}': (No password found)")
    else:
        st.stop() # Si load_config_local falló, detener la ejecución
except Exception as e:
    st.error(f"Error inesperado al cargar la configuración inicial: {e}.")
    st.stop()


if 'credentials' not in config or 'cookie' not in config:
    st.error("Error: La estructura de 'config.yaml' es inválida. Faltan secciones 'credentials' o 'cookie'.")
    st.stop()


authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    auto_hash=False
)
print("DEBUG: Objeto Authenticate inicializado.")

# Cargar los tokens de restablecimiento al inicio del script desde el archivo
st.session_state.reset_tokens = load_reset_tokens()


# --- Funciones de Callback para Reseteo de Contraseña ---
def send_reset_password_email_callback(username, email, key):
    """
    Envía un correo electrónico con el enlace de restablecimiento de contraseña.
    """
    try:
        base_url = "http://localhost:8501"
        reset_link = f"{base_url}/?token={key}"

        asunto = "Restablece tu contraseña de PowerLogic Monitor"
        html_mensaje = f"""
        <h2>Restablecimiento de Contraseña</h2>
        <p>Hola {username},</p>
        <p>Hemos recibido una solicitud para restablecer la contraseña de tu cuenta.</p>
        <p>Haz clic en el siguiente enlace para establecer una nueva contraseña:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p>Si no solicitaste un restablecimiento de contraseña, ignora este correo electrónico.</p>
        <p>Este enlace es válido por un tiempo limitado.</p>
        <p>Gracias,<br>El equipo de PowerLogic Monitor</p>
        """

        enviar_alerta(email, asunto, html_mensaje)
        st.success("Se ha enviado un correo electrónico con instrucciones para restablecer tu contraseña. Por favor, revisa tu bandeja de entrada (y la carpeta de spam).")
        return True
    except Exception as e:
        st.error(f"Error al enviar el correo de restablecimiento: {e}")
        return False

def update_password_callback(username, new_hashed_password):
    """
    Actualiza la contraseña hasheada en el archivo de configuración.
    Esta función es llamada directamente por nuestro formulario personalizado.
    """
    print(f"DEBUG: update_password_callback llamado para '{username}' con nueva contraseña hasheada: {new_hashed_password}")
    try:
        # Volver a cargar la configuración justo antes de actualizar
        current_config = load_config_local()
        if not current_config:
            return False
        
        if username in current_config['credentials']['usernames']:
            current_config['credentials']['usernames'][username]['password'] = new_hashed_password

            if save_config_local(current_config):
                print(f"DEBUG: Contraseña para '{username}' guardada en el archivo config.yaml.")
                print(f"DEBUG: Verificado hash en archivo después de guardar: {current_config['credentials']['usernames'][username]['password']}")
                return True
            else:
                st.error("Error al guardar la nueva contraseña en config.yaml.")
                return False
        else:
            st.error("Error: Usuario no encontrado para actualizar la contraseña en config.yaml.")
            return False
    except Exception as e:
        st.error(f"Error al actualizar la contraseña en config.yaml: {e}")
        return False

# --- Función auxiliar para mostrar el formulario de registro ---
def display_register_form():
    """
    Muestra el formulario para registrar un nuevo usuario.
    """
    st.markdown("---")
    st.subheader("Registrar nuevo usuario")

    if 'recibir_notificaciones_registro' not in st.session_state:
        st.session_state['recibir_notificaciones_registro'] = True

    recibir_notificaciones = st.checkbox("Deseo recibir notificaciones por email al registrarme", value=st.session_state['recibir_notificaciones_registro'], key="register_notifications_checkbox")
    st.session_state['recibir_notificaciones_registro'] = recibir_notificaciones

    email_of_registered_user, username_of_registered_user, name_of_registered_user = None, None, None

    try:
        # authenticator.register_user modifica el objeto 'config' global en memoria
        register_user_result = authenticator.register_user(
            location='main',
            pre_authorized=None,
            fields={'First name': 'Nombre', 'Last name': 'Apellido', 'Form name': 'Formulario de Registro',
                    'Email': 'Correo Electrónico', 'Username': 'Nombre de Usuario', 'Password': 'Contraseña',
                    'Repeat password': 'Repetir Contraseña', 'Password hint': 'Ayuda en caso de olvidar contraseña',
                    'Register': 'Registrarse'}
        )

        if register_user_result is not None:
            email_of_registered_user, username_of_registered_user, name_of_registered_user = register_user_result
            
            # Usar el objeto `config` global (que fue modificado por authenticator.register_user)
            # Asegurarse de que el usuario haya sido añadido por register_user en la configuración en memoria
            if username_of_registered_user not in config['credentials']['usernames']:
                 st.error(f"Error interno: Usuario '{username_of_registered_user}' no fue añadido a la configuración en memoria por la librería de autenticación.")
                 st.stop() # Added st.stop()
            
            if email_of_registered_user:
                if not email_of_registered_user.endswith('@ing.unrc.edu.ar'):
                    st.error("Error: Solo se permiten registros con correos electrónicos de '@ing.unrc.edu.ar'.")
                    # Si el registro falla por el dominio, asegurar que no quede en config.yaml
                    if username_of_registered_user in config['credentials']['usernames']: # Usar el global config
                        del config['credentials']['usernames'][username_of_registered_user]
                        if save_config_local(config): # Guardar el global config modificado
                            print(f"DEBUG: Usuario '{username_of_registered_user}' eliminado de config.yaml por dominio no permitido.")
                        else:
                            print(f"ERROR: No se pudo eliminar usuario '{username_of_registered_user}' de config.yaml tras dominio inválido.")
                    st.rerun() # Refresh in case of domain error
                    st.stop() # Added st.stop()
                else:
                    # El dominio es válido. Guardar las credenciales actualizadas del objeto `config` global
                    if not save_config_local(config): # Guardar el objeto `config` global modificado
                        st.error("Error: No se pudo guardar el nuevo usuario en config.yaml.")
                        st.stop() # Added st.stop()

                    # Guardar en usuarios.json
                    usuarios_path = USUARIOS_FILE
                    nuevo_usuario_data = {
                        "login_email": email_of_registered_user,
                        "nombre": name_of_registered_user,
                        "alert_email": email_of_registered_user,
                        "recibir_notificaciones": recibir_notificaciones
                    }

                    try:
                        if os.path.exists(usuarios_path):
                            with open(usuarios_path, "r", encoding="utf-8") as f:
                                usuarios = json.load(f)
                        else:
                            usuarios = []

                        actualizado = False
                        for u in usuarios:
                            if u.get("login_email") == email_of_registered_user:
                                u.update(nuevo_usuario_data)
                                actualizado = True
                                break

                        if not actualizado:
                            usuarios.append(nuevo_usuario_data)

                        with open(usuarios_path, "w", encoding="utf-8") as f:
                            json.dump(usuarios, f, indent=4)
                        print(f"DEBUG: Preferencias de notificación guardadas para {email_of_registered_user} en usuarios.json.")

                        st.success("Tu preferencia de notificación ha sido guardada en usuarios.json.")
                        st.success('Usuario registrado exitosamente. Ahora puedes iniciar sesión.') # Consolidar mensaje de éxito
                        st.rerun() # Recargar la página para limpiar el formulario y actualizar la UI
                        st.stop() # Added st.stop()
                    except Exception as e:
                        st.error(f"Error al guardar preferencias de notificación en usuarios.json: {e}")
                        st.stop() # Added st.stop()
    except Exception as e:
        st.error(f"Error durante el registro de usuario: {e}")


# --- Lógica Principal de Autenticación y Enrutamiento ---

query_params = st.query_params

# Inicializar variables de autenticación en st.session_state si no existen
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'name' not in st.session_state:
    st.session_state['name'] = None
if 'email' not in st.session_state:
    st.session_state['email'] = None
if 'roles' not in st.session_state:
    st.session_state['roles'] = None
# Inicializar la bandera para el mensaje de contraseña cambiada
if 'password_changed_success' not in st.session_state:
    st.session_state['password_changed_success'] = False


# 1. Manejar el flujo de restablecimiento de contraseña si hay un token en la URL
if "token" in query_params:
    token_from_query = query_params["token"]
    print(f"DEBUG: Token detectado en URL: {token_from_query}")
    
    now = datetime.now()
    st.session_state.reset_tokens = {k: v for k, v in st.session_state.reset_tokens.items() if v['expiry'] > now}
    save_reset_tokens(st.session_state.reset_tokens)

    if token_from_query in st.session_state.reset_tokens:
        reset_info = st.session_state.reset_tokens[token_from_query]
        print(f"DEBUG: Token encontrado en reset_tokens. Detalles: {reset_info['username']}, expira en: {reset_info['expiry']}")
        if reset_info['expiry'] > now:
            st.subheader(f"Restablecer Contraseña para {reset_info['username']}")
            with st.form("set_new_password_form"):
                new_password = st.text_input("Nueva Contraseña", type="password", key="new_password_input")
                confirm_password = st.text_input("Confirmar Contraseña", type="password", key="confirm_password_input")
                submit_new_password = st.form_submit_button("Establecer Nueva Contraseña")

                if submit_new_password:
                    print("DEBUG: Formulario de nueva contraseña enviado.")
                    if new_password and confirm_password:
                        if new_password == confirm_password:
                            hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            print(f"DEBUG: Nueva contraseña hasheada: {hashed_new_password}")
                            
                            password_updated_successfully = update_password_callback(reset_info['username'], hashed_new_password)
                            
                            if password_updated_successfully:
                                st.session_state['password_changed_success'] = True
                                st.success("Tu contraseña ha sido restablecida exitosamente. Ahora puedes iniciar sesión con tu nueva contraseña.")
                                print(f"DEBUG: Contraseña para '{reset_info['username']}' actualizada con éxito.")
                                del st.session_state.reset_tokens[token_from_query]
                                save_reset_tokens(st.session_state.reset_tokens)
                                st.query_params.pop("token")
                                st.session_state['authentication_status'] = None
                                st.session_state['username'] = None
                                st.session_state['name'] = None
                                st.session_state['email'] = None
                                st.session_state['roles'] = None
                                st.rerun()
                            else:
                                st.error("Hubo un problema al actualizar la contraseña. Inténtalo de nuevo.")
                                print("DEBUG: Fallo al actualizar la contraseña en update_password_callback.")
                        else:
                            st.error("Las contraseñas no coinciden. Por favor, inténtalo de nuevo.")
                            print("DEBUG: Contraseñas ingresadas no coinciden.")
                    else:
                        st.error("Por favor, ingresa y confirma tu nueva contraseña.")
                        print("DEBUG: Campos de nueva contraseña vacíos.")
        else:
            st.error("El enlace de restablecimiento ha expirado. Por favor, solicita uno nuevo.")
            print("DEBUG: Token expirado al segundo chequeo.")
            st.query_params.pop("token")
            st.rerun()
    else:
        st.error("Token de restablecimiento inválido o ya utilizado. Por favor, solicita uno nuevo.")
        print("DEBUG: Token no encontrado en st.session_state.reset_tokens. Probablemente ya usado o inválido.")
        st.query_params.pop("token")
        st.rerun()
    
else:
    # 2. Si NO hay token en la URL y el usuario no está autenticado, mostrar el formulario de login principal.
    if st.session_state['authentication_status'] != True:
        if st.session_state.get('password_changed_success', False):
            st.success("Contraseña cambiada correctamente. Por favor, inicia sesión con tu nueva contraseña.")
            st.session_state['password_changed_success'] = False
            print("DEBUG: Mensaje de contraseña cambiada mostrado en login.")

        print("DEBUG: Intentando renderizar formulario de login.")
        with st.form(key='login_form'):
            st.markdown("## Login")
            login_username = st.text_input("Username", key="login_username_input")
            login_password = st.text_input("Password", type="password", key="login_password_input")
            submit_login_button = st.form_submit_button("Iniciar Sesión")

            if submit_login_button:
                print(f"DEBUG: Formulario de login enviado para usuario: {login_username}")
                current_config_for_login = load_config_local()
                if not current_config_for_login:
                    st.error("Error: No se pudo cargar la configuración para el login.")
                    st.session_state['authentication_status'] = False
                    st.session_state['username'] = None
                    st.session_state['name'] = None
                    st.session_state['email'] = None
                    st.session_state['roles'] = None
                    st.rerun()
                    st.stop()

                user_credentials = current_config_for_login['credentials']['usernames'].get(login_username)
                
                if user_credentials and 'password' in user_credentials:
                    stored_hashed_password = user_credentials['password']
                    try:
                        if isinstance(stored_hashed_password, str):
                            stored_hashed_password = stored_hashed_password.encode('utf-8')
                        
                        if bcrypt.checkpw(login_password.encode('utf-8'), stored_hashed_password):
                            st.session_state['authentication_status'] = True
                            st.session_state['username'] = login_username
                            st.session_state['name'] = user_credentials.get('first_name', login_username)
                            st.session_state['email'] = user_credentials.get('email')
                            st.session_state['roles'] = user_credentials.get('roles')
                            st.success(f"Bienvenido, {st.session_state['name']}!")
                            print(f"DEBUG: Autenticación exitosa para {login_username}. Estado: True, Email: {st.session_state['email']}, Rol: {st.session_state['roles']}")
                            st.rerun()
                        else:
                            st.session_state['authentication_status'] = False
                            st.session_state['username'] = None
                            st.session_state['name'] = None
                            st.session_state['email'] = None
                            st.session_state['roles'] = None
                            st.error("Usuario/Contraseña incorrecta.")
                            print(f"DEBUG: Contraseña incorrecta para {login_username}.")
                    except Exception as e:
                        st.session_state['authentication_status'] = False
                        st.session_state['username'] = None
                        st.session_state['name'] = None
                        st.session_state['email'] = None
                        st.session_state['roles'] = None
                        st.error("Error en la verificación de contraseña. Intenta de nuevo.")
                        print(f"DEBUG: Error durante bcrypt.checkpw para {login_username}: {e}")
                else:
                    st.session_state['authentication_status'] = False
                    st.session_state['username'] = None
                    st.session_state['name'] = None
                    st.session_state['email'] = None
                    st.session_state['roles'] = None
                    st.error("Usuario/Contraseña incorrecta.")
                    print(f"DEBUG: Usuario '{login_username}' no encontrado o sin contraseña.")
        
        if st.session_state['authentication_status'] is None:
            st.warning("Por favor, ingresá tu Usuario y Contraseña")

        st.markdown("---")
        st.subheader("¿Olvidaste tu contraseña?")
        with st.form("forgot_password_form"):
            st.write("Ingresa tu nombre de usuario para restablecer la contraseña.")
            forgot_username_input = st.text_input("Nombre de Usuario", key="forgot_username_input_widget")
            submit_forgot_password = st.form_submit_button("Solicitar Restablecimiento")

            if submit_forgot_password:
                print(f"DEBUG: Solicitud de restablecimiento para usuario: {forgot_username_input}")
                if forgot_username_input:
                    user_found = False
                    user_email = None
                    current_config_for_reset = load_config_local()
                    if not current_config_for_reset:
                        st.error("Error: No se pudo cargar la configuración para restablecer contraseña.")
                        st.stop() # Added st.stop()

                    if forgot_username_input in current_config_for_reset['credentials']['usernames']:
                        user_data_from_config = current_config_for_reset['credentials']['usernames'][forgot_username_input]
                        user_email = user_data_from_config.get('email')
                        user_found = True
                        print(f"DEBUG: Usuario '{forgot_username_input}' encontrado en config.yaml con email: {user_email}")
                    
                    if not user_found and os.path.exists(USUARIOS_FILE):
                        try:
                            with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
                                usuarios_data = json.load(f)
                            for u in usuarios_data:
                                if u.get('login_email') == forgot_username_input:
                                    user_email = u.get('alert_email') or u.get('login_email')
                                    if user_email:
                                        user_found = True
                                        print(f"DEBUG: Usuario '{forgot_username_input}' encontrado en usuarios.json con email: {user_email}")
                                        break
                        except Exception as e:
                            st.error(f"Error al leer usuarios.json: {e}")
                            print(f"DEBUG: Error al leer usuarios.json: {e}")

                    if user_found and user_email:
                        reset_token = secrets.token_urlsafe(32)
                        expiry_time = datetime.now() + timedelta(minutes=15)
                        print(f"DEBUG: Token generado: {reset_token}, expira en: {expiry_time}")

                        st.session_state.reset_tokens[reset_token] = {
                            'username': forgot_username_input,
                            'email': user_email,
                            'expiry': expiry_time
                        }
                        save_reset_tokens(st.session_state.reset_tokens)

                        send_reset_password_email_callback(
                            forgot_username_input,
                            user_email,
                            reset_token
                        )
                        st.success("Si el nombre de usuario existe y tiene un correo electrónico válido, se ha enviado un enlace de restablecimiento.")
                    else:
                        st.error("Nombre de usuario no encontrado o no tiene un correo electrónico asociado para restablecer la contraseña.")
                        print(f"DEBUG: Usuario '{forgot_username_input}' no encontrado o sin email asociado.")
                else:
                    st.error("Por favor, ingresa tu nombre de usuario.")
                    print("DEBUG: Campo de nombre de usuario vacío en solicitud de restablecimiento.")
        
        display_register_form()
    else: # Si authentication_status es True (ya autenticado)
        authenticator.logout("Cerrar Sesión", "sidebar")
        app_final()
