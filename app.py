from __future__ import annotations

import streamlit as st

from bootstrap import bootstrap_database
from views.admin_view import render_admin_view
from views.auth_view import render_auth_view
from views.cliente_view import render_cliente_view


bootstrap_database()

st.set_page_config(page_title='Viajes Aventura', page_icon='✈️', layout='wide')

if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'rol' not in st.session_state:
    st.session_state.rol = None

if st.session_state.usuario is None:
    render_auth_view()
    st.stop()

usuario = st.session_state.usuario
rol = str(usuario.get('rol') or st.session_state.rol or 'CLIENTE').upper()

with st.sidebar:
    st.write(f'Usuario: {usuario["nombre"]} {usuario["apellido"]}')
    st.write(f'Rol: {rol}')
    if st.button('Cerrar sesión'):
        st.session_state.usuario = None
        st.session_state.rol = None
        st.rerun()

if rol == 'ADMINISTRADOR':
    render_admin_view()
else:
    render_cliente_view()
