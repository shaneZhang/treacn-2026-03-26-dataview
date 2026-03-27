# 架构设计文档

## 1. 系统概述

### 1.1 项目简介
小学生身高数据分析与可视化系统 v2.0 是一个基于分层架构的数据分析平台，用于分析小学各年级学生的身高数据，提供统计分析、生长趋势分析和数据可视化功能。

### 1.2 架构演进
- **v1.0**: 单体脚本模式，数据存储为本地Excel文件
- **v2.0**: 分层架构，支持SQLite/PostgreSQL数据库，应用多种设计模式

## 2. 架构设计

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                      表现层 (Presentation)                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  HeightVisualizer                                      │  │
│  │  - ChartBase (抽象基类)                                 │  │
│  │  - HeightByGradeChart                                  │  │
│  │  - HeightByGenderChart                                 │  │
│  │  - HeightDistributionChart                             │  │
│  │  - BoxPlotByGradeChart                                 │  │
│  │  - GrowthTrendChart                                    │  │
│  │  - BMIDistributionChart                                │  │
│  │  - HeightHeatmapChart                                  │  │
│  │  - ScatterAgeHeightChart                               │  │
│  └───────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      业务逻辑层 (Service)                     │
│  ┌─────────────────────────┐  ┌──────────────────────────┐  │
│  │  DataGeneratorService   │  │  AnalysisService         │  │
│  │  - 数据生成              │  │  - 基础统计分析           │  │
│  │  - Excel导入/导出        │  │  - 年级/性别统计          │  │
│  │  - 数据验证              │  │  - BMI分析               │  │
│  │                         │  │  - 生长趋势分析           │  │
│  │                         │  │  - 百分位数分析           │  │
│  └─────────────────────────┘  └──────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      数据访问层 (DAO)                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  BaseDAO (抽象基类)                                    │  │
│  │  ├─ StudentDAO                                        │  │
│  │  ├─ HeightRecordDAO                                   │  │
│  │  └─ ClassDAO                                          │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  DatabaseManager (单例)                                │  │
│  │  ├─ PostgreSQLStrategy (策略)                         │  │
│  │  ├─ MySQLStrategy (策略)                              │  │
│  │  └─ SQLiteStrategy (策略)                             │  │
│  └───────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      核心层 (Core)                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │  Exceptions     │  │  Logger         │  │  Observer   │  │
│  │  - 自定义异常    │  │  - 日志管理     │  │  - 观察者模式│  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      配置层 (Config)                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Settings (Pydantic)                                   │  │
│  │  - 数据库配置                                          │  │
│  │  - 应用配置                                            │  │
│  │  - 日志配置                                            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 设计模式应用

#### 2.2.1 工厂模式 (Factory Pattern)
**位置**: `src/dao/database.py`

用于创建不同数据库类型的连接策略：

```python
class DatabaseStrategyFactory:
    _strategies = {
        "postgresql": PostgreSQLStrategy,
        "mysql": MySQLStrategy,
        "sqlite": SQLiteStrategy,
    }
    
    @classmethod
    def create_strategy(cls, driver: str) -> DatabaseStrategy:
        # 根据驱动类型返回对应的策略实例
```

**优点**:
- 解耦数据库连接创建逻辑
- 易于扩展新的数据库类型
- 集中管理数据库配置

#### 2.2.2 策略模式 (Strategy Pattern)
**位置**: `src/dao/database.py`

定义数据库连接的通用接口，支持多种数据源：

```python
class DatabaseStrategy(ABC):
    @abstractmethod
    def create_engine(self, settings: AppSettings) -> Engine:
        pass

class PostgreSQLStrategy(DatabaseStrategy):
    # PostgreSQL特定实现

class SQLiteStrategy(DatabaseStrategy):
    # SQLite特定实现
```

**优点**:
- 算法可互换
- 避免多重条件判断
- 易于单元测试

#### 2.2.3 单例模式 (Singleton Pattern)
**位置**: `src/dao/database.py`, `config/settings.py`

确保全局只有一个实例：

