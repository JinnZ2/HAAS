from haas.protections import (
    THREAT_REGISTRY,
    Entity,
    ProtectionState,
    Severity,
    Violation,
    evaluate_protections,
    format_violation,
    get_threat,
    get_threats_for,
    get_threats_from,
    get_threats_targeting,
)


# ---- Threat registry structure ----

def test_all_entity_pairs_covered():
    """Every ordered pair of distinct entities has at least one threat."""
    entities = list(Entity)
    covered = set()
    for t in THREAT_REGISTRY:
        covered.add((t.target, t.source))
    for target in entities:
        for source in entities:
            if target != source:
                assert (target, source) in covered, (
                    f"Missing threat: {target.value} <- {source.value}"
                )


def test_threat_ids_unique():
    ids = [t.id for t in THREAT_REGISTRY]
    assert len(ids) == len(set(ids))


def test_get_threat_by_id():
    t = get_threat("H_AI_1")
    assert t is not None
    assert t.target == Entity.HUMAN
    assert t.source == Entity.AI


def test_get_threat_missing():
    assert get_threat("NONEXISTENT") is None


def test_get_threats_for_pair():
    threats = get_threats_for(Entity.HUMAN, Entity.AI)
    assert len(threats) >= 1
    for t in threats:
        assert t.target == Entity.HUMAN
        assert t.source == Entity.AI


def test_get_threats_targeting():
    threats = get_threats_targeting(Entity.HUMAN)
    assert len(threats) >= 4  # human is protected from all 4 other entities
    targets = {t.target for t in threats}
    assert targets == {Entity.HUMAN}


def test_get_threats_from():
    threats = get_threats_from(Entity.INSTITUTION)
    assert len(threats) >= 3
    sources = {t.source for t in threats}
    assert sources == {Entity.INSTITUTION}


# ---- Violation detection ----

def _default_pstate(**overrides) -> ProtectionState:
    ps = ProtectionState()
    for k, v in overrides.items():
        setattr(ps, k, v)
    return ps


def test_no_violations_nominal():
    ps = _default_pstate()
    violations = evaluate_protections(
        risk=0.2, confidence=0.9, decision="MOVE",
        brake_efficiency=1.0, sensor_noise=0.0,
        proximity=5.0, velocity=0.5,
        institutional_friction=1.0, pstate=ps,
    )
    assert violations == []


def test_violation_h_ai_1_unsafe_motion():
    ps = _default_pstate()
    violations = evaluate_protections(
        risk=0.8, confidence=0.85, decision="MOVE",
        brake_efficiency=1.0, sensor_noise=0.0,
        proximity=0.3, velocity=0.5,
        institutional_friction=0.0, pstate=ps,
    )
    ids = [v.threat_id for v in violations]
    assert "H_AI_1" in ids


def test_violation_h_aut_1_kinetic_harm():
    ps = _default_pstate()
    violations = evaluate_protections(
        risk=0.9, confidence=0.5, decision="STOP",
        brake_efficiency=1.0, sensor_noise=0.0,
        proximity=0.2, velocity=0.5,
        institutional_friction=0.0, pstate=ps,
    )
    ids = [v.threat_id for v in violations]
    assert "H_AUT_1" in ids


def test_violation_h_ins_1_institutional_friction():
    ps = _default_pstate()
    violations = evaluate_protections(
        risk=0.3, confidence=0.8, decision="MOVE",
        brake_efficiency=1.0, sensor_noise=0.0,
        proximity=5.0, velocity=0.3,
        institutional_friction=8.0, pstate=ps,
    )
    ids = [v.threat_id for v in violations]
    assert "H_INS_1" in ids


def test_violation_ai_h_1_override_abuse():
    ps = _default_pstate(override_count_recent=7)
    violations = evaluate_protections(
        risk=0.1, confidence=0.9, decision="MOVE",
        brake_efficiency=1.0, sensor_noise=0.0,
        proximity=5.0, velocity=0.3,
        institutional_friction=0.0, pstate=ps,
    )
    ids = [v.threat_id for v in violations]
    assert "AI_H_1" in ids


