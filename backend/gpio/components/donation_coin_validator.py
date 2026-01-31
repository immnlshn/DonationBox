"""
Donation Coin Validator component.
Handles coin insertions and creates donations.
"""
import logging

from backend.gpio import GPIOEvent
from backend.gpio.components.gpio_coin_validator import GPIOCoinValidator
from backend.core.container import AppContainer
from backend.core.decorators import event

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
    ):
        """
        Initialize DonationCoinValidator.

        Args:
            component_id: Unique identifier for this validator
            pin: GPIO pin number (BCM numbering)
            pulse_timeout: Timeout in seconds to consider coin sequence complete
            bounce_time: Debounce time in seconds
            cents_per_pulse: Amount in cents per pulse (default: 100 = 1 EUR)
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


        # TODO: Implement donation creation logic here
        # This would be similar to ChooseCategoryButton's handle_press method
        # Example:
        # donation_service = container.donation_service()
        # await donation_service.create_donation_from_coin(amount_cents)

        # For now, just log the event
        logger.info(f"Would create donation with amount: {amount_cents} cents")
