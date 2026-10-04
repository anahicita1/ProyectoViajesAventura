import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "viajes_aventura.db"


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Genera una conexión SQLite con soporte de foreign keys habilitado."""
    target = db_path or str(DB_PATH)
    connection = sqlite3.connect(target)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def ensure_parent_dir() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def initialize_database() -> None:
    ensure_parent_dir()
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                rut TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                rol TEXT NOT NULL CHECK(rol IN ('CLIENTE', 'ADMINISTRADOR')),
                activo INTEGER NOT NULL DEFAULT 1,
                intentos_fallidos INTEGER NOT NULL DEFAULT 0,
                bloqueado_hasta TEXT DEFAULT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS destinos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                region TEXT NOT NULL,
                descripcion TEXT DEFAULT '',
                costo_base INTEGER NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1,
                latitud REAL DEFAULT 0.0,
                longitud REAL DEFAULT 0.0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS paquetes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                destino_id INTEGER NOT NULL,
                destinos_secundarios TEXT DEFAULT '[]',
                precio_base INTEGER NOT NULL,
                precio_congelado INTEGER NOT NULL,
                cupos_total INTEGER NOT NULL,
                descripcion TEXT DEFAULT '',
                activo INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (destino_id) REFERENCES destinos(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reservas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                paquete_id INTEGER NOT NULL,
                pasajeros INTEGER NOT NULL CHECK(pasajeros > 0),
                precio_total INTEGER NOT NULL,
                estado TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK(estado IN ('PENDIENTE', 'CONFIRMADA', 'CANCELADA', 'VENCIDA')),
                fecha_reserva TEXT NOT NULL,
                fecha_salida TEXT NOT NULL,
                FOREIGN KEY (cliente_id) REFERENCES usuarios(id),
                FOREIGN KEY (paquete_id) REFERENCES paquetes(id)
            )
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_unica_reserva_confirmada
            ON reservas(cliente_id, paquete_id)
            WHERE estado = 'CONFIRMADA'
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_reservas_paquete_estado
            ON reservas(paquete_id, estado)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_destinos_activos
            ON destinos(activo)
            """
        )
