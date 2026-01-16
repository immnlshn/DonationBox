"""
DonationService - Manages the creation and management of donations.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from backend.repositories import DonationRepository
from backend.services.voting import VotingService
from backend.services.websocket import WebSocketService
from backend.models import Donation

logger = logging.getLogger(__name__)


class DonationService:
    """Service for managing donations."""

    def __init__(
        self,
        donation_repo: DonationRepository,
        voting_service: VotingService,
        websocket_service: WebSocketService,
    ):
        """
        Initialize DonationService with repository and services.

        Args:
            donation_repo: DonationRepository instance
            voting_service: VotingService instance for vote-related operations
            websocket_service: WebSocketService instance for broadcasting
        """
        self.donation_repo = donation_repo
        self.voting_service = voting_service
        self.websocket_service = websocket_service

    async def create_donation(
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
        return await self.donation_repo.create(
            vote_id=vote_id,
            category_id=category_id,
            amount_cents=amount_cents,
            timestamp=timestamp,
        )

    async def get_donation_by_id(self, donation_id: int) -> Optional[Donation]:
        """
        Returns a donation by ID.

        Args:
            donation_id: The ID of the donation to find

        Returns:
            The Donation object or None if not found
        """
        return await self.donation_repo.get_by_id(donation_id)

    async def list_donations_for_vote(self, vote_id: int) -> list[Donation]:
        """
        Returns all donations for a specific voting.

        Args:
            vote_id: The ID of the voting

        Returns:
            List of Donation objects
        """
        return await self.donation_repo.list_for_vote(vote_id)

    async def get_total_amount_for_vote(self, vote_id: int) -> int:
        """
        Calculates the total amount of all donations for a voting.

        Args:
            vote_id: The ID of the voting

        Returns:
            Total amount in cents
        """
        totals = await self.donation_repo.get_totals_for_vote(vote_id)
        return totals["total_amount_cents"]

    async def get_totals_for_vote(self, vote_id: int) -> dict:
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
        totals = await self.donation_repo.get_totals_for_vote(vote_id)
        category_totals = {
            cat["category_id"]: cat["amount_cents"]
            for cat in totals["by_category"]
        }
        return {
            "total_amount_cents": totals["total_amount_cents"],
            "total_donations": sum(cat["count"] for cat in totals["by_category"]),
            "category_totals": category_totals,
        }

    async def get_vote_totals_detailed(self, vote_id: int) -> dict:
        """
        Returns detailed information about all donations of a voting.

        Args:
            vote_id: The ID of the voting

        Returns:
            Dictionary with total_amount_cents and by_category (list with details per category)
        """
        return await self.donation_repo.get_totals_for_vote(vote_id)

    async def get_active_vote_totals(self) -> Optional[dict]:
        """
        Returns detailed information about all donations of the currently active voting.

        Returns:
            Dictionary with statistics or None if no voting is active
        """
        active_vote = await self.voting_service.get_active_vote()
        if not active_vote:
            return None
        return await self.donation_repo.get_totals_for_vote(active_vote.id)

    async def create_donation_for_active_vote(
        self,
        category_id: int,
        amount_cents: int,
        timestamp: Optional[datetime] = None,
    ) -> Optional[Donation]:
        """
        Creates a donation for the currently active voting and broadcasts update via WebSocket.

        Args:
            category_id: The ID of the category to donate to
            amount_cents: The donation amount in cents
            timestamp: Optional - Timestamp of the donation (default: now)

        Returns:
            The created Donation object or None if no voting is active

        Raises:
            IntegrityError: If category_id does not exist or does not belong to the voting
        """
        active_vote = await self.voting_service.get_active_vote()
        if not active_vote:
            logger.warning("Cannot create donation: No active vote exists")
            return None

        logger.info(
            f"Creating donation: vote_id={active_vote.id}, "
            f"category_id={category_id}, amount_cents={amount_cents}"
        )

        donation = await self.create_donation(
            vote_id=active_vote.id,
            category_id=category_id,
            amount_cents=amount_cents,
            timestamp=timestamp,
        )

        logger.info(f"Donation created successfully: donation_id={donation.id}")

        # Get updated totals after donation
        totals = await self.get_totals_for_vote(active_vote.id)

        # Broadcast donation event to all connected WebSocket clients
        try:
            await self.websocket_service.broadcast_json({
                "type": "donation_created",
                "data": {
                    "vote_id": active_vote.id,
                    "category_id": category_id,
                    "amount_cents": amount_cents,
                    "totals": totals
                }
            })
            logger.debug(
                f"WebSocket broadcast sent for donation_id={donation.id}, "
                f"connections={self.websocket_service.get_connection_count()}"
            )
        except Exception as e:
            # Log but don't fail the donation if broadcast fails
            logger.error(
                f"Failed to broadcast donation update: donation_id={donation.id}, error={e}",
                exc_info=True
            )

        return donation

    async def get_donation_count_for_vote(self, vote_id: int) -> int:
        """
        Returns the number of all donations for a voting.

        Args:
            vote_id: The ID of the voting

        Returns:
            Number of donations
        """
        donations = await self.list_donations_for_vote(vote_id)
        return len(donations)


