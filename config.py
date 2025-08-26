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
    
    # Tax Rate Configuration
    # 法人税率設定
    corporate_tax_rate_large: float = Field(default=0.232, description="大法人の法人税率 (23.2%)")
    corporate_tax_rate_small: float = Field(default=0.15, description="中小法人の軽減税率 (15%)")
    corporate_tax_rate_small_high: float = Field(default=0.232, description="中小法人の一般税率 (23.2%)")
    
    # 地方法人税率設定
    local_corporate_tax_rate: float = Field(default=0.103, description="地方法人税率 (10.3%)")
    
    # 事業税率設定
    business_tax_rate_low: float = Field(default=0.035, description="事業税率（低所得）(3.5%)")
    business_tax_rate_mid: float = Field(default=0.053, description="事業税率（中所得）(5.3%)")
    business_tax_rate_high: float = Field(default=0.07, description="事業税率（高所得）(7.0%)")
    business_tax_rate_low_excess: float = Field(default=0.0375, description="事業税超過税率（低所得）(3.75%)")
    business_tax_rate_mid_excess: float = Field(default=0.0565, description="事業税超過税率（中所得）(5.665%)")
    business_tax_rate_high_excess: float = Field(default=0.0748, description="事業税超過税率（高所得）(7.48%)")
    
    # 住民税率設定
    resident_tax_income_rate: float = Field(default=0.07, description="住民税法人税割税率 (7%)")
    resident_tax_equal_capital_50m_below: int = Field(default=70000, description="住民税均等割（資本金5000万円以下）")
    resident_tax_equal_capital_50m_1b: int = Field(default=180000, description="住民税均等割（資本金5000万円超～10億円以下）")
    resident_tax_equal_capital_1b_above: int = Field(default=290000, description="住民税均等割（資本金10億円超）")
    
    # 計算設定
    default_rounding_enabled: bool = Field(default=True, description="デフォルトの丸め処理有効化")
    rounding_precision: int = Field(default=0, description="丸め精度（小数点以下桁数）")
    rounding_method: str = Field(default="round_half_up", description="丸め方法: round_half_up, truncate, no_rounding")
    
    # Development Settings
    debug: bool = Field(default=False, description="Debug mode")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()