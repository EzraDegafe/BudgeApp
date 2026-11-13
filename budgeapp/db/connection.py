"""Database engine and session setup.

Reads DATABASE_URL from .env, e.g.
postgresql+psycopg://USER:PASSWORD@localhost:5432/budgeapp
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from budgeapp.db.models import Base

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and fill in your Postgres credentials."
    )

# pool_pre_ping checks a pooled connection is still alive before using it,
# so a Postgres restart doesn't cause errors in a long-running Streamlit server.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    """Create any tables that don't exist yet."""
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
