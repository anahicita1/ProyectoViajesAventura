from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

from config.database import get_connection, initialize_database
from repositories.destino_repository import DestinoRepository
from repositories.paquete_repository import PaqueteRepository
from repositories.usuario_repository import UsuarioRepository
from services.autenticacion_service import AutenticacionService
from services.reserva_service import ReservaService


def _reset_db():
    initialize_database()
    with get_connection() as conn:
        conn.execute('DELETE FROM reservas')
        conn.execute('DELETE FROM paquetes')
        conn.execute('DELETE FROM destinos')
        conn.execute('DELETE FROM usuarios')

    destino_id = DestinoRepository.crear_destino(
        nombre='Destino Concurrencia',
        region='Región de Prueba',
        descripcion='Destino para pruebas de concurrencia.',
        costo_base=100000,
        latitud=-33.0,
        longitud=-70.0,
    )
    paquete_id = PaqueteRepository.crear_paquete(
        nombre='Paquete de Prueba',
        destino_id=destino_id,
        precio_base=100000,
        precio_congelado=100000,
        cupos_total=3,
        descripcion='Cupo limitado.',
    )
    for index in range(10):
        AutenticacionService.registrar_usuario(
            nombre=f'Usuario{index}',
            apellido='Prueba',
            rut=f'11.111.11{index}-1',
            email=f'usuario{index}@test.com',
            password='Secret123.',
            rol='CLIENTE',
        )
    return paquete_id


def test_concurrency_does_not_overbook():
    paquete_id = _reset_db()
    usuarios = UsuarioRepository.listar_usuarios()
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
        executor.map(reservar, [usuario['id'] for usuario in usuarios])

    assert len(resultados) <= 3
    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) AS total FROM reservas WHERE paquete_id = ? AND estado = 'CONFIRMADA'",
            (paquete_id,),
        ).fetchone()['total']
    assert total <= 3
