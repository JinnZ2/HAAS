import time

from haas.store import EventStore


def test_record_and_retrieve_event(tmp_path):
    db = tmp_path / "test.db"
    with EventStore(db) as store:
        rid = store.record_event(
            risk=0.6, confidence=0.8, decision="SLOW",
            zone="YELLOW", human_pos=[1.0, 2.0], machine_pos=[3.0, 4.0],
        )
        assert rid == 1
        events = store.get_events()
        assert len(events) == 1
        assert events[0]["decision"] == "SLOW"
        assert events[0]["zone"] == "YELLOW"


def test_count_events(tmp_path):
    db = tmp_path / "test.db"
    with EventStore(db) as store:
        for i in range(5):
            store.record_event(risk=0.1 * i, confidence=0.9, decision="MOVE")
        assert store.count_events() == 5


def test_record_signals(tmp_path):
    db = tmp_path / "test.db"
    with EventStore(db) as store:
        signals = {
            "low_confidence": True,
            "confidence_variance": False,
            "override_spike": False,
            "brake_degradation": True,
            "compound_risk": True,
        }
        sid = store.record_signals(signals)
        assert sid == 1
        rows = store.get_signals()
        assert len(rows) == 1
        assert rows[0]["low_confidence"] == 1
        assert rows[0]["compound_risk"] == 1


def test_record_and_get_state(tmp_path):
    db = tmp_path / "test.db"
    with EventStore(db) as store:
        store.record_state(mode="STOP", sensor_noise=0.3, brake_efficiency=0.7)
        latest = store.get_latest_state()
        assert latest is not None
        assert latest["mode"] == "STOP"
        assert latest["sensor_noise"] == 0.3


def test_near_miss_count(tmp_path):
    db = tmp_path / "test.db"
    with EventStore(db) as store:
        store.record_event(risk=0.8, confidence=0.9, decision="SLOW")  # near miss
        store.record_event(risk=0.8, confidence=0.9, decision="STOP")  # not a near miss
        store.record_event(risk=0.3, confidence=0.9, decision="MOVE")  # low risk
        assert store.near_miss_count() == 1


def test_override_count(tmp_path):
    db = tmp_path / "test.db"
    with EventStore(db) as store:
        store.record_event(risk=0.5, confidence=0.8, decision="STOP", override_flag=True)
        store.record_event(risk=0.5, confidence=0.8, decision="MOVE", override_flag=False)
        assert store.override_count() == 1


def test_average_risk(tmp_path):
    db = tmp_path / "test.db"
    with EventStore(db) as store:
        store.record_event(risk=0.2, confidence=0.9, decision="MOVE")
        store.record_event(risk=0.8, confidence=0.9, decision="STOP")
        avg = store.average_risk(last_n=10)
        assert avg is not None
        assert abs(avg - 0.5) < 0.01


def test_context_manager(tmp_path):
    db = tmp_path / "test.db"
    with EventStore(db) as store:
        store.record_event(risk=0.1, confidence=0.9, decision="MOVE")
    # re-open to verify persistence
    with EventStore(db) as store:
        assert store.count_events() == 1
