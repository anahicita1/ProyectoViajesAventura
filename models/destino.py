from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Destino:
    """Entidad que representa un destino turístico."""

    id_destino: int
    nombre: str
    region: str
    activo: bool = True
    costo_base: int = 0
    descripcion: str = ""
