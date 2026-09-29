from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Todo API"
    environment: str = "development"  # "production" disables the interactive docs
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://todo:todo@localhost:5433/todo"
    db_pool_size: int = 10
    db_max_overflow: int = 10
    cors_origins: list[str] = ["http://localhost:5173"]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
