"""Auth domain models: usuario, rol, rol_asignacion."""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import DateTime, ForeignKey, Index, text, column
from sqlmodel import Field, Relationship, SQLModel


class Rol(SQLModel, table=True):
    """Catalogo de roles del sistema: RECEPCION, MECANICO, ADMIN, CLIENTE."""

    __tablename__ = "rol"
    __table_args__ = (
        Index("ix_rol_nombre_uc", "nombre", unique=True),
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

    rol_asignaciones: List["RolAsignacion"] = Relationship(
        back_populates="rol",
        sa_relationship_kwargs={"lazy": "raise"},
    )


class Usuario(SQLModel, table=True):
    """Usuario del sistema con email unico entre vigentes y opcional ficha de cliente."""

    __tablename__ = "usuario"
    __table_args__ = (
        Index("ix_usuario_email_uc", "email", unique=True, postgresql_where=text("fecha_baja IS NULL")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, nullable=False)
    password_hash: str = Field(nullable=False)
    password_cambiada_en: Optional[datetime] = Field(
        sa_type=DateTime(timezone=True),
        nullable=True,
        default=None,
    )
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
    cliente_id: Optional[int] = Field(
        default=None,
        foreign_key="cliente.id",
        nullable=True,
        unique=True,
    )

    rol_asignaciones: List["RolAsignacion"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"lazy": "raise"},
    )


class RolAsignacion(SQLModel, table=True):
    """Asignacion de rol a usuario con vigencia (fecha_desde / fecha_hasta)."""

    __tablename__ = "rol_asignacion"
    __table_args__ = (
        Index(
            "ix_rol_asignacion_usuario_rol_abierta_uc",
            "usuario_id",
            "rol_id",
            unique=True,
            postgresql_where=text("fecha_hasta IS NULL"),
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", nullable=False)
    rol_id: int = Field(foreign_key="rol.id", nullable=False)
    fecha_desde: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )
    fecha_hasta: Optional[datetime] = Field(
        sa_type=DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    fecha_alta: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )

    usuario: Optional[Usuario] = Relationship(back_populates="rol_asignaciones", sa_relationship_kwargs={"lazy": "raise"})
    rol: Optional[Rol] = Relationship(back_populates="rol_asignaciones", sa_relationship_kwargs={"lazy": "raise"})
