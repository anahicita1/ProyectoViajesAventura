from __future__ import annotations

import sqlite3
from datetime import date

from config.database import get_connection
from repositories.paquete_repository import PaqueteRepository
from repositories.reserva_repository import ReservaRepository


class ReservaService:
    """Servicio para reservar paquetes con validación estricta de fechas y cupos."""

    @staticmethod
    def crear_reserva(cliente_id: int, paquete_id: int, pasajeros: int, fecha_salida: str) -> dict:
        if pasajeros <= 0:
            raise ValueError('La cantidad de pasajeros debe ser mayor a 0.')
        if not fecha_salida:
            raise ValueError('La fecha de salida es obligatoria.')

        paquete = PaqueteRepository.obtener_por_id(paquete_id)
        if paquete is None:
            raise ValueError('El paquete no existe.')
        if int(paquete['activo']) == 0:
            raise ValueError('El paquete está inactivo.')

        fecha_actual = date.today().isoformat()
        if fecha_salida <= fecha_actual:
            raise ValueError('La fecha de salida debe ser posterior a la fecha actual.')

        conn = get_connection()
        try:
            conn.execute('BEGIN IMMEDIATE')
            total_confirmado = conn.execute(
                "SELECT COALESCE(SUM(pasajeros), 0) AS total FROM reservas WHERE paquete_id = ? AND estado = 'CONFIRMADA'",
                (paquete_id,),
            ).fetchone()['total']
            cupos_total = int(paquete['cupos_total'])
            if total_confirmado + pasajeros > cupos_total:
                raise ValueError('No hay cupos disponibles para esa cantidad de pasajeros.')
            if ReservaRepository.existe_reserva_confirmada(cliente_id, paquete_id):
                raise ValueError('Ya tienes una reserva confirmada para este paquete.')

            precio_total = int(paquete['precio_congelado']) * int(pasajeros)
            reserva_id = conn.execute(
                """
                INSERT INTO reservas (cliente_id, paquete_id, pasajeros, precio_total, estado, fecha_reserva, fecha_salida)
                VALUES (?, ?, ?, ?, 'CONFIRMADA', ?, ?)
                """,
                (cliente_id, paquete_id, pasajeros, precio_total, date.today().isoformat(), fecha_salida),
            ).lastrowid
            conn.commit()
            return {'id': int(reserva_id), 'precio_total': precio_total, 'estado': 'CONFIRMADA'}
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            raise ValueError('No se puede duplicar la reserva para el mismo paquete y cliente.') from exc
        finally:
            conn.close()

    @staticmethod
    def obtener_historial(cliente_id: int):
        return ReservaRepository.obtener_reservas_cliente(cliente_id)
