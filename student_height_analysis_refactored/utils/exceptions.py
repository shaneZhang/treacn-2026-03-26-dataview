"""
自定义异常类

定义系统中使用的所有自定义异常
"""
from typing import Optional, Any


class StudentHeightBaseException(Exception):
    """
    基础异常类
    
    所有自定义异常的基类
    
    Attributes:
        message: 异常消息
        error_code: 错误代码
        details: 详细信息
    
    Example:
        >>> raise StudentHeightBaseException("发生错误", error_code=1001)
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[int] = None,
        details: Optional[Any] = None
    ) -> None:
        """
        初始化异常
        
        Args:
            message: 异常消息
            error_code: 错误代码
            details: 详细信息
        """
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """字符串表示"""
        if self.error_code:
            return f"[错误代码 {self.error_code}] {self.message}"
        return self.message
    
    def to_dict(self) -> dict:
        """
        转换为字典格式
        
        Returns:
            dict: 异常信息字典
        """
        result = {
            'error_type': self.__class__.__name__,
            'message': self.message
        }
        if self.error_code:
            result['error_code'] = self.error_code
        if self.details:
            result['details'] = self.details
        return result


class DatabaseException(StudentHeightBaseException):
    """
    数据库异常
    
    数据库操作相关的异常
    
    Example:
        >>> raise DatabaseException("数据库连接失败", error_code=2001)
    """
    pass


class DatabaseConnectionException(DatabaseException):
    """
    数据库连接异常
    
    Example:
        >>> raise DatabaseConnectionException("无法连接到数据库服务器")
    """
    pass


class DatabaseQueryException(DatabaseException):
    """
    数据库查询异常
    
    Example:
        >>> raise DatabaseQueryException("查询执行失败", details={"sql": "SELECT * FROM students"})
    """
    pass


class DataNotFoundException(StudentHeightBaseException):
    """
    数据未找到异常
    
    Example:
        >>> raise DataNotFoundException("学生记录不存在", error_code=3001)
    """
    pass


class StudentNotFoundException(DataNotFoundException):
    """
    学生未找到异常
    
    Example:
        >>> raise StudentNotFoundException("学号为10001的学生不存在")
    """
    pass


class RecordNotFoundException(DataNotFoundException):
    """
    记录未找到异常
    
    Example:
        >>> raise RecordNotFoundException("身高记录不存在")
    """
    pass


class DataValidationException(StudentHeightBaseException):
    """
    数据验证异常
    
    Example:
        >>> raise DataValidationException("身高值超出合理范围", error_code=4001)
    """
    pass


class InvalidDataException(DataValidationException):
    """
    无效数据异常
    
    Example:
        >>> raise InvalidDataException("身高不能为负数")
    """
    pass


class DuplicateDataException(DataValidationException):
    """
    重复数据异常
    
    Example:
        >>> raise DuplicateDataException("学号已存在")
    """
    pass


class FileOperationException(StudentHeightBaseException):
    """
    文件操作异常
    
    Example:
        >>> raise FileOperationException("文件读取失败", error_code=5001)
    """
    pass


class FileNotFoundException(FileOperationException):
    """
    文件未找到异常
    
    Example:
        >>> raise FileNotFoundException("数据文件不存在")
    """
    pass


class FileFormatNotSupportedException(FileOperationException):
    """
    文件格式不支持异常
    
    Example:
        >>> raise FileFormatNotSupportedException("不支持的文件格式")
    """
    pass


class ConfigurationException(StudentHeightBaseException):
    """
    配置异常
    
    Example:
        >>> raise ConfigurationException("配置文件格式错误", error_code=6001)
    """
    pass


class VisualizationException(StudentHeightBaseException):
    """
    可视化异常
    
    Example:
        >>> raise VisualizationException("图表生成失败", error_code=7001)
    """
    pass


class AnalysisException(StudentHeightBaseException):
    """
    分析异常
    
    Example:
        >>> raise AnalysisException("数据分析失败", error_code=8001)
    """
    pass


class ImportExportException(StudentHeightBaseException):
    """
    导入导出异常
    
    Example:
        >>> raise ImportExportException("数据导出失败", error_code=9001)
    """
    pass


class ObserverException(StudentHeightBaseException):
    """
    观察者模式异常
    
    Example:
        >>> raise ObserverException("观察者注册失败", error_code=10001)
    """
    pass
