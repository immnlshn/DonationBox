import logging

from backend.gpio import GPIOEvent
from backend.gpio.components.gpio_button import GPIOButton
from backend.services.websocket import websocket_service

logger = logging.getLogger(__name__)

class VoteButton(GPIOButton):
    """
    GPIO button for voting functionality.

    When pressed, it triggers a vote action in the system.
    """

    async def handle_release(self, event: GPIOEvent) -> None:
        """Not needed for voting buttons."""
        pass

    async def handle_press(self, event: GPIOEvent) -> None:
      logger.info(f"Button pressed for option {self._representing_option}")
      await websocket_service.broadcast_json({
          "type": "vote_cast",
          "option": self._representing_option,
      })

    def __init__(
        self,
        component_id: str,
        representing_option: int,
        pin: int,
        bounce_time: float = 0.2,
        pull_up: bool = True,
    ):
        """
        Initialize VoteButton.

        Args:
            component_id: Unique identifier for this button
            pin: GPIO pin number (BCM numbering)
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