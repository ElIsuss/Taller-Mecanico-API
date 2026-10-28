"""Contratos de entrada y salida para repuestos."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RepuestoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str = Field(min_length=1, max_length=50)
    descripcion: str = Field(min_length=1, max_length=200)
    precio: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock: int = Field(default=0, ge=0)


class RepuestoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    descripcion: str | None = Field(default=None, min_length=1, max_length=200)
    precio: Decimal | None = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )
    usuario_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _precio_requiere_actor(self) -> "RepuestoUpdate":
        if "precio" in self.model_fields_set and self.usuario_id is None:
            raise ValueError("usuario_id es obligatorio al cambiar el precio")
        return self


class RepuestoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    descripcion: str
    precio: Decimal
    stock: int


class ReposicionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cantidad: int = Field(gt=0)
    motivo: str = Field(min_length=1, max_length=200)
    usuario_id: int = Field(gt=0)


class MovimientoStockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repuesto_id: int
    orden_id: int | None
    usuario_id: int
    cantidad: int
    motivo: str
    cuando: datetime


class HistorialPrecioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repuesto_id: int
    usuario_id: int
    precio_anterior: Decimal
    precio_nuevo: Decimal
    cuando: datetime
