import numpy as np

from haas.entities import AIController, Human, Machine


def test_human_creation():
    h = Human("H1", np.array([1.0, 2.0]), np.array([0.1, 0.0]))
    assert h.id == "H1"
    assert h.state == "normal"


def test_machine_creation():
    m = Machine("F1", np.array([0.0, 0.0]), np.array([1.0, 0.0]), max_speed=2.0)
    assert m.id == "F1"
    assert m.max_speed == 2.0
    assert m.state == "normal"


def test_ai_evaluate_stop_high_risk():
    ai = AIController(confidence=0.9, decision="move")
    assert ai.evaluate(0.8) == "stop"


def test_ai_evaluate_stop_low_confidence():
    ai = AIController(confidence=0.3, decision="move")
    assert ai.evaluate(0.1) == "stop"


def test_ai_evaluate_slow():
    ai = AIController(confidence=0.9, decision="move")
    assert ai.evaluate(0.5) == "slow"


def test_ai_evaluate_move():
    ai = AIController(confidence=0.9, decision="move")
    assert ai.evaluate(0.2) == "move"
