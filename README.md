# Documentacion de Telegraf

Telegraf, un agente basado en servidores, recoge y envía métricas y eventos de bases de datos, sistemas y sensores IoT. 
Escrito en Go, Telegraf se compila en un solo binario sin dependencias externas.Cexigando memoria muy mínima.

Tiene una estructura sencilla donde por un lado recibe datos (INPUTS), los formatea y los reenvia formateados hacia otra direccion (OUTPUTS). Soporta varios tipos de protocolos, entre los que se encuantran algunos como **MQTT**, **modbustcp**, etc. En el contexto de nuestra aplicación, recibe valores de registros desde un equipo MoudbusTCP, los formatea y los reenvia hacia una base de datos en InfluxDB.

```
TELEGRAF CONFIGURACIÓN GENERAL
│
├── [AGENT]
│   └── Configuración del agente (intervalo, precisión, etc.)
│
├── [[INPUTS]]
│   ├── [[inputs.cpu]]
│   │   └── Configuración específica del plugin de CPU
│   ├── [[inputs.mem]]
│   │   └── Configuración específica del plugin de memoria
│   ├── [[inputs.modbus]]
│   │   └── Configuración para leer desde dispositivos Modbus
│   └── ...otros plugins de entrada (disk, mqtt, http, etc.)
│
├── [[PROCESSORS]]
│   ├── [[processors.regex]]
│   │   └── Transformaciones o filtrado de datos
│   └── ...otros procesadores opcionales
│
├── [[AGGREGATORS]]
│   └── (opcional) Agrupación de métricas en intervalos
│
└── [[OUTPUTS]]
    ├── [[outputs.influxdb]]
    │   └── Configuración del servidor InfluxDB (host, token, etc.)
    ├── [[outputs.prometheus_client]]
    │   └── Exportar métricas como endpoint Prometheus
    └── ...otros outputs (mqtt, file, kafka, etc.)
```

### ¿Quién asigna el tiempo de medición?

Telegraf es el encargado de asignar la hora y fecha (timestamp) a cada valor que recolecta del equipo Modbus TCP, no el equipo esclavo ni InfluxDB.

### ¿Cómo funciona esto?

1. Telegraf hace una solicitud al dispositivo Modbus TCP (esclavo).

2. Recibe el valor del registro solicitado (por ejemplo, un número de temperatura, corriente, etc.).

3. En ese momento exacto, Telegraf adjunta un timestamp:

    "Este valor fue leído a las 13:42:15.123 del 2025-06-06".

4. Luego lo envía a InfluxDB, que simplemente almacena el valor con ese timestamp.

### ¿Y si hay retrasos?

El timestamp refleja el momento en que Telegraf recibe y procesa el dato, no el momento real de medición en el equipo, a menos que:

* El equipo tenga un reloj interno y exponga su timestamp (raro en Modbus clásico).

* O tú mismo lo leas como un registro más (si el esclavo lo proporciona). En este caso hay que crear un sript en python para que se acomoden los registros de dia, mes y hora con los valores medidos, ya que Telegraf no permite modificar su timestap por defecto. (*No es algo realmente necesario ya que mediremos valores en un intervalo de 15 minutos, por lo que con los timestaps de Telegraf debería alcanzar*).

## Explicación de la configuración de Telegraf realizada:

### `[agent]`:

| Parámetro                     | Significado                                                                                                                        |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `interval = "10s"`            | Telegraf recolecta métricas cada **10 segundos**.                                                                                  |
| `round_interval = true`       | Alinea la recolección con el reloj del sistema (por ejemplo, 10:00:00, 10:00:10, etc.). Útil para gráficas ordenadas.              |
| `metric_batch_size = 1000`    | Envia hasta **1000 métricas por lote** a los outputs (como InfluxDB).                                                              |
| `metric_buffer_limit = 10000` | Puede mantener en buffer hasta **10,000 métricas** si no logra enviarlas a tiempo (por ejemplo, si InfluxDB se cae temporalmente). |
| `collection_jitter = "0s"`    | Introduce una variación aleatoria en la recolección (para evitar que muchos agentes recojan a la vez). Aquí está desactivado.      |
| `flush_interval = "10s"`      | Telegraf **envía** los datos a los outputs cada **10 segundos**.                                                                   |
| `flush_jitter = "0s"`         | Introduce una variación aleatoria en el envío. Aquí está desactivado.                                                              |
| `precision = ""`              | Usa la precisión por defecto del plugin. Puedes poner `"s"`, `"ms"`, etc.                                                          |
| `hostname = "telegraf"`       | Define el nombre del host que aparece en las métricas (útil si hay muchos agentes).                                                |
| `omit_hostname = false`       | No omite el `hostname`. Es decir, **se incluirá** como una etiqueta en cada métrica.                                               |

### `[[outputs.influxdb_v2]]`:

| Parámetro      | Explicación                                                                                            |
| -------------- | ------------------------------------------------------------------------------------------------------ |
| `urls`         | Dirección del servidor de InfluxDB (en este caso dentro de Docker, por eso el hostname es `influxdb`). |
| `token`        | Token de autenticación generado en InfluxDB 2.x para permitir escritura.                               |
| `organization` | Nombre de la organización en InfluxDB.                                                                 |
| `bucket`       | Nombre del **bucket (base de datos lógica)** donde se almacenan los datos.                             |

Al tener dos bloques de salida, Telegraf duplicará cada métrica recolectada: una irá al bucket mensualx6 y otra a anualx4.

Esto es útil si:

* Quieres conservar distintos historiales (ej. uno de 6 meses, otro de 1 año).

* O aplicar diferentes retenciones por bucket.

### `[[inputs.modbus]]`:

| Parámetro    | Explicación                                                                                    |
| ------------ | ---------------------------------------------------------------------------------------------- |
| `name`       | Nombre identificador del input (aparece como medida en InfluxDB).                              |
| `controller` | Dirección IP y puerto del dispositivo Modbus (TCP). Puede ser un equipo físico o un simulador. |
| `slave_id`   | ID del esclavo Modbus (usualmente entre 1 y 247).                                              |

### `[[inputs.modbus.holding_registers]]`:

| Parámetro    | Explicación                                                                             |
| ------------ | --------------------------------------------------------------------------------------- |
| `name`       | Nombre del campo que se guardará en InfluxDB.                                           |
| `byte_order` | Orden de bytes para interpretar el dato (por ejemplo, `"AB"` para un valor de 16 bits). |
| `data_type`  | Tipo de dato que se leerá (aquí, `UINT16`, entero sin signo de 16 bits).                |
| `scale`      | Factor de escala que se aplica al valor leído (útil para representar decimales).        |
| `address`    | Dirección del registro holding (por ejemplo, `6` para `active_power`).                  |

### Resultados en InfluxDB:

Cada 10 segundos, Telegraf leerá los registros 0 y 6 del dispositivo y almacenará métricas como esta:
```
modbus_sim,host=telegraf active_power=320 voltaje=230  <timestamp>
```
Estas métricas se enviarán a ambos buckets (`mensualx6` y `anualx4`).

***Nota:** Cada versión de Telegraf tiene una manera distinta de formar su estructura y de llamar a los registros, por ejemplo en algunas versiones en vez de usar: `[[inputs.modbus.holding_registers]]`, se usa: `[[inputs.modbus.fields]]`. Si no se configura de manera correcta, el Docker de Telegraf no se levanta y da error si se ven sus Logs*

**Fuente:** [Documentación de Telegraf](https://docs.influxdata.com/telegraf/v1/?_gl=1*u1cc7p*_ga*MTY0MTE3NTYyOC4xNzQ2NDcwOTgw*_ga_CNWQ54SDD8*czE3NDkyMzUxOTEkbzE3JGcwJHQxNzQ5MjM1MTkzJGo2MCRsMCRoNzc3NDQyMzY.*_gcl_au*Mjg2NzIzODc1LjE3NDY0NzA5ODM.)
