FROM python:3.10-slim

WORKDIR /app

# Copia solo los archivos necesarios en lugar de todos los *.py de una vez
# Asegúrate de que 'login.py' y 'pagina.py' estén presentes en la raíz de /app
# junto con config.yaml y requirements.txt
COPY login.py pagina.py config.yaml requirements.txt emailsender.py checker.py reset_password_admin.py test_email.py usuarios.json logs_alertas.json last_digest_sent_state.json pending_alerts_buffer.json ./

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto de Streamlit
EXPOSE 8501

# Comando para ejecutar la aplicación
CMD ["streamlit", "run", "login.py"]
