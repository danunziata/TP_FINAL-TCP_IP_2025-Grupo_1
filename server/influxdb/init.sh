#!/bin/sh
set -e

# Esperar a que InfluxDB esté listo
until influx ping --host http://influxdb:8086 > /dev/null 2>&1; do
  echo "Esperando a InfluxDB..."
  sleep 2
done

INFLUX_URL=http://influxdb:8086
ORG=power_logic
TOKEN=token_telegraf

# Crear buckets adicionales
influx bucket create --name anualx4 --retention 1460d --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"

# Crear secret
influx secret update --key TOKEN_EXTRA --value otro_token --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"

# Crear token personalizado con permisos RW
influx auth create --org "$ORG"   --read-buckets --write-buckets   --token "token_lectura_escritura"   --description "Token RW buckets"   --host "$INFLUX_URL" --token "$TOKEN"
