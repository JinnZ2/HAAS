"""HAAS-Q: Integrated Human-Automation-AI Safety & Quality Framework."""

__version__ = "0.1.0"

from .control import apply_control, check_alerts, control_decision
from .entities import AIController, Human, Machine
from .event_log import EventLog
from .failures import FMEA_TABLE, FMEAEntry, SystemState, detect_failures, inject_failures
from .handshake import check_handshake_requirement
from .risk import compute_confidence, compute_risk
from .simulation import (
    run_basic_simulation,
    run_failure_simulation,
    simulate_failure_step,
    simulate_step,
)
from .telemetry import SovereignBlackBox, TelemetryFrame, create_telemetry_frame

__all__ = [
    "AIController",
    "EventLog",
    "FMEA_TABLE",
    "FMEAEntry",
    "Human",
    "Machine",
    "SovereignBlackBox",
    "SystemState",
    "TelemetryFrame",
    "apply_control",
    "check_alerts",
    "check_handshake_requirement",
    "compute_confidence",
    "compute_risk",
    "control_decision",
    "create_telemetry_frame",
    "detect_failures",
    "inject_failures",
    "run_basic_simulation",
    "run_failure_simulation",
    "simulate_failure_step",
    "simulate_step",
]
