# 数据库 ER 图与表结构设计文档

## 1. 实体关系图 (ER Diagram)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据库 ER 图                                    │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
    │   class_info    │         │    students     │         │ height_records  │
    │   (班级信息表)   │◄───────│   (学生信息表)   │◄───────│  (身高记录表)    │
    ├─────────────────┤   1:N   ├─────────────────┤   1:N   ├─────────────────┤
    │ PK id           │         │ PK id           │         │ PK id           │
    │    grade        │         │    student_id   │         │ FK student_id   │
    │    class_number │         │    name         │         │    height       │
    │    class_name   │         │    gender       │         │    weight       │
    │    student_count│         │    grade        │         │    record_date  │
    │    created_at   │         │    age          │         │    age          │
    │    updated_at   │         │    height       │         │    notes        │
    └─────────────────┘         │    weight       │         │    created_at   │
                                │    bmi          │         └─────────────────┘
                                │    bmi_category │
                                │ FK class_id     │         ┌─────────────────┐
                                │    enrollment   │         │ statistics_     │
                                │    created_at   │         │   records       │
                                │    updated_at   │         ├─────────────────┤
                                └─────────────────┘         │ PK id           │
                                                           │    stat_type    │
                                                           │    dimension    │
                                                           │    dimension_val│
                                                           │    metric_name  │
                                                           │    metric_value │
                                                           │    sample_size  │
                                                           │    calculated_at│
                                                           │    created_at   │
                                                           └─────────────────┘

    ┌─────────────────┐
    │ import_export_  │
    │     logs        │
    │ (导入导出日志表) │
    ├─────────────────┤
    │ PK id           │
    │    operation    │
    │    file_path    │
    │    file_format  │
    │    record_count │
    │    status       │
    │    error_msg    │
    │    executed_by  │
    │    executed_at  │
    └─────────────────┘

## 2. 表结构详细设计

### 2.1 class_info (班级信息表)

存储班级基本信息，支持年级和班级的层级关系。

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|----------|------|--------|------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 班级唯一标识 |
| grade | VARCHAR(20) | NOT NULL, INDEX | - | 年级（一年级~六年级） |
| class_number | INTEGER | NOT NULL | - | 班级编号（1, 2, 3...） |
| class_name | VARCHAR(50) | NOT NULL | - | 班级名称（如：一年级1班） |
| student_count | INTEGER | - | 0 | 学生人数（冗余字段，用于快速查询） |
| created_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 更新时间 |

**索引**:
```sql
-- 唯一约束：年级+班级编号
CREATE UNIQUE INDEX uix_grade_class ON class_info(grade, class_number);

-- 年级索引
CREATE INDEX ix_class_grade ON class_info(grade);
```

**关系**:
- 一对多关系：一个班级有多个学生 (class_info.id → students.class_id)

---

### 2.2 students (学生信息表)

存储学生基本信息和身高体重数据，是系统的核心表。

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|----------|------|--------|------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 学生唯一标识 |
| student_id | VARCHAR(20) | UNIQUE, NOT NULL, INDEX | - | 学号（如：STU202400001） |
| name | VARCHAR(50) | NOT NULL | - | 学生姓名 |
| gender | VARCHAR(10) | NOT NULL, INDEX | - | 性别（男/女） |
| grade | VARCHAR(20) | NOT NULL, INDEX | - | 年级（一年级~六年级） |
| age | INTEGER | NOT NULL, INDEX | - | 年龄（6~12岁） |
| height | FLOAT | NOT NULL | - | 身高（厘米） |
| weight | FLOAT | NOT NULL | - | 体重（千克） |
| bmi | FLOAT | NOT NULL, INDEX | - | BMI指数（自动计算） |
| bmi_category | VARCHAR(20) | NOT NULL, INDEX | - | BMI分类（偏瘦/正常/超重/肥胖） |
| class_id | INTEGER | FOREIGN KEY | NULL | 班级ID（可为空） |
| enrollment_date | VARCHAR(10) | - | NULL | 入学日期（格式：YYYY-MM-DD） |
| created_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 更新时间 |

**索引**:
```sql
-- 学号唯一索引
CREATE UNIQUE INDEX ix_student_id ON students(student_id);

-- 年级+性别复合索引（常用查询条件）
CREATE INDEX ix_student_grade_gender ON students(grade, gender);

-- 年级+年龄复合索引
CREATE INDEX ix_student_grade_age ON students(grade, age);

-- BMI分类索引
CREATE INDEX ix_student_bmi_category ON students(bmi_category);
```

**关系**:
- 多对一关系：学生属于一个班级 (students.class_id → class_info.id)
- 一对多关系：学生有多条身高记录 (students.id → height_records.student_id)

**约束**:
- 身高范围：90cm ~ 180cm
- 体重范围：15kg ~ 80kg
- BMI自动计算：weight / (height/100)^2

---

### 2.3 height_records (身高记录表)

存储学生历史身高记录，用于追踪生长趋势。

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|----------|------|--------|------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 记录唯一标识 |
| student_id | INTEGER | FOREIGN KEY, NOT NULL, INDEX | - | 学生ID |
| height | FLOAT | NOT NULL | - | 身高（厘米） |
| weight | FLOAT | NOT NULL | - | 体重（千克） |
| record_date | VARCHAR(10) | NOT NULL, INDEX | - | 记录日期（格式：YYYY-MM-DD） |
| age | INTEGER | NOT NULL | - | 当时年龄 |
| notes | TEXT | - | NULL | 备注信息 |
| created_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
```sql
-- 学生ID+记录日期复合索引
CREATE INDEX ix_record_student_date ON height_records(student_id, record_date);
```

**关系**:
- 多对一关系：身高记录属于一个学生 (height_records.student_id → students.id)

**说明**:
- 支持级联删除：删除学生时自动删除相关身高记录
- 用于生成生长曲线和趋势分析

---

### 2.4 statistics_records (统计记录表)

存储各维度统计结果，避免重复计算，提高查询性能。

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|----------|------|--------|------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 记录唯一标识 |
| stat_type | VARCHAR(50) | NOT NULL, INDEX | - | 统计类型（如：grade_stats, gender_stats） |
| dimension | VARCHAR(50) | NOT NULL, INDEX | - | 统计维度（如：grade, gender） |
| dimension_value | VARCHAR(100) | NOT NULL, INDEX | - | 维度值（如：一年级, 男） |
| metric_name | VARCHAR(50) | NOT NULL | - | 指标名称（如：avg_height, count） |
| metric_value | FLOAT | NOT NULL | - | 指标值 |
| sample_size | INTEGER | - | 0 | 样本数量 |
| calculated_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 计算时间 |
| created_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
```sql
-- 唯一约束：统计类型+维度+维度值+指标名
CREATE UNIQUE INDEX uix_stat_dimension_metric 
ON statistics_records(stat_type, dimension, dimension_value, metric_name);

-- 统计类型+维度复合索引
CREATE INDEX ix_stat_type_dimension ON statistics_records(stat_type, dimension);
```

**说明**:
- 用于缓存统计结果
- 通过观察者模式在数据变更时自动失效
- 可定期重新计算更新

---

### 2.5 import_export_logs (导入导出日志表)

记录数据导入导出操作日志，便于审计和故障排查。

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|----------|------|--------|------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | - | 日志唯一标识 |
| operation_type | VARCHAR(20) | NOT NULL, INDEX | - | 操作类型（IMPORT/EXPORT） |
| file_path | VARCHAR(500) | NOT NULL | - | 文件路径 |
| file_format | VARCHAR(20) | NOT NULL | - | 文件格式（XLSX/CSV） |
| record_count | INTEGER | - | 0 | 记录数量 |
| status | VARCHAR(20) | NOT NULL, INDEX | - | 状态（SUCCESS/FAILED） |
| error_message | TEXT | - | NULL | 错误信息 |
| executed_by | VARCHAR(100) | - | NULL | 执行人 |
| executed_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 执行时间 |

**索引**:
```sql
-- 操作类型+状态复合索引
CREATE INDEX ix_ie_operation_status ON import_export_logs(operation_type, status);
```

---

## 3. 枚举类型定义

### 3.1 Gender (性别)
```python
class Gender(Enum):
    MALE = "男"
    FEMALE = "女"
```

### 3.2 BMICategory (BMI分类)
```python
class BMICategory(Enum):
    UNDERWEIGHT = "偏瘦"   # BMI < 14
    NORMAL = "正常"        # 14 <= BMI < 18
    OVERWEIGHT = "超重"    # 18 <= BMI < 21
    OBESE = "肥胖"         # BMI >= 21
```

### 3.3 Grade (年级)
```python
class Grade(Enum):
    GRADE_1 = "一年级"
    GRADE_2 = "二年级"
    GRADE_3 = "三年级"
    GRADE_4 = "四年级"
    GRADE_5 = "五年级"
    GRADE_6 = "六年级"
```

## 4. 关系说明

### 4.1 关系汇总

| 关系 | 类型 | 父表 | 子表 | 外键 | 级联操作 |
|------|------|------|------|------|----------|
| 班级-学生 | 一对多 | class_info | students | class_id | SET NULL |
| 学生-身高记录 | 一对多 | students | height_records | student_id | CASCADE DELETE |

### 4.2 关系图示

```
┌─────────────────────────────────────────────────────────────┐
│                        关系详细说明                          │
└─────────────────────────────────────────────────────────────┘

1. class_info (1) ────────< (N) students
   - 一个班级可以有多个学生
   - 学生可以不指定班级（class_id可为NULL）
   - 删除班级时，学生的class_id设为NULL

2. students (1) ────────< (N) height_records
   - 一个学生可以有多条身高记录
   - 身高记录必须属于一个学生
   - 删除学生时，级联删除相关身高记录

3. students ──────── statistics_records (无直接关系)
   - 统计记录是计算结果的缓存
   - 通过观察者模式维护数据一致性
```

## 5. 数据库规范化

### 5.1 范式检查

| 范式 | 说明 | 符合情况 |
|------|------|----------|
| 第一范式 (1NF) | 所有字段原子性 | ✓ 所有字段不可再分 |
| 第二范式 (2NF) | 消除部分依赖 | ✓ 所有非主键字段完全依赖于主键 |
| 第三范式 (3NF) | 消除传递依赖 | ✓ 无传递依赖 |

### 5.2 反规范化设计

**student_count 冗余字段**:
- 位置：class_info.student_count
- 原因：避免频繁COUNT查询
- 维护：通过观察者模式在增删学生时自动更新

**bmi 和 bmi_category 字段**:
- 位置：students.bmi, students.bmi_category
- 原因：避免频繁计算
- 维护：在插入/更新时自动计算

## 6. 数据库迁移 (Alembic)

### 6.1 初始化迁移

```bash
# 初始化Alembic
alembic init alembic

# 创建初始迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

### 6.2 迁移脚本示例

```python
"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2026-03-27

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 创建班级表
    op.create_table(
        'class_info',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('grade', sa.String(20), nullable=False),
        sa.Column('class_number', sa.Integer(), nullable=False),
        sa.Column('class_name', sa.String(50), nullable=False),
        sa.Column('student_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # 创建唯一约束
    op.create_unique_constraint(
        'uix_grade_class', 'class_info', ['grade', 'class_number']
    )
    
    # 创建学生表
    op.create_table(
        'students',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('gender', sa.String(10), nullable=False),
        sa.Column('grade', sa.String(20), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('height', sa.Float(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('bmi', sa.Float(), nullable=False),
        sa.Column('bmi_category', sa.String(20), nullable=False),
        sa.Column('class_id', sa.Integer(), sa.ForeignKey('class_info.id')),
        sa.Column('enrollment_date', sa.String(10)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # 创建索引
    op.create_index('ix_student_id', 'students', ['student_id'])
    op.create_index('ix_student_grade_gender', 'students', ['grade', 'gender'])
    op.create_index('ix_student_bmi_category', 'students', ['bmi_category'])

def downgrade():
    op.drop_table('students')
    op.drop_table('class_info')
```

## 7. 性能优化建议

### 7.1 索引优化
- 所有外键字段自动创建索引
- 常用查询条件字段创建复合索引
- 避免过多索引影响写入性能

### 7.2 查询优化
- 使用统计记录表缓存复杂计算
- 分页查询避免大数据量返回
- 使用连接池减少连接开销

### 7.3 数据归档
- 历史身高记录可定期归档
- 导入导出日志可定期清理
- 统计记录可定期重新计算
