"""
Unit tests for GPIO feature - ComponentRegistry and event routing.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock

from backend.gpio.registry import ComponentRegistry
from backend.gpio.base import GPIOComponent
from backend.gpio.event import GPIOEvent


class MockComponent(GPIOComponent):
    """Mock component for testing."""

    def __init__(self, component_id: str):
        super().__init__(component_id)
        self.start_called = False
        self.stop_called = False

    def start(self) -> None:
        self._started = True
        self.start_called = True

    def stop(self) -> None:
        self._started = False
        self.stop_called = True


class TestComponentRegistry:
    """Test ComponentRegistry functionality."""

    def test_register_component(self):
        """Test registering a component."""
        registry = ComponentRegistry()
        registry.initialize(enable_gpio=False, pin_factory="mock")

        component = MockComponent("test_button_1")
        registry.register(component)

        assert "test_button_1" in registry.list_components()
        assert len(registry.list_components()) == 1

    def test_register_duplicate_raises_error(self):
        """Test that registering duplicate component ID raises error."""
        registry = ComponentRegistry()
        registry.initialize(enable_gpio=False, pin_factory="mock")

        component1 = MockComponent("test_button")
        component2 = MockComponent("test_button")

        registry.register(component1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(component2)

    def test_unregister_component(self):
        """Test unregistering a component."""
        registry = ComponentRegistry()
        registry.initialize(enable_gpio=False, pin_factory="mock")

        component = MockComponent("test_button_1")
        registry.register(component)

        result = registry.unregister("test_button_1")

        assert result is True
        assert "test_button_1" not in registry.list_components()

    def test_unregister_nonexistent_returns_false(self):
        """Test unregistering non-existent component returns False."""
        registry = ComponentRegistry()
        registry.initialize(enable_gpio=False, pin_factory="mock")

        result = registry.unregister("nonexistent")

        assert result is False

    def test_get_component(self):
        """Test getting a component by ID."""
        registry = ComponentRegistry()
        registry.initialize(enable_gpio=False, pin_factory="mock")

        component = MockComponent("test_button")
        registry.register(component)

        retrieved = registry.get_component("test_button")

        assert retrieved is component

    def test_list_components(self):
        """Test listing all registered components."""
        registry = ComponentRegistry()
        registry.initialize(enable_gpio=False, pin_factory="mock")

        component1 = MockComponent("button_1")
        component2 = MockComponent("button_2")
        component3 = MockComponent("sensor_1")

        registry.register(component1)
        registry.register(component2)
        registry.register(component3)

        components = registry.list_components()

        assert len(components) == 3
        assert "button_1" in components
        assert "button_2" in components
        assert "sensor_1" in components


class TestEventRouting:
    """Test event routing through registry."""

    @pytest.mark.asyncio
    async def test_component_event_handler(self):
        """Test that component-specific event handlers work."""
        registry = ComponentRegistry()
        registry.initialize(enable_gpio=False, pin_factory='mock')

        component = MockComponent("test_button")

        handler = AsyncMock()
        component.on("button_pressed", handler)

        registry.register(component)
        await registry.start()

        # Trigger event
        component.emit_event("button_pressed", {"pin": 17})

        # Wait for processing
        await asyncio.sleep(0.2)

        # Handler should have been called
        handler.assert_called_once()
        call_args = handler.call_args[0][0]
        assert isinstance(call_args, GPIOEvent)
        assert call_args.component_id == "test_button"
        assert call_args.event_type == "button_pressed"

        await registry.stop()

    @pytest.mark.asyncio
    async def test_multiple_handlers_on_component(self):
        """Test multiple handlers on same component."""
        registry = ComponentRegistry()
        registry.initialize(enable_gpio=False, pin_factory='mock')

        component = MockComponent("test_button")

        handler1 = AsyncMock()
        handler2 = AsyncMock()

        component.on("button_pressed", handler1)
        component.on("button_pressed", handler2)

        registry.register(component)
        await registry.start()

        component.emit_event("button_pressed", {})
        await asyncio.sleep(0.2)

        handler1.assert_called_once()
        handler2.assert_called_once()

        await registry.stop()

    @pytest.mark.asyncio
    async def test_component_isolation(self):
        """Test that events on one component don't trigger handlers on another."""
        registry = ComponentRegistry()
        registry.initialize(enable_gpio=False, pin_factory='mock')

        button1 = MockComponent("button1")
        button2 = MockComponent("button2")

        handler1 = AsyncMock()
        handler2 = AsyncMock()

        button1.on("button_pressed", handler1)
        button2.on("button_pressed", handler2)

        registry.register(button1)
        registry.register(button2)

        await registry.start()

        # Trigger event only on button1
        button1.emit_event("button_pressed", {})
        await asyncio.sleep(0.2)

        # Only handler1 should be called
        handler1.assert_called_once()
        handler2.assert_not_called()

        await registry.stop()

    @pytest.mark.asyncio
    async def test_component_lifecycle(self):
        """Test that components are started/stopped with registry."""
        registry = ComponentRegistry()
        registry.initialize(enable_gpio=False, pin_factory='mock')

        component = MockComponent("test_button")
        registry.register(component)

        assert component.start_called is False

        await registry.start()

        assert component.start_called is True
        assert component.is_started is True

        await registry.stop()

        assert component.stop_called is True
        assert component.is_started is False


class TestGPIOEvent:
    """Test GPIOEvent data structure."""

    def test_event_creation(self):
        """Test creating a GPIO event."""
        event = GPIOEvent(
            component_id="button_1",
            event_type="button_pressed",
            data={"pin": 17}
        )

        assert event.component_id == "button_1"
        assert event.event_type == "button_pressed"
        assert event.data["pin"] == 17
        assert event.timestamp is not None

    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = GPIOEvent(
            component_id="sensor_1",
            event_type="sensor_trigger",
            data={"value": 42}
        )

        event_dict = event.to_dict()

        assert event_dict["component_id"] == "sensor_1"
        assert event_dict["event_type"] == "sensor_trigger"
        assert event_dict["data"]["value"] == 42
        assert "timestamp" in event_dict
        assert isinstance(event_dict["timestamp"], str)
