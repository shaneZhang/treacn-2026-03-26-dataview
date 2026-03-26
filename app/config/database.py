"""
Database connection management with factory pattern, connection pool, and strategy pattern.

This module provides:
- Database connection factory (Factory Pattern)
- Connection pool management (Singleton Pattern)
- Strategy pattern for multiple database types
- SQLAlchemy session management
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Type
from contextlib import contextmanager
import threading

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from dbutils.pooled_db import PooledDB

from app.config.settings import settings
from app.utils.logger import get_logger
from app.utils.exceptions import ConnectionError, ConfigurationError

logger = get_logger(__name__)


class DatabaseStrategy(ABC):
    """
    Abstract base class for database connection strategies.

    This implements the Strategy Pattern to support multiple database types.
    """

    @abstractmethod
    def create_engine(self, **kwargs) -> Engine:
        """
        Create a SQLAlchemy engine for the database.

        Args:
            **kwargs: Additional engine configuration options.

        Returns:
            Engine: SQLAlchemy engine instance.
        """
        pass

    @abstractmethod
    def get_connection_string(self) -> str:
        """
        Get the database connection string.

        Returns:
            str: Database connection URL.
        """
        pass


class SQLiteStrategy(DatabaseStrategy):
    """SQLite database connection strategy."""

    def get_connection_string(self) -> str:
        """Get SQLite connection string."""
        return settings.database_url

    def create_engine(self, **kwargs) -> Engine:
        """
        Create a SQLAlchemy engine for SQLite.

        SQLite has special handling for connection pooling and threading.
        """
        engine_kwargs = {
            "poolclass": StaticPool,
            "connect_args": {"check_same_thread": False},
            "echo": settings.app_debug,
            **kwargs
        }
        return create_engine(self.get_connection_string(), **engine_kwargs)


class PostgreSQLStrategy(DatabaseStrategy):
    """PostgreSQL database connection strategy."""

    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return settings.database_url

    def create_engine(self, **kwargs) -> Engine:
        """Create a SQLAlchemy engine for PostgreSQL with connection pooling."""
        engine_kwargs = {
            "poolclass": QueuePool,
            "pool_size": settings.db_pool_min_conn,
            "max_overflow": settings.db_pool_max_overflow,
            "pool_recycle": settings.db_pool_recycle,
            "pool_pre_ping": True,
            "echo": settings.app_debug,
            **kwargs
        }
        return create_engine(self.get_connection_string(), **engine_kwargs)


class MySQLStrategy(DatabaseStrategy):
    """MySQL database connection strategy."""

    def get_connection_string(self) -> str:
        """Get MySQL connection string."""
        return settings.database_url

    def create_engine(self, **kwargs) -> Engine:
        """Create a SQLAlchemy engine for MySQL with connection pooling."""
        engine_kwargs = {
            "poolclass": QueuePool,
            "pool_size": settings.db_pool_min_conn,
            "max_overflow": settings.db_pool_max_overflow,
            "pool_recycle": settings.db_pool_recycle,
            "pool_pre_ping": True,
            "echo": settings.app_debug,
            **kwargs
        }
        return create_engine(self.get_connection_string(), **engine_kwargs)


class DatabaseStrategyFactory:
    """
    Factory class to create appropriate database strategy instances.

    This implements the Factory Pattern to create database strategy objects
    based on the configured database type.
    """

    _strategies: Dict[str, Type[DatabaseStrategy]] = {
        "sqlite": SQLiteStrategy,
        "postgresql": PostgreSQLStrategy,
        "mysql": MySQLStrategy,
    }

    @classmethod
    def create_strategy(cls, db_type: Optional[str] = None) -> DatabaseStrategy:
        """
        Create a database strategy instance.

        Args:
            db_type: Database type (sqlite, postgresql, mysql).
                     If not provided, uses settings.db_type.

        Returns:
            DatabaseStrategy: Instance of the appropriate database strategy.

        Raises:
            ConfigurationError: If the database type is not supported.
        """
        db_type = db_type or settings.db_type

        if db_type not in cls._strategies:
            supported = ", ".join(cls._strategies.keys())
            raise ConfigurationError(
                f"Unsupported database type: {db_type}. "
                f"Supported types: {supported}"
            )

        strategy_class = cls._strategies[db_type]
        logger.info(f"Creating {db_type} database strategy")
        return strategy_class()


class DatabaseConnectionPool:
    """
    Database connection pool manager (Singleton Pattern).

    This class manages database connections using a singleton pattern
    to ensure only one connection pool exists per application instance.
    """

    _instance: Optional["DatabaseConnectionPool"] = None
    _lock: threading.Lock = threading.Lock()
    _initialized: bool = False

    def __new__(cls) -> "DatabaseConnectionPool":
        """Create or return the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the connection pool (only once)."""
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            self._strategy: DatabaseStrategy = DatabaseStrategyFactory.create_strategy()
            self._engine: Optional[Engine] = None
            self._session_factory: Optional[sessionmaker] = None
            self._initialized = True
            logger.info("DatabaseConnectionPool singleton initialized")

    @property
    def engine(self) -> Engine:
        """
        Get the SQLAlchemy engine (lazy initialization).

        Returns:
            Engine: SQLAlchemy engine instance.
        """
        if self._engine is None:
            with self._lock:
                if self._engine is None:
                    self._engine = self._strategy.create_engine()
                    logger.info(f"Database engine created: {settings.db_type}")
        return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        """
        Get the SQLAlchemy session factory (lazy initialization).

        Returns:
            sessionmaker: SQLAlchemy session factory.
        """
        if self._session_factory is None:
            with self._lock:
                if self._session_factory is None:
                    self._session_factory = sessionmaker(
                        autocommit=False,
                        autoflush=False,
                        bind=self.engine
                    )
        return self._session_factory

    def get_session(self) -> Session:
        """
        Create a new database session.

        Returns:
            Session: New SQLAlchemy session instance.

        Raises:
            ConnectionError: If session creation fails.
        """
        try:
            return self.session_factory()
        except Exception as e:
            logger.error(f"Failed to create database session: {e}")
            raise ConnectionError(
                message="Failed to create database session",
                details={"error": str(e)}
            ) from e

    @contextmanager
    def session_scope(self):
        """
        Context manager for database sessions.

        This context manager ensures proper session handling:
        - Commits on successful execution
        - Rolls back on exception
        - Closes the session when done

        Yields:
            Session: Database session instance.

        Raises:
            Exception: Any exception that occurs during the session.
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session rollback due to error: {e}")
            raise
        finally:
            session.close()

    def test_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            bool: True if connection is successful, False otherwise.
        """
        try:
            with self.session_scope() as session:
                result = session.execute("SELECT 1")
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def dispose(self) -> None:
        """Dispose the connection pool and clean up resources."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connection pool disposed")


# Convenience functions for easy access
def get_db_pool() -> DatabaseConnectionPool:
    """
    Get the database connection pool singleton.

    Returns:
        DatabaseConnectionPool: Connection pool instance.
    """
    return DatabaseConnectionPool()


def get_db_session() -> Session:
    """
    Get a new database session.

    Returns:
        Session: New database session instance.
    """
    return get_db_pool().get_session()


@contextmanager
def db_session():
    """
    Context manager for database sessions (convenience wrapper).

    Yields:
        Session: Database session instance.
    """
    with get_db_pool().session_scope() as session:
        yield session


def init_database() -> None:
    """
    Initialize the database and create all tables.
    
    This function should be called at application startup to ensure
    all database tables are created.
    """
    from app.models.base import Base
    
    pool = get_db_pool()
    Base.metadata.create_all(bind=pool.engine)
    logger.info("Database tables initialized")


# Initialize the pool when the module is imported
db_pool = get_db_pool()
