"""
Application Container - Dependency Injection Container for long-lived objects.

Manages application-scoped dependencies (not request-scoped):
- Database engine and session factory (from core.database)
- WebSocket hub
- Configuration
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from backend.core.database import setup_database
from backend.services.websocket.WebSocketService import WebSocketService
from backend.repositories import VoteRepository, CategoryRepository, DonationRepository
from backend.services.voting.VotingService import VotingService
from backend.services.category.CategoryService import CategoryService
from backend.services.donation.DonationService import DonationService
from backend.core.state_store import StateStore

logger = logging.getLogger(__name__)


class AppContainer:
  """
  Application container holding long-lived dependencies.

  Created once during application startup (lifespan context).
  Stored in app.state.container for access from routes and workers.

  DO NOT store request-scoped objects here (e.g., DB sessions).
  """

  def __init__(self):
    self.config = settings
    self.engine = None
    self.sessionmaker = None
    self.websocket_service = None
    self.state_store = None

  def setup(self):
    """
    Setup container dependencies.

    Call this during application startup (lifespan context).
    """
    logger.info("Setting up AppContainer...")

    # Use existing database infrastructure
    self._setup_database()

    # Setup WebSocket hub
    self._setup_websocket()

    # Setup state store
    self._setup_state_store()

    logger.info("AppContainer setup complete")

  def _setup_database(self):
    """Setup database using setup_database() from database module."""

    # Call setup function to create engine and sessionmaker
    self.engine, self.sessionmaker = setup_database()

    logger.info("Database engine and sessionmaker configured")

  def _setup_websocket(self):
    """Setup WebSocket hub."""

    self.websocket_service = WebSocketService()
    logger.info("WebSocket hub created")

  def _setup_state_store(self):
    """Setup in-memory state store."""

    self.state_store = StateStore()
    logger.info("State store created")

  async def dispose(self):
    """
    Cleanup container resources.

    Call this during application shutdown (lifespan context).
    """
    logger.info("Disposing AppContainer...")

    # Close WebSocket connections
    if self.websocket_service:
      await self.websocket_service.close_all_connections()

    # Dispose database engine (using the shared instance)
    if self.engine:
      await self.engine.dispose()
      logger.info("Database engine disposed")

    logger.info("AppContainer disposed")

  # Factory methods for services

  def get_websocket_service(self):
    """
    Get WebSocketService instance (singleton).

    Returns:
        WebSocketService instance
    """
    return self.websocket_service

  def create_category_service(self, db: AsyncSession):
    """
    Create CategoryService instance with repository.

    Args:
        db: Database session for this service

    Returns:
        CategoryService instance
    """
    category_repo = CategoryRepository(db=db)
    return CategoryService(category_repo=category_repo)

  def create_voting_service(self, db: AsyncSession):
    """
    Create VotingService instance with repositories.

    Args:
        db: Database session for this service

    Returns:
        VotingService instance
    """

    vote_repo = VoteRepository(db=db)
    category_repo = CategoryRepository(db=db)
    return VotingService(vote_repo=vote_repo, category_repo=category_repo)

  def create_donation_service(self, db: AsyncSession):
    """
    Create DonationService instance with repositories and services.

    Args:
        db: Database session for this service

    Returns:
        DonationService instance
    """

    donation_repo = DonationRepository(db=db)
    voting_service = self.create_voting_service(db)
    return DonationService(
        donation_repo=donation_repo,
        voting_service=voting_service,
        websocket_service=self.websocket_service
    )


