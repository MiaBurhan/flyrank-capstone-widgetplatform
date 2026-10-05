"""SQLAlchemy engine, session factory and table creation."""
import time
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(retries: int = 15, delay: float = 2.0) -> None:
    """Create tables, waiting for the database to come up if needed."""
    from app import models  # noqa: F401  (registers tables on Base)

    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(engine)
            return
        except OperationalError:
            if attempt == retries:
                raise
            time.sleep(delay)
