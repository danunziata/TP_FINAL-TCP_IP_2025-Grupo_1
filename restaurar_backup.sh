#!/bin/bash

# CONFIGURACIÓN
echo "Por favor escriba la fecha del backup en el formato AÑO-MES-DIA"
echo "Ejemplo: 2025-06-02 (debe incluir los 0s)"
read -p "Fecha del backup: " FECHA_BACKUP

NOMBRE_CONTENEDOR="tp_final-tcp_ip_2025-grupo_1-influxdb-1"
BACKUP_DIR_HOST="backups_influx/backup-$FECHA_BACKUP"
BACKUP_DIR_CONT="tmp/backup_restore"

# Verificar que la carpeta del backup exista
if [ ! -d "$BACKUP_DIR_HOST" ]; then
    echo "✅ La carpeta '$carpeta' NO existe."
    exit 2
fi

echo "📁 Copiando backup al contenedor..."
docker cp "$BACKUP_DIR_HOST" "$NOMBRE_CONTENEDOR:$BACKUP_DIR_CONT"
docker exec "$NOMBRE_CONTENEDOR" influx restore --full "$BACKUP_DIR_CONT"

if [ $? -eq 0 ]; then
    echo "✅ Restauración completada con éxito"
else
    echo "❌ ERROR en la restauración"
    exit 1
fi

echo "🧹 Eliminando carpeta temporal del contenedor..."
docker exec "$NOMBRE_CONTENEDOR" rm -rf "$BACKUP_DIR_CONT"

echo "✅ Proceso finalizado correctamente."