"""Repuestos domain model: repuesto."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, text
from sqlmodel import Field, SQLModel


class Repuesto(SQLModel, table=True):
    """Catalogo de repuestos con codigo unico entre vigentes."""

    __tablename__ = "repuesto"
    __table_args__ = (
        Index(
            "ix_repuesto_codigo_uc",
            "codigo",
            unique=True,
            postgresql_where=text("fecha_baja IS NULL"),
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(index=True, nullable=False)
    nombre: str = Field(nullable=False)
    precio: float = Field(nullable=False)
    stock: int = Field(nullable=False, default=0)
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
