import json

from haas.audit import (
    Audit,
    Maturity,
    PairScore,
    ThreatAssessment,
    blank_questionnaire,
    create_audit,
    create_audit_from_responses,
    overall_rating,
)
from haas.protections import THREAT_REGISTRY, Entity


# ---- ThreatAssessment ----

def test_assessment_defaults():
    a = ThreatAssessment(threat_id="X")
    assert a.score == 0
    assert a.max_score == 9
    assert a.pct == 0.0


def test_assessment_perfect():
    a = ThreatAssessment(
        "X", Maturity.VERIFIED, Maturity.VERIFIED, Maturity.VERIFIED
    )
    assert a.score == 9
    assert a.pct == 100.0


def test_assessment_partial():
    a = ThreatAssessment(
        "X", Maturity.IMPLEMENTED, Maturity.PARTIAL, Maturity.NONE
    )
    assert a.score == 3  # 2 + 1 + 0


# ---- Create audit ----

def test_create_audit_has_all_threats():
    audit = create_audit()
    for t in THREAT_REGISTRY:
        assert t.id in audit.assessments


def test_create_audit_starts_blank():
    audit = create_audit()
    achieved, maximum, pct = audit.overall_score()
    assert achieved == 0
    assert pct == 0.0


def test_set_assessment():
    audit = create_audit()
    audit.set("H_AI_1", control=3, signal=2, enforcement=1, notes="Test")
    a = audit.get("H_AI_1")
    assert a.control_exists == Maturity.VERIFIED
    assert a.signal_monitored == Maturity.IMPLEMENTED
    assert a.enforcement_proof == Maturity.PARTIAL
    assert a.notes == "Test"


def test_set_unknown_threat_raises():
    audit = create_audit()
    try:
        audit.set("FAKE_ID", control=1)
        assert False, "Should have raised KeyError"
    except KeyError:
        pass


# ---- Scoring ----

def test_pair_scores_cover_all_pairs():
    audit = create_audit()
    ps = audit.pair_scores()
    pairs = {(p.target, p.source) for p in ps}
    entities = list(Entity)
    for t in entities:
        for s in entities:
            if t != s:
                assert (t, s) in pairs


def test_entity_scores():
    audit = create_audit()
    es = audit.entity_scores()
    entities_covered = {e.entity for e in es}
    assert entities_covered == set(Entity)


def test_entity_weakest_pair():
    audit = create_audit()
    # Score one pair highly
    audit.set("H_AI_1", control=3, signal=3, enforcement=3)
    es = audit.entity_scores()
    human_score = next(e for e in es if e.entity == Entity.HUMAN)
    weakest = human_score.weakest_pair
    assert weakest is not None
    # H_AI should NOT be the weakest since we scored it
    # (unless all others are equally zero, in which case any could be)


def test_overall_score_with_responses():
    audit = create_audit()
    audit.set("H_AI_1", control=3, signal=3, enforcement=3)
    achieved, maximum, pct = audit.overall_score()
    assert achieved == 9
    assert maximum == len(THREAT_REGISTRY) * 9
    assert pct > 0


# ---- Gaps and strengths ----

def test_gaps_all_blank():
    audit = create_audit()
    gaps = audit.gaps()
    assert len(gaps) == len(THREAT_REGISTRY)


def test_gaps_after_filling():
    audit = create_audit()
    # Fill all dimensions for one threat
    audit.set("H_AI_1", control=2, signal=2, enforcement=2)
    gaps = audit.gaps()
    gap_ids = [t.id for t, a in gaps]
    assert "H_AI_1" not in gap_ids


def test_strengths_none_by_default():
    audit = create_audit()
    assert audit.strengths() == []


def test_strengths_when_verified():
    audit = create_audit()
    audit.set("H_AI_1", control=3, signal=3, enforcement=3)
    strengths = audit.strengths()
    assert len(strengths) == 1
    assert strengths[0][0].id == "H_AI_1"


# ---- Overall rating ----

def test_overall_rating_levels():
    assert overall_rating(95) == "Exemplary"
    assert overall_rating(80) == "Strong"
    assert overall_rating(65) == "Developing"
    assert overall_rating(45) == "Weak"
    assert overall_rating(25) == "Critical"
    assert overall_rating(10) == "Non-existent"


# ---- Report ----

def test_report_contains_key_sections():
    audit = create_audit()
    audit.set("H_AI_1", control=3, signal=2, enforcement=1)
    audit.set("AUT_INS_1", control=0, signal=0, enforcement=0, notes="No maintenance program")
    report = audit.report()
    assert "HAAS-Q PROTECTION MATRIX AUDIT REPORT" in report
    assert "Overall Score" in report
    assert "ENTITY PROTECTION SCORES" in report
    assert "PROTECTION MATRIX" in report
    assert "GAPS" in report
    assert "STRENGTHS" in report
    assert "PRIORITY RECOMMENDATIONS" in report
    assert "No maintenance program" in report


def test_report_shows_matrix():
    audit = create_audit()
    report = audit.report()
    assert "human" in report
    assert "ai" in report
    assert "automation" in report
    assert "institution" in report
    assert "company" in report


# ---- From responses ----

def test_create_from_responses():
    responses = {
        "H_AI_1": {"control": 3, "signal": 2, "enforcement": 1, "notes": "Good"},
        "H_AUT_1": {"control": 2, "signal": 2, "enforcement": 2},
    }
    audit = create_audit_from_responses(responses)
    assert audit.get("H_AI_1").score == 6
    assert audit.get("H_AUT_1").score == 6
    # Unfilled threats remain at zero
    assert audit.get("H_AI_2").score == 0


# ---- Questionnaire ----

def test_blank_questionnaire():
    q = blank_questionnaire()
    assert len(q) == len(THREAT_REGISTRY)
    first = q[0]
    assert "threat_id" in first
    assert "target" in first
    assert "source" in first
    assert "q1_control_exists" in first
    assert "q2_signal_monitored" in first
    assert "q3_enforcement_proof" in first


def test_questionnaire_is_json_serializable():
    q = blank_questionnaire()
    # Should not raise
    json.dumps(q)


# ---- PairScore ----

def test_pair_score_gap_count():
    assessments = [
        ThreatAssessment("A", Maturity.VERIFIED, Maturity.VERIFIED, Maturity.VERIFIED),
        ThreatAssessment("B", Maturity.NONE, Maturity.IMPLEMENTED, Maturity.IMPLEMENTED),
        ThreatAssessment("C", Maturity.IMPLEMENTED, Maturity.IMPLEMENTED, Maturity.NONE),
    ]
    ps = PairScore(Entity.HUMAN, Entity.AI, assessments)
    assert ps.gap_count == 2  # B and C each have at least one NONE


# ---- Realistic scenario ----

def test_realistic_partial_audit():
    """Simulate a company that has strong physical safety but weak institutional controls."""
    audit = create_audit()

    # Strong: Human <- Automation (physical safety)
    for tid in ["H_AUT_1", "H_AUT_2"]:
        audit.set(tid, control=3, signal=3, enforcement=3)

    # Moderate: AI protections
    for tid in ["AI_AUT_1", "AI_AUT_2"]:
        audit.set(tid, control=2, signal=2, enforcement=1)

    # Weak: Institution protections (the "safety theater" pattern)
    for tid in ["H_INS_1", "H_INS_2", "H_INS_3"]:
        audit.set(tid, control=0, signal=0, enforcement=0)

    report = audit.report()
    assert "Weakest entity" in report

    es = audit.entity_scores()
    human_es = next(e for e in es if e.entity == Entity.HUMAN)
    # Human protection score should reflect the mix of strong + weak
    assert human_es.pct > 0
    assert human_es.pct < 100
