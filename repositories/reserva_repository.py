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
                """
                SELECT r.*, p.nombre AS paquete_nombre, p.fecha_regreso
                FROM reservas AS r
                JOIN paquetes AS p ON p.id = r.paquete_id
                WHERE r.cliente_id = ?
                ORDER BY r.id DESC
                """,
                (cliente_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def listar_todas(
        busqueda_cliente: str = '',
        paquete_id: int | None = None,
    ) -> list[dict[str, Any]]:
        busqueda = f'%{busqueda_cliente.strip()}%'
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT r.id, r.cliente_id, r.paquete_id, r.pasajeros, r.precio_total,
                       r.estado, r.fecha_reserva, r.fecha_salida,
                       c.nombre AS cliente_nombre, c.apellido AS cliente_apellido,
                       c.email AS cliente_email, c.rut AS cliente_rut,
                       c.telefono AS cliente_telefono, p.nombre AS paquete_nombre,
                       p.fecha_regreso
                FROM reservas AS r
                JOIN clientes AS c ON c.id = r.cliente_id
                JOIN paquetes AS p ON p.id = r.paquete_id
                WHERE (? = '%%' OR c.nombre LIKE ? OR c.apellido LIKE ? OR c.email LIKE ?)
                  AND (? IS NULL OR r.paquete_id = ?)
                ORDER BY r.id DESC
                """,
                (busqueda, busqueda, busqueda, busqueda, paquete_id, paquete_id),
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def obtener_metricas() -> dict[str, int]:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS total_reservas,
                       COALESCE(SUM(CASE WHEN estado = 'CONFIRMADA' THEN precio_total ELSE 0 END), 0) AS total_recaudado,
                       COALESCE(SUM(CASE WHEN estado = 'CONFIRMADA' THEN pasajeros ELSE 0 END), 0) AS pasajeros_confirmados
                FROM reservas
                """
            ).fetchone()
            return {key: int(row[key]) for key in row.keys()}

    @staticmethod
    def cancelar_reserva(reserva_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute(
                "UPDATE reservas SET estado = 'CANCELADA' WHERE id = ? AND estado = 'CONFIRMADA'",
                (reserva_id,),
            )
            return cursor.rowcount == 1

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
