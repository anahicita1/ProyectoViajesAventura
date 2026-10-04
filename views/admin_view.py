from __future__ import annotations

import streamlit as st

from repositories.destino_repository import DestinoRepository
from repositories.paquete_repository import PaqueteRepository
from services.destino_service import DestinoService
from services.paquete_service import PaqueteService


def render_admin_view() -> None:
    st.title('Administración del catálogo')

    destinos = DestinoRepository.listar_destinos(activo=None)
    paquetes = PaqueteRepository.listar_paquetes(activo=None)

    st.subheader('Crear destino')
    with st.form('destino_form'):
        nombre = st.text_input('Nombre del destino')
        region = st.text_input('Región')
        descripcion = st.text_area('Descripción')
        costo_base = st.number_input('Costo base (CLP)', min_value=1, step=1)
        latitud = st.number_input('Latitud', format='%.4f', value=-33.4372)
        longitud = st.number_input('Longitud', format='%.4f', value=-70.6506)
        if st.form_submit_button('Guardar destino'):
            try:
                DestinoService.crear_destino(nombre, region, descripcion, costo_base, latitud, longitud)
                st.success('Destino creado correctamente.')
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.subheader('Destinos registrados')
    if destinos:
        for destino in destinos:
            estado = 'Activo' if int(destino['activo']) == 1 else 'Inactivo'
            with st.container():
                st.write(f"- {destino['nombre']} ({destino['region']}) - {estado} - CLP {destino['costo_base']:,}")
    else:
        st.info('Aún no existen destinos.')

    st.subheader('Crear paquete turístico')
    with st.form('paquete_form'):
        nombre = st.text_input('Nombre del paquete')
        descripcion = st.text_area('Descripción del paquete')
        destino_ids = st.multiselect(
            'Destinos incluidos (2 a 5)',
            options=[(destino['id'], destino['nombre']) for destino in destinos if int(destino['activo']) == 1],
            format_func=lambda x: x[1] if isinstance(x, tuple) else x,
        )
        precio_base = st.number_input('Precio base (CLP)', min_value=1, step=1)
        cupos_total = st.number_input('Cupos total', min_value=1, step=1)
        if st.form_submit_button('Publicar paquete'):
            try:
                PaqueteService.crear_paquete(nombre, [destino_id for destino_id, _ in destino_ids], int(precio_base), int(cupos_total), descripcion)
                st.success('Paquete publicado correctamente.')
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.subheader('Paquetes registrados')
    if paquetes:
        for paquete in paquetes:
            destino = DestinoRepository.obtener_por_id(paquete['destino_id'])
            destino_nombre = destino['nombre'] if destino else 'Sin destino'
            st.write(f"- {paquete['nombre']} | Destino principal: {destino_nombre} | Cupos: {paquete['cupos_total']} | Precio: CLP {paquete['precio_congelado']:,}")
    else:
        st.info('Aún no hay paquetes publicados.')
