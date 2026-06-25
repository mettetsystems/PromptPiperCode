from collections.abc import Generator
from typing import Any

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from prompt_piper_api.config import get_settings
from prompt_piper_api.db.similarity_models import SimilarityDocumentRow  # noqa: F401


def _make_engine() -> Engine:
    settings = get_settings()
    connect_args: dict[str, Any] = {}
    engine_kwargs: dict[str, Any] = {"echo": False}

    if settings.is_sqlite:
        connect_args["check_same_thread"] = False
        if settings.database_url == "sqlite://":
            engine_kwargs["poolclass"] = StaticPool

    return create_engine(settings.database_url, connect_args=connect_args, **engine_kwargs)


engine = _make_engine()


def init_db() -> None:
    """Create tables for local development. Migrations will replace this later."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
