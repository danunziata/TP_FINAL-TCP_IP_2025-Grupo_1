# Telegraf Agents Configuration

Este directorio contiene los archivos de configuración para los agentes Telegraf utilizados en el sistema de monitoreo.

## Propósito

Telegraf es un agente de código abierto para la recolección, procesamiento y envío de métricas y eventos. En este proyecto, se utilizan dos instancias de Telegraf para satisfacer diferentes requisitos de recolección de datos y retención en InfluxDB.

## Estructura del Directorio

Telegraf/
├── telegraf.conf           # Configuración para datos históricos/generales
└── telegraf_warnings.conf  # Configuración para datos de alerta (temporales)


## `telegraf.conf`

### Propósito

Este archivo de configuración está diseñado para la recolección de datos Modbus de **alta frecuencia** para **almacenamiento general e histórico** en InfluxDB.

### Detalles de Configuración

* **Intervalo de Recolección**: `interval = "10s"`. Esto significa que Telegraf recolectará datos de Modbus cada 10 segundos.
* **Fuente de Entrada (`[[inputs.modbus]]`)**:
    * Se conecta al simulador Modbus TCP (`tcp://modbus-sim:5020`). En un entorno real, esta dirección se cambiaría a la IP y puerto del dispositivo PowerLogic real.
    * `slave_id = 1`.
    * Define varios "holding registers" para la recolección de datos como `active_power`, `voltaje`, `voltaje_l2n`, `voltaje_l3n`, `current_l1`, `current_l2`, `current_l3`.
    * Especifica el `byte_order`, `data_type` y `scale` para cada registro. Es crucial que la escala (`scale`) coincida con cómo el simulador o el dispositivo real está enviando los datos (por ejemplo, si el voltaje se envía como 2250 para 225.0V, la escala debe ser 0.1).
* **Salidas (`[[outputs.influxdb_v2]]`)**:
    * Los datos se envían a dos buckets en InfluxDB: `mensualx6` y `anualx4`.
    * La retención para `mensualx6` es de 180 días, y para `anualx4` es de 1460 días (4 años), según la configuración en `influxdb/init.sh`.
    * Utiliza el `INFLUX_TOKEN` y `INFLUX_ORG` definidos en `docker-compose.yml`.

### Mapeo de Registros (Ejemplo de `telegraf.conf`)

| Nombre de Campo de InfluxDB | Dirección Modbus (Hex) | Tipo de Dato | Escala |
| :-------------------------- | :--------------------- | :----------- | :----- |
| `voltaje`                   | `0x0000`               | `UINT16`     | `1.0`  |
| `voltaje_l2n`               | `0x0001`               | `UINT16`     | `0.1`  |
| `current_l1`                | `0x0003`               | `UINT16`     | `0.1`  |
| `active_power`              | `0x0006`               | `UINT16`     | `1.0`  |
| *(y otros parámetros)* |                        |              |        |

## `telegraf_warnings.conf`

### Propósito

Este archivo de configuración está dedicado a la recolección de datos específicos para el **sistema de alertas**. La clave aquí es la **frecuencia de recolección** y el **bucket de destino temporal**.

### Detalles de Configuración

* **Intervalo de Recolección**: `interval = "1m"`. Esto significa que recolectará datos cada 1 minuto, lo cual es suficiente para la detección de alertas sin sobrecargar el almacenamiento.
* **Fuente de Entrada (`[[inputs.modbus]]`)**:
    * También se conecta al simulador Modbus (`tcp://modbus-sim:5020`).
    * Define un subconjunto de "holding registers" críticos para alertas: `voltaje`, `current_l1`, `active_power`.
    * Asegura que las escalas estén configuradas correctamente (`scale = 0.1` para voltaje y corriente L1, `scale = 1.0` para potencia activa).
* **Salidas (`[[outputs.influxdb_v2]]`)**:
    * Los datos se envían exclusivamente al bucket `powerlogic_warnings_tmp`.
    * Este bucket tiene una política de retención de **1 día** (configurada en `influxdb/init.sh`), lo que significa que los datos para alertas son efímeros y se purgan automáticamente después de 24 horas. Esto es fundamental para evitar el almacenamiento innecesario de datos que solo se necesitan para la lógica de alerta a corto plazo.

### Mapeo de Registros (Ejemplo de `telegraf_warnings.conf`)

| Nombre de Campo de InfluxDB | Dirección Modbus (Hex) | Tipo de Dato | Escala |
| :-------------------------- | :--------------------- | :----------- | :----- |
| `voltaje`                   | `0x0000`               | `UINT16`     | `0.1`  |
| `current_l1`                | `0x0003`               | `UINT16`     | `0.1`  |
| `active_power`              | `0x0006`               | `UINT16`     | `1.0`  |

## Integración con Docker Compose

Ambas instancias de Telegraf se ejecutan como servicios separados en `docker-compose.yml`, cada una con su propia configuración:

```yaml
# Extracto de docker-compose.yml
telegraf:
  # ... configuración para telegraf.conf ...
  volumes:
    - ./Telegraf/telegraf.conf:/etc/telegraf/telegraf.conf:ro

telegraf-warnings:
  # ... configuración para telegraf_warnings.conf ...
  volumes:
    - ./Telegraf/telegraf_warnings.conf:/etc/telegraf/telegraf.conf:ro
Esta separación asegura que la recolección de datos para el monitoreo general no interfiera con la recolección de datos para las alertas, y viceversa, permitiendo optimizar los intervalos y retenciones para cada propósito.
