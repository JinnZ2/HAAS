"""Human energy model — ported from the Thermodynamic Accountability Framework.

Models the human operator as an energy system, not just a point mass.
Computes fatigue, distance-to-collapse, and the cognitive/metabolic cost
of operating alongside automation and AI systems.

Reference: github.com/JinnZ2/thermodynamic-accountability-framework
Modules: core/fatigue_model.py, core/human_system_collapse_model.py, core/data_logger.py

TAF Principle: "Does the energy return to an organism exceed what gets
extracted from it?" If not, the organism degrades — regardless of narrative.
"""

import math
from dataclasses import dataclass, field


# ============================================================
# Fatigue Model (TAF core)
# ============================================================

def hidden_variable_multiplier(hidden_count: int) -> float:
    """Hidden variables increase energy demand nonlinearly.

    Each additional hidden variable multiplies the space of possible failure
    modes — combinatorial explosion of interaction effects.
    TAF equation: 1 + 0.1 * count^1.5
    """
    if hidden_count <= 0:
        return 1.0
    return 1 + 0.1 * hidden_count ** 1.5


def automation_load_multiplier(automation_count: int, reliability: float = 0.9) -> float:
    """Unreliable automation isn't reducing load — it's adding monitoring burden.

    TAF equation: 1 + count * (1 - reliability) * 0.5
    """
    return 1 + automation_count * (1 - reliability) * 0.5


def environment_multiplier(temp_celsius: float = 20.0, wind_mps: float = 0.0) -> float:
    """Cold and wind increase physical and cognitive energy expenditure.

    TAF equation: 1 + max(0, (15 - temp) * 0.05) + wind * 0.02
    """
    temp_stress = max(0.0, (15 - temp_celsius) * 0.05)
    wind_stress = wind_mps * 0.02
    return 1 + temp_stress + wind_stress


def compute_fatigue(
    physical_load: float,
    cognitive_load: float,
    energy_input: float = 100.0,
    hidden_count: int = 0,
    automation_count: int = 0,
    automation_reliability: float = 0.9,
    temp_celsius: float = 20.0,
    wind_mps: float = 0.0,
) -> dict:
    """Compute human fatigue score with full breakdown.

    Returns a dict with fatigue_score (0–10), total load, deficit, and multipliers.
    """
    base_load = physical_load + cognitive_load

    hv_mult = hidden_variable_multiplier(hidden_count)
    auto_mult = automation_load_multiplier(automation_count, automation_reliability)
    env_mult = environment_multiplier(temp_celsius, wind_mps)

    adjusted_load = base_load * hv_mult * auto_mult * env_mult
    deficit = adjusted_load - energy_input
    fatigue_score = max(0.0, min(10.0, deficit / energy_input * 10))

    return {
        "fatigue_score": round(fatigue_score, 1),
        "base_load": base_load,
        "adjusted_load": round(adjusted_load, 1),
        "energy_input": energy_input,
        "deficit": round(deficit, 1),
        "multipliers": {
            "hidden_variables": round(hv_mult, 2),
            "automation": round(auto_mult, 2),
            "environment": round(env_mult, 2),
            "combined": round(hv_mult * auto_mult * env_mult, 2),
        },
    }


# ============================================================
# Collapse Model (TAF core)
# ============================================================

# TAF collapse thresholds as fractions of energy_input
PRODUCTIVITY_THRESHOLD = 1.2
SAFETY_THRESHOLD = 1.4
HEALTH_THRESHOLD = 1.6


def distance_to_collapse(total_load: float, energy_input: float = 100.0) -> float:
    """0–1 scale: 1 = fully sustainable, 0 = collapse threshold reached.

    TAF equation: clamp(0, 1, (1.6 * E_input - load) / (1.6 * E_input))
    """
    health_limit = HEALTH_THRESHOLD * energy_input
    return round(max(0.0, min(1.0, (health_limit - total_load) / health_limit)), 3)


def collapse_flags(total_load: float, energy_input: float = 100.0) -> list[str]:
    """Return human-readable collapse warning flags."""
    flags: list[str] = []
    if total_load >= HEALTH_THRESHOLD * energy_input:
        flags.append("HEALTH_COLLAPSE_IMMINENT")
    elif total_load >= SAFETY_THRESHOLD * energy_input:
        flags.append("SAFETY_BREAKDOWN_LIKELY")
    elif total_load >= PRODUCTIVITY_THRESHOLD * energy_input:
        flags.append("PRODUCTIVITY_DEGRADATION")
    return flags


# ============================================================
# Long-Tail Risk (TAF core)
# ============================================================

def long_tail_risk(hidden_count: int) -> float:
    """Hidden variables are the logarithmic factor for long-tail risk.

    TAF equation: 10 * (1 - exp(-0.35 * count)), 0–10 scale.
    """
    if hidden_count <= 0:
        return 0.0
    return round(min(10.0, 10 * (1 - math.exp(-0.35 * hidden_count))), 1)


# ============================================================
# Parasitic Energy Debt (TAF data_logger)
# ============================================================

def parasitic_energy_debt(
    unpaid_hours: float,
    friction_events: int,
    metabolic_rate: float = 1.0,
) -> float:
    """Energy extracted without resource replenishment.

    TAF equation: unpaid_hours * metabolic_rate * (1 + friction_events * 0.15)
    """
    friction_multiplier = 1 + friction_events * 0.15
    return round(unpaid_hours * metabolic_rate * friction_multiplier, 2)


# ============================================================
# Ghost-Friction / AI-Tax (TAF Safety-accounting case study)
# ============================================================

def ghost_friction_cost(
    false_alert_count: int,
    metabolic_cost_per_alert: float = 0.5,
    attention_cost_per_alert: float = 0.3,
    trust_erosion_per_alert: float = 0.1,
) -> dict:
    """Compute the cumulative cognitive/metabolic cost of false alerts.

    Each false alert operates on three fronts simultaneously:
    1. Metabolic spike (cortisol, heart rate)
    2. Attention theft (split focus)
    3. Trust erosion (discounting future real alerts)
    """
    metabolic = false_alert_count * metabolic_cost_per_alert
    attention = false_alert_count * attention_cost_per_alert
    trust = min(1.0, false_alert_count * trust_erosion_per_alert)
    return {
        "metabolic_cost": round(metabolic, 2),
        "attention_cost": round(attention, 2),
        "trust_erosion": round(trust, 3),
        "total_ai_tax": round(metabolic + attention, 2),
    }


# ============================================================
# HAAS-Q Integration: HumanEnergyState
# ============================================================

@dataclass
class HumanEnergyState:
    """Tracks the human operator's energy budget across simulation steps.

    Bridges TAF's energy model with HAAS-Q's spatial/control model.
    Updated each simulation step to accumulate fatigue, AI-tax, and
    institutional friction costs.
    """

    energy_input: float = 100.0
    physical_load: float = 30.0
    cognitive_load: float = 40.0

    # Environment (can be updated per-step)
    temp_celsius: float = 20.0
    wind_mps: float = 0.0

    # Accumulated costs
    cumulative_ai_tax: float = 0.0
    cumulative_friction_cost: float = 0.0
    false_alert_total: int = 0

    # Computed (updated each step)
    fatigue_score: float = 0.0
    total_load: float = 0.0
    collapse_distance: float = 1.0
    flags: list[str] = field(default_factory=list)

    def update(
        self,
        hidden_count: int = 0,
        automation_count: int = 1,
        automation_reliability: float = 0.9,
        alert_count: int = 0,
        friction_events: int = 0,
    ) -> None:
        """Recompute energy state for the current step.

        Maps HAAS-Q simulation state to TAF energy variables:
        - sensor_noise levels → hidden_count
        - brake_efficiency → automation_reliability
        - alert_count → ghost-friction / AI-tax
        - institutional_friction → parasitic energy debt
        """
        # Ghost-friction from alerts this step
        self.false_alert_total += alert_count
        gf = ghost_friction_cost(alert_count)
        self.cumulative_ai_tax += gf["total_ai_tax"]

        # Institutional friction cost
        if friction_events > 0:
            debt = parasitic_energy_debt(0.1, friction_events)
            self.cumulative_friction_cost += debt

        # Effective cognitive load includes accumulated AI-tax
        effective_cognitive = self.cognitive_load + self.cumulative_ai_tax * 0.5

        result = compute_fatigue(
            physical_load=self.physical_load,
            cognitive_load=effective_cognitive,
            energy_input=self.energy_input,
            hidden_count=hidden_count,
            automation_count=automation_count,
            automation_reliability=automation_reliability,
            temp_celsius=self.temp_celsius,
            wind_mps=self.wind_mps,
        )

        self.fatigue_score = result["fatigue_score"]
        self.total_load = result["adjusted_load"]
        self.collapse_distance = distance_to_collapse(self.total_load, self.energy_input)
        self.flags = collapse_flags(self.total_load, self.energy_input)

    @property
    def is_degraded(self) -> bool:
        """True if operator has crossed the productivity degradation threshold."""
        return self.fatigue_score > 5.0

    @property
    def is_unsafe(self) -> bool:
        """True if operator has crossed the safety breakdown threshold."""
        return self.collapse_distance < 0.2
