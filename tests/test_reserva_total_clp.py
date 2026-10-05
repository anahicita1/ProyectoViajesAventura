from config import database
from bootstrap import bootstrap_database
from services.autenticacion_service import AutenticacionService
from services.reserva_service import ReservaService


def test_reserva_persiste_total_oficial_en_clp(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', tmp_path / 'reserva-clp.db')
    bootstrap_database()

    cliente = AutenticacionService.registrar_usuario(
        nombre='Cliente',
        apellido='Prueba',
        rut='12.345.678-5',
        email='cliente@clp.test',
        password='ClaveCliente123!',
        telefono='+56912345678',
    )
    with database.get_connection() as conn:
        paquete = conn.execute(
            "SELECT id, precio_congelado, fecha_salida FROM paquetes WHERE nombre = 'Norte Grande en 5 días'"
        ).fetchone()

    reserva = ReservaService.crear_reserva(
        cliente_id=int(usuario_id),
        paquete_id=int(paquete['id']),
        pasajeros=2,
        fecha_salida=paquete['fecha_salida'],
    )
    total_oficial_clp = int(paquete['precio_congelado']) * 2

    with database.get_connection() as conn:
        reserva_guardada = conn.execute(
            'SELECT precio_total FROM reservas WHERE id = ?', (reserva['id'],)
        ).fetchone()

    assert reserva['precio_total'] == total_oficial_clp
    assert reserva_guardada['precio_total'] == total_oficial_clp
        assert ReservaService.cancelar_reserva(
            int(reserva['id']),
            cliente_id=int(cliente['id']),
            solo_salidas_futuras=True,
        ) is True
        with database.get_connection() as conn:
            assert ReservaService.obtener_cupo_disponible(conn, int(paquete['id'])) == int(paquete['cupos_total'])