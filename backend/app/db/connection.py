"""SQLite connection management for the Career OS knowledge base."""

import os
from pathlib import Path
from typing import Iterator, Optional

from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine
from sqlalchemy import event

DEFAULT_DB_FILENAME = "career_os.db"
DB_PATH_ENV_VAR = "CAREER_OS_DB_PATH"

_engines: dict[str, Engine] = {}


def get_database_path() -> str:
    """Return the configured database file path.

    Uses the CAREER_OS_DB_PATH environment variable if set,
    otherwise defaults to career_os.db in the backend directory.
    """
    configured = os.environ.get(DB_PATH_ENV_VAR)
    if configured:
        return configured
    return str(Path(__file__).resolve().parent.parent.parent / DEFAULT_DB_FILENAME)


def _enable_sqlite_pragmas(dbapi_connection, connection_record) -> None:
    """Enable foreign key enforcement on every new SQLite connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_engine(db_path: Optional[str] = None) -> Engine:
    """Return a cached engine for the given (or configured) database path."""
    path = db_path if db_path is not None else get_database_path()
    if path not in _engines:
        engine = create_engine(
            f"sqlite:///{path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        event.listen(engine, "connect", _enable_sqlite_pragmas)
        _engines[path] = engine
    return _engines[path]


def init_db(engine: Engine) -> None:
    """Create all tables, the FTS5 index, triggers, and indexes."""
    from sqlmodel import SQLModel

    from app.db import models  # noqa: F401 - ensures all tables are registered
    from app.db import apply_schema_extras

    SQLModel.metadata.create_all(engine)
    apply_schema_extras(engine)


def get_session() -> Iterator[Session]:
    """Yield a database session (FastAPI dependency)."""
    with Session(get_engine()) as session:
        yield session
