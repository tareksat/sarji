"""Pool several raw `measure.py` run files into one table.

    python scripts/pool_runs.py --label streaming streaming-1 streaming-2

Reads `../docs/latency/runs/<source>.md` for each source, concatenates the raw
rows from their ```json blocks, and writes `<label>-pooled.md` beside them with
the same p50/p95 table shape. `measure.py` overwrites `<label>.md` on every run,
so the pooled name is the only one safe to keep by hand.
"""

import argparse
import json
import re
from pathlib import Path

from measure import SEGMENTS, percentile

HEADER_RE = re.compile(r"^- (Target|Prompt): `(.*)`$", re.MULTILINE)
JSON_BLOCK_RE = re.compile(r"```json\n(.*?)\n```", re.DOTALL)


def parse_run(text: str) -> tuple[str, str, list[dict]]:
    fields = dict(HEADER_RE.findall(text))
    match = JSON_BLOCK_RE.search(text)
    if match is None:
        raise ValueError("no ```json block in run file")
    return fields.get("Target", ""), fields.get("Prompt", ""), json.loads(match.group(1))


def pool(label: str, base_url: str, prompt: str, sources: list[tuple[str, list[dict]]]) -> str:
    rows = [row for _, source_rows in sources for row in source_rows]
    pooled_from = ", ".join(f"`{name}` ({len(source_rows)})" for name, source_rows in sources)
    lines = [
        f"# Latency run — {label} (pooled)",
        "",
        f"- Target: `{base_url}`",
        f"- Prompt: `{prompt}`",
        f"- Pooled from: {pooled_from}",
        f"- Iterations: {len(rows)} (warm-ups discarded per invocation)",
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
    lines += ["", "Raw per-run values:", "", "```json", json.dumps(rows, indent=2), "```"]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("sources", nargs="+", help="run labels, e.g. streaming-1 streaming-2")
    parser.add_argument("--runs-dir", default="../docs/latency/runs")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    parsed = []
    base_url = prompt = ""
    for source in args.sources:
        source_url, source_prompt, rows = parse_run((runs_dir / f"{source}.md").read_text(encoding="utf-8"))
        if base_url and (source_url, source_prompt) != (base_url, prompt):
            raise SystemExit(f"{source}: target or prompt differs from {args.sources[0]}; not the same condition")
        base_url, prompt = source_url, source_prompt
        parsed.append((source, rows))

    out_path = runs_dir / f"{args.label}-pooled.md"
    out_path.write_text(pool(args.label, base_url, prompt, parsed), encoding="utf-8")
    print(f"written to {out_path}")


if __name__ == "__main__":
    main()
