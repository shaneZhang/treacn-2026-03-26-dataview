"""
小学生身高数据分析与可视化系统 - 主程序入口

重构后的系统采用分层架构：
- 数据访问层(DAO)
- 业务逻辑层(Service)
- 表现层(Visualization)
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import date

from config import Config
from core.database import DatabaseFactory
from core.observer import EventManager, LogObserver, CacheObserver
from core import (
    StudentService,
    DataAnalysisService,
    DataImportExportService,
    HeightVisualizer
)
from utils import DataGenerator, get_logger


def setup_environment() -> None:
    """设置环境"""
    config = Config.get_instance()
    
    for dir_path in [
        config.app_config['data_dir'],
        config.app_config['output_dir'],
        Path(config.log_config['file_path']).parent
    ]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def setup_observers() -> None:
    """设置观察者"""
    event_manager = EventManager.get_instance()
    
    log_observer = LogObserver()
    cache_observer = CacheObserver()
    
    event_manager.attach(log_observer)
    event_manager.attach(cache_observer)


def initialize_database() -> None:
    """初始化数据库"""
    logger = get_logger(__name__)
    
    db_factory = DatabaseFactory.get_instance()
    db_factory.create_tables()
    
    logger.info("数据库初始化完成")


def generate_sample_data(n: int = 1000) -> None:
    """
    生成示例数据
    
    Args:
        n: 数据条数
    """
    logger = get_logger(__name__)
    
    generator = DataGenerator()
    
    generator.generate_standard_heights()
    
    count = generator.generate_and_save(n=n)
    
    logger.info(f"示例数据生成完成，共{count}条")


def run_analysis() -> None:
    """运行数据分析"""
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("开始数据分析")
    logger.info("=" * 60)
    
    analysis_service = DataAnalysisService()
    
    basic_stats = analysis_service.get_basic_statistics()
    logger.info(f"基础统计: {basic_stats}")
    
    grade_stats = analysis_service.get_grade_statistics()
    logger.info(f"年级统计:\n{grade_stats}")
    
    growth_analysis = analysis_service.get_growth_analysis()
    logger.info(f"生长趋势:\n{growth_analysis}")
    
    percentile_analysis = analysis_service.get_percentile_analysis()
    logger.info(f"百分位数:\n{percentile_analysis}")
    
    logger.info("数据分析完成")


def run_visualization() -> None:
    """运行数据可视化"""
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("开始数据可视化")
    logger.info("=" * 60)
    
    visualizer = HeightVisualizer()
    
    paths = visualizer.generate_all_plots()
    
    logger.info(f"可视化完成，共生成{len(paths)}个图表")
    
    for path in paths:
        logger.info(f"  - {path}")


def export_report(output_path: str = None) -> str:
    """
    导出分析报告
    
    Args:
        output_path: 输出路径
    
    Returns:
        str: 报告文件路径
    """
    logger = get_logger(__name__)
    
    if output_path is None:
        config = Config.get_instance()
        output_path = str(
            Path(config.app_config['output_dir']) / 'analysis_report.xlsx'
        )
    
    import_service = DataImportExportService()
    path = import_service.export_statistics_report(output_path)
    
    logger.info(f"分析报告已导出: {path}")
    
    return path


def run_full_pipeline(
    n: int = 1000,
    skip_generation: bool = False,
    skip_analysis: bool = False,
    skip_visualization: bool = False
) -> None:
    """
    运行完整流程
    
    Args:
        n: 生成数据条数
        skip_generation: 是否跳过数据生成
        skip_analysis: 是否跳过数据分析
        skip_visualization: 是否跳过数据可视化
    """
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("小学生身高数据分析与可视化系统")
    logger.info("=" * 60)
    
    setup_environment()
    setup_observers()
    initialize_database()
    
    if not skip_generation:
        generate_sample_data(n)
    
    if not skip_analysis:
        run_analysis()
    
    if not skip_visualization:
        run_visualization()
    
    export_report()
    
    logger.info("=" * 60)
    logger.info("所有任务已完成！")
    logger.info("=" * 60)


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(
        description='小学生身高数据分析与可视化系统（重构版）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                    # 运行完整流程（默认生成1000条数据）
  python main.py -n 500             # 生成500条数据并分析
  python main.py --skip-generation  # 跳过数据生成，使用已有数据
  python main.py --analysis-only    # 仅运行数据分析
  python main.py --visualization-only  # 仅运行数据可视化
        """
    )
    
    parser.add_argument(
        '-n', '--number',
        type=int,
        default=1000,
        help='生成的数据条数（默认: 1000）'
    )
    
    parser.add_argument(
        '--skip-generation',
        action='store_true',
        help='跳过数据生成步骤'
    )
    
    parser.add_argument(
        '--skip-analysis',
        action='store_true',
        help='跳过数据分析步骤'
    )
    
    parser.add_argument(
        '--skip-visualization',
        action='store_true',
        help='跳过数据可视化步骤'
    )
    
    parser.add_argument(
        '--analysis-only',
        action='store_true',
        help='仅运行数据分析'
    )
    
    parser.add_argument(
        '--visualization-only',
        action='store_true',
        help='仅运行数据可视化'
    )
    
    parser.add_argument(
        '--export-only',
        action='store_true',
        help='仅导出分析报告'
    )
    
    args = parser.parse_args()
    
    try:
        if args.analysis_only:
            setup_environment()
            setup_observers()
            initialize_database()
            run_analysis()
        elif args.visualization_only:
            setup_environment()
            setup_observers()
            initialize_database()
            run_visualization()
        elif args.export_only:
            setup_environment()
            setup_observers()
            initialize_database()
            export_report()
        else:
            run_full_pipeline(
                n=args.number,
                skip_generation=args.skip_generation,
                skip_analysis=args.skip_analysis,
                skip_visualization=args.skip_visualization
            )
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
