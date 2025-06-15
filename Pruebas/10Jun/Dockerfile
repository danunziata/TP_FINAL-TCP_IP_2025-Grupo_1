FROM python:3-slim

WORKDIR /app

COPY prueba_login.py config.yaml requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto 8501 (Streamlit)
EXPOSE 8501

# Ejecuta Streamlit en modo server, sin abrir navegador y escuchando en todas las interfaces
CMD ["streamlit", "run", "prueba_login.py", "--server.port=8501", "--server.address=0.0.0.0"]
