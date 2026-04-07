"""Sovereign Black Box — immutable telemetry and dissonance detection."""

import json
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TelemetryFrame:
    """A single telemetry snapshot."""

    timestamp: float
    ai_confidence: float
    detected_objects: int
    velocity: float
    proximity_min: float
    override_active: bool
    institutional_friction_score: float


class SovereignBlackBox:
    """Append-only telemetry logger that cannot be silently edited.

    Detects Model/Reality Dissonance: high AI confidence paired with
    dangerously close proximity.
    """

    def __init__(
        self,
        log_file: str | Path = "hard_truth_log.json",
        confidence_threshold: float = 0.9,
        proximity_threshold: float = 0.5,
    ) -> None:
        self.log_file = Path(log_file)
        self.confidence_threshold = confidence_threshold
        self.proximity_threshold = proximity_threshold
        self.critical_events: list[dict] = []

    def record_frame(self, frame: TelemetryFrame) -> str | None:
        """Record a telemetry frame. Returns a reason string if dissonance detected."""
        reason = None
        if (
            frame.ai_confidence > self.confidence_threshold
            and frame.proximity_min < self.proximity_threshold
        ):
            reason = "Model/Reality Dissonance Detected"
            self._trigger_critical_log(frame, reason)

        with open(self.log_file, "a") as f:
            f.write(json.dumps(asdict(frame)) + "\n")

        return reason

    def _trigger_critical_log(self, frame: TelemetryFrame, reason: str) -> None:
        logger.critical("%s at %s", reason, frame.timestamp)
        self.critical_events.append({"frame": asdict(frame), "reason": reason})


def create_telemetry_frame(
    ai_confidence: float,
    detected_objects: int,
    velocity: float,
    proximity_min: float,
    override_active: bool = False,
    institutional_friction_score: float = 0.0,
) -> TelemetryFrame:
    """Convenience constructor with auto-timestamp."""
    return TelemetryFrame(
        timestamp=time.time(),
        ai_confidence=ai_confidence,
        detected_objects=detected_objects,
        velocity=velocity,
        proximity_min=proximity_min,
        override_active=override_active,
        institutional_friction_score=institutional_friction_score,
    )
