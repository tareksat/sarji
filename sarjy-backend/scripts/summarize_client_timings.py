"""Summarize browser timing lines into the same p50/p95 table shape.

Copy the `[sarjy-timing] {...}` lines out of the Chrome console into a file,
then:

    python scripts/summarize_client_timings.py runs/baseline-client.txt

The browser marks (STT tail, time-to-first-audio) cannot be driven headlessly
without changing the thing being measured, so they are collected by hand from
ten real spoken turns on the deployed app.
"""

import argparse
import json
import sys
from pathlib import Path

PREFIX = "[sarjy-timing] "
SEGMENTS = ["stt_tail_ms", "first_byte_ms", "reply_complete_ms", "ttfa_ms"]


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(p / 100 * len(ordered) + 0.5) - 1))
    return round(ordered[index], 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--source", choices=["voice", "typed"], default="voice")
    args = parser.parse_args()

    rows = []
    for line in Path(args.path).read_text(encoding="utf-8").splitlines():
        marker = line.find(PREFIX)
        if marker == -1:
            continue
        row = json.loads(line[marker + len(PREFIX):])
        if row.get("source") == args.source:
            rows.append(row)

    if not rows:
        print(f"No {args.source} turns found in {args.path}")
        sys.exit(1)

    print("| Segment | p50 (ms) | p95 (ms) |")
    print("|---|---:|---:|")
    for name in SEGMENTS:
        values = [r[name] for r in rows if isinstance(r.get(name), (int, float))]
        print(f"| `{name}` | {percentile(values, 50)} | {percentile(values, 95)} |")
    print(f"\n{len(rows)} {args.source} turns.")


if __name__ == "__main__":
    main()
