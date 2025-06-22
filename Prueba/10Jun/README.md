# 🛡️ Prueba de Login con Streamlit + Autenticación

Este entorno está diseñado para probar un sistema de login básico utilizando `streamlit-authenticator` en una app de Streamlit. Es útil para evaluar cómo implementar autenticación con usuarios predefinidos, ya sea con contraseñas en texto plano (para pruebas) o hasheadas con bcrypt.

---

## 📂 Estructura de archivos

```
10Jun/
│
├── config.yaml               # Configuración de usuarios y cookies
├── Dockerfile                # Instrucciones para construir imagen Docker
├── generate_keys.py          # Script para generar claves FERNET
├── prueba_login.py           # App principal de login
├── requirements.txt          # Dependencias
```

---

## 🔐 Usuarios de prueba

| Usuario   | Contraseña |
|-----------|------------|
| `admin`   | `admin`    |
| `userview`| `userview` |

> En esta versión se usan contraseñas en texto plano, pero se recomienda usar hashes bcrypt (ver más abajo).

---

## ⚙️ Configuración (`config.yaml`)

Ejemplo de formato:

```yaml
cookie:
  expiry_days: 30
  key: your_cookie_key
  name: your_cookie_name

credentials:
  usernames:
    admin:
      email: admin@example.com
      name: Administrador
      password: "admin"
    userview:
      email: userview@example.com
      name: Usuario View
      password: "userview"
```

---

## 🔐 ¿Cómo generar contraseñas hasheadas?

Ejecutar:

```bash
python generate_keys.py
```

Este script imprimirá un hash bcrypt para la contraseña ingresada. Reemplazar en `config.yaml`.

---

## 🐳 Cómo correr con Docker

1. Desde la carpeta `10Jun/`, construir la imagen:

```bash
docker build -t streamlit-login-app .
```

2. Ejecutar el contenedor:

```bash
docker run -p 8501:8501 streamlit-login-app
```

3. Abrir la app en tu navegador:

[http://localhost:8501](http://localhost:8501)

---

## 🐳 Ejecución con Docker Compose (modo persistente)

Este proyecto incluye un `docker-compose.yml` para asegurar que la configuración del sistema se mantenga persistente incluso si el equipo se apaga o reinicia.

### 🔧 Cómo ejecutar:

1. Construir la imagen (solo la primera vez o cuando haya cambios):

```bash
docker-compose build
```

2. Ejecutar la app:

```bash
docker-compose up
```

3. Detener la app:

```bash
docker-compose down
```

---

## 🗃️ Persistencia de Usuarios en Docker

Esta aplicación almacena los usuarios registrados en un archivo `config.yaml` que es persistente gracias a un **volumen Docker** llamado `login_config_data`.

Este volumen asegura que, aunque el contenedor se reinicie o se reconstruya, los usuarios registrados **no se pierdan**.

---

## 💾 Hacer Backup del archivo de configuración

Para generar una copia de seguridad del volumen (usuarios y configuración):

```bash
docker run --rm \
  -v login_config_data:/volume \
  -v $PWD:/backup \
  alpine tar czf /backup/config_backup.tar.gz -C /volume .
```

Esto crea un archivo `config_backup.tar.gz` en tu carpeta actual.

---

## 🔁 Restaurar desde un Backup

```bash
docker run --rm \
  -v login_config_data:/volume \
  -v $PWD:/backup \
  alpine tar xzf /backup/config_backup.tar.gz -C /volume
```

> Asegurate de que el contenedor esté detenido (`docker-compose down`) antes de restaurar.

---

## 📦 Archivos Clave

- `prueba_login.py`: Aplicación Streamlit.
- `config.yaml`: Configuración + usuarios registrados (bcrypt).
- `requirements.txt`: Dependencias.
- `docker-compose.yml`: Levanta la app con volumen persistente.

---

## 📌 Recomendaciones

- No subir `config.yaml` con contraseñas reales a repositorios públicos.
- Usar variables de entorno o `.env` para manejar claves sensibles.
- Documentar siempre quién gestiona las credenciales en el equipo.

---

**Desarrollado por el equipo de Seguridad**  
`TP_FINAL-TCP_IP_2025-Grupo_1 - Sección Seguridad`
