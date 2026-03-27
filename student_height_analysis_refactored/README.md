# 小学生身高数据分析与可视化系统（重构版）

## 项目简介

本项目是一个基于 Python + SQLAlchemy + Matplotlib 的小学生身高数据分析与可视化系统。系统采用分层架构设计，支持多种数据库，实现了完整的数据分析流程。

### 主要特性

- ✅ **分层架构**：数据访问层(DAO)、业务逻辑层(Service)、表现层(Visualization)
- ✅ **多数据库支持**：SQLite、MySQL、PostgreSQL
- ✅ **设计模式应用**：单例模式、工厂模式、策略模式、观察者模式
- ✅ **完整的类型注解**：所有函数都有完整的Type Hints
- ✅ **规范的文档**：Google Style Docstring
- ✅ **统一的异常处理**：自定义异常类层次结构
- ✅ **日志记录**：支持文件和控制台双输出
- ✅ **数据库迁移**：使用Alembic进行版本管理
- ✅ **完整的测试**：单元测试、集成测试，覆盖率>80%

## 项目结构

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
│   ├── database_design.md # 数据库设计文档
│   └── architecture_design.md # 架构设计文档
├── data/                   # 数据目录
├── output/                 # 输出目录
├── logs/                   # 日志目录
├── main.py                 # 主程序入口
├── requirements.txt        # 依赖列表
├── alembic.ini            # Alembic配置
└── README.md              # 项目说明
```

## 环境要求

- Python 3.8+
- 操作系统：Windows / macOS / Linux

## 安装指南

### 1. 克隆项目

```bash
git clone <repository-url>
cd student_height_analysis_refactored
```

### 2. 创建虚拟环境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置数据库

默认使用SQLite数据库，无需额外配置。

如需使用MySQL或PostgreSQL，设置环境变量：

```bash
# MySQL
export DB_TYPE=mysql
export DB_HOST=localhost
export DB_PORT=3306
export DB_NAME=student_height
export DB_USER=root
export DB_PASSWORD=password

# PostgreSQL
export DB_TYPE=postgresql
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=student_height
export DB_USER=postgres
export DB_PASSWORD=password
```

### 5. 初始化数据库

```bash
# 使用Alembic迁移
alembic upgrade head
```

## 使用方法

### 运行完整流程

```bash
python main.py
```

这将执行以下步骤：
1. 生成1000条模拟数据
2. 执行数据分析
3. 生成可视化图表
4. 导出分析报告

### 命令行参数

```bash
# 指定数据条数
python main.py -n 500

# 跳过数据生成
python main.py --skip-generation

# 仅运行数据分析
python main.py --analysis-only

# 仅运行数据可视化
python main.py --visualization-only

# 仅导出分析报告
python main.py --export-only
```

### 编程方式使用

```python
from core import StudentService, DataAnalysisService, HeightVisualizer
from datetime import date

# 创建学生
student_service = StudentService()
student = student_service.create_student(
    student_number='10001',
    name='张三',
    gender='男',
    grade='三年级',
    age=9,
    enrollment_date=date(2022, 9, 1)
)

# 添加身高记录
record = student_service.add_height_record(
    student_id=student.id,
    record_date=date.today(),
    height=130.5,
    weight=28.0
)

# 数据分析
analysis_service = DataAnalysisService()
stats = analysis_service.get_basic_statistics()
print(f"平均身高: {stats['avg_height']}cm")

# 数据可视化
visualizer = HeightVisualizer()
visualizer.plot_height_by_grade()
```

## 数据分析功能

### 基础统计

- 总人数、男女比例
- 平均身高、标准差
- 身高范围（最小值、最大值、中位数）

### 年级分析

- 各年级平均身高
- 各年级身高标准差
- 各年级体重统计

### 性别分析

- 各年级男女生身高对比
- 性别差异分析

### 生长趋势

- 相邻年级身高增长
- 增长率分析

### 百分位数分析

- P3、P10、P25、P50、P75、P90、P97百分位数
- 身高分布评估

### BMI分析

- BMI计算和分类
- 各年级BMI分布

### 标准对比

- 与国家标准身高对比
- 差异分析

## 可视化图表

系统自动生成以下图表：

1. **height_by_grade.png** - 各年级平均身高柱状图
2. **height_by_gender.png** - 男女生身高对比图
3. **height_distribution.png** - 身高分布直方图
4. **boxplot_by_grade.png** - 各年级身高箱线图
5. **growth_trend.png** - 生长趋势折线图
6. **bmi_distribution.png** - BMI分布图

## 数据库设计

详细的数据库设计请参考 [database_design.md](docs/database_design.md)

### 主要表结构

- **classes** - 班级表
- **students** - 学生表
- **height_records** - 身高记录表
- **standard_heights** - 标准身高表

## 架构设计

详细的架构设计请参考 [architecture_design.md](docs/architecture_design.md)

### 设计模式应用

1. **单例模式** - 配置管理、数据库连接、日志管理
2. **工厂模式** - 数据库连接创建
3. **策略模式** - 多数据库支持
4. **观察者模式** - 数据变更通知

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=. --cov-report=html

# 运行特定测试文件
pytest tests/test_dao.py

# 运行特定测试类
pytest tests/test_dao.py::TestStudentDAO

# 运行特定测试方法
pytest tests/test_dao.py::TestStudentDAO::test_create_student
```

### 测试覆盖率

项目测试覆盖率 > 80%，包括：

- DAO层单元测试
- Service层单元测试
- 集成测试
- 异常处理测试

## 代码质量

### 代码规范

项目遵循PEP8规范，使用以下工具进行代码质量检查：

```bash
# Flake8检查
flake8 .

# Pylint检查
pylint student_height_analysis_refactored

# MyPy类型检查
mypy .

# Black格式化
black .
```

### 类型注解

所有函数都有完整的类型注解：

```python
def create_student(
    self,
    student_number: str,
    name: str,
    gender: str,
    grade: str,
    age: int,
    enrollment_date: date
) -> Student:
    """创建学生"""
    pass
```

### 文档规范

所有函数都有Google Style Docstring：

```python
def get_basic_statistics(self) -> Dict[str, Any]:
    """
    获取基础统计数据
    
    Returns:
        Dict[str, Any]: 基础统计数据字典
    
    Example:
        >>> stats = service.get_basic_statistics()
    """
    pass
```

## 数据导入导出

### 从Excel导入

```python
from core import DataImportExportService

service = DataImportExportService()
result = service.import_from_excel('students.xlsx')
print(f"成功导入: {result['success']}条")
```

### 导出到Excel

```python
service = DataImportExportService()
path = service.export_to_excel('output.xlsx')
```

### 导出分析报告

```python
path = service.export_statistics_report('report.xlsx')
```

## 日志管理

系统自动记录日志到 `logs/app.log`，同时输出到控制台。

### 日志级别

- DEBUG - 调试信息
- INFO - 一般信息
- WARNING - 警告信息
- ERROR - 错误信息

### 日志格式

```
2026-03-27 10:30:45 - StudentHeightAnalysis - INFO - 学生创建成功: 10001
```

## 数据库迁移

### 创建迁移脚本

```bash
alembic revision --autogenerate -m "描述信息"
```

### 执行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 回滚一个版本
alembic downgrade -1

# 查看迁移历史
alembic history
```

## 性能优化

### 数据库优化

- 连接池管理
- 索引优化
- 批量操作

### 缓存策略

- 使用CacheObserver缓存常用数据
- 数据变更时自动清除缓存

## 扩展开发

### 添加新的数据库类型

1. 创建新的策略类继承 `DatabaseStrategy`
2. 实现 `create_engine()` 方法
3. 在 `DatabaseFactory` 中注册

### 添加新的图表类型

1. 在 `HeightVisualizer` 中添加新的绘图方法
2. 在 `generate_all_plots()` 中调用

### 添加新的分析功能

1. 在 `DataAnalysisService` 中添加新的分析方法
2. 编写对应的单元测试

## 常见问题

### Q: 如何切换数据库？

A: 设置环境变量 `DB_TYPE` 为 `sqlite`、`mysql` 或 `postgresql`，并配置相应的连接参数。

### Q: 如何修改日志级别？

A: 设置环境变量 `LOG_LEVEL` 为 `DEBUG`、`INFO`、`WARNING` 或 `ERROR`。

### Q: 如何自定义图表样式？

A: 修改 `core/visualization/visualizer.py` 中的 `ChartConfig` 类。

## 许可证

MIT License

## 作者

AI Assistant

## 更新日志

### v2.0.0 (2026-03-27)

- 完全重构项目架构
- 采用分层架构设计
- 应用设计模式
- 添加完整的类型注解和文档
- 实现数据库迁移
- 添加完整的测试体系
