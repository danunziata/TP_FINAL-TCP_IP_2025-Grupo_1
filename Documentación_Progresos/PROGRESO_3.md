## Prueba de LogIn avanzada 2
A toda la implementación anterior, relatada en `PROGRESO_2.md` se le agrega la opción de trabajar con Docker y abstraernos de una venv. 

### Segunda implementación

Se tiene una nueva opción, nombrada en la introducción, el Registro de Usuarios.

Estructura :
- `prueba_login.py` → Se le agrega la opción de activar notificaciones al mail regsitrado. Además, dicho mail deberá ser institucional (@ing.unrc.edu.ar)
- `config.yaml` → configuración de usuarios, contraseñas(ya hasheadas), cookies y variable que identifica si se quiere una notificación o no.
- `requirements.txt` → dependencias necesarias pero ésta vez con las versiones a utilziar específicas y no las "latest"

### Pasos para hacer pruebas

- 1 ) Dentro de la rama `Aaron` hacer una copia en otra rama y en el directorio `/Prueba`ejecutar los siguientes comandos :

```bash
docker build -t mi-streamlit-app . 
docker run --rm -p 8501:8501 mi-streamlit-app #Sacar --rm en el caso de que no quieras que se borre el contendedor una vez finalizado el proceso

```
- 2 ) Acceder a la página web mediante `localhost:8501` en el navegador y probar Registro y LogIn. 

### Descripción de los archivos

### `prueba_login.py`

Se agrega la opción de querer recibir notificaciones y de que el mail si o si sea institucional.

### `config.yaml`

Se agrega una variabe de notificaciones que puede ser `true` o `false`. En el caso de ser `true`, se puede usar una lógica de envío de mails para los warnings.

### `Dockerfile`

``` Docker
FROM python:3-slim

WORKDIR /app

COPY prueba_login.py config.yaml requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto 8501 (Streamlit)
EXPOSE 8501

# Ejecuta Streamlit en modo server, sin abrir navegador y escuchando en todas las interfaces
CMD ["streamlit", "run", "prueba_login.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Avances
A comparación de PROGRESO_2, se logró atomizar mucho mas la creación del interfaz y los features mencionados anteriormente que pueden ser útiles para el envío de mails y segurizar que no cualquier mail pueda ser registrado

---
## Próximos pasos

- Pensar una lógica para que se pueda entrar a la base de datos en el caso de querer enviar un warning a los mails introducidos (no está estrechamente relacionado a seguridad, pero debemos proveer las herramientas, como developers de dicha estructura, para que esa acción se lleve a cabo con éxito).

---