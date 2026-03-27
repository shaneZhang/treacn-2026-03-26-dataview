"""
Configuration settings for the Student Height Analysis system.

This module provides type-safe configuration settings using Pydantic Settings.
Settings are loaded from environment variables and .env file.
"""

from typing import Literal, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with type validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Disable automatic JSON parsing for all fields
        json_schema_extra={"env_parse_json": False}
    )

    # Application Configuration
    app_name: str = Field(default="StudentHeightAnalysis", description="Application name")
    app_env: Literal["development", "testing", "production"] = Field(
        default="development",
        description="Application environment"
    )
    app_debug: bool = Field(default=True, description="Debug mode flag")

    # Database Configuration
    db_type: Literal["sqlite", "postgresql", "mysql"] = Field(
        default="sqlite",
        description="Database type: sqlite, postgresql, or mysql"
    )
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="student_height_db", description="Database name")
    db_user: str = Field(default="postgres", description="Database user")
    db_password: str = Field(default="postgres", description="Database password")
    db_sqlite_path: str = Field(default="./app.db", description="SQLite database file path")

    # Connection Pool Configuration
    db_pool_min_conn: int = Field(default=5, description="Minimum connections in pool")
    db_pool_max_conn: int = Field(default=20, description="Maximum connections in pool")
    db_pool_max_overflow: int = Field(default=10, description="Maximum overflow connections")
    db_pool_recycle: int = Field(default=3600, description="Connection recycle time in seconds")

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    log_file: str = Field(default="./logs/app.log", description="Log file path")
    log_max_size: str = Field(default="10MB", description="Maximum log file size")
    log_backup_count: int = Field(default=5, description="Number of log backup files")

    # Analysis Configuration - stored as string internally, parsed via property
    grade_order_str: str = Field(
        default="一年级,二年级,三年级,四年级,五年级,六年级",
        description="Order of grades for analysis (comma-separated string)",
        validation_alias="grade_order"
    )
    standard_heights_file: str = Field(
        default="./config/standard_heights.json",
        description="Path to standard heights configuration file"
    )

    @property
    def grade_order(self) -> List[str]:
        """Get grade order as a list of strings."""
        if self.grade_order_str is None or self.grade_order_str == "":
            return ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"]
        # Handle both comma-separated strings and JSON strings
        try:
            import json
            return json.loads(self.grade_order_str)
        except (json.JSONDecodeError, TypeError):
            return [grade.strip() for grade in self.grade_order_str.split(",")]

    @property
    def database_url(self) -> str:
        """
        Construct the database URL based on the database type.

        Returns:
            str: The complete database connection URL.

        Raises:
            ValueError: If the database type is not supported.
        """
        if self.db_type == "sqlite":
            return f"sqlite:///{self.db_sqlite_path}"
        elif self.db_type == "postgresql":
            return (
                f"postgresql://{self.db_user}:{self.db_password}@"
                f"{self.db_host}:{self.db_port}/{self.db_name}"
            )
        elif self.db_type == "mysql":
            return (
                f"mysql+pymysql://{self.db_user}:{self.db_password}@"
                f"{self.db_host}:{self.db_port}/{self.db_name}"
            )
        raise ValueError(f"Unsupported database type: {self.db_type}")

    @property
    def output_dir(self) -> str:
        """Get the output directory for reports and visualizations."""
        return "./output"


# Create a singleton instance of the settings
_settings_instance: Settings | None = None


def get_settings() -> Settings:
    """
    Get the singleton settings instance.

    Returns:
        Settings: The application settings instance.
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


settings = get_settings()
