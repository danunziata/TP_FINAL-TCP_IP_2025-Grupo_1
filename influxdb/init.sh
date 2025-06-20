#!/bin/sh
set -e

INFLUX_URL=http://influxdb:8086
ORG=power_logic
TOKEN=token_telegraf

# Esperar a que InfluxDB esté listo para aceptar conexiones
until influx ping --host $INFLUX_URL > /dev/null 2>&1; do
  echo "⏳ Esperando a InfluxDB..."
  sleep 2
done

echo "✅ InfluxDB está listo."

# --- AÑADIDO: Crear el bucket principal 'mensualx6' para el dashboard ---
if ! influx bucket list --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN" | grep -q mensualx6; then
  echo "📦 Creando bucket 'mensualx6' con retención de 180 días..."
  influx bucket create --name mensualx6 --retention 180d --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"
else
  echo "✅ Bucket 'mensualx6' ya existe."
fi

# Crear bucket 'anualx4' para histórico a largo plazo
if ! influx bucket list --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN" | grep -q anualx4; then
  echo "📦 Creando bucket 'anualx4' con retención de 1460 días..."
  influx bucket create --name anualx4 --retention 1460d --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"
else
  echo "✅ Bucket 'anualx4' ya existe."
fi

# Crear bucket temporal para el sistema de alertas
if ! influx bucket list --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN" | grep -q powerlogic_warnings_tmp; then
  echo "📦 Creando bucket 'powerlogic_warnings_tmp' con retención de 1 día..."
  influx bucket create --name powerlogic_warnings_tmp --retention 1d --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"
else
  echo "✅ Bucket 'powerlogic_warnings_tmp' ya existe."
fi

# --- Opcional: Creación de tokens y secretos ---
# Crear secreto de ejemplo
influx secret update --key TOKEN_EXTRA --value otro_token \
  --org "$ORG" --host "$INFLUX_URL" --token "$TOKEN"

# Crear token con permisos de Lectura/Escritura
influx auth create \
  --org "$ORG" \
  --read-buckets --write-buckets \
  --token "token_lectura_escritura" \
  --description "Token RW para todos los buckets" \
  --host "$INFLUX_URL" --token "$TOKEN" || echo "⚠️  El token 'token_lectura_escritura' ya existe."

echo "✅ Script de inicialización de InfluxDB completado."
exit 0
