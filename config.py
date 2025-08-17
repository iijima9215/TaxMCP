"""Configuration management for the MCP Tax Calculator Server."""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server Configuration
    server_host: str = Field(default="0.0.0.0", description="Server host address")
    server_port: int = Field(default=8000, description="Server port")
    server_name: str = Field(default="Japanese Tax Calculator MCP", description="Server name")
    server_version: str = Field(default="1.0.0", description="Server version")
    
    # Security Configuration
    # ⚠️ 重要: SECRET_KEYは本番環境では必ず強力な値に変更してください
    # このキーはセッション管理、データ暗号化、JWT署名に使用されます
    # 詳細: SECRET_KEY_SETUP_GUIDE.md を参照
    secret_key: str = Field(default="your-secret-key-here-change-in-production", description="Secret key for JWT and encryption")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration time")
    
    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO", description="Log level")
    log_format: Literal["json", "text"] = Field(default="json", description="Log format")
    
    # Tax Data Configuration
    tax_data_update_interval: int = Field(default=86400, description="Tax data update interval in seconds")
    enable_audit_logging: bool = Field(default=True, description="Enable audit logging")
    
    # Development Settings
    debug: bool = Field(default=False, description="Debug mode")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()