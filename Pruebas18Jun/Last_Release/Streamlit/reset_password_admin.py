# reset_password_admin.py
import bcrypt
import yaml
from pathlib import Path
import os # Importar os para path.exists

# Asegúrate de que esta ruta sea correcta para tu config.yaml
CONFIG_PATH = Path(__file__).parent / "config.yaml"

def hash_password(password):
    # Genera un salt y hashea la contraseña
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_password.decode('utf-8')

def main():
    print("--- Herramienta de Restablecimiento de Contraseña para Administradores ---")

    if not os.path.exists(CONFIG_PATH):
        print(f"Error: El archivo de configuración no se encontró en {CONFIG_PATH}")
        print("Asegúrate de ejecutar este script desde el directorio correcto.")
        return

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    usernames = config['credentials']['usernames']
    print("\nUsuarios existentes:")
    for username in usernames.keys():
        print(f"- {username}")

    selected_username = input("\nIntroduce el nombre de usuario cuya contraseña quieres restablecer: ")

    if selected_username not in usernames:
        print(f"Error: El usuario '{selected_username}' no existe.")
        return

    new_password = input(f"Introduce la NUEVA contraseña para '{selected_username}': ")
    confirm_password = input("Confirma la nueva contraseña: ")

    if new_password != confirm_password:
        print("Error: Las contraseñas no coinciden.")
        return

    hashed_new_password = hash_password(new_password)

    # Actualiza la contraseña en la configuración
    usernames[selected_username]['password'] = hashed_new_password

    # Opcional: Actualizar el password_hint si existe y si quieres
    # if 'password_hint' in usernames[selected_username]:
    #     usernames[selected_username]['password_hint'] = "Contraseña restablecida"

    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        yaml.dump(config, file, default_flow_style=False)

    print(f"\n✅ Contraseña para el usuario '{selected_username}' restablecida exitosamente.")
    print("El archivo config.yaml ha sido actualizado.")
    print("Indica al usuario que intente iniciar sesión con la nueva contraseña.")

if __name__ == "__main__":
    main()
