import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from ..models import Memory


def facts_for_user(db: DbSession, user_id: uuid.UUID) -> list[str]:
    rows = db.execute(select(Memory).where(Memory.user_id == user_id)).scalars().all()
    return [m.content for m in rows]
