import asyncio
import logging
import time
from datetime import datetime

from backend.gpio import GPIOEvent
from backend.gpio.components.gpio_button import GPIOButton
from backend.core.container import AppContainer
from backend.core.decorators import event
from backend.schemas.websocket import CategoryChosenMessage, CategoryChosenData

logger = logging.getLogger(__name__)


class ChooseCategoryButton(GPIOButton):
    """
    GPIO button for voting functionality.

    Business logic is implemented using @event decorated methods.
    Dependencies are automatically injected based on method signature.
    """

    def __init__(
            self,
            component_id: str,
            representing_option: int,
            pin: int,
            amount_cents: int = 10,
            bounce_time: float = 0.2,
            pull_up: bool = True,
            debounce_seconds: float = 2.0,
    ):
        """
        Initialize VoteButton.

        Args:
            component_id: Unique identifier for this button
            representing_option: Option number this button represents
            pin: GPIO pin number (BCM numbering)
            amount_cents: Amount in cents per button press
            bounce_time: Debounce time in seconds
            pull_up: Use pull-up resistor (True) or pull-down (False)
            debounce_seconds: Minimum time between category changes in seconds
        """
        super().__init__(
            component_id=component_id,
            pin=pin,
            bounce_time=bounce_time,
            pull_up=pull_up,
        )
        self._representing_option = representing_option
        self._amount_cents = amount_cents
        self._debounce_seconds = debounce_seconds

    @event("button_pressed")
    async def handle_press(self, gpio_event: GPIOEvent, container: AppContainer) -> None:
        """
        Handle button press - sets category after debounce.

        Multiple buttons can be pressed, but only the last one wins (via global task cancellation).

        Args:
            gpio_event: GPIO event from the queue
            container: Application container (injected by EventHandler)
        """
        logger.info(f"Button pressed for category {self._representing_option} on pin {self.pin}")

        # Cancel any pending task from ANY button (last button wins)
        pending_task = container.state_store.get("pending_category_task", None)
        if pending_task and not pending_task.done():
            logger.debug(f"Cancelling previous category task - button {self._representing_option} pressed")
            pending_task.cancel()

        # Schedule category update after debounce period
        task = asyncio.create_task(
            self._update_category_after_debounce(container, self._representing_option)
        )
        container.state_store.set("pending_category_task", task)
        logger.debug(f"Scheduled category {self._representing_option} in {self._debounce_seconds}s")

    async def _update_category_after_debounce(self, container: AppContainer, category_option: int) -> None:
        """
        Wait for debounce period, then update the chosen category in state store with timestamp.

        Gets cancelled if another button is pressed before the timer expires.
        Tries to process donation afterwards (DonationService checks timestamps).

        Args:
            container: Application container
            category_option: Category option number (1-based button number)
        """
        try:
            # Wait for debounce period
            await asyncio.sleep(self._debounce_seconds)

            # Convert 1-based button number to 0-based array index
            position = category_option - 1

            # Debounce complete - set category position with timestamp
            logger.info(f"Debounce complete - button {category_option} -> position {position}")
            current_timestamp = time.time()
            container.state_store.set("chosen_category", {
                "position": position,
                "timestamp": current_timestamp
            })

            # Broadcast category_chosen event via WebSocket
            try:
                async with container.sessionmaker() as db:
                    websocket_service = container.get_websocket_service()
                    voting_service = container.create_voting_service(db)

                    # Get active vote to resolve position -> category
                    active_vote = await voting_service.get_active_vote()
                    if active_vote and 0 <= position < len(active_vote.categories):
                        category = active_vote.categories[position]

                        message = CategoryChosenMessage(
                            data=CategoryChosenData(
                                category_id=category.id,
                                category_name=category.name,
                                timestamp=datetime.fromtimestamp(current_timestamp)
                            )
                        )
                        await websocket_service.broadcast_json(message.model_dump(mode='json'))
                        logger.debug(f"WebSocket broadcast sent for category_chosen: button={category_option}, position={position}, category_id={category.id}")
                    else:
                        logger.warning(f"Cannot broadcast category_chosen: button={category_option}, position={position} invalid or no active vote")
            except Exception as e:
                logger.error(f"Failed to broadcast category_chosen: {e}", exc_info=True)

            # Try to process donation (DonationService will validate timestamps)
            await self._try_process_donation(container)

        except asyncio.CancelledError:
            logger.debug(f"Category {category_option} cancelled - another button pressed")
            raise

    async def _try_process_donation(self, container: AppContainer) -> None:
        """
        Try to process a donation by calling DonationService.

        DonationService will check if both category and money are present and not expired.

        Args:
            container: Application container
        """
        try:
            async with container.sessionmaker() as db:
                donation_service = container.create_donation_service(db)
                donation = await donation_service.process_pending_donation_from_state(
                    state_store=container.state_store
                )

                if donation:
                    logger.info(f"Donation processed successfully: donation_id={donation.id}")
                else:
                    logger.debug("Donation not processed - waiting for other component")

        except ValueError as e:
            # Category no longer valid for current vote (e.g., after vote update)
            logger.error(f"Cannot process donation - invalid category: {e}")
            # Clear the invalid category from state
            container.state_store.delete("chosen_category")
            logger.info("Cleared invalid category from state")
        except Exception as e:
            logger.error(f"Failed to process donation: {e}", exc_info=True)
            raise

