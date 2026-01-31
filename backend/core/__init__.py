"""
Core package for central application components.

This package contains:
- config: Application settings and configuration
- database: Database setup function (setup_database)
- logging: Logging configuration
- lifespan: FastAPI lifespan management
- container: Application dependency injection container
- events: Event queue system
- event_handler: Event processing
"""

from .config import settings
from .database import setup_database
from .logging import setup_logging
from .container import AppContainer

__all__ = [
    "settings",
    "setup_database",
    "setup_logging",
    "AppContainer",
]
