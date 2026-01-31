"""
Base class for GPIO components.
"""
import logging
from abc import ABC, abstractmethod
from typing import Callable, Optional, List, Awaitable
from .event import GPIOEvent
logger = logging.getLogger(__name__)
class GPIOComponent(ABC):
    """
    Abstract base class for GPIO components.
    Components handle specific GPIO functionality.
    Event handlers are registered using @event decorator.
    """
    def __init__(self, component_id: str):
        """
        Initialize component with unique ID.
        Args:
            component_id: Unique identifier for this component
        """
        self.component_id = component_id
        self._event_callback: Optional[Callable[[GPIOEvent], None]] = None
        self._started = False
    def set_event_callback(self, callback: Callable[[GPIOEvent], None]) -> None:
        """
        Set the callback function for emitting events to the registry.
        Internal use by ComponentRegistry.
        Args:
            callback: Function to call when an event occurs
        """
        self._event_callback = callback
    def emit_event(self, event_type: str, data: dict = None) -> None:
        """
        Emit an event through the registered callback.
        Thread-safe - can be called from GPIO callback threads.
        Args:
            event_type: Type of event
            data: Optional event data
        """
        if self._event_callback is None:
            logger.warning(f"Component {self.component_id}: No event callback registered")
            return
        event = GPIOEvent(
            component_id=self.component_id,
            event_type=event_type,
            data=data or {}
        )
        try:
            self._event_callback(event)
        except Exception as e:
            logger.error(
                f"Component {self.component_id}: Error in event callback: {e}",
                exc_info=True
            )
    def get_handlers(self, event_type: str) -> List[Callable[[GPIOEvent], Awaitable[None]]]:
        """
        Get all registered handlers for a specific event type.
        Scans the component for @event decorated methods.
        Internal use by EventHandler.
        Args:
            event_type: Type of event
        Returns:
            List of handler functions for this event type
        """
        from backend.core.decorators import get_event_handlers
        all_handlers = get_event_handlers(self)
        return all_handlers.get(event_type, [])
    @abstractmethod
    def start(self) -> None:
        """
        Start the component and begin monitoring/controlling GPIO.
        Implementation should set up GPIO pins and start any necessary threads/timers.
        """
        pass
    @abstractmethod
    def stop(self) -> None:
        """
        Stop the component and release GPIO resources.
        Implementation should clean up GPIO pins and stop any threads/timers.
        """
        pass
    @property
    def is_started(self) -> bool:
        """Check if component is started."""
        return self._started
