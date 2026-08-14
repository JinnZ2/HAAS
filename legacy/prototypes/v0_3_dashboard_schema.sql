-- ARCHIVED — HAAS-Q legacy artifact. Not imported, not executed, not maintained.
-- Kept verbatim so the original claim can be diffed against what replaced it.
-- Precedence carries: this text is the first statement of the ideas below.
-- Corrections belong in the superseding module, plus a row in legacy/README.md.
--
-- Source:       Framework.md lines 993-1015 — "Database Schema (Simple Version)"
-- Origin:       c5ba2bf  Create Framework.md
-- Superseded:   93eb5c9  Add zones, SQLite persistence, unified simulation, and terminal dashboard
-- Replaced by:  src/haas/store.py (_SCHEMA)
-- Status:       SUPERSEDED — extended. Not valid SQL as written (no CREATE TABLE).
--
-- ----- verbatim excerpt begins -----

TABLE events (
    id INT,
    timestamp FLOAT,
    risk FLOAT,
    confidence FLOAT,
    decision TEXT,
    override_flag BOOLEAN
);

TABLE signals (
    timestamp FLOAT,
    low_confidence BOOLEAN,
    sensor_variance BOOLEAN,
    drift_flag BOOLEAN,
    conflict_flag BOOLEAN
);

TABLE system_state (
    timestamp FLOAT,
    mode TEXT,
    active_controller TEXT
);