```python
class DatabaseManager:
    _instance: Optional['DatabaseManager'] = None
    
    def __new__(cls) -> 'DatabaseManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**应用**:
- DatabaseManager: 管理数据库连接池
- AppSettings: 管理应用配置
- LoggerManager: 管理日志配置

**优点**:
- 控制资源访问
- 节省内存
- 避免重复初始化

#### 2.2.4 观察者模式 (Observer Pattern)
**位置**: `src/core/observer.py`

实现数据变更通知机制：

```python
class Subject(ABC):
    def attach(self, observer: Observer) -> None
    def detach(self, observer: Observer) -> None
    def notify(self, event: DataChangeEvent) -> None

class DataChangeSubject(Subject):
    def emit(self, change_type, entity_type, ...) -> None
```

**观察者实现**:
- LoggingObserver: 记录数据变更日志
- CacheInvalidationObserver: 缓存失效处理
- NotificationObserver: 通知发送

**优点**:
- 松耦合
- 支持广播通信
- 易于扩展新的观察者

## 3. 数据库设计

### 3.1 ER图

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   class_info    │       │    students     │       │ height_records  │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ PK id           │◄──────┤ FK class_id     │       │ PK id           │
│    grade        │       │ PK id           │◄──────┤ FK student_id   │
│    class_number │       │    student_id   │       │    height       │
│    class_name   │       │    name         │       │    weight       │
│    student_count│       │    gender       │       │    record_date  │
│    created_at   │       │    grade        │       │    age          │
│    updated_at   │       │    age          │       │    notes        │
└─────────────────┘       │    height       │       │    created_at   │
                          │    weight       │       └─────────────────┘
                          │    bmi          │
                          │    bmi_category │
                          │    enrollment   │
                          │    created_at   │
                          │    updated_at   │
                          └─────────────────┘
                                   │
                                   │
                                   ▼
                          ┌─────────────────┐
                          │ statistics_     │
                          │   records       │
                          ├─────────────────┤
                          │ PK id           │
                          │    stat_type    │
                          │    dimension    │
                          │    dimension_val│
                          │    metric_name  │
                          │    metric_value │
                          │    sample_size  │
                          │    calculated_at│
                          └─────────────────┘
```

### 3.2 表结构

#### students (学生表)
| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTO_INCREMENT | 主键 |
| student_id | VARCHAR(20) | UNIQUE, NOT NULL | 学号 |
| name | VARCHAR(50) | NOT NULL | 姓名 |
| gender | VARCHAR(10) | NOT NULL, INDEX | 性别 |
| grade | VARCHAR(20) | NOT NULL, INDEX | 年级 |
| age | INTEGER | NOT NULL, INDEX | 年龄 |
| height | FLOAT | NOT NULL | 身高(cm) |
| weight | FLOAT | NOT NULL | 体重(kg) |
| bmi | FLOAT | NOT NULL, INDEX | BMI指数 |
| bmi_category | VARCHAR(20) | NOT NULL, INDEX | BMI分类 |
| class_id | INTEGER | FK | 班级ID |
| enrollment_date | VARCHAR(10) | | 入学日期 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

#### class_info (班级表)
| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTO_INCREMENT | 主键 |
| grade | VARCHAR(20) | NOT NULL, INDEX | 年级 |
| class_number | INTEGER | NOT NULL | 班级编号 |
| class_name | VARCHAR(50) | NOT NULL | 班级名称 |
| student_count | INTEGER | DEFAULT 0 | 学生人数 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

#### height_records (身高记录表)
| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTO_INCREMENT | 主键 |
| student_id | INTEGER | FK, NOT NULL, INDEX | 学生ID |
| height | FLOAT | NOT NULL | 身高(cm) |
| weight | FLOAT | NOT NULL | 体重(kg) |
| record_date | VARCHAR(10) | NOT NULL, INDEX | 记录日期 |
| age | INTEGER | NOT NULL | 年龄 |
| notes | TEXT | | 备注 |
| created_at | DATETIME | NOT NULL | 创建时间 |

### 3.3 索引设计

```sql
-- 学生表索引
CREATE INDEX ix_student_grade_gender ON students(grade, gender);
CREATE INDEX ix_student_grade_age ON students(grade, age);
CREATE INDEX ix_student_bmi_category ON students(bmi_category);

-- 班级表唯一约束
CREATE UNIQUE INDEX uix_grade_class ON class_info(grade, class_number);

-- 身高记录表索引
CREATE INDEX ix_record_student_date ON height_records(student_id, record_date);
```

## 4. 时序图

### 4.1 数据生成流程

