from datetime import date
from config import database
from bootstrap import bootstrap_database
from utils.security import verificar_password


def test_bootstrap_seeds_reservable_packages(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', tmp_path / 'bootstrap.db')

    database.initialize_database()
    with database.get_connection() as conn:
        destino_id = conn.execute(
            """
            INSERT INTO destinos (nombre, region, costo_base, latitud, longitud)
            VALUES ('Valparaíso', 'Región de Valparaíso', 180000, -33.0472, -71.6127)
            """
        ).lastrowid
        conn.execute(
            """
            INSERT INTO paquetes (nombre, destino_id, precio_base, precio_congelado, cupos_total)
            VALUES ('Costa entre cerros y mar', ?, 180000, 180000, 4)
            """,
            (destino_id,),
        )

    bootstrap_database()
    bootstrap_database()

    conn = database.get_connection()
    try:
        paquetes = conn.execute(
            'SELECT * FROM paquetes WHERE activo = 1 ORDER BY id'
        ).fetchall()
        assert len(paquetes) == 3
        destinos = conn.execute(
            'SELECT nombre, region, duracion_dias, costo_base, latitud, longitud, activo FROM destinos WHERE activo = 1 ORDER BY nombre'
        ).fetchall()
        assert len(destinos) == 6
        destinos_por_nombre = {destino['nombre']: destino for destino in destinos}
        destinos_esperados = {
            'Valle del Elqui': ('Región de Coquimbo', 2, 120000, -30.03, -70.52),
            'Salar de Surire': ('Región de Arica y Parinacota', 3, 310000, -18.84, -69.09),
            'Cajón del Maipo': ('Región Metropolitana', 1, 45000, -33.64, -70.13),
            'Parque Conguillío': ('Región de La Araucanía', 3, 185000, -38.64, -71.64),
            'Carretera Austral': ('Región de Aysén', 7, 640000, -45.57, -72.07),
            'Isla Damas': ('Región de Coquimbo', 1, 38000, -29.25, -71.53),
        }
        assert set(destinos_por_nombre) == set(destinos_esperados)
        for nombre, esperado in destinos_esperados.items():
            destino = destinos_por_nombre[nombre]
            assert (
                destino['region'], destino['duracion_dias'], destino['costo_base'],
                destino['latitud'], destino['longitud'],
            ) == esperado

        paquetes_esperados = {
            'Norte Grande en 5 días': (430000, 20, 516000, '2027-07-10', '2027-07-15', 12, ('Salar de Surire', 'Valle del Elqui')),
            'Escapada de fin de semana': (83000, 20, 99600, '2026-11-14', '2026-11-16', 20, ('Cajón del Maipo', 'Isla Damas')),
            'Sur profundo': (825000, 20, 990000, '2027-01-20', '2027-01-30', 8, ('Parque Conguillío', 'Carretera Austral')),
        }
        assert {paquete['nombre'] for paquete in paquetes} == set(paquetes_esperados)

        for paquete in paquetes:
            costo_base, margen, precio, fecha_salida, fecha_regreso, cupos, destinos_esperados = paquetes_esperados[paquete['nombre']]
            assert paquete['precio_base'] == costo_base
            assert paquete['margen_porcentaje'] == margen
            assert paquete['precio_congelado'] == precio
            assert paquete['fecha_salida'] == fecha_salida
            assert paquete['fecha_regreso'] == fecha_regreso
            assert paquete['cupos_total'] == cupos
            assert date.fromisoformat(paquete['fecha_salida']) > date.today()

            destinos = conn.execute(
                """
                SELECT d.nombre, d.activo
                FROM paquete_destino AS pd
                JOIN destinos AS d ON d.id = pd.destino_id
                WHERE pd.paquete_id = ?
                ORDER BY pd.orden
                """,
                (paquete['id'],),
            ).fetchall()
            assert tuple(destino['nombre'] for destino in destinos) == destinos_esperados
            assert all(destino['activo'] == 1 for destino in destinos)

        assert conn.execute(
            "SELECT COUNT(*) FROM destinos WHERE activo = 1 AND nombre NOT IN ("
            "'Valle del Elqui', 'Salar de Surire', 'Cajón del Maipo', "
            "'Parque Conguillío', 'Carretera Austral', 'Isla Damas')"
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT activo FROM paquetes WHERE nombre = 'Costa entre cerros y mar'"
        ).fetchone()['activo'] == 0
        assert conn.execute(
            "SELECT activo FROM destinos WHERE nombre = 'Valparaíso'"
        ).fetchone()['activo'] == 0
    finally:
        conn.close()


def test_bootstrap_crea_socios_con_area_y_password_hasheado(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', tmp_path / 'socios.db')
    monkeypatch.setenv('VIAJES_SOCIOS_PASSWORD', 'ClaveSociosSegura123!')

    bootstrap_database()

    with database.get_connection() as conn:
        socios = conn.execute(
            """
            SELECT nombre, apellido, email, rol, area, password_hash, salt
            FROM usuarios
            WHERE email IN (
                'paulina@viajesaventura.cl',
                'matias@viajesaventura.cl',
                'ignacio@viajesaventura.cl'
            )
            ORDER BY email
            """
        ).fetchall()

    esperados = {
        'paulina@viajesaventura.cl': ('Paulina', 'Ovalle', 'CATALOGO'),
        'matias@viajesaventura.cl': ('Matías', 'Bórquez', 'RESERVAS'),
        'ignacio@viajesaventura.cl': ('Ignacio', 'Salas', 'DATOS'),
    }
    assert len(socios) == 3
    for socio in socios:
        nombre, apellido, area = esperados[socio['email']]
        assert (socio['nombre'], socio['apellido'], socio['area']) == (nombre, apellido, area)
        assert socio['rol'] == 'ADMINISTRADOR'
        assert socio['password_hash'] != 'ClaveSociosSegura123!'
        assert verificar_password(
            'ClaveSociosSegura123!', socio['salt'], socio['password_hash']
        )