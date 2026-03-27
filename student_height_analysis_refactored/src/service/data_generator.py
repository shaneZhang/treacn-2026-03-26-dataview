"""
数据生成服务模块

实现学生数据的生成逻辑，支持从Excel导入和模拟数据生成。
"""

import random
from typing import List, Dict, Any, Optional
from datetime import datetime

import pandas as pd
import numpy as np

from src.dao.models import Student, ClassInfo, BMICategory
from src.dao.student_dao import StudentDAO
from src.dao.class_dao import ClassDAO
from src.core.logger import get_logger
from src.core.exceptions import DataValidationException


class DataGeneratorService:
    """数据生成服务
    
    提供学生数据的生成和导入功能。
    
    Attributes:
        _student_dao: 学生DAO
        _class_dao: 班级DAO
        _logger: 日志记录器
        _random_seed: 随机种子
    """
    
    # 姓氏库
    SURNAMES = [
        '王', '李', '张', '刘', '陈', '杨', '黄', '赵', '吴', '周',
        '徐', '孙', '马', '朱', '胡', '郭', '何', '林', '罗', '高',
        '郑', '梁', '谢', '宋', '唐', '许', '韩', '冯', '邓', '曹'
    ]
    
    # 名字库
    NAMES = [
        '伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军',
        '洋', '勇', '艳', '杰', '娟', '涛', '明', '超', '秀兰', '霞',
        '平', '刚', '桂英', '文', '辉', '鑫', '宇', '博', '浩', '然',
        '梓', '涵', '轩', '怡', '欣', '雨', '晨', '曦', '阳', '昊',
        '思', '琪', '佳', '雪', '梦', '瑶', '琳', '婉', '清', '悦'
    ]
    
    # 年级年龄映射
    GRADE_AGES = {
        '一年级': (6, 7),
        '二年级': (7, 8),
        '三年级': (8, 9),
        '四年级': (9, 10),
        '五年级': (10, 11),
        '六年级': (11, 12)
    }
    
    # 身高统计参数（均值，标准差）
    HEIGHT_STATS = {
        '一年级': {'男': (120.0, 5.5), '女': (119.0, 5.3)},
        '二年级': {'男': (125.0, 5.8), '女': (124.0, 5.5)},
        '三年级': {'男': (130.0, 6.0), '女': (129.0, 5.8)},
        '四年级': {'男': (135.0, 6.2), '女': (134.0, 6.0)},
        '五年级': {'男': (140.0, 6.5), '女': (140.0, 6.3)},
        '六年级': {'男': (147.0, 7.0), '女': (148.0, 6.8)},
    }
    
    def __init__(
        self,
        student_dao: Optional[StudentDAO] = None,
        class_dao: Optional[ClassDAO] = None,
        random_seed: int = 42,
        session=None
    ) -> None:
        """初始化数据生成服务
        
        Args:
            student_dao: 学生DAO实例
            class_dao: 班级DAO实例
            random_seed: 随机种子
            session: 可选的数据库会话（用于测试）
        """
        from sqlalchemy.orm import Session
        if session is not None:
            self._student_dao = StudentDAO(session)
            self._class_dao = ClassDAO(session)
        else:
            self._student_dao = student_dao or StudentDAO()
            self._class_dao = class_dao or ClassDAO()
        self._logger = get_logger(self.__class__.__name__)
        self._random_seed = random_seed
        
        # 设置随机种子
        random.seed(random_seed)
        np.random.seed(random_seed)
    
    def _generate_name(self) -> str:
        """生成随机姓名
        
        Returns:
            姓名
        """
        return random.choice(self.SURNAMES) + random.choice(self.NAMES)
    
    def _generate_student_id(self, index: int) -> str:
        """生成学号
        
        Args:
            index: 序号
            
        Returns:
            学号
        """
        return f"STU{2024}{index + 10001:05d}"
    
    def _generate_height_weight(
        self,
        grade: str,
        gender: str
    ) -> tuple[float, float]:
        """生成身高和体重
        
        Args:
            grade: 年级
            gender: 性别
            
        Returns:
            (身高, 体重)元组
        """
        mean, std = self.HEIGHT_STATS[grade][gender]
        height = np.random.normal(mean, std)
        height = max(90.0, min(180.0, height))  # 限制范围
        
        # 根据身高生成体重（BMI相关）
        age = self.GRADE_AGES[grade][0]
        bmi_base = 16.0 if age < 9 else 17.0
        bmi = np.random.normal(bmi_base, 1.5)
        weight = (height / 100) ** 2 * bmi
        weight = max(15.0, min(80.0, weight))  # 限制范围
        
        return round(height, 1), round(weight, 1)
    
    def _calculate_bmi(self, height: float, weight: float) -> tuple[float, str]:
        """计算BMI和分类
        
        Args:
            height: 身高（厘米）
            weight: 体重（千克）
            
        Returns:
            (BMI值, BMI分类)元组
        """
        if height <= 0:
            return 0.0, BMICategory.UNDERWEIGHT.value
        
        bmi = weight / ((height / 100) ** 2)
        bmi = round(bmi, 2)
        
        if bmi < 14:
            category = BMICategory.UNDERWEIGHT.value
        elif bmi < 18:
            category = BMICategory.NORMAL.value
        elif bmi < 21:
            category = BMICategory.OVERWEIGHT.value
        else:
            category = BMICategory.OBESE.value
        
        return bmi, category
    
    def generate_student_data(
        self,
        n: int = 1000,
        grade_distribution: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """生成学生数据
        
        Args:
            n: 生成数量
            grade_distribution: 年级分布，如{'一年级': 200, '二年级': 200, ...}
            
        Returns:
            学生数据列表
        """
        self._logger.info(f"开始生成{n}条学生数据")
        
        data = []
        grades = list(self.GRADE_AGES.keys())
        
        # 确定年级分布
        if grade_distribution:
            grade_list = []
            for grade, count in grade_distribution.items():
                grade_list.extend([grade] * count)
            # 如果数量不够，随机补充
            while len(grade_list) < n:
                grade_list.append(random.choice(grades))
            grade_list = grade_list[:n]
        else:
            # 均匀分布
            grade_list = [random.choice(grades) for _ in range(n)]
        
        for i in range(n):
            grade = grade_list[i]
            age_range = self.GRADE_AGES[grade]
            age = random.randint(age_range[0], age_range[1])
            gender = random.choice(['男', '女'])
            
            height, weight = self._generate_height_weight(grade, gender)
            bmi, bmi_category = self._calculate_bmi(height, weight)
            
            # 生成入学日期
            grade_num = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级'].index(grade) + 1
            year = 2024 - (grade_num - 1)
            month = random.randint(9, 12) if grade_num == 1 else random.randint(1, 12)
            day = random.randint(1, 28)
            enrollment_date = f"{year}-{month:02d}-{day:02d}"
            
            student_data = {
                'student_id': self._generate_student_id(i),
                'name': self._generate_name(),
                'gender': gender,
                'grade': grade,
                'age': age,
                'height': height,
                'weight': weight,
                'bmi': bmi,
                'bmi_category': bmi_category,
                'class_id': None,
                'enrollment_date': enrollment_date,
            }
            data.append(student_data)
        
        self._logger.info(f"成功生成{n}条学生数据")
        return data
    
    def import_from_excel(self, file_path: str) -> int:
        """从Excel导入学生数据
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            导入的记录数
            
        Raises:
            DataValidationException: 数据验证失败
        """
        self._logger.info(f"从Excel导入数据: {file_path}")
        
        try:
            df = pd.read_excel(file_path)
            self._logger.info(f"读取到{len(df)}条记录")
            
            # 数据验证和转换
            students_data = []
            for _, row in df.iterrows():
                student_data = self._validate_and_convert_row(row)
                if student_data:
                    students_data.append(student_data)
            
            # 批量创建
            if students_data:
                self._student_dao.create_many(students_data)
            
            self._logger.info(f"成功导入{len(students_data)}条记录")
            return len(students_data)
            
        except Exception as e:
            self._logger.error(f"导入Excel失败: {e}")
            raise DataValidationException(
                message=f"导入Excel失败: {str(e)}",
                error_code="EXCEL_IMPORT_ERROR",
                details={"file_path": file_path}
            )
    
    def _validate_and_convert_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """验证并转换数据行
        
        Args:
            row: DataFrame行
            
        Returns:
            转换后的数据字典，验证失败返回None
        """
        try:
            # 必填字段检查
            required_fields = ['姓名', '性别', '年级', '年龄', '身高(cm)', '体重(kg)']
            for field in required_fields:
                if field not in row or pd.isna(row[field]):
                    self._logger.warning(f"缺少必填字段: {field}")
                    return None
            
            # 数据转换
            height = float(row['身高(cm)'])
            weight = float(row['体重(kg)'])
            bmi, bmi_category = self._calculate_bmi(height, weight)
            
            # 学号处理
            student_id = str(row.get('学生ID', ''))
            if not student_id or student_id == 'nan':
                student_id = self._generate_student_id(random.randint(1, 99999))
            
            return {
                'student_id': student_id,
                'name': str(row['姓名']),
                'gender': str(row['性别']),
                'grade': str(row['年级']),
                'age': int(row['年龄']),
                'height': height,
                'weight': weight,
                'bmi': bmi,
                'bmi_category': bmi_category,
                'enrollment_date': str(row.get('入学日期', '')),
            }
            
        except Exception as e:
            self._logger.warning(f"数据行验证失败: {e}")
            return None
    
    def export_to_excel(self, file_path: str, students: Optional[List[Student]] = None) -> str:
        """导出学生数据到Excel
        
        Args:
            file_path: 导出文件路径
            students: 学生列表，为None则导出所有
            
        Returns:
            导出文件路径
        """
        self._logger.info(f"导出数据到Excel: {file_path}")
        
        if students is None:
            students = self._student_dao.get_all()
        
        # 转换为DataFrame
        data = []
        for student in students:
            data.append({
                '学生ID': student.student_id,
                '姓名': student.name,
                '性别': student.gender,
                '年级': student.grade,
                '年龄': student.age,
                '身高(cm)': student.height,
                '体重(kg)': student.weight,
                'BMI': student.bmi,
                'BMI分类': student.bmi_category,
                '入学日期': student.enrollment_date,
            })
        
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
        
        self._logger.info(f"成功导出{len(data)}条记录到: {file_path}")
        return file_path
