from pydantic import BaseModel, ConfigDict, Field, field_validator

# Roughly a long email. Well above any spoken turn, well below a context limit.
MESSAGE_MAX_LENGTH = 8000


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
    # Bounded because it is stored, replayed into the next `chat_history_limit`
    # turns, and sent to the model: an unbounded body is a context-limit error
    # and a large bill, and an empty one buys a real model call for nothing.
    message: str = Field(
        min_length=1,
        max_length=MESSAGE_MAX_LENGTH,
        description="The user's turn, typed or transcribed.",
    )

    @field_validator("message")
    @classmethod
    def _not_only_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value


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
