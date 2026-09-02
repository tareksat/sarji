"""Summarize browser timing lines into the same p50/p95 table shape.

Collect the `[sarjy-timing] {...}` lines from the Chrome console into a file,
then:

    python scripts/summarize_client_timings.py runs/baseline-client.txt --source typed

`--source` picks which turns to summarize, and the two kinds are not
interchangeable. A typed turn can be driven by browser automation and gives
`first_byte_ms` and `reply_complete_ms` exactly as a spoken turn does, because
nothing after the request is sent depends on how the message was composed. It
cannot give `stt_tail_ms` at all, and its `ttfa_ms` is measured from the request
rather than from the end of speech - a different quantity that must not be
reported as time-to-first-audio.

A voice turn is still collected by hand: driving the microphone would change the
thing being measured. Both kinds can share one file; `source` on each line keeps
them apart.
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

    decoder = json.JSONDecoder()
    rows = []
    skipped = 0
    for line in Path(args.path).read_text(encoding="utf-8").splitlines():
        marker = line.find(PREFIX)
        if marker == -1:
            continue
        try:
            # raw_decode stops at the end of the object, so anything the console
            # appends after it (a source annotation, a timestamp) is ignored.
            row, _ = decoder.raw_decode(line[marker + len(PREFIX):])
        except json.JSONDecodeError:
            skipped += 1
            continue
        if row.get("source") == args.source:
            rows.append(row)

    if skipped:
        print(f"skipped {skipped} unparseable line(s)\n", file=sys.stderr)

    if not rows:
        print(f"No {args.source} turns found in {args.path}")
        sys.exit(1)

    print("| Segment | p50 (ms) | p95 (ms) | N |")
    print("|---|---:|---:|---:|")
    for name in SEGMENTS:
        # Each segment is counted on its own: a turn that never started audio
        # contributes to first_byte_ms but not to ttfa_ms.
        values = [r[name] for r in rows if isinstance(r.get(name), (int, float))]
        print(f"| `{name}` | {percentile(values, 50)} | {percentile(values, 95)} | {len(values)} |")
    print(f"\n{len(rows)} {args.source} turns.")


if __name__ == "__main__":
    main()
