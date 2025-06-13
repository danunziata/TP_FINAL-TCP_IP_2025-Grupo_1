FROM python:3.10-slim

WORKDIR /app

COPY prueba_login.py pagina.py config.yaml requirements.txt ./

#Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto de Streamlit
EXPOSE 8501

# Comando para ejecutar la aplicación
CMD ["streamlit", "run", "prueba_login.py"] 