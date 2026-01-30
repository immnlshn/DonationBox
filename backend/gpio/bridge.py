"""
Event Bridge - connects GPIO callback threads to asyncio event loop.
"""
import logging
import asyncio
from typing import Optional, Callable, Awaitable
from .event import GPIOEvent
logger = logging.getLogger(__name__)
class EventBridge:
    """
    Bridges GPIO events from callback threads to the asyncio event loop.
    GPIO callbacks run in separate threads (from gpiozero).
    This bridge ensures events are safely processed in the FastAPI asyncio loop.
    KEY: Uses asyncio.Queue (not queue.Queue!) for proper async/await support.
    Thread-safety achieved via loop.call_soon_threadsafe().
    """
    def __init__(self):
        # asyncio.Queue - initialized when loop is available
        self._event_queue: Optional[asyncio.Queue[GPIOEvent]] = None
        # asyncio event loop reference
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        # Consumer task
        self._task: Optional[asyncio.Task] = None
        self._running: bool = False
        # Event dispatcher callback
        self._dispatcher: Optional[Callable[[GPIOEvent], Awaitable[None]]] = None
    def set_dispatcher(self, dispatcher: Callable[[GPIOEvent], Awaitable[None]]) -> None:
        """
        Set the event dispatcher callback.
        Args:
            dispatcher: Async function that handles dispatching events
        """
        self._dispatcher = dispatcher
    def queue_event(self, event: GPIOEvent) -> None:
        """
        Queue an event from a GPIO callback thread.
        Thread-safe: Uses call_soon_threadsafe to schedule put_nowait
        in the asyncio loop from a different thread.
        Args:
            event: GPIO event to queue
        """
        if self._loop is None or self._event_queue is None:
            logger.warning(
                f"Bridge not started - dropping event: {event.component_id}/{event.event_type}"
            )
            return
        try:
            # Thread-safe: schedule put_nowait in the event loop
            self._loop.call_soon_threadsafe(self._event_queue.put_nowait, event)
            logger.debug(f"Event queued: {event.component_id}/{event.event_type}")
        except Exception as e:
            logger.error(f"Error queuing event: {e}", exc_info=True)
    async def start(self) -> None:
        """Start the event consumer loop."""
        if self._task is not None:
            logger.warning("Event bridge already running")
            return
        self._running = True
        self._loop = asyncio.get_running_loop()
        # Create asyncio.Queue (not queue.Queue!) - supports await
        self._event_queue = asyncio.Queue(maxsize=100)
        self._task = asyncio.create_task(self._consumer_loop())
        logger.info("Event bridge started (asyncio.Queue mode)")
    async def stop(self) -> None:
        """Stop the event consumer loop."""
        if self._task is None:
            return
        self._running = False
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            logger.info("Event bridge cancelled")
        finally:
            self._task = None
            self._event_queue = None
            self._loop = None
    async def _consumer_loop(self) -> None:
        """
        Consumer loop that processes events from the queue.
        Runs in the FastAPI asyncio event loop.
        Uses asyncio.Queue.get() with timeout - proper async/await, NO busy waiting!
        The coroutine genuinely suspends until an event arrives.
        """
        try:
            logger.info("Event consumer loop started")
            while self._running:
                try:
                    # await on asyncio.Queue.get() - suspends coroutine, no CPU waste!
                    # Timeout to periodically check _running flag
                    event = await asyncio.wait_for(
                        self._event_queue.get(),
                        timeout=1.0  # Wake every second to check if we should stop
                    )
                    logger.debug(
                        f"Processing event: {event.component_id}/{event.event_type}"
                    )
                    # Dispatch to handlers
                    if self._dispatcher:
                        await self._dispatcher(event)
                    # Mark task as done (for queue.join() if needed)
                    self._event_queue.task_done()
                except asyncio.TimeoutError:
                    # No event for 1 second - normal, just check _running
                    continue
                except Exception as e:
                    logger.error(
                        f"Error processing event: {e}",
                        exc_info=True
                    )
        except asyncio.CancelledError:
            logger.info("Event consumer loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in event consumer loop: {e}", exc_info=True)
