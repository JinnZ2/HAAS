"""Core entities: Human, Machine, and AIController."""

from dataclasses import dataclass

import numpy as np


@dataclass
class Human:
    """A human operator in the interaction field."""

    id: str
    position: np.ndarray
    velocity: np.ndarray
    state: str = "normal"  # normal, distracted, fatigued


@dataclass
class Machine:
    """An automated machine (forklift, conveyor, robot)."""

    id: str
    position: np.ndarray
    velocity: np.ndarray
    max_speed: float
    state: str = "normal"  # normal, slowed, stopped


@dataclass
class AIController:
    """AI decision layer with bounded autonomy."""

    confidence: float
    decision: str  # move, slow, stop

    def evaluate(self, risk: float) -> str:
        if risk > 0.7 or self.confidence < 0.5:
            self.decision = "stop"
        elif risk > 0.4:
            self.decision = "slow"
        else:
            self.decision = "move"
        return self.decision
