import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from ..models import Memory


def facts_for_user(db: DbSession, user_id: uuid.UUID, limit: int | None = None) -> list[str]:
    """Return the user's durable facts, oldest first.

    `limit` keeps the newest N. Every fact is injected into the system prompt on
    every turn, so an unbounded read grows the input token count — and the
    time-to-first-token — for the life of the account.
    """
    query = select(Memory).where(Memory.user_id == user_id).order_by(Memory.created_at.desc())
    if limit is not None:
        query = query.limit(limit)
    rows = list(db.execute(query).scalars().all())
    rows.reverse()
    return [m.content for m in rows]
