from __future__ import annotations

import sqlite3
from datetime import date

from config.database import get_connection
from repositories.paquete_repository import PaqueteRepository
from repositories.reserva_repository import ReservaRepository


class ReservaService:
    """Servicio para reservar paquetes con validación estricta y transacción atómica."""

    @staticmethod
    def validar_fecha_salida(fecha_salida: str) -> date:
        try:
            salida = date.fromisoformat(fecha_salida)
        except ValueError as exc:
            raise ValueError('La fecha de salida no tiene un formato válido.') from exc

        if salida <= date.today():
            raise ValueError('La fecha de salida debe ser posterior a la fecha actual.')
        return salida

    @staticmethod
    def obtener_cupo_disponible(conn: sqlite3.Connection, paquete_id: int) -> int:
        fila = conn.execute(
            """
            SELECT p.cupos_total,
                   COALESCE(SUM(r.pasajeros), 0) AS ocupados
            FROM paquetes p
            LEFT JOIN reservas r
                ON r.paquete_id = p.id
               AND r.estado = 'CONFIRMADA'
            WHERE p.id = ?
            GROUP BY p.id, p.cupos_total
            """,
            (paquete_id,),
        ).fetchone()

        if fila is None:
            raise ValueError('El paquete no existe.')

        cupos_total = int(fila['cupos_total'])
        ocupados = int(fila['ocupados'])
        return cupos_total - ocupados

    @staticmethod
    def crear_reserva(cliente_id: int, paquete_id: int, pasajeros: int, fecha_salida: str) -> dict:
        if not isinstance(cliente_id, int) or cliente_id <= 0:
            raise ValueError('Cliente inválido.')
        if not isinstance(paquete_id, int) or paquete_id <= 0:
            raise ValueError('Paquete inválido.')
        if not isinstance(pasajeros, int) or pasajeros <= 0:
            raise ValueError('La cantidad de pasajeros debe ser mayor a 0.')
        if not fecha_salida:
            raise ValueError('La fecha de salida es obligatoria.')

        salida = ReservaService.validar_fecha_salida(fecha_salida)

        paquete = PaqueteRepository.obtener_por_id(paquete_id)
        if paquete is None:
            raise ValueError('El paquete no existe.')
        if int(paquete['activo']) == 0:
            raise ValueError('El paquete está inactivo.')
        fecha_salida_programada = paquete.get('fecha_salida')
        if fecha_salida_programada:
            try:
                salida_programada = date.fromisoformat(fecha_salida_programada)
            except ValueError as exc:
                raise ValueError('La fecha de salida del paquete no es válida.') from exc
            if salida_programada <= date.today():
                raise ValueError('No se puede reservar un paquete con fecha de salida vencida.')
            if salida != salida_programada:
                raise ValueError('La fecha de salida debe coincidir con la fecha programada del paquete.')

        fecha_regreso = paquete.get('fecha_regreso')
        if fecha_regreso and date.fromisoformat(fecha_regreso) <= salida:
            raise ValueError('La fecha de regreso del paquete debe ser posterior a la salida.')

        conn = get_connection()
        try:
            conn.execute('BEGIN IMMEDIATE')

            cliente_activo = conn.execute(
                'SELECT 1 FROM clientes WHERE id = ? AND activo = 1',
                (cliente_id,),
            ).fetchone()
            if cliente_activo is None:
                conn.rollback()
                raise ValueError('El cliente no existe o está inactivo.')

            paquete_actual = conn.execute(
                """
                                    SELECT p.id, p.cupos_total, p.precio_congelado, p.activo,
                                            p.fecha_salida
                  FROM paquetes AS p
                  WHERE p.id = ? AND p.activo = 1
                """,
                (paquete_id,),
            ).fetchone()
            if paquete_actual is None:
                conn.rollback()
                raise ValueError('El paquete no está disponible para reservas.')
            if paquete_actual['fecha_salida'] and paquete_actual['fecha_salida'] != salida.isoformat():
                conn.rollback()
                raise ValueError('La fecha programada del paquete cambió. Actualiza la página e inténtalo otra vez.')
            if paquete_actual['fecha_salida'] and date.fromisoformat(paquete_actual['fecha_salida']) <= date.today():
                conn.rollback()
                raise ValueError('No se puede reservar un paquete con fecha de salida vencida.')

            cupo_disponible = ReservaService.obtener_cupo_disponible(conn, paquete_id)
            if cupo_disponible < pasajeros:
                conn.rollback()
                raise ValueError('No hay cupo suficiente para la cantidad de pasajeros solicitada.')

            ya_tiene_reserva = conn.execute(
                "SELECT 1 FROM reservas WHERE cliente_id = ? AND paquete_id = ? AND estado = 'CONFIRMADA' LIMIT 1",
                (cliente_id, paquete_id),
            ).fetchone()
            if ya_tiene_reserva is not None:
                conn.rollback()
                raise ValueError('Ya existe una reserva confirmada para este cliente y paquete.')

            precio_total = int(paquete_actual['precio_congelado']) * int(pasajeros)
            fecha_reserva = date.today().isoformat()
            cursor = conn.execute(
                """
                INSERT INTO reservas (cliente_id, paquete_id, pasajeros, precio_total, estado, fecha_reserva, fecha_salida)
                VALUES (?, ?, ?, ?, 'CONFIRMADA', ?, ?)
                """,
                (cliente_id, paquete_id, pasajeros, precio_total, fecha_reserva, salida.isoformat()),
            )

            conn.execute('COMMIT')
            return {
                'id': int(cursor.lastrowid),
                'cliente_id': cliente_id,
                'paquete_id': paquete_id,
                'pasajeros': pasajeros,
                'precio_total': precio_total,
                'estado': 'CONFIRMADA',
                'fecha_reserva': fecha_reserva,
                'fecha_salida': salida.isoformat(),
            }
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            raise ValueError('No se pudo registrar la reserva por una restricción de integridad.') from exc
        except ValueError:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def obtener_historial(cliente_id: int):
        return ReservaRepository.obtener_reservas_cliente(cliente_id)

    @staticmethod
    def cancelar_reserva(
        reserva_id: int,
        cliente_id: int | None = None,
        solo_salidas_futuras: bool = False,
    ) -> bool:
        if reserva_id <= 0:
            raise ValueError('Reserva inválida.')

        conn = get_connection()
        try:
            conn.execute('BEGIN IMMEDIATE')
            reserva = conn.execute(
                'SELECT cliente_id, estado, fecha_salida FROM reservas WHERE id = ?',
                (reserva_id,),
            ).fetchone()
            if reserva is None or (cliente_id is not None and int(reserva['cliente_id']) != cliente_id):
                conn.rollback()
                raise ValueError('La reserva no existe o no pertenece al cliente autenticado.')
            if reserva['estado'] != 'CONFIRMADA':
                conn.rollback()
                return False
            if solo_salidas_futuras:
                try:
                    salida = date.fromisoformat(reserva['fecha_salida'])
                except ValueError as exc:
                    conn.rollback()
                    raise ValueError('La fecha de salida de la reserva no es válida.') from exc
                if salida <= date.today():
                    conn.rollback()
                    raise ValueError('Solo se pueden cancelar reservas con salida futura.')

            cursor = conn.execute(
                """
                UPDATE reservas SET estado = 'CANCELADA'
                WHERE id = ? AND estado = 'CONFIRMADA'
                  AND (? IS NULL OR cliente_id = ?)
                """,
                (reserva_id, cliente_id, cliente_id),
            )
            conn.execute('COMMIT')
            return cursor.rowcount == 1
        except ValueError:
            conn.rollback()
            raise
        finally:
            conn.close()
