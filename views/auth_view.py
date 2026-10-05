from __future__ import annotations

import streamlit as st

from services.autenticacion_service import AutenticacionService


def _volver_al_catalogo() -> None:
    st.session_state['portal'] = '🌴 Portal Clientes'
    st.session_state['cliente_seccion'] = 'Catálogo'
    st.session_state['auth_requested'] = False
    st.session_state['reserva_borrador'] = None


def render_auth_view(allow_registration: bool = True) -> None:
    reserva_pendiente = st.session_state.get('reserva_borrador') is not None
    acceso_socios = not allow_registration
    st.subheader('Acceso Socios' if acceso_socios else 'Inicia sesión o crea tu cuenta')
    if acceso_socios:
        st.caption('Ingreso exclusivo para las cuentas de socios autorizadas.')
    elif reserva_pendiente:
        st.info('Inicia sesión para continuar. Después podrás revisar y confirmar los datos de tu reserva.')
    elif st.session_state.get('cliente_seccion') == 'Mis Reservas':
        st.info('Inicia sesión para consultar tus reservas.')
    else:
        st.caption('Accede a tu cuenta para gestionar tus viajes.')

    st.button('Volver al catálogo', on_click=_volver_al_catalogo)

    nombres_pestanas = ['Iniciar sesión']
    if allow_registration:
        nombres_pestanas.append('Registrarse')
    pestanas = st.tabs(nombres_pestanas)

    with pestanas[0]:
        with st.form('login_form'):
            email = st.text_input('Correo electrónico', key='login_email')
            password = st.text_input('Contraseña', type='password', key='login_password')
            if st.form_submit_button('Ingresar'):
                try:
                    usuario = AutenticacionService.autenticar(email, password)
                    if acceso_socios and usuario['rol'] != 'ADMINISTRADOR':
                        st.error('Esta cuenta no tiene permisos de socio.')
                        st.stop()
                    st.session_state.usuario = usuario
                    st.session_state.rol = usuario['rol']
                    st.session_state.auth_requested = False
                    st.success(f'Bienvenido/a, {usuario["nombre"]} {usuario["apellido"]}.')
                    st.rerun()
                except (ValueError, PermissionError) as exc:
                    st.error(str(exc))

    if allow_registration:
        with pestanas[1]:
            with st.form('registro_form'):
                nombre = st.text_input('Nombre')
                apellido = st.text_input('Apellido')
                rut = st.text_input('RUT')
                email = st.text_input('Correo electrónico')
                telefono = st.text_input('Teléfono')
                password = st.text_input('Contraseña', type='password')
                if st.form_submit_button('Crear cuenta'):
                    try:
                        usuario = AutenticacionService.registrar_usuario(
                            nombre, apellido, rut, email, password,
                            rol='CLIENTE', telefono=telefono,
                        )
                        st.success('Usuario registrado correctamente.')
                        st.session_state.usuario = usuario
                        st.session_state.rol = 'CLIENTE'
                        st.session_state.auth_requested = False
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
