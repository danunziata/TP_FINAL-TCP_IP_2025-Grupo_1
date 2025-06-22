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
# Mapeo real de registros según especificación
REGISTERS = {
    1100: 'Corriente de fase A',
    1101: 'Corriente de fase B',
    1102: 'Corriente de fase C',
    1103: 'Corriente de neutro',
    1120: 'Tensión de línea A',
    1121: 'Tensión de línea B',
    1122: 'Tensión de línea C',
    1124: 'Tensión A-N',
    1125: 'Tensión B-N',
    1126: 'Tensión C-N',
    1140: 'Potencia activa fase A',
    1141: 'Potencia activa fase B',
    1142: 'Potencia activa fase C',
    1143: 'Potencia activa total',
    1144: 'Potencia reactiva fase A',
    1145: 'Potencia reactiva fase B',
    1146: 'Potencia reactiva fase C',
    1147: 'Potencia reactiva total',
    1148: 'Potencia aparente fase A',
    1149: 'Potencia aparente fase B',
    1150: 'Potencia aparente fase C',
    1151: 'Potencia aparente total',
    1160: 'Factor de potencia fase A',
    1161: 'Factor de potencia fase B',
    1162: 'Factor de potencia fase C',
    1163: 'Factor de potencia total',
}


# Generador de datos aleatorios realistas
# Se asume que los registros son consecutivos y se llenan desde 1100 hasta 1163
# Los registros no definidos explícitamente se llenan con 0
def generate_cm4000_data():
    data = [0] * (1162 - 1099 + 1)  # Inicializa todos los registros en 0
    # Asignar valores realistas a cada registro
    data[0]  = int(random.uniform(10.0, 50.0) * 10)    # 1099 Corriente fase A
    data[1]  = int(random.uniform(10.0, 50.0) * 10)    # 1100 Corriente fase B
    data[2]  = int(random.uniform(10.0, 50.0) * 10)    # 1101 Corriente fase C
    data[3]  = int(random.uniform(0.0, 10.0) * 10)     # 1102 Corriente neutro
    data[20] = int(random.uniform(380.0, 420.0) * 10)  # 1119 Tensión línea A
    data[21] = int(random.uniform(380.0, 420.0) * 10)  # 1120 Tensión línea B
    data[22] = int(random.uniform(380.0, 420.0) * 10)  # 1121 Tensión línea C
    data[24] = int(random.uniform(220.0, 240.0) * 10)  # 1123 Tensión A-N
    data[25] = int(random.uniform(220.0, 240.0) * 10)  # 1124 Tensión B-N
    data[26] = int(random.uniform(220.0, 240.0) * 10)  # 1125 Tensión C-N
    data[40] = int(random.uniform(1000.0, 10000.0))    # 1139 Potencia activa fase A
    data[41] = int(random.uniform(1000.0, 10000.0))    # 1140 Potencia activa fase B
    data[42] = int(random.uniform(1000.0, 10000.0))    # 1141 Potencia activa fase C
    data[43] = data[40] + data[41] + data[42]          # 1142 Potencia activa total
    data[44] = int(random.uniform(500.0, 5000.0))      # 1143 Potencia reactiva fase A
    data[45] = int(random.uniform(500.0, 5000.0))      # 1144 Potencia reactiva fase B
    data[46] = int(random.uniform(500.0, 5000.0))      # 1145 Potencia reactiva fase C
    data[47] = data[44] + data[45] + data[46]          # 1146 Potencia reactiva total
    data[48] = int(random.uniform(1000.0, 12000.0))    # 1147 Potencia aparente fase A
    data[49] = int(random.uniform(1000.0, 12000.0))    # 1148 Potencia aparente fase B
    data[50] = int(random.uniform(1000.0, 12000.0))    # 1149 Potencia aparente fase C
    data[51] = data[48] + data[49] + data[50]          # 1150 Potencia aparente total
    data[60] = int(random.uniform(80.0, 100.0))        # 1159 FP fase A (escala x100)
    data[61] = int(random.uniform(80.0, 100.0))        # 1160 FP fase B
    data[62] = int(random.uniform(80.0, 100.0))        # 1161 FP fase C
    data[63] = int((data[60] + data[61] + data[62]) / 3) # 1162 FP total
    return data


async def update_registers(context, interval=30):
    while True:
        values = generate_cm4000_data()
        # Los registros inician en 1099, así que offset=1099
        context[0x00].setValues(3, 1099, values)  # 3 = holding registers
        await asyncio.sleep(interval)

async def run_server():
    # Crear el contexto del servidor
    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(1099, generate_cm4000_data()),
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