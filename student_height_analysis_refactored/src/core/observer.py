"""
观察者模式实现模块

实现观察者模式，用于数据变更通知机制。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, Optional
from enum import Enum, auto
from dataclasses import dataclass
from datetime import datetime

from src.core.logger import get_logger


class DataChangeType(Enum):
    """数据变更类型枚举
    
    定义支持的数据变更事件类型。
    """
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()
    IMPORT = auto()
    EXPORT = auto()
    BATCH_CREATE = auto()
    BATCH_UPDATE = auto()
    BATCH_DELETE = auto()


@dataclass
class DataChangeEvent:
    """数据变更事件
    
    封装数据变更事件的信息。
    
    Attributes:
        change_type: 变更类型
        entity_type: 实体类型（如Student, Class等）
        entity_id: 实体ID
        old_data: 变更前的数据
        new_data: 变更后的数据
        timestamp: 事件发生时间
        source: 事件来源
        metadata: 额外元数据
    """
    change_type: DataChangeType
    entity_type: str
    entity_id: Optional[Any] = None
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    source: str = ""
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class Observer(ABC):
    """观察者抽象基类
    
    所有观察者的基类，定义更新接口。
    """
    
    @abstractmethod
    def update(self, event: DataChangeEvent) -> None:
        """接收数据变更通知
        
        Args:
            event: 数据变更事件
        """
        pass
    
    @abstractmethod
    def get_observer_name(self) -> str:
        """获取观察者名称
        
        Returns:
            观察者名称
        """
        pass


class Subject(ABC):
    """主题抽象基类
    
    定义主题的基本接口，用于管理观察者。
    """
    
    def __init__(self) -> None:
        """初始化主题"""
        self._observers: List[Observer] = []
        self._logger = get_logger(self.__class__.__name__)
    
    def attach(self, observer: Observer) -> None:
        """添加观察者
        
        Args:
            observer: 要添加的观察者
        """
        if observer not in self._observers:
            self._observers.append(observer)
            self._logger.debug(f"观察者 {observer.get_observer_name()} 已注册")
    
    def detach(self, observer: Observer) -> None:
        """移除观察者
        
        Args:
            observer: 要移除的观察者
        """
        if observer in self._observers:
            self._observers.remove(observer)
            self._logger.debug(f"观察者 {observer.get_observer_name()} 已移除")
    
    def notify(self, event: DataChangeEvent) -> None:
        """通知所有观察者
        
        Args:
            event: 数据变更事件
        """
        self._logger.debug(
            f"通知 {len(self._observers)} 个观察者: "
            f"{event.entity_type} {event.change_type.name}"
        )
        for observer in self._observers:
            try:
                observer.update(event)
            except Exception as e:
                self._logger.error(
                    f"通知观察者 {observer.get_observer_name()} 失败: {e}"
                )


class LoggingObserver(Observer):
    """日志观察者
    
    将数据变更事件记录到日志中。
    """
    
    def __init__(self) -> None:
        """初始化日志观察者"""
        self._logger = get_logger(self.__class__.__name__)
    
    def update(self, event: DataChangeEvent) -> None:
        """记录数据变更事件
        
        Args:
            event: 数据变更事件
        """
        self._logger.info(
            f"数据变更: {event.entity_type} "
            f"ID={event.entity_id} "
            f"操作={event.change_type.name} "
            f"来源={event.source}"
        )
    
    def get_observer_name(self) -> str:
        """获取观察者名称"""
        return "LoggingObserver"


class CacheInvalidationObserver(Observer):
    """缓存失效观察者
    
    在数据变更时使相关缓存失效。
    """
    
    def __init__(self) -> None:
        """初始化缓存失效观察者"""
        self._logger = get_logger(self.__class__.__name__)
        self._cache: Dict[str, Any] = {}
    
    def update(self, event: DataChangeEvent) -> None:
        """处理缓存失效
        
        Args:
            event: 数据变更事件
        """
        cache_key = f"{event.entity_type}:{event.entity_id}"
        if cache_key in self._cache:
            del self._cache[cache_key]
            self._logger.debug(f"缓存已失效: {cache_key}")
        
        # 清除相关列表缓存
        list_key = f"{event.entity_type}:list"
        if list_key in self._cache:
            del self._cache[list_key]
            self._logger.debug(f"列表缓存已失效: {list_key}")
    
    def get_observer_name(self) -> str:
        """获取观察者名称"""
        return "CacheInvalidationObserver"
    
    def set_cache(self, key: str, value: Any) -> None:
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        self._cache[key] = value
    
    def get_cache(self, key: str) -> Optional[Any]:
        """获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        return self._cache.get(key)


class NotificationObserver(Observer):
    """通知观察者
    
    在数据变更时发送通知。
    """
    
    def __init__(self) -> None:
        """初始化通知观察者"""
        self._logger = get_logger(self.__class__.__name__)
        self._handlers: Dict[DataChangeType, List[Callable]] = {}
    
    def register_handler(
        self,
        change_type: DataChangeType,
        handler: Callable[[DataChangeEvent], None]
    ) -> None:
        """注册事件处理器
        
        Args:
            change_type: 变更类型
            handler: 处理函数
        """
        if change_type not in self._handlers:
            self._handlers[change_type] = []
        self._handlers[change_type].append(handler)
        self._logger.debug(f"为 {change_type.name} 注册处理器")
    
    def update(self, event: DataChangeEvent) -> None:
        """处理通知
        
        Args:
            event: 数据变更事件
        """
        handlers = self._handlers.get(event.change_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                self._logger.error(f"执行处理器失败: {e}")
    
    def get_observer_name(self) -> str:
        """获取观察者名称"""
        return "NotificationObserver"


class DataChangeSubject(Subject):
    """数据变更主题
    
    管理数据变更事件的发布。
    """
    
    def __init__(self) -> None:
        """初始化数据变更主题"""
        super().__init__()
        self._logger = get_logger(self.__class__.__name__)
    
    def emit(
        self,
        change_type: DataChangeType,
        entity_type: str,
        entity_id: Optional[Any] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        source: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """发布数据变更事件
        
        Args:
            change_type: 变更类型
            entity_type: 实体类型
            entity_id: 实体ID
            old_data: 变更前的数据
            new_data: 变更后的数据
            source: 事件来源
            metadata: 额外元数据
        """
        event = DataChangeEvent(
            change_type=change_type,
            entity_type=entity_type,
            entity_id=entity_id,
            old_data=old_data,
            new_data=new_data,
            source=source,
            metadata=metadata
        )
        self.notify(event)


# 全局主题实例
_data_change_subject: Optional[DataChangeSubject] = None


def get_data_change_subject() -> DataChangeSubject:
    """获取数据变更主题单例
    
    Returns:
        DataChangeSubject: 数据变更主题实例
    """
    global _data_change_subject
    if _data_change_subject is None:
        _data_change_subject = DataChangeSubject()
    return _data_change_subject
