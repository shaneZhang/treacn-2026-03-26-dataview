"""初始数据库表结构

Revision ID: 001
Revises: 
Create Date: 2026-03-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级数据库 - 创建初始表结构"""
    # 创建班级表
    op.create_table(
        'classes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('class_name', sa.String(length=50), nullable=False),
        sa.Column('grade', sa.String(length=20), nullable=False),
        sa.Column('class_teacher', sa.String(length=50), nullable=True),
        sa.Column('student_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('class_name')
    )
    
    # 创建学生表
    op.create_table(
        'students',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('student_id', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('gender', sa.String(length=10), nullable=False),
        sa.Column('grade', sa.String(length=20), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=True),
        sa.Column('enrollment_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id')
    )
    
    # 创建身高记录表
    op.create_table(
        'height_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('record_date', sa.Date(), nullable=False),
        sa.Column('height', sa.Float(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('bmi', sa.Float(), nullable=False),
        sa.Column('bmi_category', sa.String(length=20), nullable=False),
        sa.Column('age_at_record', sa.Integer(), nullable=False),
        sa.Column('grade_at_record', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建标准身高表
    op.create_table(
        'standard_heights',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('grade', sa.String(length=20), nullable=False),
        sa.Column('gender', sa.String(length=10), nullable=False),
        sa.Column('standard_height', sa.Float(), nullable=False),
        sa.Column('height_range_min', sa.Float(), nullable=False),
        sa.Column('height_range_max', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('idx_students_grade', 'students', ['grade'])
    op.create_index('idx_students_gender', 'students', ['gender'])
    op.create_index('idx_height_records_student', 'height_records', ['student_id'])
    op.create_index('idx_height_records_date', 'height_records', ['record_date'])


def downgrade() -> None:
    """降级数据库 - 删除所有表"""
    op.drop_index('idx_height_records_date', 'height_records')
    op.drop_index('idx_height_records_student', 'height_records')
    op.drop_index('idx_students_gender', 'students')
    op.drop_index('idx_students_grade', 'students')
    
    op.drop_table('standard_heights')
    op.drop_table('height_records')
    op.drop_table('students')
    op.drop_table('classes')
