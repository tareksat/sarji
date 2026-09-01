"""Latency harness: N turns of one fixed prompt, p50/p95 per segment.

Usage:
    python scripts/measure.py --base-url https://sarjy.onrender.com --label baseline
    python scripts/measure.py --base-url ... --label streaming --stream

Each iteration uses a fresh session id so history length stays constant, and
the first run is discarded as a warm-up. Covers the server and network
segments only; the browser-side marks come from summarize_client_timings.py.
"""

import argparse
import json
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


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(p / 100 * len(ordered) + 0.5) - 1))
    return round(ordered[index], 1)


def run_once(client: httpx.Client, user_id: str, prompt: str, stream: bool) -> dict:
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
        return timings

    first_byte = None
    timings = {}
    with client.stream("POST", "/api/chat/stream", json=payload) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line.startswith("data: "):
                continue
            event = json.loads(line[len("data: "):])
            if event["type"] == "delta" and first_byte is None:
                first_byte = (time.perf_counter() - started) * 1000
            elif event["type"] == "done":
                timings = dict(event.get("timings") or {})
            elif event["type"] == "error":
                raise RuntimeError(event.get("detail", "stream error"))

    total = (time.perf_counter() - started) * 1000
    timings["client_first_byte_ms"] = round(first_byte or total, 1)
    timings["client_total_ms"] = round(total, 1)
    return timings


def render_table(label: str, base_url: str, prompt: str, rows: list[dict]) -> str:
    lines = [
        f"# Latency run — {label}",
        "",
        f"- Target: `{base_url}`",
        f"- Prompt: `{prompt}`",
        f"- Iterations: {len(rows)} (warm-up discarded)",
        "",
        "| Segment | p50 (ms) | p95 (ms) |",
        "|---|---:|---:|",
    ]
    for name in SEGMENTS:
        values = [r[name] for r in rows if isinstance(r.get(name), (int, float))]
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
        run_once(client, user_id, args.prompt, args.stream)
        for i in range(args.iterations):
            row = run_once(client, user_id, args.prompt, args.stream)
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


if __name__ == "__main__":
    main()
