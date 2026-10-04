from __future__ import annotations

import json
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
                    "SELECT * FROM paquetes WHERE activo = ? ORDER BY id",
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
    def crear_paquete(nombre: str, destino_id: int, precio_base: int, precio_congelado: int, cupos_total: int, descripcion: str, destinos_secundarios: list[int] | None = None) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO paquetes (nombre, destino_id, destinos_secundarios, precio_base, precio_congelado, cupos_total, descripcion, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (nombre, destino_id, json.dumps(destinos_secundarios or []), precio_base, precio_congelado, cupos_total, descripcion),
            )
            return int(cursor.lastrowid)

    @staticmethod
    def actualizar_paquete(paquete_id: int, nombre: str, descripcion: str, cupos_total: int, precio_congelado: int, destinos_secundarios: list[int] | None = None) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE paquetes
                SET nombre = ?, descripcion = ?, cupos_total = ?, precio_congelado = ?, destinos_secundarios = ?
                WHERE id = ?
                """,
                (nombre, descripcion, cupos_total, precio_congelado, json.dumps(destinos_secundarios or []), paquete_id),
            )

    @staticmethod
    def cambiar_estado(paquete_id: int, activo: bool) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE paquetes SET activo = ? WHERE id = ?",
                (1 if activo else 0, paquete_id),
            )
