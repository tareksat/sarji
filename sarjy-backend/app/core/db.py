from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

# pool_pre_ping: the pool otherwise hands out connections that died while idle --
# Postgres restarted, or a managed provider culled the socket -- and the first
# query on one fails with AdminShutdown instead of reconnecting. The ping is one
# round-trip on checkout, and a dead connection is discarded and replaced.
engine = create_engine(
    settings.database_url,
    future=True,
    pool_pre_ping=True,
    connect_args={"connect_timeout": settings.db_connect_timeout_seconds},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
