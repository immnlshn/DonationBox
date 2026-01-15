"""
VotingService - Manages the creation, activation and management of votings.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Iterable

from backend.database.repositories.vote_repository import VoteRepository
from backend.models import Vote, Category


class VotingService:
    """Service for managing votings (polls)."""

    def __init__(self, vote_repo: VoteRepository):
        """
        Initialize VotingService with repository.

        Args:
            vote_repo: VoteRepository instance
        """
        self.vote_repo = vote_repo

    async def create_vote(
        self,
        question: str,
        start_time: datetime,
        end_time: datetime,
        category_ids: Optional[Iterable[int]] = None,
        is_active: bool = False,
    ) -> Vote:
        """
        Creates a new voting with the given parameters.

        Args:
            question: The question/description of the voting
            start_time: Start time of the voting
            end_time: End time of the voting
            category_ids: Optional - List of category IDs for this voting
            is_active: Whether the voting should be active immediately

        Returns:
            The created Vote object
        """
        return await self.vote_repo.create(
            question=question,
            start_time=start_time,
            end_time=end_time,
            category_ids=category_ids,
            is_active=is_active,
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
        Returns the currently active voting.

        Returns:
            The active Vote object or None if none is active
        """
        return await self.vote_repo.get_active()

    async def set_active_vote(self, vote_id: int) -> None:
        """
        Sets a specific voting as active and deactivates all others.

        Args:
            vote_id: The ID of the voting to activate

        Raises:
            NoResultFound: If no voting with the given ID exists
        """
        await self.vote_repo.set_active(vote_id)

    async def list_votes(self, limit: int = 100, offset: int = 0) -> list[Vote]:
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

    async def add_categories_to_vote(self, vote_id: int, category_ids: Iterable[int]) -> Vote:
        """
        Adds additional categories to a voting.

        Args:
            vote_id: The ID of the voting
            category_ids: List of category IDs to add

        Returns:
            The updated Vote object

        Raises:
            NoResultFound: If no voting with the given ID exists
        """
        return await self.vote_repo.add_categories(vote_id, category_ids)

    async def remove_categories_from_vote(self, vote_id: int, category_ids: Iterable[int]) -> Vote:
        """
        Removes categories from a voting.

        Args:
            vote_id: The ID of the voting
            category_ids: List of category IDs to remove

        Returns:
            The updated Vote object

        Raises:
            NoResultFound: If no voting with the given ID exists
        """
        return await self.vote_repo.remove_categories(vote_id, category_ids)

    async def is_vote_running(self, vote_id: int) -> bool:
        """
        Checks if a voting is currently running (based on start_time and end_time).

        Args:
            vote_id: The ID of the voting

        Returns:
            True if the voting is running, False otherwise
        """
        vote = await self.get_vote_by_id(vote_id)
        if not vote:
            return False
        now = datetime.now(vote.start_time.tzinfo or None)
        return vote.start_time <= now <= vote.end_time

    async def get_vote_categories(self, vote_id: int) -> list[Category]:
        """
        Returns all categories of a voting.

        Args:
            vote_id: The ID of the voting

        Returns:
            List of Category objects or empty list if voting does not exist
        """
        vote = await self.get_vote_by_id(vote_id)
        if not vote:
            return []
        return vote.categories

