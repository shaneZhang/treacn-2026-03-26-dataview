"""
异常模块单元测试
"""

import pytest
from src.core.exceptions import (
    BaseAppException,
    DatabaseException,
    ConnectionException,
    QueryException,
    DataValidationException,
    NotFoundException,
)


class TestBaseAppException:
    """测试基础异常类"""

    def test_basic_exception(self):
        """测试基础异常创建"""
        exc = BaseAppException("测试错误")
        assert exc.message == "测试错误"
        assert exc.error_code == "UNKNOWN_ERROR"
        assert str(exc) == "[UNKNOWN_ERROR] 测试错误"

    def test_exception_with_code(self):
        """测试带错误代码的异常"""
        exc = BaseAppException("测试错误", error_code="TEST_ERROR")
        assert exc.error_code == "TEST_ERROR"
        assert "TEST_ERROR" in str(exc)

    def test_exception_with_details(self):
        """测试带详情的异常"""
        details = {"key": "value", "count": 42}
        exc = BaseAppException("测试错误", details=details)
        assert exc.details == details
        assert "key" in str(exc)

    def test_exception_to_dict(self):
        """测试异常转换为字典"""
        exc = BaseAppException(
            "测试错误",
            error_code="TEST_ERROR",
            details={"key": "value"}
        )
        result = exc.to_dict()
        assert result["message"] == "测试错误"
        assert result["error_code"] == "TEST_ERROR"
        assert result["details"] == {"key": "value"}


class TestDatabaseException:
    """测试数据库异常类"""

    def test_default_message(self):
        """测试默认错误信息"""
        exc = DatabaseException()
        assert "数据库操作失败" in exc.message
        assert exc.error_code == "DB_ERROR"

    def test_custom_message(self):
        """测试自定义错误信息"""
        exc = DatabaseException("自定义错误")
        assert exc.message == "自定义错误"


class TestConnectionException:
    """测试连接异常类"""

    def test_default_message(self):
        """测试默认错误信息"""
        exc = ConnectionException()
        assert "数据库连接失败" in exc.message
        assert exc.error_code == "DB_CONNECTION_ERROR"


class TestQueryException:
    """测试查询异常类"""

    def test_default_message(self):
        """测试默认错误信息"""
        exc = QueryException()
        assert "数据库查询失败" in exc.message
        assert exc.error_code == "DB_QUERY_ERROR"


class TestDataValidationException:
    """测试数据验证异常类"""

    def test_default_message(self):
        """测试默认错误信息"""
        exc = DataValidationException()
        assert "数据验证失败" in exc.message
        assert exc.error_code == "VALIDATION_ERROR"


class TestNotFoundException:
    """测试未找到异常类"""

    def test_default_message(self):
        """测试默认错误信息"""
        exc = NotFoundException()
        assert "资源未找到" in exc.message
        assert exc.error_code == "NOT_FOUND"
