# CLAUDE.md

## Project Overview

**HAAS-Q** (Integrated Human-Automation-AI Safety & Quality Framework) is a safety framework for environments where humans, automated machinery, and AI control systems interact — particularly warehouse/manufacturing contexts with autonomous equipment like forklifts.

**Companion project:** [Thermodynamic Accountability Framework (TAF)](https://github.com/JinnZ2/thermodynamic-accountability-framework) — provides the energy/physics layer. HAAS-Q models the *control environment* (entities, zones, decisions); TAF models the *energy consequences* on the organisms inside it. The `energy.py` module bridges them.

## Repository Structure

```
HAAS/
├── src/haas/            # Python package
│   ├── __init__.py      # Public API exports
│   ├── entities.py      # Human, Machine, AIController dataclasses
│   ├── risk.py          # Dynamic risk computation (fatigue-amplified)
│   ├── control.py       # Multi-layer control decisions and alerts
│   ├── zones.py         # Green/yellow/red geofencing with speed limits
│   ├── failures.py      # Failure injection, detection, FMEA table
│   ├── energy.py        # TAF integration — fatigue, collapse, AI-tax, parasitic debt
│   ├── telemetry.py     # Sovereign Black Box — immutable telemetry logging
│   ├── store.py         # SQLite persistence (events, signals, state, violations)
│   ├── handshake.py     # FELTSensor handshake / micro-clarification protocol
│   ├── protections.py   # Protection matrix — every entity protected from every other
│   ├── audit.py         # Internal audit — compliance scoring against protection matrix
│   ├── event_log.py     # In-memory append-only event log
│   ├── dashboard.py     # Terminal dashboard with risk/confidence/fatigue bars
│   ├── simulation.py    # Basic, failure-aware, and unified simulation runners
│   └── method.py        # Claim ledger — hypothesize, run, falsify, revise, rerun
├── tests/               # pytest test suite (200 tests)
├── legacy/              # Superseded artifacts — kept, never deleted
│   ├── README.md        # Precedence doctrine + supersession ledger
│   └── prototypes/      # Verbatim prototype code extracted from Framework.md
├── Framework.md         # Full framework specification (~1300 lines)
├── inquiry.json         # Live claim ledger — open claims, falsifications, unknowns
├── pyproject.toml       # Package config (setuptools, numpy dep, pytest)
├── LICENSE              # CC0 1.0 Universal
└── README.md            # Project README
```

## Commands

```bash
pip install -e ".[dev]"       # Install with dev dependencies
pytest                        # Run all 200 tests
pytest tests/test_energy.py -v # Run a specific test file
python -c "from haas import Inquiry; print(Inquiry.load('inquiry.json').format_ledger())"
```

## Architecture

```
entities.py, event_log.py, failures.py, telemetry.py, handshake.py, zones.py, store.py, protections.py, energy.py, audit.py
    ↑
risk.py, control.py  (depend on entities; risk uses fatigue from energy)
    ↑
dashboard.py  (depends on store)
    ↑
simulation.py  (integration layer — wires everything together)
    ↑
method.py  (claim ledger — turns runs into verdicts; imports simulation/store for typing only)
```

### Simulation Modes

1. **Basic** (`run_basic_simulation`) — spatial entities, risk computation, AI control, event log
2. **Failure-aware** (`run_failure_simulation`) — random risk, stochastic degradation, signal detection
3. **Unified** (`run_unified_simulation`) — merges spatial + failures + zones + energy + protections + SQLite + dashboard

The unified simulation pipeline per step:
failure injection -> energy state update -> fatigue-amplified spatial risk -> zone classification -> failure signals -> control decision -> zone override -> speed enforcement -> entity movement -> alerts -> AI-tax accounting -> protection matrix evaluation -> logging -> persistent storage -> dashboard render.

### TAF Energy Integration (energy.py)

Ported from the Thermodynamic Accountability Framework. Models the human operator as an energy system:

- **FatigueModel** — `total_load = (physical + cognitive) * hidden_mult * auto_mult * env_mult`
- **Collapse thresholds** — 120% productivity degradation, 140% safety breakdown, 160% health collapse
- **Distance-to-collapse** — 0-1 scale normalized against health threshold
- **Ghost-friction / AI-tax** — cumulative metabolic + cognitive cost of false alerts
- **Parasitic energy debt** — uncompensated labor extraction with friction multiplier
- **Long-tail risk** — `10 * (1 - exp(-0.35 * hidden_count))`, nonlinear in hidden variables

`HumanEnergyState` bridges TAF→HAAS by mapping:
- `sensor_noise` → hidden variable count
- `brake_efficiency` → automation reliability
- `alert_count` → ghost-friction / AI-tax
- `institutional_friction` → parasitic energy debt

Fatigue feeds back into `compute_risk()` via a fatigue multiplier (up to 1.5x at fatigue=10).

### Protection Matrix

Five entities — Human, AI, Automation, Institution, Company — each protected from every other. 35+ directional threats across all 20 entity pairs. Includes TAF-derived threats:
- `H_AI_4` — Ghost-friction / AI-tax (cumulative false alert cost)
- `H_INS_4` — Energy collapse ignored (distance-to-collapse critically low)
- `H_COM_3` — Parasitic energy extraction (uncompensated labor drain)

### Internal Audit

Scores compliance across all threats on three dimensions (0-3 each): control exists, signal monitored, enforcement proof. Generates per-pair scores, per-entity scores, gap analysis, heatmap matrix, and maturity rating.

### Claim Ledger (method.py)

The scientific method as code: hypothesize → run → observe → falsified? → edit
the claim → search for unknowns → rerun. `Inquiry` is an append-only ledger of
`Claim`s (versioned), `RunRecord`s (with seed and config, so a run can be
repeated), `Evaluation`s, and `Unknown`s. It persists to JSON — `inquiry.json`
at the repository root is the live one.

Rules that are not negotiable, for the same reason the black box is append-only:

- **Nothing is deleted.** Falsified claims are marked, not removed. `revise()`
  supersedes; it never overwrites.
- **Precedence carries.** A revision inherits `lineage_id` and `first_stated`
  from its ancestor. Editing a claim never resets its priority date.
- **Refutation is asymmetric.** One failed prediction falsifies; no number of
  passing runs proves. Supported claims keep appearing in `next_actions()`
  until they clear `MIN_CORROBORATING_RUNS`, and never stop being falsifiable.
- **An unmeasured prediction is INCONCLUSIVE, not a pass**, and automatically
  raises an `Unknown` naming the missing metric.
- **A claim with no predictions can never be supported** — `next_actions()`
  flags it as unfalsifiable.

`metrics_from_result()` / `metrics_from_store()` turn a run into the observables
predictions are written against. Set `SimConfig.seed` for any run that will be
used as evidence.

### Legacy Folder

`legacy/` holds superseded artifacts — currently the prototype code that was
embedded in `Framework.md` before the package was extracted. Same doctrine as
the ledger: nothing is deleted, precedence carries, and the fate of each
artifact (refined / extended / falsified) is recorded in `legacy/README.md`.
Archived files are kept verbatim with a provenance header; do not tidy them up,
and do not fix bugs there — fix them in the superseding module.

### Persistent Storage

SQLite with four tables: `events`, `signals`, `system_state`, `violations`.
Query helpers: `near_miss_count()`, `override_count()`, `average_risk()`, `violation_count()`, `violations_by_target()`, `violations_by_pair()`.

## Key Concepts

- **Risk field modeling** — `Risk = f(relative_velocity / distance) * (1 + latency) * fatigue_mult`
- **Control hierarchy** — hard controls (physical), soft controls (AI thresholds), adaptive controls
- **Failure-first** — `SystemState` degrades stochastically; `detect_failures()` produces observable signals
- **Energy-first** — human modeled as energy budget, not just position; fatigue and collapse are first-class signals
- **Coupled failure detection** — compound signals trigger immediate stop
- **FMEA table** — 8 structured entries with RPN scoring
- **Sovereign Black Box** — append-only telemetry; Model/Reality Dissonance detection
- **Handshake protocol** — micro-clarification when felt_level or AI confidence drops

## Development Guidelines

- Safety logic must be correct first — changes to thresholds and control decisions are deliberate
- Thresholds are claims. Changing one means recording it in `inquiry.json`: what was
  claimed, which run falsified it, what the edited claim is, what unknowns it exposed
- Superseded code goes to `legacy/` with a provenance header and a ledger row — never deleted
- All magic numbers are named constants
- Functions return values instead of printing — testable and composable
- Framework.md is the specification; code implements it — keep them aligned
- TAF equations must match their source — changes require updating both repos
- Use dataclasses with typed fields; explicit state enums over implicit strings
- Log everything — the sovereign black box principle is non-negotiable

<!-- clone-refspec-note v1 -->
## Cloning and pushing
Shallow clones are single-branch by default.
Before pushing any branch other than main, run:

    git config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'
    git fetch --depth 1

Or clone with: git clone --depth 1 --no-single-branch <url>
Without this, the first push of a new branch
fails the tracking-ref check even when the
commit landed.
<!-- /clone-refspec-note v1 -->
