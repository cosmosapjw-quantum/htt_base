"""
bass/observational/beta_threshold.py  (Week 4 Day 2, Pastén Option B Part 2)
=============================================================================

VT-07 safe-route β threshold derived from Planck-updated MES bounds.

Background
----------
The VT-07 correction (frame-attribution bias ~16%, Week 1 derivation) yields
the safe-route relation:

    β ≤ ε₁ / (1 + η_u̇)                                                    (VT-07)

where:
- β is the production tilt parameter (VER06: β = 1.36 × 10⁻³),
- ε₁ is the MES-scheme bound interpreted as the maximum shear-like anisotropy
  the tilt is allowed to produce, and
- η_u̇ = 1/12 ≈ 0.0833 is the thesis four-acceleration coefficient in the
  bound hierarchy (theoretical, not observational).

The module `bass.runtime.sigma_floor` currently encodes an illustrative
ε₁ = 0.02 that was used to populate VER06. D2 exposes the Planck-derived
alternative as a diagnostic pathway, WITHOUT modifying the production
illustrative value until the comparison has been reviewed.

Chosen ε₁ assignment
--------------------
For the Planck-derived path we set ε₁^Planck ≡ σ/Θ|_Planck = 2 ε₂.
Rationale:
- σ/Θ is the tightest MES kinematic bound on any shear-like observable.
- The safe-route formula is most conservative (blocks more β values) when
  ε₁ is the tightest available bound.
- Alternative choices (ε₃, ω/Θ, u̇/Θ) are all less tight in the Planck
  regime where 2ε₂ dominates.

Downstream consumers (D2+)
--------------------------
This module does NOT modify `sigma_floor.compute_beta_threshold` or
`baryon_only_policy.beta_policy_gate`. It emits a new
`PlanckBetaThreshold` dataclass for comparison, logging, and future
integration. The production threshold remains under explicit user control
until VER07 policy update.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from bass.observational.planck_mes_bounds import (
    MESBounds,
    ReferenceSource,
    compute_mes_bounds,
    compute_mes_bounds_2sigma_upper,
    DOCUMENTED_REFERENCE,
)

# PR-124: active MES consumers traverse the typed successor registry
# (common.mes_theorem_authority is the live authority; legacy values are
# labeled non-authoritative reproduction, see legacy_reproduction_coefficients).
from common.mes_successor_registry import current_mes_successor_registry

_MES_SUCCESSOR = current_mes_successor_registry().successor
_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id


# ============================================================================
# Section 1 - Thesis coefficients (theoretical, not observational)
# ============================================================================

ETA_U_DOT_THESIS: float = 1.0 / 12.0
"""Thesis four-acceleration coefficient η_u̇ = 1/12 ≈ 0.0833.

