import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DbSession

from ..core.db import get_db
from ..core.ids import parse_uuid
from ..dtos import ChatRequest, ChatResponse, ErrorResponse
from ..services.chat import LLMUnavailableError, handle_chat

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

BAD_UUID = {400: {"model": ErrorResponse, "description": "A path or query id is not a UUID."}}


@router.post(
    "/api/chat",
    response_model=ChatResponse,
    summary="Send a message and get Sarjy's reply",
    response_description="Sarjy's reply text.",
    responses={
        **BAD_UUID,
        502: {
            "model": ErrorResponse,
            "description": "The model could not be reached, even after retries.",
        },
    },
)
async def chat(req: ChatRequest, db: DbSession = Depends(get_db)):
    """Run one conversational turn.

    Creates the user and session rows if they are new, persists the incoming
    message, replays the recent history along with everything Sarjy remembers
    about this user, and returns the reply.

    The model may call `save_memory` during the turn to record a durable fact.
    That write is committed as part of the same turn and is visible to every
    later session for this user.

    Outbound model calls pass through a token-bucket limiter that makes callers
    wait rather than rejecting them, so a busy server shows up as latency.
    """
    user_id = parse_uuid(req.user_id, "user_id")
    session_id = parse_uuid(req.session_id, "session_id")

    try:
        reply = await handle_chat(db, user_id, session_id, req.message)
    except LLMUnavailableError as exc:
        logger.warning("Returning 502 for user_id=%s session_id=%s: %s", user_id, session_id, exc)
        raise HTTPException(status_code=502, detail=str(exc))

    return ChatResponse(reply=reply)
