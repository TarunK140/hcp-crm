"""
SQLAlchemy engine + session management.

Exposes:
- `Base`: declarative base all models inherit from
- `get_db`: FastAPI dependency that yields a session and always closes it
- `init_db`: creates all tables on startup (simple alternative to a full
  migration tool like Alembic, appropriate for an assignment-scale project)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session, closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Called once on application startup."""
    from app.models import interaction  # noqa: F401 (ensure model is registered)
    Base.metadata.create_all(bind=engine)
