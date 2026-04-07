# CLAUDE.md

## Project Overview

**HAAS-Q** (Integrated Human-Automation-AI Safety & Quality Framework) is a safety framework for environments where humans, automated machinery, and AI control systems interact — particularly warehouse/manufacturing contexts with autonomous equipment like forklifts.

This is currently a **framework specification and design document** project. The core artifact is `Framework.md`, which defines a modular, feedback-driven safety system structured as a living control system rather than a static policy.

## Repository Structure

```
HAAS/
├── README.md        # Project brief
├── Framework.md     # Comprehensive framework specification (~1250 lines)
├── LICENSE          # CC0 1.0 Universal (public domain)
└── CLAUDE.md        # This file
```

## Key Concepts

The framework is built around these core principles:

- **Closed-loop control** — safety as dynamic equilibrium, not a compliance checklist
- **Multi-entity protection** — separate domains for humans, automation, and AI
- **Risk field modeling** — `Risk = f(energy x uncertainty x latency x proximity)`
- **Near-miss as primary signal** — treat near-misses as high-value data
- **DMAIC quality integration** — Six Sigma continuous improvement applied to safety
- **Adaptive controls** — AI adjusts behavior based on real-time conditions

## Framework.md Structure

The specification covers 12 major sections:

| Section | Topic |
|---------|-------|
| 0 | System Intent (Control Definition) |
| 1 | System Topology Mapping |
| 2 | Risk Field Modeling |
| 3 | Control Hierarchy (Multi-Layer Safety) |
| 4 | Human-AI Interaction Protocol |
| 5 | Protection Domains |
| 6 | Continuous Quality Layer (ASQ + Six Sigma) |
| 7 | Learning Loop |
| 8 | Verification & Stress Testing |
| 9 | Operational States Definition |
| 10 | Governance Layer |
| 11 | Deployment Strategy |
| 12 | Minimal Viable Implementation |

Plus appendices: Python monitoring prototype, telemetry/black box logging, handshake protocol (FELTSensor), micro-clarification friction scoring, and the receipts clause.

## Technology Context

- **Language:** Python (prototype code in Framework.md uses dataclasses, NumPy, JSON logging)
- **Domain:** Industrial safety, real-time control systems, warehouse automation
- **License:** CC0 1.0 (public domain)

## Development Guidelines

- This project prioritizes **correctness and safety** over speed — changes to safety logic must be deliberate
- Framework.md is a **living document** — modular sections are designed for independent iteration
- Any proposed code implementations should follow the patterns established in the Framework.md prototype sections (dataclasses, typed fields, explicit state enums)
- Prefer explicit over implicit — all control thresholds, decision boundaries, and authority models must be clearly defined
- Log everything — the "sovereign black box" principle applies: telemetry is non-negotiable

## Working with This Repo

- No build system, test suite, or CI/CD exists yet — this is specification-stage
- When adding implementation code, follow Python best practices: type hints, dataclasses, and clear separation between control logic, sensing, and logging
- Keep Framework.md sections self-contained and independently iterable
- Any new files should be referenced from this document
