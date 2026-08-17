"""Scientific method layer — hypothesize, run, falsify, revise, search, rerun.

The framework makes claims: that fatigue amplifies risk by 5% per point, that
compound signals warrant an immediate stop, that a 0.7 risk threshold is the
right place to brake. Every one of those numbers is a hypothesis. This module
is the ledger that holds them to account.

The cycle::

    hypothesize -> run -> observe -> falsified? --no--> claim stands, keep running
                                          |
                                         yes
                                          v
                                edit the claim (v+1)
                                          |
                                          v
                          search for unknowns the failure exposed
                                          |
                                          v
                                        rerun

Two rules govern the ledger, and they are the same rule the Sovereign Black Box
follows — an edited record is a record you cannot trust:

**Nothing is deleted.** A falsified claim is marked falsified and kept. It is
evidence. Without it, the same dead idea gets re-proposed as if it were new.

**Precedence carries.** A revision inherits its ancestor's lineage id and
`first_stated` timestamp. Editing a claim does not reset its priority date —
the idea was still first stated when it was first stated. See `legacy/README.md`
for the same rule applied to superseded code.

One asymmetry is built in: a single failed prediction falsifies a claim, but no
number of passing runs proves one. Supported claims stay provisional and the
ledger keeps asking for another run.
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:  # pragma: no cover — typing only, avoids an import cycle
    from .simulation import SimResult
    from .store import EventStore


# Corroboration is provisional: a claim keeps asking to be rerun until it has
# survived this many independent runs, and never stops being falsifiable.
MIN_CORROBORATING_RUNS = 3

# Risk above this with a non-STOP decision is a near miss (matches store.py).
NEAR_MISS_RISK_THRESHOLD = 0.7


class Verdict(Enum):
    """Outcome of checking a claim against observed metrics."""

    SUPPORTED = "supported"
    FALSIFIED = "falsified"
    INCONCLUSIVE = "inconclusive"


class ClaimStatus(Enum):
    """Where a claim sits in the cycle."""

    PROPOSED = "proposed"        # stated, never run
    SUPPORTED = "supported"      # run, survived — provisionally
    FALSIFIED = "falsified"      # run, failed, awaiting revision
    SUPERSEDED = "superseded"    # revised into a successor
    RETIRED = "retired"          # withdrawn without a successor


class UnknownStatus(Enum):
    """Where an open question sits."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


# Comparison operators a prediction may use.
COMPARATORS: dict[str, Callable[[float, float], bool]] = {
    "<": lambda observed, bound: observed < bound,
    "<=": lambda observed, bound: observed <= bound,
    ">": lambda observed, bound: observed > bound,
    ">=": lambda observed, bound: observed >= bound,
    "==": lambda observed, bound: observed == bound,
    "!=": lambda observed, bound: observed != bound,
}


@dataclass(frozen=True)
class Prediction:
    """A falsifiable statement about one metric.

    `tolerance` widens the passing region in the claim's favour, so a
    prediction is only falsified by a margin the author considers real.
    """

    metric: str
    op: str
    value: float
    tolerance: float = 0.0

    def __post_init__(self) -> None:
        if self.op not in COMPARATORS:
            raise ValueError(
                f"unknown comparator {self.op!r}; expected one of {sorted(COMPARATORS)}"
            )
        if self.tolerance < 0:
            raise ValueError("tolerance must be non-negative")

    def check(self, metrics: dict[str, float]) -> Verdict:
        """Check this prediction. Missing metric means INCONCLUSIVE, not failure."""
        if self.metric not in metrics:
            return Verdict.INCONCLUSIVE

        observed = metrics[self.metric]
        compare = COMPARATORS[self.op]

        if self.op in ("==", "!="):
            equal = abs(observed - self.value) <= self.tolerance
            passed = equal if self.op == "==" else not equal
        elif self.op in ("<", "<="):
            passed = compare(observed, self.value + self.tolerance)
        else:
            passed = compare(observed, self.value - self.tolerance)

        return Verdict.SUPPORTED if passed else Verdict.FALSIFIED

    def describe(self) -> str:
        tol = f" ±{self.tolerance:g}" if self.tolerance else ""
        return f"{self.metric} {self.op} {self.value:g}{tol}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "op": self.op,
            "value": self.value,
            "tolerance": self.tolerance,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Prediction":
        return cls(
            metric=data["metric"],
            op=data["op"],
            value=data["value"],
            tolerance=data.get("tolerance", 0.0),
        )


