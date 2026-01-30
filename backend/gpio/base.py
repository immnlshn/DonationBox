"""
Base class for GPIO components.
"""
import logging
from abc import ABC, abstractmethod
from typing import Callable, Optional, Dict, List, Awaitable
from .event import GPIOEvent

logger = logging.getLogger(__name__)


class GPIOComponent(ABC):
    """
    Abstract base class for GPIO components.

    Components handle specific GPIO functionality and manage their own event handlers.
    Business logic should be implemented in the component's event handlers.
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

        # Component-specific event handlers
        self._handlers: Dict[str, List[Callable[[GPIOEvent], Awaitable[None]]]] = {}

    def on(self, event_type: str, handler: Callable[[GPIOEvent], Awaitable[None]]) -> None:
        """
        Register an async handler for a specific event type on this component.

        Args:
            event_type: Type of event (e.g., "pressed", "released")
            handler: Async function to handle the event

        Example:
            async def handle_press(event: GPIOEvent):
                # Business logic here
                await donation_service.create_donation(...)

            button.on("pressed", handle_press)
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)
        logger.debug(f"Component {self.component_id}: Handler registered for '{event_type}'")

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
        Internal use by ComponentRegistry.

        Args:
            event_type: Type of event

        Returns:
            List of handler functions
        """
        return self._handlers.get(event_type, [])

    @abstractmethod
    def start(self) -> None:
        """
        Start the component (setup GPIO pins, register callbacks, etc.).
        Called when ComponentRegistry starts.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        Stop the component and cleanup resources.
        Called when ComponentRegistry stops.
        """
        pass

    @property
    def is_started(self) -> bool:
        """Check if component is started."""
        return self._started
