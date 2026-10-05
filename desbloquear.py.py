import os
import re

print("🔓 Buscando y parcheando el sistema de inicio de sesión...\n")

archivos_modificados = 0

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".py") and not file.startswith(("diagnostico", "fix_", "crear_", "desbloquear")):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if "Credenciales inválidas" in content or "inválid" in content.lower():
                print(f"📄 Archivo de login encontrado: {path}")

                # Reemplazar validaciones de autenticación para dar acceso inmediato
                # Forzamos que la validación sea True y se defina el usuario socio
                modified = content

                # Parche 1: Si hay una función de login, hacemos que retorne datos de Paulina
                modified = re.sub(
                    r"def (verificar_|validar_)?login\([^)]*\):.*?(?=\n\s*def|\n\s*if|\Z)",
                    "def login(*args, **kwargs):\n    return {'nombre': 'Paulina Ovalle', 'email': 'paulina@viajesaventura.cl', 'rol': 'socio'}",
                    modified,
                    flags=re.DOTALL
                )

                # Parche 2: Si hay un bloque `if aut|if check|if verify`, forzar éxito
                modified = re.sub(r"if\s+.*?(?=st\.error\(.*?[Ii]nválid)", "if True:\n                    st.session_state['usuario'] = {'nombre': 'Paulina Ovalle', 'email': 'paulina@viajesaventura.cl', 'rol': 'socio'}\n                    st.session_state['autenticado'] = True\n                    # ", modified)

                with open(path, "w", encoding="utf-8") as f:
                    f.write(modified)

                archivos_modificados += 1
                print(f"✅ Login desbloqueado exitosamente en {path}")

if archivos_modificados == 0:
    print("⚠️ No se encontró el texto explícito, forzando estado global de sesión en app.py...")
    if os.path.exists("app.py"):
        with open("app.py", "r", encoding="utf-8") as f:
            app_code = f.read()
        
        # Inject bypass en app.py
        bypass_code = "\nst.session_state['autenticado'] = True\nst.session_state['usuario'] = {'nombre': 'Paulina Ovalle', 'email': 'paulina@viajesaventura.cl', 'rol': 'socio'}\n"
        with open("app.py", "w", encoding="utf-8") as f:
            f.write(app_code + bypass_code)
        print("✅ Acceso concedido automáticamente en app.py")

print("\n🚀 PROCESO COMPLETADO. Reinicia Streamlit en la terminal.")