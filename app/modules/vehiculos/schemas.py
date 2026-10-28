"""Contratos de entrada y salida para vehículos."""

from pydantic import BaseModel, ConfigDict, Field


class VehiculoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cliente_id: int = Field(gt=0)
    patente: str = Field(min_length=1, max_length=20)
    marca: str = Field(min_length=1, max_length=100)
    modelo: str = Field(min_length=1, max_length=100)
    anio: int = Field(ge=1950, le=2100)


class VehiculoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cliente_id: int | None = Field(default=None, gt=0)
    patente: str | None = Field(default=None, min_length=1, max_length=20)
    marca: str | None = Field(default=None, min_length=1, max_length=100)
    modelo: str | None = Field(default=None, min_length=1, max_length=100)
    anio: int | None = Field(default=None, ge=1950, le=2100)


class VehiculoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    patente: str
    marca: str
    modelo: str
    anio: int
