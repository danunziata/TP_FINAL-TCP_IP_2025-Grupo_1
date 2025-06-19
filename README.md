# Sistema de Monitoreo de Parámetros Eléctricos PowerLogic CM4000

Este proyecto es un sistema integral de monitoreo y alerta para dispositivos de medición eléctrica, diseñado como una solución robusta y escalable. Utiliza tecnologías modernas de código abierto para la recolección, almacenamiento, visualización y notificación de datos, siendo ideal para aplicaciones en laboratorios de electricidad, industria o entornos académicos.

## Características Principales

* **Simulación de Dispositivo**: Incluye un simulador de equipos PowerLogic CM4000 (Schneider Electric) mediante Modbus TCP, permitiendo pruebas y desarrollo sin necesidad de hardware físico.
* **Recolección de Datos Robusta**: Utiliza Telegraf como agente de recolección para adquirir datos de alta frecuencia a través del protocolo Modbus y enviarlos a InfluxDB, incluyendo **etiquetado de franjas horarias**.
* **Base de Datos de Series Temporales**: InfluxDB 2.x para almacenamiento eficiente y escalable de datos de series temporales, con diferentes políticas de retención para datos históricos y de alerta.
* **Visualización Interactiva**: Una interfaz web desarrollada con Streamlit que permite visualizar parámetros eléctricos en tiempo real, consultar datos históricos, y exportar reportes.
* **Sistema de Alertas Dinámico**: Monitoreo continuo de umbrales con **soporte para franjas horarias (DÍA/NOCHE)**, notificaciones por correo electrónico personalizables y un **sistema de buffer de alertas pendientes** para asegurar que no se pierdan notificaciones y se envíen resúmenes coherentes.
* **Gestión de Usuarios con Roles**: Sistema de autenticación de usuarios con roles (administrador y normal), funcionalidades para gestión de perfiles y usuarios, y un **asistente de configuración inicial** para franjas horarias.
* **Arquitectura Modular con Docker Compose**: Despliegue sencillo y gestión de servicios mediante Docker Compose, asegurando un entorno consistente y reproducible.

## Arquitectura del Sistema

El sistema se compone de varios servicios orquestados por Docker Compose, cada uno con una responsabilidad específica y un flujo de datos bien definido:

![Diagrama de Arquitectura](./docs/architecture.png) Para una comprensión más detallada de cada componente, consulta los READMEs específicos en cada subdirectorio:

* [**Configuración General (docker-compose.yml)**](./docker-compose.yml)
* [**InfluxDB**](./influxdb/README.md)
* [**Modbus Simulator**](./Modbus_sim/README.md)
* [**Streamlit Application & Backend**](./Streamlit/README.md)
* [**Telegraf Agents**](./Telegraf/README.md)

## Configuración y Despliegue

### Requisitos

* [Docker](https://www.docker.com/get-started/) y [Docker Compose](https://docs.docker.com/compose/install/) instalados.

### Pasos para el Despliegue

1.  **Clonar el Repositorio**:
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd <NOMBRE_DEL_REPOSITORIO>
    ```

2.  **Preparar Archivos de Estado Iniciales**:
    Asegúrate de que los siguientes archivos existan en `Streamlit/`. Si no existen, créalos con el contenido indicado:
    * `Streamlit/logs_alertas.json` (contenido: `[]`)
    * `Streamlit/last_digest_sent_state.json` (contenido: `null`)
    * `Streamlit/pending_alerts_buffer.json` (contenido: `[]`)
    * `Streamlit/reset_tokens.json` (contenido: `{}`)
    * `Streamlit/usuarios.json` (contenido: `[]` o tus usuarios iniciales si los tienes)
    * **Eliminar** `Streamlit/umbral_config.json` y `Streamlit/alert_cooldown_state.json` si existen.

3.  **Configurar `Streamlit/config.yaml`**:
    * **Abre `Streamlit/config.yaml` y asegúrate de que la sección `franjas_horarias:` esté comentada o vacía** si deseas que el asistente de configuración inicial se active la primera vez que un administrador inicie sesión.
    * **Copia y pega tus credenciales de usuario existentes** en la sección `credentials: usernames:` si tu archivo se ha restablecido.
    * Verifica `alert_digest_interval_minutes` y `notificaciones_generales`.

4.  **Construir y Ejecutar los Contenedores**:
    Desde el directorio raíz del proyecto:
    ```bash
    docker compose up --build -d
    ```
    El ` --build` es **esencial** para asegurarse de que los cambios en los Dockerfiles y scripts Python (Telegraf, Streamlit, Checker) se tomen.

5.  **Acceder a la Aplicación**:
    Una vez que todos los servicios estén en funcionamiento, la aplicación Streamlit estará disponible en:
    ```
    http://localhost:8501
    ```

## Acceso Inicial y Configuración

* **Usuario Administrador**:
    * **Username**: `ipsepadmin`
    * **Email**: `admin@ing.unrc.edu.ar`
    * **Contraseña**: La contraseña hasheada inicial se encuentra en `Streamlit/config.yaml`. Utiliza la herramienta `reset_password_admin.py` para establecer una contraseña conocida o si la olvidaste.

* **Asistente de Configuración Inicial**:
    * La primera vez que un administrador (`ipsepadmin`) inicie sesión y si `franjas_horarias` no está configurado en `config.yaml`, se presentará un asistente para definir las franjas horarias y sus umbrales por defecto (DÍA: 08:00-20:00, NOCHE: 20:01-07:59).

---

### **`docker-compose.yml` (README - Actualizado)**

```markdown
# docker-compose.yml

Este archivo es el corazón de la orquestación del sistema. Define y configura todos los servicios (contenedores Docker) que componen la aplicación PowerLogic Monitor, sus dependencias, volúmenes, puertos y variables de entorno.

## Estructura General

```yaml
services:
  # Definición de cada servicio (contenedor)
  influxdb:
  influxdb-init:
  telegraf:
  telegraf-warnings:
  modbus-sim:
  streamlit:
  checker_service:

volumes:
  # Definición de volúmenes persistentes

networks:
  # Definición de redes personalizadas (si aplica)
Sección services
Aquí se detallan cada uno de los servicios:

influxdb
image: influxdb:2.7: Utiliza la imagen oficial de InfluxDB versión 2.7.
ports: - "8086:8086": Mapea el puerto 8086 del contenedor (donde InfluxDB escucha) al puerto 8086 de la máquina host, permitiendo el acceso externo.
volumes: - influxdb-data:/var/lib/influxdb2: Persiste los datos de InfluxDB en un volumen llamado influxdb-data. Esto significa que los datos no se perderán si el contenedor es eliminado o recreado.
environment:: Variables de entorno utilizadas por InfluxDB para su configuración inicial (modo setup).
DOCKER_INFLUXDB_INIT_MODE=setup: Indica a InfluxDB que se configure en modo interactivo al primer inicio.
DOCKER_INFLUXDB_INIT_USERNAME=ipsep: Nombre de usuario inicial del administrador.
DOCKER_INFLUXDB_INIT_PASSWORD=ipsep2025: Contraseña inicial para el usuario administrador.
DOCKER_INFLUXDB_INIT_ORG=power_logic: Nombre de la organización predeterminada.
DOCKER_INFLUXDB_INIT_BUCKET=mensualx6: Nombre del bucket predeterminado que se crea.
DOCKER_INFLUXDB_INIT_RETENTION=180d: Política de retención para el bucket predeterminado (180 días).
DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=token_telegraf: Token de administrador inicial. Este token es crucial para que Telegraf y la aplicación Streamlit puedan interactuar con InfluxDB.
restart: unless-stopped: El contenedor se reiniciará automáticamente a menos que sea detenido manualmente.
influxdb-init
image: influxdb:2.7: Utiliza la misma imagen de InfluxDB.
depends_on: - influxdb: Este servicio se iniciará solo después de que influxdb esté en ejecución.
volumes: - ./influxdb/init.sh:/init.sh:ro: Monta el script local influxdb/init.sh dentro del contenedor como /init.sh en modo de solo lectura (:ro).
entrypoint: [ "sh", "/init.sh" ]: Ejecuta el script /init.sh al inicio del contenedor. Este script se encarga de crear buckets adicionales y tokens específicos que InfluxDB necesita una vez que está completamente inicializado (más allá de lo que hace DOCKER_INFLUXDB_INIT_MODE=setup).
telegraf
image: telegraf:1.28: Utiliza la imagen oficial de Telegraf versión 1.28.
volumes: - ./Telegraf/telegraf.conf:/etc/telegraf/telegraf.conf:ro: Monta el archivo de configuración Telegraf/telegraf.conf en la ubicación predeterminada de Telegraf dentro del contenedor. El modo ro (solo lectura) significa que el contenedor no puede modificar este archivo.
environment:: Variables de entorno pasadas a Telegraf.
INFLUX_TOKEN=token_telegraf: El token que Telegraf usará para autenticarse con InfluxDB.
INFLUX_ORG=power_logic: La organización de InfluxDB a la que Telegraf enviará los datos.
depends_on: - influxdb - modbus-sim: Telegraf necesita que InfluxDB y el simulador Modbus estén funcionando antes de iniciarse.
restart: unless-stopped: Reinicio automático.
networks: - default: Asegura que Telegraf esté en la misma red Docker que los otros servicios para poder comunicarse.
telegraf-warnings
image: telegraf:1.28: Otra instancia de Telegraf, misma imagen.
volumes: - ./Telegraf/telegraf_warnings.conf:/etc/telegraf/telegraf.conf:ro: Utiliza una configuración diferente (telegraf_warnings.conf) para la recolección de datos específicos de alertas, posiblemente con una frecuencia diferente.
environment:: Mismas variables de entorno para InfluxDB.
depends_on: - influxdb - modbus-sim: Misma dependencia.
restart: unless-stopped: Reinicio automático.
networks: - default: Misma red.
modbus-sim
build: context: ./Modbus_sim dockerfile: Dockerfile: Construye la imagen Docker para este servicio a partir del Dockerfile ubicado en Modbus_sim/.
command: ["sh", "-c", "while true; do python modbus_cm4000_server.py; sleep 900; done"]: Este comando sobrescribe el CMD del Dockerfile y ejecuta el servidor Modbus simulado en un bucle continuo, con una pausa de 900 segundos (15 minutos) entre reinicios del script si este finaliza. Esto asegura que el simulador siempre esté disponible.
ports: - "5020:5020": Mapea el puerto 5020 del contenedor (donde escucha el servidor Modbus) al puerto 5020 de la máquina host.
restart: unless-stopped: Reinicio automático.
networks: - default: Misma red.
streamlit
build: context: ./Streamlit dockerfile: Dockerfile: Construye la imagen Docker para la aplicación Streamlit a partir del Dockerfile en Streamlit/.
command: ["streamlit", "run", "login.py"]: (Línea crucial) Este comando indica a Docker que ejecute la aplicación Streamlit utilizando el archivo login.py (tu prueba_login.py renombrado) como punto de entrada.
ports: - "8501:8501": Mapea el puerto 8501 del contenedor (donde Streamlit escucha) al puerto 8501 de la máquina host, permitiendo el acceso a la interfaz web.
volumes: - ./Streamlit:/app: Monta el directorio local Streamlit/ dentro del contenedor en /app. Esto es muy importante porque permite que los cambios que realices en tus archivos Python y JSON (pagina.py, config.yaml, usuarios.json, logs_alertas.json, pending_alerts_buffer.json, etc.) sean visibles instantáneamente dentro del contenedor sin necesidad de reconstruir la imagen.
depends_on: - influxdb - telegraf-warnings: La aplicación Streamlit necesita que InfluxDB y el Telegraf de warnings estén funcionando para poder cargar y mostrar los datos.
environment:: Variables de entorno pasadas a la aplicación Streamlit.
INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET: Configuran la conexión de la aplicación a InfluxDB.
RESEND_API_KEY, RESEND_FROM: Credenciales para el servicio de envío de correos (Resend).
restart: unless-stopped: Reinicio automático.
networks: - default: Misma red.
checker_service
build: context: ./Streamlit dockerfile: Dockerfile: Construye la imagen Docker para este servicio a partir del mismo Dockerfile en Streamlit/. Esto significa que tendrá las mismas dependencias de Python y archivos base que el servicio streamlit.
command: ["sh", "-c", "while true; do python checker.py; sleep 60; done"]: Ejecuta el script checker.py en un bucle continuo, con una pausa de 60 segundos (1 minuto) entre ejecuciones. Esto es lo que permite el monitoreo y las alertas periódicas.
depends_on: - influxdb - telegraf-warnings: Necesita InfluxDB para consultar datos y Telegraf para que los datos estén llegando.
environment:: Variables de entorno necesarias para que checker.py se conecte a InfluxDB y use el servicio de correo.
volumes: - ./Streamlit:/app: También monta el directorio local Streamlit/, lo que permite que checker.py acceda a config.yaml, logs_alertas.json, pending_alerts_buffer.json, usuarios.json, etc.
networks: - default: Misma red.
restart: unless-stopped: Reinicio automático.
Sección volumes
influxdb-data:: Define un volumen con nombre que Docker gestionará. Este volumen se utiliza para almacenar de forma persistente los datos de InfluxDB, asegurando que no se pierdan cuando los contenedores sean recreados.
Sección networks
