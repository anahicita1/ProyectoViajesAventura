# Viajes Aventura

Aplicación de reservas turísticas construida con Python, Streamlit y SQLite. Separa el portal público de clientes de las herramientas internas de socios y conserva las reglas de catálogo, precios, disponibilidad, autenticación y privacidad en servicios y base de datos.

## Requisitos

- Python 3.10 o superior.
- Dependencias listadas en `requirements.txt` (`streamlit`, `requests` y `pytest`).

## Instalación y ejecución

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Al iniciar, `app.py` ejecuta `bootstrap_database()` para crear/migrar el esquema de forma idempotente, insertar seeds oficiales faltantes y archivar algunos nombres de seeds anteriores. El arranque normal no elimina la base ni borra datos existentes; los registros oficiales ya existentes conservan sus modificaciones administrativas.

## Portales

El selector de la barra lateral ofrece:

- **🌴 Portal Clientes:** catálogo público, detalle de paquetes, precio en CLP y referencia USD, clima actual y cupos. Se exige login para reservar o consultar **Mis Reservas**. El historial se filtra por el ID del cliente autenticado.
- **🔑 Acceso Socios:** login interno, sin autorregistro público. Las cuentas deben existir como socios en `usuarios`.

Las contraseñas se procesan con PBKDF2-HMAC-SHA256 y salt aleatorio. La sesión de Streamlit contiene solo ID, nombre, apellido, rol y, para socios, área; no almacena contraseña, hash, salt, RUT ni teléfono.

## Cuentas de socios seed

El bootstrap crea las siguientes cuentas si todavía no existen:

| Socio | Correo | Área autorizada |
| --- | --- | --- |
| Paulina Ovalle | `paulina@viajesaventura.cl` | Catálogo y Paquetes (`CATALOGO`) |
| Matías Bórquez | `matias@viajesaventura.cl` | Atención y Reservas (`RESERVAS`) |
| Ignacio Salas | `ignacio@viajesaventura.cl` | Administración y Datos (`DATOS`) |

Cada socio puede tener una contraseña propia mediante `VIAJES_PAULINA_PASSWORD`, `VIAJES_MATIAS_PASSWORD` o `VIAJES_IGNACIO_PASSWORD`. Si no se define una, se usa `VIAJES_SOCIOS_PASSWORD`; el fallback del entorno local es `ViajesAventura2026!`. Configura secretos únicos antes del primer bootstrap en cualquier despliegue compartido. Cambiar estas variables no rota las contraseñas de cuentas ya creadas.

## Base de datos

La base SQLite se guarda en `data/viajes_aventura.db`. El esquema contiene:

- `destinos`: región, duración, costo base, coordenadas y disponibilidad.
- `paquetes`: costo agregado, margen, precio congelado, cupos, fechas y estado.
- `paquete_destino`: destinos vinculados y orden de la ruta.
- `usuarios`: cuentas de socios/administradores con área autorizada.
- `clientes`: cuentas de clientes, RUT, teléfono, hash y datos de bloqueo.
- `reservas`: cliente, paquete, pasajeros, total oficial en CLP, fechas y estado.

`initialize_database()` migra instalaciones anteriores, incluida la separación de clientes desde la antigua tabla `usuarios`, preserva los hashes y las reservas históricas, y renombra `paquete_destinos` a `paquete_destino` cuando corresponde. Elimina triggers antiguos antes de cualquier migración y los crea de nuevo después de crear las tablas y aplicar columnas faltantes.

### Reinicio desde cero

El reinicio es explícito y destructivo. Primero genera una copia de seguridad con sufijo de fecha/hora y luego recrea el esquema y los seeds:

```powershell
python bootstrap.py --reset
```

La copia queda junto a la base de datos como `viajes_aventura.backup-<fecha-hora>.db`. No uses `--reset` para iniciar Streamlit: la aplicación llama el bootstrap normal y conserva datos existentes.

## Catálogo oficial inicial

El seed contiene seis destinos con coordenadas utilizadas por Open-Meteo:

| Destino | Región | Duración | Costo base (CLP) | Coordenadas |
| --- | --- | ---: | ---: | --- |
| Valle del Elqui | Región de Coquimbo | 2 días | 120.000 | -30.03, -70.52 |
| Salar de Surire | Región de Arica y Parinacota | 3 días | 310.000 | -18.84, -69.09 |
| Cajón del Maipo | Región Metropolitana | 1 día | 45.000 | -33.64, -70.13 |
| Parque Conguillío | Región de La Araucanía | 3 días | 185.000 | -38.64, -71.64 |
| Carretera Austral | Región de Aysén | 7 días | 640.000 | -45.57, -72.07 |
| Isla Damas | Región de Coquimbo | 1 día | 38.000 | -29.25, -71.53 |

También se siembran tres paquetes; el precio congelado es costo base agregado más 20%:

| Paquete | Ruta | Salida – regreso | Cupos | Precio por persona (CLP) |
| --- | --- | --- | ---: | ---: |
| Norte Grande en 5 días | Salar de Surire + Valle del Elqui | 2027-07-10 – 2027-07-15 | 12 | 516.000 |
| Escapada de fin de semana | Cajón del Maipo + Isla Damas | 2026-11-14 – 2026-11-16 | 20 | 99.600 |
| Sur profundo | Parque Conguillío + Carretera Austral | 2027-01-20 – 2027-01-30 | 8 | 990.000 |

## Herramientas de socios

- **Paulina / Gestión de Catálogo:** crea y edita destinos; calcula automáticamente precio base y precio congelado de paquetes de 2 a 5 destinos; fija margen, fechas y cupos. Un destino sin paquetes se puede eliminar; si está asociado, R8 lo marca no disponible y mantiene intactos los paquetes existentes.
- **Matías / Control de Reservas y Cupos:** consulta cupos máximos, vendidos y disponibles; identifica paquetes expirados comparando salida con la fecha actual; filtra reservas y puede cancelarlas.
- **Ignacio / Visor Global:** consulta reservas y clientes, recaudación confirmada en CLP, pasajeros atendidos, ocupación e historial por cliente.

El acceso se limita por `area` en la sesión autenticada y vuelve a validarse dentro de la vista administrativa.

## Reglas de reservas y privacidad

- Los paquetes admiten entre 2 y 5 destinos activos. El costo base se suma desde los destinos; el margen se calcula y el precio queda congelado al publicar.
- El servicio de reservas valida cliente activo, fecha de salida futura, fecha programada, destinos/cupo y duplicados dentro de una transacción `BEGIN IMMEDIATE`.
- Las reservas guardan únicamente el total oficial en pesos chilenos: precio congelado por persona multiplicado por pasajeros. USD es solo informativo.
- Los cupos disponibles se calculan como cupo total menos pasajeros de reservas confirmadas. Cambiar una reserva a `CANCELADA` los libera automáticamente; no hay contador duplicado.
- Las reservas, paquetes o destinos con historial se protegen contra borrado físico según corresponda; se conserva la trazabilidad mediante estados y disponibilidad lógica.
- En tablas del visor global, RUT y teléfono se enmascaran. No se deben imprimir esos datos en mensajes ni logs.

## Pruebas

Ejecuta la suite con:

```powershell
python -m pytest -q
```

Las pruebas cubren modelos, bootstrap y seeds, migración de cuentas, hashing, total de reserva en CLP, cancelación/liberación de cupos y concurrencia. Las pruebas que escriben datos deben usar bases temporales.

## Informe de auditoría de IA

El reporte de uso crítico de IA está en `docs/AI_AUDIT_REPORT.md`.