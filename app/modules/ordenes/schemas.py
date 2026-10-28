"""Contratos de entrada y salida para el catálogo de estados y las órdenes."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EstadoOrdenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    descripcion: str
    posicion: int
    es_final: bool


class ItemOrdenCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repuesto_id: int = Field(gt=0)
    cantidad: int = Field(gt=0)


class OrdenCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehiculo_id: int = Field(gt=0)
    mecanico_id: int | None = Field(default=None, gt=0)
    falla: str = Field(min_length=1, max_length=500)
    usuario_id: int = Field(gt=0)
    items: list[ItemOrdenCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def _sin_repuestos_repetidos(self) -> "OrdenCreate":
        repuesto_ids = [item.repuesto_id for item in self.items]
        if len(repuesto_ids) != len(set(repuesto_ids)):
            raise ValueError("No se puede repetir un repuesto en la misma orden")
        return self


class OrdenUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    falla: str | None = Field(default=None, min_length=1, max_length=500)
    mecanico_id: int | None = Field(default=None, gt=0)


class OrdenAccion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: int = Field(gt=0)


class ItemOrdenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repuesto_id: int
    cantidad: int
    precio_unitario: Decimal


class OrdenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehiculo_id: int
    mecanico_id: int | None
    estado: str
    falla: str
    creada_en: datetime
    total: Decimal
    items: list[ItemOrdenRead]
