"""Failure mode architecture — detection, injection, and FMEA data."""

import random
from dataclasses import dataclass, field
from typing import Any


# ------------------------------------
# System State
# ------------------------------------

@dataclass
class SystemState:
    """Mutable system state for failure-aware simulation."""

    confidence: float = 0.9
    sensor_noise: float = 0.0
    brake_efficiency: float = 1.0
    override_count: int = 0
    logs: list[dict[str, Any]] = field(default_factory=list)


# ------------------------------------
# Failure Injection
# ------------------------------------

def inject_failures(state: SystemState) -> None:
    """Stochastically degrade system state to simulate drift and sensor issues."""
    if random.random() < 0.1:
        state.sensor_noise += 0.1
    if random.random() < 0.05:
        state.brake_efficiency -= 0.1


# ------------------------------------
# Failure Detection
# ------------------------------------

def detect_failures(
    state: SystemState, confidence: float, risk: float
) -> dict[str, bool]:
    """Produce observable failure signals from current system state."""
    signals: dict[str, bool] = {}
    signals["low_confidence"] = confidence < 0.5
    signals["confidence_variance"] = state.sensor_noise > 0.3
    signals["override_spike"] = state.override_count > 3
    signals["brake_degradation"] = state.brake_efficiency < 0.7

    # Coupled failure detection
    signals["compound_risk"] = (
        signals["low_confidence"] and signals["brake_degradation"]
    )
    return signals


# ------------------------------------
# FMEA Data
# ------------------------------------

@dataclass(frozen=True)
class FMEAEntry:
    """A single row in the Failure Mode and Effects Analysis table."""

    id: str
    domain: str
    failure_mode: str
    mechanism: str
    effect: str
    signal: str
    severity: int
    occurrence: int
    detectability: int
    rpn: int
    control: str
    action_trigger: str


FMEA_TABLE: list[FMEAEntry] = [
    FMEAEntry("F1", "Perception", "Sensor Occlusion", "Dust / blockage",
              "Missed human detection", "Confidence variance up",
              9, 6, 4, 216, "Redundant sensors", "Variance threshold exceeded"),
    FMEAEntry("F2", "Decision", "Overconfidence Error", "Misclassification w/ high confidence",
              "Unsafe motion", "High confidence + override",
              10, 5, 6, 300, "Confidence gating", "Override spike"),
    FMEAEntry("F3", "Actuation", "Brake Delay", "Mechanical lag",
              "Collision risk", "Stop distance up",
              10, 4, 5, 200, "Independent braking", "Distance threshold"),
    FMEAEntry("F4", "Human", "Overtrust", "Automation complacency",
              "Late intervention", "Low override frequency",
              8, 7, 6, 336, "Intent display", "No overrides in high-risk zone"),
    FMEAEntry("F5", "Coordination", "Command Conflict", "AI vs human input",
              "Oscillation / stall", "Rapid state switching",
              9, 5, 5, 225, "Arbitration layer", "Conflict detection"),
    FMEAEntry("F6", "Drift", "Model Drift", "Environment change",
              "Reduced accuracy", "Near-miss trend up",
              9, 6, 7, 378, "Drift detection", "Trend threshold"),
    FMEAEntry("F7", "Data", "Data Loss", "Logging failure",
              "Blind operation", "Missing logs",
              10, 3, 8, 240, "Redundant logging", "Data gap"),
    FMEAEntry("F8", "Edge Case", "Unknown Scenario", "Novel condition",
              "Unstable response", "Confidence collapse",
              9, 4, 7, 252, "Safe fallback", "Confidence drop"),
]


def rpn_severity(rpn: int) -> str:
    """Classify RPN into action severity levels."""
    if rpn >= 300:
        return "immediate_redesign"
    if rpn >= 150:
        return "active_control"
    return "monitor"
