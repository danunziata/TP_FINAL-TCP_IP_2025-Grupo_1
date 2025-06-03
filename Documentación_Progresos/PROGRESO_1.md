## App de prueba 
Se creó una app (diferente a la que está en proceso) para hacer algunas pruebas de autenticación.

Se opta por usar la libreria "streamlint-authenticator" para implementar autenticación al ingresar a la  aplicación web desarrollada en Streamlit.

Se descarta la posibilidad de autentucación con cuenta de Google ya que hay que utiliar Google Cloud, el cual es pago y se quiere evitar esa situación.

### Primera implementación

Se utiliza Login funcional usando usuarios definidos en `config.yaml`.

Estructura agregada:
- `app.py` → script principal con formulario de login
- `config.yaml` → configuración de usuarios, contraseñas y cookies
- `requirements.txt` → dependencias necesarias
- `hashgen.py` → script auxiliar para generar hashes (en desarrollo)

Próximos pasos:
- Activar uso de contraseñas hasheadas
- Validar la seguridad de los tokens y persistencia de sesión

Los pasos para llevar a funcionamiento el programa son: 

- 1 ) Dentro de la rama `Elias` ejecutar los siguientes comandos : 
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
- 2 ) Ejecutar la app Streamlit :
```bash
streamlit run app.py
```
- 3 ) Acceso con usuarios de prueba : 

|   Usuario |   Constraseña |
|-----------|---------------|
|`admin`    |`admin`        |
|`userview` |`userview`     |


#### Descripción de los archivos

### `app.py`

Contiene la lógica de autenticación y la interfaz de login:

- Carga la configuración desde `config.yaml`.
- Usa `streamlit_authenticator.Authenticate()` para gestionar login y cookies.
- Muestra un formulario de login interactivo.
- Al autenticar correctamente, muestra contenido protegido.

### `config.yaml`

Archivo YAML con la configuración de:

- Usuarios (username, email, nombre, contraseña).
- Cookies (nombre, clave secreta, duración).

```yaml
credentials:
  usernames:
    admin:
      email: admin@example.com
      name: Administrador
      password: admin
    userview:
      email: userview@example.com
      name: Usuario View
      password: userview
cookie:
  expiry_days: 30
  key: some_secret_key
  name: ipsep_cookie
```

### `hashgen.py`

Script que permite generar hashes seguros para las contraseñas:

```python
import streamlit_authenticator as stauth

psw = input("Ingresa la contraseña: ")
hash = stauth.Hasher([psw]).generate()[0]
print("\nHash bcrypt generado:\n")
print(f'"{hash}"')
```

---

## Próximos pasos

- Implementación básica con texto plano.
- Migrar a contraseñas **hasheadas con bcrypt**.
- Separar usuarios por roles.
- Integrar pruebas automáticas de login.
- Documentar funcionalidades en español e inglés.

---