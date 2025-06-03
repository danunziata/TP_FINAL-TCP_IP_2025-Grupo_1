# 🔐 IPSEP Login Demo (Seguridad - Etapa Inicial)

Este proyecto es un entorno de pruebas para implementar y testear la **seguridad del login** en una aplicación web usando [Streamlit](https://streamlit.io/) y [streamlit-authenticator](https://github.com/mkhorasani/streamlit-authenticator). Forma parte del trabajo colaborativo de nuestro equipo en la sección de **seguridad**.

> ⚠️ Las contraseñas actualmente están almacenadas en texto plano, solo con fines de prueba. Próximamente se integrará el hasheo seguro mediante `bcrypt`.

---

## 📁 Estructura del proyecto

```
.
├── app.py              # Código principal de la app Streamlit
├── config.yaml         # Configuración de usuarios, cookies y credenciales
├── hashgen.py          # Script para generar contraseñas hasheadas con bcrypt
├── requirements.txt    # Dependencias necesarias
```

---

## 🚀 Cómo correr la app

1. **Clonar el repositorio y activar el entorno virtual:**

```bash
git clone https://github.com/<usuario>/<repositorio>.git
cd <repositorio>
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Ejecutar la app Streamlit:**

```bash
streamlit run app.py
```

3. **Acceso con usuarios de prueba:**

| Usuario    | Contraseña |
|------------|------------|
| `admin`    | `admin`    |
| `userview` | `userview` |

---

## 🧩 Descripción de archivos

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

## 🧪 Próximos pasos

- ✅ Implementación básica con texto plano.
- 🔒 Migrar a contraseñas **hasheadas con bcrypt**.
- 🧾 Separar usuarios por roles.
- 🔁 Integrar pruebas automáticas de login.
- 📚 Documentar funcionalidades en español e inglés.

---

## ✍️ Comentarios de desarrollo

Estamos trabajando en una rama separada para no afectar el `README.md` ni la estructura del repositorio principal. Este entorno es únicamente para validar el **módulo de autenticación**, y se integrará al proyecto principal una vez finalizadas las pruebas.
