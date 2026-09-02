import asyncio
import logging
import time
import uuid
from collections.abc import AsyncIterator

from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent
from sqlalchemy.orm import Session as DbSession

from ..agent import mcp
from ..agent.sarjy_agent import ChatContext, build_agent
from ..core.config import settings
from ..core.db import SessionLocal
from ..core.rate_limiter import RateLimitedError
from ..core.timing import Timings
from ..models import now_utc
from ..repositories import memory as memory_repo
from ..repositories import sessions as sessions_repo
from ..repositories import users as users_repo
from .chat import _rate_limiter, title_from_message

logger = logging.getLogger(__name__)

GENERIC_FAILURE = "Sarjy is having trouble responding right now. Please try again."


def _read_history(session_id: uuid.UUID) -> list[dict]:
    # Its own Session: SQLAlchemy's sync Session is not thread-safe, and this
    # runs concurrently with the memory read on a worker thread.
    with SessionLocal() as db:
        return [
            {"role": m.role, "content": m.content}
            for m in sessions_repo.recent_messages(db, session_id, settings.chat_history_limit)
        ]


def _read_facts(user_id: uuid.UUID) -> list[str]:
    with SessionLocal() as db:
        return memory_repo.facts_for_user(db, user_id, settings.memory_facts_limit)


async def _load_context(
    session_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[list[dict], list[str]]:
    return await asyncio.gather(
        asyncio.to_thread(_read_history, session_id),
        asyncio.to_thread(_read_facts, user_id),
    )


async def stream_chat(
    db: DbSession, user_id: uuid.UUID, session_id: uuid.UUID, message: str
) -> AsyncIterator[dict]:
    """Run one turn, yielding token deltas as they arrive.

    The point of the endpoint: the client can start speaking at the first
    sentence instead of waiting for the last token.

    An `error` frame is terminal -- no `done` follows it.
    """
    logger.info("stream_chat start user_id=%s session_id=%s", user_id, session_id)
    timings = Timings()

    # Before the first write, not after: a turn the limiter refuses must not
    # leave a session row and an unanswered user message behind. The message is
    # committed rather than flushed once we do write it, so a rollback here
    # would be a no-op.
    try:
        timings.set("limiter_wait_ms", await _rate_limiter.acquire())
    except RateLimitedError as exc:
        yield {"type": "error", "detail": f"Rate limited. Retry in {exc.retry_after_seconds:.0f}s."}
        return

    def _write_user_message():
        users_repo.upsert(db, user_id)
        session = sessions_repo.get_or_create(db, session_id, user_id, title_from_message(message))
        sessions_repo.add_message(db, session_id, "user", message)
        # Committed, not flushed: the history read runs in another Session and
        # must see this message. The assistant-side write is deferred until
        # after the stream finishes, which is the other half of taking writes
        # off the path.
        db.commit()
        return session

    # Off the event loop: a sync SQLAlchemy write on the loop stalls every other
    # stream this worker is serving for the length of the round trip.
    with timings.span("db_write_pre_ms"):
        try:
            session = await asyncio.to_thread(_write_user_message)
        except sessions_repo.SessionOwnershipError:
            db.rollback()
            logger.warning(
                "Refusing cross-user session write user_id=%s session_id=%s", user_id, session_id
            )
            yield {"type": "error", "detail": "That conversation was not found."}
            return

    with timings.span("db_read_ms"):
        history, facts = await _load_context(session_id, user_id)

    agent = build_agent(facts, mcp_ready=await mcp.ensure_connected())
    context = ChatContext(user_id=user_id, session_id=session_id)

    def _persist(reply: str) -> None:
        sessions_repo.add_message(db, session_id, "assistant", reply)
        # Inserting a Message does not touch the Session row, so `onupdate`
        # never fires. Set it explicitly to keep the recency ordering correct.
        session.updated_at = now_utc()
        db.commit()

    chunks: list[str] = []
    completed = False
    result = None
    llm_started = time.perf_counter()

    try:
        result = Runner.run_streamed(agent, input=history, context=context)
        async for event in result.stream_events():
            if event.type != "raw_response_event":
                continue
            if not isinstance(event.data, ResponseTextDeltaEvent):
                continue
            if not chunks:
                # From the model call, not from the start of the turn.
                timings.mark_from("llm_ttft_ms", llm_started)
            chunks.append(event.data.delta)
            yield {"type": "delta", "text": event.data.delta}
        completed = True
    except Exception as exc:
        db.rollback()
        logger.error(
            "stream_chat failed user_id=%s session_id=%s: %s",
            user_id, session_id, exc, exc_info=True,
        )
        # The MCP session survives a restart of the server behind it as a
        # handle that is dead but not None, and then fails every later turn.
        # Dropping it here means the next turn reconnects.
        await mcp.reset()
        yield {"type": "error", "detail": GENERIC_FAILURE}
        return
    finally:
        if not completed:
            # The turn was cut short: an error above, or -- arriving here as
            # GeneratorExit -- the client closing the tab mid-reply. Persist
            # what was streamed, so the conversation does not reload as a
            # question with no answer, and stop the run rather than paying for
            # tokens nobody will read.
            #
            # Synchronous on purpose: this also runs during generator
            # finalization, where suspending is not safe.
            if chunks:
                try:
                    _persist("".join(chunks))
                except Exception:
                    db.rollback()
                    logger.exception("Could not persist the partial reply")
            if result is not None:
                result.cancel()

    # A turn that only called tools produces no text deltas, and `final_output`
    # is then whatever the model returned -- possibly None. Coerced, because the
    # column is NOT NULL and this write happens after the headers are sent,
    # where a raised error reaches the client as a stream that simply stops.
    reply = "".join(chunks) or result.final_output
    reply = "" if reply is None else str(reply)

    with timings.span("db_write_ms"):
        try:
            await asyncio.to_thread(_persist, reply)
        except Exception:
            db.rollback()
            logger.exception(
                "Could not persist the reply user_id=%s session_id=%s", user_id, session_id
            )
            yield {"type": "error", "detail": GENERIC_FAILURE}
            return

    # Only the streamed path has a first-token moment; the whole-response
    # duration the non-streamed path reports has no counterpart here.
    timings.set("llm_total_ms", None)
    payload = timings.as_dict()
    logger.info(
        "stream_chat complete user_id=%s session_id=%s %s",
        user_id, session_id, timings.as_log_line(payload),
    )

    yield {"type": "done", "reply": reply, "timings": payload}
