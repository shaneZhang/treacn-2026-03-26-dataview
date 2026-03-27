"""
配置管理模块

使用单例模式管理应用配置
"""
import os
from typing import Dict, Any, Optional
from enum import Enum


class DatabaseType(Enum):
    """数据库类型枚举"""
    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"


class Config:
    """
    配置管理类（单例模式）
    
    管理应用程序的所有配置信息，包括数据库连接、日志配置等。
    使用单例模式确保全局只有一个配置实例。
    
    Attributes:
        _instance: 单例实例
        _initialized: 是否已初始化标志
        
    Example:
        >>> config = Config.get_instance()
        >>> db_config = config.get_database_config()
    """
    
    _instance: Optional['Config'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'Config':
        """
        重写__new__方法实现单例模式
        
        Returns:
            Config: 配置实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """
        初始化配置
        
        只在第一次创建实例时执行初始化
        """
        if self._initialized:
            return
            
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._load_config()
        Config._initialized = True
    
    def _load_config(self) -> None:
        """加载配置"""
        self.database_type = DatabaseType(
            os.getenv('DB_TYPE', 'sqlite').lower()
        )
        
        self.database_config = self._get_database_config()
        self.log_config = self._get_log_config()
        self.app_config = self._get_app_config()
    
    def _get_database_config(self) -> Dict[str, Any]:
        """
        获取数据库配置
        
        Returns:
            Dict[str, Any]: 数据库配置字典
        """
        base_config = {
            'pool_size': int(os.getenv('DB_POOL_SIZE', '5')),
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '10')),
            'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
            'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),
            'echo': os.getenv('DB_ECHO', 'false').lower() == 'true',
        }
        
        if self.database_type == DatabaseType.SQLITE:
            base_config.update({
                'database': os.getenv('DB_NAME', 'student_height.db'),
                'path': os.path.join(self.base_dir, 'data', 'student_height.db')
            })
        elif self.database_type == DatabaseType.MYSQL:
            base_config.update({
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', '3306')),
                'database': os.getenv('DB_NAME', 'student_height'),
                'user': os.getenv('DB_USER', 'root'),
                'password': os.getenv('DB_PASSWORD', ''),
                'charset': 'utf8mb4'
            })
        elif self.database_type == DatabaseType.POSTGRESQL:
            base_config.update({
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', '5432')),
                'database': os.getenv('DB_NAME', 'student_height'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', ''),
            })
        
        return base_config
    
    def _get_log_config(self) -> Dict[str, Any]:
        """
        获取日志配置
        
        Returns:
            Dict[str, Any]: 日志配置字典
        """
        return {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'file_path': os.path.join(self.base_dir, 'logs', 'app.log'),
            'max_bytes': int(os.getenv('LOG_MAX_BYTES', '10485760')),
            'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5')),
            'console_output': os.getenv('LOG_CONSOLE', 'true').lower() == 'true'
        }
    
    def _get_app_config(self) -> Dict[str, Any]:
        """
        获取应用配置
        
        Returns:
            Dict[str, Any]: 应用配置字典
        """
        return {
            'data_dir': os.path.join(self.base_dir, 'data'),
            'output_dir': os.path.join(self.base_dir, 'output'),
            'migration_dir': os.path.join(self.base_dir, 'migrations'),
            'default_data_count': int(os.getenv('DEFAULT_DATA_COUNT', '1000')),
            'random_seed': int(os.getenv('RANDOM_SEED', '42'))
        }
    
    @classmethod
    def get_instance(cls) -> 'Config':
        """
        获取配置实例
        
        Returns:
            Config: 配置实例
        
        Example:
            >>> config = Config.get_instance()
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get_database_url(self) -> str:
        """
        获取数据库连接URL
        
        Returns:
            str: 数据库连接URL
        
        Example:
            >>> config = Config.get_instance()
            >>> url = config.get_database_url()
        """
        if self.database_type == DatabaseType.SQLITE:
            return f"sqlite:///{self.database_config['path']}"
        elif self.database_type == DatabaseType.MYSQL:
            return (
                f"mysql+pymysql://{self.database_config['user']}:"
                f"{self.database_config['password']}@"
                f"{self.database_config['host']}:"
                f"{self.database_config['port']}/"
                f"{self.database_config['database']}?"
                f"charset={self.database_config['charset']}"
            )
        elif self.database_type == DatabaseType.POSTGRESQL:
            return (
                f"postgresql://{self.database_config['user']}:"
                f"{self.database_config['password']}@"
                f"{self.database_config['host']}:"
                f"{self.database_config['port']}/"
                f"{self.database_config['database']}"
            )
        else:
            raise ValueError(f"不支持的数据库类型: {self.database_type}")
    
    def reset(self) -> None:
        """
        重置配置实例（主要用于测试）
        
        Example:
            >>> config = Config.get_instance()
            >>> config.reset()
        """
        Config._instance = None
        Config._initialized = False
