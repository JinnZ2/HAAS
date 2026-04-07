"""Event logging for the safety feedback loop."""

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EventLog:
    """Append-only event log for safety telemetry."""

    events: list[dict[str, Any]] = field(default_factory=list)

    def log(self, event: Any) -> None:
        self.events.append({
            "timestamp": time.time(),
            "event": event,
        })
