from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8100

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="MCP_SERVER_"
    )


settings = Settings()
