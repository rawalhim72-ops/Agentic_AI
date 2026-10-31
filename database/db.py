"""
Database Connection and Session Management.
Uses SQLite with SQLAlchemy connection pooling and thread-safe sessions.
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config.settings import settings
from database.models import Base

# Ensure SQLite handles multi-threading safely in Streamlit
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False))


def init_db():
    """Create all tables in the database if they do not exist."""
    settings.ensure_directories()
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db_session():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
