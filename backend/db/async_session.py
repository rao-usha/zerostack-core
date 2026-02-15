"""
Async database session management for SQLAlchemy.

Provides async session maker for async database operations.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from core.config import settings


def _get_async_url(sync_url: str) -> str:
    """Convert sync database URL to async URL."""
    # Handle different URL formats
    if 'asyncpg' in sync_url:
        return sync_url
    elif 'psycopg' in sync_url:
        return sync_url.replace('postgresql+psycopg', 'postgresql+asyncpg')
    elif 'postgresql://' in sync_url:
        return sync_url.replace('postgresql://', 'postgresql+asyncpg://')
    else:
        return sync_url


# Create async engine
_async_url = _get_async_url(settings.database_url)
_async_engine = create_async_engine(_async_url, echo=False)

# Create async session maker
async_session_maker = async_sessionmaker(
    _async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session as context manager.

    Usage:
        async with get_async_session() as session:
            result = await session.execute(query)

    Yields:
        AsyncSession: Async SQLAlchemy session
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
