import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "viajes_aventura.db"


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Genera una conexión SQLite con soporte de FK y fila legible por nombre."""
    target = db_path or str(DB_PATH)
    connection = sqlite3.connect(target)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def ensure_parent_dir() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def reset_database() -> Path | None:
    """Recrear la base de datos conservando una copia de seguridad previa."""
    ensure_parent_dir()
    backup_path = None
    if DB_PATH.exists():
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        backup_path = DB_PATH.with_name(f'{DB_PATH.stem}.backup-{timestamp}{DB_PATH.suffix}')
        shutil.copy2(DB_PATH, backup_path)

    conn = get_connection()
    try:
        conn.execute('PRAGMA foreign_keys = OFF')
        triggers = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger'"
        ).fetchall()
        for trigger in triggers:
            trigger_name = trigger['name'].replace('"', '""')
            conn.execute(f'DROP TRIGGER "{trigger_name}"')
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        for table in tables:
            table_name = table['name'].replace('"', '""')
            conn.execute(f'DROP TABLE "{table_name}"')
        conn.commit()
    finally:
        conn.close()

    initialize_database()
    return backup_path


def _migrate_legacy_accounts(conn: sqlite3.Connection) -> tuple[list[dict], list[dict]]:
    tables = {
        row['name']
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }
    if 'usuarios' not in tables or 'clientes' in tables:
        return [], []

    columns = {row['name'] for row in conn.execute('PRAGMA table_info(usuarios)').fetchall()}
    if 'rol' not in columns:
        return [], []

    usuarios = [dict(row) for row in conn.execute('SELECT * FROM usuarios').fetchall()]
    reservas = (
        [dict(row) for row in conn.execute('SELECT * FROM reservas').fetchall()]
        if 'reservas' in tables
        else []
    )

    conn.execute('PRAGMA foreign_keys = OFF')
    try:
        triggers = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger' AND tbl_name IN ('usuarios', 'reservas')"
        ).fetchall()
        for trigger in triggers:
            trigger_name = trigger['name'].replace('"', '""')
            conn.execute(f'DROP TRIGGER "{trigger_name}"')
        if 'reservas' in tables:
            conn.execute('DROP TABLE reservas')
        conn.execute('DROP TABLE usuarios')
        conn.commit()
    finally:
        conn.execute('PRAGMA foreign_keys = ON')

    return usuarios, reservas


def _restore_legacy_accounts(
    conn: sqlite3.Connection,
    usuarios_legacy: list[dict],
    reservas_legacy: list[dict],
) -> None:
    if not usuarios_legacy:
        return

    usuarios_por_id = {int(usuario['id']): usuario for usuario in usuarios_legacy}
    ids_clientes = set()

    for usuario in usuarios_legacy:
        rol = str(usuario.get('rol') or '').upper()
        valores = (
            usuario['id'], usuario['nombre'], usuario['apellido'], usuario['rut'],
            usuario['email'], usuario['password_hash'], usuario['salt'],
            usuario.get('activo', 1), usuario.get('intentos_fallidos', 0),
            usuario.get('bloqueado_hasta'),
        )
        if rol == 'ADMINISTRADOR':
            conn.execute(
                """
                INSERT INTO usuarios (
                    id, nombre, apellido, rut, email, password_hash, salt,
                    activo, intentos_fallidos, bloqueado_hasta, rol
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ADMINISTRADOR')
                """,
                valores,
            )
        elif rol == 'CLIENTE':
            conn.execute(
                """
                INSERT INTO clientes (
                    id, nombre, apellido, rut, email, telefono, password_hash, salt,
                    activo, intentos_fallidos, bloqueado_hasta
                ) VALUES (?, ?, ?, ?, ?, '', ?, ?, ?, ?, ?)
                """,
                valores,
            )
            ids_clientes.add(int(usuario['id']))

    admin_ids_with_reservations = {
        int(reserva['cliente_id'])
        for reserva in reservas_legacy
        if int(reserva['cliente_id']) in usuarios_por_id
        and str(usuarios_por_id[int(reserva['cliente_id'])].get('rol') or '').upper() != 'CLIENTE'
    }
    for admin_id in admin_ids_with_reservations:
        admin = usuarios_por_id[admin_id]
        conn.execute(
            """
            INSERT INTO clientes (
                id, nombre, apellido, rut, email, telefono, password_hash, salt,
                activo, intentos_fallidos, bloqueado_hasta
            ) VALUES (?, 'Cuenta histórica', 'Administrativa', ?, ?, '', ?, ?, 0, 0, NULL)
            """,
            (
                admin_id,
                f'LEGACY-{admin_id}',
                f'legacy-admin-{admin_id}@invalid.local',
                admin['password_hash'],
                admin['salt'],
            ),
        )
        ids_clientes.add(admin_id)

    for reserva in reservas_legacy:
        cliente_id = int(reserva['cliente_id'])
        if cliente_id not in ids_clientes:
            continue
        conn.execute(
            """
            INSERT INTO reservas (
                id, cliente_id, paquete_id, pasajeros, precio_total, estado,
                fecha_reserva, fecha_salida
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reserva['id'], cliente_id, reserva['paquete_id'], reserva['pasajeros'],
                reserva['precio_total'], reserva['estado'], reserva['fecha_reserva'],
                reserva['fecha_salida'],
            ),
        )


