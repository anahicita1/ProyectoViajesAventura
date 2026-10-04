from __future__ import annotations

import json

from repositories.destino_repository import DestinoRepository
from repositories.paquete_repository import PaqueteRepository


class PaqueteService:
    """Servicio para gestionar paquetes turísticos y congelamiento de precios."""

    @staticmethod
    def listar_paquetes(activo: bool | None = True):
        paquetes = PaqueteRepository.listar_paquetes(activo)
        enriched = []
        for paquete in paquetes:
            paquete['destinos_secundarios'] = json.loads(paquete.get('destinos_secundarios') or '[]')
            destino = DestinoRepository.obtener_por_id(paquete['destino_id'])
            paquete['destino'] = destino
            enriched.append(paquete)
        return enriched

    @staticmethod
    def crear_paquete(nombre: str, destino_ids: list[int], precio_base: int, cupos_total: int, descripcion: str = ''):
        if not nombre:
            raise ValueError('El nombre del paquete es obligatorio.')
        if not isinstance(destino_ids, list) or not (2 <= len(destino_ids) <= 5):
            raise ValueError('Un paquete debe incluir entre 2 y 5 destinos.')

        destinos = []
        for destino_id in destino_ids:
            destino = DestinoRepository.obtener_por_id(destino_id)
            if destino is None or int(destino['activo']) == 0:
                raise ValueError(f'El destino {destino_id} no existe o no está activo.')
            destinos.append(destino)

        precio_congelado = int(precio_base)
        if cupos_total <= 0:
            raise ValueError('El cupo total debe ser mayor a 0.')

        principal_destino = destino_ids[0]
        secundarios = destino_ids[1:]
        paquete_id = PaqueteRepository.crear_paquete(
            nombre=nombre.strip(),
            destino_id=principal_destino,
            precio_base=precio_base,
            precio_congelado=precio_congelado,
            cupos_total=cupos_total,
            descripcion=descripcion.strip(),
            destinos_secundarios=secundarios,
        )
        return PaqueteRepository.obtener_por_id(paquete_id)
