import logging
import asyncio
from typing import Optional
from gpiozero import Device
from gpiozero.pins.mock import MockFactory
from gpiozero.pins.native import NativeFactory

logger = logging.getLogger(__name__)


class GPIOService:
    """
    GPIO service with background task support for FastAPI.
    Handles GPIO initialization and background monitoring/processing.
    """

    def __init__(self):
        self.enabled: bool = False
        self._task: Optional[asyncio.Task] = None
        self._running: bool = False

    def initialize(self, enable_gpio: bool, pin_factory: str = "mock"):
        """
        Initialize the GPIO service with the given configuration.

        Args:
            enable_gpio: Whether GPIO is enabled
            pin_factory: Pin factory to use ("mock" or "native")
        """
        self.enabled = enable_gpio
        factory = pin_factory.strip().lower()

        if not self.enabled or factory == "mock":
            Device.pin_factory = MockFactory()
            logger.info("gpiozero initialized with MockFactory")
        else:
            Device.pin_factory = NativeFactory()
            logger.info("gpiozero initialized with NativeFactory")

    async def start_background_task(self):
        """Start the background GPIO monitoring task."""
        if self._task is not None:
            logger.warning("GPIO background task already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._gpio_loop())
        logger.info("GPIO background task started")

    async def stop_background_task(self):
        """Stop the background GPIO monitoring task."""
        if self._task is None:
            return

        self._running = False
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            logger.info("GPIO background task cancelled")
        self._task = None

    async def _gpio_loop(self):
        """
        Background loop for GPIO processing.
        Override this method or add your GPIO logic here.
        """
        try:
            counter = 0
            while self._running:
                # Placeholder for GPIO monitoring logic
                # Example: check sensors, handle button presses, etc.
                if self.enabled:
                    # Your GPIO logic here
                    logger.debug("GPIO loop iteration")

                    # Example: Send status updates to WebSocket clients
                    # Uncomment the following lines to enable broadcasting:
                    # from services.websocket.WebSocketService import websocket_service
                    # counter += 1
                    # if counter % 50 == 0:  # Every 5 seconds (if sleep is 0.1s)
                    #     await websocket_service.broadcast_json({
                    #         "type": "gpio_status",
                    #         "data": {
                    #             "enabled": self.enabled,
                    #             "counter": counter
                    #         }
                    #     })

                await asyncio.sleep(0.1)  # Adjust interval as needed
        except asyncio.CancelledError:
            logger.info("GPIO loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in GPIO loop: {e}", exc_info=True)


# Global GPIO service instance
gpio_service = GPIOService()