@dataclass
class Claim:
    """A hypothesis, versioned, with its precedence attached.

    `lineage_id` and `first_stated` are inherited by every revision — they are
    the claim's priority date and they never move. `version` and `stated_at`
    belong to this revision alone.
    """

    id: str
    lineage_id: str
    statement: str
    predictions: list[Prediction] = field(default_factory=list)
    version: int = 1
    status: ClaimStatus = ClaimStatus.PROPOSED
    first_stated: float = 0.0
    stated_at: float = 0.0
    supersedes: str | None = None
    superseded_by: str | None = None
    sources: list[str] = field(default_factory=list)
    rationale: str = ""

    @property
    def is_falsifiable(self) -> bool:
        """A claim with no predictions cannot be tested, so it cannot be supported."""
        return len(self.predictions) > 0

    @property
    def is_live(self) -> bool:
        """True while this claim is still the head of its lineage."""
        return self.status not in (ClaimStatus.SUPERSEDED, ClaimStatus.RETIRED)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "lineage_id": self.lineage_id,
            "statement": self.statement,
            "predictions": [p.to_dict() for p in self.predictions],
            "version": self.version,
            "status": self.status.value,
            "first_stated": self.first_stated,
            "stated_at": self.stated_at,
            "supersedes": self.supersedes,
            "superseded_by": self.superseded_by,
            "sources": list(self.sources),
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Claim":
        return cls(
            id=data["id"],
            lineage_id=data["lineage_id"],
            statement=data["statement"],
            predictions=[Prediction.from_dict(p) for p in data.get("predictions", [])],
            version=data.get("version", 1),
            status=ClaimStatus(data.get("status", "proposed")),
            first_stated=data.get("first_stated", 0.0),
            stated_at=data.get("stated_at", 0.0),
            supersedes=data.get("supersedes"),
            superseded_by=data.get("superseded_by"),
            sources=list(data.get("sources", [])),
            rationale=data.get("rationale", ""),
        )


@dataclass
class RunRecord:
    """One execution and what it measured.

    `config` and `seed` are what make a rerun a rerun rather than a new
    experiment — without them an observation cannot be reproduced or disputed.
    """

    id: str
    claim_id: str
    metrics: dict[str, float] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    seed: int | None = None
    notes: str = ""
    timestamp: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "claim_id": self.claim_id,
            "metrics": dict(self.metrics),
            "config": dict(self.config),
            "seed": self.seed,
            "notes": self.notes,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunRecord":
        return cls(
            id=data["id"],
            claim_id=data["claim_id"],
            metrics=dict(data.get("metrics", {})),
            config=dict(data.get("config", {})),
            seed=data.get("seed"),
            notes=data.get("notes", ""),
            timestamp=data.get("timestamp", 0.0),
        )


@dataclass
class PredictionResult:
    """One prediction checked against one run."""

    prediction: Prediction
    observed: float | None
    verdict: Verdict

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction": self.prediction.to_dict(),
            "observed": self.observed,
            "verdict": self.verdict.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PredictionResult":
        return cls(
            prediction=Prediction.from_dict(data["prediction"]),
            observed=data.get("observed"),
            verdict=Verdict(data["verdict"]),
        )


