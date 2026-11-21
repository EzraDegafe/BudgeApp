"""Database engine and session setup.

By default the app uses a SQLite file, budgeapp.db, in the project folder. It is created
automatically, tables included, the first time the app starts.

To use a different database, set DATABASE_URL in .env, e.g.
postgresql+psycopg://USER:PASSWORD@localhost:5432/budgeapp
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from budgeapp.db.models import Base

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _database_url() -> str:
    url = make_url(os.getenv("DATABASE_URL") or "sqlite:///budgeapp.db")
    # Resolve a relative SQLite path against the project folder, so the same file is used
    # no matter which folder `streamlit run` is started from.
    if url.get_backend_name() == "sqlite" and url.database and url.database != ":memory:":
        path = Path(url.database)
        if not path.is_absolute():
            url = url.set(database=str(PROJECT_ROOT / path))
    return url.render_as_string(hide_password=False)


DATABASE_URL = _database_url()

# SQLite: Streamlit runs each session on its own thread, so let connections be shared.
# Others: pool_pre_ping checks a pooled connection is still alive before using it.
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    """Create the database file (for SQLite) and any tables that don't exist yet."""
    Base.metadata.create_all(engine)


@contextmanager
def get_session() -> Iterator[Session]:
    """Yield a session that commits on success and rolls back on error."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
