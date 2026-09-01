from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://sarjy:sarjy@localhost:5432/sarjy"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    llm_base_url: str = ""
    llm_api_key: str = ""
    cors_origin: str = "http://localhost:5173"
    llm_rate_limit_per_minute: int = 20
    chat_history_limit: int = 20
    llm_retry_backoff_seconds: list[int] = [1, 2]
    log_level: str = "INFO"
    mcp_server_url: str = "http://localhost:8100/mcp"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
