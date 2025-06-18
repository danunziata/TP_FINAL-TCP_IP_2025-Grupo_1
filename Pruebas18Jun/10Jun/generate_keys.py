import streamlit_authenticator as stauth # Importa la librería para usar el Hasher
import yaml
from pathlib import Path

# Define la estructura de las credenciales según la nueva versión de streamlit-authenticator
# Las contraseñas se guardan en texto plano aquí temporalmente; la librería las hasheará.
config = {
    'cookie': {
        'name': 'your_cookie_name', # Cambia esto por un nombre único para tu cookie
        'key': 'your_cookie_key', # Cambia esto por una clave secreta aleatoria
        'expiry_days': 30
    },
    'credentials': {
        'usernames': {
            'admin': {
                'email': 'admin@example.com', # Agrega un email
                'first_name': 'Admin', # Agrega nombre
                'last_name': 'User', # Agrega apellido
                'password': 'abc123', # Contraseña en texto plano
                'failed_login_attempts': 0, # Campo requerido
                'logged_in': False # Campo requerido
            },
            'invitado': {
                'email': 'invitado@example.com', # Agrega un email
                'first_name': 'Guest', # Agrega nombre
                'last_name': 'User', # Agrega apellido
                'password': 'def456', # Contraseña en texto plano
                'failed_login_attempts': 0, # Campo requerido
                'logged_in': False # Campo requerido
            }
        }
    }
}

# Hashea las contraseñas en el diccionario de configuración
# La función hash_passwords toma el diccionario de credenciales y hashea los valores 'password'
config['credentials'] = stauth.Hasher.hash_passwords(config['credentials'])

# Define la ruta del archivo de configuración
file_path = Path(__file__).parent / "config.yaml"

# Escribe la configuración en el archivo YAML
with file_path.open("w") as file:
    yaml.dump(config, file, default_flow_style=False)

print(f"Archivo de configuración guardado en: {file_path}")
