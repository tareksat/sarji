import asyncio
import logging
import uuid
from collections.abc import AsyncIterator

from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent
from sqlalchemy.orm import Session as DbSession

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
    """
    logger.info("stream_chat start user_id=%s session_id=%s", user_id, session_id)
    timings = Timings()

    # Committed, not flushed: the history read runs in another Session and must
    # see this message. The assistant-side write is deferred until after the
    # stream finishes, which is the other half of taking writes off the path.
    with timings.span("db_write_pre_ms"):
        users_repo.upsert(db, user_id)
        session = sessions_repo.get_or_create(db, session_id, user_id, title_from_message(message))
        sessions_repo.add_message(db, session_id, "user", message)
        db.commit()

    with timings.span("db_read_ms"):
        history, facts = await _load_context(session_id, user_id)

    agent = build_agent(facts)
    context = ChatContext(user_id=user_id, session_id=session_id, db=db)

    try:
        timings.set("limiter_wait_ms", await _rate_limiter.acquire())
    except RateLimitedError as exc:
        # A frame rather than an exception: the response has already been
        # opened, so a raised error would reach the client as a broken stream.
        db.rollback()
        yield {"type": "error", "detail": f"Rate limited. Retry in {exc.retry_after_seconds:.0f}s."}
        return

    chunks: list[str] = []
    try:
        result = Runner.run_streamed(agent, input=history, context=context)
        async for event in result.stream_events():
            if event.type != "raw_response_event":
                continue
            if not isinstance(event.data, ResponseTextDeltaEvent):
                continue
            if not chunks:
                timings.mark("llm_ttft_ms")
            chunks.append(event.data.delta)
            yield {"type": "delta", "text": event.data.delta}
    except Exception as exc:
        db.rollback()
        logger.error(
            "stream_chat failed user_id=%s session_id=%s: %s",
            user_id, session_id, exc, exc_info=True,
        )
        yield {
            "type": "error",
            "detail": "Sarjy is having trouble responding right now. Please try again.",
        }
        return

    reply = "".join(chunks) or result.final_output

    with timings.span("db_write_ms"):
        sessions_repo.add_message(db, session_id, "assistant", reply)
        session.updated_at = now_utc()
        db.commit()

    # Only the streamed path has a first-token moment; the whole-response
    # duration the non-streamed path reports has no counterpart here.
    timings.set("llm_total_ms", None)
    logger.info(
        "stream_chat complete user_id=%s session_id=%s %s",
        user_id, session_id, timings.as_log_line(),
    )

    yield {"type": "done", "reply": reply, "timings": timings.as_dict()}
