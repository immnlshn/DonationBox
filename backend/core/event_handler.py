"""
Core Event Handler - Processes events from the event queue.
Dispatches events to component handlers that run in AsyncIO scope.
"""
import asyncio
import logging
from backend.gpio.event import GPIOEvent
from backend.core.container import AppContainer
from backend.gpio import registry
from backend.core.decorators import call_handler_with_injection

logger = logging.getLogger(__name__)

class EventHandler:
    """
    Event handler that processes events from the Core event queue.
    Dispatches events to component handlers in AsyncIO scope.
    Handles automatic dependency injection for handlers.
    Runs as a long-lived asyncio task in the FastAPI lifespan.
    """
    def __init__(self, container: AppContainer, event_queue: asyncio.Queue):
        """
        Initialize event handler.
        Args:
            container: Application container with DB and services
            event_queue: asyncio.Queue to read events from
        """
        self.container = container
        self.event_queue = event_queue
        self._task = None
    async def start(self):
        """Start the event handler task."""
        self._task = asyncio.create_task(self._run())
        logger.info("Event handler started")
    async def stop(self):
        """Stop the event handler task."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                logger.info("Event handler stopped")
                raise
    async def _run(self):
        """Main event processing loop."""
        try:
            while True:
                try:
                    # Wait for event with timeout to check for cancellation
                    event: GPIOEvent = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=1.0
                    )
                    logger.debug(f"Processing event: {event.component_id}/{event.event_type}")
                    # Process event by dispatching to component handlers
                    await self._process_event(event)
                    # Mark task done
                    self.event_queue.task_done()
                except asyncio.TimeoutError:
                    # No event - just continue to check for cancellation
                    continue
                except Exception as e:
                    logger.error(f"Error processing event: {e}", exc_info=True)
                    # Mark task done
                    self.event_queue.task_done()

        except asyncio.CancelledError:
            logger.info("Event handler cancelled")
            raise
        except Exception as e:
            logger.error(f"Fatal error in event handler: {e}", exc_info=True)
            raise
    async def _process_event(self, event: GPIOEvent):
        """
        Process a single event by dispatching to component handlers.
        Components register handlers using @event decorator.
        This method calls those handlers with automatic dependency injection.
        Args:
            event: Event to process
        """
        # Get component
        component = registry.get_component(event.component_id)
        if component is None:
            logger.warning(f"Component not found: {event.component_id}")
            return
        # Get registered handlers for this event type
        handlers = component.get_handlers(event.event_type)
        if not handlers:
            logger.debug(f"No handlers for {event.component_id}/{event.event_type}")
            return
        logger.debug(
            f"Dispatching {event.component_id}/{event.event_type} to {len(handlers)} handler(s)"
        )
        # Call all handlers with automatic dependency injection
        for handler in handlers:
            try:
                await call_handler_with_injection(
                    handler=handler,
                    gpio_event=event,
                    container=self.container
                )
            except Exception as e:
                logger.error(
                    f"Error in handler for {event.component_id}/{event.event_type}: {e}",
                    exc_info=True
                )
