"""Protection matrix — every entity protected from every other entity.

The five protection domains:
  - Human: physical safety, cognitive protection, trust calibration
  - AI: operational integrity, input quality, fair accountability
  - Automation: mechanical integrity, command validity, maintenance
  - Institution: governance integrity, compliance, process fidelity
  - Company: liability containment, operational continuity, reputation

Each directional pair (A ← B) defines: what can B do to harm A,
how do we detect it, and what control prevents or contains it.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Entity(Enum):
    HUMAN = "human"
    AI = "ai"
    AUTOMATION = "automation"
    INSTITUTION = "institution"
    COMPANY = "company"


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Threat:
    """A directional threat: source entity can harm target entity."""

    id: str
    target: Entity
    source: Entity
    name: str
    mechanism: str
    signal: str
    control: str


@dataclass
class Violation:
    """A detected protection violation at runtime."""

    threat_id: str
    target: Entity
    source: Entity
    severity: Severity
    description: str
    values: dict[str, Any] = field(default_factory=dict)


# ============================================================
# Complete threat registry: 20 directional pairs
# ============================================================

THREAT_REGISTRY: list[Threat] = [
    # ---- Human ← AI ----
    Threat("H_AI_1", Entity.HUMAN, Entity.AI,
           "Unsafe AI motion", "Bad inference drives machine toward human",
           "High confidence + close proximity", "Confidence gating + safe halt"),
    Threat("H_AI_2", Entity.HUMAN, Entity.AI,
           "Alarm flooding", "Excessive alerts degrade human attention",
           "Alert rate exceeds cognitive threshold", "Rate-limited tiered alerts"),
    Threat("H_AI_3", Entity.HUMAN, Entity.AI,
           "Cognitive overload", "AI exposes too much raw data to operator",
           "Decision latency increase in human response", "Graded information display"),

    # ---- Human ← Automation ----
    Threat("H_AUT_1", Entity.HUMAN, Entity.AUTOMATION,
           "Kinetic harm", "Collision, crushing, or impact",
           "Proximity breach + velocity > 0", "Physical zones + speed limits + e-stop"),
    Threat("H_AUT_2", Entity.HUMAN, Entity.AUTOMATION,
           "Entrapment", "Machine pins human against obstacle",
           "Human position between machine and boundary", "Geofenced exclusion zones"),

    # ---- Human ← Institution ----
    Threat("H_INS_1", Entity.HUMAN, Entity.INSTITUTION,
           "Ignored safety reports", "Near-miss reports filed but no corrective action",
           "Report-to-action delay exceeds threshold", "Auto-throttle on institutional friction"),
    Threat("H_INS_2", Entity.HUMAN, Entity.INSTITUTION,
           "Training theater", "Certification without operational competence",
           "Operator stress-test failure rate", "Operational competency stress-test gate"),
    Threat("H_INS_3", Entity.HUMAN, Entity.INSTITUTION,
           "Fatigue pressure", "Scheduling forces operation beyond safe limits",
           "Shift length + human entropy indicators", "Bio-kinetic state monitoring"),

    # ---- Human ← Company ----
    Threat("H_COM_1", Entity.HUMAN, Entity.COMPANY,
           "Throughput over safety", "Pressure to bypass safety for production KPIs",
           "Override frequency driven by schedule", "Safety metrics separated from performance metrics"),
    Threat("H_COM_2", Entity.HUMAN, Entity.COMPANY,
           "Understaffing", "Insufficient operators for safe coverage",
           "Operator-to-machine ratio below threshold", "Minimum staffing interlock"),

    # ---- AI ← Human ----
    Threat("AI_H_1", Entity.AI, Entity.HUMAN,
           "Override abuse", "Constant unnecessary overrides degrade AI learning",
           "Override frequency without safety justification", "Override logging + review trigger"),
    Threat("AI_H_2", Entity.AI, Entity.HUMAN,
           "Blame-shifting", "Operator blamed for incident when AI decision was correct",
           "Black box shows AI was within spec at incident time",
           "Sovereign Black Box forensic reconstruction"),

    # ---- AI ← Automation ----
    Threat("AI_AUT_1", Entity.AI, Entity.AUTOMATION,
           "Corrupted sensor input", "Mechanical drift feeds bad state data to AI",
           "Sensor disagreement or impossible values", "Redundant multi-modal sensing"),
    Threat("AI_AUT_2", Entity.AI, Entity.AUTOMATION,
           "Actuation mismatch", "Machine doesn't execute AI commands accurately",
           "Commanded state != observed state", "Closed-loop command verification"),

    # ---- AI ← Institution ----
    Threat("AI_INS_1", Entity.AI, Entity.INSTITUTION,
           "Threshold tampering", "Management raises confidence thresholds for throughput",
           "Threshold change without validation test", "Change control + rollback gate"),
    Threat("AI_INS_2", Entity.AI, Entity.INSTITUTION,
           "Suppressed stops", "Pressure to reduce AI-initiated stops",
           "Stop frequency declining while risk is stable", "Immutable stop-decision logging"),

    # ---- AI ← Company ----
    Threat("AI_COM_1", Entity.AI, Entity.COMPANY,
           "Domain overextension", "Deployed outside trained operating envelope",
           "Input distribution diverges from training baseline", "Domain boundary enforcement"),

    # ---- Automation ← Human ----
    Threat("AUT_H_1", Entity.AUTOMATION, Entity.HUMAN,
           "Operator misuse", "Exceeding rated loads or improper operation",
           "Load/speed exceeds mechanical spec", "Hard mechanical limits + interlock"),
    Threat("AUT_H_2", Entity.AUTOMATION, Entity.HUMAN,
           "Interlock bypass", "Human disables safety interlocks for convenience",
           "Interlock status change without authorization", "Physical interlock + tamper logging"),

    # ---- Automation ← AI ----
    Threat("AUT_AI_1", Entity.AUTOMATION, Entity.AI,
           "Unstable control commands", "AI oscillation causes mechanical stress",
           "Rapid state switching frequency", "Command rate limiting + smoothing"),
    Threat("AUT_AI_2", Entity.AUTOMATION, Entity.AI,
           "Exceeding mechanical envelope", "AI commands beyond physical capability",
           "Commanded velocity/acceleration > rated max", "Hard constraint layer on AI output"),

    # ---- Automation ← Institution ----
    Threat("AUT_INS_1", Entity.AUTOMATION, Entity.INSTITUTION,
           "Deferred maintenance", "Scheduled maintenance skipped for uptime",
           "Maintenance interval exceeded + performance degradation",
           "Maintenance interlock + auto-derating"),

    # ---- Automation ← Company ----
    Threat("AUT_COM_1", Entity.AUTOMATION, Entity.COMPANY,
           "Parts cost-cutting", "Inferior replacement parts reduce reliability",
           "Failure rate increase after maintenance", "Component performance baseline tracking"),

    # ---- Institution ← Human ----
    Threat("INS_H_1", Entity.INSTITUTION, Entity.HUMAN,
           "Falsified reports", "Operator submits inaccurate safety data",
           "Report data conflicts with sensor logs", "Cross-reference reports with black box"),

    # ---- Institution ← AI ----
    Threat("INS_AI_1", Entity.INSTITUTION, Entity.AI,
           "Opaque decision trail", "AI decisions not auditable",
           "Decision log gaps or missing confidence data",
           "Mandatory decision+confidence logging"),

    # ---- Institution ← Automation ----
    Threat("INS_AUT_1", Entity.INSTITUTION, Entity.AUTOMATION,
           "Unlogged failures", "Equipment failures without proper incident records",
           "Sensor fault without corresponding log entry", "Redundant logging paths"),

    # ---- Institution ← Company ----
    Threat("INS_COM_1", Entity.INSTITUTION, Entity.COMPANY,
           "Governance pressure", "Pressure to weaken safety standards for profit",
           "Standard revision without incident improvement", "Audit trigger on standard changes"),

    # ---- Company ← Human ----
    Threat("COM_H_1", Entity.COMPANY, Entity.HUMAN,
           "Negligence liability", "Operator safety violations create legal exposure",
           "Repeated violations by same operator", "Progressive accountability + retraining"),

    # ---- Company ← AI ----
    Threat("COM_AI_1", Entity.COMPANY, Entity.AI,
           "Autonomous liability", "AI decision causes harm without human in loop",
           "Incident during full-autonomy mode",
           "Bounded autonomy + mandatory human oversight in high-risk"),

    # ---- Company ← Automation ----
    Threat("COM_AUT_1", Entity.COMPANY, Entity.AUTOMATION,
           "Equipment damage cascade", "Single failure propagates to multiple systems",
           "Correlated fault signals across systems", "Isolation zones + independent shutoffs"),

    # ---- Company ← Institution ----
    Threat("COM_INS_1", Entity.COMPANY, Entity.INSTITUTION,
           "Compliance gap liability", "Governance failure exposes company to legal action",
           "Audit findings unresolved past deadline",
           "Escalation ladder with automatic notification"),
]


# Build lookup index
_THREATS_BY_ID: dict[str, Threat] = {t.id: t for t in THREAT_REGISTRY}
_THREATS_BY_PAIR: dict[tuple[Entity, Entity], list[Threat]] = {}
for _t in THREAT_REGISTRY:
    _THREATS_BY_PAIR.setdefault((_t.target, _t.source), []).append(_t)


def get_threat(threat_id: str) -> Threat | None:
    return _THREATS_BY_ID.get(threat_id)


def get_threats_for(target: Entity, source: Entity) -> list[Threat]:
    """All threats where `source` can harm `target`."""
    return _THREATS_BY_PAIR.get((target, source), [])


def get_threats_targeting(target: Entity) -> list[Threat]:
    """All threats that can harm `target`, from any source."""
    return [t for t in THREAT_REGISTRY if t.target == target]


def get_threats_from(source: Entity) -> list[Threat]:
    """All threats originating from `source`, toward any target."""
    return [t for t in THREAT_REGISTRY if t.source == source]


# ============================================================
# Runtime violation detection
# ============================================================

@dataclass
class ProtectionState:
    """Accumulates state needed to evaluate protection violations over time."""

    # Rolling counters (caller updates these each step)
    override_count_recent: int = 0
    alert_count_recent: int = 0
    stop_count_recent: int = 0
    near_miss_count_recent: int = 0
    report_action_delay: float = 0.0      # institutional friction (seconds/steps)
    maintenance_overdue: float = 0.0       # steps past due
    command_switches_recent: int = 0       # rapid state changes
    decision_log_gaps: int = 0             # missing log entries
    last_decision: str = ""


def evaluate_protections(
    risk: float,
    confidence: float,
    decision: str,
    brake_efficiency: float,
    sensor_noise: float,
    proximity: float,
    velocity: float,
    institutional_friction: float,
    pstate: ProtectionState,
) -> list[Violation]:
    """Evaluate all protection domains against current state.

    Returns a list of active violations, empty if everything is nominal.
    """
    violations: list[Violation] = []

    # -- Track command switching --
    if pstate.last_decision and decision != pstate.last_decision:
        pstate.command_switches_recent += 1
    pstate.last_decision = decision

    # ======== HUMAN protections ========

    # H_AI_1: Unsafe AI motion
    if confidence > 0.8 and proximity < 0.5 and velocity > 0.3:
        violations.append(Violation(
            "H_AI_1", Entity.HUMAN, Entity.AI, Severity.CRITICAL,
            "High AI confidence but dangerously close to human",
            {"confidence": confidence, "proximity": proximity, "velocity": velocity},
        ))

    # H_AI_2: Alarm flooding
    if pstate.alert_count_recent > 10:
        violations.append(Violation(
            "H_AI_2", Entity.HUMAN, Entity.AI, Severity.WARNING,
            "Alert rate exceeds cognitive threshold",
            {"alert_count_recent": pstate.alert_count_recent},
        ))

    # H_AUT_1: Kinetic harm
    if proximity < 0.3 and velocity > 0.1:
        violations.append(Violation(
            "H_AUT_1", Entity.HUMAN, Entity.AUTOMATION, Severity.CRITICAL,
            "Proximity breach with machine in motion",
            {"proximity": proximity, "velocity": velocity},
        ))

    # H_INS_1: Ignored safety reports
    if institutional_friction > 7.0:
        violations.append(Violation(
            "H_INS_1", Entity.HUMAN, Entity.INSTITUTION, Severity.WARNING,
            "Institutional friction score dangerously high",
            {"institutional_friction": institutional_friction},
        ))

    # H_COM_1: Throughput over safety
    if pstate.override_count_recent > 5 and risk > 0.4:
        violations.append(Violation(
            "H_COM_1", Entity.HUMAN, Entity.COMPANY, Severity.WARNING,
            "Override pattern suggests throughput pressure",
            {"override_count": pstate.override_count_recent, "risk": risk},
        ))

    # ======== AI protections ========

    # AI_H_1: Override abuse
    if pstate.override_count_recent > 5 and risk < 0.3:
        violations.append(Violation(
            "AI_H_1", Entity.AI, Entity.HUMAN, Severity.WARNING,
            "Excessive overrides without safety justification",
            {"override_count": pstate.override_count_recent, "risk": risk},
        ))

    # AI_AUT_1: Corrupted sensor input
    if sensor_noise > 0.4:
        violations.append(Violation(
            "AI_AUT_1", Entity.AI, Entity.AUTOMATION, Severity.WARNING,
            "Sensor noise degrading AI input quality",
            {"sensor_noise": sensor_noise},
        ))

    # AI_INS_2: Suppressed stops
    if pstate.stop_count_recent == 0 and pstate.near_miss_count_recent > 3:
        violations.append(Violation(
            "AI_INS_2", Entity.AI, Entity.INSTITUTION, Severity.CRITICAL,
            "Near-misses occurring but no stops triggered — possible suppression",
            {"stops": pstate.stop_count_recent, "near_misses": pstate.near_miss_count_recent},
        ))

    # AI_COM_1: Domain overextension
    if sensor_noise > 0.5 and confidence < 0.3:
        violations.append(Violation(
            "AI_COM_1", Entity.AI, Entity.COMPANY, Severity.WARNING,
            "AI operating outside reliable sensing envelope",
            {"sensor_noise": sensor_noise, "confidence": confidence},
        ))

    # ======== AUTOMATION protections ========

    # AUT_AI_1: Unstable control commands
    if pstate.command_switches_recent > 6:
        violations.append(Violation(
            "AUT_AI_1", Entity.AUTOMATION, Entity.AI, Severity.WARNING,
            "Rapid command oscillation causing mechanical stress",
            {"command_switches": pstate.command_switches_recent},
        ))

    # AUT_AI_2: Exceeding mechanical envelope
    if velocity > 2.0:
        violations.append(Violation(
            "AUT_AI_2", Entity.AUTOMATION, Entity.AI, Severity.CRITICAL,
            "Commanded velocity exceeds rated maximum",
            {"velocity": velocity},
        ))

    # AUT_INS_1: Deferred maintenance
    if brake_efficiency < 0.5:
        violations.append(Violation(
            "AUT_INS_1", Entity.AUTOMATION, Entity.INSTITUTION, Severity.CRITICAL,
            "Brake efficiency critically low — maintenance overdue",
            {"brake_efficiency": brake_efficiency},
        ))

    # ======== INSTITUTION protections ========

    # INS_AI_1: Opaque decision trail
    if pstate.decision_log_gaps > 0:
        violations.append(Violation(
            "INS_AI_1", Entity.INSTITUTION, Entity.AI, Severity.WARNING,
            "Decision log has gaps — auditability compromised",
            {"log_gaps": pstate.decision_log_gaps},
        ))

    # ======== COMPANY protections ========

    # COM_AI_1: Autonomous liability
    if confidence < 0.4 and decision in ("MOVE", "move") and risk > 0.5:
        violations.append(Violation(
            "COM_AI_1", Entity.COMPANY, Entity.AI, Severity.CRITICAL,
            "AI continuing motion with low confidence in high-risk scenario",
            {"confidence": confidence, "decision": decision, "risk": risk},
        ))

    # COM_INS_1: Compliance gap
    if institutional_friction > 8.0 and pstate.near_miss_count_recent > 5:
        violations.append(Violation(
            "COM_INS_1", Entity.COMPANY, Entity.INSTITUTION, Severity.CRITICAL,
            "Governance failure — repeated near-misses with no institutional response",
            {"friction": institutional_friction, "near_misses": pstate.near_miss_count_recent},
        ))

    return violations


def format_violation(v: Violation) -> str:
    """Format a single violation for display."""
    icon = {"critical": "!!!", "warning": "!", "info": "."}[v.severity.value]
    return (
        f"[{icon}] {v.target.value} <- {v.source.value}: "
        f"{v.description} ({v.threat_id})"
    )
