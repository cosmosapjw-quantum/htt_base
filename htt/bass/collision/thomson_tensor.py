"""
bass/collision/thomson_tensor.py  (Week 4 Day 3)
===================================================

Axisymmetric photon Thomson collision source with W3 runtime gating.

Scope
-----
This is the **Python skeleton** for the photon Thomson collision term on an
axisymmetric Bianchi I background. Every consumer entry point calls
`require_allow_reduction(...)` on a `CanonicalDecision` — this module is the
first real BASS runtime consumer of the W3 canonical decision machinery.

Scope is deliberately axisymmetric (single-DOF STF tensors). Full Bianchi I
tilted-fluid extension, nonlinear Θ⁴ bridge, and E↔B free-streaming mixing are
deferred to W5+ modules. This skeleton exposes the interface shape and exercises
the gating contract; the production numerical core will extend the same API.

Physical equations implemented (axisymmetric)
----------------------------------------------
Thomson collision tensor (ch05 Eq. Thomson-damping, linear order):

    C^(γ)_ab = -τ̇ Θ^(γ)_ab + (τ̇/10) Π_ab                                    (1)

Polarization source STF projection (the E₀ h_ab/3 term has zero STF component
so drops from the rank-2 quadrupole equation):

    Π^STF_ab = Θ^(γ)_ab + E^(γ)_ab                                            (2)

Quasi-static balance (pre-recombination, τ̇ ≫ H):

    Θ^(γ)_ab ≃ (Σ^(γ)_2 / τ̇) σ_ab                                            (3)

Shear source coefficient for photons (ch05 Eq. shear-source, BE radiation,
η = 0):

    Σ^(γ)_2 = (8/15) × I_4/I_3 = (8/15) × (24 ζ(5) / (π⁴/15)) ≈ 2.044        (4)

E-mode polarization Thomson source (Paper VI P2):

    Ė^(γ,1)_ab|_Th = -(2/5) τ̇ c_ξ T^(γ,1)_ab                                 (5)

Axisymmetric reduction
----------------------
In the axisymmetric case every rank-2 STF tensor A_ab has one scalar DOF:

    A_ab = a × (3 n_a n_b - h_ab) / 2                                         (6)

with n the symmetry axis. Addition, scaling, inner product, and collision
operations reduce to scalar operations on the amplitudes a. The full tensor
can be reconstructed via `to_matrix()` for diagnostics.

Non-goals (W5+ deferrals)
-------------------------
- Off-axis STF components (m ≠ 0) — full Bianchi I
- Θ⁴ bridge coupling to collision sources
- Tight-coupling approximation (TCA) switching — covered in
  CAMB_TCA_Mapped_to_PSTF doc
- Second-order quadratic sources (v × Θ, Θ × Θ)
- E ↔ B mode mixing via free-streaming operator
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
from scipy.special import zeta

from bass.runtime.canonical_decision import (
    CanonicalDecision,
    require_allow_reduction,
)


# ============================================================================
# Section 1 - Constants
# ============================================================================

def _compute_sigma_2_BE() -> float:
    """Σ^(γ)_2 = (8/15) × (I_4/I_3)|_BE for photons at η=0.

    Exact: I_4/I_3 = 24 ζ(5) / (π^4/15) ≈ 3.8322.
    Therefore Σ^(γ)_2 ≈ (8/15) × 3.8322 ≈ 2.044.
    """
    I_4_over_I_3 = 24.0 * float(zeta(5)) / (math.pi ** 4 / 15.0)
    return (8.0 / 15.0) * I_4_over_I_3


SIGMA_2_PHOTON_BE: float = _compute_sigma_2_BE()
"""Photon shear-source coefficient Σ^(γ)_2 for BE radiation at η=0. ≈ 2.044."""

THOMSON_POLARIZATION_COEFF: float = 1.0 / 10.0
"""The (1/10) factor on Π_ab in the Thomson collision formula."""

E_MODE_THOMSON_COEFF: float = 2.0 / 5.0
"""The (2/5) factor in the E-mode polarization Thomson source."""


# ============================================================================
# Section 2 - Axisymmetric STF tensor type
# ============================================================================

class SymmetryAxis(Enum):
    """Spatial symmetry axis for axisymmetric Bianchi I."""
    X = "x"
    Y = "y"
    Z = "z"


@dataclass(frozen=True)
class AxisymmetricSTFTensor:
    """Rank-2 STF tensor parametrized by one amplitude + axis.

    Representation:
        A_ab = amplitude × (3 n_a n_b - h_ab) / 2

    where n is the unit vector along `axis` and h_ab = diag(1, 1, 1) is the
    spatial projection tensor (flat spatial metric for Bianchi I at linear
    order). The factor of 3/2 normalization puts the diagonal entry along
    the axis at `+ amplitude` and the two transverse entries at
    `- amplitude / 2`.

    Trace: Tr(A) = 3×(+amp/(something)) + 2×(-amp/(something))... actually
    let's do the exact arithmetic once. With the (3 n_a n_b - h_ab)/2 form:
        A_aa = (3 - 3) / 2 × amplitude = 0. ✓ STF confirmed.
        A_zz = (3×1 - 1) / 2 × amplitude = amplitude  (for axis='z')
        A_xx = A_yy = (3×0 - 1) / 2 × amplitude = -amplitude/2
    """
    amplitude: float
    axis: SymmetryAxis = SymmetryAxis.Z

    def to_matrix(self) -> np.ndarray:
        """Return the 3×3 STF matrix."""
        n = np.zeros(3)
        idx = {SymmetryAxis.X: 0, SymmetryAxis.Y: 1, SymmetryAxis.Z: 2}[self.axis]
        n[idx] = 1.0
        h = np.eye(3)
        return 0.5 * self.amplitude * (3.0 * np.outer(n, n) - h)

    def trace(self) -> float:
        """Trace should be zero for STF tensors (up to numerical noise)."""
        return float(np.trace(self.to_matrix()))

    def scale(self, factor: float) -> "AxisymmetricSTFTensor":
        """Scalar multiplication preserves axis."""
        return AxisymmetricSTFTensor(
            amplitude=self.amplitude * factor, axis=self.axis,
        )

    def add(self, other: "AxisymmetricSTFTensor") -> "AxisymmetricSTFTensor":
        """Sum two tensors on the same axis."""
        if self.axis != other.axis:
            raise ValueError(
                f"cannot add tensors on different axes: "
                f"{self.axis} vs {other.axis}"
            )
        return AxisymmetricSTFTensor(
            amplitude=self.amplitude + other.amplitude, axis=self.axis,
        )


# ============================================================================
# Section 3 - Thomson collision result container
# ============================================================================

@dataclass(frozen=True)
class ThomsonCollisionResult:
    """Output of one Thomson collision evaluation.

    Attributes
    ----------
    collision : AxisymmetricSTFTensor
        The intensity-side Thomson source C^(γ)_ab = -τ̇(Θ - Π/10).
    polarization_source_stf : AxisymmetricSTFTensor
        The STF part of Π_ab (= Θ + E; E₀ h_ab/3 drops out).
    opacity : float
        τ̇ = n_e σ_T used in the computation.
    in_quasi_static_regime : bool
        True iff τ̇/H > threshold. False means free-streaming regime.
    tau_dot_over_H : Optional[float]
        Ratio τ̇/H if `hubble_rate` was supplied, else None.
    """
    collision: AxisymmetricSTFTensor
    polarization_source_stf: AxisymmetricSTFTensor
    opacity: float
    in_quasi_static_regime: bool
    tau_dot_over_H: Optional[float]


# ============================================================================
# Section 4 - Main entry points
# ============================================================================

QUASI_STATIC_TAU_H_THRESHOLD: float = 10.0
"""τ̇/H > this value means quasi-static (Thomson-dominated) regime."""


def compute_photon_thomson_collision(
    theta_gamma: AxisymmetricSTFTensor,
    E_gamma: AxisymmetricSTFTensor,
    n_e_sigmaT: float,
    decision: CanonicalDecision,
    hubble_rate: Optional[float] = None,
) -> ThomsonCollisionResult:
    """Compute the photon Thomson collision tensor, axisymmetric, linear order.

    Evaluates:

        C^(γ)_ab = -τ̇ (Θ^(γ)_ab - Π^STF_ab / 10)
        Π^STF_ab = Θ^(γ)_ab + E^(γ)_ab

    Parameters
    ----------
    theta_gamma : AxisymmetricSTFTensor
        Photon temperature quadrupole Θ^(γ)_ab.
    E_gamma : AxisymmetricSTFTensor
        Photon E-mode polarization tensor E^(γ)_ab.
    n_e_sigmaT : float
        Thomson opacity τ̇ = n_e σ_T in units matching 1/time.
    decision : CanonicalDecision
        Runtime gate. Collision evaluation proceeds only if
        `decision.allow_reduction == True`.
    hubble_rate : float, optional
        H in the same time units as τ̇. If supplied, the quasi-static
        regime flag is computed.

    Raises
    ------
    CanonicalBlockError
        If `decision.allow_reduction` is False.
    ValueError
        If the two input tensors have mismatched axes or if τ̇ < 0.

    Returns
    -------
    ThomsonCollisionResult
    """
    require_allow_reduction(
        decision, context="compute_photon_thomson_collision"
    )

    if n_e_sigmaT < 0:
        raise ValueError(f"n_e_sigmaT must be non-negative, got {n_e_sigmaT}")
    if theta_gamma.axis != E_gamma.axis:
        raise ValueError(
            f"theta_gamma axis {theta_gamma.axis} does not match "
            f"E_gamma axis {E_gamma.axis}"
        )

    # STF polarization source
    pi_stf = theta_gamma.add(E_gamma)

    # Collision amplitude:  C = -τ̇ (Θ - Π/10)
    collision_amp = -n_e_sigmaT * (
        theta_gamma.amplitude
        - THOMSON_POLARIZATION_COEFF * pi_stf.amplitude
    )
    collision = AxisymmetricSTFTensor(
        amplitude=collision_amp, axis=theta_gamma.axis,
    )

    # Quasi-static diagnostic
    if hubble_rate is not None and hubble_rate > 0:
        tau_H = n_e_sigmaT / hubble_rate
        quasi_static = tau_H > QUASI_STATIC_TAU_H_THRESHOLD
    else:
        tau_H = None
        quasi_static = False

    return ThomsonCollisionResult(
        collision=collision,
        polarization_source_stf=pi_stf,
        opacity=n_e_sigmaT,
        in_quasi_static_regime=quasi_static,
        tau_dot_over_H=tau_H,
    )


def compute_quasi_static_theta(
    shear: AxisymmetricSTFTensor,
    n_e_sigmaT: float,
    decision: CanonicalDecision,
    Sigma_2: float = SIGMA_2_PHOTON_BE,
) -> AxisymmetricSTFTensor:
    """Quasi-static photon quadrupole: Θ^(γ)_ab ≃ (Σ_2 / τ̇) σ_ab.

    Valid in the Thomson-dominated regime τ̇ ≫ H (pre-recombination).
    """
    require_allow_reduction(decision, context="compute_quasi_static_theta")

    if n_e_sigmaT <= 0:
        raise ValueError(
            f"n_e_sigmaT must be positive for quasi-static limit, "
            f"got {n_e_sigmaT}"
        )
    theta_amp = Sigma_2 * shear.amplitude / n_e_sigmaT
    return AxisymmetricSTFTensor(amplitude=theta_amp, axis=shear.axis)


def compute_e_mode_thomson_source(
    T_gamma: AxisymmetricSTFTensor,
    n_e_sigmaT: float,
    decision: CanonicalDecision,
    c_xi: float = 1.0,
) -> AxisymmetricSTFTensor:
    """Paper VI P2 E-mode polarization Thomson source.

    Ė^(γ,1)_ab|_Th = -(2/5) τ̇ c_ξ T^(γ,1)_ab

    The c_ξ coefficient (Challinor PSTF convention) depends on the statistics
    and defaults to 1.0 (ξ-independent at linear order for the Paper VI
    derivation of the E-mode source).
    """
    require_allow_reduction(decision, context="compute_e_mode_thomson_source")

    if n_e_sigmaT < 0:
        raise ValueError(f"n_e_sigmaT must be non-negative, got {n_e_sigmaT}")

    e_dot_amp = -E_MODE_THOMSON_COEFF * n_e_sigmaT * c_xi * T_gamma.amplitude
    return AxisymmetricSTFTensor(amplitude=e_dot_amp, axis=T_gamma.axis)


# ============================================================================
# Section 5 - Diagnostics
# ============================================================================

def verify_quasi_static_regime(
    n_e_sigmaT: float,
    hubble_rate: float,
    threshold: float = QUASI_STATIC_TAU_H_THRESHOLD,
) -> bool:
    """True iff τ̇/H > threshold (Thomson-dominated regime)."""
    if hubble_rate <= 0:
        raise ValueError(f"hubble_rate must be positive, got {hubble_rate}")
    return (n_e_sigmaT / hubble_rate) > threshold


def photon_Sigma_2_coefficient() -> float:
    """Publicly-exposed Σ^(γ)_2 for BE radiation at η=0."""
    return SIGMA_2_PHOTON_BE
