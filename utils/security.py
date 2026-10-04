import hashlib
import hmac
import secrets
from datetime import datetime


def generar_salt() -> str:
    return secrets.token_hex(16)


def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 600000).hex()


def verificar_password(password: str, salt: str, password_hash: str) -> bool:
    computed = hash_password(password, salt)
    return hmac.compare_digest(computed, password_hash)


def bloquear_temporalmente(minutos: int = 15) -> str:
    from datetime import timedelta

    return (datetime.now() + timedelta(minutes=minutos)).isoformat(timespec='seconds')
