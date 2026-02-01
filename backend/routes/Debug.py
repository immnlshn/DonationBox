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

    Accepts either category_id (direct) or position (resolved from active vote).

    Args:
        request: DonationRequest with amount_cents and (category_id OR position)
        donation_service: Injected DonationService

    Returns:
        DonationResponse with created donation details

    Raises:
        HTTPException 404: If no active vote exists
        HTTPException 422: If category/position is invalid
    """
    logger.info(f"Debug donation received: {request.amount_cents} cents")

    try:
        # Resolve category_id from position if needed
        if request.position is not None:
            # Get active vote
            active_vote = await donation_service.voting_service.get_active_vote()
            if not active_vote:
                raise HTTPException(
                    status_code=404,
                    detail="No active vote available. Please activate a vote first."
                )

            # Resolve position to category_id
            if not (0 <= request.position < len(active_vote.categories)):
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid position {request.position}. Active vote has {len(active_vote.categories)} categories."
                )

            category_id = active_vote.categories[request.position].id
            logger.info(f"Resolved position {request.position} -> category_id={category_id}")
        else:
            category_id = request.category_id
            logger.info(f"Using direct category_id={category_id}")

        # Create donation for active vote
        donation = await donation_service.create_donation_for_active_vote(
            category_id=category_id,
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
    except ValueError as e:
        # Category doesn't belong to active vote
        logger.warning(f"Invalid category for donation: {e}")
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )
