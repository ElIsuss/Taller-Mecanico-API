"""Clientes domain model: cliente."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, text
from sqlmodel import Field, SQLModel


class Cliente(SQLModel, table=True):
    """Ficha de cliente con documento unico entre vigentes y borrado logico."""

    __tablename__ = "cliente"
    __table_args__ = (
        Index(
            "ix_cliente_documento_uc",
            "documento",
            unique=True,
            postgresql_where=text("fecha_baja IS NULL"),
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    documento: str = Field(index=True, nullable=False)
    nombre: str = Field(nullable=False)
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
