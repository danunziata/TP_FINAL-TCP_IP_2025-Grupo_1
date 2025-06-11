#!/bin/sh
set -e

# Esperar a que InfluxDB esté listo
until influx ping --host http://influxdb:8086 > /dev/null 2>&1; do
  echo "Esperando a InfluxDB..."
  sleep 2
done

INFLUX_URL=http://influxdb:8086
ORG=power_logic

# Token administrador (mismo que el usado en DOCKER_INFLUXDB_INIT_ADMIN_TOKEN)
ADMIN_TOKEN=token_telegraf

# Crear buckets si no existen
influx bucket create --name anualx4 --retention 1460d --org "$ORG" --host "$INFLUX_URL" --token "$ADMIN_TOKEN" || true
influx bucket create --name promedios --retention 0 --org "$ORG" --host "$INFLUX_URL" --token "$ADMIN_TOKEN" || true
influx bucket create --name alertas --retention 30d --org "$ORG" --host "$INFLUX_URL" --token "$ADMIN_TOKEN" || true

# Crear un token con permisos para tareas y guardar su valor
TASK_TOKEN=$(influx auth create \
  --org "$ORG" \
  --read-buckets --write-buckets \
  --read-tasks --write-tasks \
  --description "Token para tareas de promedio" \
  --host "$INFLUX_URL" --token "$ADMIN_TOKEN" \
  --json | grep '"token"' | cut -d '"' -f 4)

# Task 1 - Promedios
influx task create \
  --org "$ORG" \
  --host "$INFLUX_URL" \
  --token "$TASK_TOKEN" <<EOF
option task = {
  name: "promedio_potencia_cada_15m",
  every: 15m,
  offset: 1m
}

from(bucket: "anualx4")
  |> range(start: -15m)
  |> filter(fn: (r) => r._field == "active_power")
  |> aggregateWindow(every: 15m, fn: mean, createEmpty: false)
  |> to(bucket: "promedios", org: "$ORG")
EOF

# Task 2 - Crear task de alerta por potencia alta
influx task create \
  --org "$ORG" \
  --host "$INFLUX_URL" \
  --token "$TASK_TOKEN" <<EOF
option task = {
  name: "alerta_potencia_alta",
  every: 1m
}

from(bucket: "mensualx6")
  |> range(start: -1m)
  |> filter(fn: (r) => r._field == "active_power" and r._value > 8000)
  |> map(fn: (r) => ({ r with mensaje: "Potencia alta detectada" }))
  |> to(bucket: "alertas", org: "$ORG")
EOF

# Crear un secret (opcional)
influx secret update --key TOKEN_EXTRA --value otro_token --org "$ORG" --host "$INFLUX_URL" --token "$ADMIN_TOKEN"

# Crear token de lectura y escritura general (opcional)
influx auth create \
  --org "$ORG" \
  --read-buckets --write-buckets \
  --token "token_lectura_escritura" \
  --description "Token RW buckets" \
  --host "$INFLUX_URL" --token "$ADMIN_TOKEN"
