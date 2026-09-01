from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://sarjy:sarjy@localhost:5432/sarjy"
    openai_api_key: str = ""
    cors_origin: str = "http://localhost:5173"
    llm_rate_limit_per_minute: int = 20
    chat_history_limit: int = 20
    llm_retry_backoff_seconds: list[int] = [1, 2]
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
