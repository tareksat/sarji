import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session as DbSession

from ..models import Memory, Message
from ..models import Session as SessionModel


def get(db: DbSession, session_id: uuid.UUID) -> SessionModel | None:
    return db.get(SessionModel, session_id)


def owned(db: DbSession, session_id: uuid.UUID, user_id: uuid.UUID) -> SessionModel | None:
    """Load a session, returning None unless it belongs to this user.

    `user_id` is a client-generated UUID, so this is a scoping check rather than
    authentication -- it prevents accidental cross-user reads, not a determined one.
    """
    session = get(db, session_id)
    if session is None or session.user_id != user_id:
        return None
    return session


def get_or_create(
    db: DbSession, session_id: uuid.UUID, user_id: uuid.UUID, title: str
) -> SessionModel:
    session = get(db, session_id)
    if session is None:
        session = SessionModel(id=session_id, user_id=user_id, title=title)
        db.add(session)
        db.commit()
    return session


def list_for_user(db: DbSession, user_id: uuid.UUID) -> list[SessionModel]:
    rows = (
        db.execute(
            select(SessionModel)
            .where(SessionModel.user_id == user_id)
            .order_by(SessionModel.updated_at.desc())
        )
        .scalars()
        .all()
    )
    return list(rows)


def rename(db: DbSession, session: SessionModel, title: str) -> SessionModel:
    session.title = title
    db.commit()
    db.refresh(session)
    return session


def delete_cascade(db: DbSession, session: SessionModel) -> None:
    """Delete a session and its messages; null out memories' source_session_id.

    The foreign keys carry no ON DELETE clause and there is no migration tool,
    so the cascade happens here.
    """
    db.execute(delete(Message).where(Message.session_id == session.id))
    db.execute(
        update(Memory)
        .where(Memory.source_session_id == session.id)
        .values(source_session_id=None)
    )
    db.delete(session)
    db.commit()


def list_messages(db: DbSession, session_id: uuid.UUID) -> list[Message]:
    rows = (
        db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
        )
        .scalars()
        .all()
    )
    return list(rows)


def recent_messages(db: DbSession, session_id: uuid.UUID, limit: int) -> list[Message]:
    rows = (
        db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    rows = list(rows)
    rows.reverse()
    return rows


def add_message(db: DbSession, session_id: uuid.UUID, role: str, content: str) -> Message:
    message = Message(session_id=session_id, role=role, content=content)
    db.add(message)
    return message
