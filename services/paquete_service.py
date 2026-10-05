from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from repositories.destino_repository import DestinoRepository
from repositories.paquete_repository import PaqueteRepository
from repositories.reserva_repository import ReservaRepository


class PaqueteService:
    """Servicio para gestionar paquetes turísticos y congelamiento de precios."""

    @staticmethod
    def listar_paquetes(activo: bool | None = True):
        paquetes = PaqueteRepository.listar_paquetes(activo)
        enriched = []
        for paquete in paquetes:
            destinos = PaqueteRepository.listar_destinos(int(paquete['id']))
            paquete['destinos'] = destinos
            paquete['destinos_secundarios'] = [
                int(destino['id'])
                for destino in destinos
                if int(destino['id']) != int(paquete['destino_id'])
            ]
            destino = DestinoRepository.obtener_por_id(paquete['destino_id'])
            paquete['destino'] = destino
            enriched.append(paquete)
        return enriched

    @staticmethod
    def crear_paquete(
        nombre: str,
        destino_ids: list[int],
        cupos_total: int,
        descripcion: str = '',
        margen_porcentaje: float = 25,
        fecha_salida: str | None = None,
        fecha_regreso: str | None = None,
    ):
        if not nombre or not nombre.strip():
            raise ValueError('El nombre del paquete es obligatorio.')
        if not isinstance(destino_ids, list) or not (2 <= len(destino_ids) <= 5):
            raise ValueError('Un paquete debe incluir entre 2 y 5 destinos.')
        if len(set(destino_ids)) != len(destino_ids):
            raise ValueError('No se puede incluir un destino más de una vez.')

        destinos = []
        for destino_id in destino_ids:
            destino = DestinoRepository.obtener_por_id(destino_id)
            if destino is None or int(destino['activo']) == 0:
                raise ValueError(f'El destino {destino_id} no existe o no está activo.')
            destinos.append(destino)

        try:
            margen = Decimal(str(margen_porcentaje))
        except InvalidOperation as exc:
            raise ValueError('El margen debe ser un número válido.') from exc
        if not margen.is_finite() or margen < 0:
            raise ValueError('El margen no puede ser negativo.')

        if cupos_total <= 0:
            raise ValueError('El cupo total debe ser mayor a 0.')
        if not fecha_salida or not fecha_regreso:
            raise ValueError('Las fechas de salida y regreso son obligatorias.')
        try:
            salida = date.fromisoformat(fecha_salida)
            regreso = date.fromisoformat(fecha_regreso)
        except ValueError as exc:
            raise ValueError('Las fechas del paquete no tienen formato válido.') from exc
        if salida <= date.today():
            raise ValueError('La fecha de salida debe ser posterior a la fecha actual.')
        if regreso <= salida:
            raise ValueError('La fecha de regreso debe ser posterior a la fecha de salida.')

        duracion_ruta = sum(int(destino['duracion_dias']) for destino in destinos)
        if (regreso - salida).days != duracion_ruta:
            raise ValueError('La duración del paquete debe coincidir con la suma de los días de sus destinos.')

        precio_base = sum(int(destino['costo_base']) for destino in destinos)

        precio_congelado = int(
            (Decimal(precio_base) * (Decimal('1') + margen / Decimal('100'))).quantize(
                Decimal('1'), rounding=ROUND_HALF_UP
            )
        )
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
            margen_porcentaje=float(margen),
            fecha_salida=salida.isoformat(),
            fecha_regreso=regreso.isoformat(),
        )
        return PaqueteRepository.obtener_por_id(paquete_id)

    @staticmethod
    def actualizar_paquete(
        paquete_id: int,
        nombre: str,
        destino_ids: list[int],
        cupos_total: int,
        descripcion: str,
        margen_porcentaje: float,
        fecha_salida: str,
        fecha_regreso: str,
    ):
        if not nombre.strip():
            raise ValueError('El nombre del paquete es obligatorio.')
        if not isinstance(destino_ids, list) or not 2 <= len(destino_ids) <= 5:
            raise ValueError('Un paquete debe incluir entre 2 y 5 destinos.')
        if len(set(destino_ids)) != len(destino_ids):
            raise ValueError('No se puede incluir un destino más de una vez.')
        destinos = [DestinoRepository.obtener_por_id(destino_id) for destino_id in destino_ids]
        if any(destino is None or int(destino['activo']) == 0 for destino in destinos):
            raise ValueError('Todos los destinos seleccionados deben estar disponibles.')
        if cupos_total <= 0:
            raise ValueError('El cupo máximo debe ser mayor a 0.')
        ocupados = ReservaRepository.obtener_total_confirmado(paquete_id)
        if cupos_total < ocupados:
            raise ValueError('El cupo máximo no puede ser menor a los pasajeros ya confirmados.')

        try:
            margen = Decimal(str(margen_porcentaje))
            salida = date.fromisoformat(fecha_salida)
            regreso = date.fromisoformat(fecha_regreso)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError('El margen o las fechas del paquete no son válidos.') from exc
        if not margen.is_finite() or margen < 0:
            raise ValueError('El margen no puede ser negativo.')
        if salida <= date.today() or regreso <= salida:
            raise ValueError('El intervalo del paquete debe tener fechas futuras y regreso posterior a salida.')

        precio_base = sum(int(destino['costo_base']) for destino in destinos)
        duracion_ruta = sum(int(destino['duracion_dias']) for destino in destinos)
        if (regreso - salida).days != duracion_ruta:
            raise ValueError('La duración debe coincidir con los días sumados de los destinos.')
        precio_congelado = int(
            (Decimal(precio_base) * (Decimal('1') + margen / Decimal('100'))).quantize(
                Decimal('1'), rounding=ROUND_HALF_UP
            )
        )
        PaqueteRepository.actualizar_paquete(
            paquete_id=paquete_id,
            nombre=nombre.strip(),
            descripcion=descripcion.strip(),
            cupos_total=int(cupos_total),
            precio_base=precio_base,
            precio_congelado=precio_congelado,
            margen_porcentaje=float(margen),
            fecha_salida=salida.isoformat(),
            fecha_regreso=regreso.isoformat(),
            destinos=destino_ids,
        )
        return PaqueteRepository.obtener_por_id(paquete_id)