def initialize_database() -> None:
    """Crea el esquema del sistema con 3FN y controles de integridad vigentes."""
    ensure_parent_dir()
    with get_connection() as conn:
        triggers = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger'"
        ).fetchall()
        for trigger in triggers:
            trigger_name = trigger['name'].replace('"', '""')
            conn.execute(f'DROP TRIGGER "{trigger_name}"')

        usuarios_legacy, reservas_legacy = _migrate_legacy_accounts(conn)
        tables = {
            row['name']
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
        if 'paquete_destinos' in tables and 'paquete_destino' not in tables:
            conn.execute('ALTER TABLE paquete_destinos RENAME TO paquete_destino')
        conn.executescript(
            """
            BEGIN;

            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                rut TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'ADMINISTRADOR' CHECK (rol = 'ADMINISTRADOR'),
                area TEXT NOT NULL DEFAULT 'ADMINISTRACION'
                    CHECK (area IN ('CATALOGO', 'RESERVAS', 'DATOS', 'ADMINISTRACION')),
                activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
                intentos_fallidos INTEGER NOT NULL DEFAULT 0 CHECK (intentos_fallidos >= 0),
                bloqueado_hasta TEXT DEFAULT NULL,
                CHECK (length(trim(nombre)) > 0),
                CHECK (length(trim(apellido)) > 0),
                CHECK (length(trim(email)) > 0),
                CHECK (length(trim(rut)) > 0)
            );

            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                rut TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                telefono TEXT NOT NULL DEFAULT '',
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
                intentos_fallidos INTEGER NOT NULL DEFAULT 0 CHECK (intentos_fallidos >= 0),
                bloqueado_hasta TEXT DEFAULT NULL,
                CHECK (length(trim(nombre)) > 0),
                CHECK (length(trim(apellido)) > 0),
                CHECK (length(trim(email)) > 0),
                CHECK (length(trim(rut)) > 0)
            );

            CREATE TABLE IF NOT EXISTS destinos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                region TEXT NOT NULL,
                descripcion TEXT DEFAULT '',
                costo_base INTEGER NOT NULL CHECK (costo_base >= 0),
                duracion_dias INTEGER NOT NULL DEFAULT 1 CHECK (duracion_dias > 0),
                activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
                latitud REAL DEFAULT 0.0,
                longitud REAL DEFAULT 0.0,
                CHECK (length(trim(nombre)) > 0),
                CHECK (length(trim(region)) > 0)
            );

            CREATE TABLE IF NOT EXISTS paquetes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                destino_id INTEGER NOT NULL,
                descripcion TEXT DEFAULT '',
                precio_base INTEGER NOT NULL CHECK (precio_base >= 0),
                precio_congelado INTEGER NOT NULL CHECK (precio_congelado >= 0),
                margen_porcentaje REAL NOT NULL DEFAULT 0 CHECK (margen_porcentaje >= 0),
                cupos_total INTEGER NOT NULL CHECK (cupos_total > 0),
                fecha_salida TEXT DEFAULT NULL CHECK (fecha_salida IS NULL OR date(fecha_salida) IS NOT NULL),
                fecha_regreso TEXT DEFAULT NULL CHECK (fecha_regreso IS NULL OR date(fecha_regreso) IS NOT NULL),
                activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
                FOREIGN KEY (destino_id) REFERENCES destinos(id),
                CHECK (length(trim(nombre)) > 0)
            );

            CREATE TABLE IF NOT EXISTS paquete_destino (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paquete_id INTEGER NOT NULL,
                destino_id INTEGER NOT NULL,
                orden INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (paquete_id) REFERENCES paquetes(id),
                FOREIGN KEY (destino_id) REFERENCES destinos(id),
                UNIQUE (paquete_id, destino_id),
                CHECK (orden >= 1)
            );

            CREATE TABLE IF NOT EXISTS reservas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                paquete_id INTEGER NOT NULL,
                pasajeros INTEGER NOT NULL CHECK (pasajeros > 0),
                precio_total INTEGER NOT NULL CHECK (precio_total >= 0),
                estado TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'CONFIRMADA', 'CANCELADA', 'VENCIDA')),
                fecha_reserva TEXT NOT NULL CHECK (date(fecha_reserva) IS NOT NULL),
                fecha_salida TEXT NOT NULL CHECK (date(fecha_salida) IS NOT NULL),
                FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                FOREIGN KEY (paquete_id) REFERENCES paquetes(id)
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_usuario_rut_unique ON usuarios(rut);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_usuario_email_unique ON usuarios(email COLLATE NOCASE);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_cliente_rut_unique ON clientes(rut);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_cliente_email_unique ON clientes(email COLLATE NOCASE);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_unica_reserva_confirmada
            ON reservas(cliente_id, paquete_id)
            WHERE estado = 'CONFIRMADA';

            CREATE INDEX IF NOT EXISTS idx_reservas_paquete_estado ON reservas(paquete_id, estado);
            CREATE INDEX IF NOT EXISTS idx_reservas_cliente_estado ON reservas(cliente_id, estado);
            CREATE INDEX IF NOT EXISTS idx_clientes_activos ON clientes(activo);
            CREATE INDEX IF NOT EXISTS idx_destinos_activos ON destinos(activo);
            CREATE INDEX IF NOT EXISTS idx_paquetes_activos ON paquetes(activo);
            CREATE INDEX IF NOT EXISTS idx_paquete_destino_paquete ON paquete_destino(paquete_id);
            CREATE INDEX IF NOT EXISTS idx_paquete_destino_destino ON paquete_destino(destino_id);

            COMMIT;
            """
        )

        _restore_legacy_accounts(conn, usuarios_legacy, reservas_legacy)

        columnas_paquetes = {
            fila['name'] for fila in conn.execute('PRAGMA table_info(paquetes)').fetchall()
        }
        if 'margen_porcentaje' not in columnas_paquetes:
            conn.execute(
                'ALTER TABLE paquetes ADD COLUMN margen_porcentaje REAL NOT NULL DEFAULT 0'
            )
        if 'fecha_salida' not in columnas_paquetes:
            conn.execute('ALTER TABLE paquetes ADD COLUMN fecha_salida TEXT DEFAULT NULL')
        if 'fecha_regreso' not in columnas_paquetes:
            conn.execute('ALTER TABLE paquetes ADD COLUMN fecha_regreso TEXT DEFAULT NULL')

        columnas_usuarios = {
            fila['name'] for fila in conn.execute('PRAGMA table_info(usuarios)').fetchall()
        }
        if 'area' not in columnas_usuarios:
            conn.execute(
                "ALTER TABLE usuarios ADD COLUMN area TEXT NOT NULL DEFAULT 'ADMINISTRACION'"
            )
        conn.execute('CREATE INDEX IF NOT EXISTS idx_usuarios_area ON usuarios(area)')

        columnas_destinos = {
            fila['name'] for fila in conn.execute('PRAGMA table_info(destinos)').fetchall()
        }
        if 'duracion_dias' not in columnas_destinos:
            conn.execute(
                'ALTER TABLE destinos ADD COLUMN duracion_dias INTEGER NOT NULL DEFAULT 1'
            )

        conn.executescript(
            """
            CREATE TRIGGER IF NOT EXISTS trg_no_delete_destino
            BEFORE DELETE ON destinos
            BEGIN
                SELECT CASE
                    WHEN EXISTS (SELECT 1 FROM paquetes WHERE destino_id = OLD.id)
                      OR EXISTS (SELECT 1 FROM paquete_destino WHERE destino_id = OLD.id)
                    THEN RAISE(ABORT, 'No se permite DELETE físico del destino asociado a paquetes.')
                END;
            END;

            CREATE TRIGGER IF NOT EXISTS trg_no_delete_paquete
            BEFORE DELETE ON paquetes
            BEGIN
                SELECT CASE
                    WHEN EXISTS (SELECT 1 FROM reservas WHERE paquete_id = OLD.id)
                    THEN RAISE(ABORT, 'No se permite DELETE físico del paquete. Use activo = 0.')
                END;
            END;

            CREATE TRIGGER IF NOT EXISTS trg_no_delete_reserva
            BEFORE DELETE ON reservas
            BEGIN
                SELECT RAISE(ABORT, 'Las reservas no se eliminan físicamente. Cambie su estado.');
            END;

            CREATE TRIGGER IF NOT EXISTS trg_usuario_email_cliente_insert
            BEFORE INSERT ON usuarios
            WHEN EXISTS (SELECT 1 FROM clientes WHERE email = NEW.email COLLATE NOCASE)
            BEGIN
                SELECT RAISE(ABORT, 'El correo ya está registrado.');
            END;

            CREATE TRIGGER IF NOT EXISTS trg_cliente_email_usuario_insert
            BEFORE INSERT ON clientes
            WHEN EXISTS (SELECT 1 FROM usuarios WHERE email = NEW.email COLLATE NOCASE)
            BEGIN
                SELECT RAISE(ABORT, 'El correo ya está registrado.');
            END;

            CREATE TRIGGER IF NOT EXISTS trg_usuario_rut_cliente_insert
            BEFORE INSERT ON usuarios
            WHEN EXISTS (SELECT 1 FROM clientes WHERE rut = NEW.rut COLLATE NOCASE)
            BEGIN
                SELECT RAISE(ABORT, 'El RUT ya está registrado.');
            END;

            CREATE TRIGGER IF NOT EXISTS trg_cliente_rut_usuario_insert
            BEFORE INSERT ON clientes
            WHEN EXISTS (SELECT 1 FROM usuarios WHERE rut = NEW.rut COLLATE NOCASE)
            BEGIN
                SELECT RAISE(ABORT, 'El RUT ya está registrado.');
            END;

            CREATE TRIGGER IF NOT EXISTS trg_usuario_email_cliente_update
            BEFORE UPDATE OF email ON usuarios
            WHEN EXISTS (SELECT 1 FROM clientes WHERE email = NEW.email COLLATE NOCASE)
            BEGIN
                SELECT RAISE(ABORT, 'El correo ya está registrado.');
            END;

            CREATE TRIGGER IF NOT EXISTS trg_cliente_email_usuario_update
            BEFORE UPDATE OF email ON clientes
            WHEN EXISTS (SELECT 1 FROM usuarios WHERE email = NEW.email COLLATE NOCASE)
            BEGIN
                SELECT RAISE(ABORT, 'El correo ya está registrado.');
            END;

            CREATE TRIGGER IF NOT EXISTS trg_usuario_rut_cliente_update
            BEFORE UPDATE OF rut ON usuarios
            WHEN EXISTS (SELECT 1 FROM clientes WHERE rut = NEW.rut COLLATE NOCASE)
            BEGIN
                SELECT RAISE(ABORT, 'El RUT ya está registrado.');
            END;

            CREATE TRIGGER IF NOT EXISTS trg_cliente_rut_usuario_update
            BEFORE UPDATE OF rut ON clientes
            WHEN EXISTS (SELECT 1 FROM usuarios WHERE rut = NEW.rut COLLATE NOCASE)
            BEGIN
                SELECT RAISE(ABORT, 'El RUT ya está registrado.');
            END;
            """
        )
