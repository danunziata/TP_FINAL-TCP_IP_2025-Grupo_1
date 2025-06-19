# Modbus Simulator

Este directorio contiene el simulador de un dispositivo de monitoreo eléctrico PowerLogic CM4000 de Schneider Electric.

## Propósito

El `modbus_cm4000_server.py` simula el comportamiento de un equipo Modbus TCP real. Esto es invaluable para el desarrollo, pruebas y demostraciones del sistema de monitoreo sin la necesidad de tener un dispositivo físico Modbus conectado. Genera datos eléctricos aleatorios pero realistas para diversas métricas.

## Estructura del Directorio

Modbus_sim/
├── Dockerfile                  # Define la imagen Docker para el simulador
├── modbus_cm4000_server.py     # Script Python del simulador Modbus
└── requirements.txt            # Dependencias Python para el simulador
└── README.md                   # Este archivo


## `modbus_cm4000_server.py`

### Propósito

Este script implementa un servidor Modbus TCP que expone un conjunto de "holding registers". Cada registro se asocia a un parámetro eléctrico simulado (voltaje, corriente, potencia, etc.) y sus valores se actualizan periódicamente con datos generados aleatoriamente.

### Análisis Línea por Línea y Lógica

```python
import random
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification
import logging
import asyncio
import random: Para generar valores aleatorios para las métricas.
from pymodbus.server import StartAsyncTcpServer: Importa la función para iniciar un servidor Modbus TCP asíncrono.
from pymodbus.datastore import ...: Importa clases para definir el contexto de datos del servidor Modbus (dónde se almacenan los registros).
from pymodbus.device import ModbusDeviceIdentification: Importa para identificar el dispositivo Modbus simulado.
import logging: Para registrar información sobre el funcionamiento del servidor.
import asyncio: Para manejar operaciones asíncronas, ya que el servidor pymodbus es asíncrono.
Python
# Configuración de logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)
Configura el sistema de logging para mostrar mensajes informativos en la consola.
Python
# Parámetros típicos de un PowerLogic CM4000 (valores de ejemplo)
# Los registros pueden variar según el mapeo real del equipo
REGISTERS = {
    'voltage_l1n': 0,   # 0x0000
    'voltage_l2n': 1,   # 0x0001
    'voltage_l3n': 2,   # 0x0002
    'current_l1': 3,    # 0x0003
    'current_l2': 4,    # 0x0004
    'current_l3': 5,    # 0x0005
    'active_power': 6,  # 0x0006
    'reactive_power': 7,# 0x0007
    'apparent_power': 8,# 0x0008
    'frequency': 9,     # 0x0009
    'energy': 10,       # 0x000A
}
Un diccionario que mapea nombres legibles de parámetros a sus direcciones de registro Modbus (offsets). El servidor llenará los registros a partir de la dirección 0.
Python
# Generador de datos aleatorios realistas
def generate_cm4000_data():
    return [
        int(random.uniform(220.0, 240.0) * 10),  # voltage_l1n (escala x10)
        int(random.uniform(220.0, 240.0) * 10),  # voltage_l2n
        int(random.uniform(220.0, 240.0) * 10),  # voltage_l3n
        int(random.uniform(10.0, 50.0) * 10),    # current_l1 (escala x10)
        int(random.uniform(10.0, 50.0) * 10),    # current_l2
        int(random.uniform(10.0, 50.0) * 10),    # current_l3
        int(random.uniform(1000.0, 10000.0)),    # active_power (W)
        int(random.uniform(500.0, 5000.0)),      # reactive_power (VAR)
        int(random.uniform(1000.0, 12000.0)),    # apparent_power (VA)
        int(random.uniform(49.5, 50.5) * 100),   # frequency (escala x100)
        int(random.uniform(10000.0, 100000.0)),  # energy (Wh)
    ]
Esta función genera una lista de valores enteros que simulan las lecturas de los sensores.
Lógica de Escala: Algunos valores (voltaje, corriente, frecuencia) se multiplican por un factor (10 o 100) antes de convertirse a int. Esto simula equipos Modbus que envían valores como enteros y requieren una escala (ej. 2250 para 225.0V). Los agentes Telegraf están configurados para aplicar la escala inversa al leer.
Python
async def update_registers(context, interval=30):
    while True:
        values = generate_cm4000_data()
        context[0x00].setValues(3, 0, values)  # 3 = holding registers
        await asyncio.sleep(interval)
Esta es una corrutina asíncrona que se ejecuta en un bucle infinito.
values = generate_cm4000_data(): Genera un nuevo conjunto de datos.
context[0x00].setValues(3, 0, values): Actualiza los valores en el "holding register" del servidor Modbus. 0x00 es el ID de la unidad (slave ID), 3 es el tipo de registro (holding register), 0 es la dirección de inicio, y values es la lista de datos.
await asyncio.sleep(interval): Pausa la ejecución por el interval especificado (30 segundos por defecto) antes de actualizar los registros nuevamente.
Python
async def run_server():
    # Crear el contexto del servidor
    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(0, generate_cm4000_data()),
        zero_mode=True
    )
    context = ModbusServerContext(slaves=store, single=True)

    # Identificación del dispositivo
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'Schneider Electric'
    identity.ProductCode = 'CM4000'
    identity.VendorUrl = 'https://www.se.com/'
    identity.ProductName = 'PowerLogic Circuit Monitor Series 4000'
    identity.ModelName = 'CM4000'
    identity.MajorMinorRevision = '1.0'

    # Iniciar actualización periódica de registros
    asyncio.create_task(update_registers(context))

    print("Servidor Modbus TCP PowerLogic CM4000 simulado corriendo en 0.0.0.0:5020")
    await StartAsyncTcpServer(context, identity=identity, address=("0.0.0.0", 5020))

if __name__ == "__main__":
    asyncio.run(run_server())
store = ModbusSlaveContext(...): Crea un almacén de datos para el esclavo Modbus, inicializándolo con datos generados y configurándolo para el modo cero.
context = ModbusServerContext(...): Envuelve el almacén del esclavo en un contexto de servidor.
identity = ModbusDeviceIdentification(...): Define la información de identificación del dispositivo Modbus simulado.
asyncio.create_task(update_registers(context)): Programa la corrutina update_registers para que se ejecute en segundo plano, actualizando los valores del registro mientras el servidor está activo.
print(...): Muestra un mensaje en la consola indicando que el servidor está funcionando.
await StartAsyncTcpServer(...): Inicia el servidor Modbus TCP en la dirección 0.0.0.0 (todas las interfaces) y el puerto 5020.
if __name__ == "__main__": asyncio.run(run_server()): Si el script se ejecuta directamente, inicia el bucle de eventos de asyncio y ejecuta la función run_server.
Dockerfile
El Dockerfile se encarga de crear una imagen Docker que contiene el entorno Python necesario y el script modbus_cm4000_server.py.

Análisis Línea por Línea y Lógica
Dockerfile
FROM python:3.9-slim
FROM python:3.9-slim: Define la imagen base para el contenedor. En este caso, una imagen ligera de Python 3.9.
Dockerfile
WORKDIR /app
WORKDIR /app: Establece el directorio de trabajo predeterminado dentro del contenedor a /app. Todos los comandos posteriores se ejecutarán desde este directorio.
Dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get update: Actualiza la lista de paquetes disponibles en el sistema operativo base.
&& apt-get install -y --no-install-recommends netcat-openbsd iproute2: Instala paquetes del sistema operativo necesarios. netcat-openbsd y iproute2 son utilidades de red que pueden ser útiles para depuración dentro del contenedor, aunque pymodbus no las necesita directamente. --no-install-recommends evita la instalación de paquetes adicionales no estrictamente necesarios.
&& rm -rf /var/lib/apt/lists/*: Limpia el caché de paquetes para reducir el tamaño final de la imagen Docker.
Dockerfile
COPY requirements.txt .
COPY requirements.txt .: Copia el archivo requirements.txt desde el contexto de construcción (el directorio Modbus_sim/ local) al directorio de trabajo (/app) dentro del contenedor. Esto se hace antes de instalar otras cosas para aprovechar el cache de Docker.
Dockerfile
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade pip: Actualiza pip a su última versión dentro del contenedor.
&& pip install --no-cache-dir -r requirements.txt: Instala todas las dependencias de Python listadas en requirements.txt (pymodbus en este caso). --no-cache-dir desactiva el caché de pip, lo que también ayuda a reducir el tamaño de la imagen.
Dockerfile
COPY modbus_cm4000_server.py .
COPY modbus_cm4000_server.py .: Copia el script principal del simulador Modbus al directorio de trabajo.
Dockerfile
EXPOSE 5020
EXPOSE 5020: Declara que el contenedor escuchará en el puerto 5020 en tiempo de ejecución. Esto es puramente informativo para Docker; el mapeo real del puerto se realiza en docker-compose.yml.
Dockerfile
CMD ["python", "modbus_cm4000_server.py"]
CMD ["python", "modbus_cm4000_server.py"]: Define el comando predeterminado que se ejecutará cuando el contenedor se inicie sin un comando explícito. En docker-compose.yml, este CMD es sobrescrito por la instrucción command: ["sh", "-c", "while true; do python modbus_cm4000_server.py; sleep 900; done"].
Flujo de Funcionamiento del Simulador Modbus
El servicio modbus-sim se inicia, construyendo su imagen Docker si es necesario.
Dentro del contenedor, el script modbus_cm4000_server.py comienza a ejecutarse.
El servidor Modbus TCP se levanta en el puerto 5020 del contenedor.
Una tarea asíncrona dentro del script comienza a actualizar los valores de los registros Modbus cada 30 segundos con datos simulados.
El puerto 5020 del contenedor está mapeado al puerto 5020 del host (5020:5020), lo que permite que Telegraf (y potencialmente otras herramientas externas) se conecten a él para leer los datos Modbus.
