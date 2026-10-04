from __future__ import annotations

from typing import Any

from config.database import get_connection


class ReservaRepository:
    """Repositorio para la gestión transaccional de reservas."""

    @staticmethod
    def crear_reserva(cliente_id: int, paquete_id: int, pasajeros: int, precio_total: int, fecha_reserva: str, fecha_salida: str, estado: str = 'CONFIRMADA') -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO reservas (cliente_id, paquete_id, pasajeros, precio_total, estado, fecha_reserva, fecha_salida)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (cliente_id, paquete_id, pasajeros, precio_total, estado, fecha_reserva, fecha_salida),
            )
            return int(cursor.lastrowid)

    @staticmethod
    def obtener_reservas_cliente(cliente_id: int) -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM reservas WHERE cliente_id = ? ORDER BY id DESC",
                (cliente_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def obtener_reservas_paquete(paquete_id: int) -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM reservas WHERE paquete_id = ? ORDER BY id DESC",
                (paquete_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def obtener_total_confirmado(paquete_id: int) -> int:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(pasajeros), 0) AS total FROM reservas WHERE paquete_id = ? AND estado = 'CONFIRMADA'",
                (paquete_id,),
            ).fetchone()
            return int(row['total']) if row and row['total'] is not None else 0

    @staticmethod
    def existe_reserva_confirmada(cliente_id: int, paquete_id: int) -> bool:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM reservas WHERE cliente_id = ? AND paquete_id = ? AND estado = 'CONFIRMADA' LIMIT 1",
                (cliente_id, paquete_id),
            ).fetchone()
            return row is not None
