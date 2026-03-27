"""
自定义异常模块

定义系统中使用的所有自定义异常类，实现统一的异常处理机制。
"""

from typing import Optional, Any, Dict


class BaseAppException(Exception):
    """应用基础异常类
    
    所有自定义异常的基类，提供统一的错误信息格式。
    
    Attributes:
        message: 错误信息
        error_code: 错误代码
        details: 错误详情
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化异常
        
        Args:
            message: 错误信息
            error_code: 错误代码
            details: 错误详情字典
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
    
    def __str__(self) -> str:
        """返回字符串表示"""
        if self.details:
            return f"[{self.error_code}] {self.message} - Details: {self.details}"
        return f"[{self.error_code}] {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            包含错误信息的字典
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class DatabaseException(BaseAppException):
    """数据库操作异常"""
    
    def __init__(
        self,
        message: str = "数据库操作失败",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code or "DB_ERROR",
            details=details
        )


class ConnectionException(DatabaseException):
    """数据库连接异常"""
    
    def __init__(
        self,
        message: str = "数据库连接失败",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code or "DB_CONNECTION_ERROR",
            details=details
        )


class QueryException(DatabaseException):
    """数据库查询异常"""
    
    def __init__(
        self,
        message: str = "数据库查询失败",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code or "DB_QUERY_ERROR",
            details=details
        )


class DataValidationException(BaseAppException):
    """数据验证异常"""
    
    def __init__(
        self,
        message: str = "数据验证失败",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code or "VALIDATION_ERROR",
            details=details
        )


class NotFoundException(BaseAppException):
    """资源未找到异常"""
    
    def __init__(
        self,
        message: str = "资源未找到",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code or "NOT_FOUND",
            details=details
        )


class ImportExportException(BaseAppException):
    """数据导入导出异常"""
    
    def __init__(
        self,
        message: str = "数据导入导出失败",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code or "IMPORT_EXPORT_ERROR",
            details=details
        )


class VisualizationException(BaseAppException):
    """可视化异常"""
    
    def __init__(
        self,
        message: str = "图表生成失败",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code or "VISUALIZATION_ERROR",
            details=details
        )


class ConfigurationException(BaseAppException):
    """配置异常"""
    
    def __init__(
        self,
        message: str = "配置错误",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code or "CONFIG_ERROR",
            details=details
        )
