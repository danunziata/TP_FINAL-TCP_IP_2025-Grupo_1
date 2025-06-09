import random
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification
import logging
import asyncio

# Configuración de logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

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

async def update_registers(context, interval=2):
    while True:
        values = generate_cm4000_data()
        context[0x00].setValues(3, 0, values)  # 3 = holding registers
        await asyncio.sleep(interval)

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