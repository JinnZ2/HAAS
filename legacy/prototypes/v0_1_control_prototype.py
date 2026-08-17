# ARCHIVED — HAAS-Q legacy artifact. Not imported, not executed, not maintained.
# Kept verbatim so the original claim can be diffed against what replaced it.
# Precedence carries: this text is the first statement of the ideas below.
# Corrections belong in the superseding module, plus a row in legacy/README.md.
#
# Source:       Framework.md lines 266-378 — "A. Python Monitoring / Control Prototype"
# Origin:       c5ba2bf  Create Framework.md
# Superseded:   896a12b  Extract Framework.md into a complete Python package
# Replaced by:  src/haas/entities.py, risk.py, control.py, event_log.py, simulation.py
# Status:       SUPERSEDED — refined, not falsified.
#
# ----- verbatim excerpt begins -----

import numpy as np
from dataclasses import dataclass, field
import time

# ----------------------------
# Core Entities
# ----------------------------

@dataclass
class Human:
    id: str
    position: np.array
    velocity: np.array
    state: str = "normal"  # normal, distracted, fatigued

@dataclass
class Machine:
    id: str
    position: np.array
    velocity: np.array
    max_speed: float
    state: str = "normal"  # normal, slowed, stopped

@dataclass
class AIController:
    confidence: float
    decision: str  # move, slow, stop

    def evaluate(self, risk):
        if risk > 0.7 or self.confidence < 0.5:
            self.decision = "stop"
        elif risk > 0.4:
            self.decision = "slow"
        else:
            self.decision = "move"
        return self.decision

# ----------------------------
# Risk Model
# ----------------------------

def compute_risk(human, machine, latency=0.1):
    distance = np.linalg.norm(human.position - machine.position)
    relative_velocity = np.linalg.norm(human.velocity - machine.velocity)

    if distance == 0:
        distance = 0.001

    risk = (relative_velocity / distance) * (1 + latency)
    return min(risk, 1.0)

# ----------------------------
# Control Logic
# ----------------------------

def apply_control(machine, decision):
    if decision == "stop":
        machine.velocity = np.array([0.0, 0.0])
        machine.state = "stopped"
    elif decision == "slow":
        machine.velocity *= 0.5
        machine.state = "slowed"
    else:
        machine.state = "normal"

# ----------------------------
# Feedback Logging
# ----------------------------

@dataclass
class EventLog:
    events: list = field(default_factory=list)

    def log(self, event):
        self.events.append({
            "timestamp": time.time(),
            "event": event
        })

# ----------------------------
# Simulation Loop
# ----------------------------

def simulate_step(human, machine, ai, log):
    risk = compute_risk(human, machine)
    decision = ai.evaluate(risk)

    apply_control(machine, decision)

    log.log({
        "risk": risk,
        "decision": decision,
        "human_pos": human.position.tolist(),
        "machine_pos": machine.position.tolist()
    })

    return risk, decision

# ----------------------------
# Example Run
# ----------------------------

human = Human("H1", np.array([0.0, 0.0]), np.array([0.1, 0.0]))
machine = Machine("F1", np.array([5.0, 0.0]), np.array([-0.5, 0.0]), max_speed=1.0)
ai = AIController(confidence=0.8, decision="move")
log = EventLog()

for _ in range(20):
    risk, decision = simulate_step(human, machine, ai, log)
    machine.position += machine.velocity
    human.position += human.velocity

print(log.events)
