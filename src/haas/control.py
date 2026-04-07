"""Control logic — multi-layer safety decisions."""

import numpy as np

from .entities import Machine


def apply_control(machine: Machine, decision: str) -> None:
    """Apply a control decision to a machine, mutating its state."""
    if decision == "stop":
        machine.velocity = np.array([0.0, 0.0])
        machine.state = "stopped"
    elif decision == "slow":
        machine.velocity = machine.velocity * 0.5
        machine.state = "slowed"
    else:
        machine.state = "normal"


def control_decision(
    confidence: float, risk: float, signals: dict[str, bool]
) -> str:
    """Failure-aware control decision incorporating detection signals."""
    if signals.get("compound_risk"):
        return "STOP"
    if confidence < 0.5 or risk > 0.7:
        return "STOP"
    if risk > 0.4:
        return "SLOW"
    return "MOVE"


def check_alerts(
    risk: float,
    confidence: float,
    override_count: int,
    drift_index: float,
    override_threshold: int = 3,
    drift_limit: float = 0.5,
) -> list[str]:
    """Return a list of active alert strings based on real-time signals."""
    alerts: list[str] = []
    if risk > 0.7:
        alerts.append("CRITICAL")
    if confidence < 0.5:
        alerts.append("LOW_CONFIDENCE")
    if override_count > override_threshold:
        alerts.append("HUMAN_AI_MISMATCH")
    if drift_index > drift_limit:
        alerts.append("DRIFT_RECALIBRATION")
    return alerts
