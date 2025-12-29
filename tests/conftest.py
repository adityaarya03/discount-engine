"""
Pytest configuration and fixtures for testing.
"""
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.core.database import get_session
from app.main import app


@pytest.fixture(name="session")
def session_fixture():
    """
    Create a fresh database session for each test.
    Uses in-memory SQLite for fast tests.
    """
    # Create in-memory SQLite database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session
    
    # Clean up
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Override the database session dependency with test session.
    """
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    
    yield
    
    app.dependency_overrides.clear()