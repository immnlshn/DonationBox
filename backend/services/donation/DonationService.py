"""
DonationService - Manages the creation and management of donations.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from backend.database.repositories.donation_repository import DonationRepository
from backend.database.repositories.vote_repository import VoteRepository
from backend.database.repositories.category_repository import CategoryRepository
from backend.models import Donation


class DonationService:
    """Service for managing donations."""

    def __init__(
        self,
        donation_repo: DonationRepository,
        vote_repo: VoteRepository,
        category_repo: CategoryRepository,
    ):
        """
        Initialize DonationService with repositories.

        Args:
            donation_repo: DonationRepository instance
            vote_repo: VoteRepository instance
            category_repo: CategoryRepository instance
        """
        self.donation_repo = donation_repo
        self.vote_repo = vote_repo
        self.category_repo = category_repo

    def create_donation(
        self,
        vote_id: int,
        category_id: int,
        amount_cents: int,
        timestamp: Optional[datetime] = None,
    ) -> Donation:
        """
        Creates a new donation.

        Args:
            vote_id: The ID of the voting the donation belongs to
            category_id: The ID of the category to donate to
            amount_cents: The donation amount in cents
            timestamp: Optional - Timestamp of the donation (default: now)

        Returns:
            The created Donation object

        Raises:
            IntegrityError: If vote_id or category_id does not exist
        """
        return self.donation_repo.create(
            vote_id=vote_id,
            category_id=category_id,
            amount_cents=amount_cents,
            timestamp=timestamp,
        )

    def get_donation_by_id(self, donation_id: int) -> Optional[Donation]:
        """
        Returns a donation by ID.

        Args:
            donation_id: The ID of the donation to find

        Returns:
            The Donation object or None if not found
        """
        return self.donation_repo.get_by_id(donation_id)

    def list_donations_for_vote(self, vote_id: int) -> list[Donation]:
        """
        Returns all donations for a specific voting.

        Args:
            vote_id: The ID of the voting

        Returns:
            List of Donation objects
        """
        return self.donation_repo.list_for_vote(vote_id)

    def get_total_amount_for_vote(self, vote_id: int) -> int:
        """
        Calculates the total amount of all donations for a voting.

        Args:
            vote_id: The ID of the voting

        Returns:
            Total amount in cents
        """
        totals = self.donation_repo.get_totals_for_vote(vote_id)
        return totals["total_amount_cents"]

    def get_totals_for_vote(self, vote_id: int) -> dict:
        """
        Returns aggregated totals for all donations of a voting.

        Args:
            vote_id: The ID of the voting

        Returns:
            Dictionary with:
                - total_amount_cents: Total amount in cents
                - total_donations: Total number of donations
                - category_totals: Dict mapping category_id to amount_cents
        """
        totals = self.donation_repo.get_totals_for_vote(vote_id)
        category_totals = {
            cat["category_id"]: cat["amount_cents"]
            for cat in totals["by_category"]
        }
        return {
            "total_amount_cents": totals["total_amount_cents"],
            "total_donations": sum(cat["count"] for cat in totals["by_category"]),
            "category_totals": category_totals,
        }

    def get_donations_by_category(self, vote_id: int, category_id: int) -> list[Donation]:
        """
        Returns all donations for a specific category in a voting.

        Args:
            vote_id: The ID of the voting
            category_id: The ID of the category

        Returns:
            List of Donation objects
        """
        all_donations = self.list_donations_for_vote(vote_id)
        return [d for d in all_donations if d.category_id == category_id]

    def get_category_total(self, vote_id: int, category_id: int) -> int:
        """
        Calculates the total amount of all donations for a specific category.

        Args:
            vote_id: The ID of the voting
            category_id: The ID of the category

        Returns:
            Total amount in cents
        """
        totals = self.donation_repo.get_totals_for_vote(vote_id)
        for cat_data in totals["by_category"]:
            if cat_data["category_id"] == category_id:
                return cat_data["amount_cents"]
        return 0

    def get_vote_totals_detailed(self, vote_id: int) -> dict:
        """
        Returns detailed information about all donations of a voting.

        Args:
            vote_id: The ID of the voting

        Returns:
            Dictionary with total_amount_cents and by_category (list with details per category)
        """
        return self.donation_repo.get_totals_for_vote(vote_id)

    def get_active_vote_totals(self) -> Optional[dict]:
        """
        Returns detailed information about all donations of the currently active voting.

        Returns:
            Dictionary with statistics or None if no voting is active
        """
        active_vote = self.vote_repo.get_active()
        if not active_vote:
            return None
        return self.donation_repo.get_totals_for_vote(active_vote.id)

    def create_donation_for_active_vote(
        self,
        category_id: int,
        amount_cents: int,
        timestamp: Optional[datetime] = None,
    ) -> Optional[Donation]:
        """
        Creates a donation for the currently active voting.

        Args:
            category_id: The ID of the category to donate to
            amount_cents: The donation amount in cents
            timestamp: Optional - Timestamp of the donation (default: now)

        Returns:
            The created Donation object or None if no voting is active

        Raises:
            IntegrityError: If category_id does not exist or does not belong to the voting
        """
        active_vote = self.vote_repo.get_active()
        if not active_vote:
            return None

        return self.create_donation(
            vote_id=active_vote.id,
            category_id=category_id,
            amount_cents=amount_cents,
            timestamp=timestamp,
        )

    def get_donation_count_for_vote(self, vote_id: int) -> int:
        """
        Returns the number of all donations for a voting.

        Args:
            vote_id: The ID of the voting

        Returns:
            Number of donations
        """
        donations = self.list_donations_for_vote(vote_id)
        return len(donations)

    def get_donation_count_by_category(self, vote_id: int, category_id: int) -> int:
        """
        Returns the number of donations for a specific category.

        Args:
            vote_id: The ID of the voting
            category_id: The ID of the category

        Returns:
            Number of donations
        """
        totals = self.donation_repo.get_totals_for_vote(vote_id)
        for cat_data in totals["by_category"]:
            if cat_data["category_id"] == category_id:
                return cat_data["count"]
        return 0

    def validate_donation(self, vote_id: int, category_id: int) -> tuple[bool, str]:
        """
        Validates if a donation is possible for a specific voting and category.

        Args:
            vote_id: The ID of the voting
            category_id: The ID of the category

        Returns:
            Tuple (is_valid, error_message)
            - is_valid: True if the donation is possible, False otherwise
            - error_message: Error message if not valid, empty string otherwise
        """
        # Check if the voting exists
        vote = self.vote_repo.get_by_id(vote_id)
        if not vote:
            return False, f"Voting with ID {vote_id} does not exist"

        # Check if the category exists
        category = self.category_repo.get_by_id(category_id)
        if not category:
            return False, f"Category with ID {category_id} does not exist"

        # Check if the category belongs to the voting
        vote_category_ids = {c.id for c in vote.categories}
        if category_id not in vote_category_ids:
            return False, f"Category {category_id} does not belong to voting {vote_id}"

        return True, ""

    def get_leading_category(self, vote_id: int) -> Optional[dict]:
        """
        Returns the category with the most donations (by amount).

        Args:
            vote_id: The ID of the voting

        Returns:
            Dictionary with category_id, category_name, amount_cents, count
            or None if no donations exist
        """
        totals = self.donation_repo.get_totals_for_vote(vote_id)
        if not totals["by_category"]:
            return None

        return max(totals["by_category"], key=lambda x: x["amount_cents"])

