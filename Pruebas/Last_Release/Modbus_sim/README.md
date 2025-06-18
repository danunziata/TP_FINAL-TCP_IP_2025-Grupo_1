# Simulador Modbus – PowerLogic CM4000

Simula un equipo PowerLogic real, expone registros por TCP:5020.

## Archivo Principal

- `modbus_cm4000_server.py`: genera datos realistas (tensión, corriente, potencia)
- `Dockerfile`: construye el contenedor con entorno Python
- `requirements.txt`: dependencias necesarias (pymodbus)

## Uso

Se lanza automáticamente por Docker Compose.
Los datos son accesibles por Telegraf en `tcp://modbus-sim:5020`.
