# ARCHIVED — HAAS-Q legacy artifact. Not imported, not executed, not maintained.
# Kept verbatim so the original claim can be diffed against what replaced it.
# Precedence carries: this text is the first statement of the ideas below.
# Corrections belong in the superseding module, plus a row in legacy/README.md.
#
# Source:       Framework.md lines 1222-1243 — "1. The Handshake Protocol: 'FELTSensor' Integration"
# Origin:       c5ba2bf  Create Framework.md
# Superseded:   896a12b  Extract Framework.md into a complete Python package
# Replaced by:  src/haas/handshake.py
# Status:       SUPERSEDED — refined, not falsified. apply_institutional_throttle never defined.
#
# ----- verbatim excerpt begins -----

def check_handshake_requirement(ai_confidence, felt_level, friction_score):
    """
    Triggers a Micro-Clarification if the 'Information Flow' is messy.
    'felt_level' is the operator's sensory input (0-1).
    """
    
    # Logic: If the human feels 'Anxious' (high prediction error) 
    # OR the AI is guessing, stop and clarify.
    
    if felt_level < 0.4 or ai_confidence < 0.8:
        trigger_micro_clarification_prompt()
        return "WAITING_FOR_HANDSHAKE"
    
    if friction_score > 7:
        # Management isn't fixing things; slow down to stay safe.
        apply_institutional_throttle(0.5)
        return "THROTTLED_BY_FRICTION"

    return "PROCEED"

def trigger_micro_clarification_prompt():
    print("HANDSHAKE REQUIRED: Operator, confirm path is clear of 'Entropy Events'.")
