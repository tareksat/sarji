import asyncio
import logging
import uuid

from agents import Runner
from openai import APIConnectionError, APITimeoutError, RateLimitError
from sqlalchemy.orm import Session as DbSession

from ..agent import mcp
from ..agent.sarjy_agent import ChatContext, build_agent
from ..core.config import settings
from ..core.rate_limiter import TokenBucketRateLimiter
from ..core.timing import Timings
from ..models import now_utc
from ..repositories import memory as memory_repo
from ..repositories import sessions as sessions_repo
from ..repositories import users as users_repo

logger = logging.getLogger(__name__)

_rate_limiter = TokenBucketRateLimiter(
    settings.llm_rate_limit_per_minute, settings.llm_rate_limit_max_wait_seconds
)

TITLE_MAX_LENGTH = 30


class LLMUnavailableError(Exception):
    """Raised when the agent turn could not complete, even after retries."""


def title_from_message(message: str) -> str:
    """Derive a session title from its first user message."""
    text = message.strip()
    if not text:
        return "New chat"
    if len(text) > TITLE_MAX_LENGTH:
        return f"{text[:TITLE_MAX_LENGTH]}…"
    return text


# Transient by nature, so worth another attempt. Anything else is a bad
# request or a bug, and retrying it just multiplies the latency before the 502.
RETRYABLE = (RateLimitError, APIConnectionError, APITimeoutError)


def tool_names_from(result) -> list[str]:
    """Names of the tools the model called this turn, in call order.

    Local tools (`save_memory`) and MCP ones (`get_weather`) both arrive as
    `tool_call_item`s on the run result, so one pass covers both. Repeats are
    kept -- calling a tool twice is worth seeing. Read defensively because the
    streamed and non-streamed results are different classes.
    """
    names: list[str] = []
    for item in getattr(result, "new_items", None) or []:
        if getattr(item, "type", None) != "tool_call_item":
            continue
        name = getattr(item, "tool_name", None)
        if name:
            names.append(name)
    return names


async def _run_with_retry(agent, history: list[dict], context: ChatContext):
    last_error: Exception | None = None
    delays = [0, *settings.llm_retry_backoff_seconds]
    for attempt, delay in enumerate(delays, start=1):
        if delay:
            await asyncio.sleep(delay)
        try:
            return await Runner.run(agent, input=history, context=context)
        except RETRYABLE as exc:
            last_error = exc
            logger.warning(
                "Retryable model error on attempt %d/%d (delay=%ss): %s",
                attempt, len(delays), delay, exc,
            )
    raise last_error


async def handle_chat(
    db: DbSession, user_id: uuid.UUID, session_id: uuid.UUID, message: str, model: str | None = None
) -> tuple[str, dict[str, float | None], list[str]]:
    logger.info("handle_chat start user_id=%s session_id=%s", user_id, session_id)
    timings = Timings()

    # Acquired before anything is written, matching the streamed path: a turn
    # the limiter refuses leaves no session row and no unanswered message.
    timings.set("limiter_wait_ms", await _rate_limiter.acquire())

    def _read() -> tuple[object, list[dict], list[str]]:
        users_repo.upsert(db, user_id)
        session = sessions_repo.get_or_create(db, session_id, user_id, title_from_message(message))
        sessions_repo.add_message(db, session_id, "user", message)
        # Committed, not flushed, matching the streamed path: the user's turn is
        # durable before the model is called, so a failure leaves their message
        # on screen to retry rather than silently discarding it.
        db.commit()
        history = [
            {"role": m.role, "content": m.content}
            for m in sessions_repo.recent_messages(db, session_id, settings.chat_history_limit)
        ]
        facts = memory_repo.facts_for_user(db, user_id, settings.memory_facts_limit)
        return session, history, facts

    # Off the event loop: sync SQLAlchemy on the loop stalls every other request
    # this worker is serving, streamed ones included.
    with timings.span("db_read_ms"):
        session, history, facts = await asyncio.to_thread(_read)

    agent = build_agent(facts, mcp_ready=await mcp.ensure_connected(), model=model)
    context = ChatContext(user_id=user_id, session_id=session_id)

    try:
        with timings.span("llm_total_ms"):
            result = await _run_with_retry(agent, history, context)
    except Exception as exc:
        db.rollback()
        # See the streamed path: a dead-but-not-None MCP session fails every
        # later turn until it is dropped.
        await mcp.reset()
        logger.error(
            "handle_chat failed user_id=%s session_id=%s: %s",
            user_id, session_id, exc, exc_info=True,
        )
        raise LLMUnavailableError(
            "Sarjy is having trouble responding right now. Please try again."
        ) from exc

    # A tool-only turn can leave `final_output` empty or non-string, and the
    # content column is NOT NULL.
    reply = "" if result.final_output is None else str(result.final_output)

    def _write() -> None:
        sessions_repo.add_message(db, session_id, "assistant", reply)
        # Inserting a Message does not touch the Session row, so `onupdate` never
        # fires. Set it explicitly to keep the sidebar's recency ordering correct.
        session.updated_at = now_utc()
        db.commit()

    with timings.span("db_write_ms"):
        await asyncio.to_thread(_write)

    # A non-streamed turn only ever sees the whole response, so there is no
    # first-token moment to measure. The streaming endpoint fills this in.
    timings.set("llm_ttft_ms", None)

    payload = timings.as_dict()
    logger.info(
        "handle_chat complete user_id=%s session_id=%s %s",
        user_id, session_id, timings.as_log_line(payload),
    )

    return reply, payload, tool_names_from(result)
