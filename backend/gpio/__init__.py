"""
GPIO Feature Package.

Manages GPIO components with event-driven architecture and asyncio integration.
"""
from .registry import registry, ComponentRegistry
from .base import GPIOComponent
from .event import GPIOEvent
from .bridge import EventBridge

__all__ = [
    "registry",
    "ComponentRegistry",
    "GPIOComponent",
    "GPIOEvent",
    "EventBridge",
]
