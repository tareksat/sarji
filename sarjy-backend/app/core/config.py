from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://sarjy:sarjy@localhost:5432/sarjy"
    openai_api_key: str = ""
    llm_model: str
    llm_base_url: str = ""
    llm_api_key: str = ""
    cors_origin: str = "http://localhost:5173"
    llm_rate_limit_per_minute: int = 20
    chat_history_limit: int = 20
    llm_retry_backoff_seconds: list[int] = [1, 2]
    log_level: str = "INFO"
    mcp_server_url: str = "http://localhost:8100/mcp"
    # The backstop, not the usual bound. Each probe carries a tighter timeout of
    # its own, so a hung dependency reports what actually failed rather than a
    # bare "timed out".
    health_check_timeout_seconds: float = 5.0
    # Per connect attempt; pool_pre_ping means a dead pooled connection costs two
    # of them, so the database probe fails at ~2x this, inside the backstop.
    db_connect_timeout_seconds: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
