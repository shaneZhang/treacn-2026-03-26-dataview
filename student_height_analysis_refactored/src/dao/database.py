"""
数据库连接管理模块

实现工厂模式创建数据库连接，使用单例模式管理连接池。
支持多种数据源（SQLite/PostgreSQL/MySQL）。
"""

from abc import ABC, abstractmethod
from typing import Optional, Generator, Any
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine, Engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool

from config.settings import get_settings, AppSettings
from src.core.exceptions import ConnectionException, ConfigurationException
from src.core.logger import get_logger


class DatabaseStrategy(ABC):
    """数据库策略抽象基类
    
    策略模式：定义数据库连接的通用接口。
    """
    
    @abstractmethod
    def create_engine(self, settings: AppSettings) -> Engine:
        """创建数据库引擎
        
        Args:
            settings: 应用配置
            
        Returns:
            SQLAlchemy引擎实例
        """
        pass
    
    @abstractmethod
    def get_pool_class(self) -> Optional[type]:
        """获取连接池类
        
        Returns:
            连接池类或None
        """
        pass


class PostgreSQLStrategy(DatabaseStrategy):
    """PostgreSQL数据库策略"""
    
    def create_engine(self, settings: AppSettings) -> Engine:
        """创建PostgreSQL引擎"""
        db_settings = settings.database
        
        engine = create_engine(
            db_settings.url,
            poolclass=self.get_pool_class(),
            pool_size=db_settings.pool_size,
            max_overflow=db_settings.max_overflow,
            pool_timeout=db_settings.pool_timeout,
            echo=db_settings.echo,
        )
        return engine
    
    def get_pool_class(self) -> type:
        """返回连接池类"""
        return QueuePool


class MySQLStrategy(DatabaseStrategy):
    """MySQL数据库策略"""
    
    def create_engine(self, settings: AppSettings) -> Engine:
        """创建MySQL引擎"""
        db_settings = settings.database
        
        engine = create_engine(
            db_settings.url,
            poolclass=self.get_pool_class(),
            pool_size=db_settings.pool_size,
            max_overflow=db_settings.max_overflow,
            pool_timeout=db_settings.pool_timeout,
            echo=db_settings.echo,
            pool_pre_ping=True,  # 自动检测断开连接
        )
        return engine
    
    def get_pool_class(self) -> type:
        """返回连接池类"""
        return QueuePool


class SQLiteStrategy(DatabaseStrategy):
    """SQLite数据库策略"""
    
    def create_engine(self, settings: AppSettings) -> Engine:
        """创建SQLite引擎"""
        db_settings = settings.database
        
        # SQLite特殊配置
        engine = create_engine(
            db_settings.url,
            poolclass=self.get_pool_class(),
            echo=db_settings.echo,
            connect_args={
                "check_same_thread": False,  # 允许多线程访问
            }
        )
        
        # 启用外键支持
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        
        return engine
    
    def get_pool_class(self) -> Optional[type]:
        """SQLite使用NullPool（无连接池）"""
        return NullPool


class DatabaseStrategyFactory:
    """数据库策略工厂
    
    工厂模式：根据数据库类型创建相应的策略。
    """
    
    _strategies = {
        "postgresql": PostgreSQLStrategy,
        "postgres": PostgreSQLStrategy,
        "mysql": MySQLStrategy,
        "mysql+pymysql": MySQLStrategy,
        "sqlite": SQLiteStrategy,
    }
    
    @classmethod
    def create_strategy(cls, driver: str) -> DatabaseStrategy:
        """创建数据库策略
        
        Args:
            driver: 数据库驱动名称
            
        Returns:
            数据库策略实例
            
        Raises:
            ConfigurationException: 不支持的数据库类型
        """
        driver_lower = driver.lower()
        strategy_class = cls._strategies.get(driver_lower)
        
        if strategy_class is None:
            supported = ", ".join(cls._strategies.keys())
            raise ConfigurationException(
                message=f"不支持的数据库类型: {driver}",
                error_code="UNSUPPORTED_DATABASE",
                details={"supported": supported, "provided": driver}
            )
        
        return strategy_class()


class DatabaseManager:
    """数据库管理器
    
    单例模式：管理数据库连接池和会话。
    """
    
    _instance: Optional['DatabaseManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'DatabaseManager':
        """创建单例实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """初始化数据库管理器"""
        if DatabaseManager._initialized:
            return
        
        self._logger = get_logger(self.__class__.__name__)
        self._settings = get_settings()
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        
        self._initialize()
        DatabaseManager._initialized = True
    
    def _initialize(self) -> None:
        """初始化数据库连接"""
        try:
            # 创建策略
            strategy = DatabaseStrategyFactory.create_strategy(
                self._settings.database.driver
            )
            
            # 创建引擎
            self._engine = strategy.create_engine(self._settings)
            
            # 创建会话工厂
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            
            self._logger.info(
                f"数据库连接已初始化: {self._settings.database.driver}"
            )
            
        except Exception as e:
            self._logger.error(f"数据库初始化失败: {e}")
            raise ConnectionException(
                message=f"数据库初始化失败: {str(e)}",
                error_code="DB_INIT_ERROR",
                details={"driver": self._settings.database.driver}
            )
    
    @property
    def engine(self) -> Engine:
        """获取数据库引擎
        
        Returns:
            SQLAlchemy引擎实例
            
        Raises:
            ConnectionException: 引擎未初始化
        """
        if self._engine is None:
            raise ConnectionException(
                message="数据库引擎未初始化",
                error_code="DB_ENGINE_NOT_INITIALIZED"
            )
        return self._engine
    
    def create_session(self) -> Session:
        """创建新会话
        
        Returns:
            新的数据库会话
        """
        if self._session_factory is None:
            raise ConnectionException(
                message="会话工厂未初始化",
                error_code="DB_SESSION_FACTORY_NOT_INITIALIZED"
            )
        return self._session_factory()
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话（上下文管理器）
        
        Yields:
            数据库会话
            
        Example:
            >>> with db_manager.get_session() as session:
            ...     result = session.query(Student).all()
        """
        session = self.create_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self._logger.error(f"数据库事务回滚: {e}")
            raise
        finally:
            session.close()
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self._engine:
            self._engine.dispose()
            self._logger.info("数据库连接已关闭")
    
    def create_tables(self) -> None:
        """创建所有表"""
        from src.dao.models import Base
        
        try:
            Base.metadata.create_all(bind=self.engine)
            self._logger.info("数据库表创建成功")
        except Exception as e:
            self._logger.error(f"创建表失败: {e}")
            raise ConnectionException(
                message=f"创建表失败: {str(e)}",
                error_code="DB_CREATE_TABLES_ERROR"
            )
    
    def drop_tables(self) -> None:
        """删除所有表"""
        from src.dao.models import Base
        
        try:
            Base.metadata.drop_all(bind=self.engine)
            self._logger.info("数据库表已删除")
        except Exception as e:
            self._logger.error(f"删除表失败: {e}")
            raise ConnectionException(
                message=f"删除表失败: {str(e)}",
                error_code="DB_DROP_TABLES_ERROR"
            )


@lru_cache()
def get_database_manager() -> DatabaseManager:
    """获取数据库管理器单例
    
    Returns:
        DatabaseManager: 数据库管理器实例
    """
    return DatabaseManager()


# 便捷函数
def get_engine() -> Engine:
    """获取数据库引擎
    
    Returns:
        SQLAlchemy引擎实例
    """
    return get_database_manager().engine


def get_session() -> Generator[Session, None, None]:
    """获取数据库会话
    
    Yields:
        数据库会话
    """
    return get_database_manager().get_session()


def create_tables() -> None:
    """创建所有表"""
    get_database_manager().create_tables()


def drop_tables() -> None:
    """删除所有表"""
    get_database_manager().drop_tables()
