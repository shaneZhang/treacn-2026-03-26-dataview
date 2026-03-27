"""
Student height data analysis module.

This module provides the StudentHeightAnalyzer class for analyzing
student height data from Excel files or databases.

Note: This is a legacy module maintained for backward compatibility.
For new development, please use the app.service module instead.
"""

import pandas as pd
import numpy as np
import warnings

# Import new architecture for compatibility
try:
    from app.service import StudentService
    from app.config.database import get_db_pool
    NEW_ARCHITECTURE_AVAILABLE = True
except ImportError:
    NEW_ARCHITECTURE_AVAILABLE = False


class StudentHeightAnalyzer:
    """
    Student height data analyzer class.

    This class provides methods for analyzing student height data,
    supporting both Excel files and database sources.

    Attributes:
        df (pandas.DataFrame): The student data
        results (dict): Dictionary to store analysis results

    Note: For new development, use app.service.StudentService instead.
    """

    def __init__(self, data_path=None, use_database=False):
        """
        Initialize the analyzer with a data source.

        Args:
            data_path: Path to Excel data file (for file-based mode)
            use_database: Whether to use the database for data access
        """
        self.results = {}
        self._use_database = use_database
        self._student_service = None

        if use_database and NEW_ARCHITECTURE_AVAILABLE:
            self._init_from_database()
        elif data_path:
            self.df = pd.read_excel(data_path)
        else:
            raise ValueError("Either data_path or use_database=True must be provided")

    def _init_from_database(self):
        """Initialize data from the database using the new architecture."""
        if not NEW_ARCHITECTURE_AVAILABLE:
            raise ImportError("New architecture modules not available")

        pool = get_db_pool()
        session = pool.get_session()
        self._student_service = StudentService(session)
        self.df = self._student_service.get_students_dataframe()

    def basic_statistics(self):
        """
        Calculate basic statistics.

        Returns:
            dict: Dictionary containing basic statistical metrics
        """
        stats = {
            '总人数': len(self.df),
            '男生人数': len(self.df[self.df['gender'] == '男']) if 'gender' in self.df.columns else len(self.df[self.df['性别'] == '男']),
            '女生人数': len(self.df[self.df['gender'] == '女']) if 'gender' in self.df.columns else len(self.df[self.df['性别'] == '女']),
            '平均身高': round(self.df['height_cm'].mean(), 2) if 'height_cm' in self.df.columns else round(self.df['身高(cm)'].mean(), 2),
            '身高标准差': round(self.df['height_cm'].std(), 2) if 'height_cm' in self.df.columns else round(self.df['身高(cm)'].std(), 2),
            '身高最小值': self.df['height_cm'].min() if 'height_cm' in self.df.columns else self.df['身高(cm)'].min(),
            '身高最大值': self.df['height_cm'].max() if 'height_cm' in self.df.columns else self.df['身高(cm)'].max(),
            '身高中位数': self.df['height_cm'].median() if 'height_cm' in self.df.columns else self.df['身高(cm)'].median(),
        }
        self.results['basic'] = stats
        return stats

    def grade_statistics(self):
        """
        Calculate statistics by grade.

        Returns:
            pandas.DataFrame: Statistics by grade
        """
        grade_col = 'grade' if 'grade' in self.df.columns else '年级'
        height_col = 'height_cm' if 'height_cm' in self.df.columns else '身高(cm)'
        weight_col = 'weight_kg' if 'weight_kg' in self.df.columns else '体重(kg)'

        grade_stats = self.df.groupby(grade_col).agg({
            height_col: ['count', 'mean', 'std', 'min', 'max'],
            weight_col: ['mean', 'std']
        }).round(2)

        grade_stats.columns = ['人数', '平均身高', '身高标准差', '最矮身高', '最高身高', '平均体重', '体重标准差']

        # Sort by grade order
        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
        grade_stats = grade_stats.reindex(grade_order)

        self.results['by_grade'] = grade_stats
        return grade_stats

    def gender_statistics(self):
        """
        Calculate statistics by gender.

        Returns:
            pandas.DataFrame: Statistics by gender and grade
        """
        grade_col = 'grade' if 'grade' in self.df.columns else '年级'
        gender_col = 'gender' if 'gender' in self.df.columns else '性别'
        height_col = 'height_cm' if 'height_cm' in self.df.columns else '身高(cm)'

        gender_stats = self.df.groupby([grade_col, gender_col])[height_col].agg(['count', 'mean', 'std']).round(2)
        gender_stats.columns = ['人数', '平均身高', '标准差']

        self.results['by_gender'] = gender_stats
        return gender_stats

    def age_statistics(self):
        """
        Calculate statistics by age.

        Returns:
            pandas.DataFrame: Statistics by age
        """
        age_col = 'age' if 'age' in self.df.columns else '年龄'
        height_col = 'height_cm' if 'height_cm' in self.df.columns else '身高(cm)'

        age_stats = self.df.groupby(age_col)[height_col].agg(['count', 'mean', 'std', 'min', 'max']).round(2)
        age_stats.columns = ['人数', '平均身高', '标准差', '最矮身高', '最高身高']

        self.results['by_age'] = age_stats
        return age_stats

    def height_distribution(self):
        """
        Calculate height distribution.

        Returns:
            dict: Distribution of students by height ranges
        """
        height_col = 'height_cm' if 'height_cm' in self.df.columns else '身高(cm)'

        bins = [0, 110, 120, 130, 140, 150, 160, 200]
        labels = ['<110cm', '110-120cm', '120-130cm', '130-140cm', '140-150cm', '150-160cm', '>160cm']

        self.df['身高段'] = pd.cut(self.df[height_col], bins=bins, labels=labels, right=False)
        distribution = self.df['身高段'].value_counts().sort_index().to_dict()

        self.results['height_distribution'] = distribution
        return distribution

    def growth_analysis(self):
        """
        Analyze growth trends between grades.

        Returns:
            pandas.DataFrame: Height growth between consecutive grades
        """
        grade_col = 'grade' if 'grade' in self.df.columns else '年级'
        height_col = 'height_cm' if 'height_cm' in self.df.columns else '身高(cm)'

        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
        grade_means = self.df.groupby(grade_col)[height_col].mean()
        grade_means = grade_means.reindex(grade_order)

        growth_data = []
        for i in range(1, len(grade_order)):
            prev_grade = grade_order[i-1]
            curr_grade = grade_order[i]
            growth = grade_means[curr_grade] - grade_means[prev_grade]
            growth_data.append({
                '年级段': f"{prev_grade}到{curr_grade}",
                '身高增长(cm)': round(growth, 2),
                '增长率(%)': round(growth / grade_means[prev_grade] * 100, 2)
            })

        growth_df = pd.DataFrame(growth_data)
        self.results['growth'] = growth_df
        return growth_df

    def percentile_analysis(self):
        """
        Calculate height percentiles by grade.

        Returns:
            pandas.DataFrame: Height percentiles by grade
        """
        grade_col = 'grade' if 'grade' in self.df.columns else '年级'
        height_col = 'height_cm' if 'height_cm' in self.df.columns else '身高(cm)'

        percentiles = [3, 10, 25, 50, 75, 90, 97]

        percentile_data = []
        for grade in ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']:
            grade_data = self.df[self.df[grade_col] == grade][height_col]
            row = {'年级': grade}
            for p in percentiles:
                row[f'P{p}'] = round(np.percentile(grade_data, p), 1)
            percentile_data.append(row)

        percentile_df = pd.DataFrame(percentile_data)
        self.results['percentiles'] = percentile_df
        return percentile_df

    def bmi_analysis(self):
        """
        Analyze BMI distribution.

        Returns:
            tuple: (bmi_distribution, bmi_by_grade)
        """
        height_col = 'height_cm' if 'height_cm' in self.df.columns else '身高(cm)'
        weight_col = 'weight_kg' if 'weight_kg' in self.df.columns else '体重(kg)'
        age_col = 'age' if 'age' in self.df.columns else '年龄'
        grade_col = 'grade' if 'grade' in self.df.columns else '年级'

        # Calculate BMI
        self.df['BMI'] = self.df[weight_col] / (self.df[height_col] / 100) ** 2
        self.df['BMI'] = self.df['BMI'].round(2)

        # BMI classification (child standards)
        def classify_bmi(bmi, age):
            if bmi < 14:
                return '偏瘦'
            elif bmi < 18:
                return '正常'
            elif bmi < 21:
                return '超重'
            else:
                return '肥胖'

        self.df['BMI分类'] = self.df.apply(lambda x: classify_bmi(x['BMI'], x[age_col]), axis=1)

        bmi_dist = self.df['BMI分类'].value_counts().to_dict()
        bmi_by_grade = pd.crosstab(self.df[grade_col], self.df['BMI分类'])

        # Sort by grade order
        grade_order = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']
        bmi_by_grade = bmi_by_grade.reindex(grade_order)

        self.results['bmi_distribution'] = bmi_dist
        self.results['bmi_by_grade'] = bmi_by_grade

        return bmi_dist, bmi_by_grade

    def compare_with_standard(self):
        """
        Compare actual heights with standard heights.

        Returns:
            pandas.DataFrame: Comparison with standard heights
        """
        grade_col = 'grade' if 'grade' in self.df.columns else '年级'
        gender_col = 'gender' if 'gender' in self.df.columns else '性别'
        height_col = 'height_cm' if 'height_cm' in self.df.columns else '身高(cm)'

        # Chinese children height standards (2023)
        standard_heights = {
            '一年级': {'男': 120.0, '女': 119.0},
            '二年级': {'男': 125.0, '女': 124.0},
            '三年级': {'男': 130.0, '女': 129.0},
            '四年级': {'男': 135.0, '女': 134.0},
            '五年级': {'男': 140.0, '女': 140.0},
            '六年级': {'男': 147.0, '女': 148.0},
        }

        comparison_data = []
        for grade in ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']:
            for gender in ['男', '女']:
                actual_mean = self.df[(self.df[grade_col] == grade) & (self.df[gender_col] == gender)][height_col].mean()
                standard = standard_heights[grade][gender]
                diff = actual_mean - standard

                comparison_data.append({
                    '年级': grade,
                    '性别': gender,
                    '实际平均身高': round(actual_mean, 2),
                    '标准身高': standard,
                    '差异': round(diff, 2),
                    '差异百分比': round(diff / standard * 100, 2)
                })

        comparison_df = pd.DataFrame(comparison_data)
        self.results['standard_comparison'] = comparison_df
        return comparison_df

    def run_all_analysis(self):
        """Run all available analyses and print results."""
        print("=" * 60)
        print("小学生身高数据分析报告")
        print("=" * 60)

        print("\n【一、基础统计】")
        basic = self.basic_statistics()
        for key, value in basic.items():
            print(f"  {key}: {value}")

        print("\n【二、年级统计】")
        grade = self.grade_statistics()
        print(grade)

        print("\n【三、性别统计】")
        gender = self.gender_statistics()
        print(gender)

        print("\n【四、年龄统计】")
        age = self.age_statistics()
        print(age)

        print("\n【五、身高分布】")
        dist = self.height_distribution()
        for key, value in dist.items():
            print(f"  {key}: {value}人")

        print("\n【六、生长趋势分析】")
        growth = self.growth_analysis()
        print(growth)

        print("\n【七、身高百分位数】")
        percentiles = self.percentile_analysis()
        print(percentiles)

        print("\n【八、BMI分析】")
        bmi_dist, bmi_by_grade = self.bmi_analysis()
        print("BMI分布:")
        for key, value in bmi_dist.items():
            print(f"  {key}: {value}人")
        print("\n各年级BMI分布:")
        print(bmi_by_grade)

        print("\n【九、与标准身高对比】")
        comparison = self.compare_with_standard()
        print(comparison)

        print("\n" + "=" * 60)
        print("分析完成！")
        print("=" * 60)

        return self.results


if __name__ == "__main__":
    # Test the analyzer
    analyzer = StudentHeightAnalyzer("../data/student_height_data.xlsx")
    analyzer.run_all_analysis()
