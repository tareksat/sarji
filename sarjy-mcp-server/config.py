from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Loopback by default: this server authenticates nothing and executes tools
    # on request, so `python server.py` on a laptop should not offer that to the
    # whole network. Both container images set MCP_SERVER_HOST=0.0.0.0
    # explicitly, where the port is never published.
    host: str = "127.0.0.1"
    port: int = 8100

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="MCP_SERVER_"
    )


settings = Settings()
