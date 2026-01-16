import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.services.dependencies import get_voting_service, get_donation_service
from backend.services.voting import VotingService
from backend.services.donation import DonationService

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models
class CategoryResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class VoteResponse(BaseModel):
    id: int
    question: str
    is_active: bool
    categories: list[CategoryResponse]

    class Config:
        from_attributes = True


class DonationTotalsResponse(BaseModel):
    vote_id: int
    total_amount_cents: int
    total_donations: int
    category_totals: dict[int, int]


@router.get('/', response_model=Optional[VoteResponse])
async def get_current_vote(
    voting_service: VotingService = Depends(get_voting_service)
):
    """
    Returns the currently active voting.

    Returns:
        The active Vote object or None if no vote is active
    """
    vote = await voting_service.get_active_vote()
    if not vote:
        logger.warning("No active vote found")
        raise HTTPException(
            status_code=404,
            detail="No active vote found"
        )
    return vote

@router.get('/{vote_id}/totals', response_model=DonationTotalsResponse)
async def get_vote_totals(
    vote_id: int,
    donation_service: DonationService = Depends(get_donation_service)
):
    """
    Returns donation totals for a voting.

    Args:
        vote_id: The ID of the voting
        donation_service: DonationService instance

    Returns:
        Totals with total amount and amounts per category
    """
    totals = await donation_service.get_totals_for_vote(vote_id)
    return DonationTotalsResponse(
        vote_id=vote_id,
        **totals
    )

