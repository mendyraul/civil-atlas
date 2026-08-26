from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Yield a transaction and always close its connection."""
    with Session(engine) as session:
        with session.begin():
            yield session
