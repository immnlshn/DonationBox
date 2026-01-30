"""
Component Registry - manages GPIO components.
"""
import logging
from typing import Dict, List
from gpiozero import Device
from gpiozero.pins.mock import MockFactory

from .base import GPIOComponent
from .event import GPIOEvent
from .bridge import EventBridge

logger = logging.getLogger(__name__)


class ComponentRegistry:
    """
    Central registry for GPIO components.

    Manages component lifecycle and event routing.
    Components register themselves here and get started/stopped automatically.
    """

    def __init__(self):
        self._components: Dict[str, GPIOComponent] = {}
        self._bridge = EventBridge()
        self._bridge.set_dispatcher(self._dispatch_event)
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

        # Set the event callback to push events into bridge
        component.set_event_callback(self._bridge.queue_event)

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

    async def start(self) -> None:
        """Start all components and the event bridge."""
        # Start event bridge
        await self._bridge.start()

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
        """Stop all components and the event bridge."""
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

        # Stop event bridge
        await self._bridge.stop()

    async def _dispatch_event(self, event: GPIOEvent) -> None:
        """
        Dispatch an event to the component's registered handlers.
        Called by the event bridge in the asyncio loop.

        Args:
            event: GPIO event to dispatch
        """
        # Get component
        component = self._components.get(event.component_id)
        if component is None:
            logger.warning(
                f"Cannot dispatch event: Component {event.component_id} not found"
            )
            return

        # Get handlers from component
        handlers = component.get_handlers(event.event_type)

        if not handlers:
            logger.debug(
                f"No handlers registered for {event.component_id}/{event.event_type}"
            )
            return

        logger.debug(
            f"Dispatching {event.component_id}/{event.event_type} to {len(handlers)} handler(s)"
        )

        # Call all handlers
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    f"Error in handler for {event.component_id}/{event.event_type}: {e}",
                    exc_info=True
                )


# Global registry instance
registry = ComponentRegistry()
