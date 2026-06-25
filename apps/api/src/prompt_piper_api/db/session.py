"""SQLModel engine and session factory with SQLite/PostgreSQL support."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from prompt_piper_api.config import Settings, get_settings

_engine: Engine | None = None


def get_engine(settings: Settings | None = None) -> Engine:
    """Return a cached SQLAlchemy engine configured for the active database."""
    global _engine
    if _engine is not None:
        return _engine

    settings = settings or get_settings()
    connect_args: dict[str, object] = {}
    if settings.is_sqlite:
        connect_args["check_same_thread"] = False

    _engine = create_engine(
        settings.database_url,
        echo=settings.app_debug,
        connect_args=connect_args,
    )
    return _engine


def init_db(settings: Settings | None = None) -> None:
    """Create database tables. pgvector extensions are applied separately for PostgreSQL."""
    engine = get_engine(settings)
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session(settings: Settings | None = None) -> Generator[Session, None, None]:
    """Yield a database session bound to the configured engine."""
    with Session(get_engine(settings)) as session:
        yield session
