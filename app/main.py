#!/usr/bin/env python3
"""
Main application entry point for the Student Height Analysis System.

This module provides the command-line interface and main application logic
for the student height data analysis and visualization system.
"""

import os
import sys
from typing import Optional, List, Dict, Any
import argparse
from datetime import date

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import get_settings
from app.config.database import get_db_pool, init_database
from app.service import (
    StudentService,
    StatisticsService,
    DataImportExportService,
    VisualizationService
)
from app.utils.logger import get_logger
from app.utils.observer import (
    get_event_manager,
    LoggingObserver,
    StatisticsUpdateObserver
)
from app.utils.exceptions import ApplicationError

logger = get_logger(__name__)


class StudentHeightAnalysisApp:
    """
    Main application class for the Student Height Analysis System.

    This class orchestrates all the services and provides high-level
    functionality for the application.
    """

    def __init__(self):
        """Initialize the application."""
        self.settings = get_settings()
        self._db_pool = None
        self._event_manager = None
        self._services: Dict[str, Any] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the application services and observers."""
        if self._initialized:
            return

        logger.info("Initializing Student Height Analysis System...")

        # Initialize database
        init_database()
        self._db_pool = get_db_pool()

        # Initialize event manager
        self._event_manager = get_event_manager()

        # Initialize services first (needed for observers that depend on them)
        self._init_services()

        # Set up observers
        self._setup_observers()

        self._initialized = True
        logger.info("Application initialized successfully")

    def _init_services(self) -> None:
        """Initialize core services needed for observers."""
        # Create services that observers depend on
        _ = self.student_service
        _ = self.statistics_service
        logger.debug("Core services initialized")

    def _setup_observers(self) -> None:
        """Set up event observers."""
        observers = [
            LoggingObserver(),
            StatisticsUpdateObserver(self.statistics_service),
        ]

        for observer in observers:
            self._event_manager.add_observer(observer)
            logger.debug(f"Added observer: {observer.__class__.__name__}")

    def _get_service(self, service_class, *args, **kwargs):
        """
        Get or create a service instance.

        Args:
            service_class: The service class to instantiate.
            *args: Positional arguments for the service constructor.
            **kwargs: Keyword arguments for the service constructor.

        Returns:
            An instance of the requested service.
        """
        service_name = service_class.__name__
        if service_name not in self._services:
            session = self._db_pool.get_session()
            self._services[service_name] = service_class(session, *args, **kwargs)
        return self._services[service_name]

    @property
    def student_service(self) -> StudentService:
        """Get the student service instance."""
        return self._get_service(StudentService)

    @property
    def statistics_service(self) -> StatisticsService:
        """Get the statistics service instance."""
        return self._get_service(StatisticsService)

    @property
    def import_export_service(self) -> DataImportExportService:
        """Get the import/export service instance."""
        return self._get_service(DataImportExportService)

    @property
    def visualization_service(self) -> VisualizationService:
        """Get the visualization service instance."""
        return self._get_service(VisualizationService)

    def generate_sample_data(
        self,
        num_students: int = 1000,
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate sample student data and save to Excel.

        Args:
            num_students: Number of students to generate.
            output_file: Output Excel file path.

        Returns:
            str: Path to the generated Excel file.
        """
        import pandas as pd
        import numpy as np

        logger.info(f"Generating {num_students} sample student records...")

        names = [
            '张伟', '王芳', '李娜', '刘洋', '陈明', '杨静', '赵磊', '黄丽',
            '周强', '吴敏', '徐涛', '孙艳', '胡军', '朱婷', '郭鹏', '何欣',
            '高峰', '林琳', '罗勇', '梁颖', '宋晨', '唐悦', '许航', '韩冰',
            '冯涛', '董洁', '萧宇', '程倩', '蔡博', '彭娟', '潘帅', '袁婷',
            '蒋巍', '沈娜', '卢凯', '丁玲', '钱鑫', '崔妍', '康磊', '毛颖'
        ]

        grades = StudentService.GRADE_ORDER

        data = []
        for i in range(1, num_students + 1):
            grade = np.random.choice(grades)
            grade_index = grades.index(grade)
            gender = np.random.choice(['男', '女'])

            base_height = {
                '一年级': {'男': 120, '女': 119},
                '二年级': {'男': 125, '女': 124},
                '三年级': {'男': 130, '女': 129},
                '四年级': {'男': 135, '女': 134},
                '五年级': {'男': 140, '女': 140},
                '六年级': {'男': 147, '女': 148},
            }[grade][gender]

            height = np.random.normal(loc=base_height, scale=5)
            weight = np.random.normal(loc=40, scale=10)

            student = {
                'student_id': i,
                'name': np.random.choice(names),
                'gender': gender,
                'grade': grade,
                'age': 7 + grade_index + np.random.randint(-1, 2),
                'height_cm': round(float(np.clip(height, 100, 170)), 1),
                'weight_kg': round(float(np.clip(weight, 20, 80)), 1),
                'enrollment_date': date.today().replace(year=date.today().year - grade_index)
            }
            data.append(student)

        df = pd.DataFrame(data)

        if output_file is None:
            output_dir = self.settings.output_dir
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, 'sample_student_data.xlsx')

        # Rename columns to Chinese for Excel
        column_mapping = {
            'student_id': '学生ID',
            'name': '姓名',
            'gender': '性别',
            'grade': '年级',
            'age': '年龄',
            'height_cm': '身高(cm)',
            'weight_kg': '体重(kg)',
            'enrollment_date': '入学日期'
        }
        df = df.rename(columns=column_mapping)

        df.to_excel(output_file, index=False)
        logger.info(f"Sample data generated and saved to: {output_file}")

        return output_file

    def run_full_analysis(
        self,
        generate_visualizations: bool = True,
        export_statistics: bool = True
    ) -> Dict[str, Any]:
        """
        Run a complete analysis including statistics and visualizations.

        Args:
            generate_visualizations: Whether to generate visualizations.
            export_statistics: Whether to export statistics to Excel.

        Returns:
            Dict[str, Any]: Analysis results including statistics and file paths.
        """
        logger.info("Starting full analysis...")

        results = {
            'timestamp': date.today().isoformat(),
            'basic_statistics': {},
            'grade_statistics': [],
            'visualizations': {},
            'export_files': []
        }

        # Generate statistics
        basic_stats = self.student_service.calculate_basic_statistics()
        results['basic_statistics'] = basic_stats

        for grade in StudentService.GRADE_ORDER:
            grade_stats = self.statistics_service.generate_grade_statistics(grade, save=True)
            results['grade_statistics'].append(grade_stats)

        # Generate comparison report
        comparison_report = self.statistics_service.generate_comparison_report(output_format='text')
        logger.info("\n" + comparison_report)

        # Generate visualizations
        if generate_visualizations:
            viz_results = self.visualization_service.generate_all_plots()
            results['visualizations'] = viz_results

        # Export statistics
        if export_statistics:
            output_dir = self.settings.output_dir
            os.makedirs(output_dir, exist_ok=True)
            stats_file = os.path.join(output_dir, 'statistics_report.xlsx')
            export_result = self.import_export_service.export_statistics_to_excel(stats_file)
            results['export_files'].append(export_result)

        logger.info("Full analysis completed successfully!")
        return results

    def cleanup(self) -> None:
        """Clean up application resources."""
        for service in self._services.values():
            if hasattr(service, 'close'):
                service.close()

        if self._db_pool:
            self._db_pool.dispose()

        self._services.clear()
        self._initialized = False
        logger.info("Application cleaned up")


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        description='Student Height Analysis System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s generate-samples --num-students 1000
  %(prog)s import --file sample_data.xlsx
  %(prog)s analyze
  %(prog)s export --file output.xlsx
  %(prog)s visualize
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Generate samples command
    gen_parser = subparsers.add_parser('generate-samples', help='Generate sample student data')
    gen_parser.add_argument('--num-students', type=int, default=1000, help='Number of students to generate')
    gen_parser.add_argument('--output-file', help='Output Excel file path')

    # Import command
    import_parser = subparsers.add_parser('import', help='Import data from Excel')
    import_parser.add_argument('--file', required=True, help='Excel file to import')
    import_parser.add_argument('--overwrite', action='store_true', help='Overwrite existing records')
    import_parser.add_argument('--sync-mode', choices=['upsert', 'append', 'replace'], default='upsert', help='Synchronization mode')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export data to Excel')
    export_parser.add_argument('--file', required=True, help='Output Excel file path')
    export_parser.add_argument('--grade', help='Optional grade filter')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run statistical analysis')
    analyze_parser.add_argument('--grade', help='Optional grade filter')
    analyze_parser.add_argument('--export-stats', action='store_true', help='Export statistics to Excel')

    # Visualize command
    visualize_parser = subparsers.add_parser('visualize', help='Generate visualizations')
    visualize_parser.add_argument('--type', choices=['all', 'height_by_grade', 'height_by_gender', 'distribution', 'boxplot', 'growth', 'bmi', 'scatter'], default='all', help='Type of visualization')
    visualize_parser.add_argument('--grade', help='Optional grade filter')
    visualize_parser.add_argument('--output-dir', help='Output directory for visualizations')

    # Full analysis command
    full_parser = subparsers.add_parser('full-analysis', help='Run complete analysis with visualizations')
    full_parser.add_argument('--no-viz', action='store_true', help='Skip visualization generation')
    full_parser.add_argument('--no-export', action='store_true', help='Skip statistics export')

    # Stats report command
    subparsers.add_parser('stats-report', help='Generate statistics report')

    return parser.parse_args()


def main() -> int:
    """
    Main function to run the application from command line.

    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    args = parse_args()

    if not args.command:
        print("Please specify a command. Use --help for available commands.")
        return 1

    app = StudentHeightAnalysisApp()

    try:
        app.initialize()

        if args.command == 'generate-samples':
            app.generate_sample_data(args.num_students, args.output_file)

        elif args.command == 'import':
            result = app.import_export_service.sync_excel_to_database(
                args.file,
                sync_mode=args.sync_mode
            )
            print(f"\nImport Result:")
            print(f"  Total records: {result.get('total', 0)}")
            print(f"  Created: {result.get('created', 0)}")
            print(f"  Updated: {result.get('updated', 0)}")
            print(f"  Skipped: {result.get('skipped', 0)}")
            if result.get('errors'):
                print(f"  Errors: {len(result['errors'])}")

        elif args.command == 'export':
            result = app.import_export_service.export_to_excel(
                args.file,
                grade=args.grade
            )
            print(f"Exported {result.get('exported_count', 0)} records to {result.get('file_path')}")

        elif args.command == 'analyze':
            if args.grade:
                stats = app.statistics_service.generate_grade_statistics(args.grade)
                print(f"\nStatistics for {args.grade}:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
            else:
                basic_stats = app.student_service.calculate_basic_statistics()
                print("\nBasic Statistics:")
                for key, value in basic_stats.items():
                    print(f"  {key}: {value}")

            if args.export_stats:
                output_dir = app.settings.output_dir
                os.makedirs(output_dir, exist_ok=True)
                stats_file = os.path.join(output_dir, 'statistics_report.xlsx')
                app.import_export_service.export_statistics_to_excel(stats_file)
                print(f"\nStatistics exported to: {stats_file}")

        elif args.command == 'visualize':
            viz_service = app.visualization_service

            if args.output_dir:
                viz_service.output_dir = args.output_dir
                os.makedirs(args.output_dir, exist_ok=True)

            if args.type == 'all':
                results = viz_service.generate_all_plots()
                print(f"Generated {len(results)} visualizations:")
                for name, path in results.items():
                    print(f"  {name}: {path}")
            else:
                plot_methods = {
                    'height_by_grade': viz_service.plot_height_by_grade,
                    'height_by_gender': viz_service.plot_height_by_gender,
                    'distribution': viz_service.plot_height_distribution,
                    'boxplot': viz_service.plot_boxplot_by_grade,
                    'growth': viz_service.plot_growth_trend,
                    'bmi': viz_service.plot_bmi_distribution,
                    'scatter': viz_service.plot_scatter_age_height
                }

                method = plot_methods.get(args.type)
                if method:
                    if args.type == 'height_by_gender':
                        path = method(grade=args.grade)
                    else:
                        path = method()
                    print(f"Generated visualization: {path}")
                else:
                    print(f"Unknown visualization type: {args.type}")
                    return 1

        elif args.command == 'full-analysis':
            results = app.run_full_analysis(
                generate_visualizations=not args.no_viz,
                export_statistics=not args.no_export
            )

            print("\n=== Analysis Results ===")
            print(f"Total Students: {results['basic_statistics'].get('total_students', 0)}")
            print(f"Average Height: {results['basic_statistics'].get('average_height', 'N/A')} cm")

            if results.get('visualizations'):
                print(f"\nGenerated {len(results['visualizations'])} visualizations")

            if results.get('export_files'):
                print(f"\nExported {len(results['export_files'])} files")

        elif args.command == 'stats-report':
            report = app.statistics_service.generate_comparison_report(output_format='text')
            print(report)

        else:
            print(f"Unknown command: {args.command}")
            return 1

    except ApplicationError as e:
        logger.error(f"Application error: {e}")
        print(f"\nError: {e.message}")
        if e.details:
            print(f"Details: {e.details}")
        return 1

    except Exception as e:
        logger.exception("Unexpected error")
        print(f"\nUnexpected error: {e}")
        return 1

    finally:
        app.cleanup()

    return 0


if __name__ == '__main__':
    sys.exit(main())
