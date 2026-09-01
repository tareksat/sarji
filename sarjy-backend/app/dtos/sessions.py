import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str = Field(description="Derived from the first user message, or set by a rename.")
    created_at: datetime
    updated_at: datetime = Field(
        description="Touched on every turn. Drives the sidebar's ordering."
    )


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str = Field(description="Either `user` or `assistant`. Tool calls are not persisted.")
    content: str
    created_at: datetime


class SessionUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"title": "Trip planning"}})

    title: str = Field(min_length=1, max_length=200, description="The new session title.")
