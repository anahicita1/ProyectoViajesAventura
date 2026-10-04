from __future__ import annotations

from datetime import datetime, timedelta

from repositories.usuario_repository import UsuarioRepository
from utils.security import bloquear_temporalmente, generar_salt, hash_password, verificar_password


class AutenticacionService:
    """Servicio responsable de registro, autenticación y bloqueo de cuentas."""

    MAX_INTENTOS_FALLIDOS = 5
    BLOQUEO_MINUTOS = 15

    @staticmethod
    def registrar_usuario(nombre: str, apellido: str, rut: str, email: str, password: str, rol: str = 'CLIENTE') -> dict:
        email = email.strip().lower()
        if not nombre or not apellido or not rut or not email or not password:
            raise ValueError('Todos los campos son obligatorios.')

        if UsuarioRepository.get_by_email(email):
            raise ValueError('El correo ya existe en el sistema.')

        salt = generar_salt()
        password_hash = hash_password(password, salt)
        usuario_id = UsuarioRepository.create_usuario(nombre, apellido, rut, email, password_hash, salt, rol)
        return UsuarioRepository.get_by_id(usuario_id)

    @staticmethod
    def autenticar(email: str, password: str) -> dict:
        email = email.strip().lower()
        usuario = UsuarioRepository.get_by_email(email)
        if usuario is None:
            raise ValueError('Credenciales inválidas.')

        if int(usuario['activo']) == 0:
            raise PermissionError('La cuenta está inactiva.')

        bloqueado = usuario.get('bloqueado_hasta')
        if bloqueado:
            bloqueo_dt = datetime.fromisoformat(bloqueado)
            if datetime.now() < bloqueo_dt:
                raise PermissionError('La cuenta está bloqueada temporalmente.')
            UsuarioRepository.reset_fallos(email)

        salt = usuario['salt']
        password_hash = usuario['password_hash']
        if not verificar_password(password, salt, password_hash):
            intentos = int(usuario['intentos_fallidos']) + 1
            if intentos >= AutenticacionService.MAX_INTENTOS_FALLIDOS:
                bloqueado_hasta = bloquear_temporalmente(AutenticacionService.BLOQUEO_MINUTOS)
                UsuarioRepository.update_fallos(email, intentos, bloqueado_hasta)
                raise PermissionError('Cuenta bloqueada por demasiados intentos fallidos.')
            UsuarioRepository.update_fallos(email, intentos, None)
            raise ValueError('Credenciales inválidas.')

        UsuarioRepository.reset_fallos(email)
        return usuario
