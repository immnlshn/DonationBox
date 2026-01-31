"""
Core Event System - Central event queue for GPIO and other events.

This module provides the central event queue that GPIO components use
to dispatch events into the asyncio event loop for processing.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global event queue - initialized during app startup
_event_queue: Optional[asyncio.Queue] = None


def initialize_event_queue(maxsize: int = 100) -> asyncio.Queue:
    """
    Initialize the global event queue.

    Called during application startup (lifespan context).

    Args:
        maxsize: Maximum queue size

    Returns:
        The created event queue
    """
    global _event_queue
    _event_queue = asyncio.Queue(maxsize=maxsize)
    logger.info(f"Event queue initialized (maxsize={maxsize})")
    return _event_queue


def get_event_queue() -> Optional[asyncio.Queue]:
    """
    Get the global event queue.

    Returns:
        The event queue, or None if not initialized
    """
    return _event_queue
