from __future__ import annotations

import streamlit as st

from bootstrap import bootstrap_database
from views.admin_view import render_admin_view
from views.auth_view import render_auth_view
from views.cliente_view import render_cliente_view


st.set_page_config(page_title='Viajes Aventura', page_icon='✈️', layout='wide')

bootstrap_database()

if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'rol' not in st.session_state:
    st.session_state.rol = None
if 'cliente_seccion' not in st.session_state:
    st.session_state.cliente_seccion = 'Catálogo'
if 'auth_requested' not in st.session_state:
    st.session_state.auth_requested = False
if 'reserva_borrador' not in st.session_state:
    st.session_state.reserva_borrador = None
if 'portal' not in st.session_state:
    st.session_state.portal = '🌴 Portal Clientes'

st.title('Viajes Aventura')
st.caption('Tu agencia de reservas para paquetes turísticos de aventura')

usuario = st.session_state.usuario
if isinstance(usuario, dict):
    usuario = {
        'id': usuario.get('id'),
        'nombre': usuario.get('nombre', ''),
        'apellido': usuario.get('apellido', ''),
        'rol': usuario.get('rol') or st.session_state.rol,
        'area': usuario.get('area'),
    }
    st.session_state.usuario = usuario
rol = str((usuario or {}).get('rol') or st.session_state.rol or 'CLIENTE').upper()

if usuario is not None and rol not in {'CLIENTE', 'ADMINISTRADOR'}:
    st.session_state.usuario = None
    st.session_state.rol = None
    st.error('El rol de la sesión no es válido. Inicia sesión nuevamente.')
    st.stop()

with st.sidebar:
    portal = st.radio(
        'Portal de acceso',
        ['🌴 Portal Clientes', '🔑 Acceso Socios'],
        key='portal',
    )
    if usuario is not None:
        st.write(f'Usuario: {usuario["nombre"]} {usuario["apellido"]}')
        if rol == 'ADMINISTRADOR':
            area = str(usuario.get('area') or 'ADMINISTRACION')
            etiqueta_area = {
                'CATALOGO': 'Catálogo y Paquetes',
                'RESERVAS': 'Atención y Reservas',
                'DATOS': 'Administración y Datos',
                'ADMINISTRACION': 'Administración general',
            }.get(area, 'Administración')
            st.write(f'Socio: {etiqueta_area}')
        else:
            st.write('Rol: Cliente')
        if st.button('Cerrar sesión'):
            st.session_state.usuario = None
            st.session_state.rol = None
            st.session_state.auth_requested = False
            st.session_state.reserva_borrador = None
            st.rerun()

if usuario is not None and rol == 'ADMINISTRADOR':
    if portal != '🔑 Acceso Socios':
        st.info('Cierra sesión para cambiar al portal de clientes.')
        st.stop()
    render_admin_view(area=str(usuario.get('area') or 'ADMINISTRACION'))
    st.stop()

if usuario is not None and rol == 'CLIENTE' and portal == '🔑 Acceso Socios':
    st.info('La cuenta autenticada pertenece al portal de clientes. Cierra sesión para acceder a socios.')
    st.stop()

if portal == '🔑 Acceso Socios' and usuario is None:
    render_auth_view(allow_registration=False)
    st.stop()

with st.sidebar:
    st.radio('Navegación', ['Catálogo', 'Mis Reservas'], key='cliente_seccion')
    if usuario is None and st.button('Iniciar sesión / Registrarse'):
        st.session_state.auth_requested = True
        st.rerun()

seccion = st.session_state.cliente_seccion
requiere_autenticacion = usuario is None and (
    st.session_state.auth_requested
    or seccion == 'Mis Reservas'
    or st.session_state.reserva_borrador is not None
)

if requiere_autenticacion:
    render_auth_view(allow_registration=True)
    st.stop()

render_cliente_view(seccion=seccion)
