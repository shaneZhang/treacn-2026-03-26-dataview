# 小学生身高数据分析与可视化系统

## 项目简介

本项目是一个基于 Python + Pandas + Matplotlib 的小学生身高数据分析与可视化工程。系统可以生成模拟的小学生身高数据，进行全面的统计分析，并生成多种可视化图表。

## 项目结构

```
student_height_analysis/
├── README.md                    # 项目说明文档
├── data/                        # 数据目录
│   └── student_height_data.xlsx # 生成的学生身高数据
├── src/                         # 源代码目录
│   ├── main.py                  # 主程序入口
│   ├── generate_data.py         # 数据生成模块
│   ├── data_analysis.py         # 数据分析模块
│   └── visualization.py         # 数据可视化模块
└── output/                      # 输出目录（图表）
    ├── height_by_grade.png      # 各年级平均身高柱状图
    ├── height_by_gender.png     # 男女生身高对比图
    ├── height_distribution.png  # 身高分布直方图
    ├── boxplot_by_grade.png     # 各年级身高箱线图
    ├── growth_trend.png         # 生长趋势折线图
    ├── scatter_age_height.png   # 年龄身高散点图
    ├── bmi_distribution.png     # BMI分布图
    └── height_heatmap.png       # 身高热力图
```

## 功能特性

### 1. 数据生成
- 自动生成 1000 条小学生模拟数据
- 包含字段：学生ID、姓名、性别、年级、年龄、身高、体重、入学日期
- 基于中国儿童生长标准生成真实合理的身高数据

### 2. 数据分析
- **基础统计**：总人数、男女比例、平均身高、标准差等
- **年级分析**：各年级的身高统计信息
- **性别分析**：按性别和年级的身高对比
- **年龄分析**：各年龄段的身高统计
- **分布分析**：身高段分布统计
- **生长趋势**：相邻年级的身高增长分析
- **百分位数**：P3、P10、P25、P50、P75、P90、P97 百分位数
- **BMI分析**：体重指数分布及分类
- **标准对比**：与国家标准身高的对比

### 3. 数据可视化
- 各年级平均身高柱状图
- 男女生身高对比图
- 身高分布直方图
- 各年级身高箱线图
- 生长趋势折线图
- 年龄身高散点图
- BMI分布饼图和柱状图
- 身高热力图

## 环境要求

- Python 3.7+
- pandas
- numpy
- matplotlib
- openpyxl

## 安装依赖

```bash
pip install pandas numpy matplotlib openpyxl
```

## 使用方法

### 方法一：运行完整流程（推荐）

```bash
cd src
python main.py
```

这将执行以下步骤：
1. 生成 1000 条模拟数据
2. 执行数据分析
3. 生成可视化图表

### 方法二：指定数据条数

```bash
python main.py -n 500    # 生成500条数据
python main.py -n 2000   # 生成2000条数据
```

### 方法三：跳过数据生成

如果你已经生成了数据，只想重新分析和可视化：

```bash
python main.py -s
```

### 方法四：单独使用各模块

#### 生成数据
```python
from generate_data import generate_student_data, save_to_excel

df = generate_student_data(n=1000)
save_to_excel(df, "data/student_height_data.xlsx")
```

#### 数据分析
```python
from data_analysis import StudentHeightAnalyzer

analyzer = StudentHeightAnalyzer("data/student_height_data.xlsx")
results = analyzer.run_all_analysis()
```

#### 数据可视化
```python
from visualization import HeightVisualizer

visualizer = HeightVisualizer("data/student_height_data.xlsx")
visualizer.generate_all_plots()
```

## 数据字段说明

| 字段名 | 说明 | 示例 |
|--------|------|------|
| 学生ID | 唯一标识符 | 10001 |
| 姓名 | 学生姓名 | 王伟 |
| 性别 | 男/女 | 男 |
| 年级 | 一至六年级 | 三年级 |
| 年龄 | 6-12岁 | 9 |
| 身高(cm) | 身高（厘米） | 130.5 |
| 体重(kg) | 体重（千克） | 28.3 |
| 入学日期 | 入学时间 | 2022-09-01 |

## 数据分析指标说明

### 基础统计指标
- **平均身高**：所有学生的平均身高
- **标准差**：身高的离散程度
- **中位数**：身高的中间值
- **最值**：最高和最矮身高

### 百分位数
- **P3**：3%的学生低于此身高（偏矮）
- **P50**：50%的学生低于此身高（中位数）
- **P97**：97%的学生低于此身高（偏高）

### BMI分类（儿童标准）
- **偏瘦**：BMI < 14
- **正常**：14 ≤ BMI < 18
- **超重**：18 ≤ BMI < 21
- **肥胖**：BMI ≥ 21

## 输出图表说明

| 图表文件名 | 说明 |
|-----------|------|
| height_by_grade.png | 展示各年级平均身高的柱状图 |
| height_by_gender.png | 对比各年级男女生平均身高 |
| height_distribution.png | 全体学生身高分布直方图 |
| boxplot_by_grade.png | 展示各年级身高分布的箱线图 |
| growth_trend.png | 展示身高随年级增长的趋势 |
| scatter_age_height.png | 年龄与身高的散点关系图 |
| bmi_distribution.png | BMI分布的饼图和柱状图 |
| height_heatmap.png | 年级与性别的身高热力图 |

## 示例输出

运行程序后，你将看到类似以下的输出：

```
============================================================
小学生身高数据分析报告
============================================================

【一、基础统计】
  总人数: 1000
  男生人数: 503
  女生人数: 497
  平均身高: 133.45
  ...

【二、年级统计】
              人数  平均身高  身高标准差  ...
一年级       167   119.52      5.42  ...
二年级       168   124.38      5.78  ...
...

所有图表已保存至: ../output/
```

## 注意事项

1. **数据真实性**：生成的数据为模拟数据，基于中国儿童生长标准，但仅供参考。
2. **字体显示**：如果在图表中遇到中文显示问题，请确保系统安装了中文字体。
3. **随机种子**：数据生成使用固定随机种子（42），确保结果可重复。

## 扩展开发

你可以根据需要扩展以下功能：
- 添加更多分析指标
- 生成PDF报告
- 添加数据导出功能（CSV、JSON等）
- 开发Web界面
- 添加数据筛选和查询功能

## 技术栈

- **数据处理**：Pandas、NumPy
- **数据可视化**：Matplotlib
- **数据存储**：Excel（openpyxl）

## 许可证

本项目仅供学习和研究使用。
