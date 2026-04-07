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
│   ├── failures.py      # Failure injection, detection, FMEA table
│   ├── telemetry.py     # Sovereign Black Box — immutable telemetry logging
│   ├── handshake.py     # FELTSensor handshake / micro-clarification protocol
│   ├── event_log.py     # Append-only event log
│   └── simulation.py    # Basic and failure-aware simulation runners
├── tests/               # pytest test suite (46 tests)
├── Framework.md         # Full framework specification (~1250 lines)
├── pyproject.toml       # Package config (setuptools, numpy dep, pytest)
├── LICENSE              # CC0 1.0 Universal
└── README.md            # Project README
```

## Commands

```bash
pip install -e ".[dev]"  # Install with dev dependencies
pytest                   # Run all tests
pytest tests/test_risk.py -v  # Run a specific test file
```

## Architecture

The package follows a layered dependency graph with no circular imports:

```
entities.py, event_log.py, failures.py, telemetry.py, handshake.py  (leaf modules)
    ↑
risk.py, control.py  (depend on entities)
    ↑
simulation.py  (integration layer — wires everything together)
```

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
