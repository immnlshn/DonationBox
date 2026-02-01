"""
CategoryService - Service for managing categories.
"""
from __future__ import annotations

import logging
from typing import Optional

from backend.repositories import CategoryRepository
from backend.models import Category

logger = logging.getLogger(__name__)


class CategoryService:
    """Service for managing categories."""

    def __init__(self, category_repo: CategoryRepository):
        """
        Initialize CategoryService with repository.

        Args:
            category_repo: CategoryRepository instance
        """
        self.category_repo = category_repo

    async def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """
        Get a category by its ID.

        Args:
            category_id: ID of the category to retrieve

        Returns:
            Category instance or None if not found
        """
        return await self.category_repo.get_by_id(category_id)

    async def get_category_name(self, category_id: int) -> Optional[str]:
        """
        Get the name of a category by its ID.

        Args:
            category_id: ID of the category

        Returns:
            Category name or None if not found
        """
        category = await self.get_category_by_id(category_id)
        return category.name if category else None

    async def get_or_create_category(self, name: str) -> Category:
        """
        Get or create a category by name.

        Args:
            name: Name of the category

        Returns:
            Category instance
        """
        return await self.category_repo.get_or_create(name.strip())

    async def list_all_categories(self) -> list[Category]:
        """
        Get all categories.

        Returns:
            List of all categories
        """
        return await self.category_repo.list_all()
