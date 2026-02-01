"""
WebSocket message schemas for real-time communication.
"""
from datetime import datetime
from typing import Literal, Dict, Optional
from pydantic import BaseModel, Field


class CategoryChosenData(BaseModel):
    """Data payload when a category is chosen."""
    category_id: int = Field(..., description="ID of the chosen category")
    category_name: Optional[str] = Field(None, description="Name of the category (optional)")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the category was chosen")


class CategoryChosenMessage(BaseModel):
    """WebSocket message sent when a category is successfully chosen."""
    type: Literal["category_chosen"] = "category_chosen"
    data: CategoryChosenData


class MoneyInsertedData(BaseModel):
    """Data payload when money is inserted."""
    amount_cents: int = Field(..., description="Amount inserted in cents", ge=0)
    total_amount_cents: int = Field(..., description="Total accumulated amount in cents", ge=0)
    timestamp: datetime = Field(default_factory=datetime.now, description="When the money was inserted")


class MoneyInsertedMessage(BaseModel):
    """WebSocket message sent when money is inserted."""
    type: Literal["money_inserted"] = "money_inserted"
    data: MoneyInsertedData


class DonationTotals(BaseModel):
    """Aggregated totals for a voting."""
    total_amount_cents: int = Field(..., description="Total amount donated in cents")
    total_donations: int = Field(..., description="Total number of donations")
    category_totals: Dict[int, int] = Field(..., description="Map of category_id to amount_cents")


class DonationCreatedData(BaseModel):
    """Data payload when a donation is successfully created."""
    vote_id: int = Field(..., description="ID of the vote")
    category_id: int = Field(..., description="ID of the category donated to")
    amount_cents: int = Field(..., description="Amount donated in cents", ge=0)
    totals: DonationTotals = Field(..., description="Updated totals after donation")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the donation was created")


class DonationCreatedMessage(BaseModel):
    """WebSocket message sent when a donation is successfully created."""
    type: Literal["donation_created"] = "donation_created"
    data: DonationCreatedData


# Union type for all possible WebSocket messages
WebSocketMessage = CategoryChosenMessage | MoneyInsertedMessage | DonationCreatedMessage
