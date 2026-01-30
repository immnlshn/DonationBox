from typing import Generic, TypeVar, Type, Optional
from sqlalchemy.ext.asyncio import AsyncSession


T = TypeVar('T')


class BaseRepository(Generic[T]):
  """
  Base repository class with common CRUD operations.

  Type parameter T should be a SQLAlchemy model class.
  """

  def __init__(self, db: AsyncSession, model: Type[T]):
    """
    Initialize repository with async database session and model class.

    Args:
        db: SQLAlchemy AsyncSession
        model: SQLAlchemy model class
    """
    self.db = db
    self.model = model

  async def get_by_id(self, id: int) -> Optional[T]:
    """
    Get entity by ID.

    Args:
        id: Entity ID

    Returns:
        Entity or None if not found
    """
    return await self.db.get(self.model, id)

  async def commit(self) -> None:
    """Commit current transaction."""
    await self.db.commit()

  async def rollback(self) -> None:
    """Rollback current transaction."""
    await self.db.rollback()

  async def flush(self) -> None:
    """Flush pending changes without committing."""
    await self.db.flush()

  async def refresh(self, instance: T) -> None:
    """
    Refresh entity from database.

    Args:
        instance: Entity to refresh
    """
    await self.db.refresh(instance)