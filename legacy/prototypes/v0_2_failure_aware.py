# ARCHIVED — HAAS-Q legacy artifact. Not imported, not executed, not maintained.
# Kept verbatim so the original claim can be diffed against what replaced it.
# Precedence carries: this text is the first statement of the ideas below.
# Corrections belong in the superseding module, plus a row in legacy/README.md.
#
# Source:       Framework.md lines 882-951 — "2. PYTHON SYSTEM (Failure-Aware Upgrade)"
# Origin:       c5ba2bf  Create Framework.md
# Superseded:   896a12b  Extract Framework.md into a complete Python package
# Replaced by:  src/haas/failures.py, risk.py, control.py, simulation.py
# Status:       SUPERSEDED — refined, not falsified.
#
# ----- verbatim excerpt begins -----

import numpy as np
import random

class SystemState:
    def __init__(self):
        self.confidence = 0.9
        self.sensor_noise = 0.0
        self.brake_efficiency = 1.0
        self.override_count = 0
        self.logs = []

state = SystemState()

def inject_failures(state):
    # Simulate drift or sensor issues
    if random.random() < 0.1:
        state.sensor_noise += 0.1
    
    if random.random() < 0.05:
        state.brake_efficiency -= 0.1

def compute_confidence(state):
    return max(0.0, state.confidence - state.sensor_noise)

def detect_failures(state, confidence, risk):
    signals = {}

    signals["low_confidence"] = confidence < 0.5
    signals["confidence_variance"] = state.sensor_noise > 0.3
    signals["override_spike"] = state.override_count > 3
    signals["brake_degradation"] = state.brake_efficiency < 0.7

    # Coupled failure detection
    signals["compound_risk"] = (
        signals["low_confidence"] and
        signals["brake_degradation"]
    )

    return signals

def control_decision(confidence, risk, signals):
    if signals["compound_risk"]:
        return "STOP"

    if confidence < 0.5 or risk > 0.7:
        return "STOP"
    elif risk > 0.4:
        return "SLOW"
    return "MOVE"

def simulate_step(state):
    inject_failures(state)

    risk = random.uniform(0, 1)
    confidence = compute_confidence(state)

    signals = detect_failures(state, confidence, risk)
    decision = control_decision(confidence, risk, signals)

    state.logs.append({
        "risk": risk,
        "confidence": confidence,
        "signals": signals,
        "decision": decision
    })

for _ in range(50):
    simulate_step(state)

print(state.logs[-5:])
