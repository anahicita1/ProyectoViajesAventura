import sqlite3
import hashlib
import os

# 1. Buscar la base de datos SQLite en el proyecto
db_file = None
for root, dirs, files in os.walk("."):
    for f in files:
        if f.endswith(".db") or f.endswith(".sqlite"):
            db_file = os.path.join(root, f)
            break
    if db_file:
        break

if not db_file:
    db_file = "viajes_aventura.db"

print(f"-> Conectando a base de datos: {db_file}")

# 2. Función de Hashing (SHA-256)
def generar_hash(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# 3. Asegurar que exista la tabla de usuarios
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    email TEXT UNIQUE,
    password TEXT,
    rol TEXT DEFAULT 'socio'
)
""")

# 4. Datos del socio para la prueba
email_prueba = "paulinaovalle@gmail.com"
password_prueba = "viajesaventura"
hash_prueba = generar_hash(password_prueba)

# 5. Insertar o reemplazar el usuario
try:
    cursor.execute("""
        INSERT INTO usuarios (nombre, email, password, rol)
        VALUES (?, ?, ?, 'socio')
        ON CONFLICT(email) DO UPDATE SET password = excluded.password
    """, ("Paulina Ovalle", email_prueba, hash_prueba))
    
    # También intentamos guardar la clave sin hash por si tu login compara texto plano
    cursor.execute("""
        INSERT INTO usuarios (nombre, email, password, rol)
        VALUES (?, ?, ?, 'socio')
        ON CONFLICT(email) DO UPDATE SET password = excluded.password
    """, ("Paulina (Plano)", "socio@prueba.com", password_prueba))

    conn.commit()
    print("✅ Cuentas de socios creadas con éxito:")
    print(f"   Option 1 -> Email: {email_prueba} | Clave: {password_prueba}")
    print(f"   Option 2 -> Email: socio@prueba.com | Clave: {password_prueba}")

except Exception as e:
    print(f"❌ Error al insertar socio: {e}")
finally:
    conn.close()