from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

import streamlit as st

from repositories.destino_repository import DestinoRepository
from repositories.cliente_repository import ClienteRepository
from repositories.paquete_repository import PaqueteRepository
from repositories.reserva_repository import ReservaRepository
from services.destino_service import DestinoService
from services.paquete_service import PaqueteService
from services.reserva_service import ReservaService
from utils.validators import enmascarar_rut, enmascarar_telefono


def render_admin_view(area: str = 'ADMINISTRACION') -> None:
    usuario = st.session_state.get('usuario') or {}
    if str(usuario.get('rol') or '').upper() != 'ADMINISTRADOR':
        st.error('No tienes permisos para acceder a la administración.')
        return

    area = str(usuario.get('area') or area).upper()
    if area not in {'CATALOGO', 'RESERVAS', 'DATOS', 'ADMINISTRACION'}:
        st.error('El perfil de socio no tiene un área válida.')
        return

    if area == 'CATALOGO':
        st.title('Gestión de Catálogo')
        catalogo_tab, = st.tabs(['Destinos y Paquetes'])
        with catalogo_tab:
            _render_destinos()
            _render_paquetes()
        return

    if area == 'RESERVAS':
        st.title('Control de Reservas y Cupos')
        _render_cupos()
        _render_reservas()
        return

    if area == 'DATOS':
        st.title('Visor Global y Protección de Datos')
        _render_reservas()
        _render_clientes()
        return

    st.title('Administración general')
    reservas_tab, paquetes_tab, destinos_tab, clientes_tab = st.tabs(
        ['Visor de Reservas', 'CRUD de Paquetes', 'CRUD de Destinos', 'Gestión de Clientes']
    )

    with reservas_tab:
        _render_reservas()

    with paquetes_tab:
        _render_paquetes()

    with destinos_tab:
        _render_destinos()

    with clientes_tab:
        _render_clientes()


def _render_cupos() -> None:
    paquetes = PaqueteRepository.listar_paquetes(activo=None)
    if not paquetes:
        st.info('No hay paquetes registrados.')
        return

    hoy = date.today()
    for paquete in paquetes:
        total = int(paquete['cupos_total'])
        vendidos = ReservaRepository.obtener_total_confirmado(int(paquete['id']))
        disponibles = max(0, total - vendidos)
        fecha_salida = paquete.get('fecha_salida')
        try:
            expirado = bool(fecha_salida) and date.fromisoformat(fecha_salida) < hoy
        except ValueError:
            expirado = True
        estado = 'Expirado' if expirado else 'Activo' if int(paquete['activo']) else 'No disponible'
        with st.container(border=True):
            st.write(f"**{paquete['nombre']}** · {estado}")
            columnas = st.columns(3)
            columnas[0].metric('Cupo máximo', total)
            columnas[1].metric('Vendidos', vendidos)
            columnas[2].metric('Disponibles', disponibles)
            st.caption(f'Salida programada: {fecha_salida or "Sin fecha"}')


def _render_destinos() -> None:
    destinos = DestinoRepository.listar_destinos(activo=None)
    st.subheader('Agregar destino')
    with st.form('destino_form'):
        nombre = st.text_input('Nombre del destino')
        region = st.text_input('Región')
        descripcion = st.text_area('Descripción')
        costo_base = st.number_input('Costo base (CLP)', min_value=1, step=1000)
        duracion_dias = st.number_input('Duración (días)', min_value=1, step=1)
        latitud = st.number_input('Latitud', format='%.4f', value=-33.4372)
        longitud = st.number_input('Longitud', format='%.4f', value=-70.6506)
        if st.form_submit_button('Guardar destino'):
            try:
                DestinoService.crear_destino(
                    nombre, region, descripcion, int(costo_base), latitud, longitud,
                    int(duracion_dias),
                )
                st.success('Destino creado correctamente.')
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.subheader('Destinos registrados')
    if not destinos:
        st.info('Aún no existen destinos.')
        return

    for destino in destinos:
        destino_id = int(destino['id'])
        activo = int(destino['activo']) == 1
        with st.expander(f"{destino['nombre']} · {'Disponible' if activo else 'No disponible'}"):
            with st.form(f'destino_editar_{destino_id}'):
                nombre = st.text_input('Nombre', value=destino['nombre'], key=f'destino_nombre_{destino_id}')
                region = st.text_input('Región', value=destino['region'], key=f'destino_region_{destino_id}')
                descripcion = st.text_area(
                    'Descripción', value=destino.get('descripcion') or '',
                    key=f'destino_descripcion_{destino_id}',
                )
                costo_base = st.number_input(
                    'Costo base (CLP)', min_value=1, value=int(destino['costo_base']), step=1000,
                    key=f'destino_costo_{destino_id}',
                )
                duracion_dias = st.number_input(
                    'Duración (días)', min_value=1, value=int(destino['duracion_dias']), step=1,
                    key=f'destino_duracion_{destino_id}',
                )
                latitud = st.number_input(
                    'Latitud', value=float(destino['latitud']), format='%.4f',
                    key=f'destino_latitud_{destino_id}',
                )
                longitud = st.number_input(
                    'Longitud', value=float(destino['longitud']), format='%.4f',
                    key=f'destino_longitud_{destino_id}',
                )
                if st.form_submit_button('Guardar cambios'):
                    try:
                        DestinoService.actualizar_destino(
                            destino_id, nombre, region, descripcion, int(costo_base),
                            latitud, longitud, int(duracion_dias),
                        )
                        st.success('Destino actualizado.')
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

            if st.button(
                'Marcar no disponible' if activo else 'Volver a habilitar',
                key=f'destino_estado_{destino_id}',
            ):
                DestinoService.cambiar_disponibilidad(destino_id, not activo)
                st.rerun()
            if st.button('Eliminar (regla R8)', key=f'destino_eliminar_{destino_id}'):
                resultado = DestinoService.eliminar_destino(destino_id)
                if resultado == 'eliminado':
                    st.success('Destino eliminado porque no tiene paquetes asociados.')
                else:
                    st.info('El destino se marcó como no disponible; los paquetes existentes se conservan.')
                st.rerun()


