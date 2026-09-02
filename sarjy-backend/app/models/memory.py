import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base
from .base import now_utc


class Memory(Base):
    __tablename__ = "memories"
    __table_args__ = (
        # `facts_for_user` runs on every turn: this user's rows, newest first.
        Index("ix_memories_user_created", "user_id", "created_at"),
        # `delete_cascade` nulls this column out by session id. Unindexed, every
        # session delete is a full scan of the table.
        Index("ix_memories_source_session", "source_session_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    source_session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("sessions.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
