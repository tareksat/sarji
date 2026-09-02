import uuid

from sqlalchemy import func, select

from app.agent.sarjy_agent import _save_fact
from app.models import Memory
from tests.conftest import make_session, make_user


def _count(db, user_id):
    return db.execute(
        select(func.count()).select_from(Memory).where(Memory.user_id == user_id)
    ).scalar_one()


def test_replaying_a_turn_does_not_duplicate_the_fact(db):
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    make_user(db, user_id)
    make_session(db, session_id, user_id)

    # A transient model error makes `_run_with_retry` re-run the whole turn,
    # and this tool has already committed by then.
    assert _save_fact(db, user_id, session_id, "Lives in Riyadh") is True
    assert _save_fact(db, user_id, session_id, "Lives in Riyadh") is False

    assert _count(db, user_id) == 1


def test_the_same_fact_is_stored_once_per_user(db):
    first, second = uuid.uuid4(), uuid.uuid4()
    session_id = uuid.uuid4()
    make_user(db, first)
    make_user(db, second)
    make_session(db, session_id, first)

    assert _save_fact(db, first, session_id, "Prefers metric units") is True
    assert _save_fact(db, second, session_id, "Prefers metric units") is True

    assert _count(db, first) == 1
    assert _count(db, second) == 1


def test_distinct_facts_are_all_kept(db):
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    make_user(db, user_id)
    make_session(db, session_id, user_id)

    _save_fact(db, user_id, session_id, "Lives in Riyadh")
    _save_fact(db, user_id, session_id, "Has a dog named Pepper")

    assert _count(db, user_id) == 2
