"""
数据生成工具

生成模拟的学生身高数据
"""
from typing import List, Dict, Any
import random
from datetime import date, datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

from config import Config
from utils.logger import get_logger


class DataGenerator:
    """
    数据生成器
    
    生成模拟的学生身高数据
    
    Example:
        >>> generator = DataGenerator()
        >>> generator.generate_and_save(n=1000)
    """
    
    SURNAMES = [
        '王', '李', '张', '刘', '陈', '杨', '黄', '赵', '吴', '周',
        '徐', '孙', '马', '朱', '胡', '郭', '何', '林', '罗', '高',
        '郑', '梁', '谢', '宋', '唐', '许', '韩', '冯', '邓', '曹'
    ]
    
    NAMES = [
        '伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军',
        '洋', '勇', '艳', '杰', '娟', '涛', '明', '超', '秀兰', '霞',
        '平', '刚', '桂英', '文', '辉', '鑫', '宇', '博', '浩', '然',
        '梓', '涵', '轩', '怡', '欣', '雨', '晨', '曦', '阳', '昊',
        '思', '琪', '佳', '雪', '梦', '瑶', '琳', '婉', '清', '悦'
    ]
    
    GRADES = {
        '一年级': (6, 7),
        '二年级': (7, 8),
        '三年级': (8, 9),
        '四年级': (9, 10),
        '五年级': (10, 11),
        '六年级': (11, 12)
    }
    
    HEIGHT_STATS = {
        '一年级': {'男': (120, 5.5), '女': (119, 5.3)},
        '二年级': {'男': (125, 5.8), '女': (124, 5.5)},
        '三年级': {'男': (130, 6.0), '女': (129, 5.8)},
        '四年级': {'男': (135, 6.2), '女': (134, 6.0)},
        '五年级': {'男': (140, 6.5), '女': (140, 6.3)},
        '六年级': {'男': (147, 7.0), '女': (148, 6.8)},
    }
    
    def __init__(self, random_seed: int = 42) -> None:
        """
        初始化数据生成器
        
        Args:
            random_seed: 随机种子
        """
        self.config = Config.get_instance()
        self.logger = get_logger(__name__)
        self.random_seed = random_seed
        
        np.random.seed(random_seed)
        random.seed(random_seed)
    
    def generate_student_data(
        self, 
        n: int = 1000,
        start_id: int = 10001
    ) -> List[Dict[str, Any]]:
        """
        生成学生数据
        
        Args:
            n: 生成数据条数
            start_id: 起始学号
        
        Returns:
            List[Dict[str, Any]]: 学生数据列表
        
        Example:
            >>> data = generator.generate_student_data(100)
        """
        self.logger.info(f"开始生成{n}条学生数据...")
        
        data = []
        
        for i in range(n):
            grade = random.choice(list(self.GRADES.keys()))
            age_range = self.GRADES[grade]
            age = random.randint(age_range[0], age_range[1])
            
            gender = random.choice(['男', '女'])
            
            mean, std = self.HEIGHT_STATS[grade][gender]
            height = round(np.random.normal(mean, std), 1)
            
            bmi_base = 16 if age < 9 else 17
            weight = round(
                (height / 100) ** 2 * np.random.normal(bmi_base, 1.5), 1
            )
            
            name = random.choice(self.SURNAMES) + random.choice(self.NAMES)
            
            grade_num = list(self.GRADES.keys()).index(grade) + 1
            year = 2024 - (grade_num - 1)
            month = random.randint(9, 12) if grade_num == 1 else random.randint(1, 12)
            day = random.randint(1, 28)
            enrollment_date = date(year, month, day)
            
            student_data = {
                'student_id': str(start_id + i),
                'name': name,
                'gender': gender,
                'grade': grade,
                'age': age,
                'height': height,
                'weight': weight,
                'enrollment_date': enrollment_date
            }
            
            data.append(student_data)
        
        self.logger.info(f"学生数据生成完成，共{n}条")
        
        return data
    
    def generate_and_save(
        self, 
        n: int = 1000,
        start_id: int = 10001
    ) -> int:
        """
        生成并保存学生数据到数据库
        
        Args:
            n: 生成数据条数
            start_id: 起始学号
        
        Returns:
            int: 成功保存的记录数
        
        Example:
            >>> count = generator.generate_and_save(1000)
        """
        from core.database import DatabaseFactory
        from core.dao import StudentDAO, HeightRecordDAO
        
        student_data_list = self.generate_student_data(n, start_id)
        
        student_dao = StudentDAO()
        record_dao = HeightRecordDAO()
        
        success_count = 0
        
        for student_data in student_data_list:
            try:
                student = student_dao.create({
                    'student_id': student_data['student_id'],
                    'name': student_data['name'],
                    'gender': student_data['gender'],
                    'grade': student_data['grade'],
                    'age': student_data['age'],
                    'enrollment_date': student_data['enrollment_date']
                })
                
                record_dao.create({
                    'student_id': student.id,
                    'record_date': date.today(),
                    'height': student_data['height'],
                    'weight': student_data['weight'],
                    'age_at_record': student.age,
                    'grade_at_record': student.grade
                })
                
                success_count += 1
                
            except Exception as e:
                self.logger.warning(
                    f"保存学生数据失败: {student_data['student_id']}, 错误: {e}"
                )
        
        self.logger.info(f"数据保存完成，成功{success_count}条")
        
        return success_count
    
    def generate_standard_heights(self) -> None:
        """
        生成标准身高数据
        
        Example:
            >>> generator.generate_standard_heights()
        """
        from core.database import DatabaseFactory
        from models import StandardHeight
        
        standards_data = [
            ('一年级', '男', 120.0, 110.0, 130.0),
            ('一年级', '女', 119.0, 109.0, 129.0),
            ('二年级', '男', 125.0, 115.0, 135.0),
            ('二年级', '女', 124.0, 114.0, 134.0),
            ('三年级', '男', 130.0, 120.0, 140.0),
            ('三年级', '女', 129.0, 119.0, 139.0),
            ('四年级', '男', 135.0, 125.0, 145.0),
            ('四年级', '女', 134.0, 124.0, 144.0),
            ('五年级', '男', 140.0, 130.0, 150.0),
            ('五年级', '女', 140.0, 130.0, 150.0),
            ('六年级', '男', 147.0, 137.0, 157.0),
            ('六年级', '女', 148.0, 138.0, 158.0),
        ]
        
        with DatabaseFactory.get_instance().session_scope() as session:
            for grade, gender, std_height, min_height, max_height in standards_data:
                standard = StandardHeight(
                    grade=grade,
                    gender=gender,
                    standard_height=std_height,
                    height_range_min=min_height,
                    height_range_max=max_height
                )
                session.add(standard)
        
        self.logger.info("标准身高数据生成完成")
    
    def export_to_excel(
        self, 
        n: int = 1000,
        output_path: str = None
    ) -> str:
        """
        生成数据并导出到Excel
        
        Args:
            n: 生成数据条数
            output_path: 输出文件路径
        
        Returns:
            str: 导出文件路径
        
        Example:
            >>> path = generator.export_to_excel(1000, 'data.xlsx')
        """
        if output_path is None:
            output_path = str(
                Path(self.config.app_config['data_dir']) / 'student_height_data.xlsx'
            )
        
        student_data_list = self.generate_student_data(n)
        
        df_data = []
        for data in student_data_list:
            df_data.append({
                '学生ID': data['student_id'],
                '姓名': data['name'],
                '性别': data['gender'],
                '年级': data['grade'],
                '年龄': data['age'],
                '身高(cm)': data['height'],
                '体重(kg)': data['weight'],
                '入学日期': data['enrollment_date']
            })
        
        df = pd.DataFrame(df_data)
        
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        df.to_excel(output_path, index=False, engine='openpyxl')
        
        self.logger.info(f"数据已导出到: {output_path}")
        
        return output_path