```
User          Main        DataGeneratorService    StudentDAO    Database
 |              |                  |                  |             |
 |──generate──►|                  |                  |             |
 |              |──generate_data──►|                  |             |
 |              |                  |──generate_name──►|             |
 |              |                  |◄──name───────────|             |
 |              |                  |──calculate_bmi──►|             |
 |              |                  |◄──bmi────────────|             |
 |              |◄──data───────────|                  |             |
 |              |──create_many────────────────────────►|             |
 |              |                                   │──INSERT──────►|
 |              |                                   │◄──OK─────────|
 |              |◄──entities─────────────────────────|             |
 |◄──done───────|                  |                  |             |
```

### 4.2 数据分析流程

```
User          Main        AnalysisService    StudentDAO    Database
 |              |               |                  |             |
 |──analyze───►|               |                  |             |
 |              |──get_stats───►|                  |             |
 |              |               |──query──────────►|             |
 |              |               |                  │──SELECT────►|
 |              |               |                  │◄──data─────|
 |              |               |◄──results────────|             |
 |              |──calculate───►|                  |             |
 |              |◄──report──────|                  |             |
 |◄──display────|               |                  |             |
```

### 4.3 图表生成流程

```
User          Main        HeightVisualizer    AnalysisService    Chart
 |              |               |                    |              |
 |──visualize─►|               |                    |              |
 |              |──generate────►|                    |              |
 |              |               |──get_data─────────►|              |
 |              |               |◄──data─────────────|              |
 |              |               |──create─────────────────────────►|
 |              |               |◄──figure─────────────────────────|
 |              |               |──save───────────────────────────►|
 |              |◄──filepath────|                    |              |
 |◄──done───────|               |                    |              |
```

## 5. 模块依赖关系

```
config
  └── settings
      └── pydantic

src.core
  ├── exceptions
  ├── logger
  │   └── logging
  └── observer

src.dao
  ├── models
  │   └── sqlalchemy
  ├── database
  │   ├── sqlalchemy
  │   └── config.settings
  ├── base_dao
  │   ├── database
  │   ├── core.exceptions
  │   └── core.observer
  ├── student_dao
  │   └── base_dao
  └── class_dao
      └── base_dao

src.service
  ├── data_generator
  │   ├── pandas
  │   ├── numpy
  │   ├── dao.student_dao
  │   └── core.exceptions
  └── analysis_service
      ├── pandas
      ├── numpy
      ├── dao.student_dao
      └── core.logger

src.visualization
  ├── charts
  │   ├── matplotlib
  │   ├── pandas
  │   └── numpy
  └── visualizer
      ├── charts
      ├── service.analysis_service
      └── dao.student_dao

src.main
  ├── config.settings
  ├── core.logger
  ├── core.observer
  ├── dao
  ├── service
  └── visualization
```

## 6. 配置说明

### 6.1 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DB_DRIVER | postgresql | 数据库驱动 |
| DB_HOST | localhost | 数据库主机 |
| DB_PORT | 5432 | 数据库端口 |
| DB_NAME | student_height_db | 数据库名称 |
| DB_USER | postgres | 数据库用户 |
| DB_PASSWORD | postgres | 数据库密码 |
| DB_POOL_SIZE | 5 | 连接池大小 |
| LOG_LEVEL | INFO | 日志级别 |
| DEBUG | False | 调试模式 |

### 6.2 配置文件示例

```python
# .env
DB_DRIVER=sqlite
DB_NAME=data/student_height.db
LOG_LEVEL=DEBUG
```

## 7. 扩展性设计

### 7.1 添加新的数据库支持

1. 创建新的策略类继承 `DatabaseStrategy`
2. 在 `DatabaseStrategyFactory._strategies` 中注册
3. 实现 `create_engine` 和 `get_pool_class` 方法

### 7.2 添加新的图表类型

1. 创建新的图表类继承 `ChartBase`
2. 实现 `create` 方法
3. 在 `HeightVisualizer` 中注册并添加生成方法

### 7.3 添加新的观察者

1. 创建新的观察者类继承 `Observer`
2. 实现 `update` 和 `get_observer_name` 方法
3. 在 `setup_observers` 中注册

## 8. 性能优化

### 8.1 数据库优化
- 连接池管理
- 索引优化
- 批量操作

### 8.2 缓存策略
- 统计结果缓存
- 观察者模式自动失效

### 8.3 图表优化
- 非交互式后端
- 异步生成（可扩展）
