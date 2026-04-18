"""
bass/observational/planck_mes_bounds.py  (Week 4 Day 1, Pastén Option B)
=========================================================================

Modern MES (Maartens-Ellis-Stoeger 1995) kinematic bounds re-derived with
Planck 2018 Commander low-ℓ TT data.

This module closes the 29-year gap since Stoeger-Araujo-Gebbie (1997) which
used COBE data. No existing paper has published the full general re-derivation
— Maluf & Neves (2021, arXiv:2105.08659) did the closest analog in a bumblebee
gravity context. Pastén (arXiv:2603.20963, 2026) provides theoretical
motivation via z-dependent dipole formalism but stops short of updating the
all-sky CMB bound.

Mathematical framework (MES Paper II = PRD 51, 5942, 1995):

    ε_ℓ² ≡ [(2ℓ+1) / (4π)] × C_ℓ / T₀²                              (2.4)
    C_ℓ = 2π × D_ℓ / [ℓ(ℓ+1)]                                        (power-D conv)

MES kinematic bounds (Paper II Eqs. 20-22, 32-35):

    σ/Θ ≤ 2 ε₂                                    (shear)             (2.5a)
    ω/Θ ≤ √3 ε₂                                   (vorticity)         (2.5b)
    u̇/Θ ≤ max(3 ε₁^res, 2 ε₂, ε₃)                (four-acceleration) (2.5c)

with ε₁^res the residual dipole after subtracting the kinematic dipole; in the
dominant-channel regime u̇/Θ ≈ 2 ε₂ at Planck precision, as the second argument
of the max dominates.

Planck 2018 Commander low-ℓ TT (arXiv:1807.06205, Table 2):

    D₂ = 201.5 ± 96.6 μK²
    D₃ = 1034 ± 236 μK²

T₀ = 2.7255 K = 2.7255 × 10⁶ μK  (Fixsen ApJ 707, 916, 2009)

Non-goals (deferred to D2)
--------------------------
- Integration with VT-07 β threshold (`baryon_only_policy.beta_policy_gate`)
- Replacement of the illustrative ε₁=0.02 currently wired into `sigma_floor`
- Comparison table with COBE (SAG97), Maluf-Neves 2021, and this-work values
- z-dependent tomographic extension (Pastén's contribution)

D1 scope is: a clean, tested numerical core with documented sources.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ============================================================================
# Section 1 - Constants with provenance
# ============================================================================

T_CMB_K: float = 2.7255
"""CMB monopole temperature in K. Fixsen, ApJ 707, 916 (2009)."""

T_CMB_MICROK: float = 2.7255e6
"""CMB monopole temperature in μK (unit of Planck D_ell values)."""


@dataclass(frozen=True)
class PlanckLowL_Commander:
    """Planck 2018 Commander low-ℓ TT spectrum (arXiv:1807.06205, Table 2).

    D_ℓ ≡ ℓ(ℓ+1) C_ℓ / (2π)  with units μK².

    Uncertainties are 1σ. Both central values and uncertainties include
    cosmic variance and are reported as published. Planck uses one-sided
    cosmic-variance-limited error bars; for a frequentist 2σ upper limit
    we simply take central + 2 × σ.
    """
    D_2_central: float = 201.5
    D_2_sigma: float = 96.6
    D_3_central: float = 1034.0
    D_3_sigma: float = 236.0
    spectrum_id: str = "Planck 2018 Commander low-ℓ TT (arXiv:1807.06205 Table 2)"


# Frozen instance — this is the authoritative Planck data source
PLANCK_2018_COMMANDER: PlanckLowL_Commander = PlanckLowL_Commander()


class ReferenceSource(Enum):
    """Provenance tag for MES bound derivations."""
    COBE_SAG97 = "Stoeger, Araujo & Gebbie, ApJ 476, 435 (1997)"
    MALUF_NEVES_2021 = "Maluf & Neves, PRD 105, 083516 (2021)"
    PLANCK_2018_THIS_WORK = "Planck 2018 Commander via MES (this work)"


# ============================================================================
# Section 2 - Power-spectrum conversions
# ============================================================================

def compute_C_ell(D_ell: float, ell: int) -> float:
    """Convert D_ℓ → C_ℓ via C_ℓ = 2π D_ℓ / [ℓ(ℓ+1)].

    Parameters
    ----------
    D_ell : float
        Temperature power D_ℓ, in μK² (or any consistent T² unit).
    ell : int
        Multipole order, must be ≥ 1.

    Returns
    -------
    float
        C_ℓ in the same T² units as D_ell.
    """
    if ell < 1:
        raise ValueError(f"ell must be ≥ 1, got {ell}")
    if D_ell < 0:
        raise ValueError(f"D_ell must be non-negative, got {D_ell}")
    return 2.0 * math.pi * D_ell / (ell * (ell + 1))


def compute_epsilon_ell(
    D_ell: float,
    ell: int,
    T0_microK: float = T_CMB_MICROK,
) -> float:
    """Compute ε_ℓ from D_ℓ via MES Eq. (2.4).

    ε_ℓ² = [(2ℓ+1) / (4π)] × C_ℓ / T₀²
         = [(2ℓ+1) / (4π)] × 2π D_ℓ / [ℓ(ℓ+1) T₀²]
         = [(2ℓ+1) / (2 ℓ(ℓ+1))] × D_ℓ / T₀²

    Parameters
    ----------
    D_ell : float
        Temperature power in μK².
    ell : int
        Multipole order.
    T0_microK : float
        CMB monopole temperature in μK. Defaults to Fixsen 2009 value.

    Returns
    -------
    float
        ε_ℓ (dimensionless). Always non-negative.
    """
    if ell < 1:
        raise ValueError(f"ell must be ≥ 1, got {ell}")
    if D_ell < 0:
        raise ValueError(f"D_ell must be non-negative, got {D_ell}")
    if T0_microK <= 0:
        raise ValueError(f"T0_microK must be positive, got {T0_microK}")
    C_ell = compute_C_ell(D_ell, ell)
    epsilon_sq = (2 * ell + 1) / (4 * math.pi) * C_ell / (T0_microK ** 2)
    return math.sqrt(epsilon_sq)


# ============================================================================
# Section 3 - MES kinematic bounds
# ============================================================================

@dataclass(frozen=True)
class MESBounds:
    """MES kinematic bounds for a given ε_ℓ set.

    Attributes
    ----------
    epsilon_2, epsilon_3 : float
        Dimensionless temperature-anisotropy multipole amplitudes.
    sigma_over_Theta : float
        2 × ε₂ bound on shear / expansion.
    omega_over_Theta : float
        √3 × ε₂ bound on vorticity / expansion.
    udot_over_Theta : float
        max(3 ε₁^res, 2 ε₂, ε₃). In the Planck regime the 2 ε₂ term
        dominates; 3 ε₁^res is typically removed by dipole subtraction.
    epsilon_1_residual : float
        The residual dipole amplitude after kinematic-dipole subtraction.
        Conventionally set to 0 at the CMB bound level. Supplied here for
        completeness.
    source : ReferenceSource
        Provenance of the ε_ℓ values.
    confidence_level : str
        'central' or '2sigma_upper'.
    """
    epsilon_2: float
    epsilon_3: float
    sigma_over_Theta: float
    omega_over_Theta: float
    udot_over_Theta: float
    epsilon_1_residual: float = 0.0
    source: ReferenceSource = ReferenceSource.PLANCK_2018_THIS_WORK
    confidence_level: str = "central"


def compute_mes_bounds(
    D_2: float,
    D_3: float,
    T0_microK: float = T_CMB_MICROK,
    epsilon_1_residual: float = 0.0,
    source: ReferenceSource = ReferenceSource.PLANCK_2018_THIS_WORK,
    confidence_level: str = "central",
) -> MESBounds:
    """Full MES evaluation from D₂, D₃ inputs.

    Applies Eqs. (2.5a-c) to produce the three kinematic bounds.

    Parameters
    ----------
    D_2, D_3 : float
        Quadrupole and octupole temperature power in μK².
    T0_microK : float
        CMB monopole in μK.
    epsilon_1_residual : float
        Residual dipole after kinematic subtraction. Default 0.
    source : ReferenceSource
        Provenance tag.
    confidence_level : str
        Tag for downstream interpretation.

    Returns
    -------
    MESBounds
    """
    eps_2 = compute_epsilon_ell(D_2, 2, T0_microK)
    eps_3 = compute_epsilon_ell(D_3, 3, T0_microK)

    sigma_bound = 2.0 * eps_2
    omega_bound = math.sqrt(3.0) * eps_2
    udot_bound = max(3.0 * epsilon_1_residual, 2.0 * eps_2, eps_3)

    return MESBounds(
        epsilon_2=eps_2,
        epsilon_3=eps_3,
        sigma_over_Theta=sigma_bound,
        omega_over_Theta=omega_bound,
        udot_over_Theta=udot_bound,
        epsilon_1_residual=epsilon_1_residual,
        source=source,
        confidence_level=confidence_level,
    )


def compute_mes_bounds_2sigma_upper(
    planck: PlanckLowL_Commander = PLANCK_2018_COMMANDER,
    T0_microK: float = T_CMB_MICROK,
    epsilon_1_residual: float = 0.0,
) -> MESBounds:
    """Shortcut: 2σ upper-limit MES bounds using Planck data.

    Uses D_ℓ central + 2 × σ_ℓ as the conservative upper edge of the
    measured band, matching the convention in SAG97 and in the Maluf-Neves
    2021 application.
    """
    D_2_upper = planck.D_2_central + 2.0 * planck.D_2_sigma
    D_3_upper = planck.D_3_central + 2.0 * planck.D_3_sigma
    return compute_mes_bounds(
        D_2=D_2_upper,
        D_3=D_3_upper,
        T0_microK=T0_microK,
        epsilon_1_residual=epsilon_1_residual,
        source=ReferenceSource.PLANCK_2018_THIS_WORK,
        confidence_level="2sigma_upper",
    )


# ============================================================================
# Section 4 - Documented reference values (for cross-check)
# ============================================================================

@dataclass(frozen=True)
class DocumentedReferenceTable:
    """Bound values documented in project knowledge, used for regression.

    Values come from `tomographic_MES_framework.md §2.2` which records the
    "this work" 2σ numbers independently arithmetically verified.
    """
    epsilon_2_2sigma: float = 4.7e-6
    epsilon_3_2sigma: float = 7.7e-6
    sigma_over_Theta_2sigma: float = 9.4e-6
    omega_over_Theta_2sigma: float = 8.2e-6
    udot_over_Theta_2sigma: float = 9.4e-6
    # COBE SAG97 comparison (order-of-magnitude)
    cobe_epsilon_floor: float = 1.0e-4
    # Maluf-Neves 2021 comparison (bumblebee context; model-specific)
    maluf_neves_epsilon_2: float = 1.1e-5
    maluf_neves_epsilon_3: float = 2.6e-5


DOCUMENTED_REFERENCE: DocumentedReferenceTable = DocumentedReferenceTable()


# ============================================================================
# Section 5 - Convenience accessors
# ============================================================================

def compute_planck_central_bounds(
    T0_microK: float = T_CMB_MICROK,
) -> MESBounds:
    """Central-value MES bounds (no 2σ widening). Primarily for diagnostics."""
    return compute_mes_bounds(
        D_2=PLANCK_2018_COMMANDER.D_2_central,
        D_3=PLANCK_2018_COMMANDER.D_3_central,
        T0_microK=T0_microK,
        source=ReferenceSource.PLANCK_2018_THIS_WORK,
        confidence_level="central",
    )


def format_bounds(bounds: MESBounds) -> str:
    """Human-readable one-line summary of a MESBounds instance."""
    return (
        f"[{bounds.confidence_level}, {bounds.source.name}] "
        f"ε₂={bounds.epsilon_2:.3e}, ε₃={bounds.epsilon_3:.3e}, "
        f"σ/Θ={bounds.sigma_over_Theta:.3e}, "
        f"ω/Θ={bounds.omega_over_Theta:.3e}, "
        f"u̇/Θ={bounds.udot_over_Theta:.3e}"
    )
