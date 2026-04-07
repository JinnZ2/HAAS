"""Terminal dashboard — real-time safety monitoring display."""

import sys
import time
from dataclasses import dataclass, field

from .store import EventStore


# Alert level thresholds
RISK_CRITICAL = 0.7
RISK_WARNING = 0.5
CONFIDENCE_LOW = 0.5

# ANSI color codes
_RED = "\033[91m"
_YELLOW = "\033[93m"
_GREEN = "\033[92m"
_CYAN = "\033[96m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"


@dataclass
class DashboardSnapshot:
    """A single dashboard frame, computed from current simulation state."""

    step: int
    risk: float
    confidence: float
    decision: str
    zone: str
    signals: dict[str, bool]
    sensor_noise: float
    brake_efficiency: float
    human_pos: list[float]
    machine_pos: list[float]
    alerts: list[str]
    violations: list[str] = field(default_factory=list)  # formatted violation strings

    @property
    def risk_bar(self) -> str:
        filled = int(self.risk * 20)
        if self.risk > RISK_CRITICAL:
            color = _RED
        elif self.risk > RISK_WARNING:
            color = _YELLOW
        else:
            color = _GREEN
        return f"{color}{'█' * filled}{'░' * (20 - filled)}{_RESET}"

    @property
    def confidence_bar(self) -> str:
        filled = int(self.confidence * 20)
        if self.confidence < CONFIDENCE_LOW:
            color = _RED
        else:
            color = _CYAN
        return f"{color}{'█' * filled}{'░' * (20 - filled)}{_RESET}"


def format_dashboard(snap: DashboardSnapshot) -> str:
    """Render a dashboard snapshot as a multi-line terminal string."""
    active_signals = [k for k, v in snap.signals.items() if v]
    alert_str = ", ".join(snap.alerts) if snap.alerts else f"{_GREEN}NONE{_RESET}"
    signal_str = ", ".join(active_signals) if active_signals else "none"

    decision_colors = {
        "STOP": _RED, "stop": _RED,
        "SLOW": _YELLOW, "slow": _YELLOW,
        "MOVE": _GREEN, "move": _GREEN,
    }
    dc = decision_colors.get(snap.decision, _RESET)

    lines = [
        f"{_BOLD}═══ HAAS-Q Safety Dashboard ═══{_RESET}  step {snap.step}",
        "",
        f"  Risk:       {snap.risk_bar} {snap.risk:.3f}",
        f"  Confidence: {snap.confidence_bar} {snap.confidence:.3f}",
        f"  Decision:   {dc}{_BOLD}{snap.decision}{_RESET}",
        f"  Zone:       {snap.zone}",
        "",
        f"  {_DIM}Sensor noise: {snap.sensor_noise:.2f}  "
        f"Brake eff: {snap.brake_efficiency:.2f}{_RESET}",
        f"  {_DIM}Human: ({snap.human_pos[0]:+.1f}, {snap.human_pos[1]:+.1f})  "
        f"Machine: ({snap.machine_pos[0]:+.1f}, {snap.machine_pos[1]:+.1f}){_RESET}",
        "",
        f"  Signals:    {signal_str}",
        f"  Alerts:     {alert_str}",
    ]

    if snap.violations:
        lines.append("")
        lines.append(f"  {_BOLD}Protection Violations:{_RESET}")
        for v in snap.violations:
            lines.append(f"    {_RED}{v}{_RESET}")

    lines.append(f"{_BOLD}{'═' * 35}{_RESET}")
    return "\n".join(lines)


def print_dashboard(snap: DashboardSnapshot, clear: bool = True) -> None:
    """Print a dashboard snapshot to the terminal."""
    if clear:
        sys.stdout.write("\033[2J\033[H")  # clear screen + home
    sys.stdout.write(format_dashboard(snap) + "\n")
    sys.stdout.flush()


def show_summary(store: EventStore, last_n: int = 50) -> str:
    """Generate a text summary from the persistent event store."""
    total = store.count_events()
    avg_risk = store.average_risk(last_n)
    near_misses = store.near_miss_count()
    overrides = store.override_count()
    latest = store.get_latest_state()

    v_total = store.violation_count()
    v_critical = store.violation_count("critical")
    v_by_target = store.violations_by_target()

    lines = [
        f"{_BOLD}═══ HAAS-Q Session Summary ═══{_RESET}",
        f"  Total events:  {total}",
        f"  Avg risk (last {last_n}): {avg_risk:.3f}" if avg_risk is not None else "  Avg risk: N/A",
        f"  Near-misses:   {near_misses}",
        f"  Overrides:     {overrides}",
    ]
    if latest:
        lines.append(f"  Last mode:     {latest['mode']}")
        lines.append(f"  Sensor noise:  {latest['sensor_noise']:.2f}")
        lines.append(f"  Brake eff:     {latest['brake_efficiency']:.2f}")

    lines.append("")
    lines.append(f"  {_BOLD}Protection Violations:{_RESET}  {v_total} total, {v_critical} critical")
    if v_by_target:
        for target, count in sorted(v_by_target.items()):
            lines.append(f"    {target}: {count}")

    lines.append(f"{_BOLD}{'═' * 35}{_RESET}")
    return "\n".join(lines)
