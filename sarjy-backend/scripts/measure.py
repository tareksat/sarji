"""Latency harness: N turns of one fixed prompt, p50/p95 per segment.

Usage:
    python scripts/measure.py --base-url https://sarjy.onrender.com --label baseline
    python scripts/measure.py --base-url ... --label streaming --stream

Each iteration uses a fresh session id so history length stays constant, and
the first run is discarded as a warm-up. Covers the server and network
segments.

Every measured turn is also validated, so a fast-but-broken turn cannot pass:
the streamed deltas must reconstruct the reply, the reply must satisfy the
validator for its prompt, both messages must be readable back from the session
endpoints, and the weather prompt must actually have called `get_weather`.
Failed turns are kept in the raw dump but excluded from the percentiles, and
`main` exits non-zero if any of them failed.
"""

import argparse
import json
import math
import re
import sys
import time
import uuid
from pathlib import Path

import httpx

TIMEOUT_SECONDS = 120.0
DEFAULT_PROMPT = "In one sentence, what is the capital of France?"
SEGMENTS = [
    "db_read_ms",
    "db_write_pre_ms",
    "limiter_wait_ms",
    "llm_ttft_ms",
    "llm_total_ms",
    "db_write_ms",
    "total_ms",
    "client_first_byte_ms",
    "client_total_ms",
]

# A sentence ends at `.`, `!` or `?` followed by whitespace or the end of the
# string. Deliberately naive: abbreviations are out of scope, and the tolerance
# below absorbs the odd miscount.
SENTENCE_END_RE = re.compile(r"[.!?](?:\s+|$)")
# A number glued or spaced to a degree sign or a bare C/F unit: 34°C, 34 C, 34F.
# The word boundary keeps "34 Celsius" and "12 Coffees" out.
TEMPERATURE_RE = re.compile(r"\d\s*(?:°|[CF]\b)")


def sentence_count(reply: str) -> int:
    """How many sentences the reply contains, ignoring empty segments."""
    return len([part for part in SENTENCE_END_RE.split(reply) if part.strip()])


def mentions_paris(reply: str) -> bool:
    return "paris" in reply.lower()


def is_four_sentences(reply: str) -> bool:
    # 4 ± 1: the model is asked for exactly four, but one miscounted clause
    # should not fail a latency run.
    return 3 <= sentence_count(reply) <= 5


def looks_like_weather(reply: str) -> bool:
    return "riyadh" in reply.lower() or TEMPERATURE_RE.search(reply) is not None


# Keyed by the exact prompt strings the study uses; see docs/latency/REPORT.md.
# Each validator is pure: no network, no model call.
VALIDATORS = {
    "In one sentence, what is the capital of France?": mentions_paris,
    "Describe Paris in exactly four sentences.": is_four_sentences,
    "What's the weather in Riyadh right now?": looks_like_weather,
}

# Tools a prompt must have called. Only the weather prompt asserts anything.
REQUIRED_TOOLS = {
    "What's the weather in Riyadh right now?": ["get_weather"],
}


def percentile(values: list[float], p: float) -> float | None:
    """Nearest-rank percentile: the smallest value at or above rank ceil(p/100*n).

    The previous form, `round(p/100*n + 0.5) - 1`, landed one rank high and, via
    banker's rounding, did so only for some sample counts -- at n=10 it reported
    the upper median as p50, and runs of different lengths were not comparable
    with each other.
    """
    if not values:
        return None
    ordered = sorted(values)
    rank = math.ceil(p / 100 * len(ordered))
    index = min(len(ordered) - 1, max(0, rank - 1))
    return round(ordered[index], 1)


def valid_rows(rows: list[dict]) -> list[dict]:
    """The rows that passed validation.

    Percentiles are computed over these only: an error response answers fast,
    and letting it into the sample flatters every segment it touches.
    """
    return [row for row in rows if row.get("ok", True)]


def stream_integrity_ok(deltas: list[str], reply: str) -> bool:
    """Whether the deltas, concatenated in arrival order, are the final reply."""
    return "".join(deltas) == reply


