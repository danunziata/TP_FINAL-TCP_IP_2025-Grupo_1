import os
import requests

# Se espera que estas variables estén definidas como variables de entorno
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "tu_api_key_aqui")
RESEND_FROM = os.getenv("RESEND_FROM", "alertas@tudominio.com")

def enviar_alerta(destinatario, asunto, html_mensaje):
    if not RESEND_API_KEY or not RESEND_FROM:
        print("[ERROR] Falta configurar RESEND_API_KEY o RESEND_FROM")
        return

    url = "https://api.resend.com/emails"

    payload = {
        "from": RESEND_FROM,
        "to": destinatario,
        "subject": asunto,
        "html": html_mensaje
    }

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.ok: # response.ok es True para códigos de estado 200-299
            print(f"[OK] Correo enviado a {destinatario} (ID: {response.json().get('id', 'N/A')})")
        else:
            print(f"[ERROR] Falló el envío a {destinatario}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[EXCEPCIÓN] Error al enviar correo: {e}")

# base_url para construir enlaces en correos (por ejemplo, para restablecimiento de contraseña)
# Se revierte a localhost para una configuración completamente local.
base_url = "http://localhost:8501"
