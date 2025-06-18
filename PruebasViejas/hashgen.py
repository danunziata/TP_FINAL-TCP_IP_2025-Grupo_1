import bcrypt

def generar_hash():
    password = input("Ingresa la contraseña: ").encode('utf-8')
    hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
    print("\nHash bcrypt generado:\n")
    print(f'"{hashed}"')

if __name__ == "__main__":
    generar_hash()