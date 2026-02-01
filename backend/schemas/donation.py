"""
Donation domain schemas.

Contains request and response models for donation-related endpoints.
"""
from typing import Optional
from pydantic import BaseModel, model_validator


class DonationRequest(BaseModel):
    """Request model for creating a donation."""
    amount_cents: int
    category_id: Optional[int] = None
    position: Optional[int] = None

    @model_validator(mode='after')
    def validate_category_or_position(self):
        """Ensure exactly one of category_id or position is provided."""
        if self.category_id is None and self.position is None:
            raise ValueError("Either category_id or position must be provided")
        if self.category_id is not None and self.position is not None:
            raise ValueError("Cannot specify both category_id and position")
        return self


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
