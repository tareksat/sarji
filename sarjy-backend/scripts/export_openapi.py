"""Write the OpenAPI schema to docs/openapi.json.

The live spec is always at /openapi.json with Swagger UI at /docs, but that
needs the server running. This checks a copy into the repo so the API can be
read on GitHub. Re-run it whenever an endpoint or schema changes:

    python scripts/export_openapi.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402

OUT = ROOT.parent / "docs" / "openapi.json"


def main() -> None:
    OUT.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
    paths = sum(len(ops) for ops in app.openapi()["paths"].values())
    print(f"wrote {OUT.relative_to(ROOT.parent)} ({paths} operations)")


if __name__ == "__main__":
    main()
