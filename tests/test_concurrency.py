from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

from config.database import get_connection, initialize_database
from repositories.destino_repository import DestinoRepository
from repositories.paquete_repository import PaqueteRepository
from services.autenticacion_service import AutenticacionService
from services.reserva_service import ReservaService


def _rut_valido(numero: int) -> str:
    suma = 0
    factor = 2
    for digito in reversed(str(numero)):
        suma += int(digito) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - suma % 11
    digito_verificador = '0' if resto == 11 else 'K' if resto == 10 else str(resto)
    return f'{numero}-{digito_verificador}'


def _crear_datos_prueba():
    initialize_database()
    destino_id = DestinoRepository.crear_destino(
        nombre='Destino Concurrencia',
        region='Región de Prueba',
        descripcion='Destino para pruebas de concurrencia.',
        costo_base=100000,
        latitud=-33.0,
        longitud=-70.0,
    )
    segundo_destino_id = DestinoRepository.crear_destino(
        nombre='Segundo Destino Concurrencia',
        region='Región de Prueba',
        descripcion='Destino secundario de prueba.',
        costo_base=50000,
        latitud=-34.0,
        longitud=-71.0,
    )

    paquete_id = PaqueteRepository.crear_paquete(
        nombre='Paquete de Prueba',
        destino_id=destino_id,
        precio_base=100000,
        precio_congelado=100000,
        cupos_total=3,
        descripcion='Cupo limitado.',
        destinos_secundarios=[segundo_destino_id],
    )
    clientes = []
    for index in range(10):
        cliente = AutenticacionService.registrar_usuario(
            nombre=f'Usuario{index}',
            apellido='Prueba',
            rut=_rut_valido(12000000 + index),
            email=f'usuario{index}@test.com',
            password='Secret123.',
            rol='CLIENTE',
            telefono=f'+569123456{index}',
        )
        clientes.append(cliente)
    return paquete_id, clientes


def test_concurrency_does_not_overbook(tmp_path, monkeypatch):
    from config import database

    monkeypatch.setattr(database, 'DB_PATH', tmp_path / 'concurrency.db')
    paquete_id, clientes = _crear_datos_prueba()
    resultados = []
    lock = threading.Lock()

    def reservar(usuario_id: int):
        try:
            ReservaService.crear_reserva(
                cliente_id=usuario_id,
                paquete_id=paquete_id,
                pasajeros=1,
                fecha_salida='2099-12-31',
            )
            with lock:
                resultados.append(usuario_id)
        except ValueError:
            pass

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(reservar, [cliente['id'] for cliente in clientes])

    assert len(resultados) <= 3
    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) AS total FROM reservas WHERE paquete_id = ? AND estado = 'CONFIRMADA'",
            (paquete_id,),
        ).fetchone()['total']
    assert total <= 3
