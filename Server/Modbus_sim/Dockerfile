# Usa una imagen base ligera de Python
FROM python:3.9-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instala dependencias del sistema necesarias para muchas librerías de red
# (como pymodbus o async frameworks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Copia el archivo de requisitos primero para aprovechar el cache
COPY requirements.txt .
<<<<<<< HEAD:Server/Dockerfile.modbus

# Instala dependencias de Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
=======
RUN pip install --no-cache-dir -r requirements.txt
>>>>>>> bb7f761b1fe8c713249ab87d0753ed0f4860f6a1:Server/Modbus_sim/Dockerfile

# Copia el script principal de tu servidor Modbus
COPY modbus_cm4000_server.py .

# Expone el puerto que usa tu servidor Modbus
EXPOSE 5020

<<<<<<< HEAD:Server/Dockerfile.modbus
# Comando por defecto al iniciar el contenedor
CMD ["python", "modbus_cm4000_server.py"]
=======
CMD ["python", "modbus_cm4000_server.py"] 
>>>>>>> bb7f761b1fe8c713249ab87d0753ed0f4860f6a1:Server/Modbus_sim/Dockerfile
