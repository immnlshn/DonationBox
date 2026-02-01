"""
FastAPI Dependencies for Services.

All dependencies use the AppContainer from app.state.container.
Services are created via Container factory methods.

Usage in Routes:
    from fastapi import Depends
    from backend.services.dependencies import get_voting_service

    @router.get("/votes")
    async def list_votes(voting_service: VotingService = Depends(get_voting_service)):
        return await voting_service.list_votes()
"""

from typing import AsyncGenerator

from fastapi import Depends, Request, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core import AppContainer
from backend.services.voting.VotingService import VotingService
from backend.services.donation.DonationService import DonationService
from backend.services.websocket.WebSocketService import WebSocketService


# Container accessor

def get_container(request: Request) -> AppContainer:
    """
    Get the application container from app.state.

    Args:
        request: FastAPI request object

    Returns:
        AppContainer instance
    """
    return request.app.state.container


# Database session dependency

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI Dependency for Async Database Sessions.

    Creates a new async session from the container's sessionmaker.

    Usage in routes:
        @router.get("/")
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...
    """
    container = get_container(request)
    async with container.sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Service Dependencies
# Note: We don't expose Repository dependencies directly anymore.
# Services are created via Container factory methods.

def get_websocket_service(request: Request) -> WebSocketService:
    """
    FastAPI Dependency for WebSocketService (HTTP endpoints).
    Returns the WebSocketService from the container.
    """
    container = get_container(request)
    return container.websocket_service


def get_websocket_service_ws(websocket: WebSocket) -> WebSocketService:
    """
    FastAPI Dependency for WebSocketService (WebSocket endpoints).
    WebSocket endpoints don't have a Request object, so we access the app directly.

    Args:
        websocket: WebSocket connection instance

    Returns:
        WebSocketService instance
    """
    return websocket.app.state.container.websocket_service


def get_voting_service(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> VotingService:
    """
    FastAPI Dependency for VotingService.
    Uses the container's factory method.
    """
    container = get_container(request)
    return container.create_voting_service(db)


def get_donation_service(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> DonationService:
    """
    FastAPI Dependency for DonationService.
    Uses the container's factory method.
    """
    container = get_container(request)
    return container.create_donation_service(db)





