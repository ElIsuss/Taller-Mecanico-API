"""Schemas de contrato para el módulo de autenticación.

Pydantic V2 con extra="forbid": ningún endpoint acepta campos no declarados.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, validator


class Login(BaseModel):
    """Login de usuario con email y password."""

    email: str = Field(..., description="Email del usuario")
    password: str = Field(..., description="Contraseña en texto plano")

    @validator("email")
    def email_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Email no puede estar vacío")
        return v.lower().strip()

    @validator("password")
    def password_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Password no puede estar vacío")
        if len(v) > 72:
            raise ValueError("Password muy largo: bcrypt límite 72 bytes")
        return v


class Register(BaseModel):
    """Registro atómico: usuario + rol CLIENTE + ficha cliente."""

    email: str = Field(..., description="Email del usuario")
    nombre: str = Field(..., description="Nombre completo")
    password: str = Field(..., description="Contraseña en texto plano")
    documento: str = Field(..., description="Documento de identidad")
    telefono: str = Field(..., description="Teléfono opcional")

    @validator("email")
    def email_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Email no puede estar vacío")
        return v.lower().strip()

    @validator("password")
    def password_no_vacio_y_longitud(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Password no puede estar vacío")
        if len(v) > 72:
            raise ValueError("Password muy largo: bcrypt límite 72 bytes")
        return v


class Me(BaseModel):
    """Respuesta del perfil del usuario autenticado (GET /auth/yo)."""

    id: int
    email: str
    nombre: str
    rol: Literal["ADMIN", "RECEPCION", "MECANICO", "CLIENTE"]
    iat: int  # issued at timestamp (sin truncar)


class TokenData(BaseModel):
    """Datos derivados del JWT (solo informativos)."""

    roles: list[str] = Field(default_factory=list)
    exp: int | None = None
    iat: int | None = None