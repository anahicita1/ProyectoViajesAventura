from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Reserva:
    """Reserva de un paquete turístico hecha por un cliente."""

    id_reserva: int
    cliente_id: int
    paquete_turistico_id: int
    pasajeros: int
    precio_total: int
    estado: str = 'PENDIENTE'
    fecha_reserva: Optional[date] = None
    fecha_salida: Optional[date] = None
