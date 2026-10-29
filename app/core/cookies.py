"""Cookie utilities for JWT access_token."""

from fastapi import Response


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