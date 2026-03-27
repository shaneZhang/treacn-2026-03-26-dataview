"""
数据访问对象基类模块

实现DAO层的基础功能，提供通用的CRUD操作。
"""

from typing import TypeVar, Generic, List, Optional, Dict, Any, Type
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update

from src.dao.database import get_database_manager
from src.core.exceptions import QueryException, NotFoundException
from src.core.logger import get_logger
from src.core.observer import (
    DataChangeType, get_data_change_subject, DataChangeEvent
)


T = TypeVar("T")


class BaseDAO(Generic[T], ABC):
    """数据访问对象基类
    
    提供通用的CRUD操作，支持观察者模式通知数据变更。
    
    Attributes:
        _model_class: ORM模型类
        _entity_name: 实体名称
        _logger: 日志记录器
    """
    
    def __init__(
        self,
        model_class: Type[T],
        entity_name: str,
        session: Optional[Session] = None
    ) -> None:
        """初始化DAO
        
        Args:
            model_class: ORM模型类
            entity_name: 实体名称（用于观察者通知）
            session: 可选的数据库会话（用于测试）
        """
        self._model_class = model_class
        self._entity_name = entity_name
        self._logger = get_logger(self.__class__.__name__)
        self._db_manager = get_database_manager()
        self._subject = get_data_change_subject()
        self._session = session
    
    def _get_session(self) -> Session:
        """获取数据库会话
        
        Returns:
            数据库会话
        """
        if self._session is not None:
            return self._session
        return self._db_manager.create_session()
    
    def _notify_change(
        self,
        change_type: DataChangeType,
        entity_id: Optional[Any] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        source: str = ""
    ) -> None:
        """通知数据变更
        
        Args:
            change_type: 变更类型
            entity_id: 实体ID
            old_data: 变更前的数据
            new_data: 变更后的数据
            source: 事件来源
        """
        try:
            self._subject.emit(
                change_type=change_type,
                entity_type=self._entity_name,
                entity_id=entity_id,
                old_data=old_data,
                new_data=new_data,
                source=source or self.__class__.__name__
            )
        except Exception as e:
            self._logger.error(f"通知数据变更失败: {e}")
    
    def create(self, data: Dict[str, Any]) -> T:
        """创建新记录
        
        Args:
            data: 记录数据
            
        Returns:
            创建的记录对象
            
        Raises:
            QueryException: 创建失败
        """
        session = self._get_session()
        try:
            entity = self._model_class(**data)
            session.add(entity)
            session.commit()
            session.refresh(entity)
            
            self._notify_change(
                change_type=DataChangeType.CREATE,
                entity_id=getattr(entity, 'id', None),
                new_data=data
            )
            
            self._logger.debug(f"创建{self._entity_name}成功: {getattr(entity, 'id', None)}")
            return entity
            
        except Exception as e:
            session.rollback()
            self._logger.error(f"创建{self._entity_name}失败: {e}")
            raise QueryException(
                message=f"创建{self._entity_name}失败: {str(e)}",
                error_code="CREATE_ERROR",
                details={"data": data}
            )
        finally:
            session.close()
    
    def create_many(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """批量创建记录
        
        Args:
            data_list: 记录数据列表
            
        Returns:
            创建的记录对象列表
            
        Raises:
            QueryException: 创建失败
        """
        session = self._get_session()
        try:
            entities = [self._model_class(**data) for data in data_list]
            session.add_all(entities)
            session.commit()
            
            for entity in entities:
                session.refresh(entity)
            
            self._notify_change(
                change_type=DataChangeType.BATCH_CREATE,
                new_data={"count": len(data_list)}
            )
            
            self._logger.debug(f"批量创建{self._entity_name}成功: {len(entities)}条")
            return entities
            
        except Exception as e:
            session.rollback()
            self._logger.error(f"批量创建{self._entity_name}失败: {e}")
            raise QueryException(
                message=f"批量创建{self._entity_name}失败: {str(e)}",
                error_code="BATCH_CREATE_ERROR",
                details={"count": len(data_list)}
            )
        finally:
            session.close()
    
    def get_by_id(self, entity_id: Any) -> Optional[T]:
        """根据ID获取记录
        
        Args:
            entity_id: 记录ID
            
        Returns:
            记录对象，不存在则返回None
        """
        session = self._get_session()
        try:
            result = session.get(self._model_class, entity_id)
            return result
        finally:
            session.close()
    
    def get_by_id_or_raise(self, entity_id: Any) -> T:
        """根据ID获取记录，不存在则抛出异常
        
        Args:
            entity_id: 记录ID
            
        Returns:
            记录对象
            
        Raises:
            NotFoundException: 记录不存在
        """
        entity = self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundException(
                message=f"{self._entity_name}不存在: ID={entity_id}",
                error_code="ENTITY_NOT_FOUND",
                details={"entity_type": self._entity_name, "id": entity_id}
            )
        return entity
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """获取所有记录
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            记录列表
        """
        session = self._get_session()
        try:
            stmt = select(self._model_class)
            
            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)
            
            result = session.execute(stmt)
            return list(result.scalars().all())
        finally:
            session.close()
    
    def update(self, entity_id: Any, data: Dict[str, Any]) -> T:
        """更新记录
        
        Args:
            entity_id: 记录ID
            data: 更新数据
            
        Returns:
            更新后的记录对象
            
        Raises:
            NotFoundException: 记录不存在
            QueryException: 更新失败
        """
        session = self._get_session()
        try:
            # 获取旧数据
            entity = session.get(self._model_class, entity_id)
            if entity is None:
                raise NotFoundException(
                    message=f"{self._entity_name}不存在: ID={entity_id}",
                    error_code="ENTITY_NOT_FOUND"
                )
            
            old_data = {
                col: getattr(entity, col) 
                for col in entity.__table__.columns.keys()
            }
            
            # 更新数据
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            
            session.commit()
            session.refresh(entity)
            
            self._notify_change(
                change_type=DataChangeType.UPDATE,
                entity_id=entity_id,
                old_data=old_data,
                new_data=data
            )
            
            self._logger.debug(f"更新{self._entity_name}成功: {entity_id}")
            return entity
            
        except NotFoundException:
            raise
        except Exception as e:
            session.rollback()
            self._logger.error(f"更新{self._entity_name}失败: {e}")
            raise QueryException(
                message=f"更新{self._entity_name}失败: {str(e)}",
                error_code="UPDATE_ERROR",
                details={"id": entity_id, "data": data}
            )
        finally:
            session.close()
    
    def delete(self, entity_id: Any) -> bool:
        """删除记录
        
        Args:
            entity_id: 记录ID
            
        Returns:
            是否删除成功
            
        Raises:
            NotFoundException: 记录不存在
        """
        session = self._get_session()
        try:
            entity = session.get(self._model_class, entity_id)
            if entity is None:
                raise NotFoundException(
                    message=f"{self._entity_name}不存在: ID={entity_id}",
                    error_code="ENTITY_NOT_FOUND"
                )
            
            old_data = {
                col: getattr(entity, col) 
                for col in entity.__table__.columns.keys()
            }
            
            session.delete(entity)
            session.commit()
            
            self._notify_change(
                change_type=DataChangeType.DELETE,
                entity_id=entity_id,
                old_data=old_data
            )
            
            self._logger.debug(f"删除{self._entity_name}成功: {entity_id}")
            return True
            
        except NotFoundException:
            raise
        except Exception as e:
            session.rollback()
            self._logger.error(f"删除{self._entity_name}失败: {e}")
            raise QueryException(
                message=f"删除{self._entity_name}失败: {str(e)}",
                error_code="DELETE_ERROR",
                details={"id": entity_id}
            )
        finally:
            session.close()
    
    def count(self) -> int:
        """获取记录总数
        
        Returns:
            记录总数
        """
        session = self._get_session()
        try:
            from sqlalchemy import func
            stmt = select(func.count()).select_from(self._model_class)
            result = session.execute(stmt)
            return result.scalar() or 0
        finally:
            session.close()
    
    @abstractmethod
    def get_by_condition(self, **kwargs: Any) -> List[T]:
        """根据条件查询记录
        
        Args:
            **kwargs: 查询条件
            
        Returns:
            记录列表
        """
        pass
