"""User-domain repository definitions."""

from datetime import datetime

from sqlalchemy import func, or_, select

from app.core.repository import BaseRepository
from app.modules.usuarios.models import (
    AsignacionRol,
    EventoSeguridad,
    IntentoAcceso,
    Usuario,
)


class UsuarioRepository(BaseRepository[Usuario]):
    model = Usuario

    async def get_by_email(self, email: str) -> Usuario | None:
        return await self.get_one(Usuario.email == email)


class AsignacionRolRepository(BaseRepository[AsignacionRol]):
    model = AsignacionRol

    async def list_active_for_user(self, usuario_id: int) -> list[AsignacionRol]:
        session = self._require_session()
        stmt = (
            select(AsignacionRol)
            .where(AsignacionRol.usuario_id == usuario_id)
            .where(AsignacionRol.revocada_en.is_(None))
            .where(
                or_(
                    AsignacionRol.vence_en.is_(None),
                    AsignacionRol.vence_en > func.now(),
                )
            )
        )
        return list(await session.scalars(stmt))

    async def get_active_assignment(
        self, usuario_id: int, rol: str
    ) -> AsignacionRol | None:
        session = self._require_session()
        stmt = (
            select(AsignacionRol)
            .where(AsignacionRol.usuario_id == usuario_id)
            .where(AsignacionRol.rol == rol)
            .where(AsignacionRol.revocada_en.is_(None))
            .where(
                or_(
                    AsignacionRol.vence_en.is_(None),
                    AsignacionRol.vence_en > func.now(),
                )
            )
        )
        return await session.scalar(stmt)

    async def count_active_admins(self) -> int:
        session = self._require_session()
        result = await session.scalar(
            select(func.count())
            .select_from(AsignacionRol)
            .where(AsignacionRol.rol == "ADMIN")
            .where(AsignacionRol.revocada_en.is_(None))
            .where(
                or_(
                    AsignacionRol.vence_en.is_(None),
                    AsignacionRol.vence_en > func.now(),
                )
            )
        )
        return int(result or 0)


class EventoSeguridadRepository(BaseRepository[EventoSeguridad]):
    model = EventoSeguridad

    async def list_recent(self) -> list[EventoSeguridad]:
        return await self.list(order_by=EventoSeguridad.cuando.desc())


class IntentoAccesoRepository(BaseRepository[IntentoAcceso]):
    model = IntentoAcceso

    async def latest_success(self, email: str, ip: str) -> datetime | None:
        session = self._require_session()
        stmt = (
            select(func.max(IntentoAcceso.cuando))
            .where(IntentoAcceso.email == email)
            .where(IntentoAcceso.ip == ip)
            .where(IntentoAcceso.exito.is_(True))
        )
        return await session.scalar(stmt)

    async def count_recent_failures(
        self,
        email: str,
        ip: str,
        since: datetime,
        after: datetime | None = None,
    ) -> int:
        session = self._require_session()
        stmt = (
            select(func.count(IntentoAcceso.id))
            .where(IntentoAcceso.email == email)
            .where(IntentoAcceso.ip == ip)
            .where(IntentoAcceso.exito.is_(False))
            .where(IntentoAcceso.cuando >= since)
        )
        if after is not None:
            stmt = stmt.where(IntentoAcceso.cuando > after)
        result = await session.scalar(stmt)
        return int(result or 0)


__all__ = [
    "AsignacionRolRepository",
    "EventoSeguridadRepository",
    "IntentoAccesoRepository",
    "UsuarioRepository",
]
