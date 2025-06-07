## Prueba de LogIn avanzada
En base a la aplicación anterior, se hizo una mejora en la cual hay un menú de registro debajo del LogIn, el cual permite que un usuario nuevo se registre introduciendo sus datos.

Mediante la librería `streamlit-authenticator` podemos realizar un "hasheo" de la contraseña ingresada por el usuario y guardarla,junto a los otros datos cargados, en la base de datos, que es el archivo `configure.yaml`.

`streamlit-authenticator`, en la opción de registro, establece que el Mail a introducir tenga el formato adecuado, la contraseña tenga mayúsculas, minúsculas, caracteres especiales y número, la posibilidad de un "password hint" y verificación e Captcha. Todas estas features fueron utilizadas para proveer un registro lo mas seguro y completo posible. 


### Segunda implementación

Se tiene una nueva opción, nombrada en la introducción, el Registro de Usuarios.

Estructura :
- `prueba_login.py` → script principal con formulario de login y registro. Es un template proximo a unificarse con la app web desarrollada.
- `config.yaml` → configuración de usuarios, contraseñas(ya hasheadas) y cookies.
- `requirements.txt` → dependencias necesarias
- `generate_keys.py` → script auxiliar para generar hashes. Sirve mas como una forma manual de agregar usuarios y para pruebas. No es llamado por prueba_login.py ya que el hasheo se hace directamente en ese archivo.

### Pasos para hacer pruebas

- 1 ) Dentro de la rama `Aaron` , en el directorio `/Prueba`ejecutar los siguientes comandos : 
```bash
python3 -m venv venv #Creación del entorno virtual
source venv/bin/activate #Activación del mismo 
pip install -r requirements.txt #Instalar las librerias necesarias
```
- 2 ) Ejecutar la app Streamlit :
```bash
streamlit run prueba_login.py
```
- 3 ) Realizar un registro y rpobar el LogIn

### Descripción de los archivos

### `app.py`

Contiene la lógica de autenticación y la interfaz de login:

- Carga la configuración desde `config.yaml`.
- Usa `streamlit_authenticator` para gestionar login, registro y cookies.
- Muestra un formulario de login interactivo.
- Al autenticar correctamente, muestra contenido protegido.

### `config.yaml`

Archivo YAML con la configuración de:

- Usuarios (nombre, apellido, username, email, contraseña).
- Cookies (nombre, clave secreta, duración).

```yaml
cookie:
  expiry_days: 30
  key: your_cookie_key
  name: your_cookie_name
credentials:
  usernames:
  #Aquí se encontraría la información cargada en el registro.
```

### `generate_keys.py`

Script que permite generar hashes seguros para las contraseñas de forma manual, no utilizado para la prueba final pero si para validar funcionamientos.

## Avances
A comparación de PROGRESO_1, se logró el hasheo de contraseñas que se esperaba desarrollar para lograr una amyor seguridad y un registro de usuarios mas dinámico.

---
## Próximos pasos

- Segurizar la base de datos
- Pensar una lógica para que se pueda entrar a la base de datos en el caso de querer enviar un warning a los mails introducidos (no está estrechamente relacionado a seguridad, pero debemos proveer las herramientas, como developers de dicha estructura, para que esa acción se lleve a cabo con éxito).

---