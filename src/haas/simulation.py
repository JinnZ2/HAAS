"""Simulation runners — basic and failure-aware modes."""

import random
from typing import Any

import numpy as np

from .control import apply_control, control_decision
from .entities import AIController, Human, Machine
from .event_log import EventLog
from .failures import SystemState, detect_failures, inject_failures
from .risk import compute_confidence, compute_risk


# ------------------------------------
# Basic Simulation
# ------------------------------------

def simulate_step(
    human: Human, machine: Machine, ai: AIController, log: EventLog
) -> tuple[float, str]:
    """Run one step of the basic control loop."""
    risk = compute_risk(human, machine)
    decision = ai.evaluate(risk)
    apply_control(machine, decision)

    log.log({
        "risk": risk,
        "decision": decision,
        "human_pos": human.position.tolist(),
        "machine_pos": machine.position.tolist(),
    })
    return risk, decision


def run_basic_simulation(steps: int = 20) -> EventLog:
    """Run the basic simulation with default entities."""
    human = Human("H1", np.array([0.0, 0.0]), np.array([0.1, 0.0]))
    machine = Machine("F1", np.array([5.0, 0.0]), np.array([-0.5, 0.0]), max_speed=1.0)
    ai = AIController(confidence=0.8, decision="move")
    log = EventLog()

    for _ in range(steps):
        simulate_step(human, machine, ai, log)
        machine.position = machine.position + machine.velocity
        human.position = human.position + human.velocity

    return log


# ------------------------------------
# Failure-Aware Simulation
# ------------------------------------

def simulate_failure_step(state: SystemState) -> dict[str, Any]:
    """Run one step of the failure-aware simulation."""
    inject_failures(state)

    risk = random.uniform(0, 1)
    confidence = compute_confidence(state.confidence, state.sensor_noise)

    signals = detect_failures(state, confidence, risk)
    decision = control_decision(confidence, risk, signals)

    entry = {
        "risk": risk,
        "confidence": confidence,
        "signals": signals,
        "decision": decision,
    }
    state.logs.append(entry)
    return entry


def run_failure_simulation(steps: int = 50) -> SystemState:
    """Run the failure-aware simulation and return the final state."""
    state = SystemState()
    for _ in range(steps):
        simulate_failure_step(state)
    return state
