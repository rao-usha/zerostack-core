"""
Database session management for SQLModel.

Provides database engine and session factory for chat and other features
that use the main Postgres database.
"""

from sqlmodel import Session, create_engine
from contextlib import contextmanager
from typing import Generator
from core.config import settings

# Create engine
engine = create_engine(settings.database_url, echo=settings.debug)


def get_session() -> Generator[Session, None, None]:
    """
    Get database session.
    
    Usage with FastAPI Depends:
        @router.get("/")
        async def endpoint(session: Session = Depends(get_session)):
            ...
    """
    with Session(engine) as session:
        yield session


@contextmanager
def get_session_context():
    """
    Get database session as context manager.
    
    Usage:
        with get_session_context() as session:
            ...
    """
    with Session(engine) as session:
        yield session

