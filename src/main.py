#!/usr/bin/env python3
"""
小学生身高数据分析与可视化系统

本程序用于分析小学各年级学生的身高数据，包括：
- 基础统计分析
- 年级、性别、年龄分组分析
- 生长趋势分析
- BMI分析
- 数据可视化图表生成

作者: AI Assistant
日期: 2026-03-26
"""

import os
import sys
import argparse

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_data import generate_student_data, save_to_excel
from data_analysis import StudentHeightAnalyzer
from visualization import HeightVisualizer


def get_project_paths():
    """获取项目各目录路径"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return {
        'base': base_dir,
        'data': os.path.join(base_dir, 'data'),
        'src': os.path.join(base_dir, 'src'),
        'output': os.path.join(base_dir, 'output')
    }


def check_dependencies():
    """检查必要的依赖包"""
    required_packages = ['pandas', 'numpy', 'matplotlib', 'openpyxl']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("错误: 缺少以下依赖包:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print("\n请使用以下命令安装:")
        print(f"  pip install {' '.join(missing_packages)}")
        return False
    return True


def generate_data(paths, n=1000):
    """生成模拟数据"""
    print("\n" + "=" * 60)
    print("步骤 1: 生成模拟数据")
    print("=" * 60)

    data_file = os.path.join(paths['data'], 'student_height_data.xlsx')

    print(f"正在生成 {n} 条学生身高数据...")
    df = generate_student_data(n=n)

    print(f"正在保存数据到: {data_file}")
    save_to_excel(df, data_file)

    print("\n数据预览（前10条）:")
    print(df.head(10).to_string())
    print(f"\n数据总量: {len(df)} 条")

    return data_file


def analyze_data(paths, data_file):
    """执行数据分析"""
    print("\n" + "=" * 60)
    print("步骤 2: 数据分析")
    print("=" * 60)

    analyzer = StudentHeightAnalyzer(data_file)
    results = analyzer.run_all_analysis()

    return results


def visualize_data(paths, data_file):
    """生成可视化图表"""
    print("\n" + "=" * 60)
    print("步骤 3: 数据可视化")
    print("=" * 60)

    visualizer = HeightVisualizer(data_file, output_dir=paths['output'])
    visualizer.generate_all_plots()


def run_full_pipeline(n=1000, skip_generation=False):
    """
    运行完整的数据分析流程

    参数:
        n: 生成的数据条数
        skip_generation: 是否跳过数据生成步骤
    """
    paths = get_project_paths()

    # 确保目录存在
    for dir_path in paths.values():
        os.makedirs(dir_path, exist_ok=True)

    data_file = os.path.join(paths['data'], 'student_height_data.xlsx')

    # 步骤1: 生成数据（如果需要）
    if not skip_generation or not os.path.exists(data_file):
        data_file = generate_data(paths, n=n)
    else:
        print(f"\n使用已有数据文件: {data_file}")

    # 步骤2: 数据分析
    analyze_data(paths, data_file)

    # 步骤3: 数据可视化
    visualize_data(paths, data_file)

    print("\n" + "=" * 60)
    print("所有任务已完成！")
    print("=" * 60)
    print(f"\n输出文件位置:")
    print(f"  - 数据文件: {data_file}")
    print(f"  - 图表文件: {paths['output']}/")
    print("\n生成的图表包括:")
    print("  1. height_by_grade.png - 各年级平均身高柱状图")
    print("  2. height_by_gender.png - 男女生身高对比图")
    print("  3. height_distribution.png - 身高分布直方图")
    print("  4. boxplot_by_grade.png - 各年级身高箱线图")
    print("  5. growth_trend.png - 生长趋势折线图")
    print("  6. scatter_age_height.png - 年龄身高散点图")
    print("  7. bmi_distribution.png - BMI分布图")
    print("  8. height_heatmap.png - 身高热力图")
    print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='小学生身高数据分析与可视化系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                    # 运行完整流程（默认生成1000条数据）
  python main.py -n 500             # 生成500条数据并分析
  python main.py -s                 # 跳过数据生成，使用已有数据
  python main.py -n 2000 -s         # 生成2000条数据，但跳过生成步骤
        """
    )

    parser.add_argument(
        '-n', '--number',
        type=int,
        default=1000,
        help='生成的数据条数（默认: 1000）'
    )

    parser.add_argument(
        '-s', '--skip-generation',
        action='store_true',
        help='跳过数据生成步骤，使用已有数据文件'
    )

    args = parser.parse_args()

    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    try:
        run_full_pipeline(n=args.number, skip_generation=args.skip_generation)
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
