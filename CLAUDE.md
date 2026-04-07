# CLAUDE.md

## Project Overview

**HAAS-Q** (Integrated Human-Automation-AI Safety & Quality Framework) is a safety framework for environments where humans, automated machinery, and AI control systems interact — particularly warehouse/manufacturing contexts with autonomous equipment like forklifts.

## Repository Structure

```
HAAS/
├── src/haas/            # Python package
│   ├── __init__.py      # Public API exports
│   ├── entities.py      # Human, Machine, AIController dataclasses
│   ├── risk.py          # Dynamic risk computation
│   ├── control.py       # Multi-layer control decisions and alerts
│   ├── zones.py         # Green/yellow/red geofencing with speed limits
│   ├── failures.py      # Failure injection, detection, FMEA table
│   ├── telemetry.py     # Sovereign Black Box — immutable telemetry logging
│   ├── store.py         # SQLite persistence (events, signals, system_state tables)
│   ├── handshake.py     # FELTSensor handshake / micro-clarification protocol
│   ├── event_log.py     # In-memory append-only event log
│   ├── dashboard.py     # Terminal dashboard with ANSI color bars and session summary
│   └── simulation.py    # Basic, failure-aware, and unified simulation runners
├── tests/               # pytest test suite (72 tests)
├── Framework.md         # Full framework specification (~1250 lines)
├── pyproject.toml       # Package config (setuptools, numpy dep, pytest)
├── LICENSE              # CC0 1.0 Universal
└── README.md            # Project README
```

## Commands

```bash
pip install -e ".[dev]"       # Install with dev dependencies
pytest                        # Run all 72 tests
pytest tests/test_zones.py -v # Run a specific test file
```

## Architecture

The package follows a layered dependency graph with no circular imports:

```
entities.py, event_log.py, failures.py, telemetry.py, handshake.py, zones.py, store.py
    ↑
risk.py, control.py  (depend on entities)
    ↑
dashboard.py  (depends on store)
    ↑
simulation.py  (integration layer — wires everything together)
```

### Simulation Modes

1. **Basic** (`run_basic_simulation`) — spatial entities, risk computation, AI control, event log
2. **Failure-aware** (`run_failure_simulation`) — random risk, stochastic degradation, signal detection
3. **Unified** (`run_unified_simulation`) — merges spatial + failures + zones + SQLite + dashboard

The unified simulation runs: failure injection -> spatial risk -> zone classification -> failure signals -> control decision -> zone override -> speed enforcement -> entity movement -> alerts -> logging -> persistent storage -> dashboard render.

### Zone System

Three levels with strict priority: RED (full stop) > YELLOW (half speed) > GREEN (normal). Zones are axis-aligned rectangles. The most restrictive zone containing either the human or machine position wins.

### Persistent Storage

SQLite with three tables matching the Framework.md spec:
- `events` — risk, confidence, decision, zone, positions, override flag
- `signals` — boolean failure indicators per timestamp
- `system_state` — mode, active controller, sensor noise, brake efficiency

Query helpers: `near_miss_count()`, `override_count()`, `average_risk()`.

## Key Concepts

- **Risk field modeling** — `Risk = f(relative_velocity / distance) * (1 + latency)`, clamped to [0, 1]
- **Control hierarchy** — hard controls (physical), soft controls (AI thresholds), adaptive controls
- **Failure-first** — `SystemState` degrades stochastically; `detect_failures()` produces observable signals
- **Coupled failure detection** — compound signals (e.g., low confidence AND brake degradation) trigger immediate stop
- **FMEA table** — 8 structured entries (F1-F8) with RPN scoring as queryable data
- **Sovereign Black Box** — append-only telemetry; detects Model/Reality Dissonance (high confidence + close proximity)
- **Handshake protocol** — micro-clarification when felt_level or AI confidence drops; institutional friction throttling

## Development Guidelines

- Safety logic must be correct first — changes to thresholds and control decisions are deliberate
- All magic numbers are named constants (e.g., `FELT_LEVEL_THRESHOLD`, `AI_CONFIDENCE_THRESHOLD`)
- Functions return values instead of printing — keeps them testable and composable
- Framework.md is the specification; code implements it — keep them aligned
- Use dataclasses with typed fields; explicit state enums over implicit strings
- Log everything — the sovereign black box principle is non-negotiable
