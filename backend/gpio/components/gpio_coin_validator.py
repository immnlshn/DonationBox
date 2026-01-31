"""
GPIO Coin Validator component.
Handles pulse counting from coin validator (e.g., HX-916).
"""
import logging
from gpiozero import DigitalInputDevice
from typing import Optional
from time import time
import asyncio

from backend.gpio.base import GPIOComponent

logger = logging.getLogger(__name__)


class GPIOCoinValidator(GPIOComponent):
    """
    GPIO Coin Validator component.

    Counts pulses from a coin validator device (e.g., HX-916).
    The coin validator sends pulses (LOW signals) based on the coin value.

    Hardware Configuration:
    - HX-916 uses NO (Normally Open) connection
    - Signals are sent to GND (LOW)
    - pull_up=True is required
    - P1 setting on device determines pulses per coin (e.g., 1 pulse = 1 EUR)

    After a configurable timeout without pulses, a "coin_inserted" event
    is emitted with the total pulse count.

    Example:
        validator = GPIOCoinValidator(
            component_id="coin_validator_1",
            pin=23,
            pulse_timeout=0.3
        )

        # In handler:
        @event("coin_inserted")
        async def handle_coin(self, event: GPIOEvent):
            pulse_count = event.data["pulse_count"]
            # Handle coin insertion
    """

    def __init__(
        self,
        component_id: str,
        pin: int,
        pulse_timeout: float = 0.3,
        bounce_time: float = 0.01,
    ):
        """
        Initialize Coin Validator.

        Args:
            component_id: Unique identifier for this validator
            pin: GPIO pin number (BCM numbering)
            pulse_timeout: Timeout in seconds to consider coin sequence complete
            bounce_time: Debounce time in seconds (filters very short noise)
        """
        super().__init__(component_id)
        self.pin = pin
        self.pulse_timeout = pulse_timeout
        self.bounce_time = bounce_time
        self._input_device: Optional[DigitalInputDevice] = None

        # Pulse counting state
        self._pulse_count = 0
        self._last_pulse_time = 0
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False

    def start(self) -> None:
        """Setup the coin validator and start monitoring."""
        if self._started:
            logger.warning(f"CoinValidator {self.component_id} already started")
            return

        try:
            # Setup GPIO with pull_up=True (HX-916 switches to GND)
            self._input_device = DigitalInputDevice(
                self.pin,
                pull_up=True,
                bounce_time=self.bounce_time,
            )

            # Register pulse detection callback (triggers on falling edge = LOW signal)
            self._input_device.when_activated = self._on_pulse_detected

            self._started = True
            self._running = True

            # Start the monitoring task
            loop = asyncio.get_event_loop()
            self._monitor_task = loop.create_task(self._monitor_pulse_sequence())

            logger.info(
                f"CoinValidator {self.component_id} started on pin {self.pin} "
                f"(pulse_timeout={self.pulse_timeout}s, bounce_time={self.bounce_time}s)"
            )
        except Exception as e:
            logger.error(
                f"Failed to start CoinValidator {self.component_id}: {e}",
                exc_info=True
            )
            raise

    def stop(self) -> None:
        """Cleanup coin validator resources."""
        if not self._started:
            return

        try:
            self._running = False

            # Cancel monitoring task
            if self._monitor_task and not self._monitor_task.done():
                self._monitor_task.cancel()
                # Don't wait for cancellation here to avoid blocking

            # Cleanup GPIO
            if self._input_device:
                self._input_device.close()
                self._input_device = None

            self._started = False
            logger.info(f"CoinValidator {self.component_id} stopped")
        except Exception as e:
            logger.error(
                f"Error stopping CoinValidator {self.component_id}: {e}",
                exc_info=True
            )

    def _on_pulse_detected(self) -> None:
        """
        gpiozero callback when a pulse is detected (input goes LOW).
        Runs in gpiozero's callback thread.
        """
        self._pulse_count += 1
        self._last_pulse_time = time()
        logger.debug(
            f"CoinValidator {self.component_id}: Pulse detected "
            f"(total: {self._pulse_count})"
        )

    async def _monitor_pulse_sequence(self) -> None:
        """
        Monitor pulse sequences and emit coin_inserted event when complete.
        Runs in asyncio event loop.
        """
        logger.info(f"CoinValidator {self.component_id}: Monitoring started")

        try:
            while self._running:
                # Check if we have pulses and timeout has passed
                if self._pulse_count > 0:
                    time_since_last_pulse = time() - self._last_pulse_time

                    if time_since_last_pulse > self.pulse_timeout:
                        # Coin sequence complete!
                        pulse_count = self._pulse_count

                        logger.info(
                            f"CoinValidator {self.component_id}: "
                            f"Coin insertion complete with {pulse_count} pulse(s)"
                        )

                        # Emit coin_inserted event
                        self.emit_event(
                            event_type="coin_inserted",
                            data={
                                "pin": self.pin,
                                "pulse_count": pulse_count,
                            }
                        )

                        # Reset for next coin
                        self._pulse_count = 0

                # Sleep briefly before next check
                await asyncio.sleep(0.05)

        except asyncio.CancelledError:
            logger.info(f"CoinValidator {self.component_id}: Monitoring cancelled")
            raise
        except Exception as e:
            logger.error(
                f"CoinValidator {self.component_id}: Error in monitoring: {e}",
                exc_info=True
            )
