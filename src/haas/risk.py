"""Risk field modeling — dynamic risk computation."""

import numpy as np

from .entities import Human, Machine


def compute_risk(
    human: Human,
    machine: Machine,
    latency: float = 0.1,
    fatigue_score: float = 0.0,
) -> float:
    """Compute dynamic risk score between a human and a machine.

    Base: Risk = (relative_velocity / distance) * (1 + latency), clamped to [0, 1].

    When fatigue_score > 0, risk is amplified by the human's degraded reaction
    capacity. A fatigued operator cannot evade as quickly, so the effective risk
    is higher even at the same distance and velocity.

    Fatigue multiplier: 1 + fatigue_score * 0.05 (up to 1.5x at fatigue=10).
    """
    distance = np.linalg.norm(human.position - machine.position)
    relative_velocity = np.linalg.norm(human.velocity - machine.velocity)

    if distance == 0:
        distance = 0.001

    risk = (relative_velocity / distance) * (1 + latency)

    # TAF integration: fatigue amplifies risk
    if fatigue_score > 0:
        fatigue_mult = 1 + fatigue_score * 0.05
        risk *= fatigue_mult

    return min(risk, 1.0)


def compute_confidence(confidence: float, sensor_noise: float) -> float:
    """Compute effective AI confidence after sensor noise degradation."""
    return max(0.0, confidence - sensor_noise)
