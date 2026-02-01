"""
Category Repository - Handles all database operations for Category entities.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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

    async def get_or_create(self, name: str) -> Category:
        """
        Get existing category by name or create it if it doesn't exist.

        This method handles race conditions by catching IntegrityError
        (unique constraint violation) and retrying the get operation.

        Args:
            name: Category name

        Returns:
            Category entity (existing or newly created)
        """
        # First, try to get existing category
        existing = await self.get_by_name(name)
        if existing:
            return existing

        # Try to create new category
        try:
            category = Category(name=name)
            self.db.add(category)
            await self.commit()
            await self.refresh(category)
            return category
        except IntegrityError:
            # Another transaction created this category between our check and insert
            # Rollback and fetch the existing one
            await self.db.rollback()
            existing = await self.get_by_name(name)
            if existing:
                return existing
            # If still not found, something else went wrong, re-raise
            raise

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

    async def is_orphaned(self, category_id: int) -> bool:
        """
        Check if a category is orphaned (not used by any vote or donation).

        Args:
            category_id: Category ID

        Returns:
            True if category has no votes and no donations, False otherwise
        """
        from sqlalchemy import func
        from sqlalchemy.orm import selectinload

        # Load category with relationships
        stmt = select(Category).where(Category.id == category_id).options(
            selectinload(Category.votes),
            selectinload(Category.donations)
        )
        result = await self.db.execute(stmt)
        category = result.scalars().first()

        if not category:
            return False

        # Check if category has any votes or donations
        has_votes = len(category.votes) > 0
        has_donations = len(category.donations) > 0

        return not has_votes and not has_donations

    async def delete_orphaned_categories(self, category_ids: list[int]) -> int:
        """
        Delete categories that are orphaned (no votes, no donations).

        Args:
            category_ids: List of category IDs to check and potentially delete

        Returns:
            Number of categories deleted
        """
        deleted_count = 0
        for category_id in category_ids:
            # Expire all cached objects to ensure fresh data from DB
            self.db.expire_all()

            if await self.is_orphaned(category_id):
                if await self.delete(category_id):
                    deleted_count += 1
        return deleted_count
