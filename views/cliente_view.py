from __future__ import annotations

import streamlit as st

from repositories.destino_repository import DestinoRepository
from repositories.paquete_repository import PaqueteRepository
from services.currency_service import CurrencyService
from services.reserva_service import ReservaService
from services.weather_service import WeatherService


def render_cliente_view() -> None:
    st.title('Catálogo y reservas')

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
    destino = DestinoRepository.obtener_por_id(paquete['destino_id'])

    st.subheader(f'Paquete: {nombre}')
    st.write(f"Destino principal: {destino['nombre']} ({destino['region']})")
    st.write(f"Precio congelado: CLP {paquete['precio_congelado']:,}")
    st.write(f"Cupos disponibles: {int(paquete['cupos_total'])}")

    if destino:
        try:
            clima = WeatherService.obtener_clima_por_destino(float(destino['latitud']), float(destino['longitud']))
            st.write(f"Temperatura actual: {clima['temperatura_c']} {clima['unidad']}")
        except Exception as exc:
            st.warning(f'No se pudo consultar el clima: {exc}')

    usd_value = CurrencyService.convertir_clp_a_usd(int(paquete['precio_congelado']))
    st.write(f"Valor estimado en USD: ${usd_value:.2f}")

    with st.form('reserva_form'):
        pasajeros = st.number_input('Cantidad de pasajeros', min_value=1, step=1)
        fecha_salida = st.date_input('Fecha de salida')
        if st.form_submit_button('Reservar paquete'):
            try:
                data = ReservaService.crear_reserva(
                    cliente_id=int(st.session_state.usuario['id']),
                    paquete_id=int(paquete_id),
                    pasajeros=int(pasajeros),
                    fecha_salida=fecha_salida.isoformat(),
                )
                st.success(f'Reserva creada correctamente. Total: CLP {data["precio_total"]:,}')
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
