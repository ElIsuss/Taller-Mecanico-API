"""Ordenes domain models: estado_orden, orden_trabajo, orden_item,
historial_estado_orden, movimiento_stock, historial_precio_repuesto."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, text
from sqlmodel import Field, SQLModel


class EstadoOrden(SQLModel, table=True):
    """Catalogo de estados de orden: PENDIENTE, EN_REPARACION, TERMINADA, CANCELADA."""

    __tablename__ = "estado_orden"
    __table_args__ = (
        Index("ix_estado_orden_nombre_uc", "nombre", unique=True),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True, unique=True, nullable=False)
    fecha_alta: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )
    fecha_baja: Optional[datetime] = Field(
        sa_type=DateTime(timezone=True),
        nullable=True,
        default=None,
    )


class OrdenTrabajo(SQLModel, table=True):
    """Orden de trabajo vinculada a cliente, vehiculo y estado; mecanico asignado es cualquier usuario."""

    __tablename__ = "orden_trabajo"

    id: Optional[int] = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="cliente.id", nullable=False)
    vehiculo_id: int = Field(foreign_key="vehiculo.id", nullable=False)
    mecanico_asignado_id: Optional[int] = Field(
        default=None, foreign_key="usuario.id", nullable=True
    )
    estado_id: int = Field(foreign_key="estado_orden.id", nullable=False)
    fecha_alta: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )
    fecha_baja: Optional[datetime] = Field(
        sa_type=DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    __table_args__ = (
        Index("ix_orden_trabajo_estado_id", "estado_id"),
        Index("ix_orden_trabajo_cliente_id", "cliente_id"),
        Index("ix_orden_trabajo_vehiculo_id", "vehiculo_id"),
        Index("ix_orden_trabajo_mecanico_asignado_id", "mecanico_asignado_id"),
    )


class OrdenItem(SQLModel, table=True):
    """Item de repuesto de una orden de trabajo."""

    __tablename__ = "orden_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    orden_trabajo_id: int = Field(foreign_key="orden_trabajo.id", nullable=False)
    repuesto_id: int = Field(foreign_key="repuesto.id", nullable=False)
    cantidad: int = Field(nullable=False)
    precio_unitario: float = Field(nullable=False)
    fecha_alta: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )
    fecha_baja: Optional[datetime] = Field(
        sa_type=DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    __table_args__ = (
        Index("ix_orden_item_orden_trabajo_id", "orden_trabajo_id"),
        Index("ix_orden_item_repuesto_id", "repuesto_id"),
    )


class HistorialEstadoOrden(SQLModel, table=True):
    """Historial de cambios de estado de una orden (solo agregado, protegido por trigger RN-15)."""

    __tablename__ = "historial_estado_orden"

    id: Optional[int] = Field(default=None, primary_key=True)
    orden_trabajo_id: int = Field(foreign_key="orden_trabajo.id", nullable=False)
    estado_id: int = Field(foreign_key="estado_orden.id", nullable=False)
    fecha_cambio: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )
    fecha_alta: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )

    __table_args__ = (
        Index("ix_historial_estado_orden_orden_id", "orden_trabajo_id"),
        Index("ix_historial_estado_orden_estado_id", "estado_id"),
    )


class MovimientoStock(SQLModel, table=True):
    """Movimiento de stock de un repuesto (alta, reposicion, terminacion)."""

    __tablename__ = "movimiento_stock"

    id: Optional[int] = Field(default=None, primary_key=True)
    repuesto_id: int = Field(foreign_key="repuesto.id", nullable=False)
    tipo: str = Field(nullable=False)  # alta | reposicion | terminacion
    cantidad: int = Field(nullable=False)
    fecha_alta: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )

    __table_args__ = (
        Index("ix_movimiento_stock_repuesto_id", "repuesto_id"),
    )


class HistorialPrecioRepuesto(SQLModel, table=True):
    """Historial de cambios de precio de un repuesto (solo agregado, protegido por trigger RN-15)."""

    __tablename__ = "historial_precio_repuesto"

    id: Optional[int] = Field(default=None, primary_key=True)
    repuesto_id: int = Field(foreign_key="repuesto.id", nullable=False)
    precio_anterior: float = Field(nullable=False)
    precio_nuevo: float = Field(nullable=False)
    fecha_cambio: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )
    fecha_alta: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )

    __table_args__ = (
        Index("ix_historial_precio_repuesto_repuesto_id", "repuesto_id"),
    )
