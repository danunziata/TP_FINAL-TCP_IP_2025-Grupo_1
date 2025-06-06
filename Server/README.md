## Pasos para levantar en servidor:

Antes de levantarlo revisar que no haya contenedores o procesos de linux que esten utilizando los mismos puertos que se van a utilizar para esto. Recomiendo borrar los containers, las network que no se utilicen o de trabajos previos, los volumenes (las imagenes dejarlas).

Una vez hecho esto, ubicarse en el mismo directorio que los archivos: `docker-compose.yml`, `telegraf.conf` y `init.sh`. Y escribir:
```bash
docker-compose up -d
```

Debería ya estar funcionando. Ahora para revisar si funciona correctamente conectar el equipo modbustcp o ejecutar el simulador de la rama `develop-vale`.

**NOTA:** *Este docker-compose es el mismo que se encuentra en la rama `develop-mati`, pero se le agregó un docker para Telegraf y se creó una red para interconectarlos y así evitar tener problemas de cambio de IP en la red docker cada vez que se inicia. **Es recomendable tener todas las imágenes del docker compose con versiones y no en `latest`, ya que si se actualiza alguna imagen, seguramente al querer levantar el servidor más a futuro, de error por incompatibilidad de versiones.***
