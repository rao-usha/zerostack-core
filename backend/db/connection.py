"""
Database connection management for SQLAlchemy.

Provides database connection dependency for FastAPI routers.
"""

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection
from typing import Generator
from core.config import settings

# Create SQLAlchemy engine
_engine = create_engine(settings.database_url, echo=settings.debug)


def get_db_connection() -> Generator[Connection, None, None]:
    """
    Get database connection as FastAPI dependency.
    
    Usage with FastAPI Depends:
        @router.get("/")
        def endpoint(conn: Connection = Depends(get_db_connection)):
            ...
    
    Yields:
        Connection: SQLAlchemy database connection
    """
    with _engine.connect() as conn:
        yield conn
        conn.commit()
