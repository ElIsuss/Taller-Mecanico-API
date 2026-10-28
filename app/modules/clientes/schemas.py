"""Contratos de entrada y salida para clientes."""

from pydantic import BaseModel, ConfigDict, Field


class ClienteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: int | None = Field(default=None, gt=0)
    nombre: str = Field(min_length=1, max_length=200)
    documento: str = Field(min_length=1, max_length=50)
    telefono: str = Field(min_length=1, max_length=50)


class ClienteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: int | None = Field(default=None, gt=0)
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    documento: str | None = Field(default=None, min_length=1, max_length=50)
    telefono: str | None = Field(default=None, min_length=1, max_length=50)


class ClienteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int | None
    nombre: str
    documento: str
    telefono: str
