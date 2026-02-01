"""
Donation Repository - Handles all database operations for Donation entities.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository
from backend.models import Donation, Category

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


class DonationRepository(BaseRepository[Donation]):
    """Repository for Donation entity operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(db, Donation)

    async def create(
        self,
        vote_id: int,
        category_id: int,
        amount_cents: int,
        timestamp: Optional[datetime] = None,
    ) -> Donation:
        """
        Create a new donation.

        Args:
            vote_id: Vote ID
            category_id: Category ID
            amount_cents: Donation amount in cents
            timestamp: Optional donation timestamp (defaults to now)

        Returns:
            Created Donation entity
        """
        donation = Donation(
            vote_id=vote_id,
            category_id=category_id,
            amount=amount_cents,
            timestamp=timestamp or utcnow(),
        )
        self.db.add(donation)
        await self.commit()
        await self.refresh(donation)
        return donation

    async def list_for_vote(self, vote_id: int) -> list[Donation]:
        """
        List all donations for a specific vote.

        Args:
            vote_id: Vote ID

        Returns:
            List of Donation entities
        """
        stmt = select(Donation).where(Donation.vote_id == vote_id).order_by(Donation.id.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_totals_for_vote(self, vote_id: int) -> dict:
        """
        Calculate donation totals for a vote.

        Returns totals for ALL categories currently in the vote, ordered by position.
        Categories without donations show 0. This ensures UI always shows all options.

        Args:
            vote_id: Vote ID

        Returns:
            Dictionary with:
                - vote_id: Vote ID
                - total_amount_cents: Total amount in cents (only current categories)
                - by_category: List of dicts with category breakdown (all categories, ordered by position)
        """
        # Import here to avoid circular dependency
        from backend.models.associations import vote_category

        # Get current categories for this vote with their positions
        vote_cat_stmt = (
            select(
                vote_category.c.category_id,
                vote_category.c.position,
                Category.name
            )
            .join(Category, Category.id == vote_category.c.category_id)
            .where(vote_category.c.vote_id == vote_id)
            .order_by(vote_category.c.position.asc())
        )
        result = await self.db.execute(vote_cat_stmt)
        vote_categories = result.all()

        if not vote_categories:
            return {
                "vote_id": vote_id,
                "total_amount_cents": 0,
                "by_category": []
            }

        current_category_ids = [cat.category_id for cat in vote_categories]

        # Calculate total amount only for current categories
        total_stmt = select(
            func.coalesce(func.sum(Donation.amount), 0)
        ).where(
            Donation.vote_id == vote_id,
            Donation.category_id.in_(current_category_ids)
        )
        result = await self.db.execute(total_stmt)
        total_amount = int(result.scalar_one())

        # Get donation sums per category
        donation_sums_stmt = (
            select(
                Donation.category_id,
                func.coalesce(func.sum(Donation.amount), 0).label("amount_cents"),
                func.count(Donation.id).label("count"),
            )
            .where(
                Donation.vote_id == vote_id,
                Donation.category_id.in_(current_category_ids)
            )
            .group_by(Donation.category_id)
        )
        result = await self.db.execute(donation_sums_stmt)
        donation_sums = {row.category_id: (row.amount_cents, row.count) for row in result.all()}

        # Build result: all categories ordered by position, with donation data or zeros
        by_category = []
        for cat in vote_categories:
            amount_cents, count = donation_sums.get(cat.category_id, (0, 0))
            by_category.append({
                "category_id": int(cat.category_id),
                "category_name": str(cat.name),
                "amount_cents": int(amount_cents),
                "count": int(count),
            })

        return {
            "vote_id": vote_id,
            "total_amount_cents": total_amount,
            "by_category": by_category
        }

    async def reassign_categories_for_vote(
        self,
        vote_id: int,
        mapping: dict[int, int]
    ) -> int:
        """
        Reassign donations from old categories to new categories for a vote.

        This method updates donations in bulk, changing their category_id
        based on the provided mapping. All updates happen in the current transaction.

        Args:
            vote_id: Vote ID to update donations for
            mapping: Dictionary mapping old_category_id -> new_category_id

        Returns:
            Total number of donation rows updated
        """
        if not mapping:
            return 0

        total_updated = 0

        # Execute one UPDATE per mapping entry for clarity and control
        for old_category_id, new_category_id in mapping.items():
            stmt = (
                update(Donation)
                .where(Donation.vote_id == vote_id)
                .where(Donation.category_id == old_category_id)
                .values(category_id=new_category_id)
            )
            result = await self.db.execute(stmt)
            rows_updated = result.rowcount
            total_updated += rows_updated

            if rows_updated > 0:
                logger.info(
                    f"Reassigned {rows_updated} donations from category {old_category_id} "
                    f"to category {new_category_id} for vote {vote_id}"
                )

        # Flush changes but don't commit - caller controls transaction
        await self.flush()

        return total_updated


