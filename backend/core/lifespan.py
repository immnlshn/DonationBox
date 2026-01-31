"""
FastAPI lifespan management.

Handles application startup and shutdown events, including:
- Application container setup
- Core event system
- GPIO initialization and cleanup
- Event handler
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.gpio import registry
from backend.gpio.components import setup_components
from backend.core.container import AppContainer
from backend.core import events
from backend.core.event_handler import EventHandler
from .config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Handles startup and shutdown events for the application:
    - Startup: Create container, init event system, start GPIO, start handler
    - Shutdown: Stop handler, stop GPIO, cleanup container

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting application...")

    # Create and setup application container
    logger.info("Setting up application container...")
    container = AppContainer()
    container.setup()
    app.state.container = container
    logger.info("Application container ready")

    # Initialize Core event system
    logger.info("Initializing event system...")
    event_queue = events.initialize_event_queue(maxsize=100)
    logger.info("Event system ready")

    # Initialize GPIO hardware
    logger.info("Initializing GPIO...")
    registry.initialize(
        enable_gpio=settings.ENABLE_GPIO,
        pin_factory=settings.PIN_FACTORY
    )

    # Setup GPIO components
    setup_components(registry)
    logger.info(f"Registered {len(registry.list_components())} GPIO components")

    # Start GPIO registry (passes Core event queue)
    logger.info("Starting GPIO registry...")
    await registry.start(event_queue=event_queue)

    # Start Core event handler
    logger.info("Starting event handler...")
    event_handler = EventHandler(container, event_queue)
    await event_handler.start()
    app.state.event_handler = event_handler
    logger.info("Event handler started")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")

    # Stop event handler
    if hasattr(app.state, 'event_handler'):
        logger.info("Stopping event handler...")
        await app.state.event_handler.stop()

    # Stop GPIO registry
    logger.info("Stopping GPIO registry...")
    await registry.stop()

    # Dispose container (closes DB, WebSocket)
    logger.info("Disposing application container...")
    await container.dispose()

    logger.info("Application shutdown complete")
