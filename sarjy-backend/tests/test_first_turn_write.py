"""The first turn of a new chat writes user, session and message together.

All three rows land in one transaction, and Postgres enforces the foreign keys
at flush time, so the order the unit of work picks is part of the contract.
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories import sessions as sessions_repo
from app.repositories import users as users_repo


def test_new_user_session_and_message_commit_together(db):
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()

    users_repo.upsert(db, user_id)
    sessions_repo.get_or_create(db, session_id, user_id, "New chat")
    sessions_repo.add_message(db, session_id, "user", "hello hello")

    try:
        db.commit()
    except IntegrityError as exc:
        pytest.fail(f"first turn of a new chat violated a foreign key: {exc.orig}")

    assert sessions_repo.get(db, session_id) is not None
    assert [m.content for m in sessions_repo.recent_messages(db, session_id, 10)] == ["hello hello"]


def test_message_into_an_existing_session_still_commits(db):
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    users_repo.upsert(db, user_id)
    sessions_repo.get_or_create(db, session_id, user_id, "New chat")
    db.commit()

    users_repo.upsert(db, user_id)
    sessions_repo.get_or_create(db, session_id, user_id, "New chat")
    sessions_repo.add_message(db, session_id, "assistant", "hi back")
    db.commit()

    assert len(sessions_repo.recent_messages(db, session_id, 10)) == 1
