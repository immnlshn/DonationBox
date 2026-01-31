"""
Core Event Handler - Processes events from the event queue.

Handles GPIO and other events with proper DB sessions and service calls.
"""

import asyncio
import logging

from backend.gpio.event import GPIOEvent
from backend.core.container import AppContainer

logger = logging.getLogger(__name__)


class EventHandler:
    """
    Event handler that processes events from the Core event queue.

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

                    # Process event with its own DB session
                    await self._process_event(event)

                    # Mark task done
                    self.event_queue.task_done()

                except asyncio.TimeoutError:
                    # No event - just continue to check for cancellation
                    continue
                except Exception as e:
                    logger.error(f"Error processing event: {e}", exc_info=True)

        except asyncio.CancelledError:
            logger.info("Event handler cancelled")
            raise
        except Exception as e:
            logger.error(f"Fatal error in event handler: {e}", exc_info=True)
            raise

    async def _process_event(self, event: GPIOEvent):
        """
        Process a single event with its own DB session.

        Args:
            event: Event to process
        """
        # Create dedicated DB session for this event
        async with self.container.sessionmaker() as session:
            try:
                # Route to appropriate handler based on component_id
                if event.component_id.startswith("button_"):
                    await self._handle_vote_button(session, event)
                else:
                    logger.warning(f"Unknown component type: {event.component_id}")

                # Commit transaction
                await session.commit()
                logger.debug(f"Event processed successfully: {event.component_id}")

            except Exception as e:
                # Rollback on error
                await session.rollback()
                logger.error(
                    f"Error handling event {event.component_id}/{event.event_type}: {e}",
                    exc_info=True
                )
                raise

    async def _handle_vote_button(self, session, event: GPIOEvent):
        """
        Handle vote button press events.

        Creates a donation for the active vote and broadcasts update.

        Args:
            session: Database session
            event: GPIO event
        """
        # Only handle press events
        if event.event_type != "pressed":
            return

        # Extract option from component_id (e.g., "button_1" -> option 1)
        try:
            option = int(event.component_id.split("_")[1])
        except (IndexError, ValueError):
            logger.error(f"Cannot extract option from component_id: {event.component_id}")
            return

        logger.info(f"Vote button pressed: option={option}")

        # Get donation service with this session
        donation_service = self.container.create_donation_service(session)

        # Create donation
        try:
            # 10 cents per button press
            amount_cents = 10

            donation = await donation_service.create_donation_for_active_vote(
                category_id=option,
                amount_cents=amount_cents,
            )

            if donation:
                logger.info(f"Donation created: id={donation.id}, category={option}, amount={amount_cents}")
            else:
                logger.warning(f"No donation created - no active vote")

        except Exception as e:
            logger.error(f"Failed to create donation for option {option}: {e}", exc_info=True)
            raise
