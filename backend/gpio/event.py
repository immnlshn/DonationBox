"""
GPIO Event data structure.
"""
from dataclasses import dataclass, field
from typing import Any, Dict
from datetime import datetime


@dataclass
class GPIOEvent:
    """
    Represents a GPIO event from a component.
    """
    component_id: str
    event_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "component_id": self.component_id,
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }
