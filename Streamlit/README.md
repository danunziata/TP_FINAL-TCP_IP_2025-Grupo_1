# Streamlit Application & Backend Logic

Este directorio contiene la aplicación web principal desarrollada con Streamlit, así como los scripts de backend cruciales para la autenticación, gestión de usuarios, sistema de alertas y envío de notificaciones.

## Propósito

Actúa como la interfaz de usuario para la visualización de datos, la configuración del sistema de alertas y la administración de usuarios. También aloja la lógica de negocio para la verificación de umbrales y el manejo de notificaciones.

## Estructura del Directorio

Streamlit/
├── Dockerfile                      # Define la imagen Docker para la aplicación Streamlit y checker_service
├── login.py                        # Punto de entrada y gestión de autenticación (login, registro, restablecimiento)
├── pagina.py                       # Lógica principal de la aplicación web (dashboard, alertas, perfil, gestión)
├── checker.py                      # Script de verificación de umbrales y envío de alertas
├── emailsender.py                  # Módulo para el envío de correos electrónicos
├── requirements.txt                # Dependencias Python
├── config.yaml                     # Configuración de usuarios, ajustes globales y DEFINICIÓN DE FRANJAS HORARIAS
├── usuarios.json                   # Información adicional de usuarios (emails, preferencias)
├── logs_alertas.json               # Historial de alertas registradas (generado en runtime)
├── reset_tokens.json               # Tokens temporales para restablecimiento de contraseña (generado en runtime)
├── last_digest_sent_state.json     # Marca de tiempo del último resumen de alertas enviado (generado en runtime)
├── pending_alerts_buffer.json      # Buffer de alertas pendientes de envío en el resumen (generado en runtime)
├── reset_password_admin.py         # Herramienta CLI para restablecer contraseñas de admin
└── test_email.py                   # Script de prueba para el envío de correos


## Componentes Principales y su Lógica

### `Dockerfile`

Este `Dockerfile` se utiliza para construir las imágenes Docker para dos servicios: `streamlit` (la interfaz web) y `checker_service` (el proceso de alertas en segundo plano).

### Análisis Línea por Línea y Lógica

