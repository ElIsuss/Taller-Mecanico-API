"""Vehiculos domain model: vehiculo."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import CheckConstraint, DateTime, Index, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.clientes.models import Cliente
    from app.modules.ordenes.models import OrdenTrabajo


class Vehiculo(SQLModel, table=True):
    """Vehiculo de un cliente, con patente unica entre los vigentes (RN-01, RN-16)."""

    __tablename__ = "vehiculo"
    __table_args__ = (
        CheckConstraint("anio BETWEEN 1950 AND 2100", name="ck_vehiculo_anio"),
        Index(
            "ix_vehiculo_patente_uc",
            "patente",
            unique=True,
            postgresql_where=text("borrado_en IS NULL"),
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="cliente.id", nullable=False, index=True)
    patente: str = Field(nullable=False)
    marca: str = Field(nullable=False)
    modelo: str = Field(nullable=False)
    anio: int = Field(nullable=False)
    borrado_en: Optional[datetime] = Field(
        sa_type=DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    cliente: Optional["Cliente"] = Relationship(
        back_populates="vehiculos",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    ordenes: List["OrdenTrabajo"] = Relationship(
        back_populates="vehiculo",
        sa_relationship_kwargs={"lazy": "raise"},
    )
