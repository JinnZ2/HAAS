import json
import time

from haas.telemetry import SovereignBlackBox, TelemetryFrame, create_telemetry_frame


def test_telemetry_frame_creation():
    f = TelemetryFrame(
        timestamp=1.0, ai_confidence=0.9, detected_objects=2,
        velocity=1.5, proximity_min=1.0, override_active=False,
        institutional_friction_score=3.0,
    )
    assert f.ai_confidence == 0.9


def test_create_telemetry_frame_auto_timestamp():
    before = time.time()
    f = create_telemetry_frame(0.8, 1, 1.0, 2.0)
    after = time.time()
    assert before <= f.timestamp <= after


def test_black_box_writes_to_file(tmp_path):
    log_file = tmp_path / "test_log.json"
    bb = SovereignBlackBox(log_file=log_file)

    frame = TelemetryFrame(
        timestamp=1.0, ai_confidence=0.5, detected_objects=1,
        velocity=1.0, proximity_min=2.0, override_active=False,
        institutional_friction_score=1.0,
    )
    bb.record_frame(frame)

    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["ai_confidence"] == 0.5


def test_black_box_dissonance_detection(tmp_path):
    log_file = tmp_path / "test_log.json"
    bb = SovereignBlackBox(log_file=log_file)

    # High confidence + dangerously close = dissonance
    frame = TelemetryFrame(
        timestamp=1.0, ai_confidence=0.98, detected_objects=1,
        velocity=1.5, proximity_min=0.3, override_active=False,
        institutional_friction_score=8.0,
    )
    reason = bb.record_frame(frame)
    assert reason == "Model/Reality Dissonance Detected"
    assert len(bb.critical_events) == 1


def test_black_box_no_dissonance(tmp_path):
    log_file = tmp_path / "test_log.json"
    bb = SovereignBlackBox(log_file=log_file)

    frame = TelemetryFrame(
        timestamp=1.0, ai_confidence=0.5, detected_objects=1,
        velocity=0.5, proximity_min=3.0, override_active=False,
        institutional_friction_score=1.0,
    )
    reason = bb.record_frame(frame)
    assert reason is None
    assert len(bb.critical_events) == 0
