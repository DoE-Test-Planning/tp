import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

# Add the parent directory to sys.path to allow absolute imports
sys.path.append(str(Path(__file__).resolve().parents[1].parent))

# Import SQLAlchemy components
try:
    from sqlalchemy import engine_from_config, pool
    from sqlalchemy.engine import Connection
    from sqlalchemy.ext.asyncio import async_engine_from_config
except ImportError as e:
    print(f"Error importing SQLAlchemy modules: {e}")
    print(f"Current sys.path: {sys.path}")
    raise

from alembic import context

# Import our models and config
try:
    from app.core.config import settings  
    from app.models.base import Base
    from app.models.user import User
    from app.models.doe_asset import DoEAsset, DoEAssetVersion, ShareableLink
except ImportError as e:
    print(f"Error importing application modules: {e}")
    print(f"Current sys.path: {sys.path}")
    raise

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override the SQLAlchemy URL with our config
try:
    config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URI))
except Exception as e:
    print(f"Error setting database URI: {e}")
    # Fallback to environment variable if settings object fails
    db_url = os.getenv("DATABASE_URI")
    if db_url:
        config.set_main_option("sqlalchemy.url", db_url)
    else:
        print("Warning: No database URI set, migrations may fail")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    
    This is the synchronous wrapper for the async migration function.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 