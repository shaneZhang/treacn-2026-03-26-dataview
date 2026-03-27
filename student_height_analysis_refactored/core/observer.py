"""
观察者模式实现

实现数据变更通知机制
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from utils import ObserverException, get_logger


class EventType(Enum):
    """事件类型枚举"""
    STUDENT_CREATED = "student_created"
    STUDENT_UPDATED = "student_updated"
    STUDENT_DELETED = "student_deleted"
    RECORD_CREATED = "record_created"
    RECORD_UPDATED = "record_updated"
    RECORD_DELETED = "record_deleted"
    DATA_IMPORTED = "data_imported"
    DATA_EXPORTED = "data_exported"
    ANALYSIS_COMPLETED = "analysis_completed"
    VISUALIZATION_COMPLETED = "visualization_completed"


@dataclass
class Event:
    """
    事件数据类
    
    Attributes:
        event_type: 事件类型
        data: 事件数据
        timestamp: 时间戳
        source: 事件源
    """
    event_type: EventType
    data: Any
    timestamp: datetime
    source: str
    
    def to_dict(self) -> dict:
        """
        转换为字典
        
        Returns:
            dict: 事件信息字典
        """
        return {
            'event_type': self.event_type.value,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }


class Observer(ABC):
    """
    观察者抽象基类
    
    定义观察者的统一接口
    
    Example:
        >>> class LogObserver(Observer):
        ...     def update(self, event):
        ...         print(f"收到事件: {event.event_type}")
    """
    
    @abstractmethod
    def update(self, event: Event) -> None:
        """
        更新方法，当被观察对象发生变化时调用
        
        Args:
            event: 事件对象
        
        Example:
            >>> observer.update(event)
        """
        pass


class Subject:
    """
    被观察对象（主题）
    
    管理观察者列表，并在状态变化时通知所有观察者。
    
    Attributes:
        _observers: 观察者列表
        _logger: 日志记录器
    
    Example:
        >>> subject = Subject()
        >>> subject.attach(observer)
        >>> subject.notify(event)
    """
    
    def __init__(self) -> None:
        """初始化被观察对象"""
        self._observers: List[Observer] = []
        self._logger = get_logger(__name__)
    
    def attach(self, observer: Observer) -> None:
        """
        添加观察者
        
        Args:
            observer: 观察者对象
        
        Example:
            >>> subject.attach(log_observer)
        """
        if observer not in self._observers:
            self._observers.append(observer)
            self._logger.debug(f"观察者已添加: {observer.__class__.__name__}")
    
    def detach(self, observer: Observer) -> None:
        """
        移除观察者
        
        Args:
            observer: 观察者对象
        
        Example:
            >>> subject.detach(log_observer)
        """
        if observer in self._observers:
            self._observers.remove(observer)
            self._logger.debug(f"观察者已移除: {observer.__class__.__name__}")
    
    def notify(self, event: Event) -> None:
        """
        通知所有观察者
        
        Args:
            event: 事件对象
        
        Example:
            >>> subject.notify(event)
        """
        self._logger.debug(
            f"通知观察者: {event.event_type.value}, "
            f"观察者数量: {len(self._observers)}"
        )
        
        for observer in self._observers:
            try:
                observer.update(event)
            except Exception as e:
                self._logger.error(
                    f"观察者 {observer.__class__.__name__} 处理事件失败: {e}"
                )


class LogObserver(Observer):
    """
    日志观察者
    
    将事件记录到日志
    
    Example:
        >>> observer = LogObserver()
        >>> subject.attach(observer)
    """
    
    def __init__(self) -> None:
        """初始化日志观察者"""
        self.logger = get_logger('EventLogger')
    
    def update(self, event: Event) -> None:
        """
        记录事件到日志
        
        Args:
            event: 事件对象
        """
        self.logger.info(
            f"事件: {event.event_type.value}, "
            f"来源: {event.source}, "
            f"数据: {event.data}"
        )


class CacheObserver(Observer):
    """
    缓存观察者
    
    当数据变更时清除相关缓存
    
    Attributes:
        _cache: 缓存字典
    
    Example:
        >>> observer = CacheObserver()
        >>> subject.attach(observer)
    """
    
    def __init__(self) -> None:
        """初始化缓存观察者"""
        self._cache: dict = {}
        self.logger = get_logger(__name__)
    
    def update(self, event: Event) -> None:
        """
        清除相关缓存
        
        Args:
            event: 事件对象
        """
        cache_keys_to_clear = []
        
        if event.event_type in [
            EventType.STUDENT_CREATED,
            EventType.STUDENT_UPDATED,
            EventType.STUDENT_DELETED
        ]:
            cache_keys_to_clear = [
                'students_list',
                'student_stats',
                'grade_stats'
            ]
        elif event.event_type in [
            EventType.RECORD_CREATED,
            EventType.RECORD_UPDATED,
            EventType.RECORD_DELETED
        ]:
            cache_keys_to_clear = [
                'records_list',
                'height_stats',
                'bmi_stats'
            ]
        
        for key in cache_keys_to_clear:
            if key in self._cache:
                del self._cache[key]
                self.logger.debug(f"缓存已清除: {key}")
    
    def get_cache(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
        
        Returns:
            Optional[Any]: 缓存值，不存在则返回None
        """
        return self._cache.get(key)
    
    def set_cache(self, key: str, value: Any) -> None:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        self._cache[key] = value


class NotificationObserver(Observer):
    """
    通知观察者
    
    发送通知（可扩展为邮件、短信等）
    
    Example:
        >>> observer = NotificationObserver()
        >>> subject.attach(observer)
    """
    
    def __init__(self) -> None:
        """初始化通知观察者"""
        self.notifications: List[dict] = []
        self.logger = get_logger(__name__)
    
    def update(self, event: Event) -> None:
        """
        添加通知
        
        Args:
            event: 事件对象
        """
        notification = {
            'event_type': event.event_type.value,
            'message': self._generate_message(event),
            'timestamp': event.timestamp,
            'read': False
        }
        self.notifications.append(notification)
        self.logger.info(f"新通知: {notification['message']}")
    
    def _generate_message(self, event: Event) -> str:
        """
        生成通知消息
        
        Args:
            event: 事件对象
        
        Returns:
            str: 通知消息
        """
        messages = {
            EventType.STUDENT_CREATED: "新学生已添加",
            EventType.STUDENT_UPDATED: "学生信息已更新",
            EventType.STUDENT_DELETED: "学生记录已删除",
            EventType.RECORD_CREATED: "新身高记录已添加",
            EventType.RECORD_UPDATED: "身高记录已更新",
            EventType.RECORD_DELETED: "身高记录已删除",
            EventType.DATA_IMPORTED: "数据导入完成",
            EventType.DATA_EXPORTED: "数据导出完成",
            EventType.ANALYSIS_COMPLETED: "数据分析完成",
            EventType.VISUALIZATION_COMPLETED: "可视化图表生成完成"
        }
        
        return messages.get(event.event_type, f"事件: {event.event_type.value}")
    
    def get_unread_notifications(self) -> List[dict]:
        """
        获取未读通知
        
        Returns:
            List[dict]: 未读通知列表
        """
        return [n for n in self.notifications if not n['read']]
    
    def mark_as_read(self, index: int) -> None:
        """
        标记通知为已读
        
        Args:
            index: 通知索引
        """
        if 0 <= index < len(self.notifications):
            self.notifications[index]['read'] = True


class EventManager:
    """
    事件管理器
    
    单例模式，管理全局事件和观察者
    
    Attributes:
        _instance: 单例实例
        _subject: 被观察对象
    
    Example:
        >>> manager = EventManager.get_instance()
        >>> manager.emit(EventType.STUDENT_CREATED, data)
    """
    
    _instance: Optional['EventManager'] = None
    
    def __new__(cls) -> 'EventManager':
        """
        重写__new__方法实现单例模式
        
        Returns:
            EventManager: 事件管理器实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subject = Subject()
            cls._instance._logger = get_logger(__name__)
        return cls._instance
    
    def attach(self, observer: Observer) -> None:
        """
        添加观察者
        
        Args:
            observer: 观察者对象
        """
        self._subject.attach(observer)
    
    def detach(self, observer: Observer) -> None:
        """
        移除观察者
        
        Args:
            observer: 观察者对象
        """
        self._subject.detach(observer)
    
    def emit(
        self, 
        event_type: EventType, 
        data: Any, 
        source: str = "system"
    ) -> None:
        """
        发送事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件源
        
        Example:
            >>> manager.emit(EventType.STUDENT_CREATED, {'student_id': 1})
        """
        event = Event(
            event_type=event_type,
            data=data,
            timestamp=datetime.now(),
            source=source
        )
        self._subject.notify(event)
    
    @classmethod
    def get_instance(cls) -> 'EventManager':
        """
        获取事件管理器实例
        
        Returns:
            EventManager: 事件管理器实例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """
        重置事件管理器（主要用于测试）
        """
        cls._instance = None
