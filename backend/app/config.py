"""Application configuration settings using pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql://soc_app:soc_app@localhost:5432/soc_dashboard"
    REDIS_URL: str = "redis://localhost:6379/0"
    CORS_ORIGINS: str = "http://localhost:5173"

    WAZUH_MODE: str = "mock"  # "mock" | "real"
    WAZUH_API_URL: str = "https://localhost:55000"
    WAZUH_API_USER: str = "wazuh-wui"
    WAZUH_API_PASSWORD: str = "change_me"
    WAZUH_VERIFY_SSL: bool = False

    WAZUH_INDEXER_URL: str = "https://localhost:9200"
    WAZUH_INDEXER_USER: str = "admin"
    WAZUH_INDEXER_PASSWORD: str = "change_me"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
