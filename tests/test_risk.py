import numpy as np

from haas.entities import Human, Machine
from haas.risk import compute_confidence, compute_risk


def test_risk_bounded():
    h = Human("H1", np.array([0.0, 0.0]), np.array([1.0, 0.0]))
    m = Machine("F1", np.array([0.0, 0.0]), np.array([-1.0, 0.0]), max_speed=2.0)
    risk = compute_risk(h, m)
    assert 0.0 <= risk <= 1.0


def test_risk_zero_distance_clamped():
    h = Human("H1", np.array([0.0, 0.0]), np.array([0.0, 0.0]))
    m = Machine("F1", np.array([0.0, 0.0]), np.array([0.0, 0.0]), max_speed=1.0)
    risk = compute_risk(h, m)
    assert risk == 0.0  # zero velocity / 0.001 distance = 0


def test_risk_high_when_close_and_fast():
    h = Human("H1", np.array([0.0, 0.0]), np.array([0.0, 0.0]))
    m = Machine("F1", np.array([0.1, 0.0]), np.array([-2.0, 0.0]), max_speed=3.0)
    risk = compute_risk(h, m)
    assert risk > 0.5


def test_risk_low_when_far():
    h = Human("H1", np.array([0.0, 0.0]), np.array([0.0, 0.0]))
    m = Machine("F1", np.array([100.0, 0.0]), np.array([-0.1, 0.0]), max_speed=1.0)
    risk = compute_risk(h, m)
    assert risk < 0.1


def test_compute_confidence_normal():
    assert compute_confidence(0.9, 0.0) == 0.9


def test_compute_confidence_degraded():
    assert compute_confidence(0.9, 0.5) == 0.4


def test_compute_confidence_clamped():
    assert compute_confidence(0.3, 0.5) == 0.0
