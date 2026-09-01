from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from sqlalchemy.orm import Session as DbSession

from ..core.db import get_db
from ..core.ids import parse_uuid
from ..repositories import sessions as sessions_repo
from ..models import Session as SessionModel
from ..dtos import ErrorResponse, MessageOut, SessionOut, SessionUpdate

router = APIRouter(tags=["sessions"])

BAD_UUID = {400: {"model": ErrorResponse, "description": "A path or query id is not a UUID."}}
NOT_FOUND = {404: {"model": ErrorResponse, "description": "No such session for this user."}}

USER_ID_QUERY = Query(
    ...,
    description="The browser's UUID, from `localStorage` under `sarjy_user_id`.",
    examples=["3f1a9c2e-5b7d-4e88-9a21-6c0f4d8b1e33"],
)
SESSION_ID_PATH = Path(
    ...,
    description="The conversation's UUID.",
    examples=["b74e2f10-8c3a-4d61-9f52-1a7e0c9d4b88"],
)


def _owned_session(db: DbSession, session_id: str, user_id: str) -> SessionModel:
    sid = parse_uuid(session_id, "session_id")
    uid = parse_uuid(user_id, "user_id")
    session = sessions_repo.owned(db, sid, uid)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get(
    "/api/sessions",
    response_model=list[SessionOut],
    summary="List a user's conversations",
    response_description="Sessions, most recently active first.",
    responses={**BAD_UUID},
)
def list_sessions(user_id: str = USER_ID_QUERY, db: DbSession = Depends(get_db)):
    """Return every session belonging to this user, ordered by `updated_at`
    descending. Sessions with no messages yet do not appear, because their row
    does not exist until the first turn.
    """
    uid = parse_uuid(user_id, "user_id")
    return sessions_repo.list_for_user(db, uid)


@router.get(
    "/api/sessions/{session_id}/messages",
    response_model=list[MessageOut],
    summary="Read a conversation's transcript",
    response_description="Messages in chronological order.",
    responses={**BAD_UUID, **NOT_FOUND},
)
def list_messages(
    session_id: str = SESSION_ID_PATH,
    user_id: str = USER_ID_QUERY,
    db: DbSession = Depends(get_db),
):
    """Return the full transcript for one session, oldest first.

    This is the whole conversation, not the windowed slice replayed to the
    model on each turn -- that window is capped by `chat_history_limit`.
    """
    session = _owned_session(db, session_id, user_id)
    return sessions_repo.list_messages(db, session.id)


@router.patch(
    "/api/sessions/{session_id}",
    response_model=SessionOut,
    summary="Rename a conversation",
    response_description="The updated session.",
    responses={**BAD_UUID, **NOT_FOUND},
)
def rename_session(
    body: SessionUpdate,
    session_id: str = SESSION_ID_PATH,
    user_id: str = USER_ID_QUERY,
    db: DbSession = Depends(get_db),
):
    """Replace the session's title.

    Titles are otherwise derived from the first user message. A rename is
    permanent -- later turns do not overwrite it.
    """
    session = _owned_session(db, session_id, user_id)
    return sessions_repo.rename(db, session, body.title.strip())


@router.delete(
    "/api/sessions/{session_id}",
    status_code=204,
    summary="Delete a conversation",
    response_description="Deleted. No body.",
    responses={**BAD_UUID, **NOT_FOUND},
)
def remove_session(
    session_id: str = SESSION_ID_PATH,
    user_id: str = USER_ID_QUERY,
    db: DbSession = Depends(get_db),
):
    """Delete a session and its messages.

    Memories learned during the conversation are kept, with their
    `source_session_id` set to null. Durable facts about the user are not the
    conversation's to take with it.
    """
    session = _owned_session(db, session_id, user_id)
    sessions_repo.delete_cascade(db, session)
    return Response(status_code=204)