def _render_paquetes() -> None:
    destinos = DestinoRepository.listar_destinos(activo=True)
    st.subheader('Armar paquete')
    if len(destinos) < 2:
        st.info('Se necesitan al menos dos destinos disponibles para armar un paquete.')
        return

    opciones = [(int(destino['id']), destino['nombre']) for destino in destinos]
    seleccionados = st.multiselect(
        'Destinos incluidos (2 a 5)',
        options=opciones,
        format_func=lambda opcion: opcion[1],
        max_selections=5,
        key='paquete_destinos_seleccionados',
    )
    margen = st.number_input('Margen de ganancia (%)', min_value=0.0, value=20.0, step=1.0)
    mapa_destinos = {int(destino['id']): destino for destino in destinos}
    costo_base = sum(int(mapa_destinos[destino_id]['costo_base']) for destino_id, _ in seleccionados)
    duracion_ruta = sum(
        int(mapa_destinos[destino_id]['duracion_dias'])
        for destino_id, _ in seleccionados
    )
    precio_estimado = int(
        (Decimal(costo_base) * (Decimal('1') + Decimal(str(margen)) / Decimal('100'))).quantize(
            Decimal('1'), rounding=ROUND_HALF_UP
        )
    )
    st.write(f'Costo base: CLP {costo_base:,}')
    st.write(f'Duración de la ruta: {duracion_ruta} días')
    st.write(f'Precio congelado estimado: CLP {precio_estimado:,} por persona')

    fecha_minima = date.today() + timedelta(days=1)
    fecha_salida = st.date_input(
        'Fecha de salida', value=fecha_minima, min_value=fecha_minima,
        key='paquete_fecha_salida',
    )
    fecha_regreso_minima = fecha_salida + timedelta(days=max(1, duracion_ruta))
    fecha_regreso = st.date_input(
        'Fecha de regreso', value=fecha_regreso_minima, min_value=fecha_regreso_minima,
        key='paquete_fecha_regreso',
    )

    with st.form('paquete_form'):
        nombre = st.text_input('Nombre del paquete')
        descripcion = st.text_area('Descripción del paquete')
        cupos_total = st.number_input('Cupo máximo', min_value=1, value=10, step=1)
        if st.form_submit_button('Publicar paquete'):
            if not 2 <= len(seleccionados) <= 5:
                st.error('Selecciona entre 2 y 5 destinos activos.')
            else:
                try:
                    PaqueteService.crear_paquete(
                        nombre,
                        [destino_id for destino_id, _ in seleccionados],
                        int(cupos_total),
                        descripcion,
                        float(margen),
                        fecha_salida.isoformat(),
                        fecha_regreso.isoformat(),
                    )
                    st.success('Paquete publicado correctamente.')
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    st.subheader('Paquetes registrados')
    paquetes = PaqueteRepository.listar_paquetes(activo=None)
    if not paquetes:
        st.info('Aún no hay paquetes publicados.')
        return

    for paquete in paquetes:
        paquete_id = int(paquete['id'])
        destinos_paquete = PaqueteRepository.listar_destinos(paquete_id)
        ruta = ' → '.join(destino['nombre'] for destino in destinos_paquete)
        activo = int(paquete['activo']) == 1
        estado = 'Disponible' if activo else 'No disponible'
        cupos_disponibles = max(
            0,
            int(paquete['cupos_total']) - ReservaRepository.obtener_total_confirmado(paquete_id),
        )
        st.write(
            f"**{paquete['nombre']}** · {estado} · {ruta} · "
            f"Salida {paquete.get('fecha_salida') or 'por definir'} · "
            f"Regreso {paquete.get('fecha_regreso') or 'por definir'} · "
            f"{cupos_disponibles}/{paquete['cupos_total']} cupos disponibles · "
            f"Costo base CLP {paquete['precio_base']:,} · Margen {paquete['margen_porcentaje']:g}% · "
            f"Precio congelado CLP {paquete['precio_congelado']:,}"
        )
        if st.button(
            'Marcar no disponible' if activo else 'Volver a habilitar',
            key=f'paquete_estado_{paquete_id}',
        ):
            PaqueteRepository.cambiar_estado(paquete_id, not activo)
            st.rerun()

        with st.expander(f'Editar {paquete["nombre"]}', expanded=False):
            ids_actuales = {int(destino['id']) for destino in destinos_paquete}
            seleccion_actual = [
                opcion for opcion in opciones if opcion[0] in ids_actuales
            ]
            seleccion_edicion = st.multiselect(
                'Destinos del paquete (2 a 5)',
                options=opciones,
                default=seleccion_actual,
                format_func=lambda opcion: opcion[1],
                max_selections=5,
                key=f'editar_destinos_{paquete_id}',
            )
            margen_edicion = st.number_input(
                'Margen (%)', min_value=0.0,
                value=float(paquete['margen_porcentaje']), step=1.0,
                key=f'editar_margen_{paquete_id}',
            )
            costo_edicion = sum(
                int(mapa_destinos[destino_id]['costo_base'])
                for destino_id, _ in seleccion_edicion
            )
            duracion_edicion = sum(
                int(mapa_destinos[destino_id]['duracion_dias'])
                for destino_id, _ in seleccion_edicion
            )
            precio_edicion = int(
                (Decimal(costo_edicion) * (Decimal('1') + Decimal(str(margen_edicion)) / Decimal('100'))).quantize(
                    Decimal('1'), rounding=ROUND_HALF_UP
                )
            )
            st.caption(
                f'Costo base CLP {costo_edicion:,} · Duración {duracion_edicion} días · '
                f'Precio congelado al guardar CLP {precio_edicion:,}'
            )
            fecha_minima_edicion = date.today() + timedelta(days=1)
            fecha_salida_original = paquete.get('fecha_salida')
            try:
                fecha_salida_valor = date.fromisoformat(fecha_salida_original)
            except (TypeError, ValueError):
                fecha_salida_valor = fecha_minima_edicion
            fecha_salida_valor = max(fecha_salida_valor, fecha_minima_edicion)
            fecha_regreso_minima_edicion = fecha_salida_valor + timedelta(
                days=max(1, duracion_edicion)
            )
            try:
                fecha_regreso_valor = date.fromisoformat(paquete.get('fecha_regreso'))
            except (TypeError, ValueError):
                fecha_regreso_valor = fecha_regreso_minima_edicion
            fecha_regreso_valor = max(fecha_regreso_valor, fecha_regreso_minima_edicion)

            with st.form(f'paquete_editar_form_{paquete_id}'):
                nombre_edicion = st.text_input(
                    'Nombre', value=paquete['nombre'], key=f'editar_nombre_{paquete_id}'
                )
                descripcion_edicion = st.text_area(
                    'Descripción', value=paquete.get('descripcion') or '',
                    key=f'editar_descripcion_{paquete_id}',
                )
                cupos_edicion = st.number_input(
                    'Cupo máximo', min_value=1, value=int(paquete['cupos_total']), step=1,
                    key=f'editar_cupos_{paquete_id}',
                )
                salida_edicion = st.date_input(
                    'Salida', value=fecha_salida_valor, min_value=fecha_minima_edicion,
                    key=f'editar_salida_{paquete_id}',
                )
                regreso_edicion = st.date_input(
                    'Regreso', value=fecha_regreso_valor,
                    min_value=salida_edicion + timedelta(days=max(1, duracion_edicion)),
                    key=f'editar_regreso_{paquete_id}',
                )
                if st.form_submit_button('Guardar paquete'):
                    try:
                        PaqueteService.actualizar_paquete(
                            paquete_id,
                            nombre_edicion,
                            [destino_id for destino_id, _ in seleccion_edicion],
                            int(cupos_edicion),
                            descripcion_edicion,
                            float(margen_edicion),
                            salida_edicion.isoformat(),
                            regreso_edicion.isoformat(),
                        )
                        st.success('Paquete actualizado; precio congelado recalculado para futuras reservas.')
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))


def _render_reservas() -> None:
    metricas = ReservaRepository.obtener_metricas()
    paquetes_activos = PaqueteRepository.listar_paquetes(activo=True)
    cupos_totales = sum(int(paquete['cupos_total']) for paquete in paquetes_activos)
    pasajeros_vendidos = sum(
        ReservaRepository.obtener_total_confirmado(int(paquete['id']))
        for paquete in paquetes_activos
    )
    ocupacion = (pasajeros_vendidos / cupos_totales * 100) if cupos_totales else 0
    total_col, recaudado_col, pasajeros_col, ocupacion_col = st.columns(4)
    total_col.metric('Total de reservas', metricas['total_reservas'])
    recaudado_col.metric('Total recaudado confirmado', f"CLP {metricas['total_recaudado']:,}")
    pasajeros_col.metric('Pasajeros atendidos', metricas['pasajeros_confirmados'])
    ocupacion_col.metric('Ocupación', f'{ocupacion:.1f}%')

    paquetes = PaqueteRepository.listar_paquetes(activo=None)
    opciones = [(None, 'Todos los paquetes')] + [
        (int(paquete['id']), paquete['nombre']) for paquete in paquetes
    ]
    filtro_col, busqueda_col = st.columns([1, 2])
    paquete_filtro = filtro_col.selectbox(
        'Filtrar por paquete',
        options=opciones,
        format_func=lambda opcion: opcion[1],
        key='reservas_filtro_paquete',
    )
    busqueda = busqueda_col.text_input(
        'Buscar cliente', placeholder='Nombre, apellido o correo', key='reservas_busqueda_cliente'
    )

    reservas = ReservaRepository.listar_todas(
        busqueda_cliente=busqueda,
        paquete_id=paquete_filtro[0],
    )
    if not reservas:
        st.info('No se encontraron reservas con esos filtros.')
        return

    for reserva in reservas:
        estado = reserva['estado']
        rut = enmascarar_rut(reserva['cliente_rut'])
        telefono = enmascarar_telefono(reserva['cliente_telefono'])
        with st.container(border=True):
            st.write(f"**{reserva['paquete_nombre']}** · Reserva #{reserva['id']} · {estado}")
            st.caption(
                f"Cliente: {reserva['cliente_nombre']} {reserva['cliente_apellido']} · "
                f"RUT {rut} · Tel. {telefono} · {reserva['cliente_email']}"
            )
            st.caption(
                f"Salida {reserva['fecha_salida']} · {reserva['pasajeros']} pasajeros · "
                f"CLP {reserva['precio_total']:,} · creada {reserva['fecha_reserva']}"
            )
            if estado == 'CONFIRMADA' and st.button(
                'Cancelar reserva', key=f'cancelar_reserva_{reserva["id"]}'
            ):
                if ReservaService.cancelar_reserva(int(reserva['id'])):
                    st.success('Reserva cancelada; los cupos volvieron a estar disponibles.')
                    st.rerun()


def _render_clientes() -> None:
    clientes = ClienteRepository.listar_clientes()
    if not clientes:
        st.info('Aún no hay clientes registrados.')
        return

    filas = [
        {
            'Nombre': f"{cliente['nombre']} {cliente['apellido']}",
            'RUT': enmascarar_rut(cliente['rut']),
            'Correo': cliente['email'],
            'Teléfono': enmascarar_telefono(cliente['telefono']),
        }
        for cliente in clientes
    ]
    st.dataframe(filas, hide_index=True, use_container_width=True)

    st.subheader('Historial de compras')
    for cliente in clientes:
        with st.expander(f"{cliente['nombre']} {cliente['apellido']}"):
            reservas = ReservaService.obtener_historial(int(cliente['id']))
            if not reservas:
                st.caption('Sin reservas registradas.')
                continue
            for reserva in reservas:
                st.write(
                    f"{reserva['paquete_nombre']} · {reserva['estado']} · "
                    f"{reserva['pasajeros']} pasajeros · CLP {reserva['precio_total']:,} · "
                    f"salida {reserva['fecha_salida']}"
                )