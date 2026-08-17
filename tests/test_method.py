"""Tests for the scientific method layer — claims, runs, falsification, precedence."""

import pytest

from haas.method import (
    MIN_CORROBORATING_RUNS,
    ClaimStatus,
    Inquiry,
    Prediction,
    UnknownStatus,
    Verdict,
    metrics_from_result,
    metrics_from_store,
)
from haas.simulation import SimConfig, run_unified_simulation
from haas.store import EventStore


# ---- Predictions ----

def test_prediction_rejects_unknown_operator():
    with pytest.raises(ValueError):
        Prediction("mean_risk", "=~", 0.5)


def test_prediction_rejects_negative_tolerance():
    with pytest.raises(ValueError):
        Prediction("mean_risk", "<", 0.5, tolerance=-0.1)


def test_prediction_supported():
    assert Prediction("mean_risk", "<", 0.5).check({"mean_risk": 0.3}) is Verdict.SUPPORTED


def test_prediction_falsified():
    assert Prediction("mean_risk", "<", 0.5).check({"mean_risk": 0.9}) is Verdict.FALSIFIED


def test_prediction_missing_metric_is_inconclusive():
    """An unmeasured prediction is a gap in instrumentation, not a pass."""
    assert Prediction("fatigue_score", ">", 1.0).check({"mean_risk": 0.3}) is Verdict.INCONCLUSIVE


def test_tolerance_widens_in_the_claims_favour():
    strict = Prediction("mean_risk", "<", 0.5)
    lenient = Prediction("mean_risk", "<", 0.5, tolerance=0.1)
    metrics = {"mean_risk": 0.55}
    assert strict.check(metrics) is Verdict.FALSIFIED
    assert lenient.check(metrics) is Verdict.SUPPORTED


def test_tolerance_applies_to_greater_than():
    lenient = Prediction("mean_risk", ">", 0.5, tolerance=0.1)
    assert lenient.check({"mean_risk": 0.45}) is Verdict.SUPPORTED
    assert lenient.check({"mean_risk": 0.35}) is Verdict.FALSIFIED


def test_equality_uses_tolerance_band():
    prediction = Prediction("stop_fraction", "==", 0.5, tolerance=0.05)
    assert prediction.check({"stop_fraction": 0.52}) is Verdict.SUPPORTED
    assert prediction.check({"stop_fraction": 0.7}) is Verdict.FALSIFIED


def test_inequality_operator():
    prediction = Prediction("stop_fraction", "!=", 0.0)
    assert prediction.check({"stop_fraction": 0.3}) is Verdict.SUPPORTED
    assert prediction.check({"stop_fraction": 0.0}) is Verdict.FALSIFIED


def test_prediction_describe_includes_tolerance():
    assert Prediction("mean_risk", "<", 0.5, tolerance=0.1).describe() == "mean_risk < 0.5 ±0.1"
    assert Prediction("mean_risk", "<", 0.5).describe() == "mean_risk < 0.5"


# ---- Hypothesize ----

def test_hypothesize_starts_proposed():
    inquiry = Inquiry()
    claim = inquiry.hypothesize("fatigue raises risk", [Prediction("mean_risk", ">", 0.1)])
    assert claim.status is ClaimStatus.PROPOSED
    assert claim.version == 1
    assert claim.id == "C1v1"
    assert claim.lineage_id == "C1"


def test_hypothesize_sets_precedence_date():
    inquiry = Inquiry()
    claim = inquiry.hypothesize("a claim", timestamp=1000.0)
    assert claim.first_stated == 1000.0
    assert claim.stated_at == 1000.0


def test_claim_without_predictions_is_not_falsifiable():
    inquiry = Inquiry()
    claim = inquiry.hypothesize("safety improves")
    assert not claim.is_falsifiable


# ---- Run and evaluate ----

def test_run_supports_claim():
    inquiry = Inquiry()
    claim = inquiry.hypothesize("risk stays low", [Prediction("mean_risk", "<", 0.5)])
    _, evaluation = inquiry.run_and_evaluate(claim.id, {"mean_risk": 0.2})
    assert evaluation.verdict is Verdict.SUPPORTED
    assert claim.status is ClaimStatus.SUPPORTED


def test_run_falsifies_claim():
    inquiry = Inquiry()
    claim = inquiry.hypothesize("risk stays low", [Prediction("mean_risk", "<", 0.5)])
    _, evaluation = inquiry.run_and_evaluate(claim.id, {"mean_risk": 0.9})
    assert evaluation.verdict is Verdict.FALSIFIED
    assert claim.status is ClaimStatus.FALSIFIED
    assert len(evaluation.failures) == 1
    assert evaluation.failures[0].observed == 0.9


def test_one_failure_falsifies_the_whole_claim():
    """Refutation is asymmetric — a single counterexample is enough."""
    inquiry = Inquiry()
    claim = inquiry.hypothesize(
        "both hold",
        [Prediction("mean_risk", "<", 0.5), Prediction("stop_fraction", "<", 0.1)],
    )
    _, evaluation = inquiry.run_and_evaluate(
        claim.id, {"mean_risk": 0.2, "stop_fraction": 0.8}
    )
    assert evaluation.verdict is Verdict.FALSIFIED


def test_falsified_beats_inconclusive():
    inquiry = Inquiry()
    claim = inquiry.hypothesize(
        "both hold",
        [Prediction("mean_risk", "<", 0.5), Prediction("never_measured", "<", 1.0)],
    )
    _, evaluation = inquiry.run_and_evaluate(claim.id, {"mean_risk": 0.9})
    assert evaluation.verdict is Verdict.FALSIFIED


def test_unfalsifiable_claim_is_never_supported():
    inquiry = Inquiry()
    claim = inquiry.hypothesize("safety improves")
    _, evaluation = inquiry.run_and_evaluate(claim.id, {"mean_risk": 0.1})
    assert evaluation.verdict is Verdict.INCONCLUSIVE
    assert claim.status is ClaimStatus.PROPOSED


def test_run_records_seed_and_config():
    inquiry = Inquiry()
    claim = inquiry.hypothesize("risk stays low", [Prediction("mean_risk", "<", 0.5)])
    run = inquiry.record_run(claim.id, {"mean_risk": 0.2}, config={"steps": 50}, seed=7)
    assert run.seed == 7
    assert run.config == {"steps": 50}
    assert inquiry.runs_for(claim.id) == [run]


def test_run_against_unknown_claim_raises():
    inquiry = Inquiry()
    with pytest.raises(KeyError):
        inquiry.record_run("C9v1", {"mean_risk": 0.1})


# ---- Search for unknowns ----

def test_inconclusive_run_raises_an_unknown():
    inquiry = Inquiry()
    claim = inquiry.hypothesize("fatigue climbs", [Prediction("fatigue_score", ">", 1.0)])
    inquiry.run_and_evaluate(claim.id, {"mean_risk": 0.2})

    unknowns = inquiry.open_unknowns()
    assert len(unknowns) == 1
    assert "fatigue_score" in unknowns[0].question
    assert unknowns[0].probe == {"measure": "fatigue_score"}


def test_repeating_an_open_unknown_is_a_noop():
    inquiry = Inquiry()
    first = inquiry.raise_unknown("is the 0.05 coefficient real?", raised_by="C1v1")
    second = inquiry.raise_unknown("is the 0.05 coefficient real?", raised_by="C1v2")
    assert first.id == second.id
    assert len(inquiry.unknowns) == 1


def test_resolving_an_unknown_records_the_answer():
    inquiry = Inquiry()
    unknown = inquiry.raise_unknown("does braking wear the brakes?", raised_by="R1")
    inquiry.resolve_unknown(unknown.id, "yes — measured in field data")
    assert unknown.status is UnknownStatus.RESOLVED
    assert unknown.resolution == "yes — measured in field data"
    assert unknown.resolved_at is not None
    assert inquiry.open_unknowns() == []


def test_resolved_question_can_be_reopened_as_a_new_unknown():
    inquiry = Inquiry()
    first = inquiry.raise_unknown("same question", raised_by="R1")
    inquiry.resolve_unknown(first.id, "answered")
    second = inquiry.raise_unknown("same question", raised_by="R2")
    assert second.id != first.id


def test_resolving_missing_unknown_raises():
    inquiry = Inquiry()
    with pytest.raises(KeyError):
        inquiry.resolve_unknown("U9", "nope")


# ---- Edit the claim: precedence carries ----

def test_revision_inherits_precedence():
    inquiry = Inquiry()
    v1 = inquiry.hypothesize(
        "risk = velocity / distance",
        [Prediction("mean_risk", "<", 0.5)],
        timestamp=1000.0,
    )
    inquiry.run_and_evaluate(v1.id, {"mean_risk": 0.9})
    v2 = inquiry.revise(
        v1.id,
        statement="risk = velocity / distance * fatigue",
        reason="fatigue term was missing",
        timestamp=2000.0,
    )

    assert v2.lineage_id == v1.lineage_id
    assert v2.first_stated == 1000.0     # precedence carries
    assert v2.stated_at == 2000.0        # this revision is new
    assert v2.version == 2
    assert v2.id == "C1v2"


def test_revision_links_both_directions():
    inquiry = Inquiry()
    v1 = inquiry.hypothesize("first", [Prediction("m", "<", 1.0)])
    v2 = inquiry.revise(v1.id, statement="second")
    assert v1.superseded_by == v2.id
    assert v2.supersedes == v1.id


def test_superseded_claim_is_kept_not_deleted():
    inquiry = Inquiry()
    v1 = inquiry.hypothesize("first", [Prediction("m", "<", 1.0)])
    inquiry.run_and_evaluate(v1.id, {"m": 5.0})
    inquiry.revise(v1.id, statement="second")

    assert v1.id in inquiry.claims
    assert inquiry.claims[v1.id].status is ClaimStatus.SUPERSEDED
    assert len(inquiry.evaluations_for(v1.id)) == 1


def test_revision_inherits_predictions_when_not_given():
    inquiry = Inquiry()
    v1 = inquiry.hypothesize("first", [Prediction("m", "<", 1.0)])
    v2 = inquiry.revise(v1.id, statement="reworded")
    assert v2.predictions == v1.predictions


def test_cannot_revise_a_superseded_claim():
    inquiry = Inquiry()
    v1 = inquiry.hypothesize("first", [Prediction("m", "<", 1.0)])
    inquiry.revise(v1.id, statement="second")
    with pytest.raises(ValueError, match="already superseded"):
        inquiry.revise(v1.id, statement="forked")


def test_cannot_revise_a_retired_claim():
    inquiry = Inquiry()
    claim = inquiry.hypothesize("first", [Prediction("m", "<", 1.0)])
    inquiry.retire(claim.id, reason="out of scope")
    with pytest.raises(ValueError, match="retired"):
        inquiry.revise(claim.id, statement="revived")


def test_retired_claim_keeps_its_record():
    inquiry = Inquiry()
    claim = inquiry.hypothesize("first", [Prediction("m", "<", 1.0)])
    inquiry.retire(claim.id, reason="superseded by field data")
    assert claim.status is ClaimStatus.RETIRED
    assert claim.rationale == "superseded by field data"
    assert claim.id in inquiry.claims


def test_late_run_does_not_revive_a_superseded_claim():
    inquiry = Inquiry()
    v1 = inquiry.hypothesize("first", [Prediction("m", "<", 1.0)])
    inquiry.revise(v1.id, statement="second")
    _, evaluation = inquiry.run_and_evaluate(v1.id, {"m": 0.5})
    assert evaluation.verdict is Verdict.SUPPORTED   # the run is still recorded
    assert v1.status is ClaimStatus.SUPERSEDED       # but the claim stays superseded


def test_lineage_returns_every_version_in_order():
    inquiry = Inquiry()
    v1 = inquiry.hypothesize("first", [Prediction("m", "<", 1.0)])
    v2 = inquiry.revise(v1.id, statement="second")
    v3 = inquiry.revise(v2.id, statement="third")
    assert [c.id for c in inquiry.lineage(v1.id)] == [v1.id, v2.id, v3.id]
    assert inquiry.head(v1.id).id == v3.id
    assert all(c.first_stated == v1.first_stated for c in inquiry.lineage(v1.id))


def test_live_claims_excludes_superseded_and_retired():
    inquiry = Inquiry()
    v1 = inquiry.hypothesize("first", [Prediction("m", "<", 1.0)])
    v2 = inquiry.revise(v1.id, statement="second")
    retired = inquiry.hypothesize("other", [Prediction("m", "<", 1.0)])
    inquiry.retire(retired.id)
    assert [c.id for c in inquiry.live_claims()] == [v2.id]


# ---- Rerun ----

def test_proposed_claim_is_told_to_run():
    inquiry = Inquiry()
    claim = inquiry.hypothesize("untested", [Prediction("m", "<", 1.0)])
    assert any(a.startswith(f"{claim.id}: run it") for a in inquiry.next_actions())


def test_falsified_claim_is_told_to_edit_with_the_failing_metric():
    inquiry = Inquiry()
    claim = inquiry.hypothesize("risk stays low", [Prediction("mean_risk", "<", 0.5)])
    inquiry.run_and_evaluate(claim.id, {"mean_risk": 0.9})
    actions = inquiry.next_actions()
    assert any("edit the claim" in a and "mean_risk" in a for a in actions)


def test_supported_claim_keeps_asking_for_reruns():
    """One passing run is corroboration, not proof."""
    inquiry = Inquiry()
    claim = inquiry.hypothesize("risk stays low", [Prediction("mean_risk", "<", 0.5)])
    inquiry.run_and_evaluate(claim.id, {"mean_risk": 0.2})
    assert any("rerun" in a for a in inquiry.next_actions())


def test_corroborated_claim_stops_asking():
    inquiry = Inquiry()
    claim = inquiry.hypothesize("risk stays low", [Prediction("mean_risk", "<", 0.5)])
    for _ in range(MIN_CORROBORATING_RUNS):
        inquiry.run_and_evaluate(claim.id, {"mean_risk": 0.2})
    assert not any(a.startswith(f"{claim.id}: rerun") for a in inquiry.next_actions())


def test_unfalsifiable_claim_is_flagged():
    inquiry = Inquiry()
    claim = inquiry.hypothesize("safety improves")
    actions = inquiry.next_actions()
    assert any("cannot be falsified" in a for a in actions)


def test_open_unknown_with_probe_becomes_a_rerun_instruction():
    inquiry = Inquiry()
    unknown = inquiry.raise_unknown(
        "does seeding change the outcome?", raised_by="R1", probe={"seed": 42}
    )
    assert any(f"{unknown.id}: rerun with seed=42" in a for a in inquiry.next_actions())


# ---- Ledger reporting ----

def test_summary_counts_the_cycle():
    inquiry = Inquiry()
    claim = inquiry.hypothesize("risk stays low", [Prediction("mean_risk", "<", 0.5)])
    inquiry.run_and_evaluate(claim.id, {"mean_risk": 0.9})
    inquiry.revise(claim.id, statement="risk stays low under load")

    summary = inquiry.summary()
    assert summary["claims"] == 2
    assert summary["lineages"] == 1
    assert summary["runs"] == 1
    assert summary["falsifications"] == 1
    assert summary["by_status"]["superseded"] == 1


def test_format_ledger_shows_lineage_and_actions():
    inquiry = Inquiry()
    claim = inquiry.hypothesize(
        "risk stays low",
        [Prediction("mean_risk", "<", 0.5)],
        sources=["Framework.md:53"],
    )
    inquiry.run_and_evaluate(claim.id, {"mean_risk": 0.9})
    inquiry.revise(claim.id, statement="risk stays low when rested", reason="fatigue ignored")

    text = inquiry.format_ledger()
    assert "C1" in text
    assert "SUPERSEDED" in text
    assert "risk stays low when rested" in text
    assert "fatigue ignored" in text
    assert "Framework.md:53" in text
    assert "NEXT ACTIONS" in text


def test_format_ledger_handles_empty_inquiry():
    text = Inquiry(name="fresh").format_ledger()
    assert "fresh" in text
    assert "none" in text


# ---- Persistence: the point is the next session ----

def test_ledger_round_trips_through_json(tmp_path):
    inquiry = Inquiry(name="haas-q")
    claim = inquiry.hypothesize(
        "risk stays low",
        [Prediction("mean_risk", "<", 0.5, tolerance=0.05)],
        sources=["Framework.md:53"],
        rationale="original risk equation",
    )
    inquiry.run_and_evaluate(claim.id, {"mean_risk": 0.9}, seed=7, config={"steps": 10})
    inquiry.revise(claim.id, statement="risk stays low when rested", reason="fatigue term missing")
    inquiry.raise_unknown("is 0.05 the right coefficient?", raised_by=claim.id)

    path = inquiry.save(tmp_path / "inquiry.json")
    reloaded = Inquiry.load(path)

    assert reloaded.name == "haas-q"
    assert reloaded.summary() == inquiry.summary()
    assert reloaded.claims["C1v1"].status is ClaimStatus.SUPERSEDED
    assert reloaded.claims["C1v2"].first_stated == claim.first_stated
    assert reloaded.claims["C1v1"].predictions[0].tolerance == 0.05
    assert reloaded.runs[0].seed == 7
    assert reloaded.evaluations[0].verdict is Verdict.FALSIFIED
    assert reloaded.format_ledger() == inquiry.format_ledger()


def test_reloaded_ledger_continues_numbering(tmp_path):
    """A later session must not reuse ids and overwrite history."""
    inquiry = Inquiry()
    first = inquiry.hypothesize("first", [Prediction("m", "<", 1.0)])
    inquiry.run_and_evaluate(first.id, {"m": 0.5})
    path = inquiry.save(tmp_path / "inquiry.json")

    reloaded = Inquiry.load(path)
    second = reloaded.hypothesize("second", [Prediction("m", "<", 1.0)])
    run = reloaded.record_run(second.id, {"m": 0.5})

    assert second.id == "C2v1"
    assert run.id == "R2"
    assert first.id in reloaded.claims


# ---- Bridges to real runs ----

def test_metrics_from_result_are_falsifiable_observables():
    result = run_unified_simulation(SimConfig(steps=20, enable_zones=False, seed=1))
    metrics = metrics_from_result(result)

    assert metrics["steps"] == 20
    assert 0.0 <= metrics["mean_risk"] <= 1.0
    assert 0.0 <= metrics["max_risk"] <= 1.0
    fractions = metrics["stop_fraction"] + metrics["slow_fraction"] + metrics["move_fraction"]
    assert fractions == pytest.approx(1.0)
    assert metrics["final_brake_efficiency"] <= 1.0
    assert "fatigue_score" in metrics
    assert "collapse_distance" in metrics


def test_metrics_from_empty_result_do_not_divide_by_zero():
    result = run_unified_simulation(SimConfig(steps=0))
    metrics = metrics_from_result(result)
    assert metrics == {"steps": 0.0}


def test_seeded_runs_are_reproducible():
    """Without this, no claim tested against a run can ever be disputed."""
    a = metrics_from_result(run_unified_simulation(SimConfig(steps=30, seed=42)))
    b = metrics_from_result(run_unified_simulation(SimConfig(steps=30, seed=42)))
    assert a == b


def test_metrics_from_store(tmp_path):
    with EventStore(tmp_path / "m.db") as store:
        store.record_event(risk=0.9, confidence=0.8, decision="MOVE")
        store.record_event(risk=0.1, confidence=0.9, decision="MOVE")
        metrics = metrics_from_store(store)

    assert metrics["event_count"] == 2
    assert metrics["near_miss_count"] == 1
    assert metrics["mean_risk"] == pytest.approx(0.5)


def test_metrics_from_empty_store(tmp_path):
    with EventStore(tmp_path / "empty.db") as store:
        metrics = metrics_from_store(store)
    assert metrics["event_count"] == 0
    assert metrics["mean_risk"] == 0.0


# ---- The full cycle, end to end ----

def test_full_cycle_against_a_real_simulation(tmp_path):
    """hypothesize -> run -> falsified -> edit -> unknown -> rerun."""
    inquiry = Inquiry(name="haas-q")

    # Hypothesize: an operator driven toward energy collapse gets a protective stop.
    claim = inquiry.hypothesize(
        "a run that drives the operator toward energy collapse produces at least one stop",
        [Prediction("stop_fraction", ">", 0.0)],
        sources=["Framework.md:39", "src/haas/energy.py"],
    )

    # Run.
    metrics = metrics_from_result(
        run_unified_simulation(SimConfig(steps=40, enable_zones=False, seed=99))
    )
    run, evaluation = inquiry.run_and_evaluate(
        claim.id, metrics, config={"steps": 40, "enable_zones": False}, seed=99
    )

    # The run did drive toward collapse, so the claim was fairly tested.
    assert metrics["collapse_distance"] < 0.2
    assert metrics["critical_violation_count"] > 0

    # Result: falsified. Collapse is logged as a violation and the machine keeps moving.
    assert evaluation.verdict is Verdict.FALSIFIED
    assert claim.status is ClaimStatus.FALSIFIED

    # Edit the claim, precedence intact.
    v2 = inquiry.revise(
        claim.id,
        statement="collapse is caught by the protection matrix, not the controller — "
                  "it surfaces as critical violations",
        predictions=[Prediction("critical_violation_count", ">", 0.0)],
        reason=f"falsified by {run.id}: collapse_distance 0.13 with zero stops",
    )
    assert v2.first_stated == claim.first_stated

    # Search for unknowns the failure exposed.
    unknown = inquiry.raise_unknown(
        "should collapse_distance feed control_decision, not just the protection matrix?",
        raised_by=run.id,
        probe={"seed": 7},
    )

    # Rerun under the probe, and again — one surviving run is not corroboration.
    for seed in (7, 11):
        rerun_metrics = metrics_from_result(
            run_unified_simulation(SimConfig(steps=40, enable_zones=False, seed=seed))
        )
        _, rerun_evaluation = inquiry.run_and_evaluate(
            v2.id, rerun_metrics, config={"steps": 40, "enable_zones": False}, seed=seed
        )
        assert rerun_evaluation.verdict is Verdict.SUPPORTED

    # The unknown stays open — the reruns confirmed the revision, not the mechanism.
    assert unknown.status is UnknownStatus.OPEN

    # The ledger survives the session.
    reloaded = Inquiry.load(inquiry.save(tmp_path / "inquiry.json"))
    assert reloaded.summary()["falsifications"] == 1
    assert reloaded.claims[claim.id].status is ClaimStatus.SUPERSEDED
    assert [u.question for u in reloaded.open_unknowns()] == [unknown.question]