def run_once(client: httpx.Client, user_id: str, prompt: str, stream: bool) -> dict:
    """One turn. Returns its timings, reply, tools and any failure found here.

    The `failures` list carries only what this function can see -- currently
    the stream-integrity check; the content, persistence and tool checks are
    applied by `evaluate`, which needs the prompt and a second HTTP call.
    """
    session_id = str(uuid.uuid4())
    payload = {"user_id": user_id, "session_id": session_id, "message": prompt}
    started = time.perf_counter()

    if not stream:
        resp = client.post("/api/chat", json=payload)
        resp.raise_for_status()
        body = resp.json()
        elapsed = (time.perf_counter() - started) * 1000
        timings = dict(body.get("timings") or {})
        timings["client_first_byte_ms"] = round(elapsed, 1)
        timings["client_total_ms"] = round(elapsed, 1)
        return {
            "timings": timings,
            "reply": body.get("reply", ""),
            "tools_used": list(body.get("tools_used") or []),
            "session_id": session_id,
            "failures": [],
        }

    first_byte = None
    timings = {}
    deltas: list[str] = []
    reply = ""
    tools_used: list[str] = []
    with client.stream("POST", "/api/chat/stream", json=payload) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line.startswith("data: "):
                continue
            event = json.loads(line[len("data: "):])
            if event["type"] == "delta":
                if first_byte is None:
                    first_byte = (time.perf_counter() - started) * 1000
                deltas.append(event.get("text", ""))
            elif event["type"] == "done":
                timings = dict(event.get("timings") or {})
                reply = event.get("reply", "")
                tools_used = list(event.get("tools_used") or [])
            elif event["type"] == "error":
                raise RuntimeError(event.get("detail", "stream error"))

    total = (time.perf_counter() - started) * 1000
    timings["client_first_byte_ms"] = round(first_byte or total, 1)
    timings["client_total_ms"] = round(total, 1)

    failures = [] if stream_integrity_ok(deltas, reply) else ["stream_integrity"]
    return {
        "timings": timings,
        "reply": reply,
        "tools_used": tools_used,
        "session_id": session_id,
        "failures": failures,
    }


def persisted(client: httpx.Client, user_id: str, session_id: str, prompt: str, reply: str) -> bool:
    """Whether both halves of the turn can be read back from the session API.

    Public HTTP only -- the harness runs against deployed targets, where there
    is no database to look into.
    """
    resp = client.get(
        f"/api/sessions/{session_id}/messages", params={"user_id": user_id}
    )
    if resp.status_code != 200:
        return False
    stored = resp.json()
    contents = {(m.get("role"), m.get("content")) for m in stored}
    return ("user", prompt) in contents and ("assistant", reply) in contents


def evaluate(client: httpx.Client, user_id: str, prompt: str, result: dict) -> str | None:
    """The first check this turn failed, or None if it passed them all.

    Order matters: a broken stream explains a bad reply, which explains a bad
    persisted row, so the earliest failure is the one worth reporting.
    """
    if result["failures"]:
        return result["failures"][0]

    validator = VALIDATORS.get(prompt)
    # A prompt with no validator is measured but not content-checked, as before.
    if validator is not None and not validator(result["reply"]):
        return "content"

    if not persisted(client, user_id, result["session_id"], prompt, result["reply"]):
        return "persistence"

    for tool in REQUIRED_TOOLS.get(prompt, []):
        if tool not in result["tools_used"]:
            return "tool_not_called"

    return None


def render_table(label: str, base_url: str, prompt: str, rows: list[dict]) -> str:
    passing = valid_rows(rows)
    failed = [
        (i, row.get("failed_check", "unknown"))
        for i, row in enumerate(rows, start=1)
        if not row.get("ok", True)
    ]

    lines = [
        f"# Latency run — {label}",
        "",
        f"- Target: `{base_url}`",
        f"- Prompt: `{prompt}`",
        f"- Iterations: {len(rows)} (warm-up discarded)",
        "",
        f"Valid: {len(passing)}/{len(rows)} turns",
    ]
    for iteration, check in failed:
        lines.append(f"- {iteration} → {check}")
    lines += [
        "",
        "| Segment | p50 (ms) | p95 (ms) |",
        "|---|---:|---:|",
    ]
    for name in SEGMENTS:
        values = [r[name] for r in passing if isinstance(r.get(name), (int, float))]
        if not values:
            lines.append(f"| `{name}` | — | — |")
            continue
        lines.append(f"| `{name}` | {percentile(values, 50)} | {percentile(values, 95)} |")
    lines.append("")
    lines.append("Raw per-run values:")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(rows, indent=2))
    lines.append("```")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--out-dir", default="../docs/latency/runs")
    args = parser.parse_args()

    user_id = str(uuid.uuid4())
    rows: list[dict] = []

    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=TIMEOUT_SECONDS) as client:
        print("warm-up…")
        # Discarded, and not validated: it exists to pay the cold-start cost.
        run_once(client, user_id, args.prompt, args.stream)
        for i in range(args.iterations):
            result = run_once(client, user_id, args.prompt, args.stream)
            failed_check = evaluate(client, user_id, args.prompt, result)
            row = {**result["timings"], "ok": failed_check is None}
            if failed_check is not None:
                row["failed_check"] = failed_check
            rows.append(row)
            print(f"{i + 1}/{args.iterations}: {row}")

    table = render_table(args.label, args.base_url, args.prompt, rows)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.label}.md"
    out_path.write_text(table, encoding="utf-8")

    print()
    print(table)
    print(f"written to {out_path}")

    failures = len(rows) - len(valid_rows(rows))
    if failures:
        print(f"{failures} of {len(rows)} turns failed validation", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
