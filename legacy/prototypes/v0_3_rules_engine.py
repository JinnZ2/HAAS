# ARCHIVED — HAAS-Q legacy artifact. Not imported, not executed, not maintained.
# Kept verbatim so the original claim can be diffed against what replaced it.
# Precedence carries: this text is the first statement of the ideas below.
# Corrections belong in the superseding module, plus a row in legacy/README.md.
#
# Source:       Framework.md lines 1036-1046 — "4. Minimal Real-Time Rules Engine"
# Origin:       c5ba2bf  Create Framework.md
# Superseded:   896a12b  Extract Framework.md into a complete Python package
# Replaced by:  src/haas/control.py (check_alerts)
# Status:       SUPERSEDED — refined, not falsified. Pseudocode; names never bound.
#
# ----- verbatim excerpt begins -----

if risk > 0.7:
    alert("CRITICAL")

if confidence < 0.5:
    alert("LOW CONFIDENCE")

if override_count > threshold:
    alert("HUMAN-AI MISMATCH")

if drift_index > limit:
    trigger_recalibration()
