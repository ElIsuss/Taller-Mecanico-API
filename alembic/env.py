from logging.config import fileConfig

from sqlalchemy import pool
from alembic import context
from sqlmodel import SQLModel

# Import every model module so that SQLModel.metadata is fully populated
# before Alembic inspects it (autogenerate + online migrations).
from app.modules.auth.models import *  # noqa: F401,F403
from app.modules.clientes.models import *  # noqa: F401,F403
from app.modules.vehiculos.models import *  # noqa: F401,F403
from app.modules.repuestos.models import *  # noqa: F401,F403
from app.modules.ordenes.models import *  # noqa: F401,F403
from app.modules.roles.models import *  # noqa: F401,F403

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def _get_url() -> str:
    """Resolve the database URL from settings, honoring DATABASE_URL env override."""
    from app.core.config import settings

    return settings.SQLALCHEMY_DATABASE_URI


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    from sqlalchemy.ext.asyncio import create_async_engine

    url = _get_url()
    connectable = create_async_engine(url, poolclass=pool.NullPool, future=True)

    async def run_async_migrations() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_migrations)

    import asyncio

    asyncio.run(run_async_migrations())


def do_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
