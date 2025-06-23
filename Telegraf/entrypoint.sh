#!/bin/bash

# Primero, ejecuta el one-shot config
echo "Running one-time Telegraf collection..."
/usr/bin/telegraf --config /etc/telegraf/telegraf_onetime.conf --once

# Luego, inicia el servicio principal de Telegraf
echo "Starting main Telegraf service..."
exec /usr/bin/telegraf --config /etc/telegraf/telegraf.conf