import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.models.models
from app.core.config import settings
from app.db.session import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_database_url() -> str:
    """Get database URL with proper handling for Railway environment variables."""
    postgres_host = os.getenv("POSTGRES_HOST") or settings.POSTGRES_SERVER
    postgres_port = os.getenv("POSTGRES_PORT") or settings.POSTGRES_PORT
    postgres_user = os.getenv("POSTGRES_USER") or settings.POSTGRES_USER
    postgres_password = os.getenv("POSTGRES_PASSWORD") or settings.POSTGRES_PASSWORD
    postgres_db = os.getenv("POSTGRES_DB") or settings.POSTGRES_DB

    return f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Override the SQLAlchemy URL in alembic.ini
    config.set_main_option("sqlalchemy.url", get_database_url())

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
