import asyncio
import logging
from dataclasses import dataclass
from uuid import UUID

from agents import Agent, RunContextWrapper, function_tool
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..core.config import settings
from ..core.db import SessionLocal
from ..models import Memory
from .local_weather import local_get_weather
from .mcp import sarjy_mcp_server

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Sarjy, a helpful, warm voice-and-text assistant. "
    "Keep replies concise and conversational, since they may be read aloud.\n\n"
    "Memory: whenever the user states a durable fact about themselves -- their "
    "name, where they live, their job or employer, family, pets, preferences, "
    "goals, or an ongoing situation -- call save_memory in that same turn, once "
    "per fact, and then answer normally. Write each fact as one short "
    "third-person sentence, for example \"User works as a data engineer\". A "
    "message with several facts means several save_memory calls, not one merged "
    "call. Do not ask permission and do not mention that you saved anything. If "
    "a new fact contradicts a known one (they moved, changed jobs), save the new "
    "one anyway.\n\n"
    "When the user asks about the weather: look for a saved location among the "
    "known facts about this user below. If one is present, call get_weather with "
    "it directly. If none is present, ask the user what location they mean before "
    "calling any weather tool. Once they answer, call save_memory to remember the "
    "location, then call get_weather with it."
)

FACT_LOG_MAX_LENGTH = 60


@dataclass
class ChatContext:
    # No DB session here on purpose. The SDK runs every tool call of a turn as
    # its own task, and this tool does its write on a worker thread; handing
    # those the request's Session would share one non-thread-safe Session
    # between threads. The tool opens its own.
    user_id: UUID
    session_id: UUID


def _save_fact(user_id: UUID, session_id: UUID, fact: str) -> bool:
    """Store the fact unless the user already has it. True if a row was added.

    Idempotent because a turn can be replayed: `_run_with_retry` re-runs the
    whole agent turn after a transient model error, and this tool has already
    committed by then. Without the check, "remember I live in Riyadh" becomes
    two or three identical rows, each of which is then injected into the system
    prompt of every later turn.

    The select is only a fast path. Two calls in one turn run in parallel, so
    both can miss the row the other is about to commit; the unique constraint
    on (user_id, content) is what actually holds the line.
    """
    with SessionLocal() as db:
        existing = db.execute(
            select(Memory.id).where(Memory.user_id == user_id, Memory.content == fact).limit(1)
        ).first()
        if existing is not None:
            return False
        db.add(Memory(user_id=user_id, content=fact, source_session_id=session_id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return False
        return True


@function_tool
async def save_memory(ctx: RunContextWrapper[ChatContext], fact: str) -> str:
    """Save one durable fact about the user so it is remembered in every future
    conversation, including other sessions: their name, where they live, their
    job or employer, family, pets, preferences, goals, ongoing situations. Call
    it as soon as the user states such a fact, once per fact, with one short
    third-person sentence such as "User works as a data engineer"."""
    fact = fact.strip()
    if not fact:
        return "Nothing to remember."

    # Every stored fact is injected into the system prompt of every later turn,
    # so one verbose "fact" would raise the time-to-first-token for the life of
    # the account. Shortened rather than refused: refusing costs the memory.
    shortened = len(fact) > settings.memory_fact_max_length
    if shortened:
        fact = fact[: settings.memory_fact_max_length].rstrip()

    try:
        # Off the event loop: this runs mid-turn, while other turns are
        # streaming through the same worker.
        added = await asyncio.to_thread(
            _save_fact, ctx.context.user_id, ctx.context.session_id, fact
        )
    except Exception:
        # Returned to the model rather than raised: a failed memory write should
        # cost the user a memory, not the whole answer.
        logger.exception("Could not save memory for user_id=%s", ctx.context.user_id)
        return "That could not be saved right now."

    truncated = fact if len(fact) <= FACT_LOG_MAX_LENGTH else f"{fact[:FACT_LOG_MAX_LENGTH]}…"
    logger.info(
        "%s memory for user_id=%s: %s",
        "Saved" if added else "Already knew", ctx.context.user_id, truncated,
    )

    return f"Remembered (shortened): {fact}" if shortened else f"Remembered: {fact}"


def build_agent(memory_facts: list[str], mcp_ready: bool = True, model: str | None = None) -> Agent:
    instructions = SYSTEM_PROMPT
    if memory_facts:
        bullet_list = "\n".join(f"- {fact}" for fact in memory_facts)
        instructions += (
            "\n\nKnown facts about this user, oldest first; a later entry "
            f"supersedes an earlier one it contradicts:\n{bullet_list}"
        )

    tools = [save_memory]
    # `mcp_ready` false means the tool server is down. Answering without weather
    # beats failing every turn until it comes back.
    mcp_servers = [sarjy_mcp_server] if mcp_ready else []  # get_weather lives there
    if settings.use_local_weather_tool:
        # A/B for the latency write-up: same tool, no transport hop.
        tools.append(local_get_weather)
        mcp_servers = []

    return Agent(
        name="Sarjy",
        instructions=instructions,
        model=model or settings.llm_model,
        tools=tools,
        mcp_servers=mcp_servers,
    )
