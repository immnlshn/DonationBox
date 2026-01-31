"""
FastAPI lifespan management.

Handles application startup and shutdown events, including:
- GPIO initialization and cleanup
- WebSocket connection management
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.gpio import registry
from backend.gpio.components import setup_components
from backend.services.dependencies import get_websocket_service
from .config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Handles startup and shutdown events for the application:
    - Startup: Initialize GPIO components and start registry
    - Shutdown: Close WebSocket connections and stop GPIO registry

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting application...")

    logger.info("Initializing GPIO...")
    registry.initialize(
        enable_gpio=settings.ENABLE_GPIO,
        pin_factory=settings.PIN_FACTORY
    )

    # Setup GPIO components from configuration
    setup_components(registry)
    logger.info(f"Registered {len(registry.list_components())} GPIO components")

    logger.info("Starting GPIO registry...")
    await registry.start()

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")

    # First, close all WebSocket connections gracefully
    logger.info("Closing WebSocket connections...")
    await get_websocket_service().close_all_connections()

    # Then stop GPIO registry
    logger.info("Stopping GPIO registry...")
    await registry.stop()

    logger.info("Application shutdown complete")
