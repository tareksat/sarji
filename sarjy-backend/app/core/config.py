from pydantic import Field, field_validator, model_validator
from sqlalchemy import URL
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # A full DSN, when the provider hands one over (Neon, Render). Otherwise the
    # discrete parts below are assembled into one.
    database_url: str = ""
    postgres_user: str = "sarjy"
    postgres_password: str = "sarjy"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "sarjy"
    openai_api_key: str = ""
    llm_model: str
    llm_base_url: str = ""
    llm_api_key: str = ""
    cors_origin: str = "http://localhost:5173"
    # Zero is not "block every call": it divides by the refill rate, so the
    # bound has to be positive and the intent expressed some other way.
    llm_rate_limit_per_minute: int = Field(default=20, gt=0)
    llm_rate_limit_max_wait_seconds: float = Field(default=2.0, ge=0)
    chat_history_limit: int = Field(default=20, gt=0)
    memory_facts_limit: int = Field(default=20, gt=0)
    # Characters per stored fact. Facts are injected into every later prompt.
    memory_fact_max_length: int = Field(default=200, gt=0)
    llm_retry_backoff_seconds: list[int] = [1, 2]
    log_level: str = "INFO"
    # Empty means log to stdout only, which is what a container wants.
    log_dir: str = ""
    mcp_server_url: str = "http://localhost:8100/mcp"
    # The whole tool call, not one phase of it: a stalled upstream must not hold
    # a conversational turn open indefinitely.
    mcp_timeout_seconds: float = Field(default=15.0, gt=0)
    # Measurement switch only: serves get_weather as a local function tool so
    # the MCP transport's per-call cost can be measured. Ships false.
    use_local_weather_tool: bool = False
    # The backstop, not the usual bound. Each probe carries a tighter timeout of
    # its own, so a hung dependency reports what actually failed rather than a
    # bare "timed out".
    health_check_timeout_seconds: float = 5.0
    # Per connect attempt; pool_pre_ping means a dead pooled connection costs two
    # of them, so the database probe fails at ~2x this, inside the backstop.
    db_connect_timeout_seconds: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def sqlalchemy_url(self) -> str | URL:
        """The DSN, assembled safely when it is not given whole.

        Compose interpolates `${POSTGRES_PASSWORD}` into a URL literally, so a
        password containing `@`, `/`, `:` or `#` parses as a different host or
        database and fails with an error that names neither. `URL.create` quotes
        each part instead of trusting the string.
        """
        if self.database_url:
            return self.database_url
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    @field_validator("log_level")
    @classmethod
    def _known_log_level(cls, value: str) -> str:
        level = value.upper()
        if level not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}:
            raise ValueError(f"Unknown log level: {value!r}")
        return level

    @model_validator(mode="after")
    def _has_a_model_credential(self):
        """Fail at boot rather than on the first user's first message."""
        if not self.llm_base_url and not self.openai_api_key:
            raise ValueError(
                "Set OPENAI_API_KEY, or LLM_BASE_URL to route through a proxy."
            )
        return self


settings = Settings()
