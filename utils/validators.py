from __future__ import annotations

from datetime import datetime


def validar_rut_chileno(rut: str) -> bool:
    """Valida RUT chileno usando el algoritmo Módulo 11."""
    rut = rut.strip().upper().replace('.', '').replace('-', '')
    if len(rut) < 2 or not rut[:-1].isdigit():
        return False
    dv = rut[-1]
    cuerpo = rut[:-1]
    suma = 0
    multiplo = 2
    for digito in reversed(cuerpo):
        suma += int(digito) * multiplo
        multiplo += 1
        if multiplo == 8:
            multiplo = 2
    resto = suma % 11
    resultado = 11 - resto
    dv_esperado = '0' if resultado == 11 else 'K' if resultado == 10 else str(resultado)
    return dv == dv_esperado


def enmascarar_rut(rut: str) -> str:
    if not rut:
        return ''
    rut_limpio = rut.strip().upper()
    if len(rut_limpio) <= 2:
        return rut_limpio
    if '-' in rut_limpio:
        cuerpo, dv = rut_limpio.split('-', 1)
    else:
        cuerpo, dv = rut_limpio[:-1], rut_limpio[-1]
    numero = cuerpo.replace('.', '')
    if len(numero) <= 3:
        return f'{numero}-{dv}'
    masked = f'{numero[:-3]}.XXX.XXX-{dv}'
    return masked


def enmascarar_telefono(telefono: str) -> str:
    if not telefono:
        return ''
    digits = ''.join(ch for ch in telefono if ch.isdigit())
    if len(digits) <= 4:
        return telefono
    return f'+56 9 XXXX {digits[-4:]}'


def fecha_valida(fecha: str) -> bool:
    try:
        datetime.fromisoformat(fecha)
        return True
    except ValueError:
        return False
