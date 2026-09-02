import uuid

from fastapi import HTTPException


def parse_uuid(value: str, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (ValueError, TypeError, AttributeError) as exc:
        # Not just ValueError: a non-string reaches uuid.UUID as a TypeError or
        # an AttributeError, and those would surface as a 500 rather than the
        # 400 this is for. Not reachable while every caller is a pydantic-typed
        # str, but it is one loosened annotation away.
        raise HTTPException(status_code=400, detail=f"{field} must be a UUID") from exc
