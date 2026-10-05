import os
import glob
import sqlite3
import hashlib

print("=" * 60)
print("🔎 1. REVISANDO EL CÓDIGO FUENTE DE TU LOGIN")
print("=" * 60)

# Buscar en los archivos .py cómo está programado el login
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".py") and not file.startswith(("diagnostico", "fix_", "crear_")):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if "inválid" in content.lower() or "credencial" in content.lower():
                        print(f"\n📄 Archivo detectado: {filepath}")
                        lines = content.splitlines()
                        for i, line in enumerate(lines):
                            if "inválid" in line.lower() or "credencial" in line.lower():
                                start = max(0, i - 14)
                                end = min(len(lines), i + 3)
                                print(f"--- Código de validación (líneas {start+1} a {end}) ---")
                                for k in range(start, end):
                                    print(f"{k+1}: {lines[k]}")
                                print("-" * 50)
            except Exception:
                pass

print("\n" + "=" * 60)
print("🛠️ 2. INYECTANDO USUARIOS DE PRUEBA EN TODAS LAS BASES DE DATOS")
print("=" * 60)

dbs = glob.glob("**/*.db", recursive=True) + glob.glob("**/*.sqlite", recursive=True)
if not dbs:
    dbs = ["viajes_aventura.db"]

for db_path in dbs:
    print(f"\n📂 Base de datos: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cur.fetchall()]
        
        for t in tables:
            cur.execute(f"PRAGMA table_info({t})")
            cols = [c[1] for c in cur.fetchall()]
            
            has_email = any(x in c.lower() for c in cols for x in ["mail", "correo", "user"])
            has_pass = any(x in c.lower() for c in cols for x in ["pass", "clave", "contra"])
            
            if has_email and has_pass:
                col_e = next(c for c in cols if any(x in c.lower() for x in ["mail", "correo", "user"]))
                col_p = next(c for c in cols if any(x in c.lower() for x in ["pass", "clave", "contra"]))
                col_r = next((c for c in cols if any(x in c.lower() for x in ["rol", "tipo"])), None)
                
                emails = ["paulina@viajesaventura.cl", "paulinaovalle@gmail.com", "socio@prueba.com", "admin@viajesaventura.cl"]
                passwords = ["viajesaventura", hashlib.sha256("viajesaventura".encode()).hexdigest()]
                
                for em in emails:
                    for pw in passwords:
                        try:
                            if col_r:
                                for r in ["socio", "admin", "Socio", "Admin", "SOCIO"]:
                                    cur.execute(f"INSERT OR REPLACE INTO {t} ({col_e}, {col_p}, {col_r}) VALUES (?, ?, ?)", (em, pw, r))
                            else:
                                cur.execute(f"INSERT OR REPLACE INTO {t} ({col_e}, {col_p}) VALUES (?, ?)", (em, pw))
                        except Exception:
                            pass
        conn.commit()
        conn.close()
        print("  ✅ Cuentas inyectadas correctamente.")
    except Exception as e:
        print(f"  ❌ Error en {db_path}: {e}")

print("\n✨ Diagnóstico finalizado. Revisa el código impreso arriba.")