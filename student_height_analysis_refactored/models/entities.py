"""
数据模型定义

定义数据库表结构对应的ORM模型
"""
from datetime import date, datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, 
    ForeignKey, Enum as SQLEnum, Text
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declared_attr
import enum


class Base(DeclarativeBase):
    """SQLAlchemy基类"""
    
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class GenderEnum(enum.Enum):
    """性别枚举"""
    MALE = "男"
    FEMALE = "女"


class GradeEnum(enum.Enum):
    """年级枚举"""
    GRADE_1 = "一年级"
    GRADE_2 = "二年级"
    GRADE_3 = "三年级"
    GRADE_4 = "四年级"
    GRADE_5 = "五年级"
    GRADE_6 = "六年级"


class BMICategory(enum.Enum):
    """BMI分类枚举"""
    UNDERWEIGHT = "偏瘦"
    NORMAL = "正常"
    OVERWEIGHT = "超重"
    OBESE = "肥胖"


class TimestampMixin:
    """时间戳混入类"""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )


class Class(Base, TimestampMixin):
    """
    班级表
    
    Attributes:
        id: 班级ID（主键）
        class_name: 班级名称
        grade: 年级
        class_teacher: 班主任姓名
        student_count: 学生人数
        created_at: 创建时间
        updated_at: 更新时间
        students: 学生列表（关系）
    """
    
    __tablename__ = 'classes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    class_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    grade: Mapped[str] = mapped_column(String(20), nullable=False)
    class_teacher: Mapped[Optional[str]] = mapped_column(String(50))
    student_count: Mapped[int] = mapped_column(Integer, default=0)
    
    students: Mapped[List["Student"]] = relationship(
        "Student", 
        back_populates="class_info",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Class(id={self.id}, class_name='{self.class_name}', grade='{self.grade}')>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        result = super().to_dict()
        result['students_count'] = len(self.students) if self.students else 0
        return result


class Student(Base, TimestampMixin):
    """
    学生表
    
    Attributes:
        id: 学生ID（主键）
        student_id: 学号（唯一）
        name: 姓名
        gender: 性别
        grade: 年级
        age: 年龄
        class_id: 班级ID（外键）
        enrollment_date: 入学日期
        created_at: 创建时间
        updated_at: 更新时间
        class_info: 班级信息（关系）
        height_records: 身高记录列表（关系）
    """
    
    __tablename__ = 'students'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    grade: Mapped[str] = mapped_column(String(20), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    class_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey('classes.id', ondelete='SET NULL')
    )
    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    class_info: Mapped[Optional["Class"]] = relationship(
        "Class", 
        back_populates="students"
    )
    height_records: Mapped[List["HeightRecord"]] = relationship(
        "HeightRecord",
        back_populates="student",
        cascade="all, delete-orphan",
        order_by="HeightRecord.record_date.desc()"
    )
    
    def __repr__(self) -> str:
        return f"<Student(id={self.id}, student_id='{self.student_id}', name='{self.name}')>"
    
    def get_latest_record(self) -> Optional["HeightRecord"]:
        """
        获取最新的身高记录
        
        Returns:
            Optional[HeightRecord]: 最新的身高记录，如果没有则返回None
        """
        return self.height_records[0] if self.height_records else None


class HeightRecord(Base, TimestampMixin):
    """
    身高记录表
    
    Attributes:
        id: 记录ID（主键）
        student_id: 学生ID（外键）
        record_date: 记录日期
        height: 身高(cm)
        weight: 体重(kg)
        bmi: BMI指数
        bmi_category: BMI分类
        age_at_record: 记录时的年龄
        grade_at_record: 记录时的年级
        notes: 备注
        created_at: 创建时间
        updated_at: 更新时间
        student: 学生信息（关系）
    """
    
    __tablename__ = 'height_records'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey('students.id', ondelete='CASCADE'),
        nullable=False
    )
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    bmi: Mapped[float] = mapped_column(Float, nullable=False)
    bmi_category: Mapped[str] = mapped_column(String(20), nullable=False)
    age_at_record: Mapped[int] = mapped_column(Integer, nullable=False)
    grade_at_record: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="height_records"
    )
    
    def __repr__(self) -> str:
        return (
            f"<HeightRecord(id={self.id}, student_id={self.student_id}, "
            f"height={self.height}, date={self.record_date})>"
        )
    
    @staticmethod
    def calculate_bmi(height: float, weight: float) -> float:
        """
        计算BMI指数
        
        Args:
            height: 身高(cm)
            weight: 体重(kg)
        
        Returns:
            float: BMI指数
        
        Example:
            >>> bmi = HeightRecord.calculate_bmi(150.0, 40.0)
        """
        height_m = height / 100
        return round(weight / (height_m ** 2), 2)
    
    @staticmethod
    def classify_bmi(bmi: float, age: int) -> str:
        """
        根据BMI和年龄分类
        
        Args:
            bmi: BMI指数
            age: 年龄
        
        Returns:
            str: BMI分类
        
        Example:
            >>> category = HeightRecord.classify_bmi(16.5, 8)
        """
        if age < 9:
            if bmi < 14:
                return BMICategory.UNDERWEIGHT.value
            elif bmi < 18:
                return BMICategory.NORMAL.value
            elif bmi < 21:
                return BMICategory.OVERWEIGHT.value
            else:
                return BMICategory.OBESE.value
        else:
            if bmi < 15:
                return BMICategory.UNDERWEIGHT.value
            elif bmi < 19:
                return BMICategory.NORMAL.value
            elif bmi < 22:
                return BMICategory.OVERWEIGHT.value
            else:
                return BMICategory.OBESE.value


class StandardHeight(Base):
    """
    标准身高表
    
    存储各年级男女生的标准身高数据
    
    Attributes:
        id: 记录ID（主键）
        grade: 年级
        gender: 性别
        standard_height: 标准身高(cm)
        height_range_min: 身高范围最小值
        height_range_max: 身高范围最大值
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    __tablename__ = 'standard_heights'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    grade: Mapped[str] = mapped_column(String(20), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    standard_height: Mapped[float] = mapped_column(Float, nullable=False)
    height_range_min: Mapped[float] = mapped_column(Float, nullable=False)
    height_range_max: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return (
            f"<StandardHeight(grade='{self.grade}', gender='{self.gender}', "
            f"standard_height={self.standard_height})>"
        )
