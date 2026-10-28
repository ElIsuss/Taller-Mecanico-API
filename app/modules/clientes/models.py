"""Clientes domain models: cliente y vehiculo."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import CheckConstraint, DateTime, Index, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.ordenes.models import OrdenTrabajo
    from app.modules.usuarios.models import Usuario


class Cliente(SQLModel, table=True):
    """Ficha de cliente; puede estar vinculada a un usuario (1:1) y tener vehiculos."""

    __tablename__ = "cliente"

    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: Optional[int] = Field(
        default=None,
        foreign_key="usuario.id",
        nullable=True,
        unique=True,
    )
    nombre: str = Field(nullable=False)
    documento: str = Field(nullable=False, unique=True)
    telefono: str = Field(nullable=False)

    usuario: Optional["Usuario"] = Relationship(
        back_populates="cliente",
        sa_relationship_kwargs={"lazy": "raise", "uselist": False},
    )
    vehiculos: List["Vehiculo"] = Relationship(
        back_populates="cliente",
        sa_relationship_kwargs={"lazy": "raise"},
    )


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
