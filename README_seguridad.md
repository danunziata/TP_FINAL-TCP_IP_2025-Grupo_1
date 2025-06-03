# IPSEP - App de Prueba de Seguridad en Login

Esta aplicación es un ejemplo funcional desarrollado en **Python con Streamlit**, con el objetivo de explorar y asegurar el proceso de **autenticación de usuarios** para proyectos internos del equipo de ciberseguridad de IPSEP.

---

## 🔍 Objetivo del Proyecto

Construir una app web ligera donde se pueda:

* Implementar y probar autenticación de usuarios con contraseñas cifradas.
* Validar la integridad del archivo de configuración (`config.yaml`).
* Gestionar de forma segura los usuarios y contraseñas.

---

## 🚀 Tecnologías utilizadas

* **Python 3.11**
* **Streamlit**
* **Streamlit Authenticator** (`streamlit-authenticator`)
* **bcrypt** (para hashing seguro de contraseñas)
* **PyYAML** (lectura del archivo `config.yaml`)

---

## 📂 Estructura del Proyecto

```
tcp/
├── app.py              # App principal de Streamlit
├── config.yaml         # Usuarios, contraseñas y cookies
├── hashgen.py          # Script para generar hashes bcrypt
├── requirements.txt    # Dependencias del proyecto
├── .gitignore          # Archivos que git ignora
└── README.md           # Documentación del proyecto
```

---

## 🔐 Autenticación con Hash Bcrypt

Las contraseñas se almacenan usando el algoritmo **bcrypt**. Se genera el hash mediante el script `hashgen.py`:

```bash
$ python hashgen.py
Ingresa la contraseña: admin123

Hash bcrypt generado:
"$2b$12$EIvVKFhrk4Tk4FZlNEm2vOGL9aRxxtcSblnW0xVYd6AHOMAx9eHE2"
```

Este valor se copia luego al archivo `config.yaml`.

---

## 🔧 Cómo usar la aplicación

### 1. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # En macOS/Linux
# o .\venv\Scripts\activate en Windows
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación

```bash
streamlit run app.py
```

---

## 💳 Estructura del `config.yaml`

```yaml
credentials:
  usernames:
    admin:
      email: admin@example.com
      name: Administrador
      password: "$2b$12$..."
    userview:
      email: userview@example.com
      name: Usuario View
      password: "$2b$12$..."

cookie:
  expiry_days: 30
  key: some_secret_key
  name: ipsep_cookie
```

---

## 📚 Detalle de los archivos principales

### `app.py`

Contiene:

* Lectura de `config.yaml` con validación de estructura.
* Configuración del autenticador con `streamlit_authenticator`.
* Verificación de usuario/contraseña.
* Vista de login e interfaz principal tras autenticación.

**Fragmento clave:**

```python
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)
```

---

### `hashgen.py`

Script independiente para generar hashes bcrypt:

```python
import streamlit_authenticator as stauth

password = input("Ingresa la contraseña: ")
hash = stauth.Hasher([password]).generate()[0]
print("\nHash bcrypt generado:\n")
print(f'"{hash}"')
```

---

## 📖 Buenas prácticas de seguridad aplicadas

* No se almacenan contraseñas en texto plano.
* Se validan claves de configuración antes de continuar.
* Separamos el hash en un script externo (`hashgen.py`) para evitar errores humanos.
* Se usa bcrypt con costo 12.

---

## 🤔 TO-DO / Mejoras futuras

* Implementar roles de acceso (admin, lector, etc).
* Cifrado completo del `config.yaml` en producción.
* Expiración forzada de sesión inactiva.
* Logging de intentos fallidos.

---

## 📡 Licencia

Uso interno IPSEP. Proyecto de prueba sin fines comerciales.
