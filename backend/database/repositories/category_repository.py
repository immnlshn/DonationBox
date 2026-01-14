"""
Category Repository - Handles all database operations for Category entities.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.repositories import BaseRepository
from backend.models import Category


class CategoryRepository(BaseRepository[Category]):
    """Repository for Category entity operations."""

    def __init__(self, db: Session):
        super().__init__(db, Category)

    def create(self, name: str) -> Category:
        """
        Create a new category.

        Args:
            name: Category name

        Returns:
            Created Category entity
        """
        category = Category(name=name)
        self.db.add(category)
        self.commit()
        self.refresh(category)
        return category

    def get_by_name(self, name: str) -> Optional[Category]:
        """
        Get category by name.

        Args:
            name: Category name

        Returns:
            Category or None if not found
        """
        stmt = select(Category).where(Category.name == name)
        return self.db.execute(stmt).scalars().first()

    def list_all(self) -> list[Category]:
        """
        List all categories.

        Returns:
            List of Category entities
        """
        stmt = select(Category).order_by(Category.id.asc())
        return list(self.db.execute(stmt).scalars().all())

    def delete(self, category_id: int) -> bool:
        """
        Delete a category.

        Note: May fail if donations reference it and FK is RESTRICT.

        Args:
            category_id: Category ID

        Returns:
            True if deleted, False if not found
        """
        category = self.get_by_id(category_id)
        if not category:
            return False
        self.db.delete(category)
        self.commit()
        return True

