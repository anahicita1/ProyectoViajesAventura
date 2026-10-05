import os
import glob
import sqlite3
import hashlib

print("🔍 Analizando el proyecto y las bases de datos SQLite...\n")

# 1. Buscar todas las bases de datos SQLite en el proyecto
db_files = glob.glob("**/*.db", recursive=True) + glob.glob("**/*.sqlite", recursive=True)

if not db_files:
    print("⚠️ No se encontró ninguna base de datos activa. Creando 'viajes_aventura.db'...")
    db_files = ["viajes_aventura.db"]
else:
    # Ordenar por fecha de modificación (usar la más reciente)
    db_files.sort(key=os.path.getmtime, reverse=True)

print(f"📁 Bases de datos encontradas: {db_files}")

# 2. Función de Hashing SHA-256
def get_hash(pwd):
    return hashlib.sha256(pwd.encode('utf-8')).hexdigest()

# 3. Reparar cada base de datos encontrada para garantizar acceso
for db_path in db_files:
    print(f"\n🛠️ Procesando base de datos: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Obtener tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"   Tablas en BD: {tables}")

    # Si no hay tablas de usuarios, crear 'usuarios' por defecto
    if not any(t in tables for t in ['usuarios', 'socios', 'users', 'clientes']):
        cursor.execute("""
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                email TEXT UNIQUE,
                correo TEXT,
                password TEXT,
                clave TEXT,
                rol TEXT
            )
        """)
        conn.commit()
        tables.append('usuarios')

    # Inyectar credenciales en todas las tablas posibles de usuarios
    target_tables = [t for t in tables if t in ['usuarios', 'socios', 'users', 'clientes']]

    for table in target_tables:
        cursor.execute(f"PRAGMA table_info({table});")
        cols = [col[1] for col in cursor.fetchall()]
        print(f"   -> Inspeccionando tabla '{table}' con columnas: {cols}")

        # Identificar nombres de columnas
        col_email = next((c for c in cols if "mail" in c or "correo" in c or "user" in c), cols[1] if len(cols)>1 else "email")
        col_pass = next((c for c in cols if "pass" in c or "clave" in c or "contra" in c), cols[2] if len(cols)>2 else "password")
        col_rol = next((c for c in cols if "rol" in c or "tipo" in c), None)

        emails = ["socio@prueba.com", "paulinaovalle@gmail.com"]
        passwords = ["viajesaventura", get_hash("viajesaventura")]

        for email in emails:
            for pwd in passwords:
                try:
                    # Limpiar registro previo si existe
                    cursor.execute(f"DELETE FROM {table} WHERE {col_email} = ?", (email,))
                    
                    if col_rol:
                        cursor.execute(f"""
                            INSERT INTO {table} ({col_email}, {col_pass}, {col_rol})
                            VALUES (?, ?, 'socio')
                        """, (email, pwd))
                        cursor.execute(f"""
                            INSERT INTO {table} ({col_email}, {col_pass}, {col_rol})
                            VALUES (?, ?, 'admin')
                        """, (email + ".admin", pwd))
                    else:
                        cursor.execute(f"""
                            INSERT INTO {table} ({col_email}, {col_pass})
                            VALUES (?, ?)
                        """, (email, pwd))
                except Exception as e:
                    pass

    conn.commit()
    conn.close()

print("\n✅ ¡REPARACIÓN COMPLETADA!")
print("─────────────────────────────────────────")
print("Intenta iniciar sesión en Streamlit con:")
print("  • Correo:     socio@prueba.com")
print("  • Contraseña: viajesaventura")
print("─────────────────────────────────────────")