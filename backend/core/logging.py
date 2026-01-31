"""
Logging configuration for the application.

Sets up Python logging with appropriate formatters and levels.
"""

import logging

from .config import settings


def setup_logging() -> None:
    """
    Configure application logging.

    Sets up logging format and level based on application settings.
    Also configures uvicorn loggers to match the application log level.
    """
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # Configure uvicorn loggers to match application log level
    logging.getLogger("uvicorn").setLevel(settings.LOG_LEVEL)
    logging.getLogger("uvicorn.error").setLevel(settings.LOG_LEVEL)
    logging.getLogger("uvicorn.access").setLevel(settings.LOG_LEVEL)

    # Log the current log level
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized with level: {settings.LOG_LEVEL}")
