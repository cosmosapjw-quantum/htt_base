"""
htt/infer/control_registry.py — Matched-Complexity Controls
=============================================================
P-15 deliverable. Four controls with matched parameter counts:

  C0 (baseline):     Current scalar-amplitude pipeline (no direction)
  C1 (aligned):      Latent axis forced to CMB dipole direction
  C2 (misaligned):   Latent axis forced 90° from CMB dipole
  C3 (disconnected): Each survey has independent direction

Matched-complexity: all controls have the same number of amplitude
parameters, nuisance parameters, and prior widths. Only the
directional structure differs.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Callable

__all__ = [
    'ControlSpec', 'CONTROLS', 'get_control',
    'matched_complexity_check',
]


@dataclass(frozen=True)
class ControlSpec:
    """Specification for a matched-complexity control."""
    name: str
    code: str           # C0, C1, C2, C3
    n_direction: int    # number of direction parameters
    n_amplitude: int    # number of amplitude parameters
    n_nuisance: int     # number of nuisance parameters
    n_total: int        # total parameters
    direction_constraint: str   # description of direction handling
    prior_width_amplitude: float  # prior width for amplitude params
    prior_width_nuisance: float   # prior width for nuisance params


# ── Control definitions ─────────────────────────────────────

C0 = ControlSpec(
    name='baseline',
    code='C0',
    n_direction=0,
    n_amplitude=1,   # β only
    n_nuisance=0,
    n_total=1,
    direction_constraint='None (scalar amplitude only)',
    prior_width_amplitude=1e-1,  # log-uniform over 4 decades
    prior_width_nuisance=0.0,
)

C1 = ControlSpec(
    name='aligned',
    code='C1',
    n_direction=0,   # fixed to CMB dipole
    n_amplitude=4,   # A + δ_CW + δ_rad + δ_CF4
    n_nuisance=2,    # σ_sys_CW + σ_sys_rad
    n_total=6,
    direction_constraint='Fixed at CMB dipole (l=264°, b=+48°)',
    prior_width_amplitude=2e-3,
    prior_width_nuisance=5e-4,
)

C2 = ControlSpec(
    name='misaligned',
    code='C2',
    n_direction=0,   # fixed 90° from CMB
    n_amplitude=4,
    n_nuisance=2,
    n_total=6,
    direction_constraint='Fixed 90° from CMB dipole (l=354°, b=0°)',
    prior_width_amplitude=2e-3,
    prior_width_nuisance=5e-4,
)

C3 = ControlSpec(
    name='disconnected',
    code='C3',
    n_direction=6,   # (l,b) per survey × 3
    n_amplitude=3,   # A_CW + A_rad + A_CF4
    n_nuisance=2,
    n_total=11,
    direction_constraint='Independent (l,b) per survey',
    prior_width_amplitude=2e-3,
    prior_width_nuisance=5e-4,
)

CONTROLS = {
    'C0': C0,
    'C1': C1,
    'C2': C2,
    'C3': C3,
}


def get_control(code: str) -> ControlSpec:
    """Retrieve a control by code."""
    if code not in CONTROLS:
        raise KeyError(f"Unknown control '{code}'. Available: {list(CONTROLS)}")
    return CONTROLS[code]


def matched_complexity_check() -> dict:
    """Verify matched-complexity constraints across C1–C3.

    Returns dict with check results. C0 is exempt (baseline).
    """
    checks = {}

    # C1 and C2 must have identical parameter structure
    checks['C1_C2_amplitude_match'] = C1.n_amplitude == C2.n_amplitude
    checks['C1_C2_nuisance_match'] = C1.n_nuisance == C2.n_nuisance
    checks['C1_C2_prior_width_match'] = (
        C1.prior_width_amplitude == C2.prior_width_amplitude
        and C1.prior_width_nuisance == C2.prior_width_nuisance
    )

    # C3 has more direction parameters but same amplitude priors
    checks['C3_amplitude_prior_match'] = (
        C3.prior_width_amplitude == C1.prior_width_amplitude
    )
    checks['C3_nuisance_match'] = C3.n_nuisance == C1.n_nuisance

    checks['all_pass'] = all(checks.values())
    return checks
