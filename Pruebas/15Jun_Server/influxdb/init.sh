#!/bin/sh
set -e

INFLUX_URL=http://influxdb:8086
ORG=power_logic
TOKEN=token_telegraf

# Esperar a que Influx esté listo
until influx ping --host $INFLUX_URL > /dev/null 2>&1; do
  echo "⏳ Esperando a InfluxDB..."
  sleep 2
done

# Crear bucket 'anualx4' si no existe
if ! influx bucket list --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN" | grep -q anualx4; then
  echo "📦 Creando bucket 'anualx4'..."
  influx bucket create --name anualx4 --retention 1460d --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"
else
  echo "✅ Bucket 'anualx4' ya existe."
fi

# Crear bucket temporal para alertas si no existe
if ! influx bucket list --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN" | grep -q powerlogic_warnings_tmp; then
  echo "📦 Creando bucket 'powerlogic_warnings_tmp'..."
  influx bucket create --name powerlogic_warnings_tmp --retention 1d --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"
else
  echo "✅ Bucket 'powerlogic_warnings_tmp' ya existe."
fi

# Crear secreto ejemplo
influx secret update --key TOKEN_EXTRA --value otro_token \
  --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"

# Crear token RW
influx auth create \
  --org "$ORG" \
  --read-buckets --write-buckets \
  --token "token_lectura_escritura" \
  --description "Token RW buckets" \
  --host "$INFLUX_URL" --token "$TOKEN" || echo "⚠️ Token ya existe."

echo "✅ Script de inicialización completado."
exit 0
