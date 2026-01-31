import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.schemas.donation import DonationRequest, DonationResponse
from backend.services.dependencies import get_donation_service
from backend.services.donation.DonationService import DonationService

logger = logging.getLogger(__name__)

router = APIRouter()



@router.post('/donation', response_model=DonationResponse)
async def send_donation(
    request: DonationRequest,
    donation_service: DonationService = Depends(get_donation_service)
):
    """
    Debug endpoint to simulate a donation from GPIO/coin validator.
    Creates a donation for the currently active vote.

    Args:
        request: DonationRequest with amount_cents and category_id
        donation_service: Injected DonationService

    Returns:
        DonationResponse with created donation details

    Raises:
        HTTPException 400: If no active vote exists
        HTTPException 400: If category doesn't exist or doesn't belong to vote
    """
    logger.info(f"Debug donation received: {request.amount_cents} cents for category {request.category_id}")

    # Create donation for active vote
    donation = await donation_service.create_donation_for_active_vote(
        category_id=request.category_id,
        amount_cents=request.amount_cents
    )

    if donation is None:
        logger.warning("No active vote found for donation")
        raise HTTPException(
            status_code=404,
            detail="No active vote available. Please activate a vote first."
        )

    logger.info(f"Donation created: ID={donation.id}, Vote={donation.vote_id}, Category={donation.category_id}")

    return DonationResponse(
        success=True,
        donation_id=donation.id,
        vote_id=donation.vote_id,
        category_id=donation.category_id,
        amount_cents=donation.amount,
        message="Donation successfully created and broadcast to clients"
    )
