#!/bin/bash

# Obtiene la ruta absoluta del directorio donde está el script
script_dir="$(cd "$(dirname "$0")" && pwd)"
backup_dir="$script_dir/backups_influx"

# Fecha de corte: 30 días atrás
fecha_limite=$(date -d '30 days ago' +%Y-%m-%d)

# Recorre todas las carpetas con el patrón backup-YYYY-MM-DD
for folder in "$backup_dir"/backup-*; do
    # Verifica que sea un directorio
    [ -d "$folder" ] || continue

    # Extrae la fecha del nombre del directorio
    folder_name=$(basename "$folder")
    fecha_folder=${folder_name#backup-}

    # Verifica que la fecha extraída sea válida (formato YYYY-MM-DD)
    if [[ "$fecha_folder" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        # Compara fechas
        if [[ "$fecha_folder" < "$fecha_limite" ]]; then
            echo "Eliminando carpeta antigua: $folder"
            rm -rf "$folder"
        fi
    fi
done
