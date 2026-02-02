"""
Abstract GPIO Button base class.
Handles all GPIO logic - subclasses only need to implement business logic.
"""
import logging

from gpiozero import Button
from typing import Optional

from backend.gpio.base import GPIOComponent
from backend.gpio.event import GPIOEvent

logger = logging.getLogger(__name__)


class GPIOButton(GPIOComponent):
    """
    Abstract base class for GPIO buttons.

    Handles all GPIO setup, callbacks, and cleanup.
    Subclasses only need to implement the business logic in handle_press().

    Example:
        class MyButton(GPIOButton):
            async def handle_press(self, event: GPIOEvent):
                # Your business logic here
                await some_service.do_something()
    """

    def __init__(
        self,
        component_id: str,
        pin: int,
        bounce_time: float = 0.2,
        pull_up: bool = True,
    ):
        """
        Initialize GPIO button.

        Args:
            component_id: Unique identifier for this button
            pin: GPIO pin number (BCM numbering)
            bounce_time: Debounce time in seconds
            pull_up: Use pull-up resistor (True) or pull-down (False)
        """
        super().__init__(component_id)
        self.pin = pin
        self.bounce_time = bounce_time
        self.pull_up = pull_up
        self._button: Optional[Button] = None

        # Note: Event handlers are registered via @event decorator in subclasses

    def start(self) -> None:
        """Setup the button and register callbacks."""
        if self._started:
            logger.warning(f"Button {self.component_id} already started")
            return

        try:
            self._button = Button(
                self.pin,
                bounce_time=self.bounce_time,
                pull_up=self.pull_up,
            )

            # Register gpiozero callbacks
            self._button.when_pressed = self._on_pressed
            self._button.when_released = self._on_released

            self._started = True
            logger.info(
                f"GPIOButton {self.component_id} started on pin {self.pin} "
                f"(bounce_time={self.bounce_time}s, pull_up={self.pull_up})"
            )
        except Exception as e:
            logger.error(
                f"Failed to start button {self.component_id}: {e}",
                exc_info=True
            )
            raise

    def stop(self) -> None:
        """Cleanup button resources."""
        if not self._started:
            return

        try:
            if self._button:
                self._button.close()
                self._button = None

            self._started = False
            logger.info(f"GPIOButton {self.component_id} stopped")
        except Exception as e:
            logger.error(
                f"Error stopping button {self.component_id}: {e}",
                exc_info=True
            )

    def _on_pressed(self) -> None:
        """
        gpiozero callback when button is pressed.
        Runs in gpiozero's callback thread.
        """
        logger.debug(f"Button {self.component_id} pressed")
        self.emit_event(
            event_type="button_pressed",
            data={"pin": self.pin}
        )

    def _on_released(self) -> None:
        """
        gpiozero callback when button is released.
        Runs in gpiozero's callback thread.
        """
        logger.debug(f"Button {self.component_id} released")
        self.emit_event(
            event_type="button_released",
            data={"pin": self.pin}
        )