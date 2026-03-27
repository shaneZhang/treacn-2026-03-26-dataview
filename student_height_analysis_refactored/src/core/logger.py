"""
日志管理模块

实现统一的日志记录系统，支持文件和控制台双输出。
使用单例模式管理日志配置。
"""

import os
import sys
import logging
from typing import Optional
from logging.handlers import RotatingFileHandler
from functools import lru_cache

from config.settings import get_settings, AppSettings


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器
    
    为控制台输出添加颜色支持。
    """
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录
        
        Args:
            record: 日志记录对象
            
        Returns:
            格式化后的日志字符串
        """
        # 保存原始levelname
        original_levelname = record.levelname
        
        # 添加颜色
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        
        # 格式化
        result = super().format(record)
        
        # 恢复原始levelname
        record.levelname = original_levelname
        
        return result


class LoggerManager:
    """日志管理器
    
    使用单例模式管理日志配置，支持文件和控制台双输出。
    
    Attributes:
        _instance: 单例实例
        _initialized: 是否已初始化
    """
    
    _instance: Optional['LoggerManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'LoggerManager':
        """创建单例实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """初始化日志管理器"""
        if LoggerManager._initialized:
            return
        
        self.settings = get_settings()
        self._loggers: dict = {}
        self._setup_root_logger()
        LoggerManager._initialized = True
    
    def _setup_root_logger(self) -> None:
        """配置根日志记录器"""
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.settings.log_level.upper()))
        
        # 清除现有处理器
        root_logger.handlers.clear()
        
        # 添加控制台处理器
        console_handler = self._create_console_handler()
        root_logger.addHandler(console_handler)
        
        # 添加文件处理器
        file_handler = self._create_file_handler()
        if file_handler:
            root_logger.addHandler(file_handler)
    
    def _create_console_handler(self) -> logging.Handler:
        """创建控制台日志处理器
        
        Returns:
            配置好的控制台处理器
        """
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, self.settings.log_level.upper()))
        
        # 使用带颜色的格式化器
        formatter = ColoredFormatter(self.settings.log_format)
        handler.setFormatter(formatter)
        
        return handler
    
    def _create_file_handler(self) -> Optional[logging.Handler]:
        """创建文件日志处理器
        
        Returns:
            配置好的文件处理器，如果无法创建则返回None
        """
        try:
            # 确保日志目录存在
            log_dir = os.path.dirname(self.settings.log_file)
            os.makedirs(log_dir, exist_ok=True)
            
            # 创建轮转文件处理器（最大10MB，保留5个备份）
            handler = RotatingFileHandler(
                self.settings.log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            handler.setLevel(getattr(logging, self.settings.log_level.upper()))
            
            # 使用标准格式化器
            formatter = logging.Formatter(self.settings.log_format)
            handler.setFormatter(formatter)
            
            return handler
        except Exception as e:
            # 如果文件处理器创建失败，只使用控制台
            logging.warning(f"无法创建文件日志处理器: {e}")
            return None
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            配置好的日志记录器
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        return self._loggers[name]


@lru_cache()
def get_logger_manager() -> LoggerManager:
    """获取日志管理器单例
    
    Returns:
        LoggerManager: 日志管理器实例
    """
    return LoggerManager()


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器
    
    便捷函数，用于快速获取日志记录器。
    
    Args:
        name: 日志记录器名称，通常使用__name__
        
    Returns:
        logging.Logger: 配置好的日志记录器
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条信息日志")
    """
    manager = get_logger_manager()
    return manager.get_logger(name)


# 导出便捷函数
__all__ = ['get_logger', 'get_logger_manager', 'LoggerManager']
