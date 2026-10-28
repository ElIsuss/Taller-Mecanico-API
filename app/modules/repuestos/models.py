"""Repuestos domain model: repuesto."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import CheckConstraint, DateTime, Index, Numeric, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.ordenes.models import (
        HistorialPrecioRepuesto,
        ItemOrden,
        MovimientoStock,
    )


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
