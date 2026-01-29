"""Database session management."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from wf_catalogue_service.core.settings import current_settings

engine = create_async_engine(current_settings().db.url)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Yield database session for dependency injection."""
    async with session_factory() as session:
        yield session
