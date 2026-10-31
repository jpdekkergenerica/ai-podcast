import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/app.db")

# SQLite heeft check_same_thread=False nodig voor FastAPI
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401
    if DATABASE_URL.startswith("sqlite"):
        Path = __import__("pathlib").Path
        Path("data").mkdir(exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _add_missing_columns()


def _add_missing_columns() -> None:
    """create_all voegt geen kolommen toe aan bestaande tabellen; doe dat hier voor nieuwe velden."""
    from sqlalchemy import inspect, text
    wanted = {
        "shows": [("schedule", "JSON"), ("style", "VARCHAR(16) DEFAULT 'informeel'"), ("cover_file", "VARCHAR(200)")],
        "users": [("notify_new", "BOOLEAN DEFAULT TRUE"), ("notify_failed", "BOOLEAN DEFAULT TRUE")],
        "episodes": [("period_start", "VARCHAR(40) DEFAULT ''"), ("period_end", "VARCHAR(40) DEFAULT ''")],
        "jobs": [("scheduled_for", "VARCHAR(10)"), ("attempts", "INTEGER DEFAULT 0"), ("run_after", "TIMESTAMP")],
    }
    insp = inspect(engine)
    with engine.begin() as conn:
        for table, cols in wanted.items():
            have = {c["name"] for c in insp.get_columns(table)}
            for name, kind in cols:
                if name not in have:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {kind}"))
