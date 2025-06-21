#!/bin/bash

# Levantar todo el stack de aplicaciones (en segundo plano con -d para que siga corriendo el script, y sin la linea --build
# --build demoraría más tiempo si alguna vez se ejecuta de nuevo este script, y si no se han realizado
# modificaciones, no es necesario --build)
docker compose up -d

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
