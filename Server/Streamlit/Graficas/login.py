<<<<<<< HEAD
import streamlit as st
import hashlib

# Credenciales válidas (usuario: contraseña_hasheada)
CREDENCIALES_VALIDAS = {
    "admin": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",  # sha256 de 'admin'
    "usuario": "04f8996da763b7a969b1028ee3007569eaf3a635486ddab211d512c85b9df8fb"  # sha256 de 'usuario123'
}

def validar_credenciales(usuario, contrasena):
    """Valida las credenciales del usuario contra nuestro diccionario seguro"""
    if usuario in CREDENCIALES_VALIDAS:
        # Hash SHA-256 de la contraseña ingresada
        contrasena_hash = hashlib.sha256(contrasena.encode()).hexdigest()
        # Comparación segura de hashes
        return CREDENCIALES_VALIDAS[usuario] == contrasena_hash
    return False

def generarLogin():
    """Muestra el formulario de login y maneja la autenticación"""
    
    # Solo mostrar formulario si no hay sesión activa
    if 'usuario' not in st.session_state:
        with st.container():
            st.title("🔑 Sistema de Autenticación")
            
            with st.form("login_form"):
                usuario = st.text_input("Usuario", placeholder="Ingresa tu usuario")
                contrasena = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
                enviar = st.form_submit_button("Iniciar sesión")
                
                if enviar:
                    if usuario and contrasena:
                        if validar_credenciales(usuario, contrasena):
                            # Guardar usuario en sesión
                            st.session_state['usuario'] = usuario
                            st.success(f"¡Bienvenido {usuario}!")
                            st.rerun()  # Forzar actualización de la página
                        else:
                            st.error("Credenciales incorrectas")
                    else:
                        st.warning("Debes completar ambos campos")

def logout():
    """Cierra la sesión del usuario"""
    if 'usuario' in st.session_state:
        del st.session_state['usuario']
=======
import streamlit as st
import hashlib

# Credenciales válidas (usuario: contraseña_hasheada)
CREDENCIALES_VALIDAS = {
    "admin": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",  # sha256 de 'admin'
    "usuario": "04f8996da763b7a969b1028ee3007569eaf3a635486ddab211d512c85b9df8fb"  # sha256 de 'usuario123'
}

def validar_credenciales(usuario, contrasena):
    """Valida las credenciales del usuario contra nuestro diccionario seguro"""
    if usuario in CREDENCIALES_VALIDAS:
        # Hash SHA-256 de la contraseña ingresada
        contrasena_hash = hashlib.sha256(contrasena.encode()).hexdigest()
        # Comparación segura de hashes
        return CREDENCIALES_VALIDAS[usuario] == contrasena_hash
    return False

def generarLogin():
    """Muestra el formulario de login y maneja la autenticación"""
    
    # Solo mostrar formulario si no hay sesión activa
    if 'usuario' not in st.session_state:
        with st.container():
            st.title("🔑 Sistema de Autenticación")
            
            with st.form("login_form"):
                usuario = st.text_input("Usuario", placeholder="Ingresa tu usuario")
                contrasena = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
                enviar = st.form_submit_button("Iniciar sesión")
                
                if enviar:
                    if usuario and contrasena:
                        if validar_credenciales(usuario, contrasena):
                            # Guardar usuario en sesión
                            st.session_state['usuario'] = usuario
                            st.success(f"¡Bienvenido {usuario}!")
                            st.rerun()  # Forzar actualización de la página
                        else:
                            st.error("Credenciales incorrectas")
                    else:
                        st.warning("Debes completar ambos campos")

def logout():
    """Cierra la sesión del usuario"""
    if 'usuario' in st.session_state:
        del st.session_state['usuario']
>>>>>>> bb7f761b1fe8c713249ab87d0753ed0f4860f6a1
    st.rerun()