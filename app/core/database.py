from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from app.core.config import settings
from app.core.unit_of_work import UnitOfWork

# Metadata de SQLModel expuesto hacia Alembic (autogenerate).
# Los modelos deben importarse (p.ej. desde migrations/env.py) para que
# SQLModel.metadata quede poblado con todas las tablas del proyecto.
SQLModel_metadata = SQLModel.metadata


def create_engine_and_session_maker():
    """Create engine and session maker - called from lifespan."""
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=settings.SQL_ECHO,
        future=True,
        pool_pre_ping=True,
        pool_size=settings.POOL_SIZE,
    )
    async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    return engine, async_session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get session from app.state (set in lifespan)."""
    from app.main import app
    async with app.state.async_session_maker() as session:
        yield session


async def get_uow() -> UnitOfWork:
    """Create a UnitOfWork that owns its own async session."""
    from app.main import app
    return UnitOfWork(session_factory=app.state.async_session_maker)