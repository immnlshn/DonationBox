"""
Component Registry - manages GPIO components.
"""
import asyncio
import logging
from typing import Dict, List, Optional
from gpiozero import Device
from gpiozero.pins.mock import MockFactory

from .base import GPIOComponent
from .event import GPIOEvent

logger = logging.getLogger(__name__)


class ComponentRegistry:
    """
    Central registry for GPIO components.

    Manages component lifecycle and dispatches events to Core event queue.
    """

    def __init__(self):
        self._components: Dict[str, GPIOComponent] = {}
        self._event_queue: Optional[asyncio.Queue] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self.enabled: bool = False

    def initialize(self, enable_gpio: bool, pin_factory: str = "mock") -> None:
        """
        Initialize GPIO hardware.

        Args:
            enable_gpio: Whether GPIO is enabled
            pin_factory: Pin factory to use ("mock", "lgpio", "rpigpio", or "native")
        """
        self.enabled = enable_gpio
        factory = pin_factory.strip().lower()

        if not self.enabled or factory == "mock":
            Device.pin_factory = MockFactory()
            logger.info("GPIO initialized with MockFactory")
        elif factory == "lgpio":
            # Modern approach using /dev/gpiochip0 (Raspberry Pi OS Bookworm+)
            try:
                from gpiozero.pins.lgpio import LGPIOFactory
                Device.pin_factory = LGPIOFactory(chip=0)
                logger.info("GPIO initialized with LGPIOFactory (chip0)")
            except ImportError:
                logger.error("lgpio not installed. Install with: pip install lgpio")
                raise
        elif factory == "rpigpio":
            # RPi.GPIO library (older, but stable)
            try:
                from gpiozero.pins.rpigpio import RPiGPIOFactory
                Device.pin_factory = RPiGPIOFactory()
                logger.info("GPIO initialized with RPiGPIOFactory")
            except ImportError:
                logger.error("RPi.GPIO not installed. Install with: pip install RPi.GPIO")
                raise
        else:
            # Native/sysfs (deprecated on newer systems)
            try:
                from gpiozero.pins.native import NativeFactory
                Device.pin_factory = NativeFactory()
                logger.info("GPIO initialized with NativeFactory (legacy sysfs)")
            except Exception as e:
                logger.error(f"NativeFactory failed: {e}")
                raise

    def register(self, component: GPIOComponent) -> None:
        """
        Register a GPIO component.

        Args:
            component: GPIOComponent instance to register

        Raises:
            ValueError: If component with same ID already registered
        """
        if component.component_id in self._components:
            raise ValueError(f"Component {component.component_id} already registered")

        # Set the event callback to push events into Core queue
        component.set_event_callback(self._queue_event)

        self._components[component.component_id] = component
        logger.info(f"Component registered: {component.component_id}")

    def unregister(self, component_id: str) -> bool:
        """
        Unregister a GPIO component.

        Args:
            component_id: ID of the component to unregister

        Returns:
            True if component was unregistered, False if not found
        """
        component = self._components.pop(component_id, None)
        if component is None:
            logger.warning(f"Cannot unregister: Component {component_id} not found")
            return False

        # Stop component if it's running
        if component.is_started:
            try:
                component.stop()
            except Exception as e:
                logger.error(
                    f"Error stopping component {component_id}: {e}",
                    exc_info=True
                )

        logger.info(f"Component unregistered: {component_id}")
        return True

    def list_components(self) -> List[str]:
        """
        Get list of registered component IDs.

        Returns:
            List of component IDs
        """
        return list(self._components.keys())

    def get_component(self, component_id: str) -> GPIOComponent:
        """
        Get a component by ID.

        Args:
            component_id: ID of the component

        Returns:
            The component instance

        Raises:
            KeyError: If component not found
        """
        return self._components[component_id]

    def get_event_queue(self):
        """
        Get the event queue.

        Returns:
            asyncio.Queue for GPIO events, or None if not started
        """
        return self._event_queue

    def _queue_event(self, event: GPIOEvent) -> None:
        """
        Queue an event from a GPIO callback thread.

        Thread-safe: Uses call_soon_threadsafe to schedule put_nowait
        in the asyncio loop from a different thread.

        Args:
            event: GPIO event to queue
        """
        if self._loop is None or self._event_queue is None:
            logger.warning(
                f"Registry not started - dropping event: {event.component_id}/{event.event_type}"
            )
            return

        try:
            # Thread-safe: schedule put_nowait in the event loop
            self._loop.call_soon_threadsafe(self._event_queue.put_nowait, event)
            logger.debug(f"Event queued: {event.component_id}/{event.event_type}")
        except Exception as e:
            logger.error(f"Error queuing event: {e}", exc_info=True)

    async def start(self, event_queue: asyncio.Queue) -> None:
        """
        Start all components and initialize event dispatching.

        Args:
            event_queue: Event queue from Core to dispatch events to
        """
        # Store queue and loop reference for thread-safe event dispatching
        self._event_queue = event_queue
        self._loop = asyncio.get_running_loop()
        logger.info("Registry initialized with Core event queue")

        # Start all registered components
        for component_id, component in self._components.items():
            try:
                component.start()
                logger.info(f"Component started: {component_id}")
            except Exception as e:
                logger.error(
                    f"Failed to start component {component_id}: {e}",
                    exc_info=True
                )

    async def stop(self) -> None:
        """Stop all components."""
        # Stop all components
        for component_id, component in self._components.items():
            try:
                component.stop()
                logger.info(f"Component stopped: {component_id}")
            except Exception as e:
                logger.error(
                    f"Error stopping component {component_id}: {e}",
                    exc_info=True
                )

        # Clear queue and loop reference
        self._event_queue = None
        self._loop = None


# Global registry instance
registry = ComponentRegistry()
