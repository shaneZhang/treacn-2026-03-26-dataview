# 小学生身高数据分析与可视化系统 v2.0

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

一个基于分层架构的小学生身高数据分析与可视化系统，支持SQLite/PostgreSQL数据库，应用多种设计模式，提供完整的数据分析、可视化和导入导出功能。

## 目录

- [功能特性](#功能特性)
- [架构设计](#架构设计)
- [快速开始](#快速开始)
- [部署指南](#部署指南)
- [使用说明](#使用说明)
- [开发指南](#开发指南)
- [测试](#测试)
- [文档](#文档)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 功能特性

### 核心功能
- 📊 **基础统计分析**：总人数、平均身高、标准差、极值等
- 📈 **年级分析**：各年级平均身高、人数分布
- 👫 **性别分析**：男女生身高对比
- 📉 **生长趋势分析**：相邻年级身高增长分析
- 🎯 **BMI分析**：BMI计算与分类统计
- 📏 **百分位数分析**：P3/P10/P25/P50/P75/P90/P97
- 📐 **标准对比**：与中国儿童身高标准对比

### 可视化图表
- 各年级平均身高柱状图
- 男女生身高对比图
- 身高分布直方图
- 各年级身高箱线图
- 生长趋势折线图
- 年龄身高散点图
- BMI分布饼图+柱状图
- 身高热力图

### 数据管理
- 📥 Excel数据导入
- 📤 Excel数据导出
- 🗄️ 数据库迁移（Alembic）
- 🔄 数据同步

### 技术特性
- 🏗️ **分层架构**：DAO/Service/Visualization三层分离
- 🎨 **设计模式**：工厂模式、策略模式、观察者模式、单例模式
- 📝 **类型注解**：完整的Type Hints
- 📚 **文档规范**：Google Style Docstring
- 🐛 **异常处理**：统一的异常体系
- 📝 **日志系统**：文件+控制台双输出
- ✅ **代码质量**：PEP8规范，flake8/pylint检查
- 🧪 **测试覆盖**：单元测试+集成测试，覆盖率>80%

## 架构设计

### 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                      表现层 (Presentation)                    │
│              HeightVisualizer + Chart Classes                │
├─────────────────────────────────────────────────────────────┤
│                      业务逻辑层 (Service)                     │
│         DataGeneratorService + AnalysisService               │
├─────────────────────────────────────────────────────────────┤
│                      数据访问层 (DAO)                         │
│    BaseDAO + StudentDAO + ClassDAO + HeightRecordDAO         │
│              DatabaseManager + Strategy Pattern              │
├─────────────────────────────────────────────────────────────┤
│                      核心层 (Core)                           │
│         Exceptions + Logger + Observer Pattern               │
├─────────────────────────────────────────────────────────────┤
│                      配置层 (Config)                          │
│              Settings (Pydantic) + Environment               │
└─────────────────────────────────────────────────────────────┘
```

### 设计模式

| 模式 | 应用位置 | 用途 |
|------|----------|------|
| 工厂模式 | `DatabaseStrategyFactory` | 创建数据库连接策略 |
| 策略模式 | `DatabaseStrategy` | 支持多种数据库类型 |
| 单例模式 | `DatabaseManager`, `AppSettings` | 全局唯一实例 |
| 观察者模式 | `DataChangeSubject` | 数据变更通知 |

更多架构细节请参考 [架构设计文档](docs/ARCHITECTURE.md)。

## 快速开始

### 环境要求

- Python 3.9+
- SQLite（内置）或 PostgreSQL 12+

### 安装

1. 克隆仓库
```bash
git clone <repository-url>
cd student_height_analysis_refactored
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 运行程序
```bash
python src/main.py
```

## 部署指南

### 使用SQLite（开发环境）

```bash
# 默认使用SQLite，无需额外配置
python src/main.py
```

### 使用PostgreSQL（生产环境）

1. 安装PostgreSQL
```bash
# macOS
brew install postgresql
brew services start postgresql

# Ubuntu
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

2. 创建数据库
```bash
createdb student_height_db
```

3. 配置环境变量
```bash
export DB_DRIVER=postgresql
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=student_height_db
export DB_USER=postgres
export DB_PASSWORD=your_password
```

4. 或使用.env文件
```bash
cat > .env << EOF
DB_DRIVER=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=student_height_db
DB_USER=postgres
DB_PASSWORD=your_password
LOG_LEVEL=INFO
EOF
```

5. 初始化数据库
```bash
python src/main.py --init-db
```

### Docker部署（可选）

```bash
# 构建镜像
docker build -t student-height-analysis .

# 运行容器
docker run -v $(pwd)/data:/app/data -v $(pwd)/output:/app/output student-height-analysis
```

## 使用说明

### 命令行参数

```bash
python src/main.py [选项]

选项:
  -h, --help            显示帮助信息
  -n NUMBER, --number NUMBER
                        生成的数据条数（默认: 1000）
  -s, --skip-generation
                        跳过数据生成步骤
  --init-db             仅初始化数据库
  --drop-db             删除数据库表（危险操作）
  --import FILE         从Excel文件导入数据
  --export FILE         导出数据到Excel文件
```

### 示例

```bash
# 运行完整流程（生成1000条数据）
python src/main.py

# 生成500条数据
python src/main.py -n 500

# 跳过数据生成，使用已有数据
python src/main.py -s

# 从Excel导入数据
python src/main.py --import data/students.xlsx

# 导出数据到Excel
python src/main.py --export output/export.xlsx

# 初始化数据库
python src/main.py --init-db
```

### 数据导入格式

Excel文件应包含以下列：
- 学生ID（可选）
- 姓名（必填）
- 性别（必填）
- 年级（必填）
- 年龄（必填）
- 身高(cm)（必填）
- 体重(kg)（必填）
- 入学日期（可选）

## 开发指南

### 项目结构

```
student_height_analysis_refactored/
├── config/                 # 配置模块
│   ├── __init__.py
│   └── settings.py         # 应用配置
├── src/                    # 源代码
│   ├── core/              # 核心模块
│   │   ├── exceptions.py  # 异常类
│   │   ├── logger.py      # 日志管理
│   │   └── observer.py    # 观察者模式
│   ├── dao/               # 数据访问层
│   │   ├── models.py      # ORM模型
│   │   ├── database.py    # 数据库管理
│   │   ├── base_dao.py    # DAO基类
│   │   ├── student_dao.py # 学生DAO
│   │   └── class_dao.py   # 班级DAO
│   ├── service/           # 业务逻辑层
│   │   ├── data_generator.py
│   │   └── analysis_service.py
│   ├── visualization/     # 表现层
│   │   ├── charts.py      # 图表类
│   │   └── visualizer.py  # 可视化器
│   └── main.py            # 主程序
├── tests/                 # 测试
│   ├── unit/             # 单元测试
│   └── integration/      # 集成测试
├── docs/                  # 文档
│   ├── ARCHITECTURE.md   # 架构设计
│   └── ER_DIAGRAM.md     # ER图设计
├── data/                  # 数据目录
├── output/                # 输出目录
├── logs/                  # 日志目录
├── requirements.txt       # 依赖
├── pytest.ini            # pytest配置
└── README.md             # 本文件
```

### 代码规范

- 遵循PEP8规范
- 使用类型注解
- 编写Google Style Docstring
- 通过flake8检查：`flake8 src/`
- 通过pylint检查：`pylint src/`

### 添加新功能

1. **添加新的图表类型**
```python
# src/visualization/charts.py
class NewChart(ChartBase):
    def create(self, data: Any) -> plt.Figure:
        # 实现图表创建逻辑
        pass

# src/visualization/visualizer.py
class HeightVisualizer:
    def generate_new_chart(self) -> str:
        fig = self._charts['new_chart'].create(data)
        return self._charts['new_chart'].save(fig, 'new_chart.png')
```

2. **添加新的分析指标**
```python
# src/service/analysis_service.py
class AnalysisService:
    def get_new_metric(self) -> Dict[str, Any]:
        # 实现新指标计算
        pass
```

3. **添加新的观察者**
```python
# src/core/observer.py
class NewObserver(Observer):
    def update(self, event: DataChangeEvent) -> None:
        # 实现通知处理
        pass

# src/main.py
def setup_observers():
    subject.attach(NewObserver())
```

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

### 测试结构

```
tests/
├── conftest.py           # pytest配置和固件
├── unit/                # 单元测试
│   ├── test_exceptions.py
│   ├── test_observer.py
│   ├── test_dao.py
│   └── test_service.py
└── integration/         # 集成测试
    ├── test_database.py
    └── test_end_to_end.py
```

## 文档

- [架构设计文档](docs/ARCHITECTURE.md) - 详细的架构设计和设计模式说明
- [ER图设计文档](docs/ER_DIAGRAM.md) - 数据库表结构详细设计

## 贡献指南

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 提交规范

- 使用语义化提交信息
- 格式：`<type>(<scope>): <subject>`
- 类型：feat/fix/docs/style/refactor/test/chore

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 更新日志

### v2.0.0 (2026-03-27)
- ✨ 重构为分层架构
- ✨ 支持SQLite/PostgreSQL数据库
- ✨ 应用工厂模式、策略模式、观察者模式、单例模式
- ✨ 添加完整的类型注解
- ✨ 实现统一的异常处理机制
- ✨ 添加日志系统
- ✨ 编写完整的测试套件
- ✨ 添加数据库迁移支持

### v1.0.0 (2026-03-26)
- 🎉 初始版本发布
- 基础数据分析和可视化功能
- Excel数据导入导出

## 联系方式

如有问题或建议，欢迎提交Issue或Pull Request。

---

**致谢**

感谢所有为本项目做出贡献的开发者！
