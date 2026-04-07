"""Simulation runners — basic, failure-aware, and unified modes."""

import random
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .control import apply_control, check_alerts, control_decision
from .dashboard import DashboardSnapshot, print_dashboard
from .entities import AIController, Human, Machine
from .event_log import EventLog
from .failures import SystemState, detect_failures, inject_failures
from .protections import ProtectionState, Violation, evaluate_protections, format_violation
from .risk import compute_confidence, compute_risk
from .store import EventStore
from .zones import ZoneLevel, ZoneMap


# ------------------------------------
# Basic Simulation (preserved)
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
# Failure-Aware Simulation (preserved)
# ------------------------------------

def simulate_failure_step(state: SystemState) -> dict[str, Any]:
    """Run one step of the failure-aware simulation (random risk, no spatial)."""
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


# ------------------------------------
# Unified Simulation
# ------------------------------------

@dataclass
class SimConfig:
    """Configuration for a unified simulation run."""

    steps: int = 100
    dt: float = 0.1
    enable_failures: bool = True
    enable_zones: bool = True
    enable_dashboard: bool = False
    dashboard_delay: float = 0.15
    store: EventStore | None = None


@dataclass
class SimResult:
    """Full result from a unified simulation run."""

    log: EventLog
    state: SystemState
    human: Human
    machine: Machine
    snapshots: list[DashboardSnapshot] = field(default_factory=list)
    all_violations: list[Violation] = field(default_factory=list)


def unified_step(
    human: Human,
    machine: Machine,
    ai: AIController,
    state: SystemState,
    zone_map: ZoneMap | None,
    log: EventLog,
    step: int,
    dt: float = 0.1,
    store: EventStore | None = None,
    pstate: ProtectionState | None = None,
    institutional_friction: float = 0.0,
) -> DashboardSnapshot:
    """Run one unified step: spatial risk + failure injection + zones + protections + logging."""
    ts = time.time()

    # 1. Failure injection (degrades state over time)
    inject_failures(state)

    # 2. Compute real spatial risk
    risk = compute_risk(human, machine)

    # 3. Effective confidence after sensor degradation
    confidence = compute_confidence(state.confidence, state.sensor_noise)
    ai.confidence = confidence

    # 4. Zone classification
    zone_level = ZoneLevel.GREEN
    zone_str = "GREEN"
    if zone_map is not None:
        machine_zone = zone_map.classify(machine.position)
        human_zone = zone_map.classify(human.position)
        # Use the most restrictive of the two
        zone_level = max(machine_zone, human_zone, key=lambda z: {
            ZoneLevel.GREEN: 0, ZoneLevel.YELLOW: 1, ZoneLevel.RED: 2
        }[z])
        zone_str = zone_level.value.upper()

    # 5. Failure signals
    signals = detect_failures(state, confidence, risk)

    # 6. Control decision (failure-aware)
    decision = control_decision(confidence, risk, signals)

    # 7. Zone override — RED zone forces STOP regardless
    if zone_level == ZoneLevel.RED:
        decision = "STOP"
    elif zone_level == ZoneLevel.YELLOW and decision == "MOVE":
        decision = "SLOW"

    # 8. Apply control to machine
    apply_control(machine, decision.lower())

    # 9. Zone speed limit enforcement
    if zone_map is not None:
        speed_mult = zone_map.speed_limit(machine.position)
        current_speed = float(np.linalg.norm(machine.velocity))
        if current_speed > machine.max_speed * speed_mult and speed_mult > 0:
            scale = (machine.max_speed * speed_mult) / current_speed
            machine.velocity = machine.velocity * scale

    # 10. Move entities
    machine.position = machine.position + machine.velocity * dt
    human.position = human.position + human.velocity * dt

    # 11. Alerts
    alerts = check_alerts(
        risk=risk,
        confidence=confidence,
        override_count=state.override_count,
        drift_index=state.sensor_noise,
    )

    # 11b. Protection matrix evaluation
    violations: list[Violation] = []
    violation_strs: list[str] = []
    if pstate is not None:
        proximity = float(np.linalg.norm(human.position - machine.position))
        machine_speed = float(np.linalg.norm(machine.velocity))

        # Update rolling counters
        pstate.alert_count_recent += len(alerts)
        if decision in ("STOP", "stop"):
            pstate.stop_count_recent += 1
        if risk > 0.7 and decision not in ("STOP", "stop"):
            pstate.near_miss_count_recent += 1

        violations = evaluate_protections(
            risk=risk,
            confidence=confidence,
            decision=decision,
            brake_efficiency=state.brake_efficiency,
            sensor_noise=state.sensor_noise,
            proximity=proximity,
            velocity=machine_speed,
            institutional_friction=institutional_friction,
            pstate=pstate,
        )
        violation_strs = [format_violation(v) for v in violations]

    # 12. Log
    log.log({
        "risk": risk,
        "confidence": confidence,
        "decision": decision,
        "zone": zone_str,
        "signals": signals,
        "human_pos": human.position.tolist(),
        "machine_pos": machine.position.tolist(),
        "alerts": alerts,
        "violations": [v.threat_id for v in violations],
    })

    state.logs.append({
        "risk": risk,
        "confidence": confidence,
        "signals": signals,
        "decision": decision,
    })

    # 13. Persistent store
    if store is not None:
        store.record_event(
            risk=risk,
            confidence=confidence,
            decision=decision,
            zone=zone_str,
            human_pos=human.position.tolist(),
            machine_pos=machine.position.tolist(),
        )
        store.record_signals(signals, timestamp=ts)
        store.record_state(
            mode=decision,
            sensor_noise=state.sensor_noise,
            brake_efficiency=state.brake_efficiency,
            timestamp=ts,
        )
        for v in violations:
            store.record_violation(
                threat_id=v.threat_id,
                target=v.target.value,
                source=v.source.value,
                severity=v.severity.value,
                description=v.description,
                values=v.values,
                timestamp=ts,
            )

    # 14. Build snapshot
    snap = DashboardSnapshot(
        step=step,
        risk=risk,
        confidence=confidence,
        decision=decision,
        zone=zone_str,
        signals=signals,
        sensor_noise=state.sensor_noise,
        brake_efficiency=state.brake_efficiency,
        human_pos=human.position.tolist(),
        machine_pos=machine.position.tolist(),
        alerts=alerts,
        violations=violation_strs,
    )
    return snap, violations


