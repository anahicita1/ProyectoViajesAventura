from __future__ import annotations

from typing import Any

from config.database import get_connection


class ClienteRepository:
    """Persistencia separada para cuentas de clientes."""

    @staticmethod
    def crear_cliente(
        nombre: str,
        apellido: str,
        rut: str,
        email: str,
        telefono: str,
        password_hash: str,
        salt: str,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO clientes (
                    nombre, apellido, rut, email, telefono,
                    password_hash, salt, activo, intentos_fallidos
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0)
                """,
                (nombre, apellido, rut, email, telefono, password_hash, salt),
            )
            return int(cursor.lastrowid)

    @staticmethod
    def obtener_por_email(email: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            row = conn.execute(
                'SELECT * FROM clientes WHERE email = ? COLLATE NOCASE LIMIT 1',
                (email,),
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def obtener_por_id(cliente_id: int) -> dict[str, Any] | None:
        with get_connection() as conn:
            row = conn.execute(
                'SELECT * FROM clientes WHERE id = ? LIMIT 1', (cliente_id,)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def actualizar_fallos(email: str, intentos_fallidos: int, bloqueado_hasta: str | None) -> None:
        with get_connection() as conn:
            conn.execute(
                'UPDATE clientes SET intentos_fallidos = ?, bloqueado_hasta = ? WHERE email = ? COLLATE NOCASE',
                (intentos_fallidos, bloqueado_hasta, email),
            )

    @staticmethod
    def reset_fallos(email: str) -> None:
        ClienteRepository.actualizar_fallos(email, 0, None)

    @staticmethod
    def listar_clientes() -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, nombre, apellido, rut, email, telefono, activo
                FROM clientes
                WHERE activo = 1
                ORDER BY apellido COLLATE NOCASE, nombre COLLATE NOCASE
                """
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def cambiar_estado(cliente_id: int, activo: bool) -> None:
        with get_connection() as conn:
            conn.execute(
                'UPDATE clientes SET activo = ? WHERE id = ?',
                (1 if activo else 0, cliente_id),
            )