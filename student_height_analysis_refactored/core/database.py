"""
数据库连接工厂

使用工厂模式和策略模式创建数据库连接
"""
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from contextlib import contextmanager
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import QueuePool, StaticPool
import threading

from config import Config, DatabaseType
from models import Base
from utils import DatabaseConnectionException, get_logger


class DatabaseStrategy(ABC):
    """
    数据库策略抽象基类
    
    定义数据库连接的统一接口，不同数据库类型实现具体的连接策略。
    使用策略模式支持多种数据库类型。
    
    Example:
        >>> strategy = SQLiteStrategy(config)
        >>> engine = strategy.create_engine()
    """
    
    @abstractmethod
    def create_engine(self) -> Engine:
        """
        创建数据库引擎
        
        Returns:
            Engine: SQLAlchemy数据库引擎
        """
        pass
    
    @abstractmethod
    def get_connection_url(self) -> str:
        """
        获取数据库连接URL
        
        Returns:
            str: 数据库连接URL
        """
        pass
    
    @abstractmethod
    def get_pool_config(self) -> Dict[str, Any]:
        """
        获取连接池配置
        
        Returns:
            Dict[str, Any]: 连接池配置字典
        """
        pass


class SQLiteStrategy(DatabaseStrategy):
    """
    SQLite数据库策略
    
    实现SQLite数据库的连接策略
    
    Attributes:
        config: 配置对象
    
    Example:
        >>> strategy = SQLiteStrategy(config)
        >>> engine = strategy.create_engine()
    """
    
    def __init__(self, config: Config) -> None:
        """
        初始化SQLite策略
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.db_config = config.database_config
        self.logger = get_logger(__name__)
    
    def create_engine(self) -> Engine:
        """
        创建SQLite数据库引擎
        
        Returns:
            Engine: SQLAlchemy数据库引擎
        
        Raises:
            DatabaseConnectionException: 数据库连接失败
        """
        try:
            import os
            db_path = self.db_config['path']
            
            # 如果不是内存数据库，创建目录
            if db_path != ':memory:':
                db_dir = os.path.dirname(db_path)
                if db_dir:
                    os.makedirs(db_dir, exist_ok=True)
            
            engine = create_engine(
                self.get_connection_url(),
                echo=self.db_config.get('echo', False),
                poolclass=StaticPool,
                connect_args={'check_same_thread': False}
            )
            
            self.logger.info(f"SQLite数据库引擎创建成功: {db_path}")
            return engine
        except Exception as e:
            self.logger.error(f"SQLite数据库引擎创建失败: {e}")
            raise DatabaseConnectionException(
                f"SQLite数据库连接失败: {e}",
                details={'path': self.db_config.get('path')}
            )
    
    def get_connection_url(self) -> str:
        """
        获取SQLite连接URL
        
        Returns:
            str: 连接URL
        """
        return f"sqlite:///{self.db_config['path']}"
    
    def get_pool_config(self) -> Dict[str, Any]:
        """
        获取连接池配置
        
        Returns:
            Dict[str, Any]: 连接池配置
        """
        return {
            'poolclass': StaticPool,
            'connect_args': {'check_same_thread': False}
        }


class MySQLStrategy(DatabaseStrategy):
    """
    MySQL数据库策略
    
    实现MySQL数据库的连接策略
    
    Attributes:
        config: 配置对象
    
    Example:
        >>> strategy = MySQLStrategy(config)
        >>> engine = strategy.create_engine()
    """
    
    def __init__(self, config: Config) -> None:
        """
        初始化MySQL策略
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.db_config = config.database_config
        self.logger = get_logger(__name__)
    
    def create_engine(self) -> Engine:
        """
        创建MySQL数据库引擎
        
        Returns:
            Engine: SQLAlchemy数据库引擎
        
        Raises:
            DatabaseConnectionException: 数据库连接失败
        """
        try:
            pool_config = self.get_pool_config()
            
            engine = create_engine(
                self.get_connection_url(),
                echo=self.db_config.get('echo', False),
                pool_size=pool_config['pool_size'],
                max_overflow=pool_config['max_overflow'],
                pool_timeout=pool_config['pool_timeout'],
                pool_recycle=pool_config['pool_recycle'],
                pool_pre_ping=True
            )
            
            self.logger.info(
                f"MySQL数据库引擎创建成功: "
                f"{self.db_config['host']}:{self.db_config['port']}"
            )
            return engine
        except Exception as e:
            self.logger.error(f"MySQL数据库引擎创建失败: {e}")
            raise DatabaseConnectionException(
                f"MySQL数据库连接失败: {e}",
                details={
                    'host': self.db_config.get('host'),
                    'port': self.db_config.get('port'),
                    'database': self.db_config.get('database')
                }
            )
    
    def get_connection_url(self) -> str:
        """
        获取MySQL连接URL
        
        Returns:
            str: 连接URL
        """
        return (
            f"mysql+pymysql://{self.db_config['user']}:"
            f"{self.db_config['password']}@"
            f"{self.db_config['host']}:"
            f"{self.db_config['port']}/"
            f"{self.db_config['database']}?"
            f"charset={self.db_config['charset']}"
        )
    
    def get_pool_config(self) -> Dict[str, Any]:
        """
        获取连接池配置
        
        Returns:
            Dict[str, Any]: 连接池配置
        """
        return {
            'pool_size': self.db_config.get('pool_size', 5),
            'max_overflow': self.db_config.get('max_overflow', 10),
            'pool_timeout': self.db_config.get('pool_timeout', 30),
            'pool_recycle': self.db_config.get('pool_recycle', 3600)
        }


class PostgreSQLStrategy(DatabaseStrategy):
    """
    PostgreSQL数据库策略
    
    实现PostgreSQL数据库的连接策略
    
    Attributes:
        config: 配置对象
    
    Example:
        >>> strategy = PostgreSQLStrategy(config)
        >>> engine = strategy.create_engine()
    """
    
    def __init__(self, config: Config) -> None:
        """
        初始化PostgreSQL策略
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.db_config = config.database_config
        self.logger = get_logger(__name__)
    
    def create_engine(self) -> Engine:
        """
        创建PostgreSQL数据库引擎
        
        Returns:
            Engine: SQLAlchemy数据库引擎
        
        Raises:
            DatabaseConnectionException: 数据库连接失败
        """
        try:
            pool_config = self.get_pool_config()
            
            engine = create_engine(
                self.get_connection_url(),
                echo=self.db_config.get('echo', False),
                pool_size=pool_config['pool_size'],
                max_overflow=pool_config['max_overflow'],
                pool_timeout=pool_config['pool_timeout'],
                pool_recycle=pool_config['pool_recycle'],
                pool_pre_ping=True
            )
            
            self.logger.info(
                f"PostgreSQL数据库引擎创建成功: "
                f"{self.db_config['host']}:{self.db_config['port']}"
            )
            return engine
        except Exception as e:
            self.logger.error(f"PostgreSQL数据库引擎创建失败: {e}")
            raise DatabaseConnectionException(
                f"PostgreSQL数据库连接失败: {e}",
                details={
                    'host': self.db_config.get('host'),
                    'port': self.db_config.get('port'),
                    'database': self.db_config.get('database')
                }
            )
    
    def get_connection_url(self) -> str:
        """
        获取PostgreSQL连接URL
        
        Returns:
            str: 连接URL
        """
        return (
            f"postgresql://{self.db_config['user']}:"
            f"{self.db_config['password']}@"
            f"{self.db_config['host']}:"
            f"{self.db_config['port']}/"
            f"{self.db_config['database']}"
        )
    
    def get_pool_config(self) -> Dict[str, Any]:
        """
        获取连接池配置
        
        Returns:
            Dict[str, Any]: 连接池配置
        """
        return {
            'pool_size': self.db_config.get('pool_size', 5),
            'max_overflow': self.db_config.get('max_overflow', 10),
            'pool_timeout': self.db_config.get('pool_timeout', 30),
            'pool_recycle': self.db_config.get('pool_recycle', 3600)
        }


class DatabaseFactory:
    """
    数据库连接工厂
    
    使用工厂模式创建数据库连接，根据配置选择合适的数据库策略。
    
    Attributes:
        _instance: 单例实例
        _lock: 线程锁
        _engine: 数据库引擎
        _session_factory: 会话工厂
    
    Example:
        >>> factory = DatabaseFactory.get_instance()
        >>> session = factory.get_session()
    """
    
    _instance: Optional['DatabaseFactory'] = None
    _lock: threading.Lock = threading.Lock()
    _engine: Optional[Engine] = None
    _session_factory: Optional[scoped_session] = None
    
    def __new__(cls) -> 'DatabaseFactory':
        """
        重写__new__方法实现单例模式
        
        Returns:
            DatabaseFactory: 工厂实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """
        初始化数据库工厂
        """
        self.logger = get_logger(__name__)
        self.config = Config.get_instance()
    
    def _get_strategy(self) -> DatabaseStrategy:
        """
        获取数据库策略
        
        Returns:
            DatabaseStrategy: 数据库策略实例
        
        Raises:
            DatabaseConnectionException: 不支持的数据库类型
        """
        db_type = self.config.database_type
        
        strategies = {
            DatabaseType.SQLITE: SQLiteStrategy,
            DatabaseType.MYSQL: MySQLStrategy,
            DatabaseType.POSTGRESQL: PostgreSQLStrategy
        }
        
        strategy_class = strategies.get(db_type)
        if strategy_class is None:
            raise DatabaseConnectionException(
                f"不支持的数据库类型: {db_type}"
            )
        
        return strategy_class(self.config)
    
    def get_engine(self) -> Engine:
        """
        获取数据库引擎
        
        Returns:
            Engine: SQLAlchemy数据库引擎
        
        Example:
            >>> factory = DatabaseFactory.get_instance()
            >>> engine = factory.get_engine()
        """
        if self._engine is None:
            with self._lock:
                if self._engine is None:
                    strategy = self._get_strategy()
                    self._engine = strategy.create_engine()
        
        return self._engine
    
    def get_session_factory(self) -> scoped_session:
        """
        获取会话工厂
        
        Returns:
            scoped_session: 线程安全的会话工厂
        
        Example:
            >>> factory = DatabaseFactory.get_instance()
            >>> session_factory = factory.get_session_factory()
        """
        if self._session_factory is None:
            with self._lock:
                if self._session_factory is None:
                    engine = self.get_engine()
                    self._session_factory = scoped_session(
                        sessionmaker(bind=engine)
                    )
        
        return self._session_factory
    
    def get_session(self) -> Session:
        """
        获取数据库会话
        
        Returns:
            Session: 数据库会话
        
        Example:
            >>> factory = DatabaseFactory.get_instance()
            >>> session = factory.get_session()
        """
        return self.get_session_factory()()
    
    @contextmanager
    def session_scope(self):
        """
        会话上下文管理器
        
        自动处理会话的提交和回滚
        
        Yields:
            Session: 数据库会话
        
        Example:
            >>> with DatabaseFactory.get_instance().session_scope() as session:
            ...     student = session.query(Student).first()
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"数据库操作失败，已回滚: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self) -> None:
        """
        创建所有数据库表
        
        Example:
            >>> factory = DatabaseFactory.get_instance()
            >>> factory.create_tables()
        """
        engine = self.get_engine()
        Base.metadata.create_all(engine)
        self.logger.info("数据库表创建成功")
    
    def drop_tables(self) -> None:
        """
        删除所有数据库表
        
        Example:
            >>> factory = DatabaseFactory.get_instance()
            >>> factory.drop_tables()
        """
        engine = self.get_engine()
        Base.metadata.drop_all(engine)
        self.logger.info("数据库表删除成功")
    
    @classmethod
    def get_instance(cls) -> 'DatabaseFactory':
        """
        获取工厂实例
        
        Returns:
            DatabaseFactory: 工厂实例
        
        Example:
            >>> factory = DatabaseFactory.get_instance()
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """
        重置工厂实例（主要用于测试）
        
        Example:
            >>> DatabaseFactory.reset()
        """
        with cls._lock:
            if cls._session_factory:
                cls._session_factory.remove()
                cls._session_factory = None
            if cls._engine:
                cls._engine.dispose()
                cls._engine = None
            cls._instance = None
