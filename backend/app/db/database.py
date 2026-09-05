"""
Database engine and session management.

CONCEPT: SQLAlchemy Engine vs. Session
----------------------------------------
What it is: the `Engine` manages a pool of actual TCP connections to MySQL.
A `Session` is a lightweight, short-lived "workspace" for a single unit of
work (e.g., handling one HTTP request) that borrows a connection from the
engine's pool.

Why we need it: opening a new TCP connection to MySQL for every single
query would be slow and would exhaust MySQL's max-connections limit under
load. The engine's connection pool reuses connections. Sessions, being
request-scoped, prevent one request's uncommitted changes or transaction
state from leaking into another request.

Where we use it: `engine` is created once at import time (module-level
singleton). `SessionLocal` is a factory used by the `get_db` dependency
below, which FastAPI calls once per incoming request.

What problem it solves: connection efficiency + transaction isolation
between concurrent requests.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # checks a connection is alive before handing it out
    pool_recycle=3600,   # recycle connections after 1 hour (MySQL default
                         # wait_timeout can silently drop idle connections)
    echo=settings.DEBUG and settings.ENVIRONMENT == "development",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# CONCEPT: Declarative Base
# --------------------------
# What it is: a base class that all our ORM models (Product, Supplier,
# etc., starting Phase 2) will inherit from.
# Why we need it: SQLAlchemy uses this shared base to collect metadata
# about every model (table names, columns, relationships) in one registry.
# Where we use it: every file in app/models/ will do `class Product(Base):`.
# What problem it solves: it's how SQLAlchemy knows what tables exist, and
# it's also what Alembic reads from to auto-generate migrations by diffing
# "what models say the schema should be" against "what the DB actually has."
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session for the duration of
    a single request, and guarantees it's closed afterward.

    CONCEPT: Dependency Injection (FastAPI-specific)
    ---------------------------------------------------
    What it is: route functions declare `db: Session = Depends(get_db)` in
    their signature. FastAPI calls this generator, injects the yielded
    session into the route, and — critically — resumes this generator
    after the route finishes to run the `finally` block.

    Why we need it: without this pattern we'd have to manually open/close
    a session in every single route, and it's easy to forget to close one
    (connection leak) or to share one session across concurrent requests
    (data corruption / race conditions).

    Where we use it: every API route and repository function that touches
    the database, from Phase 2 onward.

    What problem it solves: guarantees correct session lifecycle (one
    session per request, always closed) with no repeated boilerplate.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Runs a trivial query to confirm the database is actually reachable.
    Used by the /health endpoint. Raises the underlying exception on
    failure so the caller can decide how to report it — we don't swallow
    errors here.
    """
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
