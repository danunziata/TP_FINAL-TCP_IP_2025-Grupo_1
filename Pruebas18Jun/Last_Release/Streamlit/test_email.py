from emailsender import enviar_alerta

# Datos de prueba
destinatario = "eliascoranti@gmail.com"
asunto = "🚨 Alerta de Prueba - PowerLogic"
html_mensaje = """
<h2>Alerta de Prueba</h2>
<p>Este es un mensaje de prueba del sistema PowerLogic.</p>
<p><strong>Variable:</strong> Corriente L1</p>
<p><strong>Valor actual:</strong> 12.3 A</p>
<p><strong>Umbral configurado:</strong> 10 A</p>
<p><em>Hora:</em> 2025-06-14 11:40</p>
"""

# Ejecutar prueba
enviar_alerta(destinatario, asunto, html_mensaje)
