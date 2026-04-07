"""HAAS-Q: Integrated Human-Automation-AI Safety & Quality Framework."""

__version__ = "0.1.0"

from .audit import (
    Audit,
    Maturity,
    ThreatAssessment,
    blank_questionnaire,
    create_audit,
    create_audit_from_responses,
    overall_rating,
)
from .control import apply_control, check_alerts, control_decision
from .dashboard import DashboardSnapshot, format_dashboard, show_summary
from .entities import AIController, Human, Machine
from .event_log import EventLog
from .failures import FMEA_TABLE, FMEAEntry, SystemState, detect_failures, inject_failures
from .handshake import check_handshake_requirement
from .protections import (
    THREAT_REGISTRY,
    Entity,
    ProtectionState,
    Severity,
    Threat,
    Violation,
    evaluate_protections,
    format_violation,
    get_threat,
    get_threats_for,
    get_threats_from,
    get_threats_targeting,
)
from .risk import compute_confidence, compute_risk
from .simulation import (
    SimConfig,
    SimResult,
    run_basic_simulation,
    run_failure_simulation,
    run_unified_simulation,
    simulate_failure_step,
    simulate_step,
    unified_step,
)
from .store import EventStore
from .telemetry import SovereignBlackBox, TelemetryFrame, create_telemetry_frame
from .zones import Zone, ZoneLevel, ZoneMap

__all__ = [
    "AIController",
    "Audit",
    "DashboardSnapshot",
    "Entity",
    "EventLog",
    "EventStore",
    "FMEA_TABLE",
    "FMEAEntry",
    "Human",
    "Machine",
    "Maturity",
    "ProtectionState",
    "Severity",
    "SimConfig",
    "SimResult",
    "SovereignBlackBox",
    "SystemState",
    "THREAT_REGISTRY",
    "TelemetryFrame",
    "Threat",
    "ThreatAssessment",
    "Violation",
    "Zone",
    "ZoneLevel",
    "ZoneMap",
    "blank_questionnaire",
    "create_audit",
    "create_audit_from_responses",
    "apply_control",
    "check_alerts",
    "check_handshake_requirement",
    "compute_confidence",
    "compute_risk",
    "control_decision",
    "create_telemetry_frame",
    "detect_failures",
    "evaluate_protections",
    "format_dashboard",
    "format_violation",
    "get_threat",
    "get_threats_for",
    "get_threats_from",
    "get_threats_targeting",
    "overall_rating",
    "inject_failures",
    "run_basic_simulation",
    "run_failure_simulation",
    "run_unified_simulation",
    "show_summary",
    "simulate_failure_step",
    "simulate_step",
    "unified_step",
]
