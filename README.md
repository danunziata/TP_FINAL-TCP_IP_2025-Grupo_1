# Sistema de Monitoreo de Parámetros Eléctricos **PowerLogic CM4000**

Este proyecto es un sistema integral de **monitoreo** y **alerta** para dispositivos de medición eléctrica.  
Combina tecnologías modernas de _código abierto_ para la **recolección**, **almacenamiento**, **visualización** y **notificación** de datos; es ideal para laboratorios, entornos industriales o académicos.

---

## 1. Características Principales

* **Simulación de Dispositivo**  
  Simulador de equipos **PowerLogic CM4000** (Schneider Electric) vía **Modbus TCP** — permite pruebas sin hardware físico.

* **Recolección de Datos Robusta**  
  Telegraf adquiere datos de alta frecuencia y los envía a InfluxDB, añadiendo automáticamente la **franja horaria** (`DÍA` / `NOCHE`).

* **Base de Datos de Series Temporales**  
  **InfluxDB 2.x** para un almacenamiento eficiente y escalable con políticas de retención diferenciadas.

* **Visualización Interactiva**  
  Interfaz web en **Streamlit**: tiempo real, consultas históricas y exportación de reportes.

* **Sistema de Alertas Dinámico**  
  – Monitoreo continuo de umbrales (sensibles a franjas horarias).  
  – Notificación por e-mail personalizable.  
  – _Alert buffer_ para que nunca se pierdan eventos ni resúmenes.

* **Gestión de Usuarios con Roles**  
  Autenticación, perfiles y **asistente de configuración inicial** para franjas horarias.

* **Arquitectura Modular con Docker Compose**  
  Despliegue reproducible y consistente de todos los servicios.

---

## 2. Arquitectura y Componentes del Sistema

> Los servicios se orquestan con **Docker Compose**; cada contenedor tiene responsabilidades claras y un flujo de datos bien definido.

| Directorio / Archivo | Función principal |
|----------------------|-------------------|
| **`docker-compose.yml`** | Conecta todos los servicios (`influxdb`, `telegraf`, `modbus-sim`, `streamlit`, `checker_service`). |
| **`influxdb/`** | Script **`init.sh`** crea buckets: `anualx4` (histórico) y `powerlogic_warnings_tmp` (alertas). |
| **`Modbus_sim/`** | Simulador **`modbus_cm4000_server.py`** genera datos eléctricos aleatorios. |
| **`Telegraf/`** | `telegraf.conf` (cada 10 s) y `telegraf_warnings.conf` (cada 1 min, añade etiqueta `franja_horaria`). |
| **`Streamlit/`** | Lógica de interfaz, autenticación, gestión de usuarios y motor de alertas. |

Para detalles profundos, revisá los **README.md** particulares de cada subdirectorio.

---

## 3. Configuración y Despliegue

### 3.1 Requisitos  

