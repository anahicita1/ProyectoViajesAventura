from __future__ import annotations

import streamlit as st

from services.autenticacion_service import AutenticacionService
from utils.validators import validar_rut_chileno


def render_auth_view() -> None:
    st.title('Viajes Aventura')
    st.caption('Sistema de reservas, administración y clima para destinos turísticos.')

    login_tab, registro_tab = st.tabs(['Iniciar sesión', 'Registrarse'])

    with login_tab:
        with st.form('login_form'):
            email = st.text_input('Correo electrónico', key='login_email')
            password = st.text_input('Contraseña', type='password', key='login_password')
            if st.form_submit_button('Ingresar'):
                try:
                    usuario = AutenticacionService.autenticar(email, password)
                    st.session_state.usuario = usuario
                    st.session_state.rol = usuario['rol']
                    st.success(f'Bienvenido/a, {usuario["nombre"]} {usuario["apellido"]}.')
                    st.rerun()
                except (ValueError, PermissionError) as exc:
                    st.error(str(exc))

    with registro_tab:
        with st.form('registro_form'):
            nombre = st.text_input('Nombre')
            apellido = st.text_input('Apellido')
            rut = st.text_input('RUT')
            email = st.text_input('Correo electrónico')
            password = st.text_input('Contraseña', type='password')
            if st.form_submit_button('Crear cuenta'):
                if not validar_rut_chileno(rut):
                    st.error('El RUT ingresado no es válido.')
                else:
                    try:
                        usuario = AutenticacionService.registrar_usuario(nombre, apellido, rut, email, password, rol='CLIENTE')
                        st.success('Usuario registrado correctamente.')
                        st.session_state.usuario = usuario
                        st.session_state.rol = 'CLIENTE'
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
