"""Persistent SQLite storage — events, signals, and system state."""

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


_SCHEMA = """\
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    risk REAL,
    confidence REAL,
    decision TEXT,
    override_flag INTEGER DEFAULT 0,
    zone TEXT,
    human_pos TEXT,
    machine_pos TEXT,
    extra TEXT
);

CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    low_confidence INTEGER,
    confidence_variance INTEGER,
    override_spike INTEGER,
    brake_degradation INTEGER,
    compound_risk INTEGER,
    drift_flag INTEGER DEFAULT 0,
    conflict_flag INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS system_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    mode TEXT NOT NULL,
    active_controller TEXT,
    sensor_noise REAL,
    brake_efficiency REAL
);

CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    threat_id TEXT NOT NULL,
    target TEXT NOT NULL,
    source TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT,
    values_json TEXT
);
"""


class EventStore:
    """SQLite-backed persistent event store.

    Implements the three-table schema from the framework specification:
    events, signals, system_state.
    """

    def __init__(self, db_path: str | Path = "haas_events.db") -> None:
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "EventStore":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ---- Events ----

    def record_event(
        self,
        risk: float,
        confidence: float,
        decision: str,
        override_flag: bool = False,
        zone: str | None = None,
        human_pos: list[float] | None = None,
        machine_pos: list[float] | None = None,
        extra: dict | None = None,
        timestamp: float | None = None,
    ) -> int:
        ts = timestamp or time.time()
        cur = self._conn.execute(
            "INSERT INTO events (timestamp, risk, confidence, decision, "
            "override_flag, zone, human_pos, machine_pos, extra) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ts,
                risk,
                confidence,
                decision,
                int(override_flag),
                zone,
                json.dumps(human_pos) if human_pos else None,
                json.dumps(machine_pos) if machine_pos else None,
                json.dumps(extra) if extra else None,
            ),
        )
        self._conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_events(self, limit: int = 100, offset: int = 0) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM events ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    def count_events(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM events").fetchone()
        return row[0]

    # ---- Signals ----

    def record_signals(
        self,
        signals: dict[str, bool],
        timestamp: float | None = None,
    ) -> int:
        ts = timestamp or time.time()
        cur = self._conn.execute(
            "INSERT INTO signals (timestamp, low_confidence, confidence_variance, "
            "override_spike, brake_degradation, compound_risk, drift_flag, conflict_flag) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ts,
                int(signals.get("low_confidence", False)),
                int(signals.get("confidence_variance", False)),
                int(signals.get("override_spike", False)),
                int(signals.get("brake_degradation", False)),
                int(signals.get("compound_risk", False)),
                int(signals.get("drift_flag", False)),
                int(signals.get("conflict_flag", False)),
            ),
        )
        self._conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_signals(self, limit: int = 100) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM signals ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ---- System State ----

    def record_state(
        self,
        mode: str,
        active_controller: str = "ai",
        sensor_noise: float = 0.0,
        brake_efficiency: float = 1.0,
        timestamp: float | None = None,
    ) -> int:
        ts = timestamp or time.time()
        cur = self._conn.execute(
            "INSERT INTO system_state (timestamp, mode, active_controller, "
            "sensor_noise, brake_efficiency) VALUES (?, ?, ?, ?, ?)",
            (ts, mode, active_controller, sensor_noise, brake_efficiency),
        )
        self._conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_latest_state(self) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM system_state ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

    # ---- Queries ----

    def near_miss_count(self, risk_threshold: float = 0.7) -> int:
        """Count events where risk exceeded threshold but decision was not STOP."""
        row = self._conn.execute(
            "SELECT COUNT(*) FROM events WHERE risk > ? AND decision != 'STOP'",
            (risk_threshold,),
        ).fetchone()
        return row[0]

    def override_count(self, since: float | None = None) -> int:
        """Count override events, optionally since a timestamp."""
        if since is not None:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM events WHERE override_flag = 1 AND timestamp > ?",
                (since,),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM events WHERE override_flag = 1"
            ).fetchone()
        return row[0]

    def average_risk(self, last_n: int = 50) -> float | None:
        """Average risk over the last N events."""
        row = self._conn.execute(
            "SELECT AVG(risk) FROM (SELECT risk FROM events ORDER BY timestamp DESC LIMIT ?)",
            (last_n,),
        ).fetchone()
        return row[0]

    # ---- Violations ----

    def record_violation(
        self,
        threat_id: str,
        target: str,
        source: str,
        severity: str,
        description: str,
        values: dict | None = None,
        timestamp: float | None = None,
    ) -> int:
        ts = timestamp or time.time()
        cur = self._conn.execute(
            "INSERT INTO violations (timestamp, threat_id, target, source, "
            "severity, description, values_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ts, threat_id, target, source, severity, description,
             json.dumps(values) if values else None),
        )
        self._conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_violations(self, limit: int = 100) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM violations ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def violation_count(self, severity: str | None = None) -> int:
        if severity:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM violations WHERE severity = ?", (severity,)
            ).fetchone()
        else:
            row = self._conn.execute("SELECT COUNT(*) FROM violations").fetchone()
        return row[0]

    def violations_by_target(self) -> dict[str, int]:
        """Count violations grouped by target entity."""
        rows = self._conn.execute(
            "SELECT target, COUNT(*) as cnt FROM violations GROUP BY target"
        ).fetchall()
        return {row["target"]: row["cnt"] for row in rows}

    def violations_by_pair(self) -> dict[str, int]:
        """Count violations grouped by target <- source pair."""
        rows = self._conn.execute(
            "SELECT target || ' <- ' || source as pair, COUNT(*) as cnt "
            "FROM violations GROUP BY pair"
        ).fetchall()
        return {row["pair"]: row["cnt"] for row in rows}
