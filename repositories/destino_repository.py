from __future__ import annotations

from typing import Any

from config.database import get_connection


class DestinoRepository:
    """Repositorio para gestión del catálogo de destinos."""

    @staticmethod
    def listar_destinos(activo: bool | None = True) -> list[dict[str, Any]]:
        with get_connection() as conn:
            if activo is None:
                rows = conn.execute("SELECT * FROM destinos ORDER BY id").fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM destinos WHERE activo = ? ORDER BY id",
                    (1 if activo else 0,),
                ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def obtener_por_id(destino_id: int) -> dict[str, Any] | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM destinos WHERE id = ? LIMIT 1",
                (destino_id,),
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def crear_destino(nombre: str, region: str, descripcion: str, costo_base: int, latitud: float, longitud: float) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO destinos (nombre, region, descripcion, costo_base, activo, latitud, longitud)
                VALUES (?, ?, ?, ?, 1, ?, ?)
                """,
                (nombre, region, descripcion, costo_base, latitud, longitud),
            )
            return int(cursor.lastrowid)

    @staticmethod
    def actualizar_destino(destino_id: int, nombre: str, region: str, descripcion: str, costo_base: int, latitud: float, longitud: float) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE destinos
                SET nombre = ?, region = ?, descripcion = ?, costo_base = ?, latitud = ?, longitud = ?
                WHERE id = ?
                """,
                (nombre, region, descripcion, costo_base, latitud, longitud, destino_id),
            )

    @staticmethod
    def eliminar_logico(destino_id: int) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE destinos SET activo = 0 WHERE id = ?",
                (destino_id,),
            )
