# backend/audit/database.py
"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

# Create SQLAlchemy base
Base = declarative_base()

# 1. Get URL
database_url = settings.DATABASE_URL

# 2. Fix URL for synchronous psycopg2 (standard SQLAlchemy)
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Create engine
engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    echo=False  
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database (create tables)"""
    from backend.audit import models  # Import here to avoid circular imports
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database initialized")


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    Use with dependency injection in FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    """
    Get database session as context manager.
    Use with `with get_db_session() as db:`
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "init_db",
    "get_db",
    "get_db_session",
]