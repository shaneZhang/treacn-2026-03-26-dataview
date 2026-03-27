"""
业务逻辑层 (Service)

提供业务逻辑处理服务。
"""

from src.service.data_generator import DataGeneratorService
from src.service.analysis_service import AnalysisService, StatisticsResult

__all__ = [
    "DataGeneratorService",
    "AnalysisService",
    "StatisticsResult",
]
