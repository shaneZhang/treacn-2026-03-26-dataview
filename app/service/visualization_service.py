"""
Visualization service for generating charts and graphs.

This module provides functionality for generating various visualizations
of student height data using matplotlib.
"""

from typing import Optional, Dict, Any, List, Tuple
import os
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

from app.service.base_service import BaseService
from app.service.student_service import StudentService
from app.utils.observer import EventType
from app.utils.logger import get_logger
from app.utils.exceptions import VisualizationError

logger = get_logger(__name__)

# Configure matplotlib for Chinese support
def _configure_matplotlib():
    """Configure matplotlib for Chinese font support."""
    # Try to find and use a Chinese font
    chinese_fonts = ['Heiti TC', 'STHeiti', 'PingFang HK', 'Arial Unicode MS', 'Noto Sans CJK SC',
                     'Microsoft YaHei', 'SimHei', 'WenQuanYi Micro Hei']

    available_fonts = [f.name for f in font_manager.fontManager.ttflist]

    # Find the first available Chinese font
    selected_font = None
    for font in chinese_fonts:
        if font in available_fonts:
            selected_font = font
            break

    if selected_font:
        plt.rcParams['font.sans-serif'] = [selected_font] + plt.rcParams['font.sans-serif']
        logger.debug(f"Using Chinese font: {selected_font}")
    else:
        logger.warning("No suitable Chinese font found. Chinese characters may display as squares.")

    # Fix negative sign display
    plt.rcParams['axes.unicode_minus'] = False

# Configure matplotlib at module load time
_configure_matplotlib()


