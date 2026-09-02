import asyncio
import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from agents.tool_context import ToolContext

from app.agent import sarjy_agent
from app.agent.sarjy_agent import ChatContext, _save_fact, save_memory
from app.models import Memory
from tests.conftest import make_session, make_user


@pytest.fixture(autouse=True)
def own_session(monkeypatch, session_factory):
    # The tool opens its own Session per call, so the test engine has to be
    # what it opens.
    monkeypatch.setattr(sarjy_agent, "SessionLocal", session_factory)


def _tool_context(user_id, session_id):
    return ToolContext(
        context=ChatContext(user_id=user_id, session_id=session_id),
        tool_name="save_memory", tool_call_id="call_1", tool_arguments="{}",
    )


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
    assert _save_fact(user_id, session_id, "Lives in Riyadh") is True
    assert _save_fact(user_id, session_id, "Lives in Riyadh") is False

    assert _count(db, user_id) == 1


def test_the_same_fact_is_stored_once_per_user(db):
    first, second = uuid.uuid4(), uuid.uuid4()
    session_id = uuid.uuid4()
    make_user(db, first)
    make_user(db, second)
    make_session(db, session_id, first)

    assert _save_fact(first, session_id, "Prefers metric units") is True
    assert _save_fact(second, session_id, "Prefers metric units") is True

    assert _count(db, first) == 1
    assert _count(db, second) == 1


def test_distinct_facts_are_all_kept(db):
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    make_user(db, user_id)
    make_session(db, session_id, user_id)

    _save_fact(user_id, session_id, "Lives in Riyadh")
    _save_fact(user_id, session_id, "Has a dog named Pepper")

    assert _count(db, user_id) == 2


def test_duplicate_fact_is_rejected_by_the_database(db):
    # Two `save_memory` calls in one turn run in parallel, so the pre-select
    # can miss a row the other call is about to commit. The constraint is
    # what actually holds the line.
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    make_user(db, user_id)
    make_session(db, session_id, user_id)

    db.add(Memory(user_id=user_id, content="Lives in Riyadh", source_session_id=session_id))
    db.commit()
    db.add(Memory(user_id=user_id, content="Lives in Riyadh", source_session_id=session_id))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_losing_the_insert_race_reports_already_known(db, monkeypatch):
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    make_user(db, user_id)
    make_session(db, session_id, user_id)

    # Simulate the other call landing between this call's select and insert.
    original = sarjy_agent.SessionLocal

    class RacedSession:
        def __init__(self):
            self._inner = original()

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return self._inner.__exit__(*exc)

        def execute(self, *a, **k):
            result = self._inner.execute(*a, **k)
            with original() as other:
                other.add(Memory(user_id=user_id, content="Lives in Riyadh",
                                 source_session_id=session_id))
                other.commit()
            return result

        def __getattr__(self, name):
            return getattr(self._inner, name)

    monkeypatch.setattr(sarjy_agent, "SessionLocal", RacedSession)

    assert _save_fact(user_id, session_id, "Lives in Riyadh") is False
    assert _count(db, user_id) == 1


def test_the_tool_does_not_touch_the_request_session(db):
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    make_user(db, user_id)
    make_session(db, session_id, user_id)

    # The request-scoped Session is not thread-safe and the SDK runs tool calls
    # concurrently, so the tool must not receive it at all.
    assert "db" not in ChatContext.__dataclass_fields__

    ctx = _tool_context(user_id, session_id)

    reply = asyncio.run(save_memory.on_invoke_tool(ctx, '{"fact": "Lives in Riyadh"}'))

    assert reply == "Remembered: Lives in Riyadh"
    assert _count(db, user_id) == 1


def test_parallel_saves_in_one_turn_all_land(monkeypatch, file_session_factory):
    monkeypatch.setattr(sarjy_agent, "SessionLocal", file_session_factory)
    db = file_session_factory()
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    make_user(db, user_id)
    make_session(db, session_id, user_id)

    ctx = _tool_context(user_id, session_id)

    async def turn():
        return await asyncio.gather(
            save_memory.on_invoke_tool(ctx, '{"fact": "User is called Tarek"}'),
            save_memory.on_invoke_tool(ctx, '{"fact": "User lives in Riyadh"}'),
            save_memory.on_invoke_tool(ctx, '{"fact": "User has a dog"}'),
        )

    replies = asyncio.run(turn())

    assert all(r.startswith("Remembered: ") for r in replies)
    assert _count(db, user_id) == 3


def test_an_over_long_fact_is_stored_shortened(db, monkeypatch):
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    make_user(db, user_id)
    make_session(db, session_id, user_id)
    monkeypatch.setattr(sarjy_agent.settings, "memory_fact_max_length", 20)

    ctx = _tool_context(user_id, session_id)

    reply = asyncio.run(save_memory.on_invoke_tool(
        ctx, '{"fact": "User lives in Riyadh and works as a data engineer at a bank"}'
    ))

    stored = db.execute(select(Memory.content).where(Memory.user_id == user_id)).scalar_one()
    assert len(stored) <= 20
    assert reply == f"Remembered (shortened): {stored}"
