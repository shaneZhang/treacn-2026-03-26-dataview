"""
数据可视化层

实现数据可视化功能
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
from matplotlib import font_manager

from utils import VisualizationException, get_logger
from config import Config
from core.service import DataAnalysisService
from core.observer import EventManager, EventType


class ChartConfig:
    """图表配置类"""
    
    CHINESE_FONTS = [
        'Heiti TC', 'STHeiti', 'PingFang HK', 
        'Arial Unicode MS', 'Noto Sans CJK SC'
    ]
    
    COLORS = {
        'primary': '#2E86AB',
        'secondary': '#A23B72',
        'success': '#28A745',
        'warning': '#FFC107',
        'danger': '#DC3545',
        'info': '#17A2B8',
        'grades': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD'],
        'male': '#4A90E2',
        'female': '#E94B8A'
    }
    
    FIGURE_SIZE = {
        'small': (8, 5),
        'medium': (10, 6),
        'large': (12, 7),
        'wide': (14, 6)
    }
    
    DPI = 300
    
    @classmethod
    def setup_chinese_font(cls) -> str:
        """
        设置中文字体
        
        Returns:
            str: 使用的字体名称
        """
        available_fonts = [f.name for f in font_manager.fontManager.ttflist]
        
        for font in cls.CHINESE_FONTS:
            if font in available_fonts:
                plt.rcParams['font.sans-serif'] = [font] + plt.rcParams['font.sans-serif']
                return font
        
        return 'default'
    
    @classmethod
    def setup_matplotlib(cls) -> None:
        """设置matplotlib全局配置"""
        font = cls.setup_chinese_font()
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['figure.dpi'] = cls.DPI


ChartConfig.setup_matplotlib()


class BaseVisualizer:
    """
    可视化基类
    
    提供通用的可视化方法和配置
    
    Attributes:
        output_dir: 输出目录
        logger: 日志记录器
        config: 配置对象
    
    Example:
        >>> visualizer = BaseVisualizer('output/')
        >>> visualizer.save_figure(fig, 'chart.png')
    """
    
    def __init__(self, output_dir: Optional[str] = None) -> None:
        """
        初始化可视化器
        
        Args:
            output_dir: 输出目录，默认为配置中的output目录
        """
        self.config = Config.get_instance()
        self.output_dir = Path(output_dir or self.config.app_config['output_dir'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)
        self.event_manager = EventManager.get_instance()
    
    def save_figure(
        self, 
        fig: plt.Figure, 
        filename: str,
        tight_layout: bool = True
    ) -> str:
        """
        保存图表
        
        Args:
            fig: 图表对象
            filename: 文件名
            tight_layout: 是否使用紧凑布局
        
        Returns:
            str: 保存的文件路径
        
        Example:
            >>> path = visualizer.save_figure(fig, 'chart.png')
        """
        try:
            if tight_layout:
                fig.tight_layout()
            
            filepath = self.output_dir / filename
            fig.savefig(filepath, dpi=ChartConfig.DPI, bbox_inches='tight')
            
            self.logger.info(f"图表已保存: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"保存图表失败: {e}")
            raise VisualizationException(f"保存图表失败: {e}")
    
    def close_figure(self, fig: plt.Figure) -> None:
        """
        关闭图表
        
        Args:
            fig: 图表对象
        """
        plt.close(fig)
    
    def show_figure(self, fig: plt.Figure) -> None:
        """
        显示图表
        
        Args:
            fig: 图表对象
        """
        plt.show()


class HeightVisualizer(BaseVisualizer):
    """
    身高数据可视化器
    
    提供身高数据的各种可视化图表
    
    Example:
        >>> visualizer = HeightVisualizer('output/')
        >>> visualizer.plot_height_by_grade()
    """
    
    GRADE_ORDER = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
    
    def __init__(self, output_dir: Optional[str] = None) -> None:
        """
        初始化身高可视化器
        
        Args:
            output_dir: 输出目录
        """
        super().__init__(output_dir)
        self.analysis_service = DataAnalysisService()
    
    def plot_height_by_grade(self, save: bool = True) -> Optional[str]:
        """
        绘制各年级平均身高柱状图
        
        Args:
            save: 是否保存图表
        
        Returns:
            Optional[str]: 保存的文件路径，不保存则返回None
        
        Example:
            >>> path = visualizer.plot_height_by_grade()
        """
        try:
            grade_stats = self.analysis_service.get_grade_statistics()
            
            if grade_stats.empty:
                self.logger.warning("没有数据，无法生成图表")
                return None
            
            fig, ax = plt.subplots(figsize=ChartConfig.FIGURE_SIZE['medium'])
            
            grade_means = grade_stats['平均身高'].reindex(self.GRADE_ORDER)
            
            bars = ax.bar(
                self.GRADE_ORDER,
                grade_means,
                color=ChartConfig.COLORS['grades'],
                edgecolor='black',
                linewidth=1.2
            )
            
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height,
                    f'{height:.1f}cm',
                    ha='center',
                    va='bottom',
                    fontsize=10,
                    fontweight='bold'
                )
            
            ax.set_xlabel('年级', fontsize=12, fontweight='bold')
            ax.set_ylabel('平均身高 (cm)', fontsize=12, fontweight='bold')
            ax.set_title('各年级学生平均身高分布', fontsize=14, fontweight='bold', pad=20)
            ax.set_ylim(0, max(grade_means) * 1.15)
            ax.grid(axis='y', alpha=0.3, linestyle='--')
            
            if save:
                filepath = self.save_figure(fig, 'height_by_grade.png')
                self.event_manager.emit(
                    EventType.VISUALIZATION_COMPLETED,
                    {'chart_type': 'height_by_grade', 'file_path': filepath},
                    source='HeightVisualizer'
                )
                self.close_figure(fig)
                return filepath
            
            return None
            
        except Exception as e:
            self.logger.error(f"绘制年级身高图表失败: {e}")
            raise VisualizationException(f"绘制年级身高图表失败: {e}")
    
    def plot_height_by_gender(self, save: bool = True) -> Optional[str]:
        """
        绘制男女身高对比图
        
        Args:
            save: 是否保存图表
        
        Returns:
            Optional[str]: 保存的文件路径
        
        Example:
            >>> path = visualizer.plot_height_by_gender()
        """
        try:
            gender_stats = self.analysis_service.get_gender_statistics()
            
            if gender_stats.empty:
                self.logger.warning("没有数据，无法生成图表")
                return None
            
            fig, ax = plt.subplots(figsize=ChartConfig.FIGURE_SIZE['wide'])
            
            male_means = []
            female_means = []
            
            for grade in self.GRADE_ORDER:
                male_key = (grade, '男')
                female_key = (grade, '女')
                
                male_mean = gender_stats.loc[male_key, '平均身高'] if male_key in gender_stats.index else 0
                female_mean = gender_stats.loc[female_key, '平均身高'] if female_key in gender_stats.index else 0
                
                male_means.append(male_mean)
                female_means.append(female_mean)
            
            x = np.arange(len(self.GRADE_ORDER))
            width = 0.35
            
            bars1 = ax.bar(
                x - width / 2,
                male_means,
                width,
                label='男',
                color=ChartConfig.COLORS['male'],
                edgecolor='black'
            )
            bars2 = ax.bar(
                x + width / 2,
                female_means,
                width,
                label='女',
                color=ChartConfig.COLORS['female'],
                edgecolor='black'
            )
            
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(
                            bar.get_x() + bar.get_width() / 2.,
                            height,
                            f'{height:.1f}',
                            ha='center',
                            va='bottom',
                            fontsize=9
                        )
            
            ax.set_xlabel('年级', fontsize=12, fontweight='bold')
            ax.set_ylabel('平均身高 (cm)', fontsize=12, fontweight='bold')
            ax.set_title('各年级男女生平均身高对比', fontsize=14, fontweight='bold', pad=20)
            ax.set_xticks(x)
            ax.set_xticklabels(self.GRADE_ORDER)
            ax.legend(fontsize=11)
            ax.grid(axis='y', alpha=0.3, linestyle='--')
            
            if save:
                filepath = self.save_figure(fig, 'height_by_gender.png')
                self.event_manager.emit(
                    EventType.VISUALIZATION_COMPLETED,
                    {'chart_type': 'height_by_gender', 'file_path': filepath},
                    source='HeightVisualizer'
                )
                self.close_figure(fig)
                return filepath
            
            return None
            
        except Exception as e:
            self.logger.error(f"绘制性别身高图表失败: {e}")
            raise VisualizationException(f"绘制性别身高图表失败: {e}")
    
    def plot_height_distribution(self, save: bool = True) -> Optional[str]:
        """
        绘制身高分布直方图
        
        Args:
            save: 是否保存图表
        
        Returns:
            Optional[str]: 保存的文件路径
        
        Example:
            >>> path = visualizer.plot_height_distribution()
        """
        try:
            basic_stats = self.analysis_service.get_basic_statistics()
            
            if basic_stats['total_records'] == 0:
                self.logger.warning("没有数据，无法生成图表")
                return None
            
            with self.analysis_service.student_dao._get_session() as session:
                from models import HeightRecord
                records = session.query(HeightRecord).all()
                heights = [r.height for r in records]
            
            fig, ax = plt.subplots(figsize=ChartConfig.FIGURE_SIZE['wide'])
            
            bins = range(100, 170, 5)
            ax.hist(
                heights,
                bins=bins,
                color=ChartConfig.COLORS['info'],
                edgecolor='black',
                alpha=0.7
            )
            
            mean_height = np.mean(heights)
            median_height = np.median(heights)
            
            ax.axvline(
                mean_height,
                color='red',
                linestyle='--',
                linewidth=2,
                label=f'平均值: {mean_height:.1f}cm'
            )
            ax.axvline(
                median_height,
                color='green',
                linestyle='--',
                linewidth=2,
                label=f'中位数: {median_height:.1f}cm'
            )
            
            ax.set_xlabel('身高 (cm)', fontsize=12, fontweight='bold')
            ax.set_ylabel('人数', fontsize=12, fontweight='bold')
            ax.set_title('学生身高分布直方图', fontsize=14, fontweight='bold', pad=20)
            ax.legend(fontsize=10)
            ax.grid(axis='y', alpha=0.3, linestyle='--')
            
            if save:
                filepath = self.save_figure(fig, 'height_distribution.png')
                self.event_manager.emit(
                    EventType.VISUALIZATION_COMPLETED,
                    {'chart_type': 'height_distribution', 'file_path': filepath},
                    source='HeightVisualizer'
                )
                self.close_figure(fig)
                return filepath
            
            return None
            
        except Exception as e:
            self.logger.error(f"绘制身高分布图表失败: {e}")
            raise VisualizationException(f"绘制身高分布图表失败: {e}")
    
    def plot_boxplot_by_grade(self, save: bool = True) -> Optional[str]:
        """
        绘制各年级身高箱线图
        
        Args:
            save: 是否保存图表
        
        Returns:
            Optional[str]: 保存的文件路径
        
        Example:
            >>> path = visualizer.plot_boxplot_by_grade()
        """
        try:
            with self.analysis_service.student_dao._get_session() as session:
                from models import HeightRecord
                records = session.query(HeightRecord).all()
                
                data_by_grade = {grade: [] for grade in self.GRADE_ORDER}
                for record in records:
                    if record.grade_at_record in data_by_grade:
                        data_by_grade[record.grade_at_record].append(record.height)
            
            if not any(data_by_grade.values()):
                self.logger.warning("没有数据，无法生成图表")
                return None
            
            fig, ax = plt.subplots(figsize=ChartConfig.FIGURE_SIZE['wide'])
            
            data = [data_by_grade[grade] for grade in self.GRADE_ORDER]
            
            box_plot = ax.boxplot(
                data,
                labels=self.GRADE_ORDER,
                patch_artist=True
            )
            
            for patch, color in zip(box_plot['boxes'], ChartConfig.COLORS['grades']):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            
            ax.set_xlabel('年级', fontsize=12, fontweight='bold')
            ax.set_ylabel('身高 (cm)', fontsize=12, fontweight='bold')
            ax.set_title('各年级学生身高分布箱线图', fontsize=14, fontweight='bold', pad=20)
            ax.grid(axis='y', alpha=0.3, linestyle='--')
            
            if save:
                filepath = self.save_figure(fig, 'boxplot_by_grade.png')
                self.event_manager.emit(
                    EventType.VISUALIZATION_COMPLETED,
                    {'chart_type': 'boxplot_by_grade', 'file_path': filepath},
                    source='HeightVisualizer'
                )
                self.close_figure(fig)
                return filepath
            
            return None
            
        except Exception as e:
            self.logger.error(f"绘制箱线图失败: {e}")
            raise VisualizationException(f"绘制箱线图失败: {e}")
    
    def plot_growth_trend(self, save: bool = True) -> Optional[str]:
        """
        绘制生长趋势折线图
        
        Args:
            save: 是否保存图表
        
        Returns:
            Optional[str]: 保存的文件路径
        
        Example:
            >>> path = visualizer.plot_growth_trend()
        """
        try:
            grade_stats = self.analysis_service.get_grade_statistics()
            gender_stats = self.analysis_service.get_gender_statistics()
            
            if grade_stats.empty:
                self.logger.warning("没有数据，无法生成图表")
                return None
            
            fig, ax = plt.subplots(figsize=ChartConfig.FIGURE_SIZE['wide'])
            
            overall_means = grade_stats['平均身高'].reindex(self.GRADE_ORDER)
            ax.plot(
                self.GRADE_ORDER,
                overall_means,
                marker='o',
                linewidth=3,
                markersize=10,
                color=ChartConfig.COLORS['primary'],
                label='总体平均',
                markerfacecolor='white',
                markeredgewidth=2
            )
            
            male_means = []
            female_means = []
            for grade in self.GRADE_ORDER:
                male_key = (grade, '男')
                female_key = (grade, '女')
                male_means.append(
                    gender_stats.loc[male_key, '平均身高'] if male_key in gender_stats.index else None
                )
                female_means.append(
                    gender_stats.loc[female_key, '平均身高'] if female_key in gender_stats.index else None
                )
            
            ax.plot(
                self.GRADE_ORDER,
                male_means,
                marker='s',
                linewidth=2.5,
                markersize=8,
                color=ChartConfig.COLORS['male'],
                label='男生',
                linestyle='--'
            )
            ax.plot(
                self.GRADE_ORDER,
                female_means,
                marker='^',
                linewidth=2.5,
                markersize=8,
                color=ChartConfig.COLORS['female'],
                label='女生',
                linestyle='--'
            )
            
            for i, (grade, height) in enumerate(zip(self.GRADE_ORDER, overall_means)):
                ax.annotate(
                    f'{height:.1f}cm',
                    (i, height),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha='center',
                    fontsize=9,
                    fontweight='bold'
                )
            
            ax.set_xlabel('年级', fontsize=12, fontweight='bold')
            ax.set_ylabel('平均身高 (cm)', fontsize=12, fontweight='bold')
            ax.set_title('各年级身高生长趋势', fontsize=14, fontweight='bold', pad=20)
            ax.legend(fontsize=11, loc='upper left')
            ax.grid(True, alpha=0.3, linestyle='--')
            
            if save:
                filepath = self.save_figure(fig, 'growth_trend.png')
                self.event_manager.emit(
                    EventType.VISUALIZATION_COMPLETED,
                    {'chart_type': 'growth_trend', 'file_path': filepath},
                    source='HeightVisualizer'
                )
                self.close_figure(fig)
                return filepath
            
            return None
            
        except Exception as e:
            self.logger.error(f"绘制生长趋势图表失败: {e}")
            raise VisualizationException(f"绘制生长趋势图表失败: {e}")
    
    def plot_bmi_distribution(self, save: bool = True) -> Optional[str]:
        """
        绘制BMI分布图
        
        Args:
            save: 是否保存图表
        
        Returns:
            Optional[str]: 保存的文件路径
        
        Example:
            >>> path = visualizer.plot_bmi_distribution()
        """
        try:
            bmi_dist, bmi_by_grade = self.analysis_service.get_bmi_statistics()
            
            if not bmi_dist:
                self.logger.warning("没有数据，无法生成图表")
                return None
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=ChartConfig.FIGURE_SIZE['large'])
            
            categories = ['偏瘦', '正常', '超重', '肥胖']
            values = [bmi_dist.get(cat, 0) for cat in categories]
            colors = ['#3498DB', '#2ECC71', '#F39C12', '#E74C3C']
            
            ax1.pie(
                values,
                labels=categories,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                explode=(0.05, 0, 0, 0.05)
            )
            ax1.set_title('BMI分布饼图', fontsize=12, fontweight='bold')
            
            if not bmi_by_grade.empty:
                bmi_by_grade_plot = bmi_by_grade.reindex(self.GRADE_ORDER)
                bmi_by_grade_plot.plot(
                    kind='bar',
                    ax=ax2,
                    color=colors,
                    edgecolor='black'
                )
                ax2.set_xlabel('年级', fontsize=10, fontweight='bold')
                ax2.set_ylabel('人数', fontsize=10, fontweight='bold')
                ax2.set_title('各年级BMI分类分布', fontsize=12, fontweight='bold')
                ax2.legend(title='BMI分类', fontsize=9)
                ax2.set_xticklabels(self.GRADE_ORDER, rotation=45, ha='right')
                ax2.grid(axis='y', alpha=0.3, linestyle='--')
            
            if save:
                filepath = self.save_figure(fig, 'bmi_distribution.png')
                self.event_manager.emit(
                    EventType.VISUALIZATION_COMPLETED,
                    {'chart_type': 'bmi_distribution', 'file_path': filepath},
                    source='HeightVisualizer'
                )
                self.close_figure(fig)
                return filepath
            
            return None
            
        except Exception as e:
            self.logger.error(f"绘制BMI分布图表失败: {e}")
            raise VisualizationException(f"绘制BMI分布图表失败: {e}")
    
    def generate_all_plots(self) -> List[str]:
        """
        生成所有图表
        
        Returns:
            List[str]: 所有保存的图表文件路径列表
        
        Example:
            >>> paths = visualizer.generate_all_plots()
        """
        self.logger.info("开始生成所有图表...")
        
        plot_methods = [
            ('年级身高柱状图', self.plot_height_by_grade),
            ('性别身高对比图', self.plot_height_by_gender),
            ('身高分布直方图', self.plot_height_distribution),
            ('年级身高箱线图', self.plot_boxplot_by_grade),
            ('生长趋势图', self.plot_growth_trend),
            ('BMI分布图', self.plot_bmi_distribution)
        ]
        
        saved_paths = []
        
        for name, method in plot_methods:
            try:
                self.logger.info(f"正在生成: {name}")
                path = method(save=True)
                if path:
                    saved_paths.append(path)
            except Exception as e:
                self.logger.error(f"生成{name}失败: {e}")
        
        self.logger.info(f"图表生成完成，共生成{len(saved_paths)}个图表")
        
        return saved_paths
