import uuid
from datetime import datetime, timedelta, timezone

from app.models import Memory
from app.repositories.memory import facts_for_user
from tests.conftest import make_session, make_user


def _seed(db, user_id, session_id, facts, start):
    for offset, fact in enumerate(facts):
        db.add(Memory(
            user_id=user_id, content=fact, source_session_id=session_id,
            created_at=start + timedelta(seconds=offset),
        ))
    db.commit()


def test_limit_keeps_the_newest_facts_oldest_first(db):
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    make_user(db, user_id)
    make_session(db, session_id, user_id)
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    _seed(db, user_id, session_id, ["a", "b", "c", "d"], start)

    assert facts_for_user(db, user_id, limit=2) == ["c", "d"]
    assert facts_for_user(db, user_id) == ["a", "b", "c", "d"]


def test_facts_written_at_the_same_instant_have_a_stable_order(db):
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    make_user(db, user_id)
    make_session(db, session_id, user_id)
    same = datetime(2026, 9, 1, tzinfo=timezone.utc)
    for fact in ["x", "y", "z"]:
        db.add(Memory(user_id=user_id, content=fact, source_session_id=session_id, created_at=same))
    db.commit()

    first = facts_for_user(db, user_id, limit=2)
    assert len(first) == 2
    for _ in range(5):
        assert facts_for_user(db, user_id, limit=2) == first
