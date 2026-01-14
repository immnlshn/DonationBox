"""
Donation Repository - Handles all database operations for Donation entities.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.database.repositories import BaseRepository
from backend.models import Donation, Category


def utcnow() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


class DonationRepository(BaseRepository[Donation]):
    """Repository for Donation entity operations."""

    def __init__(self, db: Session):
        super().__init__(db, Donation)

    def create(
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
        self.commit()
        self.refresh(donation)
        return donation

    def list_for_vote(self, vote_id: int) -> list[Donation]:
        """
        List all donations for a specific vote.

        Args:
            vote_id: Vote ID

        Returns:
            List of Donation entities
        """
        stmt = select(Donation).where(Donation.vote_id == vote_id).order_by(Donation.id.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_totals_for_vote(self, vote_id: int) -> dict:
        """
        Calculate donation totals for a vote.

        Args:
            vote_id: Vote ID

        Returns:
            Dictionary with:
                - vote_id: Vote ID
                - total_amount_cents: Total amount in cents
                - by_category: List of dicts with category breakdown
        """
        total_stmt = select(
            func.coalesce(func.sum(Donation.amount), 0)
        ).where(Donation.vote_id == vote_id)
        total_amount = int(self.db.execute(total_stmt).scalar_one())

        by_cat_stmt = (
            select(
                Donation.category_id.label("category_id"),
                Category.name.label("category_name"),
                func.coalesce(func.sum(Donation.amount), 0).label("amount_cents"),
                func.count(Donation.id).label("count"),
            )
            .join(Category, Category.id == Donation.category_id)
            .where(Donation.vote_id == vote_id)
            .group_by(Donation.category_id, Category.name)
            .order_by(Donation.category_id.asc())
        )

        rows = self.db.execute(by_cat_stmt).all()
        by_category = [
            {
                "category_id": int(r.category_id),
                "category_name": str(r.category_name),
                "amount_cents": int(r.amount_cents),
                "count": int(r.count),
            }
            for r in rows
        ]

        return {
            "vote_id": vote_id,
            "total_amount_cents": total_amount,
            "by_category": by_category
        }