* [Docker](https://www.docker.com/get-started/)  
* [Docker Compose](https://docs.docker.com/compose/install/)

### 3.2 Pasos de Despliegue

1. **Clonar el repositorio**

   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd <NOMBRE_DEL_REPOSITORIO>
   ```

2. **Preparar archivos de estado iniciales (💥 paso crítico)**  

   En `Streamlit/` deben existir (¡y NO estar en `.gitignore`!):

   | Archivo | Contenido inicial |
   |---------|-------------------|
   | `usuarios.json` | `[]` (o usuarios pre-cargados) |
   | `logs_alertas.json` | `[]` |
   | `pending_alerts_buffer.json` | `[]` |
   | `last_digest_sent_state.json` | `null` |
   | `reset_tokens.json` | `{}` |

   > Eliminá `umbral_config.json` y `alert_cooldown_state.json` si aún están presentes.

3. **Configurar `Streamlit/config.yaml`**

   * Comentá o dejá vacía la sección `franjas_horarias:` para que se ejecute el asistente en el primer login.  
   * Verificá `alert_digest_interval_minutes` y `notificaciones_generales`.

4. **Construir y levantar los contenedores**

   ```bash
   docker compose up --build -d
   ```

   El flag `--build` asegura que los cambios en Dockerfiles y scripts se apliquen.

5. **Acceder a la aplicación**

   ```
   http://localhost:8501
   ```

---

## 4. Acceso Inicial y Configuración

| Dato | Valor |
|------|-------|
| **Usuario admin** | `ipsepadmin` |
| **Email** | `admin@ing.unrc.edu.ar` |
| **Contraseña** | Hash inicial en `Streamlit/config.yaml` (cambiá con `reset_password_admin.py`). |

*Al primer login del admin, si `franjas_horarias` no está definido, aparecerá el asistente para programar umbrales de DÍA (08:00 – 20:00) y NOCHE (20:01 – 07:59).*

---

## 5. Guía para Desarrolladores

### 5.1 Archivos de Estado (_runtime_)

| Archivo | Propósito |
|---------|-----------|
| `logs_alertas.json` | Historial completo de alertas (lo gestiona `checker.py`). |
| `pending_alerts_buffer.json` | Cola de alertas pendientes (para el próximo e-mail digest). |
| `last_digest_sent_state.json` | Timestamp del último resumen enviado. |
| `reset_tokens.json` | Tokens seguros de recuperación de contraseña. |

### 5.2 `.gitignore` recomendado

```gitignore
# Python
__pycache__/
*.pyc

# Entornos
venv/
.env/

# IDE
.vscode/
.idea/

# Sistema & backups
.DS_Store
*~
*.bak
```

### 5.3 ¿Por qué existe `__pycache__/`?

* Guarda archivos compilados `.pyc` → **ejecución más rápida**.  
* **No** debe versionarse: es específico de versión de Python y SO, y siempre se regenera.

---

## 6. Anexo — Detalle de `docker-compose.yml`

> Fragmento simplificado: ajustá nombres de volumen/red según tu entorno.

```yaml
services:
  influxdb:
    image: influxdb:2.7
    ports: ["8086:8086"]
    volumes:
      - influxdb-data:/var/lib/influxdb2
    environment:
      DOCKER_INFLUXDB_INIT_MODE: setup
      DOCKER_INFLUXDB_INIT_USERNAME: ipsep
      DOCKER_INFLUXDB_INIT_PASSWORD: ipsep2025
      DOCKER_INFLUXDB_INIT_ORG: power_logic
      DOCKER_INFLUXDB_INIT_BUCKET: mensualx6
      DOCKER_INFLUXDB_INIT_RETENTION: 180d
      DOCKER_INFLUXDB_INIT_ADMIN_TOKEN: token_telegraf
    restart: unless-stopped

  influxdb-init:
    image: influxdb:2.7
    depends_on: [influxdb]
    volumes:
      - ./influxdb/init.sh:/init.sh:ro
    entrypoint: ["sh", "/init.sh"]

  telegraf:
    image: telegraf:1.28
    volumes:
      - ./Telegraf/telegraf.conf:/etc/telegraf/telegraf.conf:ro
    environment:
      INFLUX_TOKEN: token_telegraf
      INFLUX_ORG: power_logic
    depends_on: [influxdb, modbus-sim]
    restart: unless-stopped

  telegraf-warnings:
    image: telegraf:1.28
    volumes:
      - ./Telegraf/telegraf_warnings.conf:/etc/telegraf/telegraf.conf:ro
    environment:
      INFLUX_TOKEN: token_telegraf
      INFLUX_ORG: power_logic
    depends_on: [influxdb, modbus-sim]
    restart: unless-stopped

  modbus-sim:
    build:
      context: ./Modbus_sim
      dockerfile: Dockerfile
    command: ["sh", "-c", "while true; do python modbus_cm4000_server.py; sleep 900; done"]
    ports: ["5020:5020"]
    restart: unless-stopped

  streamlit:
    build:
      context: ./Streamlit
      dockerfile: Dockerfile
    command: ["streamlit", "run", "login.py"]
    ports: ["8501:8501"]
    volumes:
      - ./Streamlit:/app
    depends_on: [influxdb, telegraf-warnings]
    environment:
      INFLUXDB_URL: http://influxdb:8086
      INFLUXDB_TOKEN: token_telegraf
      INFLUXDB_ORG: power_logic
      INFLUXDB_BUCKET: mensualx6
      RESEND_API_KEY: <API_KEY>
      RESEND_FROM: <correo@dominio>
    restart: unless-stopped

  checker_service:
    build:
      context: ./Streamlit
      dockerfile: Dockerfile
    command: ["sh", "-c", "while true; do python checker.py; sleep 60; done"]
    volumes:
      - ./Streamlit:/app
    depends_on: [influxdb, telegraf-warnings]
    environment:
      INFLUXDB_URL: http://influxdb:8086
      INFLUXDB_TOKEN: token_telegraf
      INFLUXDB_ORG: power_logic
      INFLUXDB_BUCKET: powerlogic_warnings_tmp
      RESEND_API_KEY: <API_KEY>
      RESEND_FROM: <correo@dominio>
    restart: unless-stopped

volumes:
  influxdb-data:
```

---
