"""Utilidades de seguridad: bcrypt, JWT y cookies."""

import asyncio
from datetime import datetime, timezone
import threading
import time
from typing import Optional

import bcrypt
from fastapi import Response
import jwt as pyjwt

from app.core.config import settings

# Exported constants
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Semáforo de hilo para limitar operaciones concurrentes de bcrypt (evita saturar CPU/threadpool)
_BCRYPT_SEMAPHORE = threading.Semaphore(4)

# Hash dummy pre-generado para comparaciones en tiempo constante (RN-09)
_DUMMY_SALT = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
_DUMMY_HASH = bcrypt.hashpw(b"dummy_password_constant_time", _DUMMY_SALT).decode("utf-8")


def create_access_token(data: dict, expires_delta: int | None = None) -> str:
    """Genera un JWT access token con claims sub, iat, exp, roles."""
    to_encode = data.copy()
    now = time.time()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    to_encode.update({"exp": int(expire), "iat": now})
    encoded: str = pyjwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded


def decode_access_token(token: str) -> dict:
    """Decodifica y valida un JWT access token, retornando los claims."""
    return pyjwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )


def _hash_password_sync(password: str) -> str:
    """Hash síncrono con bcrypt protegido por semáforo y respetando settings.BCRYPT_ROUNDS."""
    with _BCRYPT_SEMAPHORE:
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            raise ValueError("Password excede límite de bcrypt (72 bytes)")
        salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
        return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


async def hash_password(password: str) -> str:
    """Hashea una contraseña usando bcrypt fuera del bucle de eventos (to_thread + semáforo)."""
    return await asyncio.to_thread(_hash_password_sync, password)


def _verify_password_sync(plain_password: str, hashed_password: str) -> bool:
    """Verificación síncrona con bcrypt protegida por semáforo."""
    with _BCRYPT_SEMAPHORE:
        password_bytes = plain_password.encode("utf-8")
        if len(password_bytes) > 72:
            return False
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash fuera del bucle de eventos."""
    return await asyncio.to_thread(_verify_password_sync, plain_password, hashed_password)


async def constant_time_verify(plain_password: str, hashed_password: str | None) -> bool:
    """Verificación en tiempo constante para evitar enumeración de usuarios (RN-09).
    
    Siempre ejecuta bcrypt.checkpw, aun si el usuario no existe (usando un hash ficticio).
    """
    target_hash = hashed_password if hashed_password is not None else _DUMMY_HASH
    is_valid = await verify_password(plain_password, target_hash)
    return is_valid and (hashed_password is not None)


def set_access_token_cookie(
    response: Response,
    token: str,
    max_age: int | None = None,
    secure: bool | None = None,
) -> None:
    """Establece la cookie HttpOnly con access_token JWT.
    
    - HttpOnly: no accesible desde JavaScript
    - SameSite=Lax: previene CSRF
    - Max-Age: segundos hasta expiración (default settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    - Secure: True en producción o si no está en modo DEBUG
    """
    if max_age is None:
        max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    if secure is None:
        secure = not settings.DEBUG

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=max_age,
        samesite="lax",
        secure=secure,
    )


def delete_access_token_cookie(response: Response) -> None:
    """Invalida la cookie access_token marcándola como expirada (Max-Age=0)."""
    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        max_age=0,
        expires=0,
        samesite="lax",
    )
