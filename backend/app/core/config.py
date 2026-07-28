from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MARTIQ API"
    database_url: str = "sqlite:///./martiq.db"
    jwt_secret: str = "development-secret"
    jwt_refresh_secret: str = "development-refresh-secret"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:5173,http://localhost:8081"
    vision_demo_enabled: bool = True
    default_language: str = "az"
    upload_dir: str = "uploads"
    max_upload_size: int = 10_485_760
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    @property
    def cors_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
