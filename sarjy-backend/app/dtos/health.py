from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DependencyHealth(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"status": "ok", "latency_ms": 4.1, "detail": "1 tools"}}
    )

    status: Literal["ok", "error", "skipped"] = Field(
        description=(
            "`skipped` means the dependency is not configured in this environment, "
            "which is not a failure."
        )
    )
    latency_ms: float = Field(description="How long the probe itself took.")
    detail: str | None = Field(
        default=None,
        description="A short fact when healthy, or the exception when not.",
    )


class FullHealthResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "degraded",
                "dependencies": {
                    "database": {"status": "ok", "latency_ms": 2.3, "detail": None},
                    "litellm": {
                        "status": "error",
                        "latency_ms": 11.7,
                        "detail": "ConnectError: All connection attempts failed",
                    },
                    "mcp": {"status": "ok", "latency_ms": 6.8, "detail": "1 tools"},
                },
            }
        }
    )

    status: Literal["ok", "degraded"] = Field(
        description="`degraded` when at least one dependency failed its probe."
    )
    dependencies: dict[str, DependencyHealth]