```dockerfile
FROM python:3.10-slim
FROM python:3.10-slim: Define la imagen base del contenedor. En este caso, una versión ligera de Python 3.10, que es adecuada para la mayoría de las necesidades del proyecto sin añadir peso innecesario al contenedor.
Dockerfile
WORKDIR /app
WORKDIR /app: Establece /app como el directorio de trabajo predeterminado dentro del contenedor. Todos los comandos subsiguientes (como COPY o RUN) se ejecutarán con /app como su directorio actual.
Dockerfile
COPY login.py pagina.py config.yaml requirements.txt emailsender.py checker.py reset_password_admin.py test_email.py usuarios.json logs_alertas.json last_digest_sent_state.json pending_alerts_buffer.json ./
COPY <archivos_origen> <directorio_destino>: Esta instrucción copia los archivos listados desde el contexto de construcción de Docker (que es el directorio Streamlit/ en tu máquina local) al directorio de trabajo (./, que es /app) dentro del contenedor.
login.py: Es el script principal de autenticación y el punto de entrada de la aplicación Streamlit. Contiene la lógica de login, registro de usuarios y restablecimiento de contraseña.
pagina.py: Es el script que define la interfaz de usuario principal de la aplicación (dashboard, sección de alertas, edición de perfil, gestión de usuarios).
config.yaml: Archivo crucial de configuración que define los usuarios, ajustes globales del sistema (como la activación de notificaciones y el intervalo de resumen) y las definiciones de las franjas horarias con sus respectivos umbrales.
requirements.txt: Este archivo lista todas las librerías de Python de las que dependen los scripts en esta carpeta (login.py, pagina.py, checker.py, emailsender.py, etc.). pip lo utilizará para instalar estas dependencias.
emailsender.py: Un módulo auxiliar que encapsula la lógica para el envío de correos electrónicos a través de la API de Resend.
checker.py: Este script es el "motor" del sistema de alertas. Se ejecuta periódicamente para consultar InfluxDB, verificar umbrales por franja horaria y gestionar el envío de resúmenes de alertas por correo.
reset_password_admin.py: Una herramienta de utilidad de línea de comandos (CLI) que permite a un administrador restablecer manualmente la contraseña de cualquier usuario en el archivo config.yaml.
test_email.py: Un script simple utilizado para realizar pruebas de la funcionalidad de envío de correos electrónicos.
usuarios.json: Este archivo almacena información adicional de los usuarios, como su nombre completo, correo electrónico de login, un correo electrónico alternativo para recibir alertas y su preferencia personal para recibir o no notificaciones.
logs_alertas.json: Es un archivo de registro donde se guarda un historial de todas las alertas que han sido detectadas por el checker.py. Se crea y actualiza dinámicamente en tiempo de ejecución.
last_digest_sent_state.json: Un archivo de estado que almacena la marca de tiempo del último momento en que se envió un correo electrónico de resumen de alertas. Es fundamental para la lógica de intervalos de envío del checker.py. Se crea y actualiza dinámicamente en tiempo de ejecución.
pending_alerts_buffer.json: Este archivo actúa como un "buffer" o cola. Almacena temporalmente las alertas individuales que han sido detectadas por checker.py y están a la espera de ser incluidas en el próximo correo de resumen. Se crea y actualiza dinámicamente en tiempo de ejecución.
Dockerfile
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install ...: Este comando instala todas las librerías de Python especificadas en requirements.txt dentro del entorno del contenedor. El flag --no-cache-dir se utiliza para deshabilitar el caché de pip, lo que ayuda a mantener el tamaño final de la imagen Docker más pequeño.
Dockerfile
EXPOSE 8501
EXPOSE 8501: Esta instrucción informa a Docker que el contenedor espera escuchar en el puerto 8501 en tiempo de ejecución. Es una declaración de intención y ayuda a documentar el puerto de la aplicación; el mapeo real del puerto al host se configura en docker-compose.yml.
Dockerfile
CMD ["streamlit", "run", "login.py"]
CMD ["streamlit", "run", "login.py"]: Este comando define el comando predeterminado que se ejecutará cuando el contenedor se inicie si no se especifica un comando diferente. Lanza la aplicación Streamlit utilizando login.py como el script principal. En tu docker-compose.yml, este CMD está sobrescrito por la instrucción command en los servicios streamlit y checker_service.

login.py (Ex prueba_login.py)
Este script es el punto de entrada principal de la aplicación Streamlit cuando se inicia. Es responsable de la autenticación de usuarios y el enrutamiento a la aplicación principal (pagina.py) una vez autenticado.

Análisis Línea por Línea y Lógica
Python
import os, json, yaml
from yaml.loader import SafeLoader
from pathlib import Path
import streamlit as st
import streamlit_authenticator as stauth
from pagina import main as app_final # Importamos la función main de pagina.py
from emailsender import enviar_alerta # Importamos la función para enviar correos
import secrets # Para generar tokens seguros
from datetime import datetime, timedelta
import bcrypt # Para hashear contraseñas en el formulario manual de reset
Importaciones: Importa las librerías y módulos necesarios.
streamlit, streamlit_authenticator: Para construir la interfaz de usuario y manejar la autenticación.
pagina.py (app_final): La aplicación principal a la que se redirige después del login.
emailsender.py: Para enviar correos de restablecimiento de contraseña.
secrets: Para generar tokens de seguridad aleatorios.
datetime, timedelta: Para manejar fechas y expiraciones de tokens.
bcrypt: Para el hashing seguro de contraseñas.
Python
# Nombres de los archivos
RESET_TOKENS_FILE = "reset_tokens.json"
CONFIG_FILE_PATH = Path(__file__).parent / "config.yaml"
USUARIOS_FILE = "usuarios.json"
Definición de rutas a los archivos de configuración y datos que este script lee/escribe.
Python
# --- Funciones locales para cargar/guardar config.yaml ---
def load_config_local():
    # ... (carga config.yaml) ...
def save_config_local(config_data):
    # ... (guarda config.yaml) ...
Funciones auxiliares para leer y escribir el archivo config.yaml. Se usan localmente en este script para la gestión de usuarios y contraseñas.
Python
# --- Funciones para cargar/guardar tokens de restablecimiento ---
def load_reset_tokens():
    # ... (carga y limpia tokens expirados) ...
def save_reset_tokens(tokens_dict):
    # ... (guarda tokens, convierte datetime a ISO) ...
Funciones para gestionar reset_tokens.json, que almacena los tokens temporales generados para restablecer contraseñas. Incluyen lógica para limpiar tokens expirados.
Python
st.set_page_config(...) # Configuración de la página Streamlit
Configura el título de la pestaña del navegador, el icono, el layout y el estado inicial de la barra lateral.
Python
# --- Carga inicial de configuración ---
config = load_config_local()
# ... (manejo de errores si la configuración no se carga) ...

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    auto_hash=False
)
config = load_config_local(): Carga el config.yaml al inicio de la aplicación.
authenticator = stauth.Authenticate(...): Inicializa el objeto streamlit_authenticator, pasándole las credenciales de los usuarios, la configuración de la cookie de sesión y deshabilitando el auto_hash (porque usamos bcrypt manualmente para más control).
Python
st.session_state.reset_tokens = load_reset_tokens()
Carga los tokens de restablecimiento existentes en la sesión de Streamlit al inicio.
Python
# --- Funciones de Callback para Reseteo de Contraseña ---
def send_reset_password_email_callback(username, email, key):
    # ... (construye enlace de reset y llama a enviar_alerta) ...
def update_password_callback(username, new_hashed_password):
    # ... (actualiza la contraseña hasheada en config.yaml, normaliza username a minúsculas) ...
send_reset_password_email_callback: Construye el enlace de restablecimiento de contraseña usando el token y la URL de la aplicación, y lo envía por correo electrónico.
update_password_callback: Actualiza la contraseña hasheada de un usuario en config.yaml después de un restablecimiento exitoso. Importante: Normaliza el nombre de usuario a minúsculas antes de buscarlo en config.yaml para asegurar la consistencia.
Python
# --- Función auxiliar para mostrar el formulario de registro ---
def display_register_form():
    # ... (formulario de registro) ...
    # Lógica de normalización del username y validación de email @ing.unrc.edu.ar
    # Guarda el nuevo usuario en config.yaml y usuarios.json
Formulario de Registro Personalizado: En lugar de usar el formulario register_user de streamlit_authenticator directamente (que tiene limitaciones para la normalización del nombre de usuario y la validación de dominio), se construye un formulario manual.
Normalización del Username: El nombre de usuario ingresado por el usuario se convierte a minúsculas (username_to_register = reg_username.lower()) antes de ser guardado en config.yaml. Esto resuelve el problema de las mayúsculas/minúsculas en el login.
Validación de Email: Verifica que el correo electrónico pertenezca al dominio @ing.unrc.edu.ar. Si no es así, el registro falla y se revierte.
Persistencia: Guarda las credenciales en config.yaml y las preferencias de notificación en usuarios.json. Maneja la actualización de usuarios existentes y la adición de nuevos.
Python
# --- Lógica Principal de Autenticación y Enrutamiento ---
query_params = st.query_params
# ... (inicialización de session_state) ...

if "token" in query_params:
    # ... (Manejo del flujo de restablecimiento de contraseña si hay un token en la URL) ...
else:
    if st.session_state['authentication_status'] != True:
        # ... (Formulario de Login) ...
        # Lógica de normalización del username para el login
        # ... (Formulario de Olvidaste tu Contraseña) ...
        # ... (Llamada a display_register_form()) ...
    else: # Si authentication_status es True (ya autenticado)
        authenticator.logout("Cerrar Sesión", "sidebar")
        app_final() # Ejecuta la función main() de pagina.py
Manejo de URL con Token: Detecta si hay un token en los parámetros de la URL (cuando un usuario hace clic en un enlace de restablecimiento de contraseña). Si lo hay, muestra un formulario para establecer una nueva contraseña y valida el token y su expiración.
Formulario de Login: Si no hay token y el usuario no está autenticado, muestra el formulario de login.
Normalización de Username en Login: El nombre de usuario ingresado en el login también se convierte a minúsculas (login_username.lower()) antes de ser verificado contra las credenciales en config.yaml. Esto asegura que el login funcione sin importar la capitalización que use el usuario al escribir su nombre de usuario.
Formulario "Olvidaste tu contraseña?": Permite a los usuarios solicitar un enlace de restablecimiento.
Redirección a app_final(): Si el usuario está autenticado (st.session_state['authentication_status'] == True), el script llama a app_final() (que es la función main de pagina.py) para renderizar la aplicación principal.
Flujo de Funcionamiento (login.py)
Al iniciar la aplicación Streamlit, se ejecuta login.py.
Se carga la configuración de config.yaml y se inicializa el objeto authenticator.
Si la URL contiene un token de restablecimiento, se activa el flujo de restablecimiento de contraseña. El usuario establece una nueva contraseña y se actualiza en config.yaml.
Si no hay token y el usuario no está autenticado, se muestran los formularios de Login, "Olvidaste tu contraseña?" y "Registrar nuevo usuario".
Login: El usuario ingresa credenciales, que son validadas contra config.yaml. Si son correctas, se establece el estado de autenticación en st.session_state.
Registro: El usuario completa el formulario. El script valida el dominio del email, normaliza el nombre de usuario a minúsculas, hashea la contraseña y guarda el nuevo usuario en config.yaml y sus preferencias en usuarios.json.
Olvido de Contraseña: El usuario ingresa su nombre de usuario. Se genera un token, se guarda en reset_tokens.json y se envía un correo con un enlace de restablecimiento.
Una vez autenticado, login.py cede el control a la función main() de pagina.py (app_final()) para mostrar la interfaz de la aplicación.
Desde cualquier página de la aplicación, el botón "Cerrar Sesión" en la barra lateral (authenticator.logout) puede ser usado para cerrar la sesión, volviendo a la pantalla de login.
Streamlit/pagina.py (Actualizado con wizard de franjas y sin debug mode)
Este es el script principal de la interfaz de usuario de tu aplicación Streamlit. Contiene el dashboard, la sección de alertas y logs, y la gestión de usuarios/perfiles.

Análisis Línea por Línea y Lógica
Python
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
Importaciones: Importa las librerías necesarias. Destaca time de datetime para el manejo de horas sin fecha, InfluxDBClient para interactuar con InfluxDB, json, subprocess (para ejecutar checker.py manualmente), yaml para config.yaml, Path para rutas de archivos, y bcrypt si se usa para cambio de contraseña.
Python
# --- Configuración de InfluxDB desde variables de entorno ---
INFLUX_URL = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
INFLUX_TOKEN = os.getenv('INFLUXDB_TOKEN', 'token_telegraf')
INFLUX_ORG = os.getenv('INFLUXDB_ORG', 'power_logic')
INFLUX_BUCKET = os.getenv('INFLUXDB_BUCKET', 'mensualx6')
Define las variables de conexión a InfluxDB, tomándolas de las variables de entorno (definidas en docker-compose.yml) o usando valores por defecto.
Python
# --- Clientes de archivos de configuración y datos ---
CONFIG_FILE_PATH = Path(__file__).parent / "config.yaml"
USUARIOS_FILE_PATH = Path(__file__).parent / "usuarios.json"
RESET_TOKENS_FILE_PATH = Path(__file__).parent / "reset_tokens.json"
Define las rutas a los archivos de configuración y datos utilizados por este script.
Python
# --- Funciones auxiliares para cargar/guardar archivos (LOAD/SAVE) ---
def load_config(): ...
def save_config(config_data): ...
def load_usuarios(): ...
def save_usuarios(usuarios_data): ...
def load_reset_tokens_file(): ...
def save_reset_tokens_file(tokens_data): ...
Un conjunto de funciones auxiliares genéricas para cargar y guardar los diferentes archivos de configuración y datos (config.yaml, usuarios.json, reset_tokens.json).
Python
# --- Cliente de InfluxDB ---
def get_influx_client(): ...
@st.cache_data
def load_data(_file_mod=None, data_version=0): ...
get_influx_client(): Retorna una instancia del cliente de InfluxDB.
load_data(): Es la función principal para cargar datos del bucket mensualx6 de InfluxDB para el dashboard.
@st.cache_data: Decorador de Streamlit que almacena en caché los resultados de la función. Esto acelera la aplicación al evitar recargar los datos de InfluxDB en cada interacción, a menos que el data_version cambie.
Realiza una consulta Flux para obtener datos de los últimos 30 días, pivota los datos y los renombra.
Aplica la escala (/ 10.0) a los voltajes y corrientes, según el simulador Modbus.
Funciones de UI y Lógica Específica
(Estas funciones se han movido a la parte superior del archivo para evitar NameError)

mostrar_alertas_activas()
Python
def mostrar_alertas_activas():
    st.subheader("📋 Últimas Alertas Registradas")
    # ... (lee logs_alertas.json) ...
    # Reorganizar columnas para mostrar franja_horaria
    columns_order = ['timestamp', 'variable', 'valor', 'umbral', 'franja_horaria', 'tipo_ejecucion']
    # ... (muestra el DataFrame) ...
Lee el archivo logs_alertas.json y muestra las últimas 10 alertas registradas en una tabla.
Importante: La tabla ahora incluye la columna franja_horaria.
display_franja_config_form(current_config, franjas_horarias_data)
Python
# Mapeo de nombres internos a nombres amigables para el usuario
display_names = { ... }
default_thresholds_for_display = { ... }

def display_franja_config_form(current_config, franjas_horarias_data):
    st.subheader("⚙️ Configuración de Umbrales por Franja Horaria")
    # ... (manejo de franjas_horarias_data) ...
    selected_franja = st.selectbox(...) # Selector de franja
    current_franja_details = ...
    current_umbrales = ...

    # --- INPUTS PARA HORAS DE FRANJA (Solo para Administradores) ---
    st.markdown(f"**Horario de la franja '{selected_franja}'**")
    col_inicio_hora, col_fin_hora = st.columns(2)
    # Lógica para inicializar y restringir la edición de horas a administradores
    if st.session_state.get('roles') == 'admin':
        new_inicio_time = st.time_input("Hora de Inicio:", ...)
        new_fin_time = st.time_input("Hora de Fin:", ...)
    else: # Para usuarios no admin, solo mostrar el horario
        st.info(f"Inicio: {initial_inicio_time.strftime('%H:%M')}")
        st.info(f"Fin: {initial_fin_time.strftime('%H:%M')}")
        new_inicio_time = initial_inicio_time # Mantener los valores para el guardado de umbrales
        new_fin_time = initial_fin_time # Mantener los valores para el guardado de umbrales

    st.markdown(f"Ajusta los valores mínimos y máximos para las métricas en la franja **{selected_franja}**.")
    # ... (inputs para umbrales min/max de cada variable) ...
    
    # --- Sección de Notificaciones Generales (Solo para Administradores) ---
    if st.session_state.get('roles') == 'admin':
        st.subheader("✉️ Configuración de Notificaciones Generales")
        # ... (checkbox para activar envío global y number_input para Frecuencia de Envío de Resumen de Alertas) ...
        if st.button("💾 Guardar Configuración", use_container_width=True):
            # ... (lógica de guardado de umbrales y horarios de franja en current_config['franjas_horarias']) ...
            # ... (lógica de guardado de notificaciones_generales y alert_digest_interval_minutes) ...
    else: # Usuario no administrador
        if st.button("💾 Guardar Umbrales (Solo Umbrales)", use_container_width=True):
            # ... (lógica de guardado de umbrales, solo umbrales, sin tocar horarios ni notificaciones generales) ...
Esta es la función central para configurar los umbrales de alerta y las notificaciones.
Selector de Franja: Permite al usuario seleccionar una franja horaria (DIA, NOCHE, etc.) para configurar sus umbrales.
Edición de Horarios de Franja (Solo Admin): Muestra st.time_input para que el administrador pueda cambiar la hora de inicio y fin de la franja seleccionada. Si el usuario no es administrador, solo se muestran las horas actuales.
Inputs de Umbrales: Permite ajustar los valores mínimos y máximos para voltaje, current_l1, y active_power para la franja seleccionada.
Configuración de Notificaciones Generales (Solo Admin): La sección para activar/desactivar el envío global de correos y definir la "Frecuencia de Envío de Resumen de Alertas" es visible y editable solo para administradores.
Guardado: Al hacer clic en "Guardar", se actualiza la estructura franjas_horarias en config.yaml con los nuevos umbrales y horarios, y la configuración general de notificaciones.
ejecutar_checker_manual()
Python
def ejecutar_checker_manual():
    st.subheader("🔍 Ejecutar Análisis Manual de Alertas")
    # ... (botón para ejecutar subprocess.run(["python", "checker.py", "--manual-run"])) ...
Permite al usuario (principalmente para pruebas) ejecutar el script checker.py manualmente en modo "no-mail" (el checker.py en modo manual no envía correos de alerta, solo registra).
editar_perfil_usuario()
Python
def editar_perfil_usuario():
    st.title("👤 Editar Perfil de Usuario")
    # ... (formulario para Nombre, Correo electrónico para alertas, y checkbox para recibir notificaciones) ...
    # ... (formulario para Cambiar Contraseña) ...
Permite a cualquier usuario autenticado actualizar su nombre, su dirección de correo electrónico para recibir alertas, y su preferencia individual para activar/desactivar las notificaciones por correo.
También incluye un formulario para cambiar la contraseña actual del usuario, que utiliza bcrypt y actualiza config.yaml.
gestionar_usuarios()
Python
def gestionar_usuarios():
    st.title("👥 Gestión de Usuarios")
    # ... (muestra tabla de usuarios) ...
    # ... (selectbox y botón para eliminar usuario, solo para admin) ...
Solo accesible para usuarios con el rol 'admin'.
Muestra una tabla de todos los usuarios registrados, combinando información de config.yaml y usuarios.json.
Permite al administrador seleccionar y eliminar usuarios del sistema (excepto a sí mismo). La eliminación afecta tanto a config.yaml como a usuarios.json y limpia los tokens de restablecimiento asociados.
create_multi_series_chart(data, title, y_columns, y_title, colors=None)
Python
def create_multi_series_chart(data, title, y_columns, y_title, colors=None):
    fig = go.Figure()
    # ... (añade trazas para múltiples columnas de datos en un solo gráfico Plotly) ...
    return fig
Función auxiliar para generar gráficos de líneas de múltiples series usando Plotly, ideal para voltajes o corrientes por fase.
create_power_chart(data, title='Potencia Activa')
Python
def create_power_chart(data, title='Potencia Activa'):
    fig = go.Figure()
    # ... (añade traza para potencia activa con relleno de área) ...
    return fig
Función auxiliar para generar un gráfico de línea con área para la potencia activa.
create_metrics_dashboard(data)
Python
def create_metrics_dashboard(data):
    col1, col2, col3, col4 = st.columns(4)
    # ... (calcula y muestra métricas promedio/máximas como voltaje promedio, corriente promedio, potencia promedio/máxima) ...
Función auxiliar para mostrar métricas clave en el dashboard (ej. promedio de voltaje, corriente, potencia).
wizard_configuracion_franjas(current_config)
Python
def wizard_configuracion_franjas(current_config):
    st.title("Asistente de Configuración Inicial de Franjas Horarias")
    # ... (inputs para horas de inicio/fin de DIA y NOCHE) ...
    # ... (inputs para umbrales por defecto para DIA y NOCHE) ...
    if st.button("💾 Guardar Configuración Inicial de Franjas", use_container_width=True, type="primary"):
        # ... (validaciones de horas y guardado en current_config['franjas_horarias']) ...
Esta función actúa como un asistente de configuración "por primera vez".
Se activa solo para el usuario administrador y solo si la sección franjas_horarias no existe o está vacía en config.yaml.
Permite al administrador definir las horas de inicio y fin para las franjas "DIA" y "NOCHE", y sus umbrales asociados, utilizando los valores de default_franjas_horarias como base.
Una vez guardada, la configuración se escribe en la sección franjas_horarias de config.yaml, y el asistente no volverá a aparecer.
main() (Función Principal de la Aplicación Streamlit)
Python
def main():
    # ... (Inicialización de session state) ...
    # --- Lógica de Wizard para configuración inicial de franjas horarias ---
    current_config = load_config()
    if not current_config: st.error("Error crítico: No se pudo cargar el archivo de configuración."); st.stop()
    if st.session_state.get('roles') == 'admin':
        if not current_config.get('franjas_horarias'):
            wizard_configuracion_franjas(current_config) # LLamada al wizard
            st.stop() # Detiene la ejecución para mostrar solo el wizard
    # --- Fin de la lógica del Wizard ---

    st.sidebar.title("Menú Principal")
    navigation_options = ["📈 Dashboard Principal", "🔔 Alertas y Logs", "👤 Editar Perfil"]
    if st.session_state.get('roles') == 'admin':
        navigation_options.append("👥 Gestión de Usuarios")
    seccion = st.sidebar.radio("Navegar:", navigation_options, index=0)

    if seccion == "📈 Dashboard Principal":
        # ... (lógica del dashboard, carga de datos, filtros, gráficos) ...
    elif seccion == "🔔 Alertas y Logs":
        # ... (llama a mostrar_alertas_activas(), display_franja_config_form(), ejecutar_checker_manual()) ...
    elif seccion == "👤 Editar Perfil":
        editar_perfil_usuario()
    elif seccion == "👥 Gestión de Usuarios":
        gestionar_usuarios()

    st.divider()
    st.caption(f"© {datetime.today().year} Schneider Electric - Power Monitoring System | v2.0 | Datos de InfluxDB")
    # Modo Debug eliminado
    # if st.sidebar.checkbox("🔧 Modo Debug"): ...
Es la función principal de la aplicación.
Lógica del Wizard: Al inicio, verifica si el usuario es administrador y si las franjas horarias no están configuradas en config.yaml. Si se cumplen estas condiciones, llama a wizard_configuracion_franjas() y luego st.stop() para pausar la ejecución del resto de la página, asegurando que el wizard sea la única UI visible hasta que se complete.
Barra Lateral de Navegación: Configura la barra lateral con las opciones de navegación ("Dashboard Principal", "Alertas y Logs", "Editar Perfil", y "Gestión de Usuarios" si es administrador).
Manejo de Secciones: Utiliza st.sidebar.radio para cambiar entre las diferentes secciones de la aplicación, llamando a las funciones correspondientes.
Eliminación del Modo Debug: La opción de "Modo Debug" en la barra lateral ha sido eliminada para no confundir a los usuarios finales.
Flujo de Funcionamiento (pagina.py)
Una vez que el usuario se autentica exitosamente a través de login.py, este llama a pagina.py a través de su función main().
pagina.py carga la configuración. Si es un administrador y las franjas horarias no están definidas, se muestra el wizard_configuracion_franjas.
Después del wizard (o si las franjas ya estaban configuradas), se renderiza la interfaz principal con el menú de navegación lateral.
El usuario puede navegar entre las diferentes secciones:
Dashboard Principal: Visualiza los datos históricos de InfluxDB con gráficos y métricas.
Alertas y Logs: Muestra el historial de alertas y permite al administrador configurar los umbrales por franja horaria y las opciones de notificación general.
Editar Perfil: Permite a cada usuario gestionar su información y preferencias de notificación.
Gestión de Usuarios: (Solo Admin) Permite listar y eliminar usuarios.
Los cambios realizados en las configuraciones se guardan persistentemente en config.yaml o usuarios.json.
Streamlit/checker.py (Actualizado con Buffer de Alertas y Franjas Horarias)
Este script se ejecuta periódicamente como un servicio separado (checker_service) y es el motor detrás del sistema de detección de alertas y envío de resúmenes.

Análisis Línea por Línea y Lógica
Python
import json, requests, yaml
from datetime import datetime, timedelta
import os
from emailsender import enviar_alerta
import argparse
Importaciones: Incluye requests para consultas HTTP a InfluxDB, yaml para config.yaml, y argparse para manejar la opción --manual-run.
Python
LOG_FILE = "logs_alertas.json"
CONFIG_FILE = "config.yaml"
USUARIOS_FILE = "usuarios.json"
LAST_DIGEST_SENT_FILE = "last_digest_sent_state.json"
PENDING_ALERTS_BUFFER_FILE = "pending_alerts_buffer.json" # Nuevo archivo para buffer
Definición de rutas a los archivos de logs y estado. PENDING_ALERTS_BUFFER_FILE es el nuevo archivo para el buffer.
Python
def cargar_configuracion_general():
    # ... (carga config.yaml, incluyendo franjas_horarias) ...
    # Ahora usa config.update(cfg_from_file) para cargar todo el diccionario de configuración de manera flexible.
def cargar_usuarios_con_alertas():
    # ... (carga usuarios.json y filtra por usuarios que quieren recibir notificaciones) ...
def registrar_alerta(variable, valor, umbral_info, franja_horaria, tipo_ejecucion="automatico"):
    # ... (registra la alerta en logs_alertas.json, incluyendo franja_horaria) ...
def load_last_digest_sent_time(): ...
def save_last_digest_sent_time(timestamp): ...
def load_pending_alerts_buffer(): ... # Nueva función para cargar el buffer
def save_pending_alerts_buffer(alerts_list): ... # Nueva función para guardar el buffer
Funciones de carga/guardado para la configuración, usuarios, el estado del último resumen y el buffer de alertas pendientes. registrar_alerta ahora guarda también la franja horaria.
determinar_franja_actual(franjas_config)
Python
def determinar_franja_actual(franjas_config):
    now = datetime.now().time()
    for nombre_franja, detalles_franja in franjas_config.items():
        # ... (lógica para comparar la hora actual con inicio_hora y fin_hora de cada franja) ...
    return "UNKNOWN"
Esta función toma la hora actual del sistema y la compara con las horas de inicio y fin de las franjas definidas en config.yaml.
Devuelve el nombre de la franja horaria ("DIA" o "NOCHE") a la que pertenece la hora actual.
Maneja correctamente las franjas que cruzan la medianoche.
Importante: La hora del sistema del contenedor de checker_service debe estar sincronizada para una detección precisa.
consultar_influx_y_verificar(manual_run=False)
Python
def consultar_influx_y_verificar(manual_run=False):
    config = cargar_configuracion_general()
    franjas_horarias_config = config.get("franjas_horarias", {})
    # Si franjas_horarias no está configurado, usa default_franjas_horarias
    if not franjas_horarias_config and config.get("default_franjas_horarias"):
        franjas_horarias_config = config.get("default_franjas_horarias")
    elif not franjas_horarias_config:
        print("[WARNING] No hay franjas horarias configuradas... No se puede aplicar umbrales.")
        return # Sale si no hay configuración de franjas

    current_franja_name = determinar_franja_actual(franjas_horarias_config)
    current_franja_umbrales = franjas_horarias_config.get(current_franja_name, {}).get("umbrales", {})

    # ... (inicialización de conexión a InfluxDB, destinatarios, etc.) ...
    
    pending_alerts_buffer = load_pending_alerts_buffer() # Cargar el buffer
    
    for variable_field_name in monitored_variables: # Itera sobre variables como voltaje, current_l1, etc.
        # ... (obtiene umbrales min/max para la variable y franja actuales) ...
        flux_query = f'''
        from(bucket: "powerlogic_warnings_tmp")
          |> range(start: -5m) 
          |> filter(fn: (r) => r["_field"] == "{variable_field_name}")
          |> filter(fn: (r) => r["franja_horaria"] == "{current_franja_name}") # FILTRA POR FRANJA HORARIA
          |> last()
        '''
        # ... (realiza la consulta a InfluxDB) ...
        if valor is not None:
            # ... (Lógica para determinar si hay alerta según los umbrales de la franja actual) ...
            if alerta_activa:
                registrar_alerta(..., franja_horaria=current_franja_name, ...)
                # Lógica para añadir al buffer y guardar el buffer
                # Se incluye un filtro para no añadir la misma alerta repetidamente en el mismo minuto.
                pending_alerts_buffer.append(alert_entry_for_buffer)
                save_pending_alerts_buffer(pending_alerts_buffer)
            # ...
    
    # Lógica de envío de resumen de alertas (solo para ejecuciones automáticas)
    if not manual_run and destinatarios:
        last_digest_sent_time = load_last_digest_sent_time()
        next_digest_send_time = (last_digest_sent_time or datetime.min) + timedelta(minutes=DIGEST_INTERVAL_MINUTES)
        
        should_send_digest = False
        if current_time_for_digest >= next_digest_send_time and pending_alerts_buffer:
            should_send_digest = True
        elif not pending_alerts_buffer:
            print("[INFO] No hay alertas pendientes en el buffer. No se enviará resumen.")
        # ...
        
        if should_send_digest:
            mensaje_html = "<h2>Resumen de Alertas de PowerLogic</h2>"
            # ... (construye el mensaje HTML usando TODAS las alertas de pending_alerts_buffer) ...
            for email in destinatarios:
                enviar_alerta(email, f"⚠️ Resumen de Alertas PowerLogic ({len(pending_alerts_buffer)} alertas)", mensaje_html)
            
            # Vaciar el buffer después de enviar el resumen
            save_pending_alerts_buffer([]) # Vaciar el buffer
            save_last_digest_sent_time(current_time_for_digest) # Actualizar el tiempo del último envío
Esta es la función principal que se ejecuta en cada ciclo del checker_service.
Carga de Configuración de Franjas: Intenta cargar las franjas_horarias configuradas. Si no existen (porque el wizard no se ha ejecutado aún o se ha reseteado config.yaml), utiliza las default_franjas_horarias.
Determinación de Franja Actual: Llama a determinar_franja_actual() para saber en qué franja horaria se encuentra el sistema en este momento.
Consulta InfluxDB con Filtro de Franja: La consulta Flux ahora incluye un filter adicional por el tag franja_horaria (r["franja_horaria"] == "{current_franja_name}"). Esto asegura que el checker solo evalúe los datos que corresponden a la franja horaria activa.
Detección y Registro de Alertas: Compara el último valor de cada métrica con los umbrales específicos de la franja horaria actual. Si un valor está fuera de umbral, se registra la alerta en logs_alertas.json y se añade al pending_alerts_buffer.json. Se evita añadir duplicados inmediatos al buffer.
Lógica del Buffer y Envío de Resumen:
Acumulación: Las alertas detectadas se añaden a pending_alerts_buffer.json. Este archivo es un "buffer" persistente de todas las alertas activas que han ocurrido desde el último resumen enviado.
Condición de Envío: Un resumen por correo electrónico solo se envía si manual_run es False (no es una ejecución manual), hay destinatarios configurados, el tiempo actual es mayor o igual al next_digest_send_time (calculado a partir del alert_digest_interval_minutes), Y hay alertas acumuladas en el pending_alerts_buffer.json.
Contenido del Resumen: El correo incluye un resumen con todas las alertas que están en el pending_alerts_buffer.json.
Vaciado del Buffer: Después de enviar un resumen exitosamente, el pending_alerts_buffer.json se vacía, y last_digest_sent_time.json se actualiza. Esto asegura que no se reenvíen alertas ya notificadas y que el sistema esté listo para acumular nuevas alertas para el siguiente intervalo.
Flujo de Funcionamiento (checker.py)
El servicio checker_service se inicia y ejecuta checker.py cada 60 segundos.
En cada ejecución, checker.py carga la configuración actual (incluyendo franjas horarias y umbrales) y el buffer de alertas pendientes.
Determina la franja horaria actual.
Consulta InfluxDB para obtener los últimos valores de las métricas clave, filtrando por la franja horaria actual.
Compara estos valores con los umbrales definidos para esa franja horaria.
Si se detecta una alerta, se registra en logs_alertas.json y se añade al pending_alerts_buffer.json.
Al final de cada ejecución, checker.py verifica si ha pasado el tiempo configurado para el alert_digest_interval_minutes desde el último envío de resumen Y si hay alertas en el pending_alerts_buffer.json.
Si ambas condiciones se cumplen, se envía un correo electrónico de resumen con todas las alertas acumuladas, el buffer se vacía y se actualiza la marca de tiempo del último envío. Si no hay alertas en el buffer, no se envía nada.
Telegraf/README.md (Actualizado)
Markdown
# Telegraf Agents Configuration

Este directorio contiene los archivos de configuración para los agentes Telegraf utilizados en el sistema de monitoreo.

## Propósito

Telegraf es un agente de código abierto para la recolección, procesamiento y envío de métricas y eventos. En este proyecto, se utilizan dos instancias de Telegraf para satisfacer diferentes requisitos de recolección de datos y retención en InfluxDB.

## Estructura del Directorio

Telegraf/
├── telegraf.conf           # Configuración para datos históricos/generales
├── telegraf_warnings.conf  # Configuración para datos de alerta (temporales y con tagging de franja)
└── README.md               # Este archivo


## `telegraf.conf`

### Propósito

Este archivo de configuración está diseñado para la recolección de datos Modbus de frecuencia regular para **almacenamiento general e histórico** en InfluxDB.

### Análisis Línea por Línea y Lógica

```toml
[agent]
  interval = "10s"
  round_interval = true
  metric_batch_size = 1000
  metric_buffer_limit = 10000
  collection_jitter = "0s"
  flush_interval = "10s"
  flush_jitter = "0s"
  precision = ""
  hostname = "telegraf"
  omit_hostname = false
[agent]: Sección global para la configuración del agente Telegraf.
interval = "10s": El intervalo predeterminado para la recolección de métricas es cada 10 segundos.
round_interval = true: Redondea los intervalos de recolección al intervalo más cercano para alineación.
hostname = "telegraf": Establece el nombre de host que se añadirá como tag a las métricas.
omit_hostname = false: Asegura que el hostname se incluya.
Ini, TOML
[[outputs.influxdb_v2]]
  urls = ["http://influxdb:8086"]
  token = "token_telegraf"
  organization = "power_logic"
  bucket = "mensualx6"

[[outputs.influxdb_v2]]
  urls = ["http://influxdb:8086"]
  token = "token_telegraf"
  organization = "power_logic"
  bucket = "anualx4"
[[outputs.influxdb_v2]]: Define las salidas para InfluxDB 2.x.
Los datos recolectados se enviarán a la URL de InfluxDB (http://influxdb:8086), usando token_telegraf para autenticación y a la organización power_logic.
El primer bloque envía datos al bucket mensualx6 (retención de 180 días).
El segundo bloque envía los mismos datos al bucket anualx4 (retención de 1460 días / 4 años), lo que permite tener datos a largo plazo y a corto/medio plazo.
Ini, TOML
[[inputs.modbus]]
  name = "modbus_sim"
  controller = "tcp://modbus-sim:5020"
  slave_id = 1
[[inputs.modbus]]: Define el plugin de entrada para Modbus.
name = "modbus_sim": Nombre para esta entrada Modbus.
controller = "tcp://modbus-sim:5020": La dirección del servidor Modbus TCP (el simulador Modbus en este caso). En un entorno real, esto se cambiaría a la IP y puerto del dispositivo PowerLogic real.
slave_id = 1: El ID del esclavo Modbus.
Ini, TOML
  [[inputs.modbus.holding_registers]]
    name = "active_power"
    byte_order = "AB"
    data_type = "UINT16"
    scale = 1.0
    address = [6]
  # ... (definiciones para voltaje, voltage_l2n, voltage_l3n, current_l1, current_l2, current_l3) ...
[[inputs.modbus.holding_registers]]: Define los registros de retención (holding registers) específicos que Telegraf leerá del dispositivo Modbus.
name: El nombre del campo que se creará en InfluxDB (ej. active_power, voltaje).
byte_order, data_type: Especifican cómo interpretar los bytes recibidos.
scale: Un factor de escala para aplicar a los valores leídos. Por ejemplo, si el dispositivo envía 2250 para 225.0V, una escala de 0.1 lo convierte correctamente. Es crucial que esto coincida con la escala del simulador/equipo real.
address: La dirección del registro Modbus que se leerá.
telegraf_warnings.conf
Propósito
Este archivo de configuración está dedicado a la recolección de datos específicos para el sistema de alertas. La clave aquí es la frecuencia de recolección más alta y el tagging de franja horaria en los datos temporales.

Análisis Línea por Línea y Lógica
Ini, TOML
[agent]
  interval = "1m"
  round_interval = true
  # ... (otras configuraciones de agente) ...
interval = "1m": Establece el intervalo de recolección de métricas a cada 1 minuto, una frecuencia más alta que el Telegraf principal, optimizada para la detección rápida de alertas.
Ini, TOML
[[inputs.modbus]]
  name = "PowerLogic4000_Warnings"
  controller = "tcp://modbus-sim:5020"
  timeout = "10s"
  slave_id = 1
  holding_registers = [
    { name = "voltaje",  byte_order = "AB", data_type = "UINT16", address = [0], scale = 0.1},
    { name = "current_l1",     byte_order = "AB", data_type = "UINT16", address = [3], scale = 0.1},
    { name = "active_power",   byte_order = "AB", data_type = "UINT16", address = [6], scale = 1.0}
  ]
Similar al telegraf.conf, pero solo recolecta un subconjunto de "holding registers" que son relevantes para el sistema de alertas (voltaje, current_l1, active_power).
Ini, TOML
[[processors.starlark]]
  source = '''
def apply(metric):
    hour = metric.time.hour # Obtener la hora del timestamp de la métrica (hora local del Telegraf)

    # Definir las franjas horarias
    # Asegúrate que estas horas coincidan con las de config.yaml si las usas para umbrales
    if hour >= 8 and hour < 20: # 8am a 8pm
        metric.tags["franja_horaria"] = "DIA"
    else: # 8:01pm a 7:59am
        metric.tags["franja_horaria"] = "NOCHE"
    return metric
'''
[[processors.starlark]]: Este es un procesador de Telegraf que ejecuta un script escrito en Starlark (un dialecto de Python).
def apply(metric):: La función principal que se ejecuta para cada métrica.
hour = metric.time.hour: Obtiene la hora del día (basada en la zona horaria del contenedor Telegraf) del timestamp de la métrica.
Lógica de Franja Horaria: Compara la hour para determinar si está en la franja "DIA" (8am a 8pm) o "NOCHE" (8:01pm a 7:59am).
metric.tags["franja_horaria"] = "DIA/NOCHE": Añade un nuevo tag llamado franja_horaria a la métrica con el valor determinado. Esto es CRUCIAL porque permite que InfluxDB almacene las métricas con esta etiqueta, y que checker.py pueda filtrarlas por franja horaria.
return metric: La métrica modificada (con el nuevo tag) es pasada a la siguiente etapa (la salida a InfluxDB).
Ini, TOML
[[outputs.influxdb_v2]]
  urls = ["http://influxdb:8086"]
  token = "token_telegraf"
  organization = "power_logic"
  bucket = "powerlogic_warnings_tmp"
bucket = "powerlogic_warnings_tmp": Los datos recolectados por esta instancia de Telegraf se envían exclusivamente al bucket powerlogic_warnings_tmp. Este bucket tiene una retención de 1 día, lo que lo hace ideal para datos efímeros de alta frecuencia que se usan solo para la detección inmediata de alertas.
Flujo de Funcionamiento (Agentes Telegraf)
Ambos servicios telegraf y telegraf-warnings se inician.
telegraf (principal) recolecta un conjunto completo de métricas Modbus cada 10 segundos y las envía a los buckets mensualx6 y anualx4 en InfluxDB.
telegraf-warnings recolecta un subconjunto de métricas críticas cada 1 minuto.
Antes de enviar los datos, el starlark processor en telegraf-warnings determina la franja horaria actual y añade un tag franja_horaria a cada métrica.
Estas métricas tageadas se envían al bucket temporal powerlogic_warnings_tmp.
Este etiquetado permite que checker.py consulte específicamente los datos de la franja horaria relevante al verificar los umbrales.
Archivos de Configuración y Datos Suplementarios
Estos archivos no tienen un README individual, pero son vitales para el proyecto:

Streamlit/emailsender.py
Propósito: Un módulo simple para enviar correos electrónicos a través de la API de Resend.
Lógica: Define la función enviar_alerta(destinatario, asunto, html_mensaje). Utiliza variables de entorno (RESEND_API_KEY, RESEND_FROM) para la autenticación con Resend. Construye el payload JSON requerido por la API de Resend y realiza una solicitud POST. Incluye manejo básico de errores e impresión de estado.
Integración: Es llamado por login.py para el restablecimiento de contraseñas y por checker.py para enviar los resúmenes de alertas.
Streamlit/requirements.txt
Propósito: Lista todas las librerías de Python de las que dependen los scripts en la carpeta Streamlit/.
Lógica: El comando pip install -r requirements.txt dentro del Dockerfile lee esta lista e instala las versiones especificadas de cada librería (ej. streamlit, pandas, plotly, influxdb-client, bcrypt, PyYAML, requests, etc.).
Streamlit/usuarios.json
Propósito: Almacena información adicional de los usuarios del sistema, principalmente su nombre, correo electrónico de login, correo electrónico para recibir alertas (alert_email) y su preferencia individual para recibir notificaciones (recibir_notificaciones).
Lógica: Es leído por login.py durante el registro y edición de perfil para guardar estas preferencias, y por checker.py para determinar a quién enviar las alertas de resumen.
Streamlit/logs_alertas.json
Propósito: Un archivo de registro persistente que almacena un historial de todas las alertas que han sido detectadas por el checker.py.
Lógica: Cada vez que checker.py identifica una condición de alerta, añade una nueva entrada a este archivo con la marca de tiempo, la variable, el valor, el umbral, la franja horaria y el tipo de ejecución (automática/manual). Se mantiene un máximo de 100 entradas por defecto.
Streamlit/last_digest_sent_state.json
Propósito: Un archivo de estado muy ligero que almacena la marca de tiempo del último momento en que se envió un resumen de alertas por correo electrónico.
Lógica: checker.py lo lee para determinar cuándo es el momento de enviar el próximo resumen de alertas, basándose en el alert_digest_interval_minutes. Se actualiza después de cada envío exitoso de un resumen.
Streamlit/pending_alerts_buffer.json
Propósito: Un archivo temporal que actúa como un "buffer" o cola para almacenar las alertas individuales que han sido detectadas por checker.py y están a la espera de ser incluidas en el próximo correo de resumen.
Lógica: Cuando checker.py detecta una alerta, la añade a este buffer. Cuando se cumple la condición de envío del resumen (intervalo transcurrido Y hay alertas en el buffer), todas las alertas de este buffer se agrupan en un solo correo, y luego el buffer se vacía. Esto asegura que no se pierda ninguna alerta entre los intervalos de resumen.
Streamlit/reset_password_admin.py
Propósito: Una herramienta de línea de comandos (CLI) para que un administrador pueda restablecer manualmente la contraseña de cualquier usuario en config.yaml.
Lógica: Pide el nombre de usuario y la nueva contraseña. Hashea la nueva contraseña usando bcrypt y actualiza directamente el config.yaml. Útil para situaciones de emergencia o cuando el flujo de restablecimiento por correo no es deseado.
Streamlit/test_email.py
Propósito: Un script simple para probar la funcionalidad de envío de correos electrónicos de forma aislada, sin tener que disparar una alerta real en el sistema.
Lógica: Simplemente llama a emailsender.enviar_alerta() con datos de prueba predefinidos.
Streamlit/umbral_config.json y Streamlit/alert_cooldown_state.json
Estado Actual: Estos archivos ya no son utilizados por las versiones más recientes de checker.py y pagina.py. Sus funcionalidades (umbrales y cooldown) han sido migradas a config.yaml y a la lógica del buffer en checker.py, respectivamente.
Recomendación: Deben ser eliminados del proyecto.
