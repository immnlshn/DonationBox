from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import event

from backend.settings import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# Convert sqlite:/// to sqlite+aiosqlite:/// for async support
async_db_url = settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://") if _is_sqlite else settings.DATABASE_URL

# Async Engine configuration
engine = create_async_engine(
    async_db_url,
    echo=False,
    pool_pre_ping=True
)

# SQLite: Enable foreign keys (async version)
if _is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI Dependency for Async Database Sessions.

    Creates a new async session for each request and closes it automatically.
    Usage in routes:
        @router.get("/")
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