@dataclass
class Evaluation:
    """The verdict of one run on one claim, prediction by prediction."""

    run_id: str
    claim_id: str
    verdict: Verdict
    results: list[PredictionResult] = field(default_factory=list)
    timestamp: float = 0.0

    @property
    def failures(self) -> list[PredictionResult]:
        """The predictions that did the falsifying."""
        return [r for r in self.results if r.verdict is Verdict.FALSIFIED]

    @property
    def unmeasured(self) -> list[PredictionResult]:
        """Predictions naming a metric the run did not report."""
        return [r for r in self.results if r.verdict is Verdict.INCONCLUSIVE]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "claim_id": self.claim_id,
            "verdict": self.verdict.value,
            "results": [r.to_dict() for r in self.results],
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Evaluation":
        return cls(
            run_id=data["run_id"],
            claim_id=data["claim_id"],
            verdict=Verdict(data["verdict"]),
            results=[PredictionResult.from_dict(r) for r in data.get("results", [])],
            timestamp=data.get("timestamp", 0.0),
        )


@dataclass
class Unknown:
    """A question the work exposed but did not answer.

    `probe` is the configuration change that would investigate it — an unknown
    with a probe is a rerun waiting to happen, not just a note.
    """

    id: str
    question: str
    raised_by: str
    status: UnknownStatus = UnknownStatus.OPEN
    probe: dict[str, Any] = field(default_factory=dict)
    resolution: str = ""
    raised_at: float = 0.0
    resolved_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "raised_by": self.raised_by,
            "status": self.status.value,
            "probe": dict(self.probe),
            "resolution": self.resolution,
            "raised_at": self.raised_at,
            "resolved_at": self.resolved_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Unknown":
        return cls(
            id=data["id"],
            question=data["question"],
            raised_by=data["raised_by"],
            status=UnknownStatus(data.get("status", "open")),
            probe=dict(data.get("probe", {})),
            resolution=data.get("resolution", ""),
            raised_at=data.get("raised_at", 0.0),
            resolved_at=data.get("resolved_at"),
        )


