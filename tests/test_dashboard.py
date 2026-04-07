from haas.dashboard import DashboardSnapshot, format_dashboard, show_summary
from haas.store import EventStore


def _make_snap(**overrides) -> DashboardSnapshot:
    defaults = dict(
        step=0, risk=0.3, confidence=0.8, decision="MOVE", zone="GREEN",
        signals={"low_confidence": False, "compound_risk": False},
        sensor_noise=0.0, brake_efficiency=1.0,
        human_pos=[0.0, 0.0], machine_pos=[5.0, 0.0], alerts=[],
    )
    defaults.update(overrides)
    return DashboardSnapshot(**defaults)


def test_format_dashboard_renders():
    snap = _make_snap()
    output = format_dashboard(snap)
    assert "HAAS-Q" in output
    assert "MOVE" in output
    assert "GREEN" in output


def test_format_dashboard_critical():
    snap = _make_snap(risk=0.9, decision="STOP", alerts=["CRITICAL"])
    output = format_dashboard(snap)
    assert "STOP" in output
    assert "CRITICAL" in output


def test_risk_bar_length():
    snap = _make_snap(risk=0.5)
    bar = snap.risk_bar
    # bar contains 20 total block characters (filled + empty)
    blocks = bar.replace("\033[93m", "").replace("\033[91m", "").replace("\033[92m", "").replace("\033[0m", "")
    assert len(blocks) == 20


def test_confidence_bar_low():
    snap = _make_snap(confidence=0.3)
    bar = snap.confidence_bar
    assert "\033[91m" in bar  # red color for low confidence


def test_show_summary(tmp_path):
    db = tmp_path / "test.db"
    with EventStore(db) as store:
        store.record_event(risk=0.5, confidence=0.8, decision="SLOW")
        store.record_event(risk=0.8, confidence=0.3, decision="STOP")
        store.record_state(mode="STOP", sensor_noise=0.2, brake_efficiency=0.9)
        output = show_summary(store)
    assert "Total events" in output
    assert "Near-misses" in output
    assert "STOP" in output
