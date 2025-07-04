import json
import requests
import yaml
from datetime import datetime, timedelta
import os
from emailsender import enviar_alerta
import argparse

LOG_FILE = "logs_alertas.json"
CONFIG_FILE = "config.yaml"
USUARIOS_FILE = "usuarios.json"
LAST_DIGEST_SENT_FILE = "last_digest_sent_state.json"
PENDING_ALERTS_BUFFER_FILE = "pending_alerts_buffer.json" # Nuevo archivo para buffer

def cargar_configuracion_general():
    config = {
        "influxdb_url": os.getenv('INFLUXDB_URL', 'http://influxdb:8086'),
        "token": os.getenv('INFLUXDB_TOKEN', 'token_telegraf'),
        "org": os.getenv('INFLUXDB_ORG', 'power_logic'),
        "notificaciones_generales": False,
        "alert_digest_interval_minutes": 1440,
        "franjas_horarias": {} # Se espera que esto esté en el config.yaml
    }
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg_from_file = yaml.safe_load(f)
                if cfg_from_file:
                    config.update(cfg_from_file) # Cargar todo el diccionario de configuración
        else:
            print(f"[INFO] El archivo '{CONFIG_FILE}' no existe. Usando configuración por defecto.")
    except Exception as e:
        print(f"[ERROR] Error al leer {CONFIG_FILE}: {e}. Usando configuración por defecto.")
    return config

def cargar_usuarios_con_alertas():
    try:
        if os.path.exists(USUARIOS_FILE):
            with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
                usuarios = json.load(f)
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

def registrar_alerta(variable, valor, umbral_info, franja_horaria, tipo_ejecucion="automatico"):
    umbral_str = f"Min: {umbral_info.get('min', 'N/A')}, Max: {umbral_info.get('max', 'N/A')}"
    entrada = {
        "timestamp": datetime.now().isoformat(),
        "variable": variable,
        "valor": valor,
        "umbral": umbral_str,
        "franja_horaria": franja_horaria,
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

def load_pending_alerts_buffer():
    """Carga las alertas pendientes de envío desde el buffer."""
    if os.path.exists(PENDING_ALERTS_BUFFER_FILE):
        try:
            with open(PENDING_ALERTS_BUFFER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"[WARNING] Error al cargar el buffer de alertas pendientes '{PENDING_ALERTS_BUFFER_FILE}': {e}. Iniciando con buffer vacío.")
            return []
    return []

def save_pending_alerts_buffer(alerts_list):
    """Guarda las alertas pendientes de envío en el buffer."""
    try:
        with open(PENDING_ALERTS_BUFFER_FILE, "w", encoding="utf-8") as f:
            json.dump(alerts_list, f, indent=4)
    except Exception as e:
        print(f"[ERROR] No se pudo guardar el buffer de alertas pendientes en '{PENDING_ALERTS_BUFFER_FILE}': {e}")

def determinar_franja_actual(franjas_config):
    now = datetime.now().time()
    for nombre_franja, detalles_franja in franjas_config.items():
        inicio_str = detalles_franja['inicio_hora']
        fin_str = detalles_franja['fin_hora']

        try:
            inicio_hora = datetime.strptime(inicio_str, "%H:%M").time()
            fin_hora = datetime.strptime(fin_str, "%H:%M").time()
        except ValueError as e:
            print(f"[ERROR] Error al parsear hora en franja '{nombre_franja}': {e}. Revisar config.yaml.")
            continue

        if inicio_hora <= fin_hora: # Franja dentro del mismo día
            if inicio_hora <= now <= fin_hora:
                return nombre_franja
        else: # Franja que cruza la medianoche (ej. 22:00 - 06:00)
            if now >= inicio_hora or now <= fin_hora:
                return nombre_franja
    return "UNKNOWN"

def consultar_influx_y_verificar(manual_run=False):
    config = cargar_configuracion_general()
    franjas_horarias_config = config.get("franjas_horarias", {})
    
    # Si las franjas horarias no están configuradas en config.yaml, usar las por defecto para el checker
    if not franjas_horarias_config and config.get("default_franjas_horarias"):
        franjas_horarias_config = config.get("default_franjas_horarias")
        print("[INFO] Usando franjas horarias por defecto para el checker.")
    elif not franjas_horarias_config:
        print("[WARNING] No hay franjas horarias configuradas ni por defecto. El checker no podrá aplicar umbrales por franja.")
        return # No podemos continuar sin umbrales de franja

    current_franja_name = determinar_franja_actual(franjas_horarias_config)
    current_franja_umbrales = franjas_horarias_config.get(current_franja_name, {}).get("umbrales", {})

    INFLUX_URL = config["influxdb_url"] + "/api/v2/query"
    TOKEN = config["token"]
    ORG = config["org"]
    ENVIAR_MAIL_GLOBAL = config.get("notificaciones_generales", False)
    DIGEST_INTERVAL_MINUTES = config.get("alert_digest_interval_minutes", 1440)

    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/vnd.flux"
    }

    destinatarios = cargar_usuarios_con_alertas() if ENVIAR_MAIL_GLOBAL and not manual_run else []

    alerts_detected_in_current_cycle = [] # Alertas detectadas en esta única ejecución del checker
    pending_alerts_buffer = load_pending_alerts_buffer() # Cargar el buffer de alertas pendientes

    current_time_for_digest = datetime.now()

    monitored_variables = current_franja_umbrales.keys()

    for variable_field_name in monitored_variables:
        umbral_data = current_franja_umbrales.get(variable_field_name)
        
        if not umbral_data:
            print(f"[WARNING] No hay umbrales definidos para '{variable_field_name}' en la franja '{current_franja_name}'. Saltando.")
            continue

        # NUEVO: Verificar si la alerta está habilitada para este parámetro
        alert_enabled = umbral_data.get('alert_enabled', True) # Por defecto, si no está definido, se asume True
        if not alert_enabled:
            print(f"[INFO] Alerta deshabilitada para '{variable_field_name}' en la franja '{current_franja_name}'. Saltando verificación.")
            continue
            
        min_umbral = umbral_data.get('min')
        max_umbral = umbral_data.get('max')

        flux_query = f'''
        from(bucket: "powerlogic_warnings_tmp")
          |> range(start: -5m) 
          |> filter(fn: (r) => r["_field"] == "{variable_field_name}")
          |> filter(fn: (r) => r["franja_horaria"] == "{current_franja_name}")
          |> last()
        '''

        try:
            response = requests.post(INFLUX_URL, headers=headers, data=flux_query, params={"org": ORG})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] No se pudo consultar InfluxDB para {variable_field_name} en franja {current_franja_name}: {e}")
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
            mensaje_alerta_motivo = []
            
            if min_umbral is not None and valor < min_umbral:
                mensaje_alerta_motivo.append(f"{variable_field_name} ({valor:.2f}) está por debajo del umbral mínimo ({min_umbral:.2f}).")
                alerta_activa = True
            
            if max_umbral is not None and valor > max_umbral:
                mensaje_alerta_motivo.append(f"{variable_field_name} ({valor:.2f}) está por encima del umbral máximo ({max_umbral:.2f}).")
                alerta_activa = True
            
            if alerta_activa:
                print(f"[ALERTA] {' '.join(mensaje_alerta_motivo)} (Franja: {current_franja_name}, Tipo: {'Manual' if manual_run else 'Automático'})")
                registrar_alerta(variable_field_name, valor, umbral_data, current_franja_name, "manual" if manual_run else "automatico")
                
                alert_entry_for_buffer = {
                    "timestamp": datetime.now().isoformat(), # Usar el timestamp del registro en lugar del del ciclo
                    "variable": variable_field_name,
                    "valor": valor,
                    "umbral": f"Min: {min_umbral:.2f}, Max: {max_umbral:.2f}",
                    "motivo": ' '.join(mensaje_alerta_motivo),
                    "franja_horaria": current_franja_name
                }
                
                # Añadir al buffer si no es una duplicación inmediata (en el mismo minuto)
                is_duplicate_in_buffer = False
                for existing_alert in pending_alerts_buffer:
                    if existing_alert["variable"] == alert_entry_for_buffer["variable"] and \
                       existing_alert["franja_horaria"] == alert_entry_for_buffer["franja_horaria"] and \
                       (datetime.fromisoformat(alert_entry_for_buffer["timestamp"]) - datetime.fromisoformat(existing_alert["timestamp"])).total_seconds() < 60:
                        is_duplicate_in_buffer = True
                        break
                
                if not is_duplicate_in_buffer:
                    pending_alerts_buffer.append(alert_entry_for_buffer)
                    save_pending_alerts_buffer(pending_alerts_buffer)
                    print(f"[INFO] Alerta para {variable_field_name} añadida al buffer de pendientes.")
                else:
                    print(f"[INFO] Alerta para {variable_field_name} es una duplicación reciente en el buffer. No se añade.")
            else:
                print(f"[OK] {variable_field_name} = {valor:.2f} (dentro de umbrales para franja {current_franja_name})")
        else:
            print(f"[INFO] No se encontró valor para {variable_field_name} en la franja {current_franja_name} en los últimos 5 minutos.")
    
    # Lógica de envío de resumen de alertas (solo para ejecuciones automáticas)
    if not manual_run and destinatarios:
        last_digest_sent_time = load_last_digest_sent_time()
        
        # Calcular el próximo tiempo de envío de resumen
        next_digest_send_time = (last_digest_sent_time or datetime.min) + timedelta(minutes=DIGEST_INTERVAL_MINUTES)
        
        should_send_digest = False
        if current_time_for_digest >= next_digest_send_time and pending_alerts_buffer:
            should_send_digest = True
            print(f"[INFO] Es hora de enviar un resumen de alertas (intervalo: {DIGEST_INTERVAL_MINUTES} min) y hay alertas pendientes.")
        elif not pending_alerts_buffer:
            print("[INFO] No hay alertas pendientes en el buffer. No se enviará resumen.")
        else: # current_time_for_digest < next_digest_send_time AND pending_alerts_buffer
            print(f"[INFO] Alertas pendientes en buffer, pero no es hora de enviar el resumen. Próximo envío: {next_digest_send_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if should_send_digest:
            mensaje_html = "<h2>Resumen de Alertas de PowerLogic</h2>"
            mensaje_html += f"<p>Se detectaron las siguientes condiciones de alerta desde el último resumen ({last_digest_sent_time.strftime('%Y-%m-%d %H:%M:%S') if last_digest_sent_time else 'Nunca'}):</p><ul>"
            
            # Usar el buffer de alertas pendientes para el resumen
            for alerta in pending_alerts_buffer:
                mensaje_html += (
                    f"<li><strong>Hora:</strong> {datetime.fromisoformat(alerta['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}<br>"
                    f"<strong>Variable:</strong> {alerta['variable']} (Franja: {alerta['franja_horaria']})<br>"
                    f"<strong>Valor actual:</strong> {alerta['valor']:.2f}<br>"
                    f"<strong>Umbrales configurados:</strong> {alerta['umbral']}<br>"
                    f"<strong>Motivo:</strong> {alerta['motivo']}</li>"
                )
            mensaje_html += "</ul><p><em>Este resumen se genera cada "
            mensaje_html += f"{DIGEST_INTERVAL_MINUTES} minutos.</em></p>"

            for email in destinatarios:
                print(f"Intentando enviar resumen de alertas a {email}...")
                enviar_alerta(email, f"⚠️ Resumen de Alertas PowerLogic ({len(pending_alerts_buffer)} alertas)", mensaje_html)
            
            # Vaciar el buffer después de enviar el resumen
            save_pending_alerts_buffer([]) # Vaciar el buffer
            print("[INFO] Buffer de alertas pendientes vaciado.")
            
            # Actualizar el tiempo del último envío de resumen
            save_last_digest_sent_time(current_time_for_digest)
            print("[INFO] Resumen de alertas enviado y estado de último envío actualizado.")
        
    elif manual_run:
        if alerts_detected_in_current_cycle:
            print(f"[INFO] Alertas detectadas en ejecución manual. No se envían correos a destinatarios globales.")
        else:
            print("[INFO] No se detectaron alertas en este ciclo en ejecución manual.")
    else:
        print("[INFO] No hay destinatarios configurados o notificaciones globales desactivadas para enviar alertas.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script para consultar InfluxDB y verificar umbrales de alerta.")
    parser.add_argument('--manual-run', action='store_true', help='Indica que la ejecución es manual y no debe enviar correos a la lista global de destinatarios.')
    args = parser.parse_args()
    
    consultar_influx_y_verificar(manual_run=args.manual_run)
