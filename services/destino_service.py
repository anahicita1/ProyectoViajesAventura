from __future__ import annotations

from repositories.destino_repository import DestinoRepository


class DestinoService:
    """Servicio para administrar destinos del catálogo."""

    @staticmethod
    def listar_destinos(activo: bool | None = True):
        return DestinoRepository.listar_destinos(activo)

    @staticmethod
    def crear_destino(nombre: str, region: str, descripcion: str, costo_base: int, latitud: float = 0.0, longitud: float = 0.0):
        if not nombre or not region:
            raise ValueError('Nombre y región son obligatorios.')
        if costo_base <= 0:
            raise ValueError('El costo base debe ser mayor a 0.')
        return DestinoRepository.crear_destino(nombre.strip(), region.strip(), descripcion.strip(), int(costo_base), float(latitud), float(longitud))

    @staticmethod
    def actualizar_destino(destino_id: int, nombre: str, region: str, descripcion: str, costo_base: int, latitud: float, longitud: float):
        DestinoRepository.actualizar_destino(destino_id, nombre.strip(), region.strip(), descripcion.strip(), int(costo_base), float(latitud), float(longitud))
        return DestinoRepository.obtener_por_id(destino_id)

    @staticmethod
    def eliminar_destino(destino_id: int):
        DestinoRepository.eliminar_logico(destino_id)
        return DestinoRepository.obtener_por_id(destino_id)
