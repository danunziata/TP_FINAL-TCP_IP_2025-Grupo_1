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
        if not CONFIG_FILE_PATH.exists():
            print(f"ERROR: El archivo '{CONFIG_FILE_PATH}' no existe. No se puede cargar la configuración localmente.")
            return None
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
                    # Asegurarse de que 'expiry' es un string antes de fromisoformat
                    expiry_dt = datetime.fromisoformat(str(info['expiry']))
                    if expiry_dt > now:
                        valid_tokens[token] = {
                            'username': info['username'],
                            'email': info['email'],
                            'expiry': expiry_dt
                        }
                except (ValueError, KeyError) as e:
                    print(f"DEBUG: Token con formato incorrecto en {RESET_TOKENS_FILE} (Error: {e}): {token}: {info}")
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
    auto_hash=False # Mantenemos auto_hash en False porque hasheamos manualmente con bcrypt para control
)
print("DEBUG: Objeto Authenticate inicializado.")

# Cargar los tokens de restablecimiento al inicio del script desde el archivo
if 'reset_tokens' not in st.session_state:
    st.session_state.reset_tokens = load_reset_tokens()


# --- Funciones de Callback para Reseteo de Contraseña ---
def send_reset_password_email_callback(username, email, key):
    """
    Envía un correo electrónico con el enlace de restablecimiento de contraseña.
    """
    try:
        base_url = "http://localhost:8501" # Asumiendo que esta es la URL de la app
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

        enviar_alerta(email, asunto, html_mensaje) # Usamos la función de emailsender.py
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
        
        # Aseguramos que el username en el config esté en minúsculas para la búsqueda
        username_lower = username.lower()
        if username_lower in current_config['credentials']['usernames']:
            current_config['credentials']['usernames'][username_lower]['password'] = new_hashed_password

            if save_config_local(current_config):
                print(f"DEBUG: Contraseña para '{username_lower}' guardada en el archivo config.yaml.")
                print(f"DEBUG: Verificado hash en archivo después de guardar: {current_config['credentials']['usernames'][username_lower]['password']}")
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
        ### CAMBIO AQUÍ: Añadido clear_on_submit=True para limpiar el formulario ###
        with st.form(key='register_form', clear_on_submit=True):
            st.markdown("### Formulario de Registro")
            reg_first_name = st.text_input("Nombre:", key="reg_first_name_input")
            reg_last_name = st.text_input("Apellido:", key="reg_last_name_input")
            reg_email = st.text_input("Correo Electrónico:", key="reg_email_input")
            reg_username = st.text_input("Nombre de Usuario:", key="reg_username_input")
            reg_password = st.text_input("Contraseña:", type="password", key="reg_password_input")
            reg_repeat_password = st.text_input("Repetir Contraseña:", type="password", key="reg_repeat_password_input")
            reg_password_hint = st.text_input("Ayuda en caso de olvidar contraseña (opcional):", key="reg_password_hint_input")
            submit_register_button = st.form_submit_button("Registrarse")

            if submit_register_button:
                if not (reg_first_name and reg_last_name and reg_email and reg_username and reg_password and reg_repeat_password):
                    st.error("Por favor, completa todos los campos requeridos para el registro.")
                    st.stop()
                if reg_password != reg_repeat_password:
                    st.error("Las contraseñas no coinciden.")
                    st.stop()
                if not reg_email.endswith('@ing.unrc.edu.ar'):
                    st.error("Error: Solo se permiten registros con correos electrónicos de '@ing.unrc.edu.ar'.")
                    st.stop()

                username_to_register = reg_username.lower()

                current_config_for_register_check = load_config_local()
                if not current_config_for_register_check:
                    st.error("Error al cargar la configuración para verificar usuarios existentes.")
                    st.stop()

                if username_to_register in current_config_for_register_check['credentials']['usernames']:
                    st.error(f"El nombre de usuario '{reg_username}' ya está en uso. Por favor, elige otro.")
                    st.stop()
                
                for existing_user, user_data in current_config_for_register_check['credentials']['usernames'].items():
                    if user_data.get('email', '').lower() == reg_email.lower():
                        st.error(f"Ya existe una cuenta registrada con el correo electrónico '{reg_email}'.")
                        st.stop()

                hashed_password = bcrypt.hashpw(reg_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                config_data_to_update = load_config_local()
                if not config_data_to_update:
                    st.error("Error: No se pudo recargar la configuración para guardar el nuevo usuario.")
                    st.stop()

                config_data_to_update['credentials']['usernames'][username_to_register] = {
                    'email': reg_email,
                    'first_name': reg_first_name,
                    'last_name': reg_last_name,
                    'password': hashed_password,
                    'password_hint': reg_password_hint if reg_password_hint else None,
                    'logged_in': False,
                    'roles': None
                }
                
                if not save_config_local(config_data_to_update):
                    st.error("Error: No se pudo guardar el nuevo usuario en config.yaml.")
                    st.stop()

                usuarios_path = USUARIOS_FILE
                nuevo_usuario_data = {
                    "login_email": reg_email,
                    "nombre": f"{reg_first_name} {reg_last_name}".strip(),
                    "alert_email": reg_email,
                    "recibir_notificaciones": recibir_notificaciones
                }

                try:
                    usuarios_data = []
                    if os.path.exists(usuarios_path):
                        with open(usuarios_path, "r", encoding="utf-8") as f:
                            usuarios_data = json.load(f)
                    
                    user_exists_in_usuarios_json = False
                    for i, u in enumerate(usuarios_data):
                        if u.get('login_email', '').lower() == reg_email.lower():
                            usuarios_data[i] = nuevo_usuario_data
                            user_exists_in_usuarios_json = True
                            break
                    if not user_exists_in_usuarios_json:
                        usuarios_data.append(nuevo_usuario_data)

                    with open(usuarios_path, "w", encoding="utf-8") as f:
                        json.dump(usuarios_data, f, indent=4)
                    print(f"DEBUG: Preferencias de notificación guardadas para {reg_email} en usuarios.json.")

                    st.session_state['just_registered'] = True
                    st.rerun()

                except Exception as e:
                    st.error(f"Error al guardar preferencias de notificación en usuarios.json: {e}")
                    if username_to_register in config_data_to_update['credentials']['usernames']:
                        del config_data_to_update['credentials']['usernames'][username_to_register]
                        save_config_local(config_data_to_update)
                    st.stop()

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
if 'password_changed_success' not in st.session_state:
    st.session_state['password_changed_success'] = False

if st.session_state.get('just_registered', False):
    st.success("✅ ¡Usuario creado exitosamente! Por favor, inicia sesión.")
    del st.session_state['just_registered']

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
        if reset_info['expiry'] > now: # Volvemos a chequear expiración
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
                                st.query_params.pop("token") # Limpiar el token de la URL
                                # Reinicializar estado de sesión para forzar re-login
                                st.session_state['authentication_status'] = None
                                st.session_state['username'] = None
                                st.session_state['name'] = None
                                st.session_state['email'] = None
                                st.session_state['roles'] = None
                                st.rerun() # Recargar para ir a la pantalla de login limpia
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
            st.query_params.pop("token") # Limpiar el token de la URL
            st.rerun()
    else:
        st.error("Token de restablecimiento inválido o ya utilizado. Por favor, solicita uno nuevo.")
        print("DEBUG: Token no encontrado en st.session_state.reset_tokens. Probablemente ya usado o inválido.")
        st.query_params.pop("token") # Limpiar el token de la URL
        st.rerun()
    
else:
    # 2. Si NO hay token en la URL y el usuario no está autenticado, mostrar el formulario de login principal.
    if st.session_state['authentication_status'] != True:
        if st.session_state.get('password_changed_success', False):
            st.success("Contraseña cambiada correctamente. Por favor, inicia sesión con tu nueva contraseña.")
            st.session_state['password_changed_success'] = False # Limpiar la bandera
            print("DEBUG: Mensaje de contraseña cambiada mostrado en login.")

        print("DEBUG: Intentando renderizar formulario de login.")
        with st.form(key='login_form'):
            st.markdown("## Login")
            login_username = st.text_input("Username", key="login_username_input")
            login_password = st.text_input("Password", type="password", key="login_password_input")
            submit_login_button = st.form_submit_button("Iniciar Sesión")

            if submit_login_button:
                login_username_normalized = login_username.lower()

                print(f"DEBUG: Formulario de login enviado para usuario: {login_username_normalized}")
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

                user_credentials = current_config_for_login['credentials']['usernames'].get(login_username_normalized)
                
                if user_credentials and 'password' in user_credentials:
                    stored_hashed_password = user_credentials['password']
                    try:
                        if isinstance(stored_hashed_password, str):
                            stored_hashed_password = stored_hashed_password.encode('utf-8')
                        
                        if bcrypt.checkpw(login_password.encode('utf-8'), stored_hashed_password):
                            st.session_state['authentication_status'] = True
                            st.session_state['username'] = login_username_normalized # Guardar normalizado
                            st.session_state['name'] = user_credentials.get('first_name', login_username_normalized)
                            st.session_state['email'] = user_credentials.get('email')
                            st.session_state['roles'] = user_credentials.get('roles')
                            st.success(f"Bienvenido, {st.session_state['name']}!")
                            print(f"DEBUG: Autenticación exitosa para {login_username_normalized}. Estado: True, Email: {st.session_state['email']}, Rol: {st.session_state['roles']}")
                            st.rerun()
                        else:
                            st.session_state['authentication_status'] = False
                            st.session_state['username'] = None
                            st.session_state['name'] = None
                            st.session_state['email'] = None
                            st.session_state['roles'] = None
                            st.error("Usuario/Contraseña incorrecta.")
                            print(f"DEBUG: Contraseña incorrecta para {login_username_normalized}.")
                    except Exception as e:
                        st.session_state['authentication_status'] = False
                        st.session_state['username'] = None
                        st.session_state['name'] = None
                        st.session_state['email'] = None
                        st.session_state['roles'] = None
                        st.error("Error en la verificación de contraseña. Intenta de nuevo.")
                        print(f"DEBUG: Error durante bcrypt.checkpw para {login_username_normalized}: {e}")
                else:
                    st.session_state['authentication_status'] = False
                    st.session_state['username'] = None
                    st.session_state['name'] = None
                    st.session_state['email'] = None
                    st.session_state['roles'] = None
                    st.error("Usuario/Contraseña incorrecta.")
                    print(f"DEBUG: Usuario '{login_username_normalized}' no encontrado o sin contraseña.")
        
        if st.session_state['authentication_status'] is None:
            st.warning("Por favor, ingresá tu Usuario y Contraseña")

        st.markdown("---")
        st.subheader("[Manual de Usuario](http://localhost:8000/)")
        st.markdown("---")
        st.subheader("¿Olvidaste tu contraseña?")
        with st.form("forgot_password_form"):
            st.write("Ingresa tu nombre de usuario para restablecer la contraseña.")
            forgot_username_input = st.text_input("Nombre de Usuario", key="forgot_username_input_widget")
            submit_forgot_password = st.form_submit_button("Solicitar Restablecimiento")

            if submit_forgot_password:
                forgot_username_input_normalized = forgot_username_input.lower()

                print(f"DEBUG: Solicitud de restablecimiento para usuario: {forgot_username_input_normalized}")
                if forgot_username_input_normalized:
                    user_found = False
                    user_email = None
                    current_config_for_reset = load_config_local()
                    if not current_config_for_reset:
                        st.error("Error: No se pudo cargar la configuración para restablecer contraseña.")
                        st.stop()

                    if forgot_username_input_normalized in current_config_for_reset['credentials']['usernames']:
                        user_data_from_config = current_config_for_reset['credentials']['usernames'][forgot_username_input_normalized]
                        user_email = user_data_from_config.get('email')
                        user_found = True
                        print(f"DEBUG: Usuario '{forgot_username_input_normalized}' encontrado en config.yaml con email: {user_email}")
                    
                    if not user_found and os.path.exists(USUARIOS_FILE):
                        try:
                            with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
                                usuarios_data = json.load(f)
                            for u in usuarios_data:
                                if u.get('login_email') and u['login_email'].lower() == forgot_username_input_normalized:
                                    user_email = u.get('alert_email') or u.get('login_email')
                                    if user_email:
                                        user_found = True
                                        print(f"DEBUG: Usuario '{forgot_username_input_normalized}' encontrado en usuarios.json con email: {user_email}")
                                        break
                        except Exception as e:
                            st.error(f"Error al leer usuarios.json: {e}")
                            print(f"DEBUG: Error al leer usuarios.json: {e}")

                    if user_found and user_email:
                        reset_token = secrets.token_urlsafe(32)
                        expiry_time = datetime.now() + timedelta(minutes=15)
                        print(f"DEBUG: Token generado: {reset_token}, expira en: {expiry_time}")

                        st.session_state.reset_tokens[reset_token] = {
                            'username': forgot_username_input_normalized, # Guardar normalizado
                            'email': user_email,
                            'expiry': expiry_time
                        }
                        save_reset_tokens(st.session_state.reset_tokens)

                        send_reset_password_email_callback(
                            forgot_username_input_normalized, # Pasar normalizado al correo
                            user_email,
                            reset_token
                        )
                        st.success("Si el nombre de usuario existe y tiene un correo electrónico válido, se ha enviado un enlace de restablecimiento.")
                    else:
                        st.error("Nombre de usuario no encontrado o no tiene un correo electrónico asociado para restablecer la contraseña.")
                        print(f"DEBUG: Usuario '{forgot_username_input_normalized}' no encontrado o sin email asociado.")
                else:
                    st.error("Por favor, ingresa tu nombre de usuario.")
                    print("DEBUG: Campo de nombre de usuario vacío en solicitud de restablecimiento.")
        
        display_register_form()
    else: # Si authentication_status es True (ya autenticado)
        with st.sidebar:
            st.markdown("---")
            st.write(f"Usuario: **{st.session_state['name']}**")
            # Mostramos el rol, si no tiene, es 'normal'. Usamos capitalize() para que se vea mejor.
            rol_usuario = st.session_state.get('roles', 'normal') or 'normal'
            st.write(f"Rol: **{rol_usuario.capitalize()}**")
            
        authenticator.logout("Cerrar Sesión", "sidebar")
        app_final()