def run_unified_simulation(
    config: SimConfig | None = None,
    zone_map: ZoneMap | None = None,
    human: Human | None = None,
    machine: Machine | None = None,
    institutional_friction: float = 0.0,
) -> SimResult:
    """Run a unified simulation combining spatial, failure, zone, and protection logic.

    Optionally displays a live terminal dashboard and persists to SQLite.
    """
    cfg = config or SimConfig()

    h = human or Human("H1", np.array([0.0, 0.0]), np.array([0.1, 0.0]))
    m = machine or Machine("F1", np.array([5.0, 0.0]), np.array([-0.5, 0.0]), max_speed=1.0)
    ai = AIController(confidence=0.9, decision="move")
    state = SystemState()
    log = EventLog()
    pstate = ProtectionState()
    snapshots: list[DashboardSnapshot] = []
    all_violations: list[Violation] = []

    for step in range(cfg.steps):
        snap, violations = unified_step(
            human=h,
            machine=m,
            ai=ai,
            state=state,
            zone_map=zone_map if cfg.enable_zones else None,
            log=log,
            step=step,
            dt=cfg.dt,
            store=cfg.store,
            pstate=pstate,
            institutional_friction=institutional_friction,
        )
        snapshots.append(snap)
        all_violations.extend(violations)

        if cfg.enable_dashboard:
            print_dashboard(snap)
            time.sleep(cfg.dashboard_delay)

    return SimResult(
        log=log, state=state, human=h, machine=m,
        snapshots=snapshots, all_violations=all_violations,
    )
