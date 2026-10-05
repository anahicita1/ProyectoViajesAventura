import sqlite3

from config import database


def test_migra_usuarios_legacy_a_clientes_y_preserva_reservas(tmp_path, monkeypatch):
    db_path = tmp_path / 'legacy.db'
    monkeypatch.setattr(database, 'DB_PATH', db_path)

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            rut TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            rol TEXT NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1,
            intentos_fallidos INTEGER NOT NULL DEFAULT 0,
            bloqueado_hasta TEXT
        );
        CREATE TABLE destinos (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            region TEXT NOT NULL,
            descripcion TEXT,
            costo_base INTEGER NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1,
            latitud REAL,
            longitud REAL
        );
        CREATE TABLE paquetes (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            destino_id INTEGER NOT NULL,
            descripcion TEXT,
            precio_base INTEGER NOT NULL,
            precio_congelado INTEGER NOT NULL,
            cupos_total INTEGER NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE reservas (
            id INTEGER PRIMARY KEY,
            cliente_id INTEGER NOT NULL REFERENCES usuarios(id),
            paquete_id INTEGER NOT NULL REFERENCES paquetes(id),
            pasajeros INTEGER NOT NULL,
            precio_total INTEGER NOT NULL,
            estado TEXT NOT NULL,
            fecha_reserva TEXT NOT NULL,
            fecha_salida TEXT NOT NULL
        );
        CREATE TRIGGER trg_no_delete_paquete
        BEFORE DELETE ON paquetes
        BEGIN
            SELECT CASE
                WHEN EXISTS (SELECT 1 FROM reservas WHERE paquete_id = OLD.id)
                THEN RAISE(ABORT, 'No se permite borrar paquetes con reservas.')
            END;
        END;
        INSERT INTO usuarios VALUES
            (1, 'Admin', 'Sistema', '11.111.111-1', 'admin@legacy.test', 'admin-hash', 'admin-salt', 'ADMINISTRADOR', 1, 0, NULL),
            (2, 'Ana', 'Cliente', '12.345.678-5', 'ana@legacy.test', 'client-hash', 'client-salt', 'CLIENTE', 1, 0, NULL);
        INSERT INTO destinos VALUES (1, 'Destino', 'Región', '', 1000, 1, -33, -70);
        INSERT INTO paquetes VALUES (1, 'Paquete', 1, '', 1000, 1200, 10, 1);
        INSERT INTO reservas VALUES (1, 2, 1, 2, 2400, 'CONFIRMADA', '2026-10-04', '2026-11-01');
        """
    )
    conn.close()

    database.initialize_database()

    with database.get_connection() as migrated:
        cliente = migrated.execute(
            "SELECT id, password_hash, salt FROM clientes WHERE email = 'ana@legacy.test'"
        ).fetchone()
        admin = migrated.execute(
            "SELECT id, rol FROM usuarios WHERE email = 'admin@legacy.test'"
        ).fetchone()
        reserva = migrated.execute(
            'SELECT cliente_id, precio_total FROM reservas WHERE id = 1'
        ).fetchone()
        destinos_table = migrated.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'paquete_destino'"
        ).fetchone()

    assert (cliente['id'], cliente['password_hash'], cliente['salt']) == (
        2, 'client-hash', 'client-salt'
    )
    assert (admin['id'], admin['rol']) == (1, 'ADMINISTRADOR')
    assert (reserva['cliente_id'], reserva['precio_total']) == (2, 2400)
    assert destinos_table is not None


def test_reset_database_respalda_y_recrea_tablas_base(tmp_path, monkeypatch):
    db_path = tmp_path / 'reset.db'
    monkeypatch.setattr(database, 'DB_PATH', db_path)
    database.initialize_database()
    with database.get_connection() as conn:
        conn.execute('CREATE TABLE dato_antiguo (valor TEXT)')
        conn.execute("INSERT INTO dato_antiguo VALUES ('anterior')")

    backup_path = database.reset_database()

    assert backup_path is not None and backup_path.exists()
    with database.get_connection() as conn:
        tablas = {
            fila['name']
            for fila in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert {'destinos', 'paquetes', 'paquete_destino', 'usuarios', 'clientes', 'reservas'} <= tablas
    assert 'dato_antiguo' not in tablas