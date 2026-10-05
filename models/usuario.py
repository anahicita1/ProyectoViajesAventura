from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Usuario(ABC):
    """Representa la base común para cualquier usuario del sistema."""

    id_usuario: int
    nombre: str
    apellido: str
    rut: str
    email: str
    password_hash: str
    rol: str = field(init=False)
    activo: bool = True
    intentos_fallidos: int = 0
    bloqueado_hasta: Optional[str] = None

    @abstractmethod
    def obtener_permisos(self) -> list[str]:
        """Devuelve los permisos asociados a cada tipo de usuario."""
        raise NotImplementedError


@dataclass
class Cliente(Usuario):
    rol: str = field(default='CLIENTE', init=False)
    telefono: str = ''

    def obtener_permisos(self) -> list[str]:
        return ['VER_CATALOGO', 'RESERVAR', 'VER_RESERVAS']


@dataclass
class Administrador(Usuario):
    rol: str = field(default='ADMINISTRADOR', init=False)

    def obtener_permisos(self) -> list[str]:
        return ['ADMINISTRAR_CATALOGO', 'GESTIONAR_USUARIOS', 'VER_REPORTES']
