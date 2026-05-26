import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # App General Settings
    APP_NAME: str = "OLT NOC Manager"
    API_V1_STR: str = "/api/v1"
    WS_STR: str = "/ws"
    
    # DB & Redis Settings
    POSTGRES_USER: str = "olt_admin"
    POSTGRES_PASSWORD: str = "olt_admin_pass_123"
    POSTGRES_DB: str = "olt_noc_db"
    DATABASE_URL: str = "postgresql+asyncpg://olt_admin:olt_admin_pass_123@db:5432/olt_noc_db"
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Security Settings
    JWT_SECRET: str = "super_secret_jwt_key_noc_2026_change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 Hours
    ENCRYPTION_KEY: str = "noc_manager_super_key_32_bytes_"  # 32 characters
    
    # Celery settings
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"
    
    # Poller Intervals
    FAST_POLL_INTERVAL: int = 30
    METRIC_POLL_INTERVAL: int = 120
    INVENTORY_SYNC_INTERVAL: int = 600

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
