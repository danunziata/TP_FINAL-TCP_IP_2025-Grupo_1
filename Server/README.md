# Sistema de Monitoreo PowerLogic 4000

Este proyecto simula y monitorea parámetros eléctricos de un equipo PowerLogic CM4000 usando un flujo moderno: Modbus TCP → Telegraf → InfluxDB → Streamlit.

## Arquitectura General

```
[Simulador Modbus TCP]
   │
   │  (puerto 5020)
   ▼
[Telegraf (inputs.modbus)]
   │
   │  (HTTP API)
   ▼
[InfluxDB]
   │
   │  (consulta)
   ▼
[Streamlit]
```

---

## Configuración de InfluxDB por variables de entorno

La aplicación web (`pagina.py`) obtiene los parámetros de conexión a InfluxDB a través de variables de entorno. Esto permite personalizar fácilmente la URL, el token, la organización y el bucket sin modificar el código fuente.

**Fragmento relevante de `pagina.py`:**
```python
INFLUX_URL = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
INFLUX_TOKEN = os.getenv('INFLUXDB_TOKEN', 'token_telegraf')
INFLUX_ORG = os.getenv('INFLUXDB_ORG', 'power_logic')
INFLUX_BUCKET = os.getenv('INFLUXDB_BUCKET', 'mensualx6')
```
- `INFLUXDB_URL`: URL del servidor InfluxDB (por defecto: `http://influxdb:8086`)
- `INFLUXDB_TOKEN`: Token de autenticación para acceder a InfluxDB (por defecto: `token_telegraf`)
- `INFLUXDB_ORG`: Organización de InfluxDB (por defecto: `power_logic`)
- `INFLUXDB_BUCKET`: Bucket donde se almacenan los datos (por defecto: `mensualx6`)

Puedes definir estas variables en tu entorno, en tu archivo `.env`, o modificarlas directamente en el código si lo prefieres.

---

## Archivos principales

### 1. `Telegraf/telegraf.conf`
Archivo de configuración de **Telegraf**. Define:
- Cómo conectarse al servidor Modbus TCP (simulador o equipo real).
- Qué registros leer (corriente, voltaje, potencia, etc.).
- A qué bucket de InfluxDB enviar los datos.

**Fragmento clave:**
```toml
[[inputs.modbus]]
  controller = "tcp://modbus-sim:5020"
  slave_id = 1
  # ...
[[outputs.influxdb_v2]]
  urls = ["http://influxdb:8086"]
  token = "token_telegraf"
  bucket = "mensualx6"
```


### 1. `Modbus_sim/modbus_cm4000_server.py`
Simulador de un PowerLogic CM4000. Genera datos eléctricos realistas y los expone vía Modbus TCP en el puerto 5020. Permite probar todo el flujo sin hardware real. Se utiliza un Dockerfile para construir la imagen del **simulador Modbus TCP**. Instala dependencias y expone el puerto 5020 para que Telegraf pueda conectarse.

### 2. `Telegraf/init.sh`
Script de inicialización para crear buckets, tokens y secretos en InfluxDB antes de iniciar Telegraf. Se usa en el arranque del contenedor para asegurar que la base de datos esté lista y configurada.

### 3. `influxdb/init.sh`
Script de inicialización para InfluxDB. Crea buckets, tokens y secretos necesarios para la operación del sistema.

### 4. `Streamlit/Pagina_PowerLogic/pagina.py`
Aplicación web en **Streamlit** que consulta los datos almacenados en InfluxDB y los muestra en tiempo casi real (según la frecuencia de muestreo). Permite filtrar por fecha y fase, visualizar gráficos interactivos y exportar los datos.

---

## ¿Cómo levantar el sistema?

1. **Clona el repositorio y entra al directorio raíz.**
2. Asegúrate de tener Docker y Docker Compose instalados.
3. Levanta todos los servicios:
   ```bash
   docker-compose up -d
   ```
4. El simulador Modbus, Telegraf e InfluxDB se levantarán automáticamente. Puedes revisar los logs con:
   ```bash
   docker-compose logs -f
   ```
5. Ejecuta la aplicación Streamlit:
   ```bash
   streamlit run Streamlit/Pagina_PowerLogic/pagina.py
   ```
6. Accede a la interfaz web en [http://localhost:8501](http://localhost:8501)

---

## Notas
- Puedes modificar el archivo `telegraf.conf` para cambiar los registros leídos o la frecuencia de muestreo.
- El simulador puede ser reemplazado por un equipo real PowerLogic CM4000 si lo conectas en la red y ajustas el host/puerto en `telegraf.conf`.
- Los datos se almacenan en InfluxDB y pueden ser consultados o exportados desde la interfaz web.

---

**Desarrollado para pruebas, capacitación y monitoreo eléctrico.**
