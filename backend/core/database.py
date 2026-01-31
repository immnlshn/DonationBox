"""
Database session and engine configuration.

Provides setup_database() function to create engine and sessionmaker.
Called by AppContainer during initialization.
"""

import logging
from typing import Tuple

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker

from .config import settings

logger = logging.getLogger(__name__)


def setup_database() -> Tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """
    Setup database engine and session factory.

    Called by AppContainer during initialization.

    Returns:
        Tuple of (engine, sessionmaker)
    """
    # Check if SQLite is being used
    is_sqlite = settings.DATABASE_URL.startswith("sqlite")

    # Convert sqlite:/// to sqlite+aiosqlite:/// for async support
    async_db_url = (
        settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
        if is_sqlite
        else settings.DATABASE_URL
    )

    # Create async engine
    engine = create_async_engine(
        async_db_url,
        echo=settings.DEBUG,  # Enable SQL echo in debug mode
        pool_pre_ping=True,
    )

    # Enable foreign keys for SQLite
    if is_sqlite:
        @event.listens_for(engine.sync_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _):
            """Enable foreign key constraints for SQLite."""
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    # Create session factory
    sessionmaker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    logger.info(f"Database configured: {async_db_url}")

    return engine, sessionmaker
