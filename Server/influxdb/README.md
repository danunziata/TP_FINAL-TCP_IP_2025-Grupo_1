# Estructura
Habrá un bucket principal llamado "mensualx6", el cual contendrá 6 meses de información con todos los datos que precisen de esta retención. Y habrá otro bucket llamado "anualx4", el cual tendrá 4 años de retención (para la demanda de potencia).

# Tasks
Cada cierto tiempo especifico, o de acuerdo a parametros de tiempo (a cierto día y hora), permiten realizar:  
Procesamiento de datos: Calcular promedios, máximos, mínimos, etc.  
Limpieza de datos: Filtrar datos corruptos o irrelevantes.  
Escritura automática: Guardar resultados procesados en otro bucket.  
Reenvío de datos: Mover datos de un bucket a otro, incluso con agregación.  
Alarmas (usando http.post): Notificar si un valor supera un umbral  
## Every

## Cron
Formato: Minuto  -   Hora    -   Día (mes)   -   Mes     -   día (semana)    
\*	any value  
,	value list separator  
\-	range of values  
/	step values  
@yearly	(non-standard)  
@annually	(non-standard)  
@monthly	(non-standard)  
@weekly	(non-standard)  
@daily	(non-standard)  
@hourly	(non-standard)  
@reboot	(non-standard)  

Link: [Cron](https://crontab.guru/#0_4_8-14_*_*)

Ejemplo:  
“At minute 0 past hour 0 and 12 on day-of-month 1 in every 2nd month.”  
0 0,12 1 */2 *
