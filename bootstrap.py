from __future__ import annotations

from config.database import get_connection, initialize_database
from repositories.destino_repository import DestinoRepository
from repositories.usuario_repository import UsuarioRepository
from services.autenticacion_service import AutenticacionService


def bootstrap_database() -> None:
    initialize_database()

    with get_connection() as conn:
        admin_exists = conn.execute(
            "SELECT 1 FROM usuarios WHERE email = 'admin@viajesaventura.cl' LIMIT 1"
        ).fetchone()
        if not admin_exists:
            AutenticacionService.registrar_usuario(
                nombre='Admin',
                apellido='Sistema',
                rut='11.111.111-1',
                email='admin@viajesaventura.cl',
                password='Admin123.',
                rol='ADMINISTRADOR',
            )

        destinos = conn.execute('SELECT COUNT(*) AS total FROM destinos').fetchone()['total']
        if destinos == 0:
            DestinoRepository.crear_destino(
                nombre='Valparaíso',
                region='Región de Valparaíso',
                descripcion='Puerto con historia, cerros y mar.',
                costo_base=180000,
                latitud=-33.0472,
                longitud=-71.6127,
            )
            DestinoRepository.crear_destino(
                nombre='Puerto Varas',
                region='Región de Los Lagos',
                descripcion='Paisajes de lagos y volcanes.',
                costo_base=220000,
                latitud=-41.3181,
                longitud=-72.9855,
            )
            DestinoRepository.crear_destino(
                nombre='San Pedro de Atacama',
                region='Región de Antofagasta',
                descripcion='Desierto y observación astronómica.',
                costo_base=260000,
                latitud=-22.9187,
                longitud=-68.2009,
            )


if __name__ == '__main__':
    bootstrap_database()
    print('Bootstrap completado.')
