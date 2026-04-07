import random

from haas.failures import (
    FMEA_TABLE,
    FMEAEntry,
    SystemState,
    detect_failures,
    inject_failures,
    rpn_severity,
)


def test_system_state_defaults():
    s = SystemState()
    assert s.confidence == 0.9
    assert s.sensor_noise == 0.0
    assert s.brake_efficiency == 1.0
    assert s.override_count == 0
    assert s.logs == []


def test_inject_failures_degrades():
    random.seed(42)
    s = SystemState()
    original_noise = s.sensor_noise
    original_brake = s.brake_efficiency
    # Run many times to ensure at least one degradation happens
    for _ in range(100):
        inject_failures(s)
    assert s.sensor_noise > original_noise or s.brake_efficiency < original_brake


def test_detect_failures_low_confidence():
    s = SystemState(sensor_noise=0.0, brake_efficiency=1.0)
    signals = detect_failures(s, confidence=0.3, risk=0.5)
    assert signals["low_confidence"] is True


def test_detect_failures_compound():
    s = SystemState(sensor_noise=0.0, brake_efficiency=0.5)
    signals = detect_failures(s, confidence=0.3, risk=0.5)
    assert signals["compound_risk"] is True


def test_detect_failures_nominal():
    s = SystemState()
    signals = detect_failures(s, confidence=0.9, risk=0.2)
    assert signals["low_confidence"] is False
    assert signals["compound_risk"] is False


def test_fmea_table_count():
    assert len(FMEA_TABLE) == 8


def test_fmea_entry_fields():
    entry = FMEA_TABLE[0]
    assert isinstance(entry, FMEAEntry)
    assert entry.id == "F1"
    assert entry.rpn == entry.severity * entry.occurrence * entry.detectability


def test_rpn_severity_levels():
    assert rpn_severity(100) == "monitor"
    assert rpn_severity(200) == "active_control"
    assert rpn_severity(350) == "immediate_redesign"
