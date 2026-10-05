from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from repositories.destino_repository import DestinoRepository
from repositories.paquete_repository import PaqueteRepository
from repositories.reserva_repository import ReservaRepository
from services.currency_service import CurrencyService
from services.reserva_service import ReservaService
from services.weather_service import WeatherService


def render_cliente_view(seccion: str = 'Catálogo') -> None:
    if st.session_state.get('usuario') is None and seccion == 'Mis Reservas':
        st.info('Inicia sesión para consultar tus reservas.')
        st.session_state.auth_requested = True
        st.rerun()

    if st.session_state.get('reserva_borrador') is not None:
        _render_confirmacion_reserva()
        return

    if seccion == 'Mis Reservas':
        _render_mis_reservas()
        return

    st.subheader('Explora paquetes de aventura')

    paquetes = PaqueteRepository.listar_paquetes(activo=True)
    if not paquetes:
        st.info('No hay paquetes disponibles en este momento.')
        return

    paquete_seleccionado = st.selectbox(
        'Selecciona un paquete',
        options=[(paquete['id'], paquete['nombre']) for paquete in paquetes],
        format_func=lambda option: option[1] if isinstance(option, tuple) else option,
    )

    if paquete_seleccionado is None:
        return

    paquete_id, nombre = paquete_seleccionado
    paquete = PaqueteRepository.obtener_por_id(paquete_id)
    if paquete is None or int(paquete['activo']) == 0:
        st.info('Este paquete ya no está disponible.')
        return
    destino = DestinoRepository.obtener_por_id(paquete['destino_id'])
    if destino is None:
        st.info('La información del destino no está disponible.')
        return

    cupos_disponibles = max(
        0,
        int(paquete['cupos_total']) - ReservaRepository.obtener_total_confirmado(int(paquete_id)),
    )

    with st.container(border=True):
        st.subheader(nombre)
        st.write(f"{destino['nombre']} · {destino['region']}")
        destinos_paquete = PaqueteRepository.listar_destinos(int(paquete_id))
        if destinos_paquete:
            ruta = ' → '.join(
                f"{item['nombre']} ({item['duracion_dias']} días)"
                for item in destinos_paquete
            )
            st.write(f'Ruta: {ruta}')
        fecha_programada = paquete.get('fecha_salida')
        if fecha_programada:
            st.write(f'Fecha de salida programada: {fecha_programada}')
        fecha_regreso = paquete.get('fecha_regreso')
        if fecha_regreso:
            st.write(f'Fecha de regreso: {fecha_regreso}')
        if paquete.get('descripcion'):
            st.write(paquete['descripcion'])
        precio = int(paquete['precio_congelado'])
        costo_base = sum(int(item['costo_base']) for item in destinos_paquete)
        if not destinos_paquete:
            costo_base = int(paquete['precio_base'])
        margen_porcentaje = float(paquete.get('margen_porcentaje') or 0)
        margen_clp = precio - costo_base
        st.caption('Desglose por persona')
        precio_base_col, margen_col, precio_final_col = st.columns(3)
        precio_base_col.metric('Costo base destinos', f'CLP {costo_base:,}')
        margen_col.metric(
            f'Margen de operación ({margen_porcentaje:g}%)',
            f'CLP {margen_clp:,}',
        )
        precio_final_col.metric('Precio final oficial', f'CLP {precio:,}')
        st.caption(f'{cupos_disponibles} cupos disponibles')

        clima_texto = 'Clima actual no disponible'
        try:
            clima = WeatherService.obtener_clima_por_destino(float(destino['latitud']), float(destino['longitud']))
            if clima.get('temperatura_c') is not None:
                clima_texto = f"Clima actual: {clima['temperatura_c']} {clima['unidad']}"
        except Exception:
            pass

        usd_value = CurrencyService.convertir_clp_a_usd(precio)
        clima_col, divisa_col = st.columns(2)
        clima_col.caption(clima_texto)
        divisa_col.caption(f'Equivalente referencial: USD {usd_value:,.2f}')

        if fecha_programada and date.fromisoformat(fecha_programada) <= date.today():
            st.info('La fecha de salida de este paquete ya venció.')
        elif cupos_disponibles > 0:
            fecha_minima = date.today() + timedelta(days=1)
            fecha_predeterminada = (
                date.fromisoformat(fecha_programada)
                if fecha_programada
                else fecha_minima
            )
            if fecha_predeterminada < fecha_minima:
                fecha_predeterminada = fecha_minima
            with st.form(f'reserva_form_{paquete_id}'):
                pasajeros = st.number_input(
                    'Pasajeros', min_value=1, max_value=cupos_disponibles, value=1, step=1,
                    key=f'pasajeros_{paquete_id}',
                )
                fecha_salida = st.date_input(
                    'Fecha de salida', value=fecha_predeterminada, min_value=fecha_minima,
                    disabled=bool(fecha_programada),
                    key=f'fecha_salida_{paquete_id}',
                )
                if st.form_submit_button('Reservar Paquete'):
                    st.session_state.reserva_borrador = {
                        'paquete_id': int(paquete_id),
                        'pasajeros': int(pasajeros),
                        'fecha_salida': fecha_salida.isoformat(),
                    }
                    st.rerun()
        else:
            st.info('Este paquete está completo por el momento.')


