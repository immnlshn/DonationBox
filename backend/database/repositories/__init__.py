"""
Base Repository class providing common database operations.
"""
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Base repository class with common CRUD operations.

    Type parameter T should be a SQLAlchemy model class.
    """

    def __init__(self, db: Session, model: Type[T]):
        """
        Initialize repository with database session and model class.

        Args:
            db: SQLAlchemy session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model

    def get_by_id(self, id: int) -> Optional[T]:
        """
        Get entity by ID.

        Args:
            id: Entity ID

        Returns:
            Entity or None if not found
        """
        return self.db.get(self.model, id)

    def commit(self) -> None:
        """Commit current transaction."""
        self.db.commit()

    def rollback(self) -> None:
        """Rollback current transaction."""
        self.db.rollback()

    def flush(self) -> None:
        """Flush pending changes without committing."""
        self.db.flush()

    def refresh(self, instance: T) -> None:
        """
        Refresh entity from database.

        Args:
            instance: Entity to refresh
        """
        self.db.refresh(instance)

