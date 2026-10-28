"""Vehiculos domain model: vehiculo."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, text
from sqlmodel import Field, SQLModel


class Vehiculo(SQLModel, table=True):
    """Vehiculo vinculado a un cliente con patente unica entre vigentes."""

    __tablename__ = "vehiculo"
    __table_args__ = (
        Index(
            "ix_vehiculo_patente_uc",
            "patente",
            unique=True,
            postgresql_where=text("fecha_baja IS NULL"),
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    patente: str = Field(index=True, nullable=False)
    cliente_id: int = Field(foreign_key="cliente.id", nullable=False)
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
