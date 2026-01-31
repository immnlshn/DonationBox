"""
Donation domain schemas.

Contains request and response models for donation-related endpoints.
"""
from pydantic import BaseModel


class DonationRequest(BaseModel):
    """Request model for creating a donation."""
    amount_cents: int
    category_id: int


class DonationResponse(BaseModel):
    """Response model for created donation."""
    success: bool
    donation_id: int
    vote_id: int
    category_id: int
    amount_cents: int
    message: str


class DonationTotalsResponse(BaseModel):
    """Response model for donation totals."""
    vote_id: int
    total_amount_cents: int
    total_donations: int
    category_totals: dict[int, int]
