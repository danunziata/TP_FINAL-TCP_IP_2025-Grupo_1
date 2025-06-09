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
influx bucket create --name promedios --retention 0 --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"

# Crear Task que calcula promedios cada 15 min
influx task create \
  --org "$ORG" \
  --host http://influxdb-influxdb-1:8086 \    # IMPORTANTE: es el nombre del servicio que aparece en el docker compose
  --token "$TOKEN" <<EOF
option task = {
  name: "promedio_potencia_cada_15m",
  every: 15m,
  offset: 1m
}

from(bucket: "anualx4")
  |> range(start: -15m)
  |> filter(fn: (r) => r.tipo == "Potencia")
  |> aggregateWindow(every: 15m, fn: mean, createEmpty: false)
  |> to(bucket: "promedios", org: "$ORG")
EOF

# Crear secret
influx secret update --key TOKEN_EXTRA --value otro_token --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"

# Crear token personalizado con permisos RW
influx auth create --org "$ORG"   --read-buckets --write-buckets   --token "token_lectura_escritura"   --description "Token RW buckets"   --host "$INFLUX_URL" --token "$TOKEN"