def _render_confirmacion_reserva() -> None:
    borrador = st.session_state.reserva_borrador
    paquete = PaqueteRepository.obtener_por_id(int(borrador['paquete_id']))
    if paquete is None or int(paquete['activo']) == 0:
        st.warning('El paquete dejó de estar disponible. Elige otro para continuar.')
        st.session_state.reserva_borrador = None
        return

    total = int(paquete['precio_congelado']) * int(borrador['pasajeros'])
    st.subheader('Confirma tu reserva')
    st.write(f"**{paquete['nombre']}**")
    fecha_regreso = (
        f" · Regreso: {paquete['fecha_regreso']}"
        if paquete.get('fecha_regreso')
        else ''
    )
    st.write(
        f"Salida: {borrador['fecha_salida']}{fecha_regreso} · "
        f"Pasajeros: {borrador['pasajeros']}"
    )
    st.write(f'Total: CLP {total:,}')

    confirmar_col, cancelar_col = st.columns(2)
    if confirmar_col.button('Confirmar reserva', type='primary'):
        try:
            data = ReservaService.crear_reserva(
                cliente_id=int(st.session_state.usuario['id']),
                paquete_id=int(borrador['paquete_id']),
                pasajeros=int(borrador['pasajeros']),
                fecha_salida=borrador['fecha_salida'],
            )
            st.session_state.reserva_borrador = None
            st.success(f'Reserva confirmada. Total: CLP {data["precio_total"]:,}')
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
    if cancelar_col.button('Cancelar'):
        st.session_state.reserva_borrador = None
        st.rerun()


def _render_mis_reservas() -> None:
    usuario = st.session_state.get('usuario')
    if usuario is None:
        st.info('Inicia sesión para consultar tus reservas.')
        st.session_state.auth_requested = True
        st.rerun()
        return

    if st.session_state.pop('mensaje_reserva_cancelada', False):
        st.success('Reserva cancelada con éxito y cupos liberados')

    st.subheader('Mis Reservas')
    reservas = ReservaService.obtener_historial(int(usuario['id']))
    if not reservas:
        st.info('Todavía no tienes reservas.')
        return

    for reserva in reservas:
        paquete = PaqueteRepository.obtener_por_id(int(reserva['paquete_id']))
        nombre_paquete = paquete['nombre'] if paquete else f"Paquete #{reserva['paquete_id']}"
        salida = reserva['fecha_salida']
        regreso = paquete.get('fecha_regreso') if paquete else None
        fechas = f'Salida: {salida}'
        if regreso:
            fechas += f' · Regreso: {regreso}'
        with st.container(border=True):
            st.write(f'**{nombre_paquete}** · {reserva["estado"]}')
            st.caption(
                f"{fechas} · {reserva['pasajeros']} pasajeros · "
                f"Total: CLP {reserva['precio_total']:,}"
            )
            try:
                salida_futura = date.fromisoformat(salida) > date.today()
            except (TypeError, ValueError):
                salida_futura = False
            if reserva['estado'] == 'CONFIRMADA' and salida_futura:
                confirmar_cancelacion = st.checkbox(
                    'Confirmo que deseo cancelar esta reserva',
                    key=f'confirmar_cancelacion_{reserva["id"]}',
                )
                if st.button(
                    'Cancelar Reserva',
                    key=f'cancelar_reserva_cliente_{reserva["id"]}',
                    disabled=not confirmar_cancelacion,
                ):
                    try:
                        cancelada = ReservaService.cancelar_reserva(
                            int(reserva['id']),
                            cliente_id=int(usuario['id']),
                            solo_salidas_futuras=True,
                        )
                        if cancelada:
                            st.session_state.mensaje_reserva_cancelada = True
                            st.rerun()
                        st.info('La reserva ya no está confirmada.')
                    except ValueError as exc:
                        st.error(str(exc))