def test_violation_ai_aut_1_sensor_noise():
    ps = _default_pstate()
    violations = evaluate_protections(
        risk=0.3, confidence=0.5, decision="SLOW",
        brake_efficiency=1.0, sensor_noise=0.5,
        proximity=3.0, velocity=0.3,
        institutional_friction=0.0, pstate=ps,
    )
    ids = [v.threat_id for v in violations]
    assert "AI_AUT_1" in ids


def test_violation_ai_ins_2_suppressed_stops():
    ps = _default_pstate(stop_count_recent=0, near_miss_count_recent=5)
    violations = evaluate_protections(
        risk=0.3, confidence=0.8, decision="MOVE",
        brake_efficiency=1.0, sensor_noise=0.0,
        proximity=5.0, velocity=0.3,
        institutional_friction=0.0, pstate=ps,
    )
    ids = [v.threat_id for v in violations]
    assert "AI_INS_2" in ids


def test_violation_aut_ai_1_oscillation():
    ps = _default_pstate(command_switches_recent=8)
    violations = evaluate_protections(
        risk=0.3, confidence=0.8, decision="MOVE",
        brake_efficiency=1.0, sensor_noise=0.0,
        proximity=5.0, velocity=0.3,
        institutional_friction=0.0, pstate=ps,
    )
    ids = [v.threat_id for v in violations]
    assert "AUT_AI_1" in ids


def test_violation_aut_ins_1_brake_degradation():
    ps = _default_pstate()
    violations = evaluate_protections(
        risk=0.3, confidence=0.8, decision="SLOW",
        brake_efficiency=0.3, sensor_noise=0.0,
        proximity=3.0, velocity=0.3,
        institutional_friction=0.0, pstate=ps,
    )
    ids = [v.threat_id for v in violations]
    assert "AUT_INS_1" in ids


def test_violation_com_ai_1_autonomous_liability():
    ps = _default_pstate()
    violations = evaluate_protections(
        risk=0.6, confidence=0.3, decision="MOVE",
        brake_efficiency=1.0, sensor_noise=0.0,
        proximity=2.0, velocity=0.5,
        institutional_friction=0.0, pstate=ps,
    )
    ids = [v.threat_id for v in violations]
    assert "COM_AI_1" in ids


def test_violation_com_ins_1_governance_failure():
    ps = _default_pstate(near_miss_count_recent=6)
    violations = evaluate_protections(
        risk=0.3, confidence=0.8, decision="MOVE",
        brake_efficiency=1.0, sensor_noise=0.0,
        proximity=5.0, velocity=0.3,
        institutional_friction=9.0, pstate=ps,
    )
    ids = [v.threat_id for v in violations]
    assert "COM_INS_1" in ids


def test_violation_severity_levels():
    ps = _default_pstate()
    violations = evaluate_protections(
        risk=0.9, confidence=0.85, decision="MOVE",
        brake_efficiency=0.3, sensor_noise=0.0,
        proximity=0.2, velocity=0.5,
        institutional_friction=0.0, pstate=ps,
    )
    severities = {v.severity for v in violations}
    assert Severity.CRITICAL in severities


def test_command_switching_tracked():
    ps = _default_pstate()
    ps.last_decision = "MOVE"
    evaluate_protections(
        risk=0.2, confidence=0.9, decision="STOP",
        brake_efficiency=1.0, sensor_noise=0.0,
        proximity=5.0, velocity=0.0,
        institutional_friction=0.0, pstate=ps,
    )
    assert ps.command_switches_recent == 1
    assert ps.last_decision == "STOP"


def test_format_violation():
    v = Violation(
        "H_AI_1", Entity.HUMAN, Entity.AI, Severity.CRITICAL,
        "Test violation description",
    )
    s = format_violation(v)
    assert "human" in s
    assert "ai" in s
    assert "H_AI_1" in s
    assert "!!!" in s


def test_multiple_violations_simultaneously():
    """A single evaluation can trigger violations across multiple domains."""
    ps = _default_pstate(override_count_recent=7, near_miss_count_recent=6)
    violations = evaluate_protections(
        risk=0.8, confidence=0.85, decision="MOVE",
        brake_efficiency=0.3, sensor_noise=0.5,
        proximity=0.2, velocity=0.5,
        institutional_friction=9.0, pstate=ps,
    )
    targets = {v.target for v in violations}
    # Should have violations targeting multiple different entities
    assert len(targets) >= 3
