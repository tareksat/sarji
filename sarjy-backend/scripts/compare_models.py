"""Latency harness across a fixed set of models: same shape as `measure.py`
per model, plus one comparison table.

Usage:
    python scripts/compare_models.py --base-url https://sarjy.onrender.com

Edit MODELS below to change what gets tested. Each entry is a model id/alias
the backend accepts in `ChatRequest.model` (e.g. a LiteLLM alias like
`groq-oss`) and doubles as that model's label in the output.
"""

import argparse
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx

from measure import (
    DEFAULT_PROMPT,
    TIMEOUT_SECONDS,
    evaluate,
    percentile,
    render_table,
    run_once,
    valid_rows,
)

MODELS = [
    "groq-oss",
    "gemini-flash",
    "gpt-4o-mini"
]

REPORT_COLUMNS = ["llm_total_ms", "client_first_byte_ms", "client_total_ms", "total_ms"]

CHART_COLORS = ["#4a7dfc", "#fc814a", "#4afc9d", "#c44afc", "#fcec4a", "#fc4a6a"]


def run_model(client: httpx.Client, user_id: str, prompt: str, stream: bool,
              model: str, iterations: int) -> list[dict]:
    print(f"{model}: warm-up…")
    run_once(client, user_id, prompt, stream, model=model)
    rows: list[dict] = []
    for i in range(iterations):
        result = run_once(client, user_id, prompt, stream, model=model)
        failed_check = evaluate(client, user_id, prompt, result)
        row = {**result["timings"], "ok": failed_check is None}
        if failed_check is not None:
            row["failed_check"] = failed_check
        rows.append(row)
        print(f"{model} {i + 1}/{iterations}: {row}")
    return rows


def p50_table(results: dict[str, list[dict]], columns: list[str]) -> dict[str, dict[str, float | None]]:
    """p50 per model per column; None where a model has no valid values for it."""
    table: dict[str, dict[str, float | None]] = {}
    for model, rows in results.items():
        passing = valid_rows(rows)
        table[model] = {}
        for name in columns:
            values = [r[name] for r in passing if isinstance(r.get(name), (int, float))]
            table[model][name] = percentile(values, 50) if values else None
    return table


def render_comparison(prompt: str, results: dict[str, list[dict]]) -> str:
    columns = REPORT_COLUMNS
    table = p50_table(results, columns)
    lines = [
        "# Latency comparison across models",
        "",
        f"- Prompt: `{prompt}`",
        "- Values are p50 (ms) across each model's valid turns.",
        "",
        "| Model | " + " | ".join(f"`{name}`" for name in columns) + " |",
        "|---|" + "---:|" * len(columns),
    ]
    for model, values in table.items():
        cells = [str(v) if v is not None else "—" for v in values.values()]
        lines.append(f"| {model} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def render_chart_svg(columns: list[str], models: list[str],
                      table: dict[str, dict[str, float | None]]) -> str:
    """One grouped bar chart: a group per column, one bar per model in it,
    all sharing a single y-axis so every column sits side by side."""
    bar_width, bar_gap, group_gap = 28, 6, 40
    left_margin, top_margin, bottom_margin = 50, 20, 60
    chart_height = 260

    group_width = len(models) * bar_width + (len(models) - 1) * bar_gap
    width = left_margin + len(columns) * (group_width + group_gap) + group_gap
    height = top_margin + chart_height + bottom_margin

    all_values = [
        table[m][c] for c in columns for m in models if table[m][c] is not None
    ]
    max_value = max(all_values) if all_values else 1

    parts = [
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="system-ui, sans-serif" font-size="11">'
    ]
    # y-axis gridlines + labels, 4 evenly spaced steps
    for step in range(5):
        y = top_margin + chart_height - (chart_height * step / 4)
        value = max_value * step / 4
        parts.append(
            f'<line x1="{left_margin}" y1="{y:.1f}" x2="{width - group_gap}" y2="{y:.1f}" '
            'stroke="#e5e5e5" stroke-width="1"/>'
        )
        parts.append(f'<text x="{left_margin - 8}" y="{y + 3:.1f}" text-anchor="end" fill="#555">{value:.0f}</text>')

    for gi, column in enumerate(columns):
        group_x = left_margin + group_gap + gi * (group_width + group_gap)
        for mi, model in enumerate(models):
            value = table[model][column]
            bar_x = group_x + mi * (bar_width + bar_gap)
            bar_height = (value / max_value * chart_height) if max_value and value is not None else 0
            bar_y = top_margin + chart_height - bar_height
            color = CHART_COLORS[mi % len(CHART_COLORS)]
            if value is not None:
                parts.append(
                    f'<rect x="{bar_x:.1f}" y="{bar_y:.1f}" width="{bar_width}" height="{bar_height:.1f}" '
                    f'fill="{color}"><title>{model}: {value:.1f}</title></rect>'
                )
                parts.append(
                    f'<text x="{bar_x + bar_width / 2:.1f}" y="{bar_y - 4:.1f}" text-anchor="middle" '
                    f'fill="#333">{value:.0f}</text>'
                )
        parts.append(
            f'<text x="{group_x + group_width / 2:.1f}" y="{top_margin + chart_height + 18}" '
            'text-anchor="middle" fill="#1a1a1a">' + column + '</text>'
        )
    parts.append(f'<line x1="{left_margin}" y1="{top_margin + chart_height}" '
                  f'x2="{width - group_gap}" y2="{top_margin + chart_height}" stroke="#999" stroke-width="1"/>')
    parts.append("</svg>")
    return "".join(parts)


def render_html(prompt: str, results: dict[str, list[dict]]) -> str:
    """Self-contained HTML report: the p50 table, plus one grouped bar chart
    with every column side by side. No external assets, so the file opens
    straight from disk."""
    columns = REPORT_COLUMNS
    table = p50_table(results, columns)
    models = list(table.keys())

    def esc(text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    header_cells = "".join(f"<th>{esc(name)}</th>" for name in columns)
    body_rows = []
    for model in models:
        cells = "".join(
            f"<td>{table[model][name]:.1f}</td>" if table[model][name] is not None else "<td>—</td>"
            for name in columns
        )
        body_rows.append(f"<tr><th>{esc(model)}</th>{cells}</tr>")

    legend_items = "".join(
        f'<span class="legend-item"><span class="swatch" style="background:{CHART_COLORS[i % len(CHART_COLORS)]}"></span>{esc(model)}</span>'
        for i, model in enumerate(models)
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Latency comparison across models</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1a1a1a; background: #fafafa; }}
  h1 {{ font-size: 1.4rem; }}
  .meta {{ color: #555; margin-bottom: 1.5rem; }}
  table {{ border-collapse: collapse; margin-bottom: 2rem; }}
  th, td {{ border: 1px solid #ddd; padding: 0.4rem 0.8rem; text-align: right; }}
  th:first-child, td:first-child {{ text-align: left; }}
  thead th {{ background: #eee; }}
  .chart-card {{ background: #fff; border: 1px solid #ddd; border-radius: 6px; padding: 1rem; max-width: 100%; overflow-x: auto; }}
  .legend {{ margin-bottom: 0.8rem; }}
  .legend-item {{ display: inline-flex; align-items: center; margin-right: 1rem; font-size: 0.85rem; }}
  .swatch {{ display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 0.4rem; }}
</style>
</head>
<body>
  <h1>Latency comparison across models</h1>
  <p class="meta">Prompt: <code>{esc(prompt)}</code> &middot; values are p50 (ms) across each model's valid turns.</p>

  <table>
    <thead><tr><th>Model</th>{header_cells}</tr></thead>
    <tbody>{"".join(body_rows)}</tbody>
  </table>

  <div class="chart-card">
    <div class="legend">{legend_items}</div>
    {render_chart_svg(columns, models, table)}
  </div>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--out-dir", default="latency_model_eval")
    args = parser.parse_args()

    user_id = str(uuid.uuid4())
    results: dict[str, list[dict]] = {}
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=TIMEOUT_SECONDS) as client:
        for model in MODELS:
            rows = run_model(client, user_id, args.prompt, args.stream, model, args.iterations)
            results[model] = rows
            table = render_table(model, args.base_url, args.prompt, rows)
            out_path = out_dir / f"{model}.md"
            out_path.write_text(table, encoding="utf-8")
            print(f"written to {out_path}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    compare_path = out_dir / f"compare-{timestamp}.md"
    compare_path.write_text(render_comparison(args.prompt, results), encoding="utf-8")
    print()
    print(f"written to {compare_path}")

    html_path = out_dir / f"compare-{timestamp}.html"
    html_path.write_text(render_html(args.prompt, results), encoding="utf-8")
    print(f"written to {html_path}")

    failures = sum(len(rows) - len(valid_rows(rows)) for rows in results.values())
    if failures:
        print(f"{failures} turns failed validation across all models", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
