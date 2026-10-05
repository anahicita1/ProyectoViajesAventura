from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timedelta

from repositories.cliente_repository import ClienteRepository
from repositories.usuario_repository import UsuarioRepository
from utils.validators import validar_rut_chileno
from utils.security import bloquear_temporalmente, generar_salt, hash_password, verificar_password


class AutenticacionService:
    """Servicio responsable de registro, autenticación y bloqueo de cuentas."""

    MAX_INTENTOS_FALLIDOS = 5
    BLOQUEO_MINUTOS = 15

    @staticmethod
    def registrar_usuario(
        nombre: str,
        apellido: str,
        rut: str,
        email: str,
        password: str,
        rol: str = 'CLIENTE',
        telefono: str = '',
        area: str = 'ADMINISTRACION',
    ) -> dict:
        email = email.strip().lower()
        nombre = nombre.strip()
        apellido = apellido.strip()
        rut = rut.strip().upper().replace('.', '').replace('-', '')
        rol = rol.strip().upper()
        if not nombre or not apellido or not rut or not email or not password:
            raise ValueError('Todos los campos son obligatorios.')
        if rol not in {'CLIENTE', 'ADMINISTRADOR'}:
            raise ValueError('El rol solicitado no es válido.')
        if rol == 'ADMINISTRADOR' and area not in {'CATALOGO', 'RESERVAS', 'DATOS', 'ADMINISTRACION'}:
            raise ValueError('Área administrativa no válida.')
        if not validar_rut_chileno(rut):
            raise ValueError('El RUT ingresado no es válido.')
        rut = f'{rut[:-1]}-{rut[-1]}'
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            raise ValueError('El correo electrónico no tiene un formato válido.')
        if rol == 'CLIENTE':
            telefono = telefono.strip()
            digitos_telefono = ''.join(caracter for caracter in telefono if caracter.isdigit())
            if not telefono or not 8 <= len(digitos_telefono) <= 15:
                raise ValueError('Ingresa un teléfono válido.')
            if ClienteRepository.obtener_por_email(email) or UsuarioRepository.get_by_email(email):
                raise ValueError('El correo ya existe en el sistema.')
        elif UsuarioRepository.get_by_email(email) or ClienteRepository.obtener_por_email(email):
            raise ValueError('El correo ya existe en el sistema.')

        salt = generar_salt()
        password_hash = hash_password(password, salt)
        try:
            if rol == 'ADMINISTRADOR':
                usuario_id = UsuarioRepository.create_usuario(
                    nombre, apellido, rut, email, password_hash, salt, rol, area
                )
                usuario = UsuarioRepository.get_by_id(usuario_id)
            else:
                usuario_id = ClienteRepository.crear_cliente(
                    nombre, apellido, rut, email, telefono, password_hash, salt
                )
                usuario = ClienteRepository.obtener_por_id(usuario_id)
        except sqlite3.IntegrityError as exc:
            raise ValueError('El RUT o correo ya está registrado.') from exc
        return AutenticacionService._publicar_sesion(usuario, rol)

    @staticmethod
    def autenticar(email: str, password: str) -> dict:
        email = email.strip().lower()
        usuario = UsuarioRepository.get_by_email(email)
        repositorio = UsuarioRepository
        rol = 'ADMINISTRADOR'
        if usuario is None:
            usuario = ClienteRepository.obtener_por_email(email)
            repositorio = ClienteRepository
            rol = 'CLIENTE'
        if usuario is None:
            raise ValueError('Credenciales inválidas.')

        if int(usuario['activo']) == 0:
            raise PermissionError('La cuenta está inactiva.')

        bloqueado = usuario.get('bloqueado_hasta')
        if bloqueado:
            bloqueo_dt = datetime.fromisoformat(bloqueado)
            if datetime.now() < bloqueo_dt:
                raise PermissionError('La cuenta está bloqueada temporalmente.')
            repositorio.reset_fallos(email)

        salt = usuario['salt']
        password_hash = usuario['password_hash']
        if not verificar_password(password, salt, password_hash):
            intentos = int(usuario['intentos_fallidos']) + 1
            if intentos >= AutenticacionService.MAX_INTENTOS_FALLIDOS:
                bloqueado_hasta = bloquear_temporalmente(AutenticacionService.BLOQUEO_MINUTOS)
                repositorio.update_fallos(email, intentos, bloqueado_hasta)
                raise PermissionError('Cuenta bloqueada por demasiados intentos fallidos.')
            repositorio.update_fallos(email, intentos, None)
            raise ValueError('Credenciales inválidas.')

        repositorio.reset_fallos(email)
        return AutenticacionService._publicar_sesion(usuario, rol)

    @staticmethod
    def _publicar_sesion(usuario: dict | None, rol: str) -> dict:
        if usuario is None:
            raise ValueError('No se pudo recuperar la cuenta registrada.')
        return {
            'id': int(usuario['id']),
            'nombre': usuario['nombre'],
            'apellido': usuario['apellido'],
            'rol': rol,
            'area': usuario.get('area') if rol == 'ADMINISTRADOR' else None,
        }