class VisualizationService(BaseService):
    """
    Service class for generating data visualizations.

    This class provides methods for creating various charts and graphs
    to visualize student height data.
    """

    def __init__(self, session=None, output_dir: str = "./output"):
        """
        Initialize the visualization service.

        Args:
            session: Optional SQLAlchemy database session.
            output_dir: Directory to save generated visualizations.
        """
        super().__init__(session)
        self._student_service = StudentService(session)
        self.output_dir = output_dir
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Ensure the output directory exists."""
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_output_path(self, filename: str) -> str:
        """
        Get the full output path for a file.

        Args:
            filename: Name of the output file. If absolute path is provided OR
                      if the filename contains a directory path component,
                      it will be used as-is after ensuring the directory exists.

        Returns:
            str: Full path to the output file.
        """
        # If filename is absolute OR has a directory component,
        # use it directly after ensuring dir exists
        filename_dir = os.path.dirname(filename)
        if os.path.isabs(filename) or filename_dir:
            if filename_dir:
                os.makedirs(filename_dir, exist_ok=True)
            return filename
        
        # For simple filenames with no path, join with self.output_dir
        return os.path.join(self.output_dir, filename)

    def plot_height_by_grade(
        self,
        save: bool = True,
        show: bool = False,
        filename: str = "height_by_grade.png"
    ) -> Optional[str]:
        """
        Generate a bar chart of average height by grade.

        Args:
            save: Whether to save the plot to file.
            show: Whether to display the plot.
            filename: Output filename.

        Returns:
            Optional[str]: Path to saved file if save is True, None otherwise.

        Raises:
            VisualizationError: If plot generation fails.
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            grade_means = []
            for grade in StudentService.GRADE_ORDER:
                stats = self._student_service.calculate_grade_statistics(grade)
                grade_means.append(stats.get('average_height', 0))

            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
            bars = ax.bar(
                StudentService.GRADE_ORDER,
                grade_means,
                color=colors,
                edgecolor='black',
                linewidth=1.2
            )

            # Add value labels
            for bar in bars:
                height = bar.get_height()
                if height > 0:
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
            ax.set_ylim(0, max(grade_means) * 1.15 if max(grade_means) > 0 else 1)
            ax.grid(axis='y', alpha=0.3, linestyle='--')

            plt.tight_layout()

            output_path = None
            if save:
                output_path = self._get_output_path(filename)
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                logger.info(f"Saved height by grade plot: {output_path}")

            if show:
                plt.show()
            else:
                plt.close(fig)

            return output_path

        except Exception as e:
            logger.error(f"Failed to generate height by grade plot: {e}")
            raise VisualizationError(
                message="Failed to generate height by grade visualization",
                details={"error": str(e)}
            ) from e

    def plot_height_by_gender(
        self,
        grade: Optional[str] = None,
        save: bool = True,
        show: bool = False,
        filename: str = "height_by_gender.png"
    ) -> Optional[str]:
        """
        Generate a grouped bar chart comparing heights by gender.

        Args:
            grade: Optional specific grade to plot.
            save: Whether to save the plot to file.
            show: Whether to display the plot.
            filename: Output filename.

        Returns:
            Optional[str]: Path to saved file if save is True, None otherwise.
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 6))

            if grade:
                # Single grade comparison
                stats = self._student_service.calculate_gender_statistics(grade)
                male_height = stats['male'].get('avg_height', 0)
                female_height = stats['female'].get('avg_height', 0)

                x = np.arange(1)
                width = 0.35

                ax.bar(x - width/2, [male_height], width, label='男', color='#4A90E2', edgecolor='black')
                ax.bar(x + width/2, [female_height], width, label='女', color='#E94B8A', edgecolor='black')

                ax.set_xticks(x)
                ax.set_xticklabels([grade])
                ax.set_title(f'{grade}男女生平均身高对比', fontsize=14, fontweight='bold', pad=20)
            else:
                # All grades comparison
                grades = StudentService.GRADE_ORDER
                male_heights = []
                female_heights = []

                for g in grades:
                    stats = self._student_service.calculate_gender_statistics(g)
                    male_heights.append(stats['male'].get('avg_height', 0))
                    female_heights.append(stats['female'].get('avg_height', 0))

                x = np.arange(len(grades))
                width = 0.35

                ax.bar(x - width/2, male_heights, width, label='男', color='#4A90E2', edgecolor='black')
                ax.bar(x + width/2, female_heights, width, label='女', color='#E94B8A', edgecolor='black')

                ax.set_xticks(x)
                ax.set_xticklabels(grades)
                ax.set_title('各年级男女生平均身高对比', fontsize=14, fontweight='bold', pad=20)

            ax.set_xlabel('年级', fontsize=12, fontweight='bold')
            ax.set_ylabel('平均身高 (cm)', fontsize=12, fontweight='bold')
            ax.legend(fontsize=11)
            ax.grid(axis='y', alpha=0.3, linestyle='--')

            plt.tight_layout()

            output_path = None
            if save:
                output_path = self._get_output_path(filename)
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                logger.info(f"Saved height by gender plot: {output_path}")

            if show:
                plt.show()
            else:
                plt.close(fig)

            return output_path

        except Exception as e:
            logger.error(f"Failed to generate height by gender plot: {e}")
            raise VisualizationError(
                message="Failed to generate height by gender visualization",
                details={"error": str(e)}
            ) from e

    def plot_height_distribution(
        self,
        save: bool = True,
        show: bool = False,
        filename: str = "height_distribution.png",
        figsize: Tuple[int, int] = (12, 6)
    ) -> Optional[str]:
        """
        Generate a histogram showing the overall height distribution.

        Args:
            save: Whether to save the plot to file.
            show: Whether to display the plot.
            filename: Output filename.
            figsize: Figure size (width, height) in inches.

        Returns:
            Optional[str]: Path to saved file if save is True, None otherwise.
        """
        try:
            df = self._student_service.get_students_dataframe()

            if df.empty:
                logger.warning("No student data available for height distribution plot")
                return None

            fig, ax = plt.subplots(figsize=figsize)

            bins = range(100, 170, 5)
            ax.hist(df['height_cm'], bins=bins, color='#5DADE2', edgecolor='black', alpha=0.7)

            mean_height = df['height_cm'].mean()
            median_height = df['height_cm'].median()

            ax.axvline(mean_height, color='red', linestyle='--', linewidth=2,
                       label=f'平均值: {mean_height:.1f}cm')
            ax.axvline(median_height, color='green', linestyle='--', linewidth=2,
                       label=f'中位数: {median_height:.1f}cm')

            ax.set_xlabel('身高 (cm)', fontsize=12, fontweight='bold')
            ax.set_ylabel('人数', fontsize=12, fontweight='bold')
            ax.set_title('学生身高分布直方图', fontsize=14, fontweight='bold', pad=20)
            ax.legend(fontsize=10)
            ax.grid(axis='y', alpha=0.3, linestyle='--')

            plt.tight_layout()

            output_path = None
            if save:
                output_path = self._get_output_path(filename)
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                logger.info(f"Saved height distribution plot: {output_path}")

            if show:
                plt.show()
            else:
                plt.close(fig)

            return output_path

        except Exception as e:
            logger.error(f"Failed to generate height distribution plot: {e}")
            raise VisualizationError(
                message="Failed to generate height distribution visualization",
                details={"error": str(e)}
            ) from e

    def plot_boxplot_by_grade(
        self,
        save: bool = True,
        show: bool = False,
        filename: str = "boxplot_by_grade.png"
    ) -> Optional[str]:
        """
        Generate boxplots showing height distribution by grade.

        Args:
            save: Whether to save the plot to file.
            show: Whether to display the plot.
            filename: Output filename.

        Returns:
            Optional[str]: Path to saved file if save is True, None otherwise.
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 6))

            data_by_grade = []
            for grade in StudentService.GRADE_ORDER:
                students = self.dao.student.get_by_grade(grade)
                heights = [s.height_cm for s in students]
                data_by_grade.append(heights)

            box_plot = ax.boxplot(data_by_grade, labels=StudentService.GRADE_ORDER, patch_artist=True)

            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
            for patch, color in zip(box_plot['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)

            ax.set_xlabel('年级', fontsize=12, fontweight='bold')
            ax.set_ylabel('身高 (cm)', fontsize=12, fontweight='bold')
            ax.set_title('各年级学生身高分布箱线图', fontsize=14, fontweight='bold', pad=20)
            ax.grid(axis='y', alpha=0.3, linestyle='--')

            plt.tight_layout()

            output_path = None
            if save:
                output_path = self._get_output_path(filename)
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                logger.info(f"Saved boxplot by grade plot: {output_path}")

            if show:
                plt.show()
            else:
                plt.close(fig)

            return output_path

        except Exception as e:
            logger.error(f"Failed to generate boxplot by grade: {e}")
            raise VisualizationError(
                message="Failed to generate boxplot visualization",
                details={"error": str(e)}
            ) from e

    def plot_growth_trend(
        self,
        save: bool = True,
        show: bool = False,
        filename: str = "growth_trend.png"
    ) -> Optional[str]:
        """
        Generate a line plot showing height growth trends across grades.

        Args:
            save: Whether to save the plot to file.
            show: Whether to display the plot.
            filename: Output filename.

        Returns:
            Optional[str]: Path to saved file if save is True, None otherwise.
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 6))

            grades = StudentService.GRADE_ORDER

            # Overall trend
            overall_means = []
            for grade in grades:
                stats = self._student_service.calculate_grade_statistics(grade)
                overall_means.append(stats.get('average_height', 0))

            ax.plot(
                grades,
                overall_means,
                marker='o',
                linewidth=3,
                markersize=10,
                color='#2E86AB',
                label='总体平均',
                markerfacecolor='white',
                markeredgewidth=2
            )

            # Male trend
            male_means = []
            for grade in grades:
                stats = self._student_service.calculate_gender_statistics(grade)
                male_means.append(stats['male'].get('avg_height', 0))

            ax.plot(
                grades,
                male_means,
                marker='s',
                linewidth=2.5,
                markersize=8,
                color='#4A90E2',
                label='男生',
                linestyle='--'
            )

            # Female trend
            female_means = []
            for grade in grades:
                stats = self._student_service.calculate_gender_statistics(grade)
                female_means.append(stats['female'].get('avg_height', 0))

            ax.plot(
                grades,
                female_means,
                marker='^',
                linewidth=2.5,
                markersize=8,
                color='#E94B8A',
                label='女生',
                linestyle='--'
            )

            # Add value labels for overall means
            for i, (grade, height) in enumerate(zip(grades, overall_means)):
                if height > 0:
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

            plt.tight_layout()

            output_path = None
            if save:
                output_path = self._get_output_path(filename)
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                logger.info(f"Saved growth trend plot: {output_path}")

            if show:
                plt.show()
            else:
                plt.close(fig)

            return output_path

        except Exception as e:
            logger.error(f"Failed to generate growth trend plot: {e}")
            raise VisualizationError(
                message="Failed to generate growth trend visualization",
                details={"error": str(e)}
            ) from e

    def plot_bmi_distribution(
        self,
        save: bool = True,
        show: bool = False,
        filename: str = "bmi_distribution.png"
    ) -> Optional[str]:
        """
        Generate pie and bar charts showing BMI distribution.

        Args:
            save: Whether to save the plot to file.
            show: Whether to display the plot.
            filename: Output filename.

        Returns:
            Optional[str]: Path to saved file if save is True, None otherwise.
        """
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

            bmi_stats = self._student_service.calculate_bmi_distribution()
            bmi_counts = bmi_stats.get('categories', {})

            if not bmi_counts:
                logger.warning("No BMI data available for distribution plot")
                return None

            # Pie chart
            labels = list(bmi_counts.keys())
            sizes = list(bmi_counts.values())
            colors_pie = ['#2ECC71', '#3498DB', '#F39C12', '#E74C3C']
            explode = (0.05, 0, 0, 0)

            wedges, texts, autotexts = ax1.pie(
                sizes,
                labels=labels,
                autopct='%1.1f%%',
                colors=colors_pie,
                explode=explode,
                shadow=True,
                startangle=90,
                textprops={'fontsize': 11}
            )
            ax1.set_title('BMI分布比例', fontsize=14, fontweight='bold', pad=20)

            # Bar chart by grade
            grade_order = StudentService.GRADE_ORDER
            grade_bmi = bmi_stats.get('by_grade', {})

            # Prepare data for stacked bar chart
            categories = ['偏瘦', '正常', '超重', '肥胖']
            bar_data = []

            for grade in grade_order:
                grade_data = grade_bmi.get(grade, {})
                bar_data.append([grade_data.get(cat, 0) for cat in categories])

            x = np.arange(len(grade_order))
            bottom = np.zeros(len(grade_order))

            for i, category in enumerate(categories):
                values = [row[i] for row in bar_data]
                ax2.bar(grade_order, values, label=category, bottom=bottom, color=colors_pie[i])
                bottom += values

            ax2.set_xlabel('年级', fontsize=12, fontweight='bold')
            ax2.set_ylabel('人数', fontsize=12, fontweight='bold')
            ax2.set_title('各年级BMI分布', fontsize=14, fontweight='bold', pad=20)
            ax2.legend(title='BMI分类', fontsize=9)
            ax2.set_xticklabels(grade_order, rotation=45)
            ax2.grid(axis='y', alpha=0.3, linestyle='--')

            plt.tight_layout()

            output_path = None
            if save:
                output_path = self._get_output_path(filename)
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                logger.info(f"Saved BMI distribution plot: {output_path}")

            if show:
                plt.show()
            else:
                plt.close(fig)

            return output_path

        except Exception as e:
            logger.error(f"Failed to generate BMI distribution plot: {e}")
            raise VisualizationError(
                message="Failed to generate BMI distribution visualization",
                details={"error": str(e)}
            ) from e

    def plot_scatter_age_height(
        self,
        save: bool = True,
        show: bool = False,
        filename: str = "scatter_age_height.png"
    ) -> Optional[str]:
        """
        Generate a scatter plot showing the relationship between age and height.

        Args:
            save: Whether to save the plot to file.
            show: Whether to display the plot.
            filename: Output filename.

        Returns:
            Optional[str]: Path to saved file if save is True, None otherwise.
        """
        try:
            df = self._student_service.get_students_dataframe()

            if df.empty:
                logger.warning("No student data available for scatter plot")
                return None

            fig, ax = plt.subplots(figsize=(12, 6))

            colors = {'男': '#4A90E2', '女': '#E94B8A'}

            for gender in ['男', '女']:
                gender_data = df[df['gender'] == gender]
                if not gender_data.empty:
                    ax.scatter(
                        gender_data['age'],
                        gender_data['height_cm'],
                        c=colors[gender],
                        alpha=0.6,
                        s=50,
                        label=gender,
                        edgecolors='white',
                        linewidth=0.5
                    )

            # Add trend line
            z = np.polyfit(df['age'], df['height_cm'], 1)
            p = np.poly1d(z)
            ax.plot(
                sorted(df['age'].unique()),
                p(sorted(df['age'].unique())),
                "r--",
                alpha=0.8,
                linewidth=2,
                label='趋势线'
            )

            ax.set_xlabel('年龄 (岁)', fontsize=12, fontweight='bold')
            ax.set_ylabel('身高 (cm)', fontsize=12, fontweight='bold')
            ax.set_title('年龄与身高关系散点图', fontsize=14, fontweight='bold', pad=20)
            ax.legend(fontsize=11)
            ax.grid(True, alpha=0.3, linestyle='--')

            plt.tight_layout()

            output_path = None
            if save:
                output_path = self._get_output_path(filename)
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                logger.info(f"Saved scatter plot: {output_path}")

            if show:
                plt.show()
            else:
                plt.close(fig)

            return output_path

        except Exception as e:
            logger.error(f"Failed to generate scatter plot: {e}")
            raise VisualizationError(
                message="Failed to generate age-height scatter plot",
                details={"error": str(e)}
            ) from e

    def plot_height_heatmap(
        self,
        save: bool = True,
        show: bool = False,
        filename: str = "height_heatmap.png"
    ) -> Optional[str]:
        """
        Generate a heatmap showing average heights by grade and gender.

        Args:
            save: Whether to save the plot to file.
            show: Whether to display the plot.
            filename: Output filename.

        Returns:
            Optional[str]: Path to saved file if save is True, None otherwise.
        """
        try:
            df = self._student_service.get_students_dataframe()

            if df.empty:
                logger.warning("No student data available for height heatmap")
                return None

            # Create pivot table
            pivot_table = df.pivot_table(
                values='height_cm',
                index='grade',
                columns='gender',
                aggfunc='mean'
            )

            # Reindex to maintain grade order
            pivot_table = pivot_table.reindex(StudentService.GRADE_ORDER)

            fig, ax = plt.subplots(figsize=(8, 6))

            im = ax.imshow(pivot_table.values, cmap='YlOrRd', aspect='auto')

            # Set ticks and labels
            ax.set_xticks(np.arange(len(pivot_table.columns)))
            ax.set_yticks(np.arange(len(pivot_table.index)))
            ax.set_xticklabels(pivot_table.columns, fontsize=11)
            ax.set_yticklabels(pivot_table.index, fontsize=11)

            # Add value labels
            for i in range(len(pivot_table.index)):
                for j in range(len(pivot_table.columns)):
                    if not np.isnan(pivot_table.iloc[i, j]):
                        text = ax.text(
                            j, i,
                            f'{pivot_table.iloc[i, j]:.1f}',
                            ha="center",
                            va="center",
                            color="black",
                            fontweight='bold',
                            fontsize=10
                        )

            ax.set_title('各年级男女生平均身高热力图', fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel('性别', fontsize=12, fontweight='bold')
            ax.set_ylabel('年级', fontsize=12, fontweight='bold')

            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('身高 (cm)', fontsize=11)

            plt.tight_layout()

            output_path = None
            if save:
                output_path = self._get_output_path(filename)
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                logger.info(f"Saved height heatmap: {output_path}")

            if show:
                plt.show()
            else:
                plt.close(fig)

            return output_path

        except Exception as e:
            logger.error(f"Failed to generate height heatmap: {e}")
            raise VisualizationError(
                message="Failed to generate height heatmap visualization",
                details={"error": str(e)}
            ) from e

    def generate_all_plots(
        self,
        save: bool = True,
        show: bool = False
    ) -> Dict[str, Optional[str]]:
        """
        Generate all available visualizations.

        Args:
            save: Whether to save the plots to files.
            show: Whether to display the plots.

        Returns:
            Dict[str, Optional[str]]: Dictionary mapping plot names to their file paths.
        """
        logger.info("Generating all visualizations...")

        results = {}

        try:
            results['height_by_grade'] = self.plot_height_by_grade(save=save, show=show)
            results['height_by_gender'] = self.plot_height_by_gender(save=save, show=show)
            results['height_distribution'] = self.plot_height_distribution(save=save, show=show)
            results['boxplot_by_grade'] = self.plot_boxplot_by_grade(save=save, show=show)
            results['growth_trend'] = self.plot_growth_trend(save=save, show=show)
            results['bmi_distribution'] = self.plot_bmi_distribution(save=save, show=show)
            results['scatter_age_height'] = self.plot_scatter_age_height(save=save, show=show)
            results['height_heatmap'] = self.plot_height_heatmap(save=save, show=show)

            self.emit_event(
                EventType.VISUALIZATION_GENERATED,
                data={'plots_generated': len(results)},
                source="VisualizationService.generate_all_plots"
            )

            logger.info(f"Successfully generated {len(results)} visualizations")

        except Exception as e:
            logger.error(f"Error generating visualizations: {e}")
            raise VisualizationError(
                message="Failed to generate all visualizations",
                details={"error": str(e), "successful_plots": len(results)}
            ) from e

        return results

    def generate_all_visualizations(
        self,
        save: bool = True,
        show: bool = False
    ) -> Dict[str, Optional[str]]:
        """
        Generate all visualizations at once.
        Alias for generate_all_plots.

        Args:
            save: Whether to save the plots to files.
            show: Whether to display the plots.

        Returns:
            Dict[str, Optional[str]]: Dictionary of visualization names to file paths.
        """
        return self.generate_all_plots(save=save, show=show)

    def plot_gender_comparison(
        self,
        save: bool = True,
        show: bool = False,
        filename: str = "gender_comparison.png"
    ) -> Optional[str]:
        """
        Generate a comparison of height distribution by gender.
        Alias for plot_height_by_gender.

        Args:
            save: Whether to save the plot to file.
            show: Whether to display the plot.
            filename: Output filename.

        Returns:
            Optional[str]: Path to saved file if save is True, None otherwise.
        """
        return self.plot_height_by_gender(save=save, show=show, filename=filename)

    def plot_grade_height_comparison(
        self,
        save: bool = True,
        show: bool = False,
        filename: str = "grade_height_comparison.png"
    ) -> Optional[str]:
        """
        Generate a comparison of height distribution by grade.
        Alias for plot_boxplot_by_grade.

        Args:
            save: Whether to save the plot to file.
            show: Whether to display the plot.
            filename: Output filename.

        Returns:
            Optional[str]: Path to saved file if save is True, None otherwise.
        """
        return self.plot_boxplot_by_grade(save=save, show=show, filename=filename)

    def plot_weight_distribution(
        self,
        save: bool = True,
        show: bool = False,
        filename: str = "weight_distribution.png"
    ) -> Optional[str]:
        """
        Generate a histogram of weight distribution.

        Args:
            save: Whether to save the plot to file.
            show: Whether to display the plot.
            filename: Output filename.

        Returns:
            Optional[str]: Path to saved file if save is True, None otherwise.
        """
        try:
            df = self._student_service.get_students_dataframe()

            if df.empty:
                logger.warning("No student data available for weight distribution plot")
                return None

            fig, ax = plt.subplots(figsize=(12, 6))

            bins = range(20, 80, 5)
            ax.hist(df['weight_kg'], bins=bins, color='#58D68D', edgecolor='black', alpha=0.7)

            mean_weight = df['weight_kg'].mean()
            median_weight = df['weight_kg'].median()

            ax.axvline(mean_weight, color='red', linestyle='--', linewidth=2,
                       label=f'平均值: {mean_weight:.1f}kg')
            ax.axvline(median_weight, color='green', linestyle='--', linewidth=2,
                       label=f'中位数: {median_weight:.1f}kg')

            ax.set_xlabel('体重 (kg)', fontsize=12, fontweight='bold')
            ax.set_ylabel('人数', fontsize=12, fontweight='bold')
            ax.set_title('学生体重分布直方图', fontsize=14, fontweight='bold', pad=20)
            ax.legend(fontsize=10)
            ax.grid(axis='y', alpha=0.3, linestyle='--')

            plt.tight_layout()

            output_path = None
            if save:
                output_path = self._get_output_path(filename)
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                logger.info(f"Saved weight distribution plot: {output_path}")

            if show:
                plt.show()
            else:
                plt.close(fig)

            return output_path

        except Exception as e:
            logger.error(f"Failed to generate weight distribution plot: {e}")
            raise VisualizationError(
                message="Failed to generate weight distribution visualization",
                details={"error": str(e)}
            ) from e

    def plot_height_weight_correlation(
        self,
        save: bool = True,
        show: bool = False,
        filename: str = "height_weight_correlation.png"
    ) -> Optional[str]:
        """
        Generate a scatter plot showing the correlation between height and weight.
        Alias for plot_scatter_age_height (with different semantics).

        Args:
            save: Whether to save the plot to file.
            show: Whether to display the plot.
            filename: Output filename.

        Returns:
            Optional[str]: Path to saved file if save is True, None otherwise.
        """
        try:
            df = self._student_service.get_students_dataframe()

            if df.empty:
                logger.warning("No student data available for height-weight correlation plot")
                return None

            fig, ax = plt.subplots(figsize=(10, 8))

            # Color by gender
            colors = {'男': '#3498DB', '女': '#E74C3C'}
            for gender in df['gender'].unique():
                gender_data = df[df['gender'] == gender]
                ax.scatter(
                    gender_data['height_cm'],
                    gender_data['weight_kg'],
                    c=colors.get(gender, '#95A5A6'),
                    label=gender,
                    alpha=0.7,
                    s=50
                )

            ax.set_xlabel('身高 (cm)', fontsize=12, fontweight='bold')
            ax.set_ylabel('体重 (kg)', fontsize=12, fontweight='bold')
            ax.set_title('身高与体重相关性散点图', fontsize=14, fontweight='bold', pad=20)
            ax.legend(fontsize=10)
            ax.grid(alpha=0.3, linestyle='--')

            plt.tight_layout()

            output_path = None
            if save:
                output_path = self._get_output_path(filename)
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                logger.info(f"Saved height-weight correlation plot: {output_path}")

            if show:
                plt.show()
            else:
                plt.close(fig)

            return output_path

        except Exception as e:
            logger.error(f"Failed to generate height-weight correlation plot: {e}")
            raise VisualizationError(
                message="Failed to generate height-weight correlation visualization",
                details={"error": str(e)}
            ) from e
