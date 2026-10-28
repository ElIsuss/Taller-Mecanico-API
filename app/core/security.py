# Security utilities
import bcrypt
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import asyncio


# Semaphore to limit concurrent bcrypt operations (prevents event loop blocking)
_BCRYPT_SEMAPHORE = asyncio.Semaphore(4)
_BCRYPT_EXECUTOR = ThreadPoolExecutor(max_workers=4)


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