import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Add the parent directory to Python path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all models so they are registered with Base.metadata
import app.models.models  # This registers all models with Base.metadata
from app.core.config import settings
from app.db.session import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# Set the database URL from settings
def get_database_url() -> str:
    """Get database URL with proper handling for Railway environment variables."""
    # Use Railway-style environment variables if available
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
