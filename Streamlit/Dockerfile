FROM python:3.10-slim

WORKDIR /app

# --- CORRECCIÓN ---
# Copiamos ÚNICAMENTE el código fuente y la configuración esencial.
# Los archivos de datos y estado (logs, usuarios, etc.) se gestionarán
# a través de volúmenes en docker-compose.yml.
COPY login.py pagina.py config.yaml requirements.txt emailsender.py checker.py reset_password_admin.py ./

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto de Streamlit
EXPOSE 8501

# Comando para ejecutar la aplicación
# (Esto es para el servicio 'streamlit_app'. El 'checker_service' lo sobreescribe).
CMD ["streamlit", "run", "login.py"]
