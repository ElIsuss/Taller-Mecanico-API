"""Clientes domain model: cliente."""

from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.auth.models import Usuario
    from app.modules.vehiculos.models import Vehiculo


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
