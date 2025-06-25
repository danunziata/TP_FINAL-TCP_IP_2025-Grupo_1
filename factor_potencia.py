import logging
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

# === Configuración de logging ===
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Parámetros de conexión
URL    = "http://localhost:8086"     # Ajustá si tu servidor es distinto
ORG    = "power_logic"
BUCKET = "mensualx6"
TOKEN  = "token_telegraf"

# Inicializo cliente y APIs
client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
write  = client.write_api(write_options=SYNCHRONOUS)  # Escritura síncrona
query  = client.query_api()

# Fases y tags de consulta
phases = ["a", "b", "c", "total"]
active_tags   = {ph: f"potencia_activa_{ph}"   for ph in phases}
apparent_tags = {ph: f"potencia_aparente_{ph}" for ph in phases}

def get_last_value(field: str):
    """Devuelve el último valor (float) de un campo, o None si no hay datos."""
    flux = f'''
    from(bucket: "{BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r._field == "{field}")
      |> last()
    '''
    logging.debug(f"Ejecutando consulta Flux para campo '{field}'")
    tables = query.query(flux)
    if not tables or not tables[0].records:
        logging.debug(f"No se encontraron registros para '{field}'")
        return None
    value = tables[0].records[0].get_value()
    logging.debug(f"Último valor de '{field}': {value}")
    return value

def compute_and_write():
    now = datetime.utcnow()
    logging.info("=== Inicio de cálculo y escritura de Factor de Potencia ===")

    # Diccionario para acumular los campos del punto
    fields = {}

    for ph in phases:
        logging.debug(f"Procesando fase '{ph}'")
        P = get_last_value(active_tags[ph])
        S = get_last_value(apparent_tags[ph])

        if P is None or S is None or S == 0:
            pf = 0.0
            logging.warning(f"Fase '{ph}': datos insuficientes o S=0, PF=0")
        else:
            pf = P / S
            logging.debug(f"Factor de potencia crudo para '{ph}': {pf}")

        # Nombre del campo según fase
        field_name = f"factor_potencia_{ph}"
        fields[field_name] = float(pf)
        logging.info(f"{field_name} = {pf:.4f}")

    # Armo un único Point con measurement "modbus", tags comunes y todos los campos
    point = (
        Point("modbus")
        .tag("name", "modbus-sim")
        .tag("slave_id", "1")
        .tag("type", "holding_register")
        .tag("host", "telegraf")
        .field("factor_potencia_a",    fields["factor_potencia_a"])
        .field("factor_potencia_b",    fields["factor_potencia_b"])
        .field("factor_potencia_c",    fields["factor_potencia_c"])
        .field("factor_potencia_total",fields["factor_potencia_total"])
        .time(now, WritePrecision.NS)
    )

    # Escribo el punto en InfluxDB
    write.write(bucket=BUCKET, org=ORG, record=point)
    logging.info("Se escribió el punto de factor de potencia en measurement 'modbus' con los tags adicionales.")

if __name__ == "__main__":
    try:
        compute_and_write()
    except Exception as e:
        logging.exception(f"Ocurrió un error inesperado: {e}")
    finally:
        client.close()
        logging.info("Conexión a InfluxDB cerrada.")
