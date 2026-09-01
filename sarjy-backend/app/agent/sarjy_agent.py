import logging
from dataclasses import dataclass
from uuid import UUID

from agents import Agent, RunContextWrapper, function_tool
from sqlalchemy.orm import Session as DbSession

from ..core.config import settings
from ..models import Memory
from .mcp import sarjy_mcp_server

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are Sarjy, a helpful, warm voice-and-text assistant. "
    "Keep replies concise and conversational, since they may be read aloud.\n\n"
    "When the user asks about the weather: look for a saved location among the "
    "known facts about this user below. If one is present, call get_weather with "
    "it directly. If none is present, ask the user what location they mean before "
    "calling any weather tool. Once they answer, call save_memory to remember the "
    "location, then call get_weather with it."
)

FACT_LOG_MAX_LENGTH = 60


@dataclass
class ChatContext:
    user_id: UUID
    session_id: UUID
    db: DbSession


@function_tool
async def save_memory(ctx: RunContextWrapper[ChatContext], fact: str) -> str:
    """Save a durable fact about the user that should be remembered in future
    conversations, even in a different session (e.g. preferences, names, ongoing
    situations). Only call this for things worth recalling later, not small talk."""
    db = ctx.context.db
    db.add(
        Memory(
            user_id=ctx.context.user_id,
            content=fact,
            source_session_id=ctx.context.session_id,
        )
    )
    db.commit()

    truncated = fact if len(fact) <= FACT_LOG_MAX_LENGTH else f"{fact[:FACT_LOG_MAX_LENGTH]}…"
    logger.info("Saved memory for user_id=%s: %s", ctx.context.user_id, truncated)

    return f"Remembered: {fact}"


def build_agent(memory_facts: list[str]) -> Agent:
    instructions = SYSTEM_PROMPT
    if memory_facts:
        bullet_list = "\n".join(f"- {fact}" for fact in memory_facts)
        instructions += f"\n\nKnown facts about this user:\n{bullet_list}"

    return Agent(
        name="Sarjy",
        instructions=instructions,
        model=settings.llm_model,
        tools=[save_memory],
        mcp_servers=[sarjy_mcp_server],  # get_weather lives in sarjy-mcp-server
    )
