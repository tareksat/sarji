from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/api/health",
    summary="Liveness probe",
    response_description="Always `{\"status\": \"ok\"}` when the process is up.",
)
async def health() -> dict[str, str]:
    """Report that the API process is running.

    Deliberately does not touch the database: this is the target of the
    platform's health check, and a slow database should not cycle the service.
    """
    return {"status": "ok"}
