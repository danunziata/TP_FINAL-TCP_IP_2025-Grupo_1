import streamlit as st
import login as login

# Streamlit asume esto como una pagina
if 'usuario' not in st.session_state:
    st.header('Pagina :orange[principal]')
    login.generarLogin()  # Muestra el formulario de login
else:
    st.header('Pagina :orange[principal]')
    st.subheader('Información pagina principal')
    
    # Botón para cerrar sesión
    if st.button("Cerrar sesión"):
        login.logout()