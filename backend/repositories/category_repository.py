"""
Category Repository - Handles all database operations for Category entities.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository
from backend.models import Category


class CategoryRepository(BaseRepository[Category]):
    """Repository for Category entity operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Category)

    async def create(self, name: str) -> Category:
        """
        Create a new category.

        Args:
            name: Category name

        Returns:
            Created Category entity
        """
        category = Category(name=name)
        self.db.add(category)
        await self.commit()
        await self.refresh(category)
        return category

    async def get_by_name(self, name: str) -> Optional[Category]:
        """
        Get category by name.

        Args:
            name: Category name

        Returns:
            Category or None if not found
        """
        stmt = select(Category).where(Category.name == name)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_all(self) -> list[Category]:
        """
        List all categories.

        Returns:
            List of Category entities
        """
        stmt = select(Category).order_by(Category.id.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, category_id: int) -> bool:
        """
        Delete a category.

        Note: May fail if donations reference it and FK is RESTRICT.

        Args:
            category_id: Category ID

        Returns:
            True if deleted, False if not found
        """
        category = await self.get_by_id(category_id)
        if not category:
            return False
        await self.db.delete(category)
        await self.commit()
        return True

