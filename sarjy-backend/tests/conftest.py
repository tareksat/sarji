import os

# Settings are read at import time and now refuse to construct without a model
# credential, so these have to be in place before anything under `app` loads.
os.environ.setdefault("LLM_MODEL", "test-model")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.db import Base  # noqa: E402
from app.models import Session as SessionModel  # noqa: E402
from app.models import User  # noqa: E402


@pytest.fixture
def session_factory():
    """An in-memory database shared by every Session the test opens.

    StaticPool keeps one connection, which is what makes `:memory:` visible to
    the second Session the streaming path opens for its history read.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    # SQLite ignores foreign keys unless asked; Postgres does not. Without this
    # the tests cannot see an insert that lands before the row it references.
    @event.listens_for(engine, "connect")
    def _enforce_foreign_keys(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    engine.dispose()


@pytest.fixture
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


def make_user(db, user_id):
    db.add(User(id=user_id))
    db.commit()


def make_session(db, session_id, user_id, title="Existing chat"):
    db.add(SessionModel(id=session_id, user_id=user_id, title=title))
    db.commit()
