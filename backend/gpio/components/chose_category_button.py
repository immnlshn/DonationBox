import logging

from backend.gpio import GPIOEvent
from backend.gpio.components.gpio_button import GPIOButton
from backend.core.container import AppContainer
from backend.core.decorators import event

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
        """
        super().__init__(
            component_id=component_id,
            pin=pin,
            bounce_time=bounce_time,
            pull_up=pull_up,
        )
        self._representing_option = representing_option
        self._amount_cents = amount_cents

    @event("button_pressed")
    async def handle_press(self, gpio_event: GPIOEvent, container: AppContainer) -> None:
        """
        Handle button press - creates donation for active vote.

        This runs in AsyncIO event loop scope (NOT in GPIO thread).
        Called by EventHandler after event is read from queue.
        Container is injected via dependency injection.

        Args:
            gpio_event: GPIO event from the queue
            container: Application container (injected by EventHandler)
        """
        logger.info(f"Vote button {self._representing_option} pressed on pin {self.pin} at time {gpio_event.timestamp}")