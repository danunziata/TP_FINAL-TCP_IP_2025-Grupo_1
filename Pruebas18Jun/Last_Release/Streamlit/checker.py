import json
import requests
import yaml
from datetime import datetime, timedelta
import os
from emailsender import enviar_alerta
import argparse

UMBRAL_FILE = "umbral_config.json"
LOG_FILE = "logs_alertas.json"
CONFIG_FILE = "config.yaml"
USUARIOS_FILE = "usuarios.json"
# Archivo para el estado del envío del resumen de alertas
LAST_DIGEST_SENT_FILE = "last_digest_sent_state.json"

def cargar_configuracion_general():
    config = {
        "influxdb_url": os.getenv('INFLUXDB_URL', 'http://influxdb:8086'),
        "token": os.getenv('INFLUXDB_TOKEN', 'token_telegraf'),
        "org": os.getenv('INFLUXDB_ORG', 'power_logic'),
        "notificaciones_generales": False,
        "alert_digest_interval_minutes": 1440 # Valor por defecto: 24 horas
    }
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg_from_file = yaml.safe_load(f)
                if cfg_from_file:
                    if "notificaciones_generales" in cfg_from_file:
                        config["notificaciones_generales"] = cfg_from_file["notificaciones_generales"]
                    if "alert_digest_interval_minutes" in cfg_from_file:
                        config["alert_digest_interval_minutes"] = cfg_from_file["alert_digest_interval_minutes"]
        else:
            print(f"[INFO] El archivo '{CONFIG_FILE}' no existe. Usando configuración por defecto.")
    except Exception as e:
        print(f"[ERROR] Error al leer {CONFIG_FILE}: {e}. Usando configuración por defecto.")
    return config

def cargar_configuracion_umbral():
    try:
        if os.path.exists(UMBRAL_FILE):
            with open(UMBRAL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            print(f"[WARNING] El archivo '{UMBRAL_FILE}' no existe. Retornando umbrales vacíos.")
            return {}
    except json.JSONDecodeError as e:
        print(f"[ERROR] Error al decodificar JSON de '{UMBRAL_FILE}': {e}. Retornando umbrales vacíos.")
        return {}
    except Exception as e:
        print(f"[ERROR] Error al cargar '{UMBRAL_FILE}': {e}. Retornando umbrales vacíos.")
        return {}

def cargar_usuarios_con_alertas():
    try:
        if os.path.exists(USUARIOS_FILE):
            with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
                usuarios = json.load(f)
            # Ahora buscamos el 'alert_email'
            return [u.get("alert_email") for u in usuarios if u.get("recibir_notificaciones", False) and u.get("alert_email")]
        else:
            print(f"[WARNING] El archivo '{USUARIOS_FILE}' no existe. No se enviarán correos.")
            return []
    except json.JSONDecodeError as e:
        print(f"[ERROR] Error al decodificar JSON de '{USUARIOS_FILE}': {e}. No se enviarán correos.")
        return []
    except Exception as e:
        print(f"[ERROR] Error al cargar '{USUARIOS_FILE}': {e}. No se enviarán correos.")
        return []

def registrar_alerta(variable, valor, umbral_info, tipo_ejecucion="automatico"):
    umbral_str = f"Min: {umbral_info.get('min', 'N/A')}, Max: {umbral_info.get('max', 'N/A')}"
    entrada = {
        "timestamp": datetime.now().isoformat(),
        "variable": variable,
        "valor": valor,
        "umbral": umbral_str,
        "tipo_ejecucion": tipo_ejecucion
    }
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        else:
            logs = []
    except json.JSONDecodeError:
        logs = []
        print(f"[WARNING] El archivo '{LOG_FILE}' está corrupto o vacío. Se reiniciará el log de alertas.")
    except FileNotFoundError:
        logs = []
    except Exception as e:
        logs = []
        print(f"[ERROR] Error inesperado al leer '{LOG_FILE}': {e}. Se reiniciará el log de alertas.")

    logs.append(entrada)

    MAX_LOG_ENTRIES = 100
    if len(logs) > MAX_LOG_ENTRIES:
        logs = logs[-MAX_LOG_ENTRIES:]

    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4)
    except Exception as e:
        print(f"[ERROR] No se pudo escribir en '{LOG_FILE}': {e}")

def load_last_digest_sent_time():
    """Carga la última vez que se envió un resumen de alertas."""
    if os.path.exists(LAST_DIGEST_SENT_FILE):
        try:
            with open(LAST_DIGEST_SENT_FILE, "r", encoding="utf-8") as f:
                timestamp_str = json.load(f)
            return datetime.fromisoformat(timestamp_str)
        except (json.JSONDecodeError, FileNotFoundError, ValueError) as e:
            print(f"[WARNING] Error al cargar el estado del último resumen '{LAST_DIGEST_SENT_FILE}': {e}. Iniciando con tiempo vacío.")
            return None
    return None

def save_last_digest_sent_time(timestamp):
    """Guarda la última vez que se envió un resumen de alertas."""
    try:
        with open(LAST_DIGEST_SENT_FILE, "w", encoding="utf-8") as f:
            json.dump(timestamp.isoformat(), f, indent=4)
    except Exception as e:
        print(f"[ERROR] No se pudo guardar el estado del último resumen en '{LAST_DIGEST_SENT_FILE}': {e}")

def consultar_influx_y_verificar(manual_run=False):
    config = cargar_configuracion_general()
    umbrales = cargar_configuracion_umbral()

    INFLUX_URL = config["influxdb_url"] + "/api/v2/query"
    TOKEN = config["token"]
    ORG = config["org"]
    ENVIAR_MAIL_GLOBAL = config.get("notificaciones_generales", False)
    DIGEST_INTERVAL_MINUTES = config.get("alert_digest_interval_minutes", 1440) # Default 24 horas

    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/vnd.flux"
    }

    # Destinatarios para envío de email (solo si no es una ejecución manual)
    destinatarios = cargar_usuarios_con_alertas() if ENVIAR_MAIL_GLOBAL and not manual_run else []

    alertas_detectadas_en_ciclo = []
    current_time = datetime.now()

    for variable_field_name, umbral_data in umbrales.items():
        min_umbral = umbral_data.get('min')
        max_umbral = umbral_data.get('max')

        flux_query = f'''
        from(bucket: "powerlogic_warnings_tmp")
          |> range(start: -2m)
          |> filter(fn: (r) => r["_field"] == "{variable_field_name}")
          |> last()
        '''

        try:
            response = requests.post(INFLUX_URL, headers=headers, data=flux_query, params={"org": ORG})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] No se pudo consultar InfluxDB para {variable_field_name}: {e}")
            continue

        valor = None
        for line in response.text.splitlines():
            if not line.startswith("#") and "_result" in line:
                partes = line.split(",")
                for parte in reversed(partes):
                    try:
                        valor = float(parte)
                        break
                    except ValueError:
                        continue
                if valor is not None:
                    break

        if valor is not None:
            alerta_activa = False
            mensaje_alerta = []
            
            if min_umbral is not None and valor < min_umbral:
                mensaje_alerta.append(f"{variable_field_name} ({valor:.2f}) está por debajo del umbral mínimo ({min_umbral:.2f}).")
                alerta_activa = True
            
            if max_umbral is not None and valor > max_umbral:
                mensaje_alerta.append(f"{variable_field_name} ({valor:.2f}) está por encima del umbral máximo ({max_umbral:.2f}).")
                alerta_activa = True
            
            if alerta_activa:
                # Registrar la alerta en el log inmediatamente
                print(f"[ALERTA] {' '.join(mensaje_alerta)} (Tipo: {'Manual' if manual_run else 'Automático'})")
                registrar_alerta(variable_field_name, valor, umbral_data, "manual" if manual_run else "automatico")
                
                # Añadir a la lista de alertas detectadas en este ciclo para el resumen
                alertas_detectadas_en_ciclo.append({
                    "variable": variable_field_name,
                    "valor": valor,
                    "umbral": f"Min: {min_umbral:.2f}, Max: {max_umbral:.2f}",
                    "motivo": ' '.join(mensaje_alerta)
                })
            else:
                print(f"[OK] {variable_field_name} = {valor:.2f} (dentro de umbrales)")
        else:
            print(f"[INFO] No se encontró valor para {variable_field_name} en los últimos 2 minutos.")
    
    # Lógica de envío de resumen de alertas (solo para ejecuciones automáticas)
    if not manual_run and destinatarios:
        last_digest_sent_time = load_last_digest_sent_time()
        
        # Calcular el próximo tiempo de envío de resumen
        next_digest_send_time = (last_digest_sent_time or datetime.min) + timedelta(minutes=DIGEST_INTERVAL_MINUTES)

        # Si hay alertas detectadas Y es hora de enviar un resumen (o nunca se ha enviado)
        if alertas_detectadas_en_ciclo and current_time >= next_digest_send_time:
            print(f"[INFO] Es hora de enviar un resumen de alertas (intervalo: {DIGEST_INTERVAL_MINUTES} min).")
            mensaje_html = "<h2>Resumen de Alertas de PowerLogic</h2>"
            mensaje_html += f"<p>Se detectaron las siguientes condiciones de alerta entre {next_digest_send_time.strftime('%Y-%m-%d %H:%M:%S')} y {current_time.strftime('%Y-%m-%d %H:%M:%S')}:</p><ul>"
            
            for alerta in alertas_detectadas_en_ciclo:
                mensaje_html += (
                    f"<li><strong>Variable:</strong> {alerta['variable']}<br>"
                    f"<strong>Valor actual:</strong> {alerta['valor']:.2f}<br>"
                    f"<strong>Umbrales configurados:</strong> {alerta['umbral']}<br>"
                    f"<strong>Motivo:</strong> {alerta['motivo']}</li>"
                )
            mensaje_html += "</ul><p><em>Este resumen se genera cada "
            mensaje_html += f"{DIGEST_INTERVAL_MINUTES} minutos.</em></p>"

            for email in destinatarios:
                print(f"Intentando enviar resumen de alertas a {email}...")
                enviar_alerta(email, f"⚠️ Resumen de Alertas PowerLogic ({len(alertas_detectadas_en_ciclo)} nuevas)", mensaje_html)
            
            # Actualizar el tiempo del último envío de resumen
            save_last_digest_sent_time(current_time)
            print("[INFO] Resumen de alertas enviado y estado actualizado.")
        elif not alertas_detectadas_en_ciclo:
            print("[INFO] No se detectaron alertas en este ciclo. No se enviará resumen.")
        else:
            print(f"[INFO] Alertas detectadas, pero no es hora de enviar el resumen. Próximo envío: {next_digest_send_time.strftime('%Y-%m-%d %H:%M:%S')}")
    elif manual_run:
        if alertas_detectadas_en_ciclo:
            print(f"[INFO] Alertas para este ciclo en ejecución manual. No se envían correos a destinatarios globales.")
        else:
            print("[INFO] No se detectaron alertas en este ciclo en ejecución manual.")
    else:
        print("[INFO] No hay destinatarios configurados o notificaciones globales desactivadas para enviar alertas.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script para consultar InfluxDB y verificar umbrales de alerta.")
    parser.add_argument('--manual-run', action='store_true', help='Indica que la ejecución es manual y no debe enviar correos a la lista global de destinatarios.')
    args = parser.parse_args()
    
    consultar_influx_y_verificar(manual_run=args.manual_run)
