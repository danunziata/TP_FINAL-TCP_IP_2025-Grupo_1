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
influx bucket create --name tension --retention 180d --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"
influx bucket create --name potencia_activa --retention 180d --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"
influx bucket create --name potencia_reactiva --retention 180d --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"
influx bucket create --name potencia_aparente --retention 180d --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"
influx bucket create --name factor_potencia --retention 180d --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"
influx bucket create --name demanda --retention 1460d --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"

# Crear labels
# NO FUNCIONA A TRAVÉS DE Influx CLI
#influx label create --name "potencia" --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"
#influx label create --name "reactiva" --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"

# Asignar labels a buckets
# NO FUNCIONA A TRAVÉS DE Influx CLI
#influx bucket label add --bucket potencia_reactiva --label reactiva --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"

# Crear secret
influx secret update --key TOKEN_EXTRA --value otro_token --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"

# Crear token personalizado con permisos RW
influx auth create --org "$ORG"   --read-buckets --write-buckets   --token "token_lectura_escritura"   --description "Token RW buckets"   --host "$INFLUX_URL" --token "$TOKEN"
