#!/bin/bash

# Levantar todo el stack de aplicaciones (en segundo plano con -d para que siga corriendo el script, y sin la linea --build
# --build demoraría más tiempo si alguna vez se ejecuta de nuevo este script, y si no se han realizado
# modificaciones, no es necesario --build)
docker compose up -d

sudo chmod +x limpieza_backups.sh
sudo chmod +x restaurar_backup.sh

ruta=$(pwd)
# Nombre del docker de InfluxDB
docker_influx=tp_final-tcp_ip_2025-grupo_1-influxdb-1

# Crear carpeta para los backups de InfluxDB
carpeta_backup=backups_influx
mkdir -p $carpeta_backup

# Agregar comandos al crontab
# Realizar backups los días Lunes, Miércoles y Viernes a las 00:10hs
comando_backup="10 0 * * 1,3,5 docker exec $docker_influx influx backup /backups/backup-\$(date +\%Y-\%m-\%d)"
(crontab -l 2>/dev/null; echo "$comando_backup") | sort -u | crontab -

# Copiar el backup a la PC host los días Lunes, Miércoles y Viernes a las 00:15hs
comando_copiar="15 0 * * 1,3,5 docker cp $docker_influx:/backups/backup-\$(date +\%Y-\%m-\%d) $ruta/$carpeta_backup/backup-\$(date +\%Y-\%m-\%d)"
(crontab -l 2>/dev/null; echo "$comando_copiar") | sort -u | crontab -

# Borrar los backups dentro del docker de InfluxDB los días Lunes, Miércoles y Viernes a las 00:20hs
comando_borrado="20 0 * * 1,3,5 docker exec $docker_influx rm -rf /backups/"
(crontab -l 2>/dev/null; echo "$comando_borrado") | sort -u | crontab -

# Borrar backups 3 veces al mes (días 1, 14 y 28 a las 00:20hs)
borrado_mensual="20 00 1,14,28 * * $ruta/limpieza_backups.sh"
(crontab -l 2>/dev/null; echo "$borrado_mensual") | sort -u | crontab -

# Calculo de factor de potencia cada 15 minutos
pip install influxdb-client==1.49.0
factor_potencia="*/15 * * * * /usr/bin/python3 $ruta/factor_potencia.py"
(crontab -l 2>/dev/null; echo "$factor_potencia") | sort -u | crontab -

# Ejecución calculo factor potencia en un primer instante
python3 factor_potencia.py

# Levantar MkDocs para el manual de usuario
pip install -r Manual/requirements.txt
cd Manual/manual
# Lo levanta en segundo plano con &, si se cierra la terminal no se termina con nohup
# Además se permite que accedan otros dispositivos desde afuera con --dev-addr
nohup mkdocs serve --dev-addr=0.0.0.0:8000 > mkdocs.log 2>&1 &

