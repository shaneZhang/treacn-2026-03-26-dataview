# 数据库设计文档

## 1. 数据库ER图

```
┌─────────────────────┐
│      classes        │
│  (班级表)           │
├─────────────────────┤
│ PK  id              │
│     class_name      │
│     grade           │
│     class_teacher   │
│     student_count   │
│     created_at      │
│     updated_at      │
└──────────┬──────────┘
           │
           │ 1:N
           │
┌──────────▼──────────┐         ┌─────────────────────┐
│     students        │         │   height_records    │
│  (学生表)           │         │   (身高记录表)      │
├─────────────────────┤         ├─────────────────────┤
│ PK  id              │         │ PK  id              │
│ UK  student_id      │         │ FK  student_id      │
│     name            │◄────────┤     record_date     │
│     gender          │   1:N   │     height          │
│     grade           │         │     weight          │
│     age             │         │     bmi             │
│ FK  class_id        │         │     bmi_category    │
│     enrollment_date │         │     age_at_record   │
│     created_at      │         │     grade_at_record │
│     updated_at      │         │     notes           │
└─────────────────────┘         │     created_at      │
                                │     updated_at      │
                                └─────────────────────┘

┌─────────────────────┐
│  standard_heights   │
│  (标准身高表)       │
├─────────────────────┤
│ PK  id              │
│     grade           │
│     gender          │
│     standard_height │
│     height_range_min│
│     height_range_max│
│     created_at      │
│     updated_at      │
└─────────────────────┘
```

## 2. 表结构详细设计

### 2.1 班级表 (classes)

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | 班级ID |
| class_name | VARCHAR(50) | NOT NULL, UNIQUE | 班级名称 |
| grade | VARCHAR(20) | NOT NULL | 年级 |
| class_teacher | VARCHAR(50) | NULL | 班主任姓名 |
| student_count | INTEGER | DEFAULT 0 | 学生人数 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

**索引：**
- PRIMARY KEY: id
- UNIQUE: class_name

### 2.2 学生表 (students)

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | 学生ID |
| student_id | VARCHAR(20) | NOT NULL, UNIQUE | 学号 |
| name | VARCHAR(50) | NOT NULL | 姓名 |
| gender | VARCHAR(10) | NOT NULL | 性别 |
| grade | VARCHAR(20) | NOT NULL | 年级 |
| age | INTEGER | NOT NULL | 年龄 |
| class_id | INTEGER | FOREIGN KEY, NULL | 班级ID |
| enrollment_date | DATE | NOT NULL | 入学日期 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

**索引：**
- PRIMARY KEY: id
- UNIQUE: student_id
- INDEX: idx_students_grade (grade)
- INDEX: idx_students_gender (gender)
- FOREIGN KEY: class_id REFERENCES classes(id) ON DELETE SET NULL

### 2.3 身高记录表 (height_records)

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | 记录ID |
| student_id | INTEGER | NOT NULL, FOREIGN KEY | 学生ID |
| record_date | DATE | NOT NULL | 记录日期 |
| height | FLOAT | NOT NULL | 身高(cm) |
| weight | FLOAT | NOT NULL | 体重(kg) |
| bmi | FLOAT | NOT NULL | BMI指数 |
| bmi_category | VARCHAR(20) | NOT NULL | BMI分类 |
| age_at_record | INTEGER | NOT NULL | 记录时年龄 |
| grade_at_record | VARCHAR(20) | NOT NULL | 记录时年级 |
| notes | TEXT | NULL | 备注 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

**索引：**
- PRIMARY KEY: id
- INDEX: idx_height_records_student (student_id)
- INDEX: idx_height_records_date (record_date)
- FOREIGN KEY: student_id REFERENCES students(id) ON DELETE CASCADE

### 2.4 标准身高表 (standard_heights)

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | 记录ID |
| grade | VARCHAR(20) | NOT NULL | 年级 |
| gender | VARCHAR(10) | NOT NULL | 性别 |
| standard_height | FLOAT | NOT NULL | 标准身高(cm) |
| height_range_min | FLOAT | NOT NULL | 身高范围最小值 |
| height_range_max | FLOAT | NOT NULL | 身高范围最大值 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

## 3. 数据库关系说明

### 3.1 主要关系

1. **班级-学生关系 (1:N)**
   - 一个班级可以有多个学生
   - 一个学生只能属于一个班级
   - 外键约束：ON DELETE SET NULL（班级删除时学生class_id置空）

2. **学生-身高记录关系 (1:N)**
   - 一个学生可以有多条身高记录
   - 一条身高记录只属于一个学生
   - 外键约束：ON DELETE CASCADE（学生删除时级联删除记录）

### 3.2 数据完整性

1. **实体完整性**
   - 所有表都有主键
   - 主键自动递增

2. **参照完整性**
   - 外键约束确保关联数据的有效性
   - 级联操作保证数据一致性

3. **域完整性**
   - NOT NULL约束确保必填字段
   - UNIQUE约束确保唯一性
   - 数据类型限制确保数据格式正确

## 4. 数据库迁移

### 4.1 使用Alembic进行数据库迁移

```bash
# 初始化迁移
alembic init migrations

# 生成迁移脚本
alembic revision --autogenerate -m "初始化数据库表结构"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 4.2 迁移脚本说明

迁移脚本位于 `migrations/versions/` 目录下，包含：
- `upgrade()`: 升级数据库的SQL操作
- `downgrade()`: 降级数据库的SQL操作

## 5. 性能优化建议

### 5.1 索引优化

- 在频繁查询的字段上建立索引（grade, gender, record_date等）
- 避免在低选择性字段上建立索引
- 定期分析索引使用情况

### 5.2 查询优化

- 使用连接池减少连接开销
- 合理使用JOIN避免N+1查询
- 对大数据量查询使用分页

### 5.3 存储优化

- 定期清理历史数据
- 对大表进行分区
- 合理设置字段长度

## 6. 数据安全

### 6.1 备份策略

- 定期全量备份
- 增量备份
- 异地备份

### 6.2 访问控制

- 使用最小权限原则
- 敏感数据加密存储
- 操作日志记录
