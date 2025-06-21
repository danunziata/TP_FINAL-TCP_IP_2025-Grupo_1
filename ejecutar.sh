#!/bin/bash

# Levantar todo el stack de aplicaciones
#docker compose up --build

# Agregar comando al crontab para realizar backups los días Lunes, Miércoles y Viernes
# a las 00:10hs
comando="10 0 * * 1,3,5 docker exec tp_final-tcp_ip_2025-grupo_1-influxdb-1 influx backup /backups/backup-$(date +\%Y-\%m-\%d)"

(crontab -l 2>/dev/null; echo "$comando") | sort -u | crontab -
