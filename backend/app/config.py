from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Todo API"
    database_url: str = "postgresql+psycopg2://todo:todo@localhost:5433/todo"
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
