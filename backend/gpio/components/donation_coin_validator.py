"""
Donation Coin Validator component.
Handles coin insertions and creates donations.
"""
import asyncio
import logging
import time
from datetime import datetime

from backend.gpio import GPIOEvent
from backend.gpio.components.gpio_coin_validator import GPIOCoinValidator
from backend.core.container import AppContainer
from backend.core.decorators import event
from backend.schemas.websocket import MoneyInsertedMessage, MoneyInsertedData

logger = logging.getLogger(__name__)


class DonationCoinValidator(GPIOCoinValidator):
    """
    Coin Validator for donation functionality.

    Maps pulse counts to Euro amounts and creates donations for active vote.

    Hardware Configuration assumptions (HX-916):
    - P1 = 1: 1 pulse = 10 Cents
    - P2 = 2: 2 pulses = 20 Cents
    - P3 = 3: 3 pulses = 50 Cents
    - P4 = 4: 4 pulses = 1 Euro
    - P5 = 5: 5 pulses = 2 Euro

    Business logic is implemented using @event decorated methods.
    Dependencies are automatically injected based on method signature.
    """

    def __init__(
        self,
        component_id: str,
        pin: int,
        pulse_timeout: float = 0.3,
        bounce_time: float = 0.01,
        puls_to_cent: dict = None,
        debounce_seconds: float = 2.0,
    ):
        """
        Initialize DonationCoinValidator.

        Args:
            component_id: Unique identifier for this validator
            pin: GPIO pin number (BCM numbering)
            pulse_timeout: Timeout in seconds to consider coin sequence complete
            bounce_time: Debounce time in seconds
            cents_per_pulse: Amount in cents per pulse (default: 100 = 1 EUR)
            debounce_seconds: Minimum time between donation state updates in seconds
        """
        super().__init__(
            component_id=component_id,
            pin=pin,
            pulse_timeout=pulse_timeout,
            bounce_time=bounce_time,
        )
        if not puls_to_cent:
            puls_to_cent = {1: 10, 2: 20, 3: 50, 4: 100, 5: 200}
        self._puls_to_cent = puls_to_cent
        self._debounce_seconds = debounce_seconds
        self._pending_donation_task = None

    @event("coin_inserted")
    async def handle_coin_insertion(
        self,
        gpio_event: GPIOEvent,
        container: AppContainer
    ) -> None:
        """
        Handle coin insertion - creates donation for active vote.

        This runs in AsyncIO event loop scope (NOT in GPIO thread).
        Called by EventHandler after event is read from queue.
        Container is injected via dependency injection.

        Args:
            gpio_event: GPIO event from the queue
            container: Application container (injected by EventHandler)
        """
        pulse_count = gpio_event.data.get("pulse_count", 0)
        amount_cents = self._puls_to_cent.get(pulse_count, 0)
        logger.info(f"Coin inserted with {pulse_count} pulses, amount: {amount_cents} cents")

        # Always increment money counter with timestamp
        current_total = container.state_store.get("total_donation_cents", {}).get("amount", 0) if isinstance(container.state_store.get("total_donation_cents", {}), dict) else 0
        new_total = current_total + amount_cents
        current_timestamp = time.time()
        container.state_store.set("total_donation_cents", {
            "amount": new_total,
            "timestamp": current_timestamp
        })
        logger.info(f"Total donation amount updated: {new_total} cents (added {amount_cents} cents)")

        # Broadcast money_inserted event via WebSocket
        try:
            websocket_service = container.get_websocket_service()
            message = MoneyInsertedMessage(
                data=MoneyInsertedData(
                    amount_cents=amount_cents,
                    total_amount_cents=new_total,
                    timestamp=datetime.fromtimestamp(current_timestamp)
                )
            )
            await websocket_service.broadcast_json(message.model_dump(mode='json'))
            logger.debug(f"WebSocket broadcast sent for money_inserted: amount={amount_cents}, total={new_total}")
        except Exception as e:
            logger.error(f"Failed to broadcast money_inserted: {e}", exc_info=True)

        # Cancel any pending donation task (new coin resets the timer)
        if self._pending_donation_task and not self._pending_donation_task.done():
            logger.debug("Cancelling previous donation task - new coin inserted")
            self._pending_donation_task.cancel()

        # Schedule donation creation after debounce period
        self._pending_donation_task = asyncio.create_task(
            self._create_donation_after_debounce(container)
        )
        logger.debug(f"Scheduled donation creation in {self._debounce_seconds} seconds")

    async def _create_donation_after_debounce(self, container: AppContainer) -> None:
        """
        Wait for debounce period, then try to create donation with accumulated amount.

        This gets cancelled if a new coin is inserted before the timer expires.
        DonationService will check if both money and category are present and not expired.

        Args:
            container: Application container
        """
        try:
            # Wait for debounce period
            await asyncio.sleep(self._debounce_seconds)

            # If we get here, no new coin was inserted - try to process donation
            logger.info("Debounce period expired - attempting to process donation")

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
        except asyncio.CancelledError:
            # Task was cancelled because a new coin was inserted
            logger.debug("Donation creation cancelled - new coin inserted before timeout")
            raise

