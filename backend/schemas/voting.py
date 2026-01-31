"""
Voting domain schemas.

Contains request and response models for voting-related endpoints.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CategoryInput(BaseModel):
    """Input for creating or referencing a category by name."""
    name: str


class CreateVoteRequest(BaseModel):
    """Request model for creating a new vote."""
    question: str
    start_time: datetime
    end_time: datetime
    categories: list[CategoryInput]


class UpdateVoteRequest(BaseModel):
    """Request model for updating an existing vote."""
    question: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    categories: Optional[list[CategoryInput]] = None


class CategoryResponse(BaseModel):
    """Response model for category data."""
    id: int
    name: str

    class Config:
        from_attributes = True


class VoteResponse(BaseModel):
    """Response model for vote data."""
    id: int
    question: str
    start_time: datetime
    end_time: datetime
    categories: list[CategoryResponse]

    class Config:
        from_attributes = True
