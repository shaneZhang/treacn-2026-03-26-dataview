"""
日志工具模块

提供统一的日志记录功能，支持文件和控制台双输出
"""
import logging
import sys
from typing import Optional
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import Config


class LoggerManager:
    """
    日志管理器
    
    管理应用程序的日志记录，支持文件和控制台双输出。
    使用单例模式确保全局只有一个日志管理器实例。
    
    Attributes:
        _instance: 单例实例
        _initialized: 是否已初始化标志
        logger: 日志记录器
    
    Example:
        >>> logger = LoggerManager.get_logger(__name__)
        >>> logger.info("这是一条日志消息")
    """
    
    _instance: Optional['LoggerManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'LoggerManager':
        """
        重写__new__方法实现单例模式
        
        Returns:
            LoggerManager: 日志管理器实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """
        初始化日志管理器
        
        只在第一次创建实例时执行初始化
        """
        if self._initialized:
            return
        
        config = Config.get_instance()
        log_config = config.log_config
        
        self.logger = logging.getLogger('StudentHeightAnalysis')
        self.logger.setLevel(getattr(logging, log_config['level']))
        
        self.logger.handlers.clear()
        
        formatter = logging.Formatter(
            log_config['format'],
            datefmt=log_config['datefmt']
        )
        
        log_dir = Path(log_config['file_path']).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_config['file_path'],
            maxBytes=log_config['max_bytes'],
            backupCount=log_config['backup_count'],
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        if log_config['console_output']:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        LoggerManager._initialized = True
    
    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称，如果为None则返回根日志记录器
        
        Returns:
            logging.Logger: 日志记录器
        
        Example:
            >>> logger = LoggerManager.get_logger(__name__)
        """
        if cls._instance is None:
            cls._instance = cls()
        
        if name:
            child_logger = cls._instance.logger.getChild(name)
            return child_logger
        return cls._instance.logger
    
    @classmethod
    def reset(cls) -> None:
        """
        重置日志管理器（主要用于测试）
        
        Example:
            >>> LoggerManager.reset()
        """
        if cls._instance and cls._instance.logger:
            for handler in cls._instance.logger.handlers[:]:
                handler.close()
                cls._instance.logger.removeHandler(handler)
        cls._instance = None
        cls._initialized = False


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器的便捷函数
    
    Args:
        name: 日志记录器名称
    
    Returns:
        logging.Logger: 日志记录器
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条日志消息")
    """
    return LoggerManager.get_logger(name)
