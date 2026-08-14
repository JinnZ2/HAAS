# Legacy

Superseded artifacts. Nothing here is imported, executed, or maintained — and
nothing here gets deleted.

## Why keep it

A framework that quietly rewrites its own history cannot be audited. If the
only surviving copy of a claim is the current one, there is no way to ask *what
did we think before, and what changed our minds?* — which is exactly the
question an incident investigation asks.

This is the same rule the framework applies to safety data. The Sovereign Black
Box is append-only because an edited log is a log you cannot trust. The claim
record is append-only for the same reason.

## Precedence carries

**A superseded artifact keeps its priority date.** When `src/haas/risk.py`
implements the risk equation, that equation was *first stated* in
`Framework.md` and first executed in `legacy/prototypes/v0_1_control_prototype.py`.
The rewrite inherits the idea; it does not reset the clock on it. Concretely:

1. **Origin stands.** The originating commit and document line range are
   recorded in every archived file's header. That is the priority date.
2. **Supersession is a link, not an erasure.** The new module cites what it
   replaced; the old artifact cites what replaced it. Both directions resolve.
3. **The reason is recorded.** *Refined*, *extended*, and *falsified* are
   different fates and the ledger says which one happened.
4. **A falsified claim stays visible.** It is marked falsified, not removed. A
   claim that was tried and failed is evidence — it stops the same idea from
   being re-proposed as if it were new.

## The cycle this folder is the tail end of

```
hypothesize → run → observe → falsified? ──no──→ claim stands (keep running it)
                                  │
                                 yes
                                  │
                                  ▼
                        edit the claim (v+1, precedence inherited)
                                  │
                                  ▼
                    search for unknowns the failure exposed
                                  │
                                  ▼
                               rerun ──────────────────┐
                                  ▲                    │
                                  └────────────────────┘
```

The live half of that loop is code: `src/haas/method.py` records claims, runs,
verdicts, revisions, and open unknowns, and persists them to JSON so a future
session can read what was already tried instead of re-deriving it. This folder
is where an artifact lands when the loop has moved past it.

## Ledger

Everything in `prototypes/` came out of `Framework.md`, which is the origin
document and stays in place at the repository root — it is the specification,
not an archive. The prototypes are the code that was embedded in it, extracted
verbatim.

| Artifact | Origin | Superseded by | Fate | What changed |
|---|---|---|---|---|
| `prototypes/v0_1_control_prototype.py` | `Framework.md:266-378` (`c5ba2bf`) | `entities.py`, `risk.py`, `control.py`, `event_log.py`, `simulation.py` (`896a12b`) | Refined | Split into modules; types added; `EventLog` kept as-is. Risk equation and the 0.7/0.4 move–slow–stop ladder survive unchanged. |
| `prototypes/v0_2_failure_aware.py` | `Framework.md:882-951` (`c5ba2bf`) | `failures.py`, `risk.py`, `control.py`, `simulation.py` (`896a12b`) | Refined + partly falsified | `SystemState`, the four detection signals, and coupled-failure `STOP` survive. `risk = random.uniform(0, 1)` did not — see *Falsified claims* below. |
| `prototypes/v0_3_dashboard_schema.sql` | `Framework.md:993-1015` (`c5ba2bf`) | `store.py` (`_SCHEMA`, `93eb5c9`) | Extended | Three tables became four (`violations` added); `id INT` became autoincrement primary keys; zone and position columns added. Never valid SQL as written — no `CREATE TABLE`. |
| `prototypes/v0_3_rules_engine.py` | `Framework.md:1036-1046` (`c5ba2bf`) | `control.py` (`check_alerts`, `896a12b`) | Refined | Bare statements became a function returning a list. `threshold` and `limit`, unbound in the original, became named parameters (`override_threshold=3`, `drift_limit=0.5`). |
| `prototypes/v0_3_sovereign_black_box.py` | `Framework.md:1153-1199` (`c5ba2bf`) | `telemetry.py` (`896a12b`) | Refined | `print` became `logging.critical`; the hardcoded 0.9 / 0.5 dissonance thresholds became constructor parameters; critical events retained in memory as well as on disk. The append-only-file guarantee is unchanged. |
| `prototypes/v0_3_handshake_protocol.py` | `Framework.md:1222-1243` (`c5ba2bf`) | `handshake.py` (`896a12b`) | Refined | `apply_institutional_throttle` was called but never defined — the prototype could not run past a high-friction branch. Thresholds became named constants. The three return states are unchanged. |

## Falsified claims

Claims that were run and did not survive. Kept because the failure is the
useful part.

### F-1 — Random risk is an adequate stand-in for spatial risk

- **Claimed in:** `prototypes/v0_2_failure_aware.py` — `risk = random.uniform(0, 1)`
- **Status:** FALSIFIED
- **Falsified by:** `896a12b` / `93eb5c9`, when the failure-aware loop and the
  spatial loop were run against each other.
- **Why it failed:** uniform random risk is independent of the machine's
  position, so a control decision can never change the next step's risk. The
  loop cannot close — braking does not lower the risk it was braking against,
  and no near miss is ever attributable to a decision. It exercises the signal
  plumbing and nothing else.
- **Edited claim:** risk must be computed from real relative velocity and
  distance for the control loop to be measurable. `unified_step` uses
  `compute_risk` on live positions. `run_failure_simulation` is kept as-is and
  is honest about what it is — a plumbing test, not a safety result.
- **Unknown it exposed:** stochastic degradation (`inject_failures`) is still
  independent of what the machine is doing. Real brake wear is a function of
  braking, and real sensor noise is a function of the environment the machine
  drove into. Open.

### F-2 — Risk is fully described by relative velocity, distance, and latency

- **Claimed in:** `Framework.md:53` and `prototypes/v0_1_control_prototype.py`
- **Status:** SUPERSEDED (claim edited, precedence retained)
- **Edited by:** `c51cf2d` — TAF energy integration.
- **Why it was incomplete:** the equation described the geometry between two
  bodies and treated the human as one of them. But evasion is metabolic. Two
  operators at identical distance and closing speed are not at identical risk
  if one of them is eleven hours into a shift. The original equation had no
  term that could express that.
- **Edited claim:** `Risk = (v_rel / d) * (1 + latency) * (1 + fatigue * 0.05)`,
  implemented in `risk.py`. The original form is the fatigue = 0 case, so the
  first statement is preserved exactly as a special case — this is refinement,
  not replacement.
- **Unknown it exposed:** the 0.05 coefficient (1.5× amplification at maximum
  fatigue) is asserted, not measured. No run in this repository can falsify it,
  because the simulation generates fatigue from the same model that consumes
  it. Falsifying it requires field data. Open.

## Adding to this folder

1. Move the artifact in verbatim. Do not clean it up on the way — a tidied
   archive is a rewritten one.
2. Add the header block: source, origin commit, superseding commit, replacement
   module, status.
3. Add a ledger row. State the fate (refined / extended / falsified) and what
   actually changed.
4. If it was falsified rather than refined, write the falsification entry —
   what was claimed, what run killed it, what the edited claim is, and which
   unknowns the failure exposed.
5. Record the open unknowns in the live ledger (`src/haas/method.py`) so the
   next run picks them up instead of rediscovering them.
