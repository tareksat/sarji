import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DbSession

from ..core.db import get_db
from ..core.ids import parse_uuid
from ..core.rate_limiter import RateLimitedError
from ..dtos import ChatRequest, ChatResponse, ErrorResponse
from ..services.chat import LLMUnavailableError, handle_chat
from ..services.streaming import stream_chat

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
        429: {
            "model": ErrorResponse,
            "description": "The local token bucket would have queued this turn past its cap.",
        },
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
        reply, timings = await handle_chat(db, user_id, session_id, req.message)
    except RateLimitedError as exc:
        raise HTTPException(
            status_code=429,
            detail=str(exc),
            headers={"Retry-After": str(max(1, round(exc.retry_after_seconds)))},
        )
    except LLMUnavailableError as exc:
        logger.warning("Returning 502 for user_id=%s session_id=%s: %s", user_id, session_id, exc)
        raise HTTPException(status_code=502, detail=str(exc))

    return ChatResponse(reply=reply, timings=timings)


@router.post(
    "/api/chat/stream",
    summary="Send a message and stream Sarjy's reply",
    response_description="A `text/event-stream` of `delta` frames, then one `done` frame.",
    responses={**BAD_UUID},
)
async def chat_stream(req: ChatRequest, db: DbSession = Depends(get_db)):
    """Run one conversational turn, streamed.

    Identical to `POST /api/chat` in what it persists; the difference is that
    tokens are emitted as they arrive, so the browser can begin speaking at the
    first sentence boundary rather than at the last token. Frames are
    `data: {json}` and carry `type` of `delta`, `done`, or `error`; failures
    arrive as an `error` frame with HTTP 200, since the response has usually
    already begun by then.
    """
    user_id = parse_uuid(req.user_id, "user_id")
    session_id = parse_uuid(req.session_id, "session_id")

    async def events():
        async for event in stream_chat(db, user_id, session_id, req.message):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # stop any proxy from buffering the stream
        },
    )
