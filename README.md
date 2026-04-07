# HAAS-Q

**Integrated Human-Automation-AI Safety & Quality Framework**

A feedback-driven safety system for environments where humans, automated machinery, and AI control systems interact — warehouse automation, manufacturing, autonomous equipment.

## Key Principles

- **Closed-loop control** — safety as dynamic equilibrium, not a compliance checklist
- **Multi-entity protection** — separate domains for humans, automation, and AI
- **Risk field modeling** — `Risk = f(energy x uncertainty x latency x proximity)`
- **Near-miss as primary signal** — high-value data, not noise
- **Failure-first architecture** — detects pre-incident instability, not just incidents

## Installation

```bash
pip install -e .
```

For development (includes pytest):

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
import numpy as np
from haas import (
    run_unified_simulation, SimConfig, EventStore,
    Zone, ZoneLevel, ZoneMap, show_summary,
)

# Define facility zones
zone_map = ZoneMap([
    Zone("floor", ZoneLevel.GREEN, np.array([-10.0, -10.0]), np.array([20.0, 20.0])),
    Zone("aisle", ZoneLevel.YELLOW, np.array([2.0, -1.0]), np.array([2.0, 2.0])),
    Zone("dock", ZoneLevel.RED, np.array([0.0, -1.0]), np.array([1.0, 2.0])),
])

# Run with SQLite persistence and live dashboard
with EventStore("session.db") as store:
    config = SimConfig(
        steps=100,
        enable_failures=True,
        enable_zones=True,
        enable_dashboard=True,
        store=store,
    )
    result = run_unified_simulation(config=config, zone_map=zone_map)
    print(show_summary(store))
```

## Package Structure

```
src/haas/
├── entities.py      # Human, Machine, AIController dataclasses
├── risk.py          # Dynamic risk computation (fatigue-amplified)
├── control.py       # Multi-layer control decisions and alerts
├── zones.py         # Green/yellow/red geofencing with speed limits
├── failures.py      # Failure injection, detection, FMEA data
├── energy.py        # TAF integration — fatigue, collapse, AI-tax, parasitic debt
├── protections.py   # Protection matrix — every entity protected from every other
├── audit.py         # Internal compliance audit against protection matrix
├── telemetry.py     # Sovereign Black Box — immutable logging
├── store.py         # SQLite persistence (events, signals, state, violations)
├── handshake.py     # FELTSensor handshake protocol
├── event_log.py     # In-memory event log for feedback loops
├── dashboard.py     # Terminal dashboard with risk/confidence/fatigue bars
└── simulation.py    # Basic, failure-aware, and unified simulation runners
```

## Testing

```bash
pytest
```

148 tests covering all modules.

## Companion Project

The **[Thermodynamic Accountability Framework](https://github.com/JinnZ2/thermodynamic-accountability-framework)** provides the energy/physics foundation. HAAS-Q models the control environment; TAF models the energy consequences on the organisms inside it. The `energy.py` module bridges them — porting TAF's fatigue model, collapse thresholds, ghost-friction accounting, and parasitic energy debt into HAAS-Q's simulation loop.

## Framework Specification

See [Framework.md](Framework.md) for the full system design document covering:

- System topology and risk field modeling
- Control hierarchy (hard/soft/adaptive)
- Human-AI interaction protocol
- Failure mode architecture (10 classes with FMEA)
- Sovereign Black Box traceability
- Handshake protocol and institutional friction scoring
- Deployment strategy and minimal viable implementation

## License

CC0 1.0 Universal — Public Domain
