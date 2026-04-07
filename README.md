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
from haas import run_basic_simulation, run_failure_simulation

# Basic control loop simulation
log = run_basic_simulation(steps=20)
for entry in log.events:
    print(entry["event"]["decision"], entry["event"]["risk"])

# Failure-aware simulation with drift and sensor degradation
state = run_failure_simulation(steps=50)
for entry in state.logs[-5:]:
    print(entry["decision"], entry["confidence"], entry["signals"])
```

## Package Structure

```
src/haas/
├── entities.py      # Human, Machine, AIController dataclasses
├── risk.py          # Dynamic risk computation
├── control.py       # Multi-layer control decisions and alerts
├── failures.py      # Failure injection, detection, FMEA data
├── telemetry.py     # Sovereign Black Box — immutable logging
├── handshake.py     # FELTSensor handshake protocol
├── event_log.py     # Event logging for feedback loops
└── simulation.py    # Basic and failure-aware simulation runners
```

## Testing

```bash
pytest
```

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
