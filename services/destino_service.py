from __future__ import annotations

from repositories.destino_repository import DestinoRepository


class DestinoService:
    """Servicio para administrar destinos del catálogo."""

    @staticmethod
    def listar_destinos(activo: bool | None = True):
        return DestinoRepository.listar_destinos(activo)

    @staticmethod
    def crear_destino(
        nombre: str,
        region: str,
        descripcion: str,
        costo_base: int,
        latitud: float = 0.0,
        longitud: float = 0.0,
        duracion_dias: int = 1,
    ):
        if not nombre or not nombre.strip() or not region or not region.strip():
            raise ValueError('Nombre y región son obligatorios.')
        if costo_base <= 0:
            raise ValueError('El costo base debe ser mayor a 0.')
        if duracion_dias <= 0:
            raise ValueError('La duración debe ser de al menos un día.')
        if not -90 <= float(latitud) <= 90 or not -180 <= float(longitud) <= 180:
            raise ValueError('Las coordenadas deben estar dentro de los rangos geográficos válidos.')
        return DestinoRepository.crear_destino(
            nombre.strip(), region.strip(), descripcion.strip(), int(costo_base),
            float(latitud), float(longitud), int(duracion_dias),
        )

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
    ):
        if not nombre or not nombre.strip() or not region or not region.strip():
            raise ValueError('Nombre y región son obligatorios.')
        if costo_base <= 0 or duracion_dias <= 0:
            raise ValueError('El costo y la duración deben ser mayores a 0.')
        if not -90 <= float(latitud) <= 90 or not -180 <= float(longitud) <= 180:
            raise ValueError('Las coordenadas deben estar dentro de los rangos geográficos válidos.')
        DestinoRepository.actualizar_destino(
            destino_id, nombre.strip(), region.strip(), descripcion.strip(),
            int(costo_base), float(latitud), float(longitud), int(duracion_dias),
        )
        return DestinoRepository.obtener_por_id(destino_id)

    @staticmethod
    def eliminar_destino(destino_id: int):
        if DestinoRepository.tiene_paquetes(destino_id):
            DestinoRepository.eliminar_logico(destino_id)
            return 'no_disponible'
        DestinoRepository.eliminar_fisicamente(destino_id)
        return 'eliminado'

    @staticmethod
    def cambiar_disponibilidad(destino_id: int, activo: bool):
        DestinoRepository.cambiar_estado(destino_id, activo)
        return DestinoRepository.obtener_por_id(destino_id)
