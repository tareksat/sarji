import uuid

import pytest

from app.repositories import sessions as sessions_repo
from tests.conftest import make_session, make_user


def test_get_or_create_refuses_another_users_session(db):
    owner, intruder = uuid.uuid4(), uuid.uuid4()
    session_id = uuid.uuid4()
    make_user(db, owner)
    make_user(db, intruder)
    make_session(db, session_id, owner)

    # Without this the intruder's turn writes into the owner's conversation and
    # gets the owner's recent messages replayed back in the reply.
    with pytest.raises(sessions_repo.SessionOwnershipError):
        sessions_repo.get_or_create(db, session_id, intruder, "Hello")


def test_get_or_create_returns_the_owners_own_session(db):
    owner = uuid.uuid4()
    session_id = uuid.uuid4()
    make_user(db, owner)
    make_session(db, session_id, owner, title="Kept")

    session = sessions_repo.get_or_create(db, session_id, owner, "Ignored")

    assert session.id == session_id
    assert session.title == "Kept"


def test_get_or_create_creates_without_committing(db):
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    make_user(db, user_id)

    sessions_repo.get_or_create(db, session_id, user_id, "First message")

    # The caller owns the transaction, so a turn that fails before it is
    # answered leaves no empty session behind.
    db.rollback()
    assert sessions_repo.get(db, session_id) is None
