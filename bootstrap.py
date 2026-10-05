from __future__ import annotations

import sqlite3
import os
import sys
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from config.database import get_connection, initialize_database, reset_database
from services.autenticacion_service import AutenticacionService
from repositories.usuario_repository import UsuarioRepository


def _rut_con_digito_verificador(numero: int) -> str:
    suma = 0
    factor = 2
    for digito in reversed(str(numero)):
        suma += int(digito) * factor
        factor = 2 if factor == 7 else factor + 1
    resultado = 11 - suma % 11
    verificador = '0' if resultado == 11 else 'K' if resultado == 10 else str(resultado)
    return f'{numero}-{verificador}'


def bootstrap_database(reset: bool = False) -> Path | None:
    backup_path = None
    if reset:
        backup_path = reset_database()
    else:
        initialize_database()

    password_socios = os.environ.get('VIAJES_SOCIOS_PASSWORD', 'ViajesAventura2026!')

    with get_connection() as conn:
        admin_exists = conn.execute(
            """
            SELECT 1 FROM usuarios
            WHERE email = 'admin@viajesaventura.cl'
               OR replace(replace(rut, '.', ''), '-', '') = '111111111'
            LIMIT 1
            """
        ).fetchone()

    if not admin_exists:
        try:
            AutenticacionService.registrar_usuario(
                nombre='Admin',
                apellido='Sistema',
                rut=_rut_con_digito_verificador(11111111),
                email='admin@viajesaventura.cl',
                password=password_socios,
                rol='ADMINISTRADOR',
                area='ADMINISTRACION',
            )
        except (sqlite3.IntegrityError, ValueError):
            pass

    socios = (
        ('Paulina', 'Ovalle', 18123456, 'paulina@viajesaventura.cl', 'CATALOGO', 'VIAJES_PAULINA_PASSWORD'),
        ('Matías', 'Bórquez', 17234567, 'matias@viajesaventura.cl', 'RESERVAS', 'VIAJES_MATIAS_PASSWORD'),
        ('Ignacio', 'Salas', 16345678, 'ignacio@viajesaventura.cl', 'DATOS', 'VIAJES_IGNACIO_PASSWORD'),
    )
    for nombre, apellido, rut_numero, email, area, variable_password in socios:
        socio = UsuarioRepository.get_by_email(email)
        if socio is None:
            AutenticacionService.registrar_usuario(
                nombre=nombre,
                apellido=apellido,
                rut=_rut_con_digito_verificador(rut_numero),
                email=email,
                password=os.environ.get(variable_password, password_socios),
                rol='ADMINISTRADOR',
                area=area,
            )
        else:
            UsuarioRepository.actualizar_area(int(socio['id']), area)

    destinos_base = (
        ('Valle del Elqui', 'Región de Coquimbo', 'Valle de cielos despejados y observación astronómica.', 2, 120000, -30.03, -70.52),
        ('Salar de Surire', 'Región de Arica y Parinacota', 'Paisaje altoandino de salares y fauna nativa.', 3, 310000, -18.84, -69.09),
        ('Cajón del Maipo', 'Región Metropolitana', 'Ruta cordillerana de ríos y montañas.', 1, 45000, -33.64, -70.13),
        ('Parque Conguillío', 'Región de La Araucanía', 'Bosques de araucarias, lagunas y paisaje volcánico.', 3, 185000, -38.64, -71.64),
        ('Carretera Austral', 'Región de Aysén', 'Travesía escénica por la Patagonia chilena.', 7, 640000, -45.57, -72.07),
        ('Isla Damas', 'Región de Coquimbo', 'Visita costera a la Reserva Nacional Pingüino de Humboldt.', 1, 38000, -29.25, -71.53),
    )

    paquetes_base = (
        ('Norte Grande en 5 días', 'Salar de Surire y Valle del Elqui: aventura altiplánica y cielos estrellados.', ('Salar de Surire', 'Valle del Elqui'), 20, '2027-07-10', '2027-07-15', 12),
        ('Escapada de fin de semana', 'Cajón del Maipo e Isla Damas: cordillera y costa en una escapada.', ('Cajón del Maipo', 'Isla Damas'), 20, '2026-11-14', '2026-11-16', 20),
        ('Sur profundo', 'Parque Conguillío y Carretera Austral: bosques, lagos y Patagonia.', ('Parque Conguillío', 'Carretera Austral'), 20, '2027-01-20', '2027-01-30', 8),
    )

    with get_connection() as conn:
        conn.execute('BEGIN IMMEDIATE')

        paquetes_seed_anteriores = (
            'Costa entre cerros y mar', 'Lagos y volcanes', 'Travesía del desierto',
            'Escapada Norte y Estrellas', 'Aventura Centro y Cordillera',
            'Ruta Extrema Austral y Salar',
        )
        for nombre in paquetes_seed_anteriores:
            conn.execute('UPDATE paquetes SET activo = 0 WHERE nombre = ?', (nombre,))

        destinos_seed_anteriores = (
            'Valparaíso', 'Viña del Mar', 'Puerto Varas', 'Frutillar',
            'San Pedro de Atacama', 'Calama', 'Destino Concurrencia',
        )
        for nombre in destinos_seed_anteriores:
            conn.execute(
                """
                UPDATE destinos
                SET activo = 0
                WHERE nombre = ?
                  AND NOT EXISTS (
                      SELECT 1
                      FROM paquetes AS p
                      WHERE p.activo = 1
                        AND (
                            p.destino_id = destinos.id
                            OR EXISTS (
                                SELECT 1 FROM paquete_destino AS pd
                                WHERE pd.paquete_id = p.id AND pd.destino_id = destinos.id
                            )
                        )
                  )
                """,
                (nombre,),
            )

        destinos_ids = {}
        costos_base = {}
        for nombre, region, descripcion, duracion_dias, costo_base, latitud, longitud in destinos_base:
            destino = conn.execute(
                'SELECT id FROM destinos WHERE lower(trim(nombre)) = lower(?) ORDER BY id LIMIT 1',
                (nombre,),
            ).fetchone()
            if destino is None:
                cursor = conn.execute(
                    """
                    INSERT INTO destinos (
                        nombre, region, descripcion, duracion_dias, costo_base,
                        latitud, longitud, activo
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (nombre, region, descripcion, duracion_dias, costo_base, latitud, longitud),
                )
                destino_id = int(cursor.lastrowid)
            else:
                destino_id = int(destino['id'])
            destinos_ids[nombre] = destino_id
            costos_base[nombre] = costo_base

        for (
            nombre, descripcion, nombres_destinos, margen,
            fecha_salida, fecha_regreso, cupos_total,
        ) in paquetes_base:
            destinos_paquete = [destinos_ids[nombre_destino] for nombre_destino in nombres_destinos]
            costo_base = sum(costos_base[nombre_destino] for nombre_destino in nombres_destinos)
            precio_congelado = int(
                (Decimal(costo_base) * (Decimal('1') + Decimal(margen) / Decimal('100'))).quantize(
                    Decimal('1'), rounding=ROUND_HALF_UP
                )
            )
            if date.fromisoformat(fecha_regreso) <= date.fromisoformat(fecha_salida):
                raise ValueError(f'La fecha de regreso del paquete {nombre} debe ser posterior a su salida.')

            paquete = conn.execute(
                'SELECT id FROM paquetes WHERE lower(trim(nombre)) = lower(?) ORDER BY id LIMIT 1',
                (nombre,),
            ).fetchone()
            if paquete is None:
                cursor = conn.execute(
                    """
                    INSERT INTO paquetes (
                        nombre, destino_id, descripcion, precio_base, precio_congelado,
                        margen_porcentaje, cupos_total, fecha_salida, fecha_regreso, activo
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        nombre, destinos_paquete[0], descripcion, costo_base,
                        precio_congelado, margen, cupos_total, fecha_salida, fecha_regreso,
                    ),
                )
                paquete_id = int(cursor.lastrowid)
                conn.executemany(
                    'INSERT INTO paquete_destino (paquete_id, destino_id, orden) VALUES (?, ?, ?)',
                    [
                        (paquete_id, destino_id, orden)
                        for orden, destino_id in enumerate(destinos_paquete, start=1)
                    ],
                )
        return backup_path


if __name__ == '__main__':
    reiniciar = '--reset' in sys.argv
    backup = bootstrap_database(reset=reiniciar)
    if reiniciar:
        print(f'Base reiniciada. Copia de seguridad: {backup}')
    else:
        print('Bootstrap completado.')