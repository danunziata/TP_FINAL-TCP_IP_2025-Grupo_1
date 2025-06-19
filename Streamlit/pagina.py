import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, time # Importar time específicamente
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
        if not CONFIG_FILE_PATH.exists():
            st.error(f"Error: El archivo de configuración '{CONFIG_FILE_PATH}' no existe.")
            return None
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
                # Reorganizar columnas para mostrar franja_horaria
                columns_order = ['timestamp', 'variable', 'valor', 'umbral', 'franja_horaria', 'tipo_ejecucion']
                # Asegurarse de que todas las columnas existan antes de reordenar
                existing_columns = [col for col in columns_order if col in df_logs.columns]
                st.dataframe(df_logs[existing_columns].tail(10).sort_values(by='timestamp', ascending=False),
                             use_container_width=True, height=250)
        else:
            st.info("El archivo 'logs_alertas.json' no existe. No hay alertas registradas.")
    except Exception as e:
        st.error(f"Error al leer el historial de alertas: {e}")

# Mapeo de nombres internos a nombres amigables para el usuario
display_names = {
    'voltaje': 'Voltaje',
    'current_l1': 'Corriente L1',
    'active_power': 'Potencia Activa'
}

# Variables que queremos configurar, con valores por defecto si no existen
default_thresholds_for_display = {
    'voltaje': {'min': 0.0, 'max': 0.0},
    'current_l1': {'min': 0.0, 'max': 0.0},
    'active_power': {'min': 0.0, 'max': 0.0}
}

def display_franja_config_form(current_config, franjas_horarias_data):
    """
    Muestra el formulario para configurar o editar las franjas horarias y sus umbrales.
    `franjas_horarias_data` son los datos actuales de las franjas (pueden ser los default).
    """
    st.subheader("⚙️ Configuración de Umbrales por Franja Horaria")
    
    if not franjas_horarias_data:
        st.warning("No se encontraron franjas horarias configuradas. Por favor, asegúrate de que config.yaml tenga la sección 'franjas_horarias' o 'default_franjas_horarias' para iniciar.")
        return False # Indicar que la configuración no pudo proceder
    
    franjas_names = list(franjas_horarias_data.keys())
    
    if not franjas_names:
        st.error("No hay franjas horarias definidas en la configuración. Por favor, define al menos una en 'config.yaml'.")
        return False

    selected_franja = st.selectbox(
        "Seleccionar Franja Horaria a configurar:",
        options=franjas_names,
        key="franja_horaria_selector"
    )

    current_franja_details = franjas_horarias_data.get(selected_franja, {})
    current_umbrales = current_franja_details.get("umbrales", {})

    # --- INPUTS PARA HORAS DE FRANJA (Solo para Administradores) ---
    st.markdown(f"**Horario de la franja '{selected_franja}'**")
    col_inicio_hora, col_fin_hora = st.columns(2)
    
    # Intentar parsear las horas, si no existen, usar un valor por defecto o 00:00
    try:
        initial_inicio_time = datetime.strptime(current_franja_details.get('inicio_hora', '00:00'), "%H:%M").time()
    except ValueError:
        initial_inicio_time = time(0, 0)
    
    try:
        initial_fin_time = datetime.strptime(current_franja_details.get('fin_hora', '00:00'), "%H:%M").time()
    except ValueError:
        initial_fin_time = time(0, 0)

    # Restringir la edición de horas solo a administradores
    if st.session_state.get('roles') == 'admin':
        with col_inicio_hora:
            new_inicio_time = st.time_input("Hora de Inicio:", value=initial_inicio_time, key=f"{selected_franja}_inicio_time_input")
        with col_fin_hora:
            new_fin_time = st.time_input("Hora de Fin:", value=initial_fin_time, key=f"{selected_franja}_fin_time_input")
    else: # Para usuarios no admin, solo mostrar el horario
        with col_inicio_hora:
            st.info(f"Inicio: {initial_inicio_time.strftime('%H:%M')}")
        with col_fin_hora:
            st.info(f"Fin: {initial_fin_time.strftime('%H:%M')}")
        new_inicio_time = initial_inicio_time # Mantener los valores para el guardado de umbrales
        new_fin_time = initial_fin_time # Mantener los valores para el guardado de umbrales


    st.markdown(f"Ajusta los valores mínimos y máximos para las métricas en la franja **{selected_franja}**.")
    
    nuevos_umbrales_para_franja = {}
    for variable_key in default_thresholds_for_display.keys():
        display_name = display_names.get(variable_key, variable_key)
        st.write(f"**{display_name}**")
        col_min, col_max = st.columns(2)
        
        initial_min = current_umbrales.get(variable_key, {}).get('min', default_thresholds_for_display[variable_key]['min'])
        initial_max = current_umbrales.get(variable_key, {}).get('max', default_thresholds_for_display[variable_key]['max'])
        
        with col_min:
            new_min = st.number_input(f"Mínimo para {display_name}", value=float(initial_min), format="%.2f", key=f"{selected_franja}_{variable_key}_min_input")
        with col_max:
            new_max = st.number_input(f"Máximo para {display_name}", value=float(initial_max), format="%.2f", key=f"{selected_franja}_{variable_key}_max_input")
        
        nuevos_umbrales_para_franja[variable_key] = {'min': new_min, 'max': new_max}

    # --- Sección de Notificaciones Generales (Solo para Administradores) ---
    st.divider()
    
    if st.session_state.get('roles') == 'admin':
        st.subheader("✉️ Configuración de Notificaciones Generales")
        notificaciones_activas = current_config.get("notificaciones_generales", False)
        current_digest_interval = current_config.get("alert_digest_interval_minutes", 1440)
        
        activar_mail_general = st.checkbox(
            "**Activar envío de correos de alerta (configuración global)**",
            value=notificaciones_activas,
            help="Si esta opción está desactivada, no se enviará ningún correo de alerta a nadie, independientemente de las preferencias individuales."
        )

        new_digest_interval = st.number_input(
            "Frecuencia de Envío de Resumen de Alertas (minutos):",
            min_value=1,
            max_value=10080,
            value=current_digest_interval,
            help="Cada cuánto tiempo se enviará un único correo con el resumen de todas las alertas detectadas en ese período.",
            key="alert_digest_interval_input"
        )
        
        if st.button("💾 Guardar Configuración", use_container_width=True):
            franjas_a_guardar = current_config.get('franjas_horarias', {}).copy()
            if selected_franja not in franjas_a_guardar:
                franjas_a_guardar[selected_franja] = franjas_horarias_data.get(selected_franja, {
                    'inicio_hora': '00:00', 'fin_hora': '00:00', 'umbrales': {}
                }).copy()
            
            franjas_a_guardar[selected_franja]['inicio_hora'] = new_inicio_time.strftime("%H:%M")
            franjas_a_guardar[selected_franja]['fin_hora'] = new_fin_time.strftime("%H:%M")
            franjas_a_guardar[selected_franja]['umbrales'] = nuevos_umbrales_para_franja

            current_config['franjas_horarias'] = franjas_a_guardar
            
            current_config['notificaciones_generales'] = activar_mail_general
            current_config['alert_digest_interval_minutes'] = new_digest_interval
            
            if save_config(current_config):
                st.success("✅ Configuración de umbrales y notificaciones actualizada correctamente.")
                time.sleep(3)
                st.rerun()
            else:
                st.error("❌ Error al guardar la configuración general.")
        return True
    else: # Usuario no administrador
        if st.button("💾 Guardar Umbrales (Solo Umbrales)", use_container_width=True):
            config_data_non_admin = load_config()
            if config_data_non_admin:
                franjas_a_guardar_non_admin = config_data_non_admin.get('franjas_horarias', {}).copy()
                if selected_franja in franjas_a_guardar_non_admin:
                    if 'umbrales' not in franjas_a_guardar_non_admin[selected_franja]:
                        franjas_a_guardar_non_admin[selected_franja]['umbrales'] = {}

                    franjas_a_guardar_non_admin[selected_franja]['umbrales'] = nuevos_umbrales_para_franja
                    config_data_non_admin['franjas_horarias'] = franjas_a_guardar_non_admin

                    if save_config(config_data_non_admin):
                        st.success("✅ Umbrales actualizados correctamente.")
                        time.sleep(3)
                        st.rerun()
                    else:
                        st.error("❌ Error al guardar los umbrales.")
                else:
                    st.error(f"❌ La franja horaria '{selected_franja}' no existe en la configuración y no puede ser modificada por un usuario regular.")
            else:
                st.error("❌ No se pudo cargar la configuración para guardar los umbrales.")
        return True


# --- Función para el Wizard de Configuración Inicial de Franjas Horarias ---
def wizard_configuracion_franjas(current_config):
    """
    Wizard para la configuración inicial de franjas horarias.
    Solo para administradores en la primera ejecución.
    """
    st.title("Asistente de Configuración Inicial de Franjas Horarias")
    st.warning("Parece que es la primera vez que configuras las franjas horarias de alerta o no están definidas.")
    st.info("Por favor, configura las franjas horarias y sus umbrales por defecto.")
    st.markdown("Puedes ajustar estos valores más tarde en la sección 'Alertas y Logs'.")

    # Obtener las franjas por defecto de config.yaml
    default_franjas = current_config.get("default_franjas_horarias", {})
    if not default_franjas:
        st.error("Error: No se encontraron franjas horarias por defecto en 'config.yaml'. Por favor, revisa el archivo.")
        return # No se puede continuar sin defaults

    st.subheader("Definición de Franjas Horarias")

    col1, col2, col3, col4 = st.columns(4)

    # Inputs para DIA
    with col1:
        st.markdown("**Franja DIA**")
        dia_inicio = st.time_input("Inicio DIA", value=datetime.strptime(default_franjas['DIA']['inicio_hora'], "%H:%M").time(), key="wiz_dia_inicio")
    with col2:
        st.markdown(" ") # Espacio para alinear
        dia_fin = st.time_input("Fin DIA", value=datetime.strptime(default_franjas['DIA']['fin_hora'], "%H:%M").time(), key="wiz_dia_fin")

    # Inputs para NOCHE
    with col3:
        st.markdown("**Franja NOCHE**")
        noche_inicio = st.time_input("Inicio NOCHE", value=datetime.strptime(default_franjas['NOCHE']['inicio_hora'], "%H:%M").time(), key="wiz_noche_inicio")
    with col4:
        st.markdown(" ") # Espacio para alinear
        noche_fin = st.time_input("Fin NOCHE", value=datetime.strptime(default_franjas['NOCHE']['fin_hora'], "%H:%M").time(), key="wiz_noche_fin")

    st.subheader("Umbrales por Defecto para Franjas")

    # Mostrar y permitir editar los umbrales predefinidos
    nuevas_franjas_config = {}
    
    # Franja DIA
    st.markdown("---")
    st.markdown("**Umbrales para DIA**")
    umbrales_dia = {}
    for variable_key in default_thresholds_for_display.keys():
        display_name = display_names.get(variable_key, variable_key)
        col_min, col_max = st.columns(2)
        with col_min:
            min_val = st.number_input(f"Mínimo {display_name} (DIA)", value=float(default_franjas['DIA']['umbrales'].get(variable_key, {}).get('min', 0.0)), format="%.2f", key=f"wiz_dia_{variable_key}_min")
        with col_max:
            max_val = st.number_input(f"Máximo {display_name} (DIA)", value=float(default_franjas['DIA']['umbrales'].get(variable_key, {}).get('max', 0.0)), format="%.2f", key=f"wiz_dia_{variable_key}_max")
        umbrales_dia[variable_key] = {'min': min_val, 'max': max_val}
    
    nuevas_franjas_config['DIA'] = {
        'inicio_hora': dia_inicio.strftime("%H:%M"),
        'fin_hora': dia_fin.strftime("%H:%M"),
        'umbrales': umbrales_dia
    }

    # Franja NOCHE
    st.markdown("---")
    st.markdown("**Umbrales para NOCHE**")
    umbrales_noche = {}
    for variable_key in default_thresholds_for_display.keys():
        display_name = display_names.get(variable_key, variable_key)
        col_min, col_max = st.columns(2)
        with col_min:
            min_val = st.number_input(f"Mínimo {display_name} (NOCHE)", value=float(default_franjas['NOCHE']['umbrales'].get(variable_key, {}).get('min', 0.0)), format="%.2f", key=f"wiz_noche_{variable_key}_min")
        with col_max:
            max_val = st.number_input(f"Máximo {display_name} (NOCHE)", value=float(default_franjas['NOCHE']['umbrales'].get(variable_key, {}).get('max', 0.0)), format="%.2f", key=f"wiz_noche_{variable_key}_max")
        umbrales_noche[variable_key] = {'min': min_val, 'max': max_val}
    
    nuevas_franjas_config['NOCHE'] = {
        'inicio_hora': noche_inicio.strftime("%H:%M"),
        'fin_hora': noche_fin.strftime("%H:%M"),
        'umbrales': umbrales_noche
    }

    st.markdown("---")
    if st.button("💾 Guardar Configuración Inicial de Franjas", use_container_width=True, type="primary"):
        # Validaciones básicas de solapamiento y orden de horas
        if dia_inicio >= dia_fin:
            st.error("Error: La hora de inicio del DIA debe ser anterior a la hora de fin del DIA.")
            return
        
        # Validar que las franjas cubran las 24 horas y no se superpongan
        dia_inicio_min = dia_inicio.hour * 60 + dia_inicio.minute
        dia_fin_min = dia_fin.hour * 60 + dia_fin.minute
        noche_inicio_min = noche_inicio.hour * 60 + noche_inicio.minute
        noche_fin_min = noche_fin.hour * 60 + noche_fin.minute

        is_valid_cycle = False
        if (dia_fin_min + 1) % 1440 == noche_inicio_min % 1440 and \
           (noche_fin_min + 1) % 1440 == dia_inicio_min % 1440:
           is_valid_cycle = True
        
        if not is_valid_cycle:
            st.warning("Advertencia: Las franjas horarias no cubren un ciclo completo de 24 horas o se superponen. Esto puede causar comportamientos inesperados en las alertas. Por favor, revisa las horas.")

        # Guardar en config.yaml
        current_config['franjas_horarias'] = nuevas_franjas_config
        if save_config(current_config):
            st.success("✅ Franjas horarias configuradas exitosamente. Puedes continuar.")
            time.sleep(2)
            st.rerun()
        else:
            st.error("❌ Error al guardar la configuración de franjas horarias.")


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

# --- Funciones de Edición de Perfil y Gestión de Usuarios ---
def editar_perfil_usuario():
    st.title("👤 Editar Perfil de Usuario")
    st.markdown("**Actualiza tu información personal, preferencias de notificación y contraseña**")
    st.divider()

    usuario_login_email = st.session_state.get("email", None)
    usuario_username = st.session_state.get("username", None)

    if not usuario_login_email or not usuario_username:
        st.warning("No se pudo detectar el email o nombre de usuario del usuario actual. Por favor, asegúrate de haber iniciado sesión correctamente.")
        return

    usuarios = load_usuarios()
    
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

            if save_usuarios(usuarios):
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
                current_config = load_config()
                if not current_config:
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
                        
                        if save_config(current_config):
                            st.session_state['password_changed_success'] = True

                            st.session_state['authentication_status'] = None
                            st.session_state['username'] = None
                            st.session_state['name'] = None
                            st.session_state['email'] = None
                            st.session_state['roles'] = None
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
    reset_tokens_data = load_reset_tokens_file()

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
            "Rol": creds.get('roles', 'normal') or 'normal'
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

    users_to_delete = [user['Username'] for user in display_users if user['Rol'] != 'admin']
    
    if st.session_state.get('username') == 'ipsepadmin':
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
                        st.rerun()
                else:
                    st.warning(f"Usuario {user_to_delete} no encontrado en config.yaml. Continuando con usuarios.json...")

                # 2. Eliminar de usuarios.json
                if deleted_user_email:
                    usuarios_data = [u for u in usuarios_data if u.get('login_email') != deleted_user_email]
                    if not save_usuarios(usuarios_data):
                        st.error("❌ Error al eliminar usuario de usuarios.json.")
                        st.rerun()
                else:
                    st.warning(f"No se encontró email de login para {user_to_delete} en config.yaml, no se pudo eliminar de usuarios.json.")

                # 3. Limpiar tokens de restablecimiento asociados
                if reset_tokens_data:
                    tokens_to_keep = {token: info for token, info in reset_tokens_data.items() if info.get('username') != user_to_delete}
                    if len(tokens_to_keep) < len(reset_tokens_data):
                        if not save_reset_tokens_file(tokens_to_keep):
                            st.warning("⚠️ Error al limpiar tokens de restablecimiento asociados.")
                
                st.success(f"✅ Usuario '{user_to_delete}' eliminado exitosamente y datos asociados limpiados.")
                time.sleep(3)
                st.rerun()

# --- Funciones de Gráficos y Dashboard ---
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

    # --- Lógica de Wizard para configuración inicial de franjas horarias ---
    current_config = load_config()
    if not current_config:
        st.error("Error crítico: No se pudo cargar el archivo de configuración.")
        st.stop()

    # Solo el administrador ve el wizard
    if st.session_state.get('roles') == 'admin':
        # Verificar si 'franjas_horarias' existe y no está vacío
        if not current_config.get('franjas_horarias'):
            wizard_configuracion_franjas(current_config) # Llamada a la función del wizard
            st.stop() # Detener la ejecución del resto del main mientras el wizard está activo
    # --- Fin de la lógica del Wizard ---


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
            
            # --- SECCIÓN ELIMINADA: "Campos disponibles:" ---
            # st.subheader("📋 Campos disponibles:")
            # available_fields = [col for col in df.columns if col != 'timestamp']
            # for field in available_fields:
            #     st.caption(f"• {field}")

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
        
        # Llama a la función de configuración de umbrales
        config_data_for_thresholds = load_config()
        if config_data_for_thresholds:
            # Pasa la sección 'franjas_horarias' si existe, si no, pasa los defaults
            franjas_to_display = config_data_for_thresholds.get('franjas_horarias')
            if not franjas_to_display: # Si 'franjas_horarias' no existe o está vacío
                franjas_to_display = config_data_for_thresholds.get('default_franjas_horarias', {}) # Usar defaults

            display_franja_config_form(config_data_for_thresholds, franjas_to_display)
        else:
            st.error("No se pudo cargar la configuración de franjas horarias.")


        st.divider()
        ejecutar_checker_manual()
        st.divider()

    elif seccion == "👤 Editar Perfil":
        editar_perfil_usuario()
    
    elif seccion == "👥 Gestión de Usuarios": # Nueva sección para administradores
        gestionar_usuarios()


    st.divider()
    st.caption(f"© {datetime.today().year} Schneider Electric - Power Monitoring System | v2.0 | Datos de InfluxDB")

    # Eliminada la checkbox de "Modo Debug"
    # if st.sidebar.checkbox("🔧 Modo Debug"):
    #     st.sidebar.subheader("Debug Info")
    #     st.sidebar.json({
    #         "URL": INFLUX_URL,
    #         "Bucket": INFLUX_BUCKET,
    #         "Org": INFLUX_ORG,
    #         "Columnas disponibles": list(df.columns) if 'df' in locals() and df is not None else []
    #     })

if __name__ == "__main__":
    main()