THEORETICAL value from the MES bound hierarchy structure (ratio of
acceleration-bound coefficient to shear-bound coefficient). Not an
observational parameter — does not update with new CMB data.
"""

PRODUCTION_BETA: float = 1.36e-3
"""VER06 production tilt parameter value from the dipole decomposition fit."""


# ============================================================================
# Section 2 - ε₁ assignment policies
# ============================================================================

class Epsilon1Policy(Enum):
    """How to derive ε₁ for the VT-07 safe-route formula.

    PLANCK_SHEAR:    ε₁ = σ/Θ|_Planck = 2 ε₂ (tightest, default)
    PLANCK_EPS2:     ε₁ = ε₂|_Planck   (alternative)
    PLANCK_EPS3:     ε₁ = ε₃|_Planck   (less tight in Planck regime)
    COBE_SHEAR:      ε₁ = σ/Θ|_COBE (for historical comparison)
    ILLUSTRATIVE:    ε₁ = 0.02 (non-physical; matches pre-D2 sigma_floor path)
    """
    PLANCK_SHEAR = "planck_shear"
    PLANCK_EPS2 = "planck_eps2"
    PLANCK_EPS3 = "planck_eps3"
    COBE_SHEAR = "cobe_shear"
    ILLUSTRATIVE = "illustrative"


def resolve_epsilon_1(
    policy: Epsilon1Policy,
    bounds: Optional[MESBounds] = None,
) -> float:
    """Return ε₁ for the chosen policy.

    Parameters
    ----------
    policy : Epsilon1Policy
    bounds : MESBounds, optional
        Pre-computed MESBounds. Required for PLANCK_* policies; ignored for
        ILLUSTRATIVE and COBE_SHEAR (which have hard-coded reference values).

    Returns
    -------
    float
        ε₁ value, dimensionless.
    """
    if policy == Epsilon1Policy.ILLUSTRATIVE:
        return 0.02
    if policy == Epsilon1Policy.COBE_SHEAR:
        # SAG97 documented σ/Θ < 2×10⁻⁴
        return 2.0 * DOCUMENTED_REFERENCE.cobe_epsilon_floor
    if bounds is None:
        bounds = compute_mes_bounds_2sigma_upper()
    if policy == Epsilon1Policy.PLANCK_SHEAR:
        return bounds.sigma_over_Theta
    if policy == Epsilon1Policy.PLANCK_EPS2:
        return bounds.epsilon_2
    if policy == Epsilon1Policy.PLANCK_EPS3:
        return bounds.epsilon_3
    raise ValueError(f"unknown policy: {policy}")


# ============================================================================
# Section 3 - β threshold container + computation
# ============================================================================

@dataclass(frozen=True)
class PlanckBetaThreshold:
    """VT-07 safe-route β threshold derived from Planck data.

    Attributes
    ----------
    beta_max : float
        The computed upper bound on β.
    epsilon_1 : float
        Value of ε₁ used in the formula.
    eta_u_dot : float
        Value of η_u̇ used.
    safety_factor : float
        Applied multiplicative safety factor (∈ (0, 1] typically).
    policy : Epsilon1Policy
        Which ε₁ derivation was used.
    production_beta : float
        VER06 β value for comparison.
    production_passes : bool
        True iff production_beta ≤ beta_max.
    slack : float
        beta_max − production_beta (positive = production safe, negative = blocked).
    """
    beta_max: float
    epsilon_1: float
    eta_u_dot: float
    safety_factor: float
    policy: Epsilon1Policy
    production_beta: float
    production_passes: bool
    slack: float


def compute_beta_threshold_from_planck(
    eta_u_dot: float = ETA_U_DOT_THESIS,
    safety_factor: float = 1.0,
    policy: Epsilon1Policy = Epsilon1Policy.PLANCK_SHEAR,
    bounds: Optional[MESBounds] = None,
    production_beta: float = PRODUCTION_BETA,
) -> PlanckBetaThreshold:
    """Evaluate the VT-07 safe-route β threshold under the given policy.

    β_max = safety_factor × ε₁ / (1 + η_u̇)

    Parameters
    ----------
    eta_u_dot : float
        Thesis four-acceleration coefficient. Defaults to 1/12.
    safety_factor : float
        Additional margin ∈ (0, 1] — tighter values produce tighter thresholds.
    policy : Epsilon1Policy
        ε₁ derivation strategy.
    bounds : MESBounds, optional
        Pre-computed bounds; otherwise uses Planck 2σ upper.
    production_beta : float
        VER06 tilt parameter for comparison.

    Returns
    -------
    PlanckBetaThreshold
    """
    if eta_u_dot < 0:
        raise ValueError(f"eta_u_dot must be non-negative, got {eta_u_dot}")
    if not (0 < safety_factor <= 1):
        raise ValueError(
            f"safety_factor must be in (0, 1], got {safety_factor}"
        )
    if production_beta < 0:
        raise ValueError(
            f"production_beta must be non-negative, got {production_beta}"
        )

    eps_1 = resolve_epsilon_1(policy, bounds)
    beta_max = safety_factor * eps_1 / (1.0 + eta_u_dot)
    passes = production_beta <= beta_max

    return PlanckBetaThreshold(
        beta_max=beta_max,
        epsilon_1=eps_1,
        eta_u_dot=eta_u_dot,
        safety_factor=safety_factor,
        policy=policy,
        production_beta=production_beta,
        production_passes=passes,
        slack=beta_max - production_beta,
    )


# ============================================================================
# Section 4 - Multi-policy comparison (diagnostic)
# ============================================================================

def compare_all_policies(
    eta_u_dot: float = ETA_U_DOT_THESIS,
    safety_factor: float = 1.0,
    production_beta: float = PRODUCTION_BETA,
) -> dict:
    """Evaluate β threshold under every Epsilon1Policy.

    Returns a dict {policy: PlanckBetaThreshold} for side-by-side comparison.
    Useful for the D2 PASTEN_OPTION_B_REPORT artifact and for verifying that
    the illustrative ε₁ = 0.02 accepts the production β while Planck-derived
    values would reject it.
    """
    bounds_planck = compute_mes_bounds_2sigma_upper()
    result = {}
    for policy in Epsilon1Policy:
        threshold = compute_beta_threshold_from_planck(
            eta_u_dot=eta_u_dot,
            safety_factor=safety_factor,
            policy=policy,
            bounds=bounds_planck,
            production_beta=production_beta,
        )
        result[policy] = threshold
    return result


def format_threshold(threshold: PlanckBetaThreshold) -> str:
    """Single-line summary."""
    verdict = "PASS" if threshold.production_passes else "BLOCK"
    return (
        f"[{threshold.policy.value}] ε₁={threshold.epsilon_1:.3e}, "
        f"β_max={threshold.beta_max:.3e}, "
        f"β_prod={threshold.production_beta:.3e}, "
        f"slack={threshold.slack:+.3e}, {verdict}"
    )
