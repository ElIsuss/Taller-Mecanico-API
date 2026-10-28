"""Contratos de entrada y salida para el catálogo de estados y las órdenes."""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EstadoOrdenCodigo(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_REPARACION = "EN_REPARACION"
    TERMINADA = "TERMINADA"
    CANCELADA = "CANCELADA"


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
    falla: str = Field(min_length=1, max_length=500)
    items: list[ItemOrdenCreate] = Field(min_length=1)
    usuario_id: int | None = Field(default=None, gt=0)

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
    repuesto_id: int
    codigo: str
    descripcion: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class HistorialEstadoOrdenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    desde_estado: str | None
    hasta_estado: str
    usuario_id: int
    cuando: datetime


class OrdenRead(BaseModel):
    id: int
    estado: str
    patente: str
    total: Decimal
    creada_en: datetime
    mecanico_id: int | None
    falla: str
    cliente: str
    items: list[ItemOrdenRead]
    historial: list[HistorialEstadoOrdenRead]
