import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.services.dependencies import get_voting_service, get_donation_service
from backend.services.voting import VotingService
from backend.services.donation import DonationService

logger = logging.getLogger(__name__)

router = APIRouter()


# Request Models
class CategoryInput(BaseModel):
    """Input for creating or referencing a category."""
    id: Optional[int] = None
    name: str


class CreateVoteRequest(BaseModel):
    question: str
    start_time: datetime
    end_time: datetime
    categories: list[CategoryInput]


class UpdateVoteRequest(BaseModel):
    question: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    categories: Optional[list[CategoryInput]] = None


# Response Models
class CategoryResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class VoteResponse(BaseModel):
    id: int
    question: str
    start_time: datetime
    end_time: datetime
    is_active: bool
    categories: list[CategoryResponse]

    class Config:
        from_attributes = True


class DonationTotalsResponse(BaseModel):
    vote_id: int
    total_amount_cents: int
    total_donations: int
    category_totals: dict[int, int]


# Public endpoints
@router.get('/active', response_model=VoteResponse)
async def get_active_vote(
    voting_service: VotingService = Depends(get_voting_service)
):
    """
    Returns the currently active voting.

    Returns:
        The active Vote object with question and categories

    Raises:
        HTTPException 404: If no active vote is found
    """
    vote = await voting_service.get_active_vote()
    if not vote:
        logger.warning("No active vote found")
        raise HTTPException(
            status_code=404,
            detail="No active vote found"
        )
    return vote


@router.get('/active/totals', response_model=DonationTotalsResponse)
async def get_active_vote_totals(
    voting_service: VotingService = Depends(get_voting_service),
    donation_service: DonationService = Depends(get_donation_service)
):
    """
    Returns donation totals for the currently active voting.

    Returns:
        Totals with total amount and amounts per category

    Raises:
        HTTPException 404: If no active vote is found
    """
    vote = await voting_service.get_active_vote()
    if not vote:
        raise HTTPException(
            status_code=404,
            detail="No active vote found"
        )

    totals = await donation_service.get_totals_for_vote(vote.id)
    return DonationTotalsResponse(
        vote_id=vote.id,
        **totals
    )


# Management endpoints
@router.get('/', response_model=list[VoteResponse])
async def list_all_votes(
    limit: int = 100,
    offset: int = 0,
    voting_service: VotingService = Depends(get_voting_service)
):
    """
    Returns a list of all votings (paginated).

    Args:
        limit: Maximum number of votings to return (default: 100)
        offset: Number of votings to skip (default: 0)

    Returns:
        List of Vote objects
    """
    votes = await voting_service.list_all_votes(limit=limit, offset=offset)
    return votes


@router.post('/', response_model=VoteResponse, status_code=201)
async def create_vote(
    request: CreateVoteRequest,
    voting_service: VotingService = Depends(get_voting_service)
):
    """
    Creates a new voting.

    The vote will be automatically active based on start_time and end_time.

    Categories can be provided as:
    - Existing category: {"id": 1, "name": "Tierschutz"}
    - New category: {"name": "Neue Kategorie"} (will be created if not exists)

    Args:
        request: CreateVoteRequest with vote details

    Returns:
        The created Vote object

    Raises:
        HTTPException 400: If validation fails
    """
    try:
        # Import CategoryInput from service
        from backend.services.voting.VotingService import CategoryInput

        # Convert request categories to service CategoryInput
        categories = [
            CategoryInput(id=cat.id, name=cat.name)
            for cat in request.categories
        ]

        vote = await voting_service.create_vote(
            question=request.question,
            start_time=request.start_time,
            end_time=request.end_time,
            categories=categories,
        )
        logger.info(f"Vote created: id={vote.id}, question='{vote.question}'")
        return vote
    except Exception as e:
        logger.error(f"Failed to create vote: {e}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create vote: {str(e)}"
        )


@router.get('/{vote_id}', response_model=VoteResponse)
async def get_vote_by_id(
    vote_id: int,
    voting_service: VotingService = Depends(get_voting_service)
):
    """
    Returns a specific voting by ID.

    Args:
        vote_id: The ID of the voting

    Returns:
        The Vote object

    Raises:
        HTTPException 404: If vote is not found
    """
    vote = await voting_service.get_vote_by_id(vote_id)
    if not vote:
        raise HTTPException(
            status_code=404,
            detail=f"Vote with id {vote_id} not found"
        )
    return vote


@router.put('/{vote_id}', response_model=VoteResponse)
async def update_vote(
    vote_id: int,
    request: UpdateVoteRequest,
    voting_service: VotingService = Depends(get_voting_service)
):
    """
    Updates an existing voting.

    Categories can be provided as:
    - Existing category: {"id": 1, "name": "Tierschutz"}
    - New category: {"name": "Neue Kategorie"} (will be created if not exists)

    Args:
        vote_id: The ID of the voting to update
        request: UpdateVoteRequest with fields to update

    Returns:
        The updated Vote object

    Raises:
        HTTPException 404: If vote is not found
        HTTPException 400: If validation fails
    """
    try:
        # Convert request categories to service CategoryInput if provided
        categories = None
        if request.categories is not None:
            from backend.services.voting.VotingService import CategoryInput
            categories = [
                CategoryInput(id=cat.id, name=cat.name)
                for cat in request.categories
            ]

        vote = await voting_service.update_vote(
            vote_id=vote_id,
            question=request.question,
            start_time=request.start_time,
            end_time=request.end_time,
            categories=categories,
        )
        logger.info(f"Vote updated: id={vote.id}")
        return vote
    except Exception as e:
        logger.error(f"Failed to update vote {vote_id}: {e}", exc_info=True)
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Vote with id {vote_id} not found"
            )
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update vote: {str(e)}"
        )


@router.delete('/{vote_id}', status_code=204)
async def delete_vote(
    vote_id: int,
    voting_service: VotingService = Depends(get_voting_service)
):
    """
    Deletes a voting. All associated donations will also be deleted (CASCADE).

    Args:
        vote_id: The ID of the voting to delete

    Raises:
        HTTPException 404: If vote is not found
    """
    success = await voting_service.delete_vote(vote_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Vote with id {vote_id} not found"
        )
    logger.info(f"Vote deleted: id={vote_id}")


@router.get('/{vote_id}/totals', response_model=DonationTotalsResponse)
async def get_vote_totals(
    vote_id: int,
    donation_service: DonationService = Depends(get_donation_service)
):
    """
    Returns donation totals for a specific voting.

    Args:
        vote_id: The ID of the voting

    Returns:
        Totals with total amount and amounts per category
    """
    totals = await donation_service.get_totals_for_vote(vote_id)
    return DonationTotalsResponse(
        vote_id=vote_id,
        **totals
    )









