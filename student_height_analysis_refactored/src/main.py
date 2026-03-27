#!/usr/bin/env python3
"""
小学生身高数据分析与可视化系统 - 重构版

本程序用于分析小学各年级学生的身高数据，包括：
- 基础统计分析
- 年级、性别、年龄分组分析
- 生长趋势分析
- BMI分析
- 数据可视化图表生成

作者: AI Assistant
版本: 2.0.0
日期: 2026-03-27
"""

import os
import sys
import argparse
from typing import Optional

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.settings import get_settings
from src.core.logger import get_logger
from src.core.observer import (
    get_data_change_subject,
    LoggingObserver,
    CacheInvalidationObserver,
)
from src.dao import create_tables, drop_tables, get_database_manager
from src.service import DataGeneratorService, AnalysisService
from src.visualization import HeightVisualizer
from src.core.exceptions import BaseAppException


def setup_logging() -> None:
    """设置日志系统"""
    # 日志在导入时已经通过get_logger自动初始化
    pass


def setup_observers() -> None:
    """设置观察者"""
    subject = get_data_change_subject()
    
    # 添加日志观察者
    logging_observer = LoggingObserver()
    subject.attach(logging_observer)
    
    # 添加缓存失效观察者
    cache_observer = CacheInvalidationObserver()
    subject.attach(cache_observer)


def check_dependencies() -> bool:
    """检查必要的依赖包
    
    Returns:
        是否所有依赖都已安装
    """
    required_packages = [
        'pandas', 'numpy', 'matplotlib', 'openpyxl',
        'sqlalchemy', 'alembic', 'pydantic'
    ]
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


def init_database() -> None:
    """初始化数据库"""
    logger = get_logger(__name__)
    logger.info("初始化数据库...")
    
    try:
        create_tables()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def generate_data(n: int = 1000) -> int:
    """生成模拟数据
    
    Args:
        n: 生成数据条数
        
    Returns:
        生成的记录数
    """
    logger = get_logger(__name__)
    logger.info(f"开始生成{n}条模拟数据...")
    
    generator = DataGeneratorService()
    
    # 生成数据
    student_data = generator.generate_student_data(n=n)
    
    # 导入到数据库
    from src.dao.student_dao import StudentDAO
    dao = StudentDAO()
    
    # 批量创建
    entities = dao.create_many(student_data)
    
    logger.info(f"成功生成并导入{len(entities)}条数据")
    return len(entities)


def analyze_data() -> None:
    """执行数据分析"""
    logger = get_logger(__name__)
    logger.info("开始数据分析...")
    
    analysis_service = AnalysisService()
    report = analysis_service.generate_report()
    
    print("\n" + report)
    
    logger.info("数据分析完成")


def visualize_data() -> None:
    """生成可视化图表"""
    logger = get_logger(__name__)
    logger.info("开始生成可视化图表...")
    
    visualizer = HeightVisualizer()
    chart_files = visualizer.generate_all_charts()
    
    print("\n生成的图表:")
    for filepath in chart_files:
        print(f"  - {os.path.basename(filepath)}")
    
    logger.info(f"成功生成{len(chart_files)}个图表")


def export_data(output_path: str) -> str:
    """导出数据到Excel
    
    Args:
        output_path: 输出文件路径
        
    Returns:
        导出的文件路径
    """
    logger = get_logger(__name__)
    logger.info(f"导出数据到: {output_path}")
    
    generator = DataGeneratorService()
    filepath = generator.export_to_excel(output_path)
    
    logger.info(f"数据导出完成: {filepath}")
    return filepath


def import_data(input_path: str) -> int:
    """从Excel导入数据
    
    Args:
        input_path: 输入文件路径
        
    Returns:
        导入的记录数
    """
    logger = get_logger(__name__)
    logger.info(f"从Excel导入数据: {input_path}")
    
    generator = DataGeneratorService()
    count = generator.import_from_excel(input_path)
    
    logger.info(f"成功导入{count}条数据")
    return count


def run_full_pipeline(n: int = 1000, skip_generation: bool = False) -> None:
    """运行完整的数据分析流程
    
    Args:
        n: 生成的数据条数
        skip_generation: 是否跳过数据生成步骤
    """
    logger = get_logger(__name__)
    
    settings = get_settings()
    
    print("\n" + "=" * 60)
    print("小学生身高数据分析与可视化系统 v2.0")
    print("=" * 60)
    
    # 步骤1: 初始化
    print("\n步骤 1: 初始化数据库")
    print("-" * 60)
    init_database()
    
    # 步骤2: 生成/导入数据
    print("\n步骤 2: 数据准备")
    print("-" * 60)
    
    from src.dao.student_dao import StudentDAO
    dao = StudentDAO()
    
    if not skip_generation or dao.count() == 0:
        count = generate_data(n=n)
        print(f"已生成 {count} 条学生数据")
    else:
        print(f"使用已有数据: {dao.count()} 条")
    
    # 步骤3: 数据分析
    print("\n步骤 3: 数据分析")
    print("-" * 60)
    analyze_data()
    
    # 步骤4: 数据可视化
    print("\n步骤 4: 数据可视化")
    print("-" * 60)
    visualize_data()
    
    print("\n" + "=" * 60)
    print("所有任务已完成！")
    print("=" * 60)
    print(f"\n输出文件位置:")
    print(f"  - 输出目录: {settings.output_path}")
    print(f"  - 日志文件: {settings.log_file}")
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


def main() -> int:
    """主函数
    
    Returns:
        退出代码
    """
    parser = argparse.ArgumentParser(
        description='小学生身高数据分析与可视化系统 v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                    # 运行完整流程（默认生成1000条数据）
  python main.py -n 500             # 生成500条数据并分析
  python main.py -s                 # 跳过数据生成，使用已有数据
  python main.py --init-db          # 仅初始化数据库
  python main.py --drop-db          # 删除并重新创建数据库
  python main.py --import data.xlsx # 从Excel导入数据
  python main.py --export output.xlsx # 导出数据到Excel
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
    
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='仅初始化数据库'
    )
    
    parser.add_argument(
        '--drop-db',
        action='store_true',
        help='删除数据库表（危险操作）'
    )
    
    parser.add_argument(
        '--import',
        dest='import_file',
        type=str,
        help='从Excel文件导入数据'
    )
    
    parser.add_argument(
        '--export',
        dest='export_file',
        type=str,
        help='导出数据到Excel文件'
    )
    
    args = parser.parse_args()
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    # 设置日志和观察者
    setup_logging()
    setup_observers()
    
    logger = get_logger(__name__)
    
    try:
        # 处理特殊命令
        if args.drop_db:
            logger.warning("正在删除数据库表...")
            drop_tables()
            logger.info("数据库表已删除")
            return 0
        
        if args.init_db:
            init_database()
            return 0
        
        if args.import_file:
            init_database()
            count = import_data(args.import_file)
            print(f"成功导入 {count} 条数据")
            return 0
        
        if args.export_file:
            filepath = export_data(args.export_file)
            print(f"数据已导出到: {filepath}")
            return 0
        
        # 运行完整流程
        run_full_pipeline(n=args.number, skip_generation=args.skip_generation)
        return 0
        
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        return 130
    except BaseAppException as e:
        logger.error(f"应用错误: {e}")
        print(f"\n错误: {e.message}")
        return 1
    except Exception as e:
        logger.exception(f"未预期的错误: {e}")
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
