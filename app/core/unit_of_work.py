"""Unit of Work pattern implementation for async SQLAlchemy sessions."""

from __future__ import annotations

from collections.abc import AsyncIterator
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class UnitOfWork:
    """Transactional boundary that owns a session and commits on success."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.session = session
        self._owns_session = session is None and session_factory is not None
        self._repositories: list[object] = []
        self._bind_repositories()

    def _register_repository(self, repository: object) -> object:
        self._repositories.append(repository)
        repository.session = self.session
        return repository

    def _bind_repositories(self) -> None:
        for repository in self._repositories:
            repository.session = self.session

    async def __aenter__(self) -> "UnitOfWork":
        if self.session is None and self.session_factory is not None:
            self.session = self.session_factory()
            await self.session.__aenter__()
            self._owns_session = True
        self._bind_repositories()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is None:
                await self.commit()
            else:
                await self.rollback()
        finally:
            if self.session is not None and self._owns_session:
                await self.session.__aexit__(exc_type, exc, tb)
                self.session = None
                self._bind_repositories()

    async def commit(self) -> None:
        if self.session is not None:
            await self.session.commit()

    async def rollback(self) -> None:
        if self.session is not None:
            await self.session.rollback()

    async def flush(self) -> None:
        if self.session is not None:
            await self.session.flush()

    async def close(self) -> None:
        if self.session is not None and self._owns_session:
            await self.session.close()
            self.session = None
            self._bind_repositories()

    async def begin(self) -> AsyncIterator["UnitOfWork"]:
        async with self:
            yield self
