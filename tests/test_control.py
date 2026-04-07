import numpy as np

from haas.control import apply_control, check_alerts, control_decision
from haas.entities import Machine


def test_apply_control_stop():
    m = Machine("F1", np.array([0.0, 0.0]), np.array([1.0, 1.0]), max_speed=2.0)
    apply_control(m, "stop")
    assert np.allclose(m.velocity, [0.0, 0.0])
    assert m.state == "stopped"


def test_apply_control_slow():
    m = Machine("F1", np.array([0.0, 0.0]), np.array([2.0, 2.0]), max_speed=3.0)
    apply_control(m, "slow")
    assert np.allclose(m.velocity, [1.0, 1.0])
    assert m.state == "slowed"


def test_apply_control_move():
    m = Machine("F1", np.array([0.0, 0.0]), np.array([1.0, 0.0]), max_speed=2.0)
    apply_control(m, "move")
    assert m.state == "normal"


def test_control_decision_compound_risk():
    signals = {"compound_risk": True}
    assert control_decision(0.9, 0.1, signals) == "STOP"


def test_control_decision_high_risk():
    assert control_decision(0.9, 0.8, {}) == "STOP"


def test_control_decision_low_confidence():
    assert control_decision(0.3, 0.1, {}) == "STOP"


def test_control_decision_medium_risk():
    assert control_decision(0.9, 0.5, {}) == "SLOW"


def test_control_decision_safe():
    assert control_decision(0.9, 0.2, {}) == "MOVE"


def test_check_alerts_critical():
    alerts = check_alerts(risk=0.8, confidence=0.9, override_count=0, drift_index=0.0)
    assert "CRITICAL" in alerts


def test_check_alerts_multiple():
    alerts = check_alerts(risk=0.8, confidence=0.3, override_count=5, drift_index=0.8)
    assert set(alerts) == {"CRITICAL", "LOW_CONFIDENCE", "HUMAN_AI_MISMATCH", "DRIFT_RECALIBRATION"}


def test_check_alerts_none():
    alerts = check_alerts(risk=0.1, confidence=0.9, override_count=0, drift_index=0.0)
    assert alerts == []
