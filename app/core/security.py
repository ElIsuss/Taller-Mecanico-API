# Security utilities
import bcrypt
import time
import jwt as pyjwt
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import asyncio
from fastapi import Response
import json

from app.core.config import settings


# Exported constants for router and other modules
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


# Semaphore to limit concurrent bcrypt operations (prevents event loop blocking)
_BCRYPT_SEMAPHORE = asyncio.Semaphore(4)
_BCRYPT_EXECUTOR = ThreadPoolExecutor(max_workers=4)


def create_access_token(data: dict, expires_delta: int | None = None) -> str:
    """Genera un JWT access token con claims sub, iat, exp, roles."""
    to_encode = data.copy()
    now = int(time.time())
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    to_encode.update({"exp": expire, "iat": now})
    encoded: str = pyjwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded


def decode_access_token(token: str) -> dict:
    """Decodifica y valida un JWT access token, retornando los claims."""
    return pyjwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )


async def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    Runs in a thread pool to avoid blocking the event loop.
    """
    loop = asyncio.get_running_loop()
    async with _BCRYPT_SEMAPHORE:
        return await loop.run_in_executor(
            _BCRYPT_EXECUTOR,
            partial(_hash_password_sync, password)
        )


def _hash_password_sync(password: str) -> str:
    """Synchronous bcrypt hash (runs in thread pool)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    Runs in a thread pool to avoid blocking the event loop.
    Placeholder for RN-09: responds the same whether the email exists or not.
    """
    loop = asyncio.get_running_loop()
    async with _BCRYPT_SEMAPHORE:
        return await loop.run_in_executor(
            _BCRYPT_EXECUTOR,
            partial(_verify_password_sync, plain_password, hashed_password)
        )


def _verify_password_sync(plain_password: str, hashed_password: str) -> bool:
    """Synchronous bcrypt verify (runs in thread pool)."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


async def constant_time_verify(plain_password: str, hashed_password: str | None) -> bool:
    """
    Constant-time password verification to prevent user enumeration (RN-09).
    Always performs a bcrypt check even if the user doesn't exist.
    """
    if hashed_password is None:
        # Use a dummy hash to ensure constant time
        dummy_hash = bcrypt.hashpw(b"dummy", bcrypt.gensalt(12))
        await verify_password(plain_password, dummy_hash.decode("utf-8"))
        return False
    return await verify_password(plain_password, hashed_password)


# Cookie utilities for JWT access_token
def set_access_token_cookie(response: Response, token: str, max_age: int = 1800, secure: bool | None = None) -> None:
    """Establecer cookie HttpOnly con access_token JWT.

    - HttpOnly: no accesible desde JavaScript del navegador
    - SameSite=Lax: previene CSRF en navegación normal
    - Max-Age: segundos hasta expiración
    - Secure: solo en producción (HTTPS)
    """
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=max_age,
        same_site="lax",
        secure=secure,
    )


def delete_access_token_cookie(response: Response) -> None:
    """Borrar cookie access_token marcándola como expirada."""

    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        max_age=0,
        expires=0,
        same_site="lax",
    )