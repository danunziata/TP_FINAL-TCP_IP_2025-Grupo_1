import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
from influxdb_client import InfluxDBClient
import json
import subprocess
import yaml
from yaml.loader import SafeLoader
from pathlib import Path
import bcrypt
import time

# --- Configuración de InfluxDB desde variables de entorno ---
INFLUX_URL = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
INFLUX_TOKEN = os.getenv('INFLUXDB_TOKEN', 'token_telegraf')
INFLUX_ORG = os.getenv('INFLUXDB_ORG', 'power_logic')
INFLUX_BUCKET = os.getenv('INFLUXDB_BUCKET', 'mensualx6')

# --- Clientes de archivos de configuración y datos ---
CONFIG_FILE_PATH = Path(__file__).parent / "config.yaml"
USUARIOS_FILE_PATH = Path(__file__).parent / "usuarios.json"
RESET_TOKENS_FILE_PATH = Path(__file__).parent / "reset_tokens.json"

# --- Funciones auxiliares para cargar/guardar archivos ---
def load_config():
    """Carga el archivo config.yaml."""
    try:
        with CONFIG_FILE_PATH.open("r", encoding="utf-8") as f:
            return yaml.load(f, Loader=SafeLoader)
    except Exception as e:
        st.error(f"Error al cargar config.yaml: {e}")
        return None

def save_config(config_data):
    """Guarda el archivo config.yaml."""
    try:
        with CONFIG_FILE_PATH.open("w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False)
        return True
    except Exception as e:
        st.error(f"Error al guardar config.yaml: {e}")
        return False

def load_usuarios():
    """Carga el archivo usuarios.json."""
    if os.path.exists(USUARIOS_FILE_PATH):
        try:
            with USUARIOS_FILE_PATH.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error al cargar usuarios.json: {e}")
            return []
    return []

def save_usuarios(usuarios_data):
    """Guarda el archivo usuarios.json."""
    try:
        with USUARIOS_FILE_PATH.open("w", encoding="utf-8") as f:
            json.dump(usuarios_data, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error al guardar usuarios.json: {e}")
        return False

def load_reset_tokens_file():
    """Carga los tokens de restablecimiento desde el archivo JSON."""
    if os.path.exists(RESET_TOKENS_FILE_PATH):
        try:
            with RESET_TOKENS_FILE_PATH.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Error al cargar reset_tokens.json: {e}. Se iniciará con tokens vacíos.")
            return {}
    return {}

def save_reset_tokens_file(tokens_data):
    """Guarda los tokens de restablecimiento en el archivo JSON."""
    try:
        with RESET_TOKENS_FILE_PATH.open("w", encoding="utf-8") as f:
            json.dump(tokens_data, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error al guardar reset_tokens.json: {e}")
        return False

# --- Cliente de InfluxDB ---
def get_influx_client():
    return InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG
    )

@st.cache_data
def load_data(_file_mod=None, data_version=0):
    """Carga datos reales desde InfluxDB"""
    client = get_influx_client()
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
        'Voltaje General (V)',
        'Corriente L1 (A)', 'Corriente L2 (A)', 'Corriente L3 (A)'
    ]
    
    for col in scale_columns:
        if col in df.columns:
            df[col] = df[col] / 10.0

    return df

# --- Funciones para Alertas y Configuración ---
def mostrar_alertas_activas():
    st.subheader("📋 Últimas Alertas Registradas")
    try:
        if os.path.exists("logs_alertas.json"):
            with open("logs_alertas.json", "r", encoding="utf-8") as f:
                logs = json.load(f)
            if not logs:
                st.info("No se han detectado alertas aún.")
            else:
                df_logs = pd.DataFrame(logs)
                df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp'])
                st.dataframe(df_logs.tail(10).sort_values(by='timestamp', ascending=False),
                             use_container_width=True, height=250)
        else:
            st.info("El archivo 'logs_alertas.json' no existe. No hay alertas registradas.")
    except Exception as e:
        st.error(f"Error al leer el historial de alertas: {e}")

def editar_umbrales_y_notificaciones():
    st.subheader("⚙️ Configuración de Umbrales")
    umbrales_path = "umbral_config.json"
    
    try:
        if os.path.exists(umbrales_path):
            with open(umbrales_path, "r", encoding="utf-8") as f:
                umbrales = json.load(f)
        else:
            umbrales = {}
    except json.JSONDecodeError:
        st.warning("El archivo 'umbral_config.json' está corrupto o vacío. Se inicializará con valores por defecto.")
        umbrales = {}
    
    # Mapeo de nombres internos a nombres amigables para el usuario
    display_names = {
        'voltaje': 'Voltaje',
        'current_l1': 'Corriente L1',
        'active_power': 'Potencia Activa'
    }

    # Valores por defecto, si el umbral_config.json está vacío o faltan claves
    default_thresholds = {
        'voltaje': {'min': 200.0, 'max': 240.0},
        'current_l1': {'min': 0.0, 'max': 50.0},
        'active_power': {'min': 0.0, 'max': 6000.0}
    }

    st.markdown("Ajusta los valores mínimos y máximos para las métricas. Deja vacío si no aplica.")
    
    nuevos_umbrales = {}
    for variable_key, defaults in default_thresholds.items(): # Iteramos sobre las claves internas
        display_name = display_names.get(variable_key, variable_key) # Obtenemos el nombre amigable
        st.write(f"**{display_name}**") # Mostramos el nombre amigable
        col_min, col_max = st.columns(2)
        
        current_min = umbrales.get(variable_key, {}).get('min', defaults.get('min'))
        current_max = umbrales.get(variable_key, {}).get('max', defaults.get('max'))
        
        with col_min:
            new_min = st.number_input(f"Mínimo para {display_name}", value=current_min, format="%.2f", key=f"{variable_key}_min_input")
        with col_max:
            new_max = st.number_input(f"Máximo para {display_name}", value=current_max, format="%.2f", key=f"{variable_key}_max_input")
        
        nuevos_umbrales[variable_key] = {'min': new_min, 'max': new_max} # Guardamos con la clave interna original

    # --- Sección de Notificaciones Generales (Solo para Administradores) ---
    st.divider()
    
    if st.session_state.get('roles') == 'admin':
        st.subheader("✉️ Configuración de Notificaciones Generales")
        config_data = load_config() # Cargar la configuración aquí
        
        if config_data:
            notificaciones_activas = config_data.get("notificaciones_generales", False)
            current_digest_interval = config_data.get("alert_digest_interval_minutes", 60)
        else:
            notificaciones_activas = False
            current_digest_interval = 60

        activar_mail_general = st.checkbox(
            "**Activar envío de correos de alerta (configuración global)**",
            value=notificaciones_activas,
            help="Si esta opción está desactivada, no se enviará ningún correo de alerta a nadie, independientemente de las preferencias individuales."
        )

        new_digest_interval = st.number_input(
            "Frecuencia de Envío de Resumen de Alertas (minutos):",
            min_value=1,
            max_value=10080, # 7 días * 24 horas/día * 60 minutos/hora = 10080 minutos
            value=current_digest_interval,
            help="Cada cuánto tiempo se enviará un único correo con el resumen de todas las alertas detectadas en ese período.",
            key="alert_digest_interval_input"
        )
        
        if st.button("💾 Guardar Configuración", use_container_width=True):
            with open(umbrales_path, "w", encoding="utf-8") as f:
                json.dump(nuevos_umbrales, f, indent=4)
            
            # Usar la config_data cargada y modificarla
            if config_data: # Asegurarse de que config_data no sea None
                config_data['notificaciones_generales'] = activar_mail_general
                config_data['alert_digest_interval_minutes'] = new_digest_interval
                if save_config(config_data): # Guardar y verificar
                    st.success("✅ Configuración de umbrales y notificaciones actualizada correctamente.")
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error("❌ Error al guardar la configuración general.")
            else:
                st.error("❌ No se pudo cargar la configuración para guardar los cambios.")
    else:
        # Si no es admin, solo permitir guardar umbrales, y el botón de guardar es para umbrales.
        # No mostrar la sección de "Configuración de Notificaciones Generales".
        if st.button("💾 Guardar Umbrales", use_container_width=True):
            with open(umbrales_path, "w", encoding="utf-8") as f:
                json.dump(nuevos_umbrales, f, indent=4)
            st.success("✅ Umbrales actualizados correctamente.")
            time.sleep(3)
            st.rerun()



def ejecutar_checker_manual():
    st.subheader("🔍 Ejecutar Análisis Manual de Alertas")
    st.info("Esto ejecutará el script 'checker.py' para revisar las condiciones de alerta en este momento.")
    if st.button("🚨 Ejecutar Checker Ahora", use_container_width=True, type="primary"):
        with st.spinner('Ejecutando checker.py (modo manual)... Esto puede tomar un momento.'):
            try:
                result = subprocess.run(
                    ["python", "checker.py", "--manual-run"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                st.success("¡Análisis completado! Las alertas detectadas se muestran a continuación.")
                st.code(result.stdout)
                
                if "ALERTA" in result.stdout:
                    st.warning("⚠️ Se detectaron condiciones de alerta. Revisa el log de alertas.")
                else:
                    st.info("✅ No se detectaron nuevas alertas en este momento.")
                
                if result.stderr:
                    st.warning("Errores o advertencias del checker.py:\n" + result.stderr)
            except subprocess.CalledProcessError as e:
                st.error(f"El script 'checker.py' terminó con un error (Código: {e.returncode}).")
                st.code(f"Salida estándar:\n{e.stdout}\nErrores:\n{e.stderr}")
            except FileNotFoundError:
                st.error("Error: 'checker.py' no se encontró. Asegúrate de que el archivo existe en el mismo directorio del contenedor de Streamlit.")
            except Exception as e:
                st.error(f"Error inesperado al ejecutar checker.py: {e}")

# --- Nueva función para Editar Perfil ---
def editar_perfil_usuario():
    st.title("👤 Editar Perfil de Usuario")
    st.markdown("**Actualiza tu información personal, preferencias de notificación y contraseña**")
    st.divider()

    usuario_login_email = st.session_state.get("email", None)
    usuario_username = st.session_state.get("username", None)

    if not usuario_login_email or not usuario_username:
        st.warning("No se pudo detectar el email o nombre de usuario del usuario actual. Por favor, asegúrate de haber iniciado sesión correctamente.")
        return

    usuarios = load_usuarios() # Usar función auxiliar
    
    usuario_idx = -1
    usuario_actual_data = None
    for i, u in enumerate(usuarios):
        if u.get("login_email") == usuario_login_email:
            usuario_idx = i
            usuario_actual_data = u
            break
    
    if usuario_actual_data is None:
        st.warning(f"Tu email de login ({usuario_login_email}) no está registrado en 'usuarios.json' como 'login_email'. Por favor, contacta al administrador o regístrate correctamente.")
        return

    st.info(f"Editando perfil para: **{usuario_username}** ({usuario_login_email})")

    st.subheader("Información Personal y Preferencias de Notificación")
    with st.form("edit_profile_form"):
        nuevo_nombre = st.text_input("Nombre:", value=usuario_actual_data.get("nombre", ""), key="perfil_nombre_input")
        
        nuevo_email_alertas = st.text_input(
            "Correo electrónico para alertas:",
            value=usuario_actual_data.get("alert_email", usuario_login_email),
            help="Este es el correo donde recibirás las alertas. No cambia tu email de login.",
            key="perfil_alert_email_input"
        )
        
        estado_notificaciones = usuario_actual_data.get("recibir_notificaciones", False)
        nueva_preferencia_notificacion = st.checkbox("✅ Quiero recibir alertas por email", value=estado_notificaciones, key="perfil_recibir_notificaciones_checkbox")

        submit_profile_changes = st.form_submit_button("💾 Guardar Cambios del Perfil")

        if submit_profile_changes:
            if not nuevo_email_alertas:
                st.error("El correo electrónico para alertas no puede estar vacío.")
                st.stop()
            
            if "@" not in nuevo_email_alertas or "." not in nuevo_email_alertas.split("@")[-1]:
                st.error("Por favor, introduce un formato de correo electrónico válido para alertas.")
                st.stop()

            usuarios[usuario_idx]["nombre"] = nuevo_nombre
            usuarios[usuario_idx]["alert_email"] = nuevo_email_alertas
            usuarios[usuario_idx]["recibir_notificaciones"] = nueva_preferencia_notificacion

            if save_usuarios(usuarios): # Usar función auxiliar
                st.success("Tu perfil ha sido actualizado correctamente.")
                time.sleep(3)
                st.rerun()
            else:
                st.error("❌ Error al guardar los cambios en el perfil.")


    st.subheader("Cambiar Contraseña")
    st.info("Para cambiar tu contraseña, ingresa tu contraseña actual, y luego tu nueva contraseña dos veces.")
    st.info("Si olvidaste tu contraseña, usa la opción '¿Olvidaste tu contraseña?' en la pantalla de inicio de sesión.")
    with st.form("change_password_form"):
        current_password = st.text_input("Contraseña Actual", type="password", key="current_password_input")
        new_password = st.text_input("Nueva Contraseña", type="password", key="new_password_change_input")
        confirm_new_password = st.text_input("Confirmar Nueva Contraseña", type="password", key="confirm_new_password_change_input")
        submit_password_change = st.form_submit_button("Cambiar Contraseña")

        if submit_password_change:
            if not current_password or not new_password or not confirm_new_password:
                st.error("Por favor, completa todos los campos para cambiar la contraseña.")
            elif new_password != confirm_new_password:
                st.error("La nueva contraseña y su confirmación no coinciden.")
            elif new_password == current_password:
                st.warning("La nueva contraseña no puede ser igual a la actual.")
            else:
                current_config = load_config() # Usar función auxiliar
                if not current_config: # Si no se pudo cargar la config
                    return

                username_from_config = st.session_state.get('username')
                if not username_from_config:
                    st.error("No se pudo obtener el nombre de usuario de la sesión para cambiar la contraseña.")
                    return

                user_creds = current_config['credentials']['usernames'].get(username_from_config)
                if user_creds and 'password' in user_creds:
                    stored_hashed_password = user_creds['password']
                    
                    if isinstance(stored_hashed_password, str):
                        stored_hashed_password = stored_hashed_password.encode('utf-8')

                    if bcrypt.checkpw(current_password.encode('utf-8'), stored_hashed_password):
                        new_hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        
                        current_config['credentials']['usernames'][username_from_config]['password'] = new_hashed_password
                        
                        if save_config(current_config): # Usar función auxiliar
                            st.session_state['password_changed_success'] = True

                            st.session_state['authentication_status'] = None
                            st.session_state['username'] = None
                            st.session_state['name'] = None
                            st.session_state['email'] = None
                            st.session_state['roles'] = None # Limpiar el rol también
                            st.rerun()
                        else:
                            st.error(f"Error al guardar la nueva contraseña en config.yaml.")
                    else:
                        st.error("La contraseña actual es incorrecta. Por favor, inténtalo de nuevo.")
                else:
                    st.error("No se encontraron credenciales de usuario para cambiar la contraseña. Contacta al administrador.")


# --- Función para Gestionar Usuarios (solo para administradores) ---
def gestionar_usuarios():
    st.title("👥 Gestión de Usuarios")
    st.markdown("**Administra los usuarios del sistema (eliminar usuarios)**")
    st.divider()

    # Verificar si el usuario actual es administrador
    if st.session_state.get('roles') != 'admin':
        st.warning("🚫 Acceso denegado. Esta sección es solo para administradores.")
        return

    st.subheader("Lista de Usuarios Registrados")

    config_data = load_config()
    usuarios_data = load_usuarios()
    reset_tokens_data = load_reset_tokens_file() # Cargar tokens de restablecimiento

    if not config_data or not usuarios_data:
        st.error("No se pudieron cargar los datos de configuración o de usuarios.")
        return

    usernames_in_config = config_data['credentials']['usernames']
    
    # Crear una lista consolidada de usuarios para mostrar
    display_users = []
    for username, creds in usernames_in_config.items():
        user_info = {
            "Username": username,
            "Nombre Completo": f"{creds.get('first_name', '')} {creds.get('last_name', '')}".strip(),
            "Email de Login": creds.get('email', 'N/A'),
            "Rol": creds.get('roles', 'normal') or 'normal' # 'null' de YAML se convierte a None, lo mapeamos a 'normal'
        }
        # Añadir info de usuarios.json si existe
        matching_user_in_usuarios = next((u for u in usuarios_data if u.get('login_email') == creds.get('email')), None)
        if matching_user_in_usuarios:
            user_info["Email de Alerta"] = matching_user_in_usuarios.get('alert_email', 'N/A')
            user_info["Recibe Notificaciones"] = matching_user_in_usuarios.get('recibir_notificaciones', False)
        else:
            user_info["Email de Alerta"] = 'N/A (no en usuarios.json)'
            user_info["Recibe Notificaciones"] = False

        display_users.append(user_info)
    
    df_users = pd.DataFrame(display_users)
    st.dataframe(df_users, use_container_width=True)

    st.subheader("Eliminar Usuario")
    st.warning("🚨 ¡CUIDADO! Esta acción eliminará permanentemente al usuario del sistema.")

    users_to_delete = [user['Username'] for user in display_users if user['Rol'] != 'admin'] # No permitir eliminar administradores
    
    if st.session_state.get('username') == 'ipsepadmin': # Asegurar que el admin no se pueda eliminar a sí mismo
        users_to_delete = [u for u in users_to_delete if u != 'ipsepadmin']


    if not users_to_delete:
        st.info("No hay usuarios no-admin para eliminar.")
        return

    user_to_delete = st.selectbox("Selecciona un usuario para eliminar:", options=[""] + users_to_delete, key="delete_user_selectbox")

    if user_to_delete:
        confirm_delete = st.checkbox(f"Confirmo que deseo eliminar al usuario: **{user_to_delete}**", key="confirm_delete_checkbox")
        if confirm_delete:
            if st.button(f"🔴 Eliminar Usuario {user_to_delete} PERMANENTEMENTE", type="secondary", use_container_width=True):
                # --- Lógica de Eliminación ---
                # 1. Eliminar de config.yaml
                if user_to_delete in config_data['credentials']['usernames']:
                    deleted_user_email = config_data['credentials']['usernames'][user_to_delete].get('email')
                    del config_data['credentials']['usernames'][user_to_delete]
                    if not save_config(config_data):
                        st.error("❌ Error al eliminar usuario de config.yaml.")
                        st.rerun() # Detener para mostrar el error
                else:
                    st.warning(f"Usuario {user_to_delete} no encontrado en config.yaml. Continuando con usuarios.json...")

                # 2. Eliminar de usuarios.json
                if deleted_user_email:
                    usuarios_data = [u for u in usuarios_data if u.get('login_email') != deleted_user_email]
                    if not save_usuarios(usuarios_data):
                        st.error("❌ Error al eliminar usuario de usuarios.json.")
                        st.rerun() # Detener para mostrar el error
                else:
                    st.warning(f"No se encontró email de login para {user_to_delete} en config.yaml, no se pudo eliminar de usuarios.json.")

                # 3. Limpiar tokens de restablecimiento asociados
                if reset_tokens_data:
                    tokens_to_keep = {token: info for token, info in reset_tokens_data.items() if info.get('username') != user_to_delete}
                    if len(tokens_to_keep) < len(reset_tokens_data): # Si se eliminó algún token
                        if not save_reset_tokens_file(tokens_to_keep):
                            st.warning("⚠️ Error al limpiar tokens de restablecimiento asociados.")
                
                st.success(f"✅ Usuario '{user_to_delete}' eliminado exitosamente y datos asociados limpiados.")
                time.sleep(3)
                st.rerun() # Recargar la página para actualizar la lista de usuarios

# --- Funciones de Gráficos y Dashboard (sin cambios) ---
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

def create_metrics_dashboard(data):
    col1, col2, col3, col4 = st.columns(4)
    
    voltage_cols = [col for col in data.columns if 'Voltaje' in col and col != 'timestamp']
    if voltage_cols:
        avg_voltage = data[voltage_cols].mean().mean()
        col1.metric("Voltaje Promedio", f"{avg_voltage:.1f} V")
    
    current_cols = [col for col in data.columns if 'Corriente' in col]
    if current_cols:
        avg_current = data[current_cols].mean().mean()
        col2.metric("Corriente Promedio", f"{avg_current:.2f} A")
    
    if 'Potencia Activa (W)' in data.columns:
        avg_power = data['Potencia Activa (W)'].mean()
        max_power = data['Potencia Activa (W)'].max()
        col3.metric("Potencia Promedio", f"{avg_power:.0f} W")
        col4.metric("Potencia Máxima", f"{max_power:.0f} W")

def main():
    # Inicializar session state
    if 'data_version' not in st.session_state:
        st.session_state.data_version = 0
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()
    
    if st.session_state.get('email') is None or st.session_state.get('username') is None:
        st.error("No se pudo detectar la sesión del usuario. Por favor, asegúrate de haber iniciado sesión correctamente.")
        st.stop()

    st.sidebar.title("Menú Principal")
    
    # Opciones de navegación para todos los usuarios
    navigation_options = ["📈 Dashboard Principal", "🔔 Alertas y Logs", "👤 Editar Perfil"]
    
    # Si el usuario es administrador, añadir la opción de Gestión de Usuarios
    if st.session_state.get('roles') == 'admin':
        navigation_options.append("👥 Gestión de Usuarios") # Nueva opción para administradores

    seccion = st.sidebar.radio(
        "Navegar:",
        navigation_options, # Usar las opciones de navegación dinámicas
        index=0
    )

    if seccion == "📈 Dashboard Principal":
        st.title("📊 Sistema de Monitoreo PowerLogic 4000")
        st.markdown("**Visualización completa de parámetros eléctricos** | Schneider Electric™")
        st.divider()

        with st.spinner('Cargando datos desde InfluxDB...'):
            df = load_data(None, st.session_state.data_version)

        if df is None or df.empty:
            st.error("❌ No se pudieron cargar los datos de InfluxDB.")
            st.info("Verifica la conexión a InfluxDB y que el bucket 'mensualx6' contenga datos.")
            
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

        st.session_state.last_update = datetime.now()

        with st.sidebar:
            st.header("⚙️ Configuración del Dashboard")
            
            if st.button("🔄 Actualizar Datos", use_container_width=True, help="Recargar datos desde InfluxDB"):
                with st.spinner('Actualizando datos desde InfluxDB...'):
                    st.session_state.data_version += 1
                    load_data.clear()
                    st.success("¡Datos actualizados exitosamente!")
                    st.rerun()
            
            st.caption(f"🕒 Última actualización: {st.session_state.last_update.strftime('%H:%M:%S')}")
            st.divider()
            
            min_d = df['timestamp'].min().date()
            max_d = df['timestamp'].max().date()
            st.info(f"📅 Datos del {min_d} al {max_d}")
            st.info(f"📊 {len(df)} registros totales")
            
            date_range = st.date_input(
                "Seleccionar rango de fechas:",
                value=(min_d, max_d),
                min_value=min_d,
                max_value=max_d
            )
            
            st.subheader("Métricas a visualizar:")
            
            show_voltages = st.checkbox("Voltajes", value=True)
            show_currents = st.checkbox("Corrientes", value=True)
            show_power = st.checkbox("Potencia Activa", value=True)
            
            st.subheader("📋 Campos disponibles:")
            available_fields = [col for col in df.columns if col != 'timestamp']
            for field in available_fields:
                st.caption(f"• {field}")

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
                st.subheader("📈 Resumen de Métricas")
                create_metrics_dashboard(filtered_df)
                st.divider()
                
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
                
                if show_power:
                    st.subheader("🔋 Potencia Activa")
                    if 'Potencia Activa (W)' in filtered_df.columns:
                        power_chart = create_power_chart(filtered_df)
                        st.plotly_chart(power_chart, use_container_width=True)
                    else:
                        st.info("No hay datos de potencia activa disponibles")
                
                st.divider()
                st.subheader("📊 Datos Detallados")
                
                st.dataframe(filtered_df, height=400, use_container_width=True)
                
                st.subheader("📥 Exportar Datos")
                col1_exp, col2_exp, col3_exp = st.columns([1, 1, 2])
                
                with col1_exp:
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
                
                with col2_exp:
                    from io import BytesIO
                    
                    def create_excel_file(data):
                        data_copy = data.copy(deep=True)
                        
                        def clean_datetime_columns(df_to_clean):
                            for col_name in df_to_clean.columns:
                                if pd.api.types.is_datetime64_any_dtype(df_to_clean[col_name]):
                                    try:
                                        df_to_clean[col_name] = pd.to_datetime(df_to_clean[col_name]).dt.strftime('%Y-%m-%d %H:%M:%S')
                                        df_to_clean[col_name] = pd.to_datetime(df_to_clean[col_name])
                                    except Exception:
                                        df_to_clean[col_name] = df_to_clean[col_name].astype(str)
                            return df_to_clean
                        
                        data_copy = clean_datetime_columns(data_copy)
                        
                        buffer = BytesIO()
                        try:
                            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                data_copy.to_excel(writer, sheet_name='Datos Completos', index=False)
                                
                                summary_data = []
                                for col in data_copy.columns:
                                    if col != 'timestamp' and pd.api.types.is_numeric_dtype(data_copy[col]):
                                        col_data = data_copy[col].dropna()
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
                                
                                voltage_cols = [col for col in data_copy.columns if 'Voltaje' in col]
                                if voltage_cols:
                                    voltage_cols_with_time = ['timestamp'] + voltage_cols
                                    voltage_cols_with_time = [col for col in voltage_cols_with_time if col in data_copy.columns]
                                    if len(voltage_cols_with_time) > 1:
                                        voltage_data = data_copy[voltage_cols_with_time].copy()
                                        voltage_data = clean_datetime_columns(voltage_data)
                                        voltage_data.to_excel(writer, sheet_name='Voltajes', index=False)
                                
                                current_cols = [col for col in data_copy.columns if 'Corriente' in col]
                                if current_cols:
                                    current_cols_with_time = ['timestamp'] + current_cols
                                    current_cols_with_time = [col for col in current_cols_with_time if col in data_copy.columns]
                                    if len(current_cols_with_time) > 1:
                                        current_data = data_copy[current_cols_with_time].copy()
                                        current_data = clean_datetime_columns(current_data)
                                        current_data.to_excel(writer, sheet_name='Corrientes', index=False)
                                
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
                            buffer = BytesIO()
                            fallback_data = data.copy()
                            for col in fallback_data.columns:
                                if pd.api.types.is_datetime64_any_dtype(fallback_data[col]):
                                    fallback_data[col] = fallback_data[col].astype(str)
                            
                            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                fallback_data.to_excel(writer, sheet_name='Datos', index=False)
                            
                            st.warning("Se creó un Excel simplificado debido a problemas con el formato de fechas.")
                            return buffer.getvalue()
                        
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
                
                with col3_exp:
                    st.metric("Total de registros mostrados", len(filtered_df))
                    
                    if st.button("📋 Copiar datos al portapapeles", use_container_width=True):
                        clipboard_data = filtered_df.copy()
                        if 'timestamp' in clipboard_data.columns:
                            clipboard_data['timestamp'] = clipboard_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                        
                        clipboard_text = clipboard_data.to_csv(sep='\t', index=False)
                        st.code(clipboard_text[:500] + "..." if len(clipboard_text) > 500 else clipboard_text,
                                language=None)
                        st.success("¡Datos listos para copiar! Selecciona el texto de arriba y cópialo.")
        else:
            st.error("❌ Por favor selecciona un rango de fechas válido")

    elif seccion == "🔔 Alertas y Logs":
        st.title("🛎️ Sistema de Alertas y Logs")
        st.markdown("**Administra umbrales de alerta y configuración general de notificaciones**")
        st.divider()

        mostrar_alertas_activas()
        st.divider()
        editar_umbrales_y_notificaciones() # Esta función contiene la lógica para mostrar/ocultar la sección
        st.divider()
        ejecutar_checker_manual()
        st.divider()

    elif seccion == "👤 Editar Perfil":
        editar_perfil_usuario()
    
    elif seccion == "👥 Gestión de Usuarios": # Nueva sección para administradores
        gestionar_usuarios()


    st.divider()
    st.caption(f"© {datetime.today().year} Schneider Electric - Power Monitoring System | v2.0 | Datos de InfluxDB")

    if st.sidebar.checkbox("🔧 Modo Debug"):
        st.sidebar.subheader("Debug Info")
        st.sidebar.json({
            "URL": INFLUX_URL,
            "Bucket": INFLUX_BUCKET,
            "Org": INFLUX_ORG,
            "Columnas disponibles": list(df.columns) if 'df' in locals() and df is not None else []
        })

if __name__ == "__main__":
    main()
