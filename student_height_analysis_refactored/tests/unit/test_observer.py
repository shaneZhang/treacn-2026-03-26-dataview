"""
观察者模式单元测试
"""

import pytest
from datetime import datetime
from src.core.observer import (
    DataChangeType,
    DataChangeEvent,
    Observer,
    Subject,
    LoggingObserver,
    CacheInvalidationObserver,
    NotificationObserver,
    DataChangeSubject,
    get_data_change_subject,
)


class MockObserver(Observer):
    """测试用观察者"""

    def __init__(self):
        self.events = []

    def update(self, event: DataChangeEvent) -> None:
        self.events.append(event)

    def get_observer_name(self) -> str:
        return "MockObserver"


class TestDataChangeEvent:
    """测试数据变更事件"""

    def test_event_creation(self):
        """测试事件创建"""
        event = DataChangeEvent(
            change_type=DataChangeType.CREATE,
            entity_type="Student",
            entity_id=1,
            new_data={"name": "张三"}
        )

        assert event.change_type == DataChangeType.CREATE
        assert event.entity_type == "Student"
        assert event.entity_id == 1
        assert event.new_data == {"name": "张三"}
        assert event.timestamp is not None

    def test_event_default_values(self):
        """测试事件默认值"""
        event = DataChangeEvent(
            change_type=DataChangeType.UPDATE,
            entity_type="Student"
        )

        assert event.entity_id is None
        assert event.old_data is None
        assert event.new_data is None
        assert event.metadata == {}


class TestSubject:
    """测试主题类"""

    def test_attach_observer(self):
        """测试添加观察者"""
        subject = Subject()
        observer = MockObserver()

        subject.attach(observer)
        assert observer in subject._observers

    def test_detach_observer(self):
        """测试移除观察者"""
        subject = Subject()
        observer = MockObserver()

        subject.attach(observer)
        subject.detach(observer)
        assert observer not in subject._observers

    def test_notify_observers(self):
        """测试通知观察者"""
        subject = Subject()
        observer = MockObserver()

        subject.attach(observer)

        event = DataChangeEvent(
            change_type=DataChangeType.CREATE,
            entity_type="Student",
            entity_id=1
        )

        subject.notify(event)
        assert len(observer.events) == 1
        assert observer.events[0].entity_id == 1


class TestLoggingObserver:
    """测试日志观察者"""

    def test_observer_name(self):
        """测试观察者名称"""
        observer = LoggingObserver()
        assert observer.get_observer_name() == "LoggingObserver"

    def test_update(self, caplog):
        """测试更新方法"""
        import logging

        observer = LoggingObserver()
        event = DataChangeEvent(
            change_type=DataChangeType.CREATE,
            entity_type="Student",
            entity_id=1,
            source="Test"
        )

        with caplog.at_level(logging.INFO):
            observer.update(event)

        assert "数据变更" in caplog.text
        assert "Student" in caplog.text


class TestCacheInvalidationObserver:
    """测试缓存失效观察者"""

    def test_observer_name(self):
        """测试观察者名称"""
        observer = CacheInvalidationObserver()
        assert observer.get_observer_name() == "CacheInvalidationObserver"

    def test_cache_operations(self):
        """测试缓存操作"""
        observer = CacheInvalidationObserver()

        # 设置缓存
        observer.set_cache("key1", "value1")
        assert observer.get_cache("key1") == "value1"

        # 更新事件应使缓存失效
        event = DataChangeEvent(
            change_type=DataChangeType.UPDATE,
            entity_type="Student",
            entity_id=1
        )
        observer.update(event)

        # 缓存应被清除
        assert observer.get_cache("Student:1") is None


class TestNotificationObserver:
    """测试通知观察者"""

    def test_observer_name(self):
        """测试观察者名称"""
        observer = NotificationObserver()
        assert observer.get_observer_name() == "NotificationObserver"

    def test_register_handler(self):
        """测试注册处理器"""
        observer = NotificationObserver()

        handler_called = False
        def handler(event):
            nonlocal handler_called
            handler_called = True

        observer.register_handler(DataChangeType.CREATE, handler)

        event = DataChangeEvent(
            change_type=DataChangeType.CREATE,
            entity_type="Student"
        )
        observer.update(event)

        assert handler_called


class TestDataChangeSubject:
    """测试数据变更主题"""

    def test_emit_event(self):
        """测试发布事件"""
        subject = DataChangeSubject()
        observer = MockObserver()
        subject.attach(observer)

        subject.emit(
            change_type=DataChangeType.CREATE,
            entity_type="Student",
            entity_id=1
        )

        assert len(observer.events) == 1
        assert observer.events[0].change_type == DataChangeType.CREATE

    def test_singleton(self):
        """测试单例模式"""
        subject1 = get_data_change_subject()
        subject2 = get_data_change_subject()
        assert subject1 is subject2
