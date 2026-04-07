"""Tests for the TAF-integrated energy model."""

from haas.energy import (
    HumanEnergyState,
    automation_load_multiplier,
    collapse_flags,
    compute_fatigue,
    distance_to_collapse,
    environment_multiplier,
    ghost_friction_cost,
    hidden_variable_multiplier,
    long_tail_risk,
    parasitic_energy_debt,
)


# ---- Multipliers ----

def test_hidden_var_multiplier_zero():
    assert hidden_variable_multiplier(0) == 1.0


def test_hidden_var_multiplier_nonlinear():
    m1 = hidden_variable_multiplier(1)
    m5 = hidden_variable_multiplier(5)
    assert m1 > 1.0
    assert m5 > m1
    # Nonlinear: 5x should grow faster than 5 * (m1 - 1)
    assert (m5 - 1) > 5 * (m1 - 1)


def test_automation_multiplier_perfect():
    assert automation_load_multiplier(3, reliability=1.0) == 1.0


def test_automation_multiplier_unreliable():
    m = automation_load_multiplier(3, reliability=0.5)
    assert m > 1.0


def test_environment_normal():
    assert environment_multiplier(20.0, 0.0) == 1.0


def test_environment_cold_windy():
    m = environment_multiplier(-10.0, 15.0)
    assert m > 1.0


# ---- Fatigue ----

def test_fatigue_sustainable():
    result = compute_fatigue(20, 20, energy_input=100)
    assert result["fatigue_score"] == 0.0  # 40 < 100


def test_fatigue_overloaded():
    result = compute_fatigue(60, 60, energy_input=100)
    assert result["fatigue_score"] > 0.0  # 120 > 100


def test_fatigue_clamped_at_10():
    result = compute_fatigue(200, 200, energy_input=100)
    assert result["fatigue_score"] == 10.0


def test_fatigue_multipliers_increase_load():
    base = compute_fatigue(30, 40, energy_input=100)
    with_hidden = compute_fatigue(30, 40, energy_input=100, hidden_count=5)
    assert with_hidden["adjusted_load"] > base["adjusted_load"]


def test_fatigue_full_breakdown():
    result = compute_fatigue(
        30, 40, energy_input=100,
        hidden_count=3, automation_count=2,
        automation_reliability=0.7, temp_celsius=0, wind_mps=10,
    )
    assert "multipliers" in result
    assert result["multipliers"]["combined"] > 1.0


# ---- Collapse ----

def test_distance_to_collapse_sustainable():
    d = distance_to_collapse(50, energy_input=100)
    assert d > 0.5


def test_distance_to_collapse_at_threshold():
    d = distance_to_collapse(160, energy_input=100)
    assert d == 0.0


def test_distance_to_collapse_beyond():
    d = distance_to_collapse(200, energy_input=100)
    assert d == 0.0


def test_collapse_flags_safe():
    assert collapse_flags(90, energy_input=100) == []


def test_collapse_flags_productivity():
    flags = collapse_flags(125, energy_input=100)
    assert "PRODUCTIVITY_DEGRADATION" in flags


def test_collapse_flags_safety():
    flags = collapse_flags(145, energy_input=100)
    assert "SAFETY_BREAKDOWN_LIKELY" in flags


def test_collapse_flags_health():
    flags = collapse_flags(165, energy_input=100)
    assert "HEALTH_COLLAPSE_IMMINENT" in flags


# ---- Long-tail risk ----

def test_long_tail_zero():
    assert long_tail_risk(0) == 0.0


def test_long_tail_nonlinear():
    r1 = long_tail_risk(1)
    r5 = long_tail_risk(5)
    r10 = long_tail_risk(10)
    assert 0 < r1 < r5 < r10 <= 10.0


# ---- Parasitic energy debt ----

def test_parasitic_debt_no_friction():
    debt = parasitic_energy_debt(10, friction_events=0)
    assert debt == 10.0


def test_parasitic_debt_with_friction():
    debt = parasitic_energy_debt(10, friction_events=4)
    assert debt > 10.0  # friction multiplier kicks in


# ---- Ghost-friction ----

def test_ghost_friction_zero_alerts():
    gf = ghost_friction_cost(0)
    assert gf["total_ai_tax"] == 0.0
    assert gf["trust_erosion"] == 0.0


def test_ghost_friction_many_alerts():
    gf = ghost_friction_cost(20)
    assert gf["total_ai_tax"] > 0
    assert gf["metabolic_cost"] > 0
    assert gf["attention_cost"] > 0
    assert gf["trust_erosion"] == 1.0  # capped


# ---- HumanEnergyState ----

def test_energy_state_defaults():
    es = HumanEnergyState()
    assert es.fatigue_score == 0.0
    assert es.collapse_distance == 1.0
    assert not es.is_degraded
    assert not es.is_unsafe


def test_energy_state_update_nominal():
    es = HumanEnergyState()
    es.update(hidden_count=0, automation_count=1, automation_reliability=0.9)
    # With default loads (30+40=70) and no multipliers, should be sustainable
    assert es.fatigue_score == 0.0


def test_energy_state_degrades_with_hidden_vars():
    es = HumanEnergyState()
    es.update(hidden_count=8, automation_count=2, automation_reliability=0.6)
    assert es.fatigue_score > 0


def test_energy_state_accumulates_ai_tax():
    es = HumanEnergyState()
    for _ in range(20):
        es.update(alert_count=5)
    assert es.cumulative_ai_tax > 0
    assert es.false_alert_total == 100


def test_energy_state_is_degraded():
    es = HumanEnergyState(energy_input=50)  # low energy budget
    es.update(hidden_count=5, automation_count=3, automation_reliability=0.5)
    assert es.is_degraded


def test_energy_state_is_unsafe():
    es = HumanEnergyState(energy_input=30)  # very low energy budget
    es.update(
        hidden_count=8, automation_count=3,
        automation_reliability=0.3, alert_count=0,
    )
    # Should push past safety breakdown
    assert es.collapse_distance < 1.0


def test_energy_state_friction_accumulates():
    es = HumanEnergyState()
    es.update(friction_events=3)
    es.update(friction_events=3)
    assert es.cumulative_friction_cost > 0
