"""Ordenes domain models: estado_orden, orden_trabajo, item_orden,
historial_estado_orden."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Numeric,
    UniqueConstraint,
    text,
)
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.clientes.models import Vehiculo
    from app.modules.repuestos.models import MovimientoStock, Repuesto
    from app.modules.usuarios.models import Usuario


class EstadoOrden(SQLModel, table=True):
    """Catalogo de estados de orden; la PK es el codigo legible (RN-19)."""

    __tablename__ = "estado_orden"

    codigo: str = Field(primary_key=True)
    descripcion: str = Field(nullable=False)
    posicion: int = Field(nullable=False, unique=True)
    es_final: bool = Field(default=False, nullable=False)

    ordenes: List["OrdenTrabajo"] = Relationship(
        back_populates="estado_actual",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    historiales_desde: List["HistorialEstadoOrden"] = Relationship(
        back_populates="desde_estado_rel",
        sa_relationship_kwargs={
            "lazy": "raise",
            "foreign_keys": "[HistorialEstadoOrden.desde_estado]",
        },
    )
    historiales_hasta: List["HistorialEstadoOrden"] = Relationship(
        back_populates="hasta_estado_rel",
        sa_relationship_kwargs={
            "lazy": "raise",
            "foreign_keys": "[HistorialEstadoOrden.hasta_estado]",
        },
    )


class OrdenTrabajo(SQLModel, table=True):
    """Orden de trabajo de un vehiculo, con mecanico opcional y total calculado."""

    __tablename__ = "orden_trabajo"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_orden_trabajo_total_no_negativo"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    vehiculo_id: int = Field(foreign_key="vehiculo.id", nullable=False, index=True)
    mecanico_id: Optional[int] = Field(
        default=None,
        foreign_key="usuario.id",
        nullable=True,
        index=True,
    )
    estado: str = Field(foreign_key="estado_orden.codigo", nullable=False, index=True)
    falla: str = Field(nullable=False)
    creada_en: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )
    total: Decimal = Field(
        sa_type=Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )

    vehiculo: Optional["Vehiculo"] = Relationship(
        back_populates="ordenes",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    mecanico: Optional["Usuario"] = Relationship(
        back_populates="ordenes_asignadas",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    estado_actual: Optional["EstadoOrden"] = Relationship(
        back_populates="ordenes",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    items: List["ItemOrden"] = Relationship(
        back_populates="orden",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    historial_estados: List["HistorialEstadoOrden"] = Relationship(
        back_populates="orden",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    movimientos_stock: List["MovimientoStock"] = Relationship(
        back_populates="orden",
        sa_relationship_kwargs={"lazy": "raise"},
    )


class ItemOrden(SQLModel, table=True):
    """Item de repuesto de una orden; el precio se copia del repuesto (RN-10)."""

    __tablename__ = "item_orden"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_item_orden_cantidad_positiva"),
        CheckConstraint(
            "precio_unitario > 0",
            name="ck_item_orden_precio_unitario_positivo",
        ),
        UniqueConstraint(
            "orden_id",
            "repuesto_id",
            name="uq_item_orden_orden_repuesto",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    orden_id: int = Field(foreign_key="orden_trabajo.id", nullable=False, index=True)
    repuesto_id: int = Field(foreign_key="repuesto.id", nullable=False, index=True)
    cantidad: int = Field(nullable=False)
    precio_unitario: Decimal = Field(sa_type=Numeric(10, 2), nullable=False)

    orden: Optional["OrdenTrabajo"] = Relationship(
        back_populates="items",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    repuesto: Optional["Repuesto"] = Relationship(
        back_populates="items_orden",
        sa_relationship_kwargs={"lazy": "raise"},
    )


class HistorialEstadoOrden(SQLModel, table=True):
    """Historial de cambios de estado (solo agregado, RN-15)."""

    __tablename__ = "historial_estado_orden"

    id: Optional[int] = Field(default=None, primary_key=True)
    orden_id: int = Field(foreign_key="orden_trabajo.id", nullable=False, index=True)
    desde_estado: Optional[str] = Field(
        default=None,
        foreign_key="estado_orden.codigo",
        nullable=True,
        index=True,
    )
    hasta_estado: str = Field(
        foreign_key="estado_orden.codigo",
        nullable=False,
        index=True,
    )
    usuario_id: int = Field(foreign_key="usuario.id", nullable=False, index=True)
    cuando: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )

    orden: Optional["OrdenTrabajo"] = Relationship(
        back_populates="historial_estados",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    desde_estado_rel: Optional["EstadoOrden"] = Relationship(
        back_populates="historiales_desde",
        sa_relationship_kwargs={
            "lazy": "raise",
            "foreign_keys": "[HistorialEstadoOrden.desde_estado]",
        },
    )
    hasta_estado_rel: Optional["EstadoOrden"] = Relationship(
        back_populates="historiales_hasta",
        sa_relationship_kwargs={
            "lazy": "raise",
            "foreign_keys": "[HistorialEstadoOrden.hasta_estado]",
        },
    )
    usuario: Optional["Usuario"] = Relationship(
        back_populates="historiales_estado",
        sa_relationship_kwargs={"lazy": "raise"},
    )
