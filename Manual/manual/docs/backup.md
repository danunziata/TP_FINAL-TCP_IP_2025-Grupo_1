# Backups y Restauración de la Base de Datos

Éste apartado contiene acciones que pueden ser realizadas solo si se tiene acceo al servidor, por lo que se hará una actualización en la cual se pueda realizar un acceso simple a la misma.

## Creación Automática de Backups

- Los backups se generan automáticamente mediante un proceso que comienza los **lunes, miércoles y viernes a las 00:10hs** y termina a las **00:20hs**

## Limpieza Automática de Backups Antiguos

- Se eliminan automáticamente los backups locales con más de **30 días** de antigüedad.
- Esta limpieza se ejecuta los días **1, 14 y 28 de cada mes a las 00:20hs**.

## Restauración de Backups

En el caso que se quiera cargar un backup viejo, se deben realizar los siguientes pasos:

**Pasos para realizar una restauración:**

- 1) Abrimos una terminal con la combinación de teclas `ctrl + T` o buscando `Emulador de Terminal` en el buscador ubicado arriba a la izquierda.

- 2) Escribimos la siguiente combinación en la terminal y damos Enter :

```bash
./restaurar_backup.sh
```

- 3) Ésto nos mostrará lo siguiente :

```bash
Por favor escriba la fecha del backup en el formato AÑO-MES-DIA
Ejemplo: 2025-06-02 (debe incluir los 0s)
Fecha del backup: 
```
En `Fecha del backup` se debe escribir la fecha del backup de datos que se desee recuperar.

**Advertencia : Éste un proceso destructivo, si hay información distinta, se pueden llegar a sobreescribir datos** 

## Ubicación de los Backups

- Todos los backups se almacenan en la carpeta `backups_influx/` en el directorio raíz del proyecto.
- Cada backup se guarda en una subcarpeta con el nombre `backup-AAAA-MM-DD`.
