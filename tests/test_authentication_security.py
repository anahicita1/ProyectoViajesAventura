import pytest

from config import database
from services.autenticacion_service import AutenticacionService
from utils.security import verificar_password
from utils.validators import enmascarar_rut, enmascarar_telefono


def test_cliente_usa_hash_y_la_sesion_no_expone_datos_sensibles(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', tmp_path / 'auth.db')
    database.initialize_database()

    sesion = AutenticacionService.registrar_usuario(
        nombre='Ana',
        apellido='Prueba',
        rut='12.345.678-5',
        email='ANA@example.com',
        password='ContraseñaSegura123!',
        telefono='+56912345678',
    )

    assert set(sesion) == {'id', 'nombre', 'apellido', 'rol', 'area'}
    assert sesion['rol'] == 'CLIENTE'
    assert sesion['area'] is None
    with database.get_connection() as conn:
        cliente = conn.execute(
            'SELECT password_hash, salt FROM clientes WHERE id = ?', (sesion['id'],)
        ).fetchone()
    assert cliente['password_hash'] != 'ContraseñaSegura123!'
    assert verificar_password('ContraseñaSegura123!', cliente['salt'], cliente['password_hash'])

    sesion_login = AutenticacionService.autenticar('ana@example.com', 'ContraseñaSegura123!')
    assert sesion_login == sesion
    with pytest.raises(ValueError, match='correo ya existe'):
        AutenticacionService.registrar_usuario(
            nombre='Otra', apellido='Cliente', rut='11.111.111-1',
            email='ana@example.com', password='OtraClave123!', telefono='+56987654321',
        )


def test_rut_y_telefono_se_enmascaran_en_listados():
    assert enmascarar_rut('12.345.678-5') == '12.345.***-*'
    assert enmascarar_telefono('+56912345678') == '+56 9 XXXX 5678'