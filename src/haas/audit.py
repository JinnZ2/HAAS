"""Internal audit — assess alignment to the protection matrix.

Generates a structured audit against every threat in the registry.
For each threat, the audit evaluates three dimensions:

  1. Control exists    — Is the specified control implemented?
  2. Signal monitored  — Is the detection signal actively observed?
  3. Enforcement proof — Is there evidence the control has been enforced?

Each dimension is scored 0–3 (None / Partial / Implemented / Verified).
The audit produces per-pair scores, per-entity scores, an overall
maturity rating, and a gap analysis identifying the weakest links.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

from .protections import THREAT_REGISTRY, Entity, Threat


class Maturity(IntEnum):
    """Maturity level for a single audit dimension."""

    NONE = 0         # No evidence of implementation
    PARTIAL = 1      # Acknowledged but incomplete
    IMPLEMENTED = 2  # In place but not independently verified
    VERIFIED = 3     # In place with evidence of effectiveness


MATURITY_LABELS: dict[Maturity, str] = {
    Maturity.NONE: "None",
    Maturity.PARTIAL: "Partial",
    Maturity.IMPLEMENTED: "Implemented",
    Maturity.VERIFIED: "Verified",
}


@dataclass
class ThreatAssessment:
    """Audit response for a single threat."""

    threat_id: str
    control_exists: Maturity = Maturity.NONE
    signal_monitored: Maturity = Maturity.NONE
    enforcement_proof: Maturity = Maturity.NONE
    notes: str = ""

    @property
    def score(self) -> int:
        """Total score for this threat (0–9)."""
        return self.control_exists + self.signal_monitored + self.enforcement_proof

    @property
    def max_score(self) -> int:
        return 9

    @property
    def pct(self) -> float:
        return self.score / self.max_score * 100


@dataclass
class PairScore:
    """Aggregate score for one directional entity pair."""

    target: Entity
    source: Entity
    assessments: list[ThreatAssessment]

    @property
    def score(self) -> int:
        return sum(a.score for a in self.assessments)

    @property
    def max_score(self) -> int:
        return sum(a.max_score for a in self.assessments)

    @property
    def pct(self) -> float:
        return (self.score / self.max_score * 100) if self.max_score > 0 else 0.0

    @property
    def gap_count(self) -> int:
        """Number of threats with at least one dimension at NONE."""
        return sum(
            1 for a in self.assessments
            if min(a.control_exists, a.signal_monitored, a.enforcement_proof) == Maturity.NONE
        )


@dataclass
class EntityScore:
    """Aggregate protection score for one entity (as target)."""

    entity: Entity
    pair_scores: list[PairScore]

    @property
    def score(self) -> int:
        return sum(p.score for p in self.pair_scores)

    @property
    def max_score(self) -> int:
        return sum(p.max_score for p in self.pair_scores)

    @property
    def pct(self) -> float:
        return (self.score / self.max_score * 100) if self.max_score > 0 else 0.0

    @property
    def weakest_pair(self) -> PairScore | None:
        if not self.pair_scores:
            return None
        return min(self.pair_scores, key=lambda p: p.pct)


# ---- Overall maturity rating ----

def overall_rating(pct: float) -> str:
    """Map an overall percentage to a maturity rating label."""
    if pct >= 90:
        return "Exemplary"
    if pct >= 75:
        return "Strong"
    if pct >= 60:
        return "Developing"
    if pct >= 40:
        return "Weak"
    if pct >= 20:
        return "Critical"
    return "Non-existent"


# ============================================================
# Audit lifecycle
# ============================================================

@dataclass
class Audit:
    """A complete protection matrix audit.

    Usage:
        audit = create_audit()
        # Fill in assessments:
        audit.set("H_AI_1", control=Maturity.VERIFIED, signal=Maturity.IMPLEMENTED, ...)
        # Generate report:
        report = audit.report()
    """

    assessments: dict[str, ThreatAssessment] = field(default_factory=dict)

    def set(
        self,
        threat_id: str,
        control: Maturity | int = Maturity.NONE,
        signal: Maturity | int = Maturity.NONE,
        enforcement: Maturity | int = Maturity.NONE,
        notes: str = "",
    ) -> None:
        """Set the assessment for a threat."""
        if threat_id not in self.assessments:
            raise KeyError(f"Unknown threat ID: {threat_id}")
        a = self.assessments[threat_id]
        a.control_exists = Maturity(control)
        a.signal_monitored = Maturity(signal)
        a.enforcement_proof = Maturity(enforcement)
        if notes:
            a.notes = notes

    def get(self, threat_id: str) -> ThreatAssessment:
        return self.assessments[threat_id]

    # ---- Scoring ----

    def pair_scores(self) -> list[PairScore]:
        """Compute scores grouped by (target, source) pair."""
        pairs: dict[tuple[Entity, Entity], list[ThreatAssessment]] = {}
        for t in THREAT_REGISTRY:
            a = self.assessments[t.id]
            pairs.setdefault((t.target, t.source), []).append(a)
        return [
            PairScore(target=t, source=s, assessments=alist)
            for (t, s), alist in sorted(pairs.items(), key=lambda x: (x[0][0].value, x[0][1].value))
        ]

    def entity_scores(self) -> list[EntityScore]:
        """Compute protection scores grouped by target entity."""
        ps = self.pair_scores()
        by_entity: dict[Entity, list[PairScore]] = {}
        for p in ps:
            by_entity.setdefault(p.target, []).append(p)
        return [
            EntityScore(entity=e, pair_scores=plist)
            for e, plist in sorted(by_entity.items(), key=lambda x: x[0].value)
        ]

    def overall_score(self) -> tuple[int, int, float]:
        """Return (achieved, maximum, percentage)."""
        achieved = sum(a.score for a in self.assessments.values())
        maximum = sum(a.max_score for a in self.assessments.values())
        pct = (achieved / maximum * 100) if maximum > 0 else 0.0
        return achieved, maximum, pct

    def gaps(self) -> list[tuple[Threat, ThreatAssessment]]:
        """Return all threats where any dimension is at NONE — ordered worst first."""
        result = []
        for t in THREAT_REGISTRY:
            a = self.assessments[t.id]
            if min(a.control_exists, a.signal_monitored, a.enforcement_proof) == Maturity.NONE:
                result.append((t, a))
        result.sort(key=lambda x: x[1].score)
        return result

    def strengths(self) -> list[tuple[Threat, ThreatAssessment]]:
        """Return all threats fully verified (score 9/9)."""
        result = []
        for t in THREAT_REGISTRY:
            a = self.assessments[t.id]
            if a.score == a.max_score:
                result.append((t, a))
        return result

    # ---- Report generation ----

    def report(self) -> str:
        """Generate a full text audit report."""
        achieved, maximum, pct = self.overall_score()
        rating = overall_rating(pct)
        entity_sc = self.entity_scores()
        gap_list = self.gaps()
        strength_list = self.strengths()

        lines: list[str] = []
        lines.append("=" * 60)
        lines.append("  HAAS-Q PROTECTION MATRIX AUDIT REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Overall
        lines.append(f"  Overall Score:  {achieved} / {maximum}  ({pct:.1f}%)")
        lines.append(f"  Maturity Rating: {rating}")
        lines.append("")

        # Per-entity protection scores
        lines.append("-" * 60)
        lines.append("  ENTITY PROTECTION SCORES")
        lines.append("-" * 60)
        for es in entity_sc:
            lines.append(f"  {es.entity.value.upper():15s}  {es.score:3d}/{es.max_score:<3d}  ({es.pct:.0f}%)")
            for ps in es.pair_scores:
                marker = "  **GAP**" if ps.gap_count > 0 else ""
                lines.append(
                    f"    <- {ps.source.value:15s}  {ps.score:3d}/{ps.max_score:<3d}  "
                    f"({ps.pct:.0f}%){marker}"
                )
        lines.append("")

        # Protection matrix heatmap (percentage per pair)
        lines.append("-" * 60)
        lines.append("  PROTECTION MATRIX (% score per pair)")
        lines.append("-" * 60)
        entities = list(Entity)
        header = "  Protected FROM ->  " + "  ".join(f"{e.value[:5]:>5s}" for e in entities)
        lines.append(header)
        pair_map = {(ps.target, ps.source): ps for ps in self.pair_scores()}
        for target in entities:
            row = f"  {target.value:15s}  "
            for source in entities:
                if target == source:
                    row += "    - "
                else:
                    ps = pair_map.get((target, source))
                    if ps:
                        row += f" {ps.pct:4.0f}% "
                    else:
                        row += "   N/A "
            lines.append(row)
        lines.append("")

        # Gaps (worst first)
        lines.append("-" * 60)
        lines.append(f"  GAPS ({len(gap_list)} threats with unaddressed dimensions)")
        lines.append("-" * 60)
        if gap_list:
            for t, a in gap_list:
                dims = []
                if a.control_exists == Maturity.NONE:
                    dims.append("control")
                if a.signal_monitored == Maturity.NONE:
                    dims.append("signal")
                if a.enforcement_proof == Maturity.NONE:
                    dims.append("enforcement")
                lines.append(
                    f"  [{t.id}] {t.target.value} <- {t.source.value}: {t.name}"
                )
                lines.append(f"    Missing: {', '.join(dims)}  |  Score: {a.score}/9")
                if a.notes:
                    lines.append(f"    Note: {a.notes}")
        else:
            lines.append("  No gaps found — all dimensions addressed.")
        lines.append("")

        # Strengths
        lines.append("-" * 60)
        lines.append(f"  STRENGTHS ({len(strength_list)} threats fully verified)")
        lines.append("-" * 60)
        if strength_list:
            for t, a in strength_list:
                lines.append(f"  [{t.id}] {t.target.value} <- {t.source.value}: {t.name}")
        else:
            lines.append("  No threats fully verified yet.")
        lines.append("")

        # Recommendations
        lines.append("-" * 60)
        lines.append("  PRIORITY RECOMMENDATIONS")
        lines.append("-" * 60)
        # Find the weakest entity
        if entity_sc:
            weakest_entity = min(entity_sc, key=lambda e: e.pct)
            lines.append(
                f"  1. Weakest entity: {weakest_entity.entity.value.upper()} "
                f"({weakest_entity.pct:.0f}%) — prioritize protection controls"
            )
            if weakest_entity.weakest_pair:
                wp = weakest_entity.weakest_pair
                lines.append(
                    f"     Weakest vector: <- {wp.source.value} ({wp.pct:.0f}%)"
                )
        # Count dimensions
        total_none = sum(
            1 for a in self.assessments.values()
            for m in [a.control_exists, a.signal_monitored, a.enforcement_proof]
            if m == Maturity.NONE
        )
        total_dims = len(self.assessments) * 3
        lines.append(f"  2. {total_none}/{total_dims} dimensions unaddressed")

        # Enforcement gap
        enforce_none = sum(
            1 for a in self.assessments.values()
            if a.enforcement_proof == Maturity.NONE
        )
        lines.append(
            f"  3. Enforcement evidence missing for {enforce_none}/{len(self.assessments)} threats"
        )

        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)


def create_audit() -> Audit:
    """Create a new blank audit with entries for every threat in the registry."""
    assessments = {
        t.id: ThreatAssessment(threat_id=t.id)
        for t in THREAT_REGISTRY
    }
    return Audit(assessments=assessments)


def create_audit_from_responses(responses: dict[str, dict[str, int | str]]) -> Audit:
    """Create an audit from a dict of responses.

    Expected format:
        {
            "H_AI_1": {"control": 2, "signal": 3, "enforcement": 1, "notes": "..."},
            ...
        }
    """
    audit = create_audit()
    for threat_id, resp in responses.items():
        audit.set(
            threat_id,
            control=resp.get("control", 0),
            signal=resp.get("signal", 0),
            enforcement=resp.get("enforcement", 0),
            notes=resp.get("notes", ""),
        )
    return audit


def blank_questionnaire() -> list[dict[str, Any]]:
    """Generate a blank questionnaire as a list of dicts (e.g., for CSV/JSON export).

    Each entry includes the threat details and fields to fill in.
    """
    questions = []
    for t in THREAT_REGISTRY:
        questions.append({
            "threat_id": t.id,
            "target": t.target.value,
            "source": t.source.value,
            "threat_name": t.name,
            "mechanism": t.mechanism,
            "expected_signal": t.signal,
            "expected_control": t.control,
            "q1_control_exists": "Is this control implemented? (0=None, 1=Partial, 2=Implemented, 3=Verified)",
            "q2_signal_monitored": "Is this signal actively monitored? (0=None, 1=Partial, 2=Implemented, 3=Verified)",
            "q3_enforcement_proof": "Is there evidence of enforcement? (0=None, 1=Partial, 2=Implemented, 3=Verified)",
            "notes": "",
        })
    return questions
