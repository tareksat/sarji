"""Add the composite indexes to a database that already has its tables.

`Base.metadata.create_all` at startup creates missing *tables*; it does not add
an index to a table that already exists. There is no migration tool in this
project, so this script is the one-off that brings an existing deployment in
line with the models.

Safe to run repeatedly, and safe to run against a database that was created
after the models gained these indexes -- every statement is IF NOT EXISTS.

The unique index on memories (user_id, content) is preceded by a delete of the
duplicate rows it would otherwise refuse: `save_memory` used to dedupe with a
check-then-insert only, and its calls run in parallel, so an existing database
can hold the same fact twice. The oldest copy is the one kept.

    python scripts/create_indexes.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402

from app.core.db import engine  # noqa: E402

STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS ix_messages_session_created "
    "ON messages (session_id, created_at)",
    "CREATE INDEX IF NOT EXISTS ix_sessions_user_updated "
    "ON sessions (user_id, updated_at)",
    "CREATE INDEX IF NOT EXISTS ix_memories_user_created "
    "ON memories (user_id, created_at)",
    "CREATE INDEX IF NOT EXISTS ix_memories_source_session "
    "ON memories (source_session_id)",
    "DELETE FROM memories AS later USING memories AS earlier "
    "WHERE later.user_id = earlier.user_id AND later.content = earlier.content "
    "AND (later.created_at > earlier.created_at "
    "OR (later.created_at = earlier.created_at AND later.id > earlier.id))",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_memories_user_content "
    "ON memories (user_id, content)",
]


def main() -> None:
    with engine.begin() as conn:
        for statement in STATEMENTS:
            print(statement)
            conn.execute(text(statement))
    print(f"Done: {len(STATEMENTS)} statements applied.")


if __name__ == "__main__":
    main()
