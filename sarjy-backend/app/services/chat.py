import asyncio
import logging
import uuid

from agents import Runner
from openai import RateLimitError
from sqlalchemy.orm import Session as DbSession

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


async def _run_with_retry(agent, history: list[dict], context: ChatContext):
    last_error: RateLimitError | None = None
    delays = [0, *settings.llm_retry_backoff_seconds]
    for attempt, delay in enumerate(delays, start=1):
        if delay:
            await asyncio.sleep(delay)
        try:
            return await Runner.run(agent, input=history, context=context)
        except RateLimitError as exc:
            last_error = exc
            logger.warning(
                "Rate limited by OpenAI on attempt %d/%d (delay=%ss): %s",
                attempt, len(delays), delay, exc,
            )
    raise last_error


async def handle_chat(
    db: DbSession, user_id: uuid.UUID, session_id: uuid.UUID, message: str
) -> tuple[str, dict[str, float | None]]:
    logger.info("handle_chat start user_id=%s session_id=%s", user_id, session_id)
    timings = Timings()

    with timings.span("db_read_ms"):
        users_repo.upsert(db, user_id)
        session = sessions_repo.get_or_create(db, session_id, user_id, title_from_message(message))
        sessions_repo.add_message(db, session_id, "user", message)
        db.flush()
        history = [
            {"role": m.role, "content": m.content}
            for m in sessions_repo.recent_messages(db, session_id, settings.chat_history_limit)
        ]
        facts = memory_repo.facts_for_user(db, user_id, settings.memory_facts_limit)

    agent = build_agent(facts)
    context = ChatContext(user_id=user_id, session_id=session_id, db=db)

    timings.set("limiter_wait_ms", await _rate_limiter.acquire())

    try:
        with timings.span("llm_total_ms"):
            result = await _run_with_retry(agent, history, context)
    except Exception as exc:
        db.rollback()
        logger.error(
            "handle_chat failed user_id=%s session_id=%s: %s",
            user_id, session_id, exc, exc_info=True,
        )
        raise LLMUnavailableError(
            "Sarjy is having trouble responding right now. Please try again."
        ) from exc

    reply = result.final_output

    with timings.span("db_write_ms"):
        sessions_repo.add_message(db, session_id, "assistant", reply)
        # Inserting a Message does not touch the Session row, so `onupdate` never
        # fires. Set it explicitly to keep the sidebar's recency ordering correct.
        session.updated_at = now_utc()
        db.commit()

    # A non-streamed turn only ever sees the whole response, so there is no
    # first-token moment to measure. The streaming endpoint fills this in.
    timings.set("llm_ttft_ms", None)

    logger.info(
        "handle_chat complete user_id=%s session_id=%s %s",
        user_id, session_id, timings.as_log_line(),
    )

    return reply, timings.as_dict()
