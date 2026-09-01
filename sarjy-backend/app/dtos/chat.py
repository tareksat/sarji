from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "3f1a9c2e-5b7d-4e88-9a21-6c0f4d8b1e33",
                "session_id": "b74e2f10-8c3a-4d61-9f52-1a7e0c9d4b88",
                "message": "What's the weather like?",
            }
        }
    )

    user_id: str = Field(description="Client-generated UUID identifying the browser.")
    session_id: str = Field(
        description=(
            "Client-generated UUID for the conversation. The row is created on the "
            "first message, so a session the user has opened but not written in does "
            "not exist server-side yet."
        )
    )
    message: str = Field(description="The user's turn, typed or transcribed.")


class ChatResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"reply": "It's 34°C and clear in Riyadh right now."}}
    )

    reply: str = Field(description="Sarjy's reply. Spoken aloud by the client unless muted.")
    timings: dict[str, float | None] | None = Field(
        default=None,
        description=(
            "Server-side spans for this turn, in milliseconds: `db_read_ms`, "
            "`db_write_ms`, `limiter_wait_ms`, `llm_total_ms`, `llm_ttft_ms` "
            "(null unless streamed) and `total_ms`. Present so the client can "
            "attribute latency without server access."
        ),
    )
