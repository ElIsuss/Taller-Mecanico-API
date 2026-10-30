"""Repuestos domain models: repuesto, movimiento_stock, historial_precio_repuesto."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import CheckConstraint, DateTime, Index, Numeric, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.ordenes.models import ItemOrden, OrdenTrabajo
    from app.modules.usuarios.models import Usuario


class Repuesto(SQLModel, table=True):
    """Catalogo de repuestos, con codigo unico entre vigentes y dinero como Decimal."""

    __tablename__ = "repuesto"
    __table_args__ = (
        CheckConstraint("precio > 0", name="ck_repuesto_precio_positivo"),
        CheckConstraint("stock >= 0", name="ck_repuesto_stock_no_negativo"),
        Index(
            "ix_repuesto_codigo_uc",
            "codigo",
            unique=True,
            postgresql_where=text("borrado_en IS NULL"),
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(nullable=False)
    descripcion: str = Field(nullable=False)
    precio: Decimal = Field(sa_type=Numeric(10, 2), nullable=False)
    stock: int = Field(default=0, nullable=False)
    borrado_en: Optional[datetime] = Field(
        sa_type=DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    items_orden: List["ItemOrden"] = Relationship(
        back_populates="repuesto",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    movimientos_stock: List["MovimientoStock"] = Relationship(
        back_populates="repuesto",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    historiales_precio: List["HistorialPrecioRepuesto"] = Relationship(
        back_populates="repuesto",
        sa_relationship_kwargs={"lazy": "raise"},
    )


class MovimientoStock(SQLModel, table=True):
    """Movimiento de stock (solo agregado, RN-14 y RN-15)."""

    __tablename__ = "movimiento_stock"
    __table_args__ = (
        CheckConstraint("cantidad <> 0", name="ck_movimiento_stock_cantidad_no_cero"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    repuesto_id: int = Field(foreign_key="repuesto.id", nullable=False, index=True)
    orden_id: Optional[int] = Field(
        default=None,
        foreign_key="orden_trabajo.id",
        nullable=True,
        index=True,
    )
    usuario_id: int = Field(foreign_key="usuario.id", nullable=False, index=True)
    cantidad: int = Field(nullable=False)
    motivo: str = Field(nullable=False)
    cuando: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )

    repuesto: Optional["Repuesto"] = Relationship(
        back_populates="movimientos_stock",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    orden: Optional["OrdenTrabajo"] = Relationship(
        back_populates="movimientos_stock",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    usuario: Optional["Usuario"] = Relationship(
        back_populates="movimientos_stock",
        sa_relationship_kwargs={"lazy": "raise"},
    )


class HistorialPrecioRepuesto(SQLModel, table=True):
    """Historial de cambios de precio (solo agregado, RN-15 y RN-20)."""

    __tablename__ = "historial_precio_repuesto"
    __table_args__ = (
        CheckConstraint(
            "precio_nuevo > 0",
            name="ck_historial_precio_nuevo_positivo",
        ),
        CheckConstraint(
            "precio_nuevo <> precio_anterior",
            name="ck_historial_precio_cambio",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    repuesto_id: int = Field(foreign_key="repuesto.id", nullable=False, index=True)
    usuario_id: int = Field(foreign_key="usuario.id", nullable=False, index=True)
    precio_anterior: Decimal = Field(sa_type=Numeric(10, 2), nullable=False)
    precio_nuevo: Decimal = Field(sa_type=Numeric(10, 2), nullable=False)
    cuando: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )

    repuesto: Optional["Repuesto"] = Relationship(
        back_populates="historiales_precio",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    usuario: Optional["Usuario"] = Relationship(
        back_populates="historiales_precio",
        sa_relationship_kwargs={"lazy": "raise"},
    )
