import numpy as np

from haas.failures import SystemState
from haas.simulation import (
    SimConfig,
    run_basic_simulation,
    run_failure_simulation,
    run_unified_simulation,
    simulate_failure_step,
)
from haas.store import EventStore
from haas.zones import Zone, ZoneLevel, ZoneMap


def test_run_basic_simulation():
    log = run_basic_simulation(steps=10)
    assert len(log.events) == 10
    entry = log.events[0]["event"]
    assert "risk" in entry
    assert "decision" in entry


def test_run_basic_simulation_default_steps():
    log = run_basic_simulation()
    assert len(log.events) == 20


def test_simulate_failure_step():
    state = SystemState()
    entry = simulate_failure_step(state)
    assert "risk" in entry
    assert "confidence" in entry
    assert "signals" in entry
    assert "decision" in entry
    assert len(state.logs) == 1


def test_run_failure_simulation():
    state = run_failure_simulation(steps=30)
    assert len(state.logs) == 30
    for entry in state.logs:
        assert entry["decision"] in ("STOP", "SLOW", "MOVE")


# ------------------------------------
# Unified simulation tests
# ------------------------------------

def test_unified_simulation_basic():
    config = SimConfig(steps=10, enable_failures=True, enable_zones=False)
    result = run_unified_simulation(config=config)
    assert len(result.log.events) == 10
    assert len(result.snapshots) == 10
    for snap in result.snapshots:
        assert snap.decision in ("STOP", "SLOW", "MOVE")


def test_unified_simulation_with_zones():
    zone_map = ZoneMap([
        Zone("floor", ZoneLevel.GREEN, np.array([-10.0, -10.0]), np.array([20.0, 20.0])),
        Zone("aisle", ZoneLevel.YELLOW, np.array([2.0, -1.0]), np.array([2.0, 2.0])),
    ])
    config = SimConfig(steps=20, enable_zones=True)
    result = run_unified_simulation(config=config, zone_map=zone_map)
    assert len(result.snapshots) == 20
    zones_seen = {s.zone for s in result.snapshots}
    # Machine starts at (5,0) moving left — should pass through yellow zone
    assert len(zones_seen) >= 1


def test_unified_simulation_red_zone_forces_stop():
    # Put a red zone right where the machine is
    zone_map = ZoneMap([
        Zone("danger", ZoneLevel.RED, np.array([4.0, -1.0]), np.array([3.0, 2.0])),
    ])
    config = SimConfig(steps=5, enable_zones=True)
    result = run_unified_simulation(config=config, zone_map=zone_map)
    # Machine starts at (5, 0), inside the red zone
    assert result.snapshots[0].decision == "STOP"


def test_unified_simulation_with_store(tmp_path):
    db = tmp_path / "test.db"
    with EventStore(db) as store:
        config = SimConfig(steps=10, store=store)
        result = run_unified_simulation(config=config)
        assert store.count_events() == 10
        state = store.get_latest_state()
        assert state is not None


def test_unified_simulation_snapshots_have_fields():
    config = SimConfig(steps=3)
    result = run_unified_simulation(config=config)
    snap = result.snapshots[0]
    assert hasattr(snap, "risk")
    assert hasattr(snap, "confidence")
    assert hasattr(snap, "zone")
    assert hasattr(snap, "signals")
    assert hasattr(snap, "alerts")
    assert hasattr(snap, "sensor_noise")
    assert hasattr(snap, "brake_efficiency")


def test_unified_simulation_state_degrades():
    config = SimConfig(steps=200, enable_failures=True)
    result = run_unified_simulation(config=config)
    # Over 200 steps with 10% chance of sensor noise injection per step,
    # sensor_noise should have increased
    assert result.state.sensor_noise > 0.0 or result.state.brake_efficiency < 1.0
