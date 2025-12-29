"""
Database connection and session management.
"""
from typing import Generator
from sqlmodel import create_engine, Session, SQLModel
from app.config import settings


# Create engine with connection pooling for production
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,   # Verify connections before using
    pool_size=10,         # Connection pool size
    max_overflow=20,      # Max overflow connections
)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency for database session.
    Yields a session and ensures proper cleanup.
    """
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    """
    Create all database tables.
    Called during application startup.
    """
    SQLModel.metadata.create_all(engine)


def init_db():
    """
    Initialize database with tables.
    Use Alembic migrations in production.
    """
    create_db_and_tables()