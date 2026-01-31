"""
Event-driven programming decorators for GPIO components.

Provides decorators to register event handlers with automatic dependency injection.
"""

import inspect
from typing import Callable, Optional, Any
from backend.gpio.event import GPIOEvent
from backend.core.container import AppContainer


def event(event_type: str):
    """
    Decorator to register a method as an event handler.

    Automatically handles dependency injection based on method signature.
    Supports injection of:
    - container: AppContainer
    - event: GPIOEvent (automatically passed)

    Usage:
        class VoteButton(GPIOButton):
            @event("pressed")
            async def handle_press(self, event: GPIOEvent, container: AppContainer):
                # Business logic here
                async with container.sessionmaker() as session:
                    ...

    Args:
        event_type: Type of event to handle (e.g., "pressed", "released")
    """
    def decorator(func: Callable) -> Callable:
        # Store event type metadata
        func._event_type = event_type
        func._is_event_handler = True

        # Analyze function signature for dependency injection
        sig = inspect.signature(func)
        func._requires_container = 'container' in sig.parameters
        func._requires_event = 'gpio_event' in sig.parameters or 'event' in sig.parameters

        return func

    return decorator


def get_event_handlers(obj: Any) -> dict:
    """
    Get all event handlers from an object.

    Scans the object for methods decorated with @event and returns
    a mapping of event_type -> handler_function.

    Args:
        obj: Object to scan for event handlers

    Returns:
        Dict mapping event types to handler functions
    """
    handlers = {}

    for name in dir(obj):
        try:
            attr = getattr(obj, name)
            if callable(attr) and hasattr(attr, '_is_event_handler'):
                event_type = attr._event_type
                if event_type not in handlers:
                    handlers[event_type] = []
                handlers[event_type].append(attr)
        except AttributeError:
            continue

    return handlers


def is_event_handler(func: Callable) -> bool:
    """
    Check if a function is an event handler.

    Args:
        func: Function to check

    Returns:
        True if function is decorated with @event
    """
    return getattr(func, '_is_event_handler', False)


def get_handler_dependencies(func: Callable) -> dict:
    """
    Get dependency requirements of a handler.

    Args:
        func: Handler function

    Returns:
        Dict with 'container' and 'event' keys indicating requirements
    """
    return {
        'container': getattr(func, '_requires_container', False),
        'event': getattr(func, '_requires_event', True),  # Event is always passed
    }


async def call_handler_with_injection(
    handler: Callable,
    gpio_event: GPIOEvent,
    container: Optional[AppContainer] = None
):
    """
    Call a handler with automatic dependency injection.

    Args:
        handler: Handler function to call
        gpio_event: GPIO event
        container: Application container (optional, injected if handler requires it)
    """
    deps = get_handler_dependencies(handler)

    kwargs = {}

    # Pass event if handler expects it (check which parameter name is used)
    if deps['event']:
        sig = inspect.signature(handler)
        # Check if handler uses 'gpio_event' or 'event' as parameter name
        if 'gpio_event' in sig.parameters:
            kwargs['gpio_event'] = gpio_event
        elif 'event' in sig.parameters:
            kwargs['event'] = gpio_event

    # Inject container if required
    if deps['container']:
        if container is None:
            raise ValueError(f"Handler {handler.__name__} requires container but none provided")
        kwargs['container'] = container

    return await handler(**kwargs)
