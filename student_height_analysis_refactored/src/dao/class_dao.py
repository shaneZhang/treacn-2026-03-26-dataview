"""
班级数据访问对象模块

实现班级相关的数据访问操作。
"""

from typing import List, Optional, Dict, Any

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from src.dao.base_dao import BaseDAO
from src.dao.models import ClassInfo, Student
from src.core.exceptions import QueryException


class ClassDAO(BaseDAO[ClassInfo]):
    """班级数据访问对象
    
    提供班级相关的数据访问操作。
    """
    
    def __init__(self, session: Optional[Session] = None) -> None:
        """初始化班级DAO
        
        Args:
            session: 可选的数据库会话（用于测试）
        """
        super().__init__(ClassInfo, "ClassInfo", session)
    
    def get_by_condition(
        self,
        grade: Optional[str] = None,
        class_number: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ClassInfo]:
        """根据条件查询班级
        
        Args:
            grade: 年级
            class_number: 班级编号
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            班级列表
        """
        session = self._get_session()
        try:
            stmt = select(ClassInfo)
            
            conditions = []
            if grade:
                conditions.append(ClassInfo.grade == grade)
            if class_number:
                conditions.append(ClassInfo.class_number == class_number)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(ClassInfo.grade, ClassInfo.class_number)
            
            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)
            
            result = session.execute(stmt)
            return list(result.scalars().all())
        finally:
            session.close()
    
    def get_by_grade(self, grade: str) -> List[ClassInfo]:
        """根据年级获取班级
        
        Args:
            grade: 年级
            
        Returns:
            班级列表
        """
        return self.get_by_condition(grade=grade)
    
    def get_by_grade_and_number(self, grade: str, class_number: int) -> Optional[ClassInfo]:
        """根据年级和班级编号获取班级
        
        Args:
            grade: 年级
            class_number: 班级编号
            
        Returns:
            班级对象，不存在则返回None
        """
        session = self._get_session()
        try:
            stmt = select(ClassInfo).where(
                and_(
                    ClassInfo.grade == grade,
                    ClassInfo.class_number == class_number
                )
            )
            result = session.execute(stmt)
            return result.scalar_one_or_none()
        finally:
            session.close()
    
    def update_student_count(self, class_id: int) -> int:
        """更新班级学生人数
        
        Args:
            class_id: 班级ID
            
        Returns:
            更新后的学生人数
        """
        session = self._get_session()
        try:
            # 统计学生人数
            count_stmt = select(func.count()).where(Student.class_id == class_id)
            count = session.execute(count_stmt).scalar() or 0
            
            # 更新班级
            class_info = session.get(ClassInfo, class_id)
            if class_info:
                class_info.student_count = count
                session.commit()
            
            return count
        except Exception as e:
            session.rollback()
            raise QueryException(
                message=f"更新班级学生人数失败: {str(e)}",
                error_code="UPDATE_CLASS_COUNT_ERROR"
            )
        finally:
            session.close()
    
    def get_statistics(self) -> List[Dict[str, Any]]:
        """获取班级统计信息
        
        Returns:
            班级统计信息列表
        """
        session = self._get_session()
        try:
            # 查询所有班级及其学生统计
            stmt = (
                select(
                    ClassInfo.id,
                    ClassInfo.grade,
                    ClassInfo.class_number,
                    ClassInfo.class_name,
                    func.count(Student.id).label("student_count"),
                    func.avg(Student.height).label("avg_height"),
                    func.avg(Student.weight).label("avg_weight"),
                )
                .outerjoin(Student, ClassInfo.id == Student.class_id)
                .group_by(ClassInfo.id)
                .order_by(ClassInfo.grade, ClassInfo.class_number)
            )
            
            result = session.execute(stmt)
            stats = []
            for row in result:
                stats.append({
                    "id": row.id,
                    "grade": row.grade,
                    "class_number": row.class_number,
                    "class_name": row.class_name,
                    "student_count": row.student_count,
                    "avg_height": round(row.avg_height, 2) if row.avg_height else 0,
                    "avg_weight": round(row.avg_weight, 2) if row.avg_weight else 0,
                })
            return stats
        finally:
            session.close()
