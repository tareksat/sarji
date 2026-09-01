import uuid

from sqlalchemy.orm import Session as DbSession

from ..models import User


def upsert(db: DbSession, user_id: uuid.UUID) -> None:
    if not db.get(User, user_id):
        db.add(User(id=user_id))
        db.commit()
