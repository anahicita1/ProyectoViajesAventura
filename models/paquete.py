from __future__ import annotations

from dataclasses import dataclass, field

from models.destino import Destino


@dataclass
class PaqueteTuristico:
    """Paquete turístico publicado con congelamiento de precio."""

    id_paquete: int | None = None
    nombre: str = ""
    destino: Destino | None = None
    destino_id: int | None = None
    destinos_secundarios: list[int] = field(default_factory=list)
    precio_base: int = 0
    cupos_total: int = 0
    precio_congelado: int = 0
    activo: bool = True
    descripcion: str = ""

    def __post_init__(self) -> None:
        if self.destino is not None and self.destino_id is None:
            self.destino_id = self.destino.id_destino
