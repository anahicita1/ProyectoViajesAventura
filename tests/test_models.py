from models.usuario import Administrador, Cliente, Usuario
from models.destino import Destino
from models.paquete import PaqueteTuristico
from models.reserva import Reserva


def test_usuario_polimorfismo_permisos():
    cliente = Cliente(
        id_usuario=1,
        nombre='Ana',
        apellido='García',
        rut='12.345.678-9',
        email='ana@example.com',
        password_hash='hash',
    )
    administrador = Administrador(
        id_usuario=2,
        nombre='Luis',
        apellido='Pérez',
        rut='98.765.432-1',
        email='luis@example.com',
        password_hash='hash',
    )

    assert isinstance(cliente, Usuario)
    assert isinstance(administrador, Usuario)
    assert 'RESERVAR' in cliente.obtener_permisos()
    assert 'ADMINISTRAR_CATALOGO' in administrador.obtener_permisos()


def test_destino_y_paquete_basicos():
    destino = Destino(
        id_destino=1,
        nombre='Valparaíso',
        region='Región de Valparaíso',
        activo=True,
        costo_base=150000,
    )
    paquete = PaqueteTuristico(
        id_paquete=1,
        nombre='Ruta del Mar',
        destino=destino,
        precio_base=150000,
        cupos_total=10,
        precio_congelado=150000,
    )

    assert destino.activo is True
    assert paquete.precio_congelado == 150000
    assert paquete.cupos_total == 10


def test_reserva_validacion_basica():
    reserva = Reserva(
        id_reserva=1,
        cliente_id=1,
        paquete_turistico_id=1,
        pasajeros=2,
        precio_total=300000,
        estado='CONFIRMADA',
    )

    assert reserva.cliente_id == 1
    assert reserva.pasajeros == 2
    assert reserva.estado == 'CONFIRMADA'
