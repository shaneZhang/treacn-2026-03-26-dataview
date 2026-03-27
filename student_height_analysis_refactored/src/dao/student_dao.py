"""
学生数据访问对象模块

实现学生相关的数据访问操作。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from src.dao.base_dao import BaseDAO
from src.dao.models import Student, HeightRecord
from src.dao.database import get_database_manager
from src.core.exceptions import QueryException
from src.core.logger import get_logger


class StudentDAO(BaseDAO[Student]):
    """学生数据访问对象
    
    提供学生相关的数据访问操作。
    """
    
    def __init__(self, session: Optional[Session] = None) -> None:
        """初始化学生DAO
        
        Args:
            session: 可选的数据库会话（用于测试）
        """
        super().__init__(Student, "Student", session)
    
    def get_by_student_id(self, student_id: str) -> Optional[Student]:
        """根据学号获取学生
        
        Args:
            student_id: 学号
            
        Returns:
            学生对象，不存在则返回None
        """
        session = self._get_session()
        try:
            stmt = select(Student).where(Student.student_id == student_id)
            result = session.execute(stmt)
            return result.scalar_one_or_none()
        finally:
            session.close()
    
    def get_by_condition(
        self,
        grade: Optional[str] = None,
        gender: Optional[str] = None,
        age: Optional[int] = None,
        class_id: Optional[int] = None,
        bmi_category: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Student]:
        """根据条件查询学生
        
        Args:
            grade: 年级
            gender: 性别
            age: 年龄
            class_id: 班级ID
            bmi_category: BMI分类
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            学生列表
        """
        session = self._get_session()
        try:
            stmt = select(Student)
            
            # 构建查询条件
            conditions = []
            if grade:
                conditions.append(Student.grade == grade)
            if gender:
                conditions.append(Student.gender == gender)
            if age:
                conditions.append(Student.age == age)
            if class_id:
                conditions.append(Student.class_id == class_id)
            if bmi_category:
                conditions.append(Student.bmi_category == bmi_category)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            # 排序
            stmt = stmt.order_by(Student.grade, Student.student_id)
            
            # 分页
            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)
            
            result = session.execute(stmt)
            return list(result.scalars().all())
        finally:
            session.close()
    
    def get_by_grade(self, grade: str) -> List[Student]:
        """根据年级获取学生
        
        Args:
            grade: 年级
            
        Returns:
            学生列表
        """
        return self.get_by_condition(grade=grade)
    
    def get_by_gender(self, gender: str) -> List[Student]:
        """根据性别获取学生
        
        Args:
            gender: 性别
            
        Returns:
            学生列表
        """
        return self.get_by_condition(gender=gender)
    
    def get_statistics_by_grade(self) -> List[Dict[str, Any]]:
        """获取各年级统计信息
        
        Returns:
            各年级统计信息列表
        """
        import numpy as np
        session = self._get_session()
        try:
            # 使用Python计算标准差以兼容SQLite
            stmt = (
                select(
                    Student.grade,
                    func.count().label("count"),
                    func.avg(Student.height).label("avg_height"),
                    func.min(Student.height).label("min_height"),
                    func.max(Student.height).label("max_height"),
                    func.avg(Student.weight).label("avg_weight"),
                )
                .group_by(Student.grade)
                .order_by(Student.grade)
            )
            
            result = session.execute(stmt)
            stats = []
            for row in result:
                # 获取该年级的所有学生身高和体重用于计算标准差
                students = session.query(Student.height, Student.weight).filter(
                    Student.grade == row.grade
                ).all()
                heights = [s.height for s in students]
                weights = [s.weight for s in students]
                
                std_height = round(np.std(heights), 2) if heights else 0
                std_weight = round(np.std(weights), 2) if weights else 0
                
                stats.append({
                    "grade": row.grade,
                    "count": row.count,
                    "avg_height": round(row.avg_height, 2) if row.avg_height else 0,
                    "std_height": std_height,
                    "min_height": round(row.min_height, 2) if row.min_height else 0,
                    "max_height": round(row.max_height, 2) if row.max_height else 0,
                    "avg_weight": round(row.avg_weight, 2) if row.avg_weight else 0,
                    "std_weight": std_weight,
                })
            return stats
        finally:
            session.close()
    
    def get_statistics_by_gender(self) -> List[Dict[str, Any]]:
        """获取按性别和年级统计信息
        
        Returns:
            统计信息列表
        """
        import numpy as np
        session = self._get_session()
        try:
            # 使用Python计算标准差以兼容SQLite
            stmt = (
                select(
                    Student.grade,
                    Student.gender,
                    func.count().label("count"),
                    func.avg(Student.height).label("avg_height"),
                )
                .group_by(Student.grade, Student.gender)
                .order_by(Student.grade, Student.gender)
            )
            
            result = session.execute(stmt)
            stats = []
            for row in result:
                # 获取该年级性别的所有学生身高用于计算标准差
                students = session.query(Student.height).filter(
                    Student.grade == row.grade,
                    Student.gender == row.gender
                ).all()
                heights = [s.height for s in students]
                std_height = round(np.std(heights), 2) if heights else 0
                
                stats.append({
                    "grade": row.grade,
                    "gender": row.gender,
                    "count": row.count,
                    "avg_height": round(row.avg_height, 2) if row.avg_height else 0,
                    "std_height": std_height,
                })
            return stats
        finally:
            session.close()
    
    def get_bmi_distribution(self) -> Dict[str, int]:
        """获取BMI分布
        
        Returns:
            BMI分类到人数的映射
        """
        session = self._get_session()
        try:
            stmt = (
                select(Student.bmi_category, func.count().label("count"))
                .group_by(Student.bmi_category)
            )
            
            result = session.execute(stmt)
            return {row.bmi_category: row.count for row in result}
        finally:
            session.close()
    
    def get_bmi_distribution_by_grade(self) -> List[Dict[str, Any]]:
        """获取各年级BMI分布
        
        Returns:
            各年级BMI分布列表
        """
        session = self._get_session()
        try:
            stmt = (
                select(
                    Student.grade,
                    Student.bmi_category,
                    func.count().label("count")
                )
                .group_by(Student.grade, Student.bmi_category)
                .order_by(Student.grade, Student.bmi_category)
            )
            
            result = session.execute(stmt)
            distribution = []
            for row in result:
                distribution.append({
                    "grade": row.grade,
                    "bmi_category": row.bmi_category,
                    "count": row.count
                })
            return distribution
        finally:
            session.close()
    
    def get_height_percentiles(self, percentiles: List[int] = None) -> List[Dict[str, Any]]:
        """获取各年级身高百分位数
        
        Args:
            percentiles: 百分位数列表，默认[3, 10, 25, 50, 75, 90, 97]
            
        Returns:
            各年级身高百分位数
        """
        import numpy as np
        
        if percentiles is None:
            percentiles = [3, 10, 25, 50, 75, 90, 97]
        
        session = self._get_session()
        try:
            results = []
            grades = ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"]
            
            for grade in grades:
                row = {"grade": grade}
                
                # 获取该年级的所有身高数据
                students = session.query(Student.height).filter(
                    Student.grade == grade
                ).all()
                heights = sorted([s.height for s in students])
                
                if heights:
                    # 使用numpy计算百分位数
                    for p in percentiles:
                        value = np.percentile(heights, p)
                        row[f"P{p}"] = round(float(value), 1)
                else:
                    for p in percentiles:
                        row[f"P{p}"] = None
                
                results.append(row)
            
            return results
        finally:
            session.close()
    
    def get_growth_trend(self) -> List[Dict[str, Any]]:
        """获取生长趋势
        
        Returns:
            相邻年级身高增长数据
        """
        grade_stats = self.get_statistics_by_grade()
        
        if len(grade_stats) < 2:
            return []
        
        growth_data = []
        grade_order = ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"]
        
        # 按年级顺序排序
        grade_stats_dict = {s["grade"]: s for s in grade_stats}
        
        for i in range(1, len(grade_order)):
            prev_grade = grade_order[i-1]
            curr_grade = grade_order[i]
            
            if prev_grade in grade_stats_dict and curr_grade in grade_stats_dict:
                prev_height = grade_stats_dict[prev_grade]["avg_height"]
                curr_height = grade_stats_dict[curr_grade]["avg_height"]
                growth = curr_height - prev_height
                
                growth_data.append({
                    "grade_range": f"{prev_grade}到{curr_grade}",
                    "height_growth": round(growth, 2),
                    "growth_rate": round(growth / prev_height * 100, 2) if prev_height > 0 else 0
                })
        
        return growth_data
    
    def bulk_update_bmi(self) -> int:
        """批量更新所有学生的BMI
        
        Returns:
            更新的记录数
        """
        session = self._get_session()
        try:
            students = session.execute(select(Student)).scalars().all()
            
            for student in students:
                student.bmi = student.calculate_bmi()
                # BMI分类在模型中自动计算
            
            session.commit()
            self._logger.info(f"批量更新BMI完成: {len(students)}条记录")
            return len(students)
        except Exception as e:
            session.rollback()
            self._logger.error(f"批量更新BMI失败: {e}")
            raise QueryException(
                message=f"批量更新BMI失败: {str(e)}",
                error_code="BULK_UPDATE_BMI_ERROR"
            )
        finally:
            session.close()


class HeightRecordDAO(BaseDAO[HeightRecord]):
    """身高记录数据访问对象"""
    
    def __init__(self, session: Optional[Session] = None) -> None:
        """初始化身高记录DAO
        
        Args:
            session: 可选的数据库会话（用于测试）
        """
        super().__init__(HeightRecord, "HeightRecord", session)
    
    def get_by_condition(
        self,
        student_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[HeightRecord]:
        """根据条件查询身高记录
        
        Args:
            student_id: 学生ID
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            身高记录列表
        """
        session = self._get_session()
        try:
            stmt = select(HeightRecord)
            
            conditions = []
            if student_id:
                conditions.append(HeightRecord.student_id == student_id)
            if start_date:
                conditions.append(HeightRecord.record_date >= start_date)
            if end_date:
                conditions.append(HeightRecord.record_date <= end_date)
            
            if conditions:
                from sqlalchemy import and_
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(HeightRecord.record_date.desc())
            
            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)
            
            result = session.execute(stmt)
            return list(result.scalars().all())
        finally:
            session.close()
    
    def get_by_student(self, student_id: int) -> List[HeightRecord]:
        """获取学生的所有身高记录
        
        Args:
            student_id: 学生ID
            
        Returns:
            身高记录列表
        """
        return self.get_by_condition(student_id=student_id)
    
    def get_latest_by_student(self, student_id: int) -> Optional[HeightRecord]:
        """获取学生最新的身高记录
        
        Args:
            student_id: 学生ID
            
        Returns:
            最新的身高记录
        """
        session = self._get_session()
        try:
            stmt = (
                select(HeightRecord)
                .where(HeightRecord.student_id == student_id)
                .order_by(HeightRecord.record_date.desc())
                .limit(1)
            )
            result = session.execute(stmt)
            return result.scalar_one_or_none()
        finally:
            session.close()
