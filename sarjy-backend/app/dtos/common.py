from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"detail": "user_id must be a UUID"}})

    detail: str
