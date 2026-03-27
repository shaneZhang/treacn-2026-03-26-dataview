# 架构设计文档

## 1. 系统架构概览

### 1.1 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                    表现层 (Presentation)                 │
│                  HeightVisualizer                        │
│              (数据可视化、图表生成)                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  业务逻辑层 (Service)                    │
│    StudentService | DataAnalysisService                 │
│         DataImportExportService                         │
│          (业务逻辑处理、数据分析)                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  数据访问层 (DAO)                        │
│   StudentDAO | HeightRecordDAO | ClassDAO               │
│              (数据CRUD操作)                              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                    数据层 (Data)                         │
│        DatabaseFactory | SQLAlchemy ORM                 │
│          (数据库连接、ORM映射)                           │
└─────────────────────────────────────────────────────────┘
```

### 1.2 模块结构

```
student_height_analysis_refactored/
├── config/                 # 配置模块
│   ├── settings.py        # 配置管理（单例模式）
│   └── __init__.py
├── models/                 # 数据模型
│   ├── entities.py        # ORM实体类
│   └── __init__.py
├── core/                   # 核心业务
│   ├── dao/               # 数据访问层
│   │   ├── base_dao.py    # DAO实现
│   │   └── __init__.py
│   ├── service/           # 业务逻辑层
│   │   ├── business_service.py
│   │   └── __init__.py
│   ├── visualization/     # 表现层
│   │   ├── visualizer.py
│   │   └── __init__.py
│   ├── database.py        # 数据库连接（工厂模式）
│   ├── observer.py        # 观察者模式
│   └── __init__.py
├── utils/                  # 工具模块
│   ├── exceptions.py      # 自定义异常
│   ├── logger.py          # 日志管理（单例模式）
│   ├── data_generator.py  # 数据生成器
│   └── __init__.py
├── tests/                  # 测试模块
│   ├── conftest.py        # 测试配置
│   ├── test_dao.py        # DAO测试
│   ├── test_service.py    # Service测试
│   └── test_integration.py # 集成测试
├── migrations/             # 数据库迁移
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── docs/                   # 文档
├── data/                   # 数据目录
├── output/                 # 输出目录
├── logs/                   # 日志目录
├── main.py                 # 主程序入口
├── requirements.txt        # 依赖列表
├── alembic.ini            # Alembic配置
└── README.md              # 项目说明
```

## 2. 设计模式应用

### 2.1 单例模式 (Singleton Pattern)

**应用场景：**
- 配置管理 (Config)
- 数据库连接工厂 (DatabaseFactory)
- 日志管理器 (LoggerManager)
- 事件管理器 (EventManager)

**类图：**

```
┌─────────────────────┐
│      Config         │
├─────────────────────┤
│ - _instance: Config │
│ - _initialized: bool│
├─────────────────────┤
│ + __new__()         │
│ + get_instance()    │
│ + reset()           │
└─────────────────────┘
```

**代码示例：**

```python
class Config:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

### 2.2 工厂模式 (Factory Pattern)

**应用场景：**
- 数据库连接创建 (DatabaseFactory)

**类图：**

```
┌─────────────────────┐
│  DatabaseFactory    │
├─────────────────────┤
│ - _engine           │
│ - _session_factory  │
├─────────────────────┤
│ + get_engine()      │
│ + get_session()     │
│ + create_tables()   │
└─────────────────────┘
         │
         │ uses
         ▼
┌─────────────────────┐
│ DatabaseStrategy    │◄───────────┐
├─────────────────────┤            │
│ + create_engine()   │            │
│ + get_connection_url()│          │
└─────────────────────┘            │
         △                         │
         │ implements              │
    ┌────┴────┬─────────┐          │
    │         │         │          │
┌───▼───┐ ┌──▼──┐ ┌────▼────┐     │
│SQLite │ │MySQL│ │PostgreSQL│     │
│Strategy│ │Strategy│ │Strategy │     │
└───────┘ └─────┘ └─────────┘     │
                                   │
                                   │
```

### 2.3 策略模式 (Strategy Pattern)

**应用场景：**
- 多数据库支持 (SQLite/MySQL/PostgreSQL)

**类图：**

```
┌──────────────────────┐
│  DatabaseStrategy    │ (抽象策略)
├──────────────────────┤
│ + create_engine()    │
│ + get_connection_url()│
│ + get_pool_config()  │
└──────────────────────┘
         △
         │
    ┌────┴────┬─────────┐
    │         │         │
┌───▼────┐ ┌──▼─────┐ ┌─▼────────┐
│SQLite  │ │MySQL   │ │PostgreSQL│
│Strategy│ │Strategy│ │Strategy  │
└────────┘ └────────┘ └──────────┘
```

**代码示例：**

```python
class DatabaseStrategy(ABC):
    @abstractmethod
    def create_engine(self) -> Engine:
        pass

class SQLiteStrategy(DatabaseStrategy):
    def create_engine(self) -> Engine:
        return create_engine(f"sqlite:///{self.db_path}")

class MySQLStrategy(DatabaseStrategy):
    def create_engine(self) -> Engine:
        return create_engine(f"mysql+pymysql://...")
```

### 2.4 观察者模式 (Observer Pattern)

**应用场景：**
- 数据变更通知机制
- 事件驱动架构

**类图：**

```
┌─────────────────────┐
│      Subject        │
├─────────────────────┤
│ - _observers: List  │
├─────────────────────┤
│ + attach(observer)  │
│ + detach(observer)  │
│ + notify(event)     │
└─────────────────────┘
         │
         │ notifies
         ▼
┌─────────────────────┐
│     Observer        │ (抽象观察者)
├─────────────────────┤
│ + update(event)     │
└─────────────────────┘
         △
         │
    ┌────┴────┬─────────┐
    │         │         │
┌───▼────┐ ┌──▼─────┐ ┌─▼────────┐
│Log     │ │Cache   │ │Notification│
│Observer│ │Observer│ │Observer  │
└────────┘ └────────┘ └──────────┘
```

**时序图：**

```
DAO              Subject           LogObserver        CacheObserver
 │                  │                    │                  │
 │ create()         │                    │                  │
 ├──────────────────>                    │                  │
 │                  │                    │                  │
 │                  │  notify(event)     │                  │
 │                  ├───────────────────>│                  │
 │                  │                    │ update(event)    │
 │                  │                    ├─────────────────>│
 │                  │                    │                  │
 │                  │                    │   log message    │
 │                  │                    │<─────────────────│
 │                  │                    │                  │ clear cache
 │                  │                    │                  │<────────────
 │<─────────────────┤                    │                  │
 │                  │                    │                  │
```

## 3. 类图

### 3.1 核心类图

```
┌─────────────────────┐
│    StudentDAO       │
├─────────────────────┤
│ - session: Session  │
│ - logger: Logger    │
├─────────────────────┤
│ + create()          │
│ + get_by_id()       │
│ + get_all()         │
│ + update()          │
│ + delete()          │
│ + count()           │
└─────────────────────┘

┌─────────────────────┐
│  StudentService     │
├─────────────────────┤
│ - student_dao       │
│ - record_dao        │
│ - event_manager     │
├─────────────────────┤
│ + create_student()  │
│ + get_student()     │
│ + add_height_record()│
│ + get_students_by_grade()│
└─────────────────────┘

┌─────────────────────┐
│DataAnalysisService  │
├─────────────────────┤
│ - student_dao       │
│ - record_dao        │
│ - standard_dao      │
├─────────────────────┤
│ + get_basic_statistics()│
│ + get_grade_statistics()│
│ + get_gender_statistics()│
│ + get_growth_analysis()│
│ + get_percentile_analysis()│
│ + get_bmi_statistics()│
│ + compare_with_standard()│
└─────────────────────┘

┌─────────────────────┐
│ HeightVisualizer    │
├─────────────────────┤
│ - output_dir: Path  │
│ - analysis_service  │
├─────────────────────┤
│ + plot_height_by_grade()│
│ + plot_height_by_gender()│
│ + plot_height_distribution()│
│ + plot_boxplot_by_grade()│
│ + plot_growth_trend()│
│ + plot_bmi_distribution()│
│ + generate_all_plots()│
└─────────────────────┘
```

## 4. 时序图

### 4.1 创建学生流程

```
User        Main        StudentService    StudentDAO      Database      EventManager
 │            │              │               │               │              │
 │ create     │              │               │               │              │
 ├───────────>│              │               │               │              │
 │            │ create_student()             │               │              │
 │            ├──────────────>│               │               │              │
 │            │              │ create()      │               │              │
 │            │              ├──────────────>│               │              │
 │            │              │               │ INSERT        │              │
 │            │              │               ├──────────────>│              │
 │            │              │               │               │              │
 │            │              │               │    success    │              │
 │            │              │               │<──────────────┤              │
 │            │              │    student    │               │              │
 │            │              │<──────────────┤               │              │
 │            │              │               │               │ emit event   │
 │            │              │               │               ├─────────────>│
 │            │              │               │               │              │
 │            │   student    │               │               │              │
 │            │<─────────────┤               │               │              │
 │   result   │              │               │               │              │
 │<───────────┤              │               │               │              │
```

### 4.2 数据分析流程

```
User        Main    DataAnalysisService  HeightRecordDAO    Database
 │            │              │                  │               │
 │ analyze    │              │                  │               │
 ├───────────>│              │                  │               │
 │            │ get_basic_statistics()         │               │
 │            ├──────────────>│                  │               │
 │            │              │ get_all()        │               │
 │            │              ├─────────────────>│               │
 │            │              │                  │ SELECT        │
 │            │              │                  ├──────────────>│
 │            │              │                  │    records    │
 │            │              │                  │<──────────────┤
 │            │              │    records       │               │
 │            │              │<─────────────────┤               │
 │            │              │                  │               │
 │            │              │ calculate stats  │               │
 │            │              ├─────────────────>│               │
 │            │   statistics │                  │               │
 │            │<─────────────┤                  │               │
 │   result   │              │                  │               │
 │<───────────┤              │                  │               │
```

## 5. 异常处理机制

### 5.1 异常层次结构

```
StudentHeightBaseException
├── DatabaseException
│   ├── DatabaseConnectionException
│   └── DatabaseQueryException
├── DataNotFoundException
│   ├── StudentNotFoundException
│   └── RecordNotFoundException
├── DataValidationException
│   ├── InvalidDataException
│   └── DuplicateDataException
├── FileOperationException
│   ├── FileNotFoundException
│   └── FileFormatNotSupportedException
├── ConfigurationException
├── VisualizationException
├── AnalysisException
├── ImportExportException
└── ObserverException
```

### 5.2 异常处理策略

1. **DAO层**：捕获数据库异常，转换为业务异常
2. **Service层**：处理业务逻辑异常，记录日志
3. **表现层**：统一异常处理，返回友好错误信息

## 6. 性能优化

### 6.1 数据库优化

- 连接池管理
- 索引优化
- 查询优化
- 批量操作

### 6.2 缓存策略

- 使用CacheObserver缓存常用数据
- 缓存失效机制
- 缓存预热

### 6.3 并发处理

- 线程安全的Session管理
- 数据库连接池
- 事务隔离级别

## 7. 扩展性设计

### 7.1 开闭原则

- 对扩展开放：新增数据库类型、新增图表类型
- 对修改关闭：核心逻辑稳定

### 7.2 依赖倒置

- 高层模块不依赖低层模块
- 都依赖于抽象

### 7.3 接口隔离

- DAO接口职责单一
- Service接口按业务划分
