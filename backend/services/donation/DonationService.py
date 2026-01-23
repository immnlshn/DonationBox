"""
DonationService - Manages the creation and management of donations.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from backend.repositories import DonationRepository
from backend.models import Donation

if TYPE_CHECKING:
    from backend.services.voting import VotingService
    from backend.services.websocket.WebSocketService import WebSocketService

logger = logging.getLogger(__name__)


class DonationService:
    """Service for managing donations."""

    def __init__(
        self,
        donation_repo: DonationRepository,
        voting_service: "VotingService",
        websocket_service: "WebSocketService",
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

        donation = await self.donation_repo.create(
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



