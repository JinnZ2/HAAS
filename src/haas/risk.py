"""Risk field modeling — dynamic risk computation."""

import numpy as np

from .entities import Human, Machine


def compute_risk(human: Human, machine: Machine, latency: float = 0.1) -> float:
    """Compute dynamic risk score between a human and a machine.

    Risk = (relative_velocity / distance) * (1 + latency), clamped to [0, 1].
    """
    distance = np.linalg.norm(human.position - machine.position)
    relative_velocity = np.linalg.norm(human.velocity - machine.velocity)

    if distance == 0:
        distance = 0.001

    risk = (relative_velocity / distance) * (1 + latency)
    return min(risk, 1.0)


def compute_confidence(confidence: float, sensor_noise: float) -> float:
    """Compute effective AI confidence after sensor noise degradation."""
    return max(0.0, confidence - sensor_noise)
