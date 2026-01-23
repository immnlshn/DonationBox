"""
VotingService - Manages the creation, activation and management of votings.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Iterable, Protocol

from backend.repositories import VoteRepository, CategoryRepository
from backend.models import Vote


class CategoryInput(Protocol):
    """Protocol for category input - any object with a 'name' attribute."""
    name: str


class VotingService:
    """Service for managing votings (polls)."""

    def __init__(self, vote_repo: VoteRepository, category_repo: CategoryRepository):
        """
        Initialize VotingService with repositories.

        Args:
            vote_repo: VoteRepository instance
            category_repo: CategoryRepository instance
        """
        self.vote_repo = vote_repo
        self.category_repo = category_repo

    async def _resolve_categories(self, category_inputs: Iterable[CategoryInput]) -> list[int]:
        """
        Resolves category names to category IDs.
        Uses get_or_create to handle race conditions safely.

        Args:
            category_inputs: List of CategoryInput objects

        Returns:
            List of category IDs
        """
        category_ids = []
        for cat_input in category_inputs:
            name = cat_input.name.strip()

            # Get or create category atomically
            category = await self.category_repo.get_or_create(name)
            category_ids.append(category.id)
        return category_ids

    async def create_vote(
        self,
        question: str,
        start_time: datetime,
        end_time: datetime,
        categories: Iterable[CategoryInput],
    ) -> Vote:
        """
        Creates a new voting with the given parameters.

        The vote is automatically active based on start_time and end_time.

        Args:
            question: The question/description of the voting
            start_time: Start time of the voting
            end_time: End time of the voting
            categories: List of CategoryInput (name only, backend resolves/creates)

        Returns:
            The created Vote object
        """
        category_ids = await self._resolve_categories(categories)
        return await self.vote_repo.create(
            question=question,
            start_time=start_time,
            end_time=end_time,
            category_ids=category_ids,
        )

    async def update_vote(
        self,
        vote_id: int,
        question: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        categories: Optional[Iterable[CategoryInput]] = None,
    ) -> Vote:
        """
        Updates a voting with the given parameters.

        Args:
            vote_id: The ID of the voting to update
            question: Optional - New question text
            start_time: Optional - New start time
            end_time: Optional - New end time
            categories: Optional - New list of categories (replaces existing)

        Returns:
            The updated Vote object

        Raises:
            NoResultFound: If no voting with the given ID exists
        """
        category_ids = None
        if categories is not None:
            category_ids = await self._resolve_categories(categories)

        return await self.vote_repo.update(
            vote_id=vote_id,
            question=question,
            start_time=start_time,
            end_time=end_time,
            category_ids=category_ids,
        )

    async def get_vote_by_id(self, vote_id: int) -> Optional[Vote]:
        """
        Returns a voting by ID.

        Args:
            vote_id: The ID of the voting to find

        Returns:
            The Vote object or None if not found
        """
        return await self.vote_repo.get_by_id(vote_id)

    async def get_active_vote(self) -> Optional[Vote]:
        """
        Returns the currently active voting based on start_time and end_time.

        A vote is active if current time is between start_time and end_time.

        Returns:
            The active Vote object or None if none is active
        """
        return await self.vote_repo.get_active_by_time()

    async def list_all_votes(self, limit: int = 100, offset: int = 0) -> list[Vote]:
        """
        Returns a list of all votings (paginated).

        Args:
            limit: Maximum number of votings to return
            offset: Number of votings to skip

        Returns:
            List of Vote objects
        """
        return await self.vote_repo.list_all(limit=limit, offset=offset)

    async def delete_vote(self, vote_id: int) -> bool:
        """
        Deletes a voting. All associated donations will also be deleted (CASCADE).

        Args:
            vote_id: The ID of the voting to delete

        Returns:
            True if deleted, False if not found
        """
        return await self.vote_repo.delete(vote_id)


