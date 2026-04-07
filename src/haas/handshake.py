"""Handshake Protocol — FELTSensor integration and micro-clarification."""

import logging

logger = logging.getLogger(__name__)

# Thresholds from the framework specification
FELT_LEVEL_THRESHOLD = 0.4
AI_CONFIDENCE_THRESHOLD = 0.8
FRICTION_SCORE_LIMIT = 7.0
DEFAULT_THROTTLE_FACTOR = 0.5


def check_handshake_requirement(
    ai_confidence: float,
    felt_level: float,
    friction_score: float,
) -> str:
    """Evaluate whether a micro-clarification handshake is needed.

    Returns one of:
      - "WAITING_FOR_HANDSHAKE" — operator must confirm before proceeding
      - "THROTTLED_BY_FRICTION" — institutional neglect triggers speed cap
      - "PROCEED" — nominal conditions
    """
    if felt_level < FELT_LEVEL_THRESHOLD or ai_confidence < AI_CONFIDENCE_THRESHOLD:
        trigger_micro_clarification_prompt()
        return "WAITING_FOR_HANDSHAKE"

    if friction_score > FRICTION_SCORE_LIMIT:
        apply_institutional_throttle(DEFAULT_THROTTLE_FACTOR)
        return "THROTTLED_BY_FRICTION"

    return "PROCEED"


def trigger_micro_clarification_prompt() -> str:
    """Issue a micro-clarification prompt to the operator."""
    msg = (
        "HANDSHAKE REQUIRED: Model/Reality Dissonance detected. "
        "Operator, confirm path is clear before proceeding."
    )
    logger.warning(msg)
    return msg


def apply_institutional_throttle(factor: float) -> None:
    """Reduce operational velocity due to institutional friction.

    In a real deployment this would interface with the machine control bus.
    """
    logger.warning("Institutional throttle applied: velocity capped to %.0f%%", factor * 100)
