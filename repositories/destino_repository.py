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
    def crear_destino(
        nombre: str,
        region: str,
        descripcion: str,
        costo_base: int,
        latitud: float,
        longitud: float,
        duracion_dias: int = 1,
    ) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO destinos (
                    nombre, region, descripcion, costo_base, duracion_dias, activo, latitud, longitud
                )
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (nombre, region, descripcion, costo_base, duracion_dias, latitud, longitud),
            )
            return int(cursor.lastrowid)

    @staticmethod
    def actualizar_destino(
        destino_id: int,
        nombre: str,
        region: str,
        descripcion: str,
        costo_base: int,
        latitud: float,
        longitud: float,
        duracion_dias: int = 1,
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE destinos
                SET nombre = ?, region = ?, descripcion = ?, costo_base = ?, latitud = ?,
                    longitud = ?, duracion_dias = ?
                WHERE id = ?
                """,
                (nombre, region, descripcion, costo_base, latitud, longitud, duracion_dias, destino_id),
            )

    @staticmethod
    def eliminar_logico(destino_id: int) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE destinos SET activo = 0 WHERE id = ?",
                (destino_id,),
            )

    @staticmethod
    def cambiar_estado(destino_id: int, activo: bool) -> None:
        with get_connection() as conn:
            conn.execute(
                'UPDATE destinos SET activo = ? WHERE id = ?',
                (1 if activo else 0, destino_id),
            )

    @staticmethod
    def tiene_paquetes(destino_id: int) -> bool:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM paquetes AS p
                WHERE p.destino_id = ?
                   OR EXISTS (
                       SELECT 1 FROM paquete_destino AS pd
                       WHERE pd.paquete_id = p.id AND pd.destino_id = ?
                   )
                LIMIT 1
                """,
                (destino_id, destino_id),
            ).fetchone()
            return row is not None

    @staticmethod
    def eliminar_fisicamente(destino_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute('DELETE FROM destinos WHERE id = ?', (destino_id,))
            return cursor.rowcount == 1
