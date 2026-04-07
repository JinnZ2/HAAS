from haas.simulation import (
    run_basic_simulation,
    run_failure_simulation,
    simulate_failure_step,
)
from haas.failures import SystemState


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