class Inquiry:
    """Append-only ledger of claims, runs, verdicts, revisions, and unknowns.

    Persist it with `save()` and reload it with `load()` so a later session
    reads what was already tried instead of re-deriving it.
    """

    def __init__(self, name: str = "haas-inquiry") -> None:
        self.name = name
        self.claims: dict[str, Claim] = {}
        self.runs: list[RunRecord] = []
        self.evaluations: list[Evaluation] = []
        self.unknowns: dict[str, Unknown] = {}
        self._lineage_seq = 0
        self._run_seq = 0
        self._unknown_seq = 0

    # ---- Hypothesize ----

    def hypothesize(
        self,
        statement: str,
        predictions: list[Prediction] | None = None,
        sources: list[str] | None = None,
        rationale: str = "",
        timestamp: float | None = None,
    ) -> Claim:
        """State a new claim. Its priority date is set here and never moves."""
        ts = timestamp if timestamp is not None else time.time()
        self._lineage_seq += 1
        lineage_id = f"C{self._lineage_seq}"

        claim = Claim(
            id=f"{lineage_id}v1",
            lineage_id=lineage_id,
            statement=statement,
            predictions=list(predictions or []),
            version=1,
            status=ClaimStatus.PROPOSED,
            first_stated=ts,
            stated_at=ts,
            sources=list(sources or []),
            rationale=rationale,
        )
        self.claims[claim.id] = claim
        return claim

    # ---- Run ----

    def record_run(
        self,
        claim_id: str,
        metrics: dict[str, float],
        config: dict[str, Any] | None = None,
        seed: int | None = None,
        notes: str = "",
        timestamp: float | None = None,
    ) -> RunRecord:
        """Record what a run measured. Does not judge it — that is `evaluate`."""
        self._require_claim(claim_id)
        self._run_seq += 1
        run = RunRecord(
            id=f"R{self._run_seq}",
            claim_id=claim_id,
            metrics=dict(metrics),
            config=dict(config or {}),
            seed=seed,
            notes=notes,
            timestamp=timestamp if timestamp is not None else time.time(),
        )
        self.runs.append(run)
        return run

    # ---- Observe / falsify ----

    def evaluate(self, run: RunRecord, timestamp: float | None = None) -> Evaluation:
        """Check a run against its claim and update the claim's status.

        One failed prediction falsifies the claim — corroboration is not
        symmetric with refutation. A prediction whose metric the run never
        reported is INCONCLUSIVE and raises an unknown: an unmeasured
        prediction is a gap in instrumentation, not a pass.
        """
        claim = self._require_claim(run.claim_id)
        ts = timestamp if timestamp is not None else time.time()

        results = [
            PredictionResult(
                prediction=p,
                observed=run.metrics.get(p.metric),
                verdict=p.check(run.metrics),
            )
            for p in claim.predictions
        ]

        if not results:
            verdict = Verdict.INCONCLUSIVE
        elif any(r.verdict is Verdict.FALSIFIED for r in results):
            verdict = Verdict.FALSIFIED
        elif any(r.verdict is Verdict.INCONCLUSIVE for r in results):
            verdict = Verdict.INCONCLUSIVE
        else:
            verdict = Verdict.SUPPORTED

        evaluation = Evaluation(
            run_id=run.id,
            claim_id=claim.id,
            verdict=verdict,
            results=results,
            timestamp=ts,
        )
        self.evaluations.append(evaluation)

        # A superseded or retired claim keeps its record; late runs do not revive it.
        if claim.is_live:
            if verdict is Verdict.FALSIFIED:
                claim.status = ClaimStatus.FALSIFIED
            elif verdict is Verdict.SUPPORTED:
                claim.status = ClaimStatus.SUPPORTED

        # Search for unknowns: anything the run failed to measure.
        for result in results:
            if result.verdict is Verdict.INCONCLUSIVE:
                self.raise_unknown(
                    question=(
                        f"Run did not measure {result.prediction.metric!r}, "
                        f"required by {claim.id}: {result.prediction.describe()}"
                    ),
                    raised_by=run.id,
                    probe={"measure": result.prediction.metric},
                    timestamp=ts,
                )

        return evaluation

    def run_and_evaluate(
        self,
        claim_id: str,
        metrics: dict[str, float],
        config: dict[str, Any] | None = None,
        seed: int | None = None,
        notes: str = "",
        timestamp: float | None = None,
    ) -> tuple[RunRecord, Evaluation]:
        """Record a run and evaluate it in one step."""
        run = self.record_run(
            claim_id, metrics, config=config, seed=seed, notes=notes, timestamp=timestamp
        )
        return run, self.evaluate(run, timestamp=timestamp)

    # ---- Edit the claim ----

    def revise(
        self,
        claim_id: str,
        statement: str | None = None,
        predictions: list[Prediction] | None = None,
        reason: str = "",
        sources: list[str] | None = None,
        timestamp: float | None = None,
    ) -> Claim:
        """Supersede a claim with a corrected version.

        The old claim is marked SUPERSEDED, not deleted, and the two are linked
        in both directions. The successor inherits `lineage_id` and
        `first_stated` — precedence carries across the edit.
        """
        old = self._require_claim(claim_id)
        if old.status is ClaimStatus.SUPERSEDED:
            raise ValueError(
                f"{old.id} was already superseded by {old.superseded_by}; "
                "revise the head of the lineage, not a superseded version"
            )
        if old.status is ClaimStatus.RETIRED:
            raise ValueError(f"{old.id} was retired; state a new claim instead")

        ts = timestamp if timestamp is not None else time.time()
        new = Claim(
            id=f"{old.lineage_id}v{old.version + 1}",
            lineage_id=old.lineage_id,
            statement=statement if statement is not None else old.statement,
            predictions=list(predictions) if predictions is not None else list(old.predictions),
            version=old.version + 1,
            status=ClaimStatus.PROPOSED,
            first_stated=old.first_stated,   # precedence carries
            stated_at=ts,
            supersedes=old.id,
            sources=list(sources) if sources is not None else list(old.sources),
            rationale=reason,
        )
        old.status = ClaimStatus.SUPERSEDED
        old.superseded_by = new.id
        self.claims[new.id] = new
        return new

    def retire(self, claim_id: str, reason: str = "") -> Claim:
        """Withdraw a claim without a successor. The record stays."""
        claim = self._require_claim(claim_id)
        if claim.status is ClaimStatus.SUPERSEDED:
            raise ValueError(f"{claim.id} was already superseded by {claim.superseded_by}")
        claim.status = ClaimStatus.RETIRED
        if reason:
            claim.rationale = reason
        return claim

    # ---- Search for unknowns ----

    def raise_unknown(
        self,
        question: str,
        raised_by: str,
        probe: dict[str, Any] | None = None,
        timestamp: float | None = None,
    ) -> Unknown:
        """Register an open question. Repeating a still-open one is a no-op."""
        for existing in self.unknowns.values():
            if existing.question == question and existing.status is not UnknownStatus.RESOLVED:
                return existing

        self._unknown_seq += 1
        unknown = Unknown(
            id=f"U{self._unknown_seq}",
            question=question,
            raised_by=raised_by,
            probe=dict(probe or {}),
            raised_at=timestamp if timestamp is not None else time.time(),
        )
        self.unknowns[unknown.id] = unknown
        return unknown

    def resolve_unknown(
        self, unknown_id: str, resolution: str, timestamp: float | None = None
    ) -> Unknown:
        """Close an open question with the answer that closed it."""
        if unknown_id not in self.unknowns:
            raise KeyError(f"unknown {unknown_id!r} not in ledger")
        unknown = self.unknowns[unknown_id]
        unknown.status = UnknownStatus.RESOLVED
        unknown.resolution = resolution
        unknown.resolved_at = timestamp if timestamp is not None else time.time()
        return unknown

    def open_unknowns(self) -> list[Unknown]:
        """Questions still waiting on an answer."""
        return [u for u in self.unknowns.values() if u.status is not UnknownStatus.RESOLVED]

    # ---- Queries ----

    def lineage(self, claim_id: str) -> list[Claim]:
        """Every version of a claim, v1 first. The full precedence chain."""
        claim = self._require_claim(claim_id)
        versions = [c for c in self.claims.values() if c.lineage_id == claim.lineage_id]
        return sorted(versions, key=lambda c: c.version)

    def head(self, claim_id: str) -> Claim:
        """The live version of a claim's lineage."""
        return self.lineage(claim_id)[-1]

    def live_claims(self) -> list[Claim]:
        """Claims that have not been superseded or retired."""
        return [c for c in self.claims.values() if c.is_live]

    def runs_for(self, claim_id: str) -> list[RunRecord]:
        return [r for r in self.runs if r.claim_id == claim_id]

    def evaluations_for(self, claim_id: str) -> list[Evaluation]:
        return [e for e in self.evaluations if e.claim_id == claim_id]

    def latest_evaluation(self, claim_id: str) -> Evaluation | None:
        evaluations = self.evaluations_for(claim_id)
        return evaluations[-1] if evaluations else None

    # ---- Rerun ----

    def next_actions(self) -> list[str]:
        """What the cycle says to do next, given the current ledger state.

        Supported claims still appear here until they have survived
        `MIN_CORROBORATING_RUNS`, and an unfalsifiable claim is always flagged —
        a claim no run can contradict is not a finding.
        """
        actions: list[str] = []

        for claim in sorted(self.live_claims(), key=lambda c: (c.lineage_id, c.version)):
            if not claim.is_falsifiable:
                actions.append(
                    f"{claim.id}: state a prediction — the claim as written cannot be falsified"
                )
                continue

            if claim.status is ClaimStatus.PROPOSED:
                actions.append(f"{claim.id}: run it — stated but never tested")

            elif claim.status is ClaimStatus.FALSIFIED:
                evaluation = self.latest_evaluation(claim.id)
                broke = (
                    ", ".join(
                        f"{r.prediction.describe()} (observed {r.observed:g})"
                        for r in evaluation.failures
                        if r.observed is not None
                    )
                    if evaluation
                    else ""
                )
                detail = f" — failed on {broke}" if broke else ""
                actions.append(f"{claim.id}: edit the claim{detail}")

            elif claim.status is ClaimStatus.SUPPORTED:
                survived = len(
                    [
                        e
                        for e in self.evaluations_for(claim.id)
                        if e.verdict is Verdict.SUPPORTED
                    ]
                )
                if survived < MIN_CORROBORATING_RUNS:
                    actions.append(
                        f"{claim.id}: rerun — survived {survived} of "
                        f"{MIN_CORROBORATING_RUNS} runs, still provisional"
                    )

            latest = self.latest_evaluation(claim.id)
            if latest is not None and latest.verdict is Verdict.INCONCLUSIVE and latest.unmeasured:
                missing = ", ".join(r.prediction.metric for r in latest.unmeasured)
                actions.append(f"{claim.id}: measure {missing} — the run could not judge it")

        for unknown in self.open_unknowns():
            if unknown.probe:
                probe = ", ".join(f"{k}={v}" for k, v in unknown.probe.items())
                actions.append(f"{unknown.id}: rerun with {probe} — {unknown.question}")
            else:
                actions.append(f"{unknown.id}: open question — {unknown.question}")

        return actions

    def summary(self) -> dict[str, Any]:
        """Counts across the ledger."""
        by_status = {status.value: 0 for status in ClaimStatus}
        for claim in self.claims.values():
            by_status[claim.status.value] += 1

        return {
            "name": self.name,
            "claims": len(self.claims),
            "lineages": len({c.lineage_id for c in self.claims.values()}),
            "by_status": by_status,
            "runs": len(self.runs),
            "evaluations": len(self.evaluations),
            "falsifications": len(
                [e for e in self.evaluations if e.verdict is Verdict.FALSIFIED]
            ),
            "unknowns_open": len(self.open_unknowns()),
            "unknowns_total": len(self.unknowns),
        }

    def format_ledger(self) -> str:
        """Render the ledger as text — claims with lineage, unknowns, next actions."""
        lines = [f"INQUIRY: {self.name}", "=" * 60, ""]

        lineages: dict[str, list[Claim]] = {}
        for claim in self.claims.values():
            lineages.setdefault(claim.lineage_id, []).append(claim)

        for lineage_id in sorted(lineages):
            versions = sorted(lineages[lineage_id], key=lambda c: c.version)
            first = versions[0]
            lines.append(f"{lineage_id}  (first stated {_fmt_time(first.first_stated)})")
            for claim in versions:
                runs = len(self.runs_for(claim.id))
                lines.append(
                    f"  v{claim.version} [{claim.status.value.upper():<10}] "
                    f"{claim.statement}  ({runs} run{'s' if runs != 1 else ''})"
                )
                for prediction in claim.predictions:
                    lines.append(f"        predicts: {prediction.describe()}")
                if claim.rationale:
                    lines.append(f"        because: {claim.rationale}")
                if claim.sources:
                    lines.append(f"        source: {', '.join(claim.sources)}")
            lines.append("")

        open_unknowns = self.open_unknowns()
        lines.append(f"OPEN UNKNOWNS ({len(open_unknowns)})")
        lines.append("-" * 60)
        for unknown in open_unknowns:
            lines.append(f"  {unknown.id}  {unknown.question}")
            lines.append(f"        raised by {unknown.raised_by}")
        if not open_unknowns:
            lines.append("  none")
        lines.append("")

        actions = self.next_actions()
        lines.append(f"NEXT ACTIONS ({len(actions)})")
        lines.append("-" * 60)
        for action in actions:
            lines.append(f"  {action}")
        if not actions:
            lines.append("  none")

        return "\n".join(lines)

    # ---- Persistence ----

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "claims": [c.to_dict() for c in self.claims.values()],
            "runs": [r.to_dict() for r in self.runs],
            "evaluations": [e.to_dict() for e in self.evaluations],
            "unknowns": [u.to_dict() for u in self.unknowns.values()],
            "counters": {
                "lineage": self._lineage_seq,
                "run": self._run_seq,
                "unknown": self._unknown_seq,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Inquiry":
        inquiry = cls(name=data.get("name", "haas-inquiry"))
        for claim_data in data.get("claims", []):
            claim = Claim.from_dict(claim_data)
            inquiry.claims[claim.id] = claim
        inquiry.runs = [RunRecord.from_dict(r) for r in data.get("runs", [])]
        inquiry.evaluations = [Evaluation.from_dict(e) for e in data.get("evaluations", [])]
        for unknown_data in data.get("unknowns", []):
            unknown = Unknown.from_dict(unknown_data)
            inquiry.unknowns[unknown.id] = unknown

        counters = data.get("counters", {})
        inquiry._lineage_seq = counters.get("lineage", len(inquiry.claims))
        inquiry._run_seq = counters.get("run", len(inquiry.runs))
        inquiry._unknown_seq = counters.get("unknown", len(inquiry.unknowns))
        return inquiry

    def save(self, path: str | Path) -> Path:
        """Write the ledger to JSON so the next session inherits it."""
        target = Path(path)
        target.write_text(json.dumps(self.to_dict(), indent=2))
        return target

    @classmethod
    def load(cls, path: str | Path) -> "Inquiry":
        """Read a ledger written by `save`."""
        return cls.from_dict(json.loads(Path(path).read_text()))

    # ---- Internals ----

    def _require_claim(self, claim_id: str) -> Claim:
        if claim_id not in self.claims:
            raise KeyError(f"claim {claim_id!r} not in ledger")
        return self.claims[claim_id]


def _fmt_time(timestamp: float) -> str:
    """Render a priority date in UTC — the record reads the same on every machine."""
    return time.strftime("%Y-%m-%d", time.gmtime(timestamp)) if timestamp else "unknown"


# ------------------------------------
# Bridges — turning a run into metrics
# ------------------------------------


def metrics_from_result(result: "SimResult") -> dict[str, float]:
    """Extract falsifiable metrics from a unified simulation result.

    These are the observables a prediction can be written against.
    """
    events = [e["event"] for e in result.log.events]
    steps = len(events)

    metrics: dict[str, float] = {"steps": float(steps)}
    if steps == 0:
        return metrics

    risks = [float(e["risk"]) for e in events]
    decisions = [str(e["decision"]).upper() for e in events]
    alert_count = sum(len(e.get("alerts", [])) for e in events)
    near_misses = sum(
        1
        for e in events
        if float(e["risk"]) > NEAR_MISS_RISK_THRESHOLD
        and str(e["decision"]).upper() != "STOP"
    )
    compound_steps = sum(1 for e in events if e.get("signals", {}).get("compound_risk"))

    metrics.update({
        "mean_risk": sum(risks) / steps,
        "max_risk": max(risks),
        "final_risk": risks[-1],
        "mean_confidence": sum(float(e["confidence"]) for e in events) / steps,
        "stop_fraction": decisions.count("STOP") / steps,
        "slow_fraction": decisions.count("SLOW") / steps,
        "move_fraction": decisions.count("MOVE") / steps,
        "near_miss_count": float(near_misses),
        "alert_count": float(alert_count),
        "compound_risk_steps": float(compound_steps),
        "violation_count": float(len(result.all_violations)),
        "critical_violation_count": float(
            sum(1 for v in result.all_violations if v.severity.value == "critical")
        ),
        "final_sensor_noise": float(result.state.sensor_noise),
        "final_brake_efficiency": float(result.state.brake_efficiency),
    })

    if result.energy is not None:
        metrics.update({
            "fatigue_score": float(result.energy.fatigue_score),
            "collapse_distance": float(result.energy.collapse_distance),
            "cumulative_ai_tax": float(result.energy.cumulative_ai_tax),
            "false_alert_total": float(result.energy.false_alert_total),
        })

    return metrics


def metrics_from_store(store: "EventStore", last_n: int = 50) -> dict[str, float]:
    """Extract metrics from persisted events — for claims tested across sessions."""
    average_risk = store.average_risk(last_n=last_n)
    return {
        "event_count": float(store.count_events()),
        "mean_risk": float(average_risk) if average_risk is not None else 0.0,
        "near_miss_count": float(store.near_miss_count()),
        "override_count": float(store.override_count()),
        "violation_count": float(store.violation_count()),
        "critical_violation_count": float(store.violation_count(severity="critical")),
    }
