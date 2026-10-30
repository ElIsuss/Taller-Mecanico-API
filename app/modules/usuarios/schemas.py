"""Schemas de contrato para el módulo de autenticación y usuarios.

Pydantic V2 con extra="forbid": ningún endpoint acepta campos no declarados.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Login(BaseModel):
    """Login de usuario con email y password."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(..., description="Email del usuario")
    password: str = Field(..., description="Contraseña en texto plano")

    @field_validator("email")
    @classmethod
    def email_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Email no puede estar vacío")
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def password_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Password no puede estar vacío")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password muy largo: bcrypt límite 72 bytes")
        return v


class Register(BaseModel):
    """Registro atómico: usuario + rol CLIENTE + ficha cliente."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(..., description="Email del usuario")
    nombre: str = Field(..., description="Nombre completo")
    password: str = Field(..., description="Contraseña en texto plano")
    documento: str = Field(..., description="Documento de identidad")
    telefono: Optional[str] = Field(default="", description="Teléfono opcional")

    @field_validator("email")
    @classmethod
    def email_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Email no puede estar vacío")
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def password_no_vacio_y_longitud(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Password no puede estar vacío")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password muy largo: bcrypt límite 72 bytes")
        return v


class Me(BaseModel):
    """Respuesta del perfil del usuario autenticado (GET /auth/yo)."""

    model_config = ConfigDict(extra="forbid")

    id: int
    email: str
    nombre: str
    rol: Literal["ADMIN", "RECEPCION", "MECANICO", "CLIENTE"]
    iat: float | int


class TokenData(BaseModel):
    """Datos derivados del JWT (solo informativos)."""

    model_config = ConfigDict(extra="forbid")

    roles: list[str] = Field(default_factory=list)
    exp: Optional[int] = None
    iat: Optional[float | int] = None
