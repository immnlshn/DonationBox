"""
FastAPI Dependencies for Services.

Usage in Routes:
    from fastapi import Depends
    from backend.services.dependencies import get_voting_service

    @router.get("/votes")
    async def list_votes(voting_service: VotingService = Depends(get_voting_service)):
        return voting_service.list_votes()
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.repositories.vote_repository import VoteRepository
from backend.database.repositories.donation_repository import DonationRepository
from backend.database.repositories.category_repository import CategoryRepository
from backend.services.voting.VotingService import VotingService
from backend.services.donation.DonationService import DonationService


# Repository Dependencies

def get_vote_repository(db: Session = Depends(get_db)) -> VoteRepository:
    """
    FastAPI Dependency for VoteRepository.
    Automatically injects the DB session.
    """
    return VoteRepository(db=db)


def get_donation_repository(db: Session = Depends(get_db)) -> DonationRepository:
    """
    FastAPI Dependency for DonationRepository.
    Automatically injects the DB session.
    """
    return DonationRepository(db=db)


def get_category_repository(db: Session = Depends(get_db)) -> CategoryRepository:
    """
    FastAPI Dependency for CategoryRepository.
    Automatically injects the DB session.
    """
    return CategoryRepository(db=db)


# Service Dependencies

def get_voting_service(
    vote_repo: VoteRepository = Depends(get_vote_repository)
) -> VotingService:
    """
    FastAPI Dependency for VotingService.
    Automatically injects the repository.
    """
    return VotingService(vote_repo=vote_repo)


def get_donation_service(
    donation_repo: DonationRepository = Depends(get_donation_repository),
    vote_repo: VoteRepository = Depends(get_vote_repository),
    category_repo: CategoryRepository = Depends(get_category_repository),
) -> DonationService:
    """
    FastAPI Dependency for DonationService.
    Automatically injects all required repositories.
    """
    return DonationService(
        donation_repo=donation_repo,
        vote_repo=vote_repo,
        category_repo=category_repo,
    )

