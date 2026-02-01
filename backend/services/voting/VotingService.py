"""
VotingService - Manages the creation, activation and management of votings.
"""
from __future__ import annotations
import logging

from datetime import datetime
from typing import Optional, Iterable, Protocol

from backend.repositories import VoteRepository, CategoryRepository, DonationRepository
from backend.models import Vote

logger = logging.getLogger(__name__)

class CategoryInput(Protocol):
    """Protocol for category input - any object with a 'name' attribute."""
    name: str


class VotingService:
    """Service for managing votings (polls)."""

    def __init__(
        self,
        vote_repo: VoteRepository,
        category_repo: CategoryRepository,
        donation_repo: DonationRepository
    ):
        """
        Initialize VotingService with repositories.

        Args:
            vote_repo: VoteRepository instance
            category_repo: CategoryRepository instance
            donation_repo: DonationRepository instance
        """
        self.vote_repo = vote_repo
        self.category_repo = category_repo
        self.donation_repo = donation_repo

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

    def _build_category_mapping_by_position(
        self,
        old_categories: list,
        new_category_ids_ordered: list[int],
    ) -> dict[int, int]:
        """
        Build mapping from old category IDs to new category IDs based on position.

        Simple strategy: Map old category at position i to new category at position i.
        - If old category ID == new category ID at same position -> no mapping needed
        - Otherwise, create mapping entry

        This preserves the user's intent: position 0 stays position 0, etc.

        Args:
            old_categories: List of old Category objects (ordered by position)
            new_category_ids_ordered: List of new category IDs in order

        Returns:
            Dictionary mapping old_category_id -> new_category_id
            Only contains entries where the ID changed at that position
        """
        mapping = {}

        # Map by position: old[i] -> new[i]
        for i, old_cat in enumerate(old_categories):
            # Handle case where new list is shorter (extra old categories)
            if i < len(new_category_ids_ordered):
                new_cat_id = new_category_ids_ordered[i]
            else:
                # If old list is longer, map remaining to last new category
                new_cat_id = new_category_ids_ordered[-1]

            # Only add mapping if ID actually changed
            if old_cat.id != new_cat_id:
                mapping[old_cat.id] = new_cat_id
                logger.info(
                    f"Position {i}: Map old category '{old_cat.name}' (id={old_cat.id}) "
                    f"-> new category id={new_cat_id}"
                )

        if not mapping:
            logger.info("No category ID changes at any position, no migration needed")

        return mapping

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
        vote = await self.vote_repo.create(
            question=question,
            start_time=start_time,
            end_time=end_time,
            category_ids=category_ids,
        )
        # vote_repo.create already commits
        return vote

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

        When categories are updated, existing donations are automatically migrated
        to ensure they reference valid categories in the new set.

        Migration Strategy (Position-based):
        - Old category at position i is mapped to new category at position i
        - This preserves the user's intent: if they change position 0 from "A" to "B",
          all donations for position 0 should go to "B"
        - If the new list is shorter, extra old categories map to the last new category

        Category handling:
        - Categories are reusable entities identified by unique names
        - Updating categories changes vote-category associations
        - Old categories remain in DB if they have donations (FK RESTRICT)

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
            ValueError: If new category set is empty (would orphan donations)
        """
        # If categories are being updated, handle migration in transaction
        if categories is not None:
            return await self._update_vote_with_category_migration(
                vote_id=vote_id,
                question=question,
                start_time=start_time,
                end_time=end_time,
                categories=categories,
            )

        # Simple update without category changes
        category_ids = None
        vote = await self.vote_repo.update(
            vote_id=vote_id,
            question=question,
            start_time=start_time,
            end_time=end_time,
            category_ids=category_ids,
        )
        await self.vote_repo.commit()
        return vote

    async def _update_vote_with_category_migration(
        self,
        vote_id: int,
        question: Optional[str],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        categories: Iterable[CategoryInput],
    ) -> Vote:
        """
        Update vote with category migration for donations.

        This method ensures that all operations happen in a single transaction:
        1. Load existing vote with current categories
        2. Resolve new categories
        3. Build migration mapping
        4. Migrate donations
        5. Update vote

        Args:
            vote_id: Vote ID
            question: Optional new question
            start_time: Optional new start time
            end_time: Optional new end time
            categories: New categories

        Returns:
            Updated Vote object

        Raises:
            ValueError: If new category set is empty
        """
        # Step 1: Load existing vote with categories
        old_vote = await self.vote_repo.get_by_id(vote_id)
        if not old_vote:
            from sqlalchemy.exc import NoResultFound
            raise NoResultFound(f"Vote id={vote_id} not found")

        old_categories = list(old_vote.categories)  # Make a copy before update

        # Step 2: Resolve new categories (get_or_create)
        new_category_ids = await self._resolve_categories(categories)

        if not new_category_ids:
            raise ValueError("Cannot update vote with empty category set - would orphan donations")

        # Step 3: Build migration mapping based on position
        # Simple: old position i maps to new position i
        mapping = self._build_category_mapping_by_position(
            old_categories=old_categories,
            new_category_ids_ordered=new_category_ids,
        )

        # Step 4: Migrate donations if needed
        if mapping:
            donations_updated = await self.donation_repo.reassign_categories_for_vote(
                vote_id=vote_id,
                mapping=mapping,
            )
            logger.info(
                f"Vote {vote_id}: Migrated {donations_updated} donations. "
                f"Mapping: {mapping}"
            )
        else:
            logger.info(f"Vote {vote_id}: No donation migration needed (all categories retained)")

        # Step 5: Update vote (including categories)
        updated_vote = await self.vote_repo.update(
            vote_id=vote_id,
            question=question,
            start_time=start_time,
            end_time=end_time,
            category_ids=new_category_ids,
        )

        # Commit the entire transaction
        await self.vote_repo.commit()

        return updated_vote

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
        Deletes a voting with all associated data.

        What gets deleted (CASCADE):
        - All donations for this vote
        - All vote-category associations (M:N entries)

        What stays:
        - Categories themselves (may be reused by other votes)
        - Categories with donations cannot be deleted anyway (FK RESTRICT)

        Args:
            vote_id: The ID of the voting to delete

        Returns:
            True if deleted, False if not found
        """
        return await self.vote_repo.delete(vote_id)


