from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite+aiosqlite:///./realty_monitor.db"
    anthropic_api_key: str = ""
    collect_interval_hours: int = 6
    secret_key: str = "change-me"


settings = Settings()
