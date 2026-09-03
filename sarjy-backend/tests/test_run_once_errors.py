import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from measure import run_once  # noqa: E402


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler), base_url="https://example.test")


def test_non_streamed_http_error_is_a_soft_failure_not_a_raise():
    def handler(request):
        return httpx.Response(502, text="upstream model rejected")

    with _client(handler) as client:
        result = run_once(client, "user-1", "hello", stream=False, model="bad-alias")

    assert result["failures"] == ["http_error:502"]
    assert result["reply"] == ""
    assert result["tools_used"] == []


def test_streamed_error_frame_is_a_soft_failure_not_a_raise():
    body = 'data: {"type": "error", "detail": "Rate limited. Retry in 3s."}\n\n'

    def handler(request):
        return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})

    with _client(handler) as client:
        result = run_once(client, "user-1", "hello", stream=True)

    assert result["failures"] == ["stream_error:Rate limited. Retry in 3s."]
    assert result["reply"] == ""


def test_non_streamed_success_still_has_no_failures():
    def handler(request):
        return httpx.Response(200, json={"reply": "hi", "timings": {}, "tools_used": []})

    with _client(handler) as client:
        result = run_once(client, "user-1", "hello", stream=False)

    assert result["failures"] == []
    assert result["reply"] == "hi"
