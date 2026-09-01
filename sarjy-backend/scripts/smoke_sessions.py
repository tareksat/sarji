"""End-to-end check of the session endpoints and the delete cascade.

Usage:
    python scripts/smoke_sessions.py --base-url http://localhost:8000

Exits non-zero on the first failed assertion. Uses a throwaway user id, so it
is safe to run against the deployed app.
"""

import argparse
import sys
import uuid

import httpx

TIMEOUT_SECONDS = 60.0


def check(condition: bool, message: str) -> None:
    if not condition:
        print(f"FAIL: {message}")
        sys.exit(1)
    print(f"ok: {message}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    other_user = str(uuid.uuid4())

    with httpx.Client(base_url=base, timeout=TIMEOUT_SECONDS) as client:
        resp = client.get("/api/health")
        check(resp.status_code == 200 and resp.json()["status"] == "ok", "health returns ok")

        resp = client.post(
            "/api/chat",
            json={
                "user_id": user_id,
                "session_id": session_id,
                "message": "Remember I live in Riyadh.",
            },
        )
        check(resp.status_code == 200, f"chat turn succeeded (got {resp.status_code})")

        resp = client.get("/api/sessions", params={"user_id": user_id})
        check(resp.status_code == 200 and len(resp.json()) == 1, "session list has one row")

        resp = client.get(f"/api/sessions/{session_id}/messages", params={"user_id": user_id})
        check(resp.status_code == 200 and len(resp.json()) >= 2, "message list has the turn")

        resp = client.get(f"/api/sessions/{session_id}/messages", params={"user_id": other_user})
        check(resp.status_code == 404, "another user's session returns 404")

        resp = client.patch(
            f"/api/sessions/{session_id}", params={"user_id": user_id}, json={"title": "renamed"}
        )
        check(resp.status_code == 200 and resp.json()["title"] == "renamed", "rename works")

        resp = client.delete(f"/api/sessions/{session_id}", params={"user_id": user_id})
        check(resp.status_code in (200, 204), "delete works")

        resp = client.get("/api/sessions", params={"user_id": user_id})
        check(resp.json() == [], "session list is empty after delete")

    print("\nAll session checks passed.")


if __name__ == "__main__":
    main()
