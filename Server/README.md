## Pasos para levantar el servidor:

Antes de levantarlo revisar que no haya contenedores o procesos de linux que esten utilizando los mismos puertos que se van a utilizar para esto. Recomiendo borrar los containers, las network que no se utilicen o de trabajos previos, los volumenes (las imagenes dejarlas).

Una vez hecho esto, ubicarse en el mismo directorio que los archivos: `docker-compose.yml`, `telegraf.conf` y `init.sh`. Y escribir:
```bash
docker-compose up -d
```

Debería ya estar funcionando. Ahora para revisar si funciona correctamente conectar el equipo modbustcp o ejecutar el simulador de la rama `develop-vale`.

**NOTA:** *Este docker-compose es el mismo que se encuentra en la rama `develop-mati`, pero se le agregó un docker para Telegraf y se creó una red para interconectarlos y así evitar tener problemas de cambio de IP en la red docker cada vez que se inicia. **Es recomendable tener todas las imágenes del docker compose con versiones y no en `latest`, ya que si se actualiza alguna imagen, seguramente al querer levantar el servidor más a futuro, de error por incompatibilidad de versiones.***

**ACTUALIZACION**: Se agregaron 2 tasks a InfluxDB:
1. La primera calcula promedios cada 15 minutos y los guarda en un bucket llamado "promedios".
2. La segunda tarea mira los valores del ultimo minuto del bucket "mensualx6" y con el tag (_field) de "active_power", y todos aquellos que superen el umbral de 8000 se guardaran en un bucket llamado "alertas", esto lo puse así para poder verlo mas rapido y no tener q esperar 15 min. *Deben cambiarse los tiempos que mira a 15 minutos y el umbral que corresponde. Dicho umbral se puede sacar de algun registro del equipo modbusTCP (q no se cual es) o a traves de una suma de la ultima hora de consumo*. Los valores que se van guardando en alerta deberían coincidir el timestap con el del bucket mensualx6, es decir, se le mantiene el valor del tiempo en que fue medido y no cuando se realizo la tarea.