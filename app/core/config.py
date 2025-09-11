"""Application configuration management."""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main application settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # This ignores extra environment variables
    )
    
    # Application
    app_name: str = Field(default="Financial Wisdom Platform")
    debug: bool = Field(default=False)
    version: str = Field(default="0.1.0")
    
    # API
    api_v1_prefix: str = Field(default="/api/v1")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production")
    access_token_expire_minutes: int = Field(default=30)
    
    # Database
    db_url: str = Field(default="postgresql+asyncpg://postgres:password@localhost:5432/financial_wisdom")
    db_echo: bool = Field(default=False)
    db_pool_size: int = Field(default=20)
    db_max_overflow: int = Field(default=30)
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379")
    redis_cache_db: int = Field(default=0)
    redis_celery_db: int = Field(default=1)
    redis_session_db: int = Field(default=2)
    
    # AI Service
    anthropic_api_key: Optional[str] = Field(default=None)
    openai_api_key: Optional[str] = Field(default=None)
    ai_primary_model: str = Field(default="claude-3-5-sonnet-20241022")
    ai_secondary_model: str = Field(default="gpt-3.5-turbo")
    ai_max_tokens_per_request: int = Field(default=2000)
    ai_request_timeout: int = Field(default=30)
    ai_requests_per_minute: int = Field(default=50)
    ai_daily_request_limit: int = Field(default=1000)
    
    # Web Scraping
    scraping_user_agent: str = Field(default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    scraping_request_delay: float = Field(default=2.0)
    scraping_max_concurrent_requests: int = Field(default=10)
    scraping_retry_times: int = Field(default=3)
    scraping_timeout: int = Field(default=30)
    scraping_finance_sources: List[str] = Field(default=[
        "https://www.investopedia.com/articles/",
        "https://www.bloomberg.com/opinion/",
        "https://seekingalpha.com/news",
        "https://www.cnbc.com/personal-finance/"
    ])
    
    # Content Generation
    content_daily_generation_time: str = Field(default="06:00")
    content_quality_threshold: float = Field(default=8.0)
    content_similarity_threshold: float = Field(default=0.8)
    content_cache_ttl: int = Field(default=7 * 24 * 3600)  # 7 days
    content_trending_cache_ttl: int = Field(default=6 * 3600)  # 6 hours
    
    # External Services
    elasticsearch_url: str = Field(default="http://localhost:9200")
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")
    
    # Notion Configuration - Simplified Single Database
    notion_token: Optional[str] = Field(default=None, alias="NOTION_TOKEN")
    notion_database_id: Optional[str] = Field(default=None, alias="NOTION_DATABASE_ID")
    
    # Monitoring
    grafana_password: str = Field(default="admin")
    prometheus_retention: str = Field(default="30d")
    
    # Email
    email_from: str = Field(default="noreply@financial-wisdom.com")
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="your_email@gmail.com")
    smtp_password: str = Field(default="your_app_password")
    
    # External Services
    webhook_url: str = Field(default="https://your-webhook-endpoint.com/notifications")
    slack_webhook_url: str = Field(default="https://hooks.slack.com/services/your/slack/webhook")
    
    # Security
    cors_origins: str = Field(default='["http://localhost:3000"]')
    
    # Cost Management
    daily_cost_limit: float = Field(default=50.00)
    monthly_cost_limit: float = Field(default=500.00)
    cost_alert_threshold: float = Field(default=0.8)
    
    # Feature Flags
    enable_web_scraping: bool = Field(default=True)
    enable_social_collection: bool = Field(default=False)
    enable_real_time_generation: bool = Field(default=True)
    enable_cache_optimization: bool = Field(default=True)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    log_file: str = Field(default="/app/logs/financial_wisdom.log")
    
    # Development
    reload_on_change: bool = Field(default=False)
    profile_performance: bool = Field(default=False)
    
    # Database compatibility fields (legacy)
    postgres_db: str = Field(default="financial_wisdom")
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="password")


# Legacy configuration objects for backward compatibility
class DatabaseConfig:
    """Database configuration wrapper."""
    def __init__(self, settings_obj):
        self.url = settings_obj.db_url
        self.echo = settings_obj.db_echo
        self.pool_size = settings_obj.db_pool_size
        self.max_overflow = settings_obj.db_max_overflow


class RedisConfig:
    """Redis configuration wrapper."""
    def __init__(self, settings_obj):
        self.url = settings_obj.redis_url
        self.cache_db = settings_obj.redis_cache_db
        self.celery_db = settings_obj.redis_celery_db
        self.session_db = settings_obj.redis_session_db


class AIConfig:
    """AI service configuration wrapper."""
    def __init__(self, settings_obj):
        self.anthropic_api_key = settings_obj.anthropic_api_key
        self.openai_api_key = settings_obj.openai_api_key
        self.primary_model = settings_obj.ai_primary_model
        self.secondary_model = settings_obj.ai_secondary_model
        self.max_tokens_per_request = settings_obj.ai_max_tokens_per_request
        self.request_timeout = settings_obj.ai_request_timeout
        self.requests_per_minute = settings_obj.ai_requests_per_minute
        self.daily_request_limit = settings_obj.ai_daily_request_limit


class ScrapingConfig:
    """Web scraping configuration wrapper."""
    def __init__(self, settings_obj):
        self.user_agent = settings_obj.scraping_user_agent
        self.request_delay = settings_obj.scraping_request_delay
        self.max_concurrent_requests = settings_obj.scraping_max_concurrent_requests
        self.retry_times = settings_obj.scraping_retry_times
        self.timeout = settings_obj.scraping_timeout
        self.finance_sources = settings_obj.scraping_finance_sources


class ContentConfig:
    """Content generation configuration wrapper."""
    def __init__(self, settings_obj):
        self.daily_generation_time = settings_obj.content_daily_generation_time
        self.quality_threshold = settings_obj.content_quality_threshold
        self.similarity_threshold = settings_obj.content_similarity_threshold
        self.content_cache_ttl = settings_obj.content_cache_ttl
        self.trending_cache_ttl = settings_obj.content_trending_cache_ttl


class NotionConfig:
    """Notion database configuration wrapper - Simplified single database."""
    def __init__(self, settings_obj):
        self.token = settings_obj.notion_token
        self.database_id = settings_obj.notion_database_id


# Enhanced settings class with backward compatibility methods  
class EnhancedSettings(Settings):
    """Enhanced Settings class with legacy compatibility."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create legacy config objects
        self._database = DatabaseConfig(self)
        self._redis = RedisConfig(self)
        self._ai = AIConfig(self)
        self._scraping = ScrapingConfig(self)
        self._content = ContentConfig(self)
        self._notion = NotionConfig(self)
    
    @property
    def database(self):
        return self._database
    
    @property  
    def redis(self):
        return self._redis
        
    @property
    def ai(self):
        return self._ai
        
    @property
    def scraping(self):
        return self._scraping
        
    @property
    def content(self):
        return self._content
        
    @property
    def notion(self):
        return self._notion


# Global settings instance
settings = EnhancedSettings()

def get_settings() -> EnhancedSettings:
    """Get application settings instance."""
    return settings