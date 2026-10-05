from __future__ import annotations

from typing import Any

from config.database import get_connection


class PaqueteRepository:
    """Repositorio para catálogo de paquetes turísticos."""

    @staticmethod
    def listar_paquetes(activo: bool | None = True) -> list[dict[str, Any]]:
        with get_connection() as conn:
            if activo is None:
                rows = conn.execute("SELECT * FROM paquetes ORDER BY id").fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT p.*
                    FROM paquetes AS p
                    WHERE p.activo = ?
                    ORDER BY p.id
                    """,
                    (1 if activo else 0,),
                ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def obtener_por_id(paquete_id: int) -> dict[str, Any] | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM paquetes WHERE id = ? LIMIT 1",
                (paquete_id,),
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def crear_paquete(
        nombre: str,
        destino_id: int,
        precio_base: int,
        precio_congelado: int,
        cupos_total: int,
        descripcion: str,
        destinos_secundarios: list[int] | None = None,
        margen_porcentaje: float = 0,
        fecha_salida: str | None = None,
        fecha_regreso: str | None = None,
    ) -> int:
        destinos_ids = list(dict.fromkeys([destino_id, *(destinos_secundarios or [])]))
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO paquetes (
                    nombre, destino_id, precio_base, precio_congelado,
                    margen_porcentaje, cupos_total, fecha_salida, fecha_regreso, descripcion, activo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    nombre, destino_id, precio_base, precio_congelado,
                    margen_porcentaje, cupos_total, fecha_salida, fecha_regreso, descripcion,
                ),
            )
            paquete_id = int(cursor.lastrowid)
            conn.executemany(
                'INSERT INTO paquete_destino (paquete_id, destino_id, orden) VALUES (?, ?, ?)',
                [(paquete_id, destino, orden) for orden, destino in enumerate(destinos_ids, start=1)],
            )
            return paquete_id

    @staticmethod
    def actualizar_paquete(
        paquete_id: int,
        nombre: str,
        descripcion: str,
        cupos_total: int,
        precio_base: int,
        precio_congelado: int,
        margen_porcentaje: float,
        fecha_salida: str,
        fecha_regreso: str,
        destinos: list[int],
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE paquetes
                SET nombre = ?, destino_id = ?, descripcion = ?, cupos_total = ?, precio_base = ?,
                    precio_congelado = ?, margen_porcentaje = ?, fecha_salida = ?, fecha_regreso = ?
                WHERE id = ?
                """,
                (
                    nombre, destinos[0], descripcion, cupos_total, precio_base,
                    precio_congelado, margen_porcentaje, fecha_salida, fecha_regreso, paquete_id,
                ),
            )
            conn.execute('DELETE FROM paquete_destino WHERE paquete_id = ?', (paquete_id,))
            conn.executemany(
                'INSERT INTO paquete_destino (paquete_id, destino_id, orden) VALUES (?, ?, ?)',
                [(paquete_id, destino, orden) for orden, destino in enumerate(destinos, start=1)],
            )

    @staticmethod
    def listar_destinos(paquete_id: int) -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT d.*
                FROM paquete_destino AS pd
                JOIN destinos AS d ON d.id = pd.destino_id
                WHERE pd.paquete_id = ?
                ORDER BY pd.orden, d.id
                """,
                (paquete_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def cambiar_estado(paquete_id: int, activo: bool) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE paquetes SET activo = ? WHERE id = ?",
                (1 if activo else 0, paquete_id),
            )
