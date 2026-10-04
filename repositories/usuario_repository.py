from __future__ import annotations

from typing import Any

from config.database import get_connection


class UsuarioRepository:
    """Repositorio para autenticación y gestión de usuarios."""

    @staticmethod
    def create_usuario(nombre: str, apellido: str, rut: str, email: str, password_hash: str, salt: str, rol: str) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO usuarios (nombre, apellido, rut, email, password_hash, salt, rol, activo, intentos_fallidos, bloqueado_hasta)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0, NULL)
                """,
                (nombre, apellido, rut, email, password_hash, salt, rol),
            )
            return int(cursor.lastrowid)

    @staticmethod
    def get_by_email(email: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM usuarios WHERE email = ? LIMIT 1",
                (email,),
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_by_id(usuario_id: int) -> dict[str, Any] | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM usuarios WHERE id = ? LIMIT 1",
                (usuario_id,),
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def update_fallos(email: str, intentos_fallidos: int, bloqueado_hasta: str | None) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE usuarios SET intentos_fallidos = ?, bloqueado_hasta = ? WHERE email = ?",
                (intentos_fallidos, bloqueado_hasta, email),
            )

    @staticmethod
    def reset_fallos(email: str) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE usuarios SET intentos_fallidos = 0, bloqueado_hasta = NULL WHERE email = ?",
                (email,),
            )

    @staticmethod
    def listar_usuarios() -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM usuarios ORDER BY id").fetchall()
            return [dict(row) for row in rows]
