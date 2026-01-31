"""
Core package for central application components.

This package contains:
- config: Application settings and configuration
- database: Database session and engine setup
- logging: Logging configuration
- lifespan: FastAPI lifespan management
"""

from .config import settings
from .database import get_db, engine, AsyncSessionLocal
from .logging import setup_logging

__all__ = [
    "settings",
    "get_db",
    "engine",
    "AsyncSessionLocal",
    "setup_logging",
]
