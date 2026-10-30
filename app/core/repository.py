"""Generic repository abstractions for the domain layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    """Thin repository that encapsulates session access and basic CRUD."""

    model: type[T]

    def __init__(self, session: AsyncSession | None, model: type[T] | None = None) -> None:
        self.session = session
        self.model = model or self.model

    def _require_session(self) -> AsyncSession:
        if self.session is None:
            raise RuntimeError("Repository session is not available. Use it inside a UnitOfWork context.")
        return self.session

    async def add(self, instance: T) -> T:
        session = self._require_session()
        session.add(instance)
        return instance

    async def save(self, instance: T) -> T:
        session = self._require_session()
        session.add(instance)
        await session.flush()
        return instance

    async def get_by_id(self, primary_key: Any) -> T | None:
        session = self._require_session()
        return await session.get(self.model, primary_key)

    async def get_one(self, *conditions: Any) -> T | None:
        session = self._require_session()
        stmt = select(self.model).where(*conditions)
        return (await session.execute(stmt)).scalar_one_or_none()

    async def list(self, *conditions: Any, order_by: Any | None = None) -> list[T]:
        session = self._require_session()
        stmt: Select = select(self.model).where(*conditions)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def remove(self, instance: T) -> None:
        session = self._require_session()
        await session.delete(instance)
        await session.flush()

    async def flush(self) -> None:
        session = self._require_session()
        await session.flush()


class SoftDeleteRepository(BaseRepository[T]):
    """Repository that hides soft-deleted rows by default."""

    deleted_field = "borrado_en"

    async def get_active_by_id(self, primary_key: Any) -> T | None:
        session = self._require_session()
        stmt = select(self.model).where(
            getattr(self.model, self.deleted_field).is_(None),
            getattr(self.model, "id") == primary_key,
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    async def list_active(self, *conditions: Any, order_by: Any | None = None) -> list[T]:
        session = self._require_session()
        stmt: Select = select(self.model).where(
            getattr(self.model, self.deleted_field).is_(None),
            *conditions,
        )
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete(self, instance: T) -> T:
        session = self._require_session()
        if hasattr(instance, self.deleted_field):
            setattr(instance, self.deleted_field, datetime.now(timezone.utc))
        else:
            raise AttributeError(
                f"{self.model.__name__} does not support soft delete"
            )
        await session.flush()
        return instance
