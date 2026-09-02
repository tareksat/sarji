import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base
from .base import now_utc


class Message(Base):
    __tablename__ = "messages"
    # `recent_messages` -- on the critical path of every turn -- filters by
    # session and takes the newest N by `created_at`. With only the single-column
    # index Postgres sorts the whole conversation to answer it.
    __table_args__ = (Index("ix_messages_session_created", "session_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
