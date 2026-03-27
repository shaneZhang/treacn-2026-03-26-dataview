"""
数据库模型模块

定义SQLAlchemy ORM模型，包括学生、班级、统计记录等表结构。
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, 
    ForeignKey, Enum, Index, UniqueConstraint, Text
)
from sqlalchemy.orm import relationship, declarative_base, Mapped, mapped_column
from sqlalchemy.sql import func

# 创建基类
Base = declarative_base()


class Gender(PyEnum):
    """性别枚举"""
    MALE = "男"
    FEMALE = "女"


class BMICategory(PyEnum):
    """BMI分类枚举"""
    UNDERWEIGHT = "偏瘦"
    NORMAL = "正常"
    OVERWEIGHT = "超重"
    OBESE = "肥胖"


class Grade(PyEnum):
    """年级枚举"""
    GRADE_1 = "一年级"
    GRADE_2 = "二年级"
    GRADE_3 = "三年级"
    GRADE_4 = "四年级"
    GRADE_5 = "五年级"
    GRADE_6 = "六年级"


class ClassInfo(Base):
    """班级信息表
    
    存储班级基本信息。
    
    Attributes:
        id: 班级ID（主键）
        grade: 年级
        class_number: 班级编号
        class_name: 班级名称
        student_count: 学生人数
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    __tablename__ = "class_info"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    grade: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    class_number: Mapped[int] = mapped_column(Integer, nullable=False)
    class_name: Mapped[str] = mapped_column(String(50), nullable=False)
    student_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    
    # 关系
    students: Mapped[List["Student"]] = relationship(
        "Student", back_populates="class_info", lazy="dynamic"
    )
    
    __table_args__ = (
        UniqueConstraint('grade', 'class_number', name='uix_grade_class'),
        Index('ix_class_grade', 'grade'),
    )
    
    def __repr__(self) -> str:
        return f"<ClassInfo(id={self.id}, grade={self.grade}, class_number={self.class_number})>"


class Student(Base):
    """学生信息表
    
    存储学生基本信息和身高体重数据。
    
    Attributes:
        id: 学生ID（主键）
        student_id: 学号（唯一）
        name: 姓名
        gender: 性别
        grade: 年级
        age: 年龄
        height: 身高（厘米）
        weight: 体重（千克）
        bmi: BMI指数
        bmi_category: BMI分类
        class_id: 班级ID（外键）
        enrollment_date: 入学日期
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    __tablename__ = "students"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    grade: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    bmi: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    bmi_category: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    class_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("class_info.id"), nullable=True
    )
    enrollment_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    
    # 关系
    class_info: Mapped[Optional["ClassInfo"]] = relationship(
        "ClassInfo", back_populates="students"
    )
    height_records: Mapped[List["HeightRecord"]] = relationship(
        "HeightRecord", back_populates="student", lazy="dynamic", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('ix_student_grade_gender', 'grade', 'gender'),
        Index('ix_student_grade_age', 'grade', 'age'),
        Index('ix_student_bmi_category', 'bmi_category'),
    )
    
    def __repr__(self) -> str:
        return f"<Student(id={self.id}, student_id={self.student_id}, name={self.name})>"
    
    def calculate_bmi(self) -> float:
        """计算BMI
        
        Returns:
            BMI值
        """
        if self.height <= 0:
            return 0.0
        return round(self.weight / ((self.height / 100) ** 2), 2)
    
    def classify_bmi(self) -> str:
        """根据BMI分类
        
        Returns:
            BMI分类字符串
        """
        if self.bmi < 14:
            return BMICategory.UNDERWEIGHT.value
        elif self.bmi < 18:
            return BMICategory.NORMAL.value
        elif self.bmi < 21:
            return BMICategory.OVERWEIGHT.value
        else:
            return BMICategory.OBESE.value


class HeightRecord(Base):
    """身高记录表
    
    存储学生历史身高记录，用于追踪生长趋势。
    
    Attributes:
        id: 记录ID（主键）
        student_id: 学生ID（外键）
        height: 身高（厘米）
        weight: 体重（千克）
        record_date: 记录日期
        age: 年龄
        notes: 备注
        created_at: 创建时间
    """
    
    __tablename__ = "height_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id"), nullable=False, index=True
    )
    height: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    record_date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    
    # 关系
    student: Mapped["Student"] = relationship("Student", back_populates="height_records")
    
    __table_args__ = (
        Index('ix_record_student_date', 'student_id', 'record_date'),
    )
    
    def __repr__(self) -> str:
        return f"<HeightRecord(id={self.id}, student_id={self.student_id}, height={self.height})>"


class StatisticsRecord(Base):
    """统计记录表
    
    存储各维度统计结果，避免重复计算。
    
    Attributes:
        id: 记录ID（主键）
        stat_type: 统计类型
        dimension: 统计维度
        dimension_value: 维度值
        metric_name: 指标名称
        metric_value: 指标值
        sample_size: 样本数量
        calculated_at: 计算时间
        created_at: 创建时间
    """
    
    __tablename__ = "statistics_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stat_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    dimension: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    dimension_value: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(50), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    
    __table_args__ = (
        UniqueConstraint(
            'stat_type', 'dimension', 'dimension_value', 'metric_name',
            name='uix_stat_dimension_metric'
        ),
        Index('ix_stat_type_dimension', 'stat_type', 'dimension'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<StatisticsRecord(id={self.id}, type={self.stat_type}, "
            f"dimension={self.dimension}, metric={self.metric_name})>"
        )


class ImportExportLog(Base):
    """导入导出日志表
    
    记录数据导入导出操作日志。
    
    Attributes:
        id: 日志ID（主键）
        operation_type: 操作类型（导入/导出）
        file_path: 文件路径
        file_format: 文件格式
        record_count: 记录数量
        status: 状态（成功/失败）
        error_message: 错误信息
        executed_by: 执行人
        executed_at: 执行时间
    """
    
    __tablename__ = "import_export_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operation_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_format: Mapped[str] = mapped_column(String(20), nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    executed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    
    __table_args__ = (
        Index('ix_ie_operation_status', 'operation_type', 'status'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<ImportExportLog(id={self.id}, type={self.operation_type}, "
            f"status={self.status})>"
        )


# 数据库版本信息表（用于Alembic）
class AlembicVersion(Base):
    """Alembic版本表
    
    存储数据库迁移版本信息。
    """
    
    __tablename__ = "alembic_version"
    
    version_num: Mapped[str] = mapped_column(String(32), primary_key=True)
