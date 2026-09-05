"""
Alembic environment configuration.

CONCEPT: Database Migrations
-------------------------------
What it is: a migration is a versioned, ordered script that describes one
incremental change to the database schema (e.g., "add a users table",
"add a quantity_received column to purchase_order_items"). Alembic tracks
which migrations have already been applied to a given database, in a
special `alembic_version` table.

Why we need it: without migrations, keeping a database schema in sync with
the code across multiple developers/environments means either manually
running ALTER TABLE statements (error-prone, undocumented, easy to forget
on one machine) or dropping and recreating the database (destroys data —
unacceptable once real data exists). Migrations make schema changes
reviewable (they're just files in git), repeatable, and reversible
(`upgrade` / `downgrade`).

Where we use it: starting Phase 2, every model change (new table, new
column, new index) gets a corresponding migration file in
alembic/versions/, generated via `alembic revision --autogenerate -m "..."`
and applied via `alembic upgrade head`.

What problem it solves: schema drift between environments, and "it worked
on my machine" database-state bugs.

This file connects Alembic to two things from our actual application
instead of duplicating config:
  1. Our `Settings` object — so migrations always target the same DB the
     app itself connects to (one source of truth for the connection URL).
  2. Our SQLAlchemy `Base.metadata` — so `--autogenerate` can diff "what
     the models say the schema should be" against "what tables actually
     exist" and generate the difference automatically, instead of us
     hand-writing every column definition twice.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db.database import Base

# Alembic Config object, giving access to values in alembic.ini
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models here so Base.metadata is fully populated before
# autogenerate compares it against the live database. As of Phase 1 there
# are no models yet; Phase 2 will add imports like:
#   from app.models.product import Product  # noqa: F401
target_metadata = Base.metadata

# Override the URL from alembic.ini with the one built from our app's
# environment-based Settings, so there's a single source of truth.
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates raw SQL)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection (the normal case)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
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
