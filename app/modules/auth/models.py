"""Auth domain models: usuario, asignacion_rol, intento_acceso, evento_seguridad."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import CheckConstraint, DateTime, Index, text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.clientes.models import Cliente
    from app.modules.ordenes.models import (
        HistorialEstadoOrden,
        HistorialPrecioRepuesto,
        MovimientoStock,
        OrdenTrabajo,
    )


class Usuario(SQLModel, table=True):
    """Usuario del sistema; el email es unico y los roles viven en asignacion_rol."""

    __tablename__ = "usuario"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(nullable=False, unique=True)
    nombre: str = Field(nullable=False)
    password_hash: str = Field(nullable=False)
    activo: bool = Field(default=True, nullable=False)
    debe_cambiar_password: bool = Field(default=False, nullable=False)
    password_cambiada_en: Optional[datetime] = Field(
        sa_type=DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    cliente: Optional["Cliente"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"lazy": "raise", "uselist": False},
    )
    asignaciones_rol: List["AsignacionRol"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={
            "lazy": "raise",
            "foreign_keys": "[AsignacionRol.usuario_id]",
        },
    )
    roles_otorgados: List["AsignacionRol"] = Relationship(
        back_populates="otorgante",
        sa_relationship_kwargs={
            "lazy": "raise",
            "foreign_keys": "[AsignacionRol.otorgada_por]",
        },
    )
    ordenes_asignadas: List["OrdenTrabajo"] = Relationship(
        back_populates="mecanico",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    historiales_estado: List["HistorialEstadoOrden"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    movimientos_stock: List["MovimientoStock"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    historiales_precio: List["HistorialPrecioRepuesto"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"lazy": "raise"},
    )


class AsignacionRol(SQLModel, table=True):
    """Asignacion de un rol a un usuario, con vigencia y revocacion (RN-03)."""

    __tablename__ = "asignacion_rol"
    __table_args__ = (
        CheckConstraint(
            "rol IN ('ADMIN', 'RECEPCION', 'MECANICO', 'CLIENTE')",
            name="ck_asignacion_rol_rol_valido",
        ),
        Index(
            "ix_asignacion_rol_usuario_rol_uc",
            "usuario_id",
            "rol",
            unique=True,
            postgresql_where=text("revocada_en IS NULL"),
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", nullable=False, index=True)
    rol: str = Field(nullable=False)
    desde: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )
    vence_en: Optional[datetime] = Field(
        sa_type=DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    revocada_en: Optional[datetime] = Field(
        sa_type=DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    otorgada_por: Optional[int] = Field(
        default=None,
        foreign_key="usuario.id",
        nullable=True,
        index=True,
    )

    usuario: Optional[Usuario] = Relationship(
        back_populates="asignaciones_rol",
        sa_relationship_kwargs={
            "lazy": "raise",
            "foreign_keys": "[AsignacionRol.usuario_id]",
        },
    )
    otorgante: Optional[Usuario] = Relationship(
        back_populates="roles_otorgados",
        sa_relationship_kwargs={
            "lazy": "raise",
            "foreign_keys": "[AsignacionRol.otorgada_por]",
        },
    )


class IntentoAcceso(SQLModel, table=True):
    """Registro de intentos de login para el limite de intentos fallidos (RN-08)."""

    __tablename__ = "intento_acceso"
    __table_args__ = (
        Index("ix_intento_acceso_email_ip_cuando", "email", "ip", "cuando"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    cuando: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )
    email: str = Field(nullable=False)
    ip: str = Field(nullable=False)
    exito: bool = Field(nullable=False)


class EventoSeguridad(SQLModel, table=True):
    """Bitacora de eventos de seguridad (quien hizo que)."""

    __tablename__ = "evento_seguridad"

    id: Optional[int] = Field(default=None, primary_key=True)
    cuando: datetime = Field(
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": text("now()")},
    )
    actor: str = Field(nullable=False)
    accion: str = Field(nullable=False)
