"""
数据访问层（DAO）

实现学生数据的CRUD操作
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from models import Student, HeightRecord, Class, StandardHeight
from utils import (
    StudentNotFoundException, 
    RecordNotFoundException,
    DatabaseQueryException,
    InvalidDataException,
    DuplicateDataException,
    get_logger
)
from core.database import DatabaseFactory
from core.observer import EventManager, EventType


class StudentDAO:
    """
    学生数据访问对象
    
    提供学生数据的CRUD操作
    
    Example:
        >>> dao = StudentDAO()
        >>> student = dao.get_by_id(1)
    """
    
    def __init__(self, session: Optional[Session] = None) -> None:
        """
        初始化学生DAO
        
        Args:
            session: 数据库会话，如果为None则自动创建
        """
        self.session = session
        self.logger = get_logger(__name__)
        self.event_manager = EventManager.get_instance()
    
    def _get_session(self) -> Session:
        """
        获取数据库会话
        
        Returns:
            Session: 数据库会话
        """
        if self.session:
            return self.session
        return DatabaseFactory.get_instance().get_session()
    
    def create(self, student_data: Dict[str, Any]) -> Student:
        """
        创建学生记录
        
        Args:
            student_data: 学生数据字典
        
        Returns:
            Student: 创建的学生对象
        
        Raises:
            DuplicateDataException: 学号已存在
            InvalidDataException: 数据验证失败
        
        Example:
            >>> student = dao.create({
            ...     'student_id': '10001',
            ...     'name': '张三',
            ...     'gender': '男',
            ...     'grade': '三年级',
            ...     'age': 9,
            ...     'enrollment_date': date(2022, 9, 1)
            ... })
        """
        session = self._get_session()
        
        try:
            existing = session.query(Student).filter(
                Student.student_id == student_data['student_id']
            ).first()
            
            if existing:
                raise DuplicateDataException(
                    f"学号 {student_data['student_id']} 已存在"
                )
            
            student = Student(**student_data)
            session.add(student)
            
            if not self.session:
                session.commit()
                session.refresh(student)
            else:
                session.flush()
            
            self.logger.info(f"学生创建成功: {student.student_id}")
            
            self.event_manager.emit(
                EventType.STUDENT_CREATED,
                {'student_id': student.id, 'student_number': student.student_id},
                source='StudentDAO'
            )
            
            return student
            
        except Exception as e:
            if not self.session:
                session.rollback()
            if isinstance(e, (DuplicateDataException, InvalidDataException)):
                raise
            self.logger.error(f"创建学生失败: {e}")
            raise DatabaseQueryException(f"创建学生失败: {e}")
    
    def get_by_id(self, student_id: int) -> Student:
        """
        根据ID获取学生
        
        Args:
            student_id: 学生ID
        
        Returns:
            Student: 学生对象
        
        Raises:
            StudentNotFoundException: 学生不存在
        
        Example:
            >>> student = dao.get_by_id(1)
        """
        session = self._get_session()
        
        try:
            student = session.query(Student).filter(
                Student.id == student_id
            ).first()
            
            if not student:
                raise StudentNotFoundException(
                    f"ID为 {student_id} 的学生不存在"
                )
            
            return student
            
        except StudentNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"查询学生失败: {e}")
            raise DatabaseQueryException(f"查询学生失败: {e}")
    
    def get_by_student_number(self, student_number: str) -> Student:
        """
        根据学号获取学生
        
        Args:
            student_number: 学号
        
        Returns:
            Student: 学生对象
        
        Raises:
            StudentNotFoundException: 学生不存在
        
        Example:
            >>> student = dao.get_by_student_number('10001')
        """
        session = self._get_session()
        
        try:
            student = session.query(Student).filter(
                Student.student_id == student_number
            ).first()
            
            if not student:
                raise StudentNotFoundException(
                    f"学号为 {student_number} 的学生不存在"
                )
            
            return student
            
        except StudentNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"查询学生失败: {e}")
            raise DatabaseQueryException(f"查询学生失败: {e}")
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        grade: Optional[str] = None,
        gender: Optional[str] = None
    ) -> List[Student]:
        """
        获取所有学生（支持分页和过滤）
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数
            grade: 年级过滤
            gender: 性别过滤
        
        Returns:
            List[Student]: 学生列表
        
        Example:
            >>> students = dao.get_all(skip=0, limit=10, grade='三年级')
        """
        session = self._get_session()
        
        try:
            query = session.query(Student)
            
            if grade:
                query = query.filter(Student.grade == grade)
            if gender:
                query = query.filter(Student.gender == gender)
            
            students = query.offset(skip).limit(limit).all()
            return students
            
        except Exception as e:
            self.logger.error(f"查询学生列表失败: {e}")
            raise DatabaseQueryException(f"查询学生列表失败: {e}")
    
    def update(self, student_id: int, update_data: Dict[str, Any]) -> Student:
        """
        更新学生信息
        
        Args:
            student_id: 学生ID
            update_data: 更新数据字典
        
        Returns:
            Student: 更新后的学生对象
        
        Raises:
            StudentNotFoundException: 学生不存在
        
        Example:
            >>> student = dao.update(1, {'age': 10})
        """
        session = self._get_session()
        
        try:
            student = self.get_by_id(student_id)
            
            for key, value in update_data.items():
                if hasattr(student, key):
                    setattr(student, key, value)
            
            student.updated_at = datetime.now()
            
            if not self.session:
                session.commit()
            
            self.logger.info(f"学生信息更新成功: {student_id}")
            
            self.event_manager.emit(
                EventType.STUDENT_UPDATED,
                {'student_id': student_id},
                source='StudentDAO'
            )
            
            return student
            
        except StudentNotFoundException:
            raise
        except Exception as e:
            if not self.session:
                session.rollback()
            self.logger.error(f"更新学生失败: {e}")
            raise DatabaseQueryException(f"更新学生失败: {e}")
    
    def delete(self, student_id: int) -> bool:
        """
        删除学生
        
        Args:
            student_id: 学生ID
        
        Returns:
            bool: 是否删除成功
        
        Raises:
            StudentNotFoundException: 学生不存在
        
        Example:
            >>> success = dao.delete(1)
        """
        session = self._get_session()
        
        try:
            student = self.get_by_id(student_id)
            
            session.delete(student)
            
            if not self.session:
                session.commit()
            
            self.logger.info(f"学生删除成功: {student_id}")
            
            self.event_manager.emit(
                EventType.STUDENT_DELETED,
                {'student_id': student_id},
                source='StudentDAO'
            )
            
            return True
            
        except StudentNotFoundException:
            raise
        except Exception as e:
            if not self.session:
                session.rollback()
            self.logger.error(f"删除学生失败: {e}")
            raise DatabaseQueryException(f"删除学生失败: {e}")
    
    def count(
        self, 
        grade: Optional[str] = None,
        gender: Optional[str] = None
    ) -> int:
        """
        统计学生数量
        
        Args:
            grade: 年级过滤
            gender: 性别过滤
        
        Returns:
            int: 学生数量
        
        Example:
            >>> count = dao.count(grade='三年级')
        """
        session = self._get_session()
        
        try:
            query = session.query(func.count(Student.id))
            
            if grade:
                query = query.filter(Student.grade == grade)
            if gender:
                query = query.filter(Student.gender == gender)
            
            return query.scalar() or 0
            
        except Exception as e:
            self.logger.error(f"统计学生数量失败: {e}")
            raise DatabaseQueryException(f"统计学生数量失败: {e}")


class HeightRecordDAO:
    """
    身高记录数据访问对象
    
    提供身高记录的CRUD操作
    
    Example:
        >>> dao = HeightRecordDAO()
        >>> records = dao.get_by_student_id(1)
    """
    
    def __init__(self, session: Optional[Session] = None) -> None:
        """
        初始化身高记录DAO
        
        Args:
            session: 数据库会话
        """
        self.session = session
        self.logger = get_logger(__name__)
        self.event_manager = EventManager.get_instance()
    
    def _get_session(self) -> Session:
        """获取数据库会话"""
        if self.session:
            return self.session
        return DatabaseFactory.get_instance().get_session()
    
    def create(self, record_data: Dict[str, Any]) -> HeightRecord:
        """
        创建身高记录
        
        Args:
            record_data: 记录数据字典
        
        Returns:
            HeightRecord: 创建的记录对象
        
        Example:
            >>> record = dao.create({
            ...     'student_id': 1,
            ...     'record_date': date.today(),
            ...     'height': 130.5,
            ...     'weight': 28.0,
            ...     'age_at_record': 9,
            ...     'grade_at_record': '三年级'
            ... })
        """
        session = self._get_session()
        
        try:
            height = record_data['height']
            weight = record_data['weight']
            age = record_data['age_at_record']
            
            bmi = HeightRecord.calculate_bmi(height, weight)
            bmi_category = HeightRecord.classify_bmi(bmi, age)
            
            record_data['bmi'] = bmi
            record_data['bmi_category'] = bmi_category
            
            record = HeightRecord(**record_data)
            session.add(record)
            
            if not self.session:
                session.commit()
                session.refresh(record)
            else:
                session.flush()
            
            self.logger.info(
                f"身高记录创建成功: 学生ID={record.student_id}, "
                f"身高={height}cm"
            )
            
            self.event_manager.emit(
                EventType.RECORD_CREATED,
                {'record_id': record.id, 'student_id': record.student_id},
                source='HeightRecordDAO'
            )
            
            return record
            
        except Exception as e:
            if not self.session:
                session.rollback()
            self.logger.error(f"创建身高记录失败: {e}")
            raise DatabaseQueryException(f"创建身高记录失败: {e}")
    
    def get_by_id(self, record_id: int) -> HeightRecord:
        """
        根据ID获取身高记录
        
        Args:
            record_id: 记录ID
        
        Returns:
            HeightRecord: 记录对象
        
        Raises:
            RecordNotFoundException: 记录不存在
        """
        session = self._get_session()
        
        try:
            record = session.query(HeightRecord).filter(
                HeightRecord.id == record_id
            ).first()
            
            if not record:
                raise RecordNotFoundException(
                    f"ID为 {record_id} 的身高记录不存在"
                )
            
            return record
            
        except RecordNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"查询身高记录失败: {e}")
            raise DatabaseQueryException(f"查询身高记录失败: {e}")
    
    def get_by_student_id(
        self, 
        student_id: int,
        limit: Optional[int] = None
    ) -> List[HeightRecord]:
        """
        获取学生的所有身高记录
        
        Args:
            student_id: 学生ID
            limit: 返回记录数限制
        
        Returns:
            List[HeightRecord]: 记录列表
        """
        session = self._get_session()
        
        try:
            query = session.query(HeightRecord).filter(
                HeightRecord.student_id == student_id
            ).order_by(HeightRecord.record_date.desc())
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
            
        except Exception as e:
            self.logger.error(f"查询学生身高记录失败: {e}")
            raise DatabaseQueryException(f"查询学生身高记录失败: {e}")
    
    def get_latest_by_student(self, student_id: int) -> Optional[HeightRecord]:
        """
        获取学生最新的身高记录
        
        Args:
            student_id: 学生ID
        
        Returns:
            Optional[HeightRecord]: 最新记录，不存在则返回None
        """
        records = self.get_by_student_id(student_id, limit=1)
        return records[0] if records else None
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        grade: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[HeightRecord]:
        """
        获取所有身高记录（支持分页和过滤）
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数
            grade: 年级过滤
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            List[HeightRecord]: 记录列表
        """
        session = self._get_session()
        
        try:
            query = session.query(HeightRecord)
            
            if grade:
                query = query.filter(HeightRecord.grade_at_record == grade)
            if start_date:
                query = query.filter(HeightRecord.record_date >= start_date)
            if end_date:
                query = query.filter(HeightRecord.record_date <= end_date)
            
            records = query.offset(skip).limit(limit).all()
            return records
            
        except Exception as e:
            self.logger.error(f"查询身高记录列表失败: {e}")
            raise DatabaseQueryException(f"查询身高记录列表失败: {e}")
    
    def update(self, record_id: int, update_data: Dict[str, Any]) -> HeightRecord:
        """
        更新身高记录
        
        Args:
            record_id: 记录ID
            update_data: 更新数据字典
        
        Returns:
            HeightRecord: 更新后的记录对象
        """
        session = self._get_session()
        
        try:
            record = self.get_by_id(record_id)
            
            for key, value in update_data.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            
            if 'height' in update_data or 'weight' in update_data:
                record.bmi = HeightRecord.calculate_bmi(
                    record.height, record.weight
                )
                record.bmi_category = HeightRecord.classify_bmi(
                    record.bmi, record.age_at_record
                )
            
            record.updated_at = datetime.now()
            
            if not self.session:
                session.commit()
            
            self.logger.info(f"身高记录更新成功: {record_id}")
            
            self.event_manager.emit(
                EventType.RECORD_UPDATED,
                {'record_id': record_id},
                source='HeightRecordDAO'
            )
            
            return record
            
        except RecordNotFoundException:
            raise
        except Exception as e:
            if not self.session:
                session.rollback()
            self.logger.error(f"更新身高记录失败: {e}")
            raise DatabaseQueryException(f"更新身高记录失败: {e}")
    
    def delete(self, record_id: int) -> bool:
        """
        删除身高记录
        
        Args:
            record_id: 记录ID
        
        Returns:
            bool: 是否删除成功
        """
        session = self._get_session()
        
        try:
            record = self.get_by_id(record_id)
            
            session.delete(record)
            
            if not self.session:
                session.commit()
            
            self.logger.info(f"身高记录删除成功: {record_id}")
            
            self.event_manager.emit(
                EventType.RECORD_DELETED,
                {'record_id': record_id},
                source='HeightRecordDAO'
            )
            
            return True
            
        except RecordNotFoundException:
            raise
        except Exception as e:
            if not self.session:
                session.rollback()
            self.logger.error(f"删除身高记录失败: {e}")
            raise DatabaseQueryException(f"删除身高记录失败: {e}")


class ClassDAO:
    """班级数据访问对象"""
    
    def __init__(self, session: Optional[Session] = None) -> None:
        self.session = session
        self.logger = get_logger(__name__)
    
    def _get_session(self) -> Session:
        if self.session:
            return self.session
        return DatabaseFactory.get_instance().get_session()
    
    def create(self, class_data: Dict[str, Any]) -> Class:
        """创建班级"""
        session = self._get_session()
        
        try:
            class_obj = Class(**class_data)
            session.add(class_obj)
            
            if not self.session:
                session.commit()
            
            self.logger.info(f"班级创建成功: {class_obj.class_name}")
            return class_obj
            
        except Exception as e:
            if not self.session:
                session.rollback()
            self.logger.error(f"创建班级失败: {e}")
            raise DatabaseQueryException(f"创建班级失败: {e}")
    
    def get_all(self) -> List[Class]:
        """获取所有班级"""
        session = self._get_session()
        
        try:
            return session.query(Class).all()
        except Exception as e:
            self.logger.error(f"查询班级列表失败: {e}")
            raise DatabaseQueryException(f"查询班级列表失败: {e}")


class StandardHeightDAO:
    """标准身高达数据访问对象"""
    
    def __init__(self, session: Optional[Session] = None) -> None:
        self.session = session
        self.logger = get_logger(__name__)
    
    def _get_session(self) -> Session:
        if self.session:
            return self.session
        return DatabaseFactory.get_instance().get_session()
    
    def get_by_grade_and_gender(
        self, 
        grade: str, 
        gender: str
    ) -> Optional[StandardHeight]:
        """根据年级和性别获取标准身高"""
        session = self._get_session()
        
        try:
            return session.query(StandardHeight).filter(
                and_(
                    StandardHeight.grade == grade,
                    StandardHeight.gender == gender
                )
            ).first()
        except Exception as e:
            self.logger.error(f"查询标准身高失败: {e}")
            raise DatabaseQueryException(f"查询标准身高失败: {e}")
    
    def get_all(self) -> List[StandardHeight]:
        """获取所有标准身高数据"""
        session = self._get_session()
        
        try:
            return session.query(StandardHeight).all()
        except Exception as e:
            self.logger.error(f"查询标准身高列表失败: {e}")
            raise DatabaseQueryException(f"查询标准身高列表失败: {e}")
