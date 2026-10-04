"""Paquete de modelos del sistema de viajes."""

from models.destino import Destino
from models.paquete import PaqueteTuristico
from models.reserva import Reserva
from models.usuario import Administrador, Cliente, Usuario

__all__ = [
    'Usuario',
    'Cliente',
    'Administrador',
    'Destino',
    'PaqueteTuristico',
    'Reserva',
]
