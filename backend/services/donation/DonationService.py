"""
DonationService - Manages the creation and management of donations.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Optional

from backend.repositories import DonationRepository
from backend.models import Donation
from backend.services.voting import VotingService
from backend.services.websocket.WebSocketService import WebSocketService
from backend.core.state_store import StateStore

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


    async def process_pending_donation_from_state(
        self,
        state_store: "StateStore",
        ttl_seconds: float = 30.0
    ) -> Optional[Donation]:
        """
        Process a pending donation from state store.

        Checks if both category and money are present in state and not expired (< ttl_seconds old).
        If both conditions are met, creates donation and clears state.

        Args:
            state_store: State store instance to read from
            ttl_seconds: Maximum age in seconds for category and money (default: 30s)

        Returns:
            Created Donation or None if conditions not met
        """
        current_time = time.time()

        # Get category from state
        category_data = state_store.get("chosen_category", None)
        if not category_data or not isinstance(category_data, dict):
            logger.debug("No category selected or invalid format")
            return None

        category_id = category_data.get("category_id")
        category_timestamp = category_data.get("timestamp", 0)

        # Check category TTL
        if current_time - category_timestamp > ttl_seconds:
            logger.info(f"Category expired (age: {current_time - category_timestamp:.1f}s > {ttl_seconds}s)")
            state_store.delete("chosen_category")
            return None

        # Get money from state
        money_data = state_store.get("total_donation_cents", None)
        if not money_data or not isinstance(money_data, dict):
            logger.debug("No money inserted or invalid format")
            return None

        amount_cents = money_data.get("amount", 0)
        money_timestamp = money_data.get("timestamp", 0)

        # Check money amount
        if amount_cents <= 0:
            logger.debug("No money inserted (amount: 0)")
            return None

        # Check money TTL
        if current_time - money_timestamp > ttl_seconds:
            logger.info(f"Money expired (age: {current_time - money_timestamp:.1f}s > {ttl_seconds}s)")
            state_store.set("total_donation_cents", {"amount": 0, "timestamp": current_time})
            return None

        # Both present and valid - create donation
        logger.info(
            f"Processing donation: category_id={category_id}, amount_cents={amount_cents} "
            f"(category_age={current_time - category_timestamp:.1f}s, money_age={current_time - money_timestamp:.1f}s)"
        )

        donation = await self.create_donation_for_active_vote(
            category_id=category_id,
            amount_cents=amount_cents
        )

        if donation:
            # Clear state after successful donation
            logger.info("Donation successful - clearing state")
            state_store.set("total_donation_cents", {"amount": 0, "timestamp": current_time})
            state_store.delete("chosen_category")

        return donation


