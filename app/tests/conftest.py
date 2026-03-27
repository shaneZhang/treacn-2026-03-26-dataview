"""
Pytest configuration for the Student Height Analysis System.

This module provides fixtures and configuration for running tests.
"""

import os
import sys
import pytest
from typing import Generator

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.config.database import get_db_pool
from app.main import StudentHeightAnalysisApp


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """
    Fixture for the test database URL.
    
    Returns:
        str: SQLite in-memory database URL for testing.
    """
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine(test_db_url: str):
    """
    Fixture for the test database engine.
    
    Args:
        test_db_url: URL of the test database.
        
    Returns:
        Engine: SQLAlchemy engine connected to the test database.
    """
    return create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """
    Fixture for the test session factory.
    
    Args:
        test_engine: SQLAlchemy engine for the test database.
        
    Returns:
        sessionmaker: Session factory for creating test sessions.
    """
    Base.metadata.create_all(bind=test_engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def test_session(test_session_factory, test_engine) -> Generator:
    """
    Fixture for a test database session.
    
    Creates a new session for each test and rolls back after the test completes.
    Each test runs with a clean database state.
    
    Args:
        test_session_factory: Session factory for creating test sessions.
        test_engine: SQLAlchemy engine for the test database.
        
    Yields:
        Session: Database session for testing.
    """
    # Reset database state before each test
    from app.models.base import Base
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    session = test_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_app() -> Generator[StudentHeightAnalysisApp, None, None]:
    """
    Fixture for the test application instance.
    
    Returns:
        StudentHeightAnalysisApp: Initialized application instance for testing.
    """
    app = StudentHeightAnalysisApp()
    app.initialize()
    try:
        yield app
    finally:
        app.cleanup()
