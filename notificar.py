from influxdb_client import InfluxDBClient
from datetime import datetime, timezone, timedelta
import smtplib
from email.message import EmailMessage

def enviar_alerta(asunto, cuerpo):
    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = EMAIL_EMISOR
    mensaje["To"] = EMAIL_RECEPTOR
    mensaje.set_content(cuerpo)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_EMISOR, CONTRASENA_APP)
            smtp.send_message(mensaje)
        print("📧 Correo enviado correctamente.")
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")

# Configuración
URL = "http://localhost:8086"
TOKEN = "token_telegraf"
ORG = "power_logic"
BUCKET = "alertas"

# Configuración del correo
EMAIL_EMISOR = "MAIL EMISOR" # crear un mail para el powerlogic
EMAIL_RECEPTOR = "LISTA DE MAILS OBTENIDOS DE LA DB" # idealmente en que los destinatarios estén en CC
CONTRASENA_APP = " ACA VA LA CONTRASEÑA " #https://myaccount.google.com/apppasswords

# Crear cliente
client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
query_api = client.query_api()

# Consulta: obtener el último dato
query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -1h)
  |> sort(columns: ["_time"], desc: true)
  |> limit(n:1)
'''

# Ejecutar consulta
tables = query_api.query(query)

# Verificar si hay resultados
if not tables or not tables[0].records:
    pass
else:
    record = tables[0].records[0]
    time = record.get_time()  # timestamp en UTC
    valor = record.get_value()
    medicion = record.get_measurement()

    # Comparar con hora actual
    ahora = datetime.now(timezone.utc)
    diferencia = ahora - time

    #print(f"✅ Último dato ({medicion}): {valor} @ {time.isoformat()}")
    if diferencia <= timedelta(minutes=15):
        enviar_alerta("Alerta Power Logic", f"{medicion}: {valor}")
