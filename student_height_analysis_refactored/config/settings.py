"""
配置管理模块

使用单例模式管理应用配置，支持从环境变量和配置文件加载配置。
"""

import os
from typing import Optional
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """数据库配置类"""
    
    model_config = SettingsConfigDict(env_prefix="DB_")
    
    host: str = Field(default="localhost", description="数据库主机地址")
    port: int = Field(default=5432, description="数据库端口")
    name: str = Field(default="student_height_db", description="数据库名称")
    user: str = Field(default="postgres", description="数据库用户名")
    password: str = Field(default="postgres", description="数据库密码")
    driver: str = Field(default="postgresql", description="数据库驱动")
    pool_size: int = Field(default=5, description="连接池大小")
    max_overflow: int = Field(default=10, description="连接池最大溢出数")
    pool_timeout: int = Field(default=30, description="连接池超时时间")
    echo: bool = Field(default=False, description="是否打印SQL语句")
    
    @property
    def url(self) -> str:
        """生成数据库连接URL"""
        if self.driver == "sqlite":
            return f"sqlite:///{self.name}"
        return f"{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class AppSettings(BaseSettings):
    """应用配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # 应用基本信息
    app_name: str = Field(default="Student Height Analysis System", description="应用名称")
    app_version: str = Field(default="2.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    
    # 路径配置
    base_dir: str = Field(
        default_factory=lambda: os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        description="项目根目录"
    )
    data_dir: str = Field(default="data", description="数据目录")
    output_dir: str = Field(default="output", description="输出目录")
    log_dir: str = Field(default="logs", description="日志目录")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    log_file: Optional[str] = Field(default=None, description="日志文件路径")
    
    # 数据库配置
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    
    # 可视化配置
    chart_dpi: int = Field(default=300, description="图表DPI")
    chart_format: str = Field(default="png", description="图表格式")
    chart_style: str = Field(default="seaborn-v0_8", description="图表样式")
    
    # 数据生成配置
    default_data_count: int = Field(default=1000, description="默认生成数据条数")
    random_seed: int = Field(default=42, description="随机种子")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保目录存在
        os.makedirs(os.path.join(self.base_dir, self.data_dir), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, self.output_dir), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, self.log_dir), exist_ok=True)
        
        # 设置日志文件路径
        if self.log_file is None:
            self.log_file = os.path.join(self.base_dir, self.log_dir, "app.log")
    
    @property
    def data_path(self) -> str:
        """获取数据目录完整路径"""
        return os.path.join(self.base_dir, self.data_dir)
    
    @property
    def output_path(self) -> str:
        """获取输出目录完整路径"""
        return os.path.join(self.base_dir, self.output_dir)


@lru_cache()
def get_settings() -> AppSettings:
    """
    获取应用配置单例
    
    Returns:
        AppSettings: 应用配置实例
    """
    return AppSettings()
