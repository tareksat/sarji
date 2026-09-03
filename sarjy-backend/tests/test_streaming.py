import asyncio
import uuid

import pytest
from openai.types.responses import ResponseTextDeltaEvent
from sqlalchemy import select

from app.models import Message
from app.services import streaming
from tests.conftest import make_session, make_user


class FakeStreamEvent:
    type = "raw_response_event"

    def __init__(self, delta):
        # `model_construct` skips validation: the test only needs an instance
        # the isinstance check in `stream_chat` accepts.
        self.data = ResponseTextDeltaEvent.model_construct(delta=delta)


class FakeRun:
    """Stands in for `RunResultStreaming`."""

    def __init__(self, deltas, final_output=""):
        self._deltas = deltas
        self.final_output = final_output
        self.cancelled = False

    async def stream_events(self):
        for delta in self._deltas:
            yield FakeStreamEvent(delta)

    def cancel(self, mode="immediate"):
        self.cancelled = True


class FakeToolCall:
    """The one shape `tool_names_from` reads off a run's `new_items`."""

    type = "tool_call_item"

    def __init__(self, tool_name):
        self.tool_name = tool_name


class ExplodingRun(FakeRun):
    async def stream_events(self):
        for delta in self._deltas:
            yield FakeStreamEvent(delta)
        raise RuntimeError("upstream went away")


@pytest.fixture
def streamed(monkeypatch, session_factory):
    """Wire `stream_chat` to the in-memory database and a scripted model run."""
    monkeypatch.setattr(streaming, "SessionLocal", session_factory)
    monkeypatch.setattr(streaming, "build_agent", lambda facts, mcp_ready=True: object())

    async def never_connected():
        return False

    async def no_reset():
        return None

    monkeypatch.setattr(streaming.mcp, "ensure_connected", never_connected)
    monkeypatch.setattr(streaming.mcp, "reset", no_reset)

    def install(run):
        monkeypatch.setattr(streaming.Runner, "run_streamed", lambda *a, **k: run, raising=False)
        return run

    return install


def drive(coro):
    """Run one coroutine to completion.

    Explicit rather than pytest-asyncio: the suite has no async plugin, and one
    helper is a smaller thing to carry than another test dependency.
    """
    return asyncio.run(coro)


def messages(db, session_id, role):
    return list(
        db.execute(
            select(Message.content)
            .where(Message.session_id == session_id, Message.role == role)
            .order_by(Message.created_at.asc())
        ).scalars()
    )


def test_done_frame_carries_the_whole_reply(db, streamed):
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    streamed(FakeRun(["Hello", " there."]))

    async def scenario():
        return [e async for e in streaming.stream_chat(db, user_id, session_id, "Hi")]

    events = drive(scenario())

    assert [e["type"] for e in events] == ["delta", "delta", "done"]
    assert events[-1]["reply"] == "Hello there."
    assert messages(db, session_id, "assistant") == ["Hello there."]


def test_a_tool_only_turn_does_not_write_a_null_reply(db, streamed):
    # No text deltas, and `final_output` is None. Persisting that violates the
    # NOT NULL constraint after the headers are sent, which reaches the client
    # as a stream that simply stops -- no `done`, no `error`.
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    streamed(FakeRun([], final_output=None))

    async def scenario():
        return [
            e async for e in streaming.stream_chat(db, user_id, session_id, "Remember this")
        ]

    events = drive(scenario())

    assert [e["type"] for e in events] == ["done"]
    assert events[-1]["reply"] == ""
    assert messages(db, session_id, "assistant") == [""]


def test_the_done_frame_names_the_tools_the_turn_called(db, streamed):
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    run = streamed(FakeRun(["Sunny."]))
    run.new_items = [FakeToolCall("get_weather"), FakeToolCall("save_memory")]

    async def scenario():
        return [e async for e in streaming.stream_chat(db, user_id, session_id, "Weather?")]

    events = drive(scenario())

    assert events[-1]["tools_used"] == ["get_weather", "save_memory"]


def test_a_turn_that_called_nothing_reports_no_tools(db, streamed):
    # `FakeRun` has no `new_items` at all, which is also what a run cut short
    # before the SDK populated it looks like.
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    streamed(FakeRun(["Hello."]))

    async def scenario():
        return [e async for e in streaming.stream_chat(db, user_id, session_id, "Hi")]

    assert drive(scenario())[-1]["tools_used"] == []


def test_a_client_disconnect_persists_what_was_streamed(db, streamed):
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    run = streamed(FakeRun(["Partial", " answer", " continues"]))

    async def scenario():
        gen = streaming.stream_chat(db, user_id, session_id, "Tell me a long story")
        assert (await gen.__anext__())["type"] == "delta"
        assert (await gen.__anext__())["type"] == "delta"
        # The user closes the tab: Starlette closes the generator mid-reply.
        await gen.aclose()

    drive(scenario())

    # Otherwise the conversation reloads as a question with no answer, and the
    # model run keeps producing billable tokens nobody will read.
    assert messages(db, session_id, "assistant") == ["Partial answer"]
    assert run.cancelled is True


def test_a_cross_user_session_is_refused_before_the_model_runs(db, streamed):
    owner, intruder = uuid.uuid4(), uuid.uuid4()
    session_id = uuid.uuid4()
    make_user(db, owner)
    make_user(db, intruder)
    make_session(db, session_id, owner)
    streamed(FakeRun(["should not run"]))

    async def scenario():
        return [
            e
            async for e in streaming.stream_chat(
                db, intruder, session_id, "Summarize our conversation"
            )
        ]

    events = drive(scenario())

    assert [e["type"] for e in events] == ["error"]
    assert messages(db, session_id, "user") == []


def test_a_failed_run_still_ends_the_stream(db, streamed):
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    streamed(ExplodingRun(["Half a th"]))

    async def scenario():
        return [e async for e in streaming.stream_chat(db, user_id, session_id, "Hi")]

    events = drive(scenario())

    assert [e["type"] for e in events] == ["delta", "error"]
    # `error` is terminal, and what was streamed is still saved.
    assert messages(db, session_id, "assistant") == ["Half a th"]
