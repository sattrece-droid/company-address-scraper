"""
Configuration management using Pydantic Settings.
Loads environment variables and provides type-safe config access.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    serper_api_key: str
    firecrawl_api_key: str
    
    # AWS Bedrock Configuration
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_default_region: str = "us-east-1"
    
    # Redis Configuration (optional - falls back to SQLite)
    redis_url: Optional[str] = None
    
    # App Configuration
    environment: str = "development"
    max_companies_per_request: int = 10
    cache_ttl_days: int = 7
    max_concurrent_playwright: int = 1
    
    # Rate Limiting
    daily_company_limit_per_ip: int = 10
    
    # Paths
    data_dir: str = "./data"
    cache_db_path: str = "./data/cache.db"
    
    # Bedrock Model Configuration
    bedrock_model_id: str = "amazon.nova-micro-v1:0"
    bedrock_fallback_model_id: str = "anthropic.claude-haiku-3-5-v2:0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()