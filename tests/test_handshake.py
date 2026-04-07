from haas.handshake import (
    check_handshake_requirement,
    trigger_micro_clarification_prompt,
)


def test_handshake_low_felt_level():
    result = check_handshake_requirement(ai_confidence=0.9, felt_level=0.2, friction_score=1.0)
    assert result == "WAITING_FOR_HANDSHAKE"


def test_handshake_low_ai_confidence():
    result = check_handshake_requirement(ai_confidence=0.5, felt_level=0.9, friction_score=1.0)
    assert result == "WAITING_FOR_HANDSHAKE"


def test_handshake_high_friction():
    result = check_handshake_requirement(ai_confidence=0.9, felt_level=0.9, friction_score=8.0)
    assert result == "THROTTLED_BY_FRICTION"


def test_handshake_proceed():
    result = check_handshake_requirement(ai_confidence=0.9, felt_level=0.9, friction_score=3.0)
    assert result == "PROCEED"


def test_micro_clarification_prompt():
    msg = trigger_micro_clarification_prompt()
    assert "HANDSHAKE REQUIRED" in msg
