"""
bass/transport/ray_transport.py  (Week 4 Day 4)
=================================================

Axisymmetric ℓ=2 transport equation for photon and neutrino quadrupoles,
with W3 runtime gating at every public entry.

Scope
-----
Single-species, single-multipole (ℓ=2) transport equation:

    dΘ^(s)_ab/dt + Γ^(s) Θ^(s)_ab = Σ^(s)_2 σ_ab + O(ℓ=4)                   (*)

where:
- Θ^(s)_ab is the species quadrupole (axisymmetric: one DOF)
- Γ^(s) is the species-dependent damping rate:
    Γ^(γ) = τ̇ = n_e σ_T           (photon, Thomson damping)
    Γ^(ν) ~ H                       (neutrino, Hubble damping only)
- Σ^(s)_2 = (8/15) I_4/I_3 is the shear-source coefficient (species-dependent)
- σ_ab is the background shear tensor (driver)
- The O(ℓ=4) leakage term is absorbed at the absorbing boundary (W5+)

This module implements:
- Euler step of (*) with frozen σ background
- Analytic steady-state Θ_∞ = Σ_2 σ / Γ
- Integration-to-convergence driver
- Damping-rate helpers for photon (collision-coupled) and neutrino
  (collision-free) variants

The linear damping equation (*) is identical in structure for both species;
only Γ^(s) differs. This is the skeleton: production code extends to ℓ ≥ 3
streaming coupling via the divergence term D^b Θ_{bA_ℓ}.

Non-goals (W5+ deferrals)
-------------------------
- Multi-ℓ hierarchy coupling (D_⟨a_ℓ Θ_{A_{ℓ-1}⟩})
- Off-axis (m ≠ 0) components
- Nonlinear Θ⁴ bridge
- Tilt-induced dipole-quadrupole mixing
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from bass.collision.thomson_tensor import (
    AxisymmetricSTFTensor,
    SymmetryAxis,
    SIGMA_2_PHOTON_BE,
)
from bass.runtime.canonical_decision import (
    CanonicalDecision,
    require_allow_reduction,
)


# ============================================================================
# Section 1 - Species identification
# ============================================================================

class TransportSpecies(Enum):
    """Species whose quadrupole transport is covered by this module.

    PHOTON    : Collision-coupled, Γ = τ̇. Σ_2 = 2.044 (BE, η=0).
    NEUTRINO  : Collision-free, Γ ~ H. Σ_2 ≈ 2.19 (FD, η=0; see Paper I).
    """
    PHOTON = "photon"
    NEUTRINO = "neutrino"


# Shear-source coefficient per species at η=0.
# Photon: BE, I_4/I_3 ≈ 3.832, Σ_2 ≈ 2.044.
# Neutrino: FD, I_4/I_3 ≈ 4.106, Σ_2 ≈ 2.190.
SIGMA_2_NEUTRINO_FD: float = (8.0 / 15.0) * 4.10596
"""Neutrino FD quadrupole shear-source coefficient at η=0."""


# ============================================================================
# Section 2 - Damping-rate helpers
# ============================================================================

def photon_damping_rate(
    n_e_sigmaT: float,
    decision: CanonicalDecision,
) -> float:
    """Thomson damping rate for photons: Γ^(γ) = τ̇ = n_e σ_T.

    Parameters
    ----------
    n_e_sigmaT : float
        Thomson opacity. Must be non-negative.
    decision : CanonicalDecision
        Runtime gate.

    Returns
    -------
    float
        Γ^(γ) ≥ 0.
    """
    require_allow_reduction(decision, context="photon_damping_rate")
    if n_e_sigmaT < 0:
        raise ValueError(f"n_e_sigmaT must be non-negative, got {n_e_sigmaT}")
    return n_e_sigmaT


def neutrino_damping_rate(
    hubble_rate: float,
    decision: CanonicalDecision,
) -> float:
    """Hubble damping rate for free-streaming neutrinos: Γ^(ν) ~ H.

    Neutrinos have no Thomson coupling at T << 1 MeV; the only damping is
    cosmological redshift, captured by the Hubble rate.
    """
    require_allow_reduction(decision, context="neutrino_damping_rate")
    if hubble_rate <= 0:
        raise ValueError(
            f"hubble_rate must be positive, got {hubble_rate}"
        )
    return hubble_rate


def species_shear_coefficient(species: TransportSpecies) -> float:
    """Default Σ^(s)_2 for each species at η=0."""
    if species == TransportSpecies.PHOTON:
        return SIGMA_2_PHOTON_BE
    if species == TransportSpecies.NEUTRINO:
        return SIGMA_2_NEUTRINO_FD
    raise ValueError(f"unknown species: {species}")


# ============================================================================
# Section 3 - Transport parameter container
# ============================================================================

@dataclass(frozen=True)
class TransportParameters:
    """All inputs needed to evolve one ℓ=2 multipole.

    Attributes
    ----------
    species : TransportSpecies
        Determines which damping-rate helper applies by default.
    damping_rate : float
        Γ^(s) in time units matching the integration dt.
    shear : AxisymmetricSTFTensor
        Background σ_ab. Constant across the Euler step (frozen-background
        approximation valid for timescales short compared to the shear
        evolution).
    shear_coefficient : float
        Σ^(s)_2. Defaults to the species value if a factory is used.
    """
    species: TransportSpecies
    damping_rate: float
    shear: AxisymmetricSTFTensor
    shear_coefficient: float

    def __post_init__(self) -> None:
        if self.damping_rate < 0:
            raise ValueError(
                f"damping_rate must be non-negative, got {self.damping_rate}"
            )
        if self.shear_coefficient < 0:
            raise ValueError(
                f"shear_coefficient must be non-negative, "
                f"got {self.shear_coefficient}"
            )


def make_photon_parameters(
    n_e_sigmaT: float,
    shear: AxisymmetricSTFTensor,
    decision: CanonicalDecision,
) -> TransportParameters:
    """Factory: photon parameters with default Σ^(γ)_2."""
    gamma = photon_damping_rate(n_e_sigmaT, decision)
    return TransportParameters(
        species=TransportSpecies.PHOTON,
        damping_rate=gamma,
        shear=shear,
        shear_coefficient=SIGMA_2_PHOTON_BE,
    )


def make_neutrino_parameters(
    hubble_rate: float,
    shear: AxisymmetricSTFTensor,
    decision: CanonicalDecision,
) -> TransportParameters:
    """Factory: neutrino parameters with default Σ^(ν)_2."""
    gamma = neutrino_damping_rate(hubble_rate, decision)
    return TransportParameters(
        species=TransportSpecies.NEUTRINO,
        damping_rate=gamma,
        shear=shear,
        shear_coefficient=SIGMA_2_NEUTRINO_FD,
    )


# ============================================================================
# Section 4 - Euler step
# ============================================================================

def _euler_step_unchecked(
    theta: AxisymmetricSTFTensor,
    params: TransportParameters,
    dt: float,
) -> AxisymmetricSTFTensor:
    """Private Euler step without gating — internal use only."""
    if theta.axis != params.shear.axis:
        raise ValueError(
            f"theta axis {theta.axis} does not match "
            f"shear axis {params.shear.axis}"
        )
    dot_amp = (
        -params.damping_rate * theta.amplitude
        + params.shear_coefficient * params.shear.amplitude
    )
    new_amp = theta.amplitude + dt * dot_amp
    return AxisymmetricSTFTensor(amplitude=new_amp, axis=theta.axis)


def euler_step(
    theta: AxisymmetricSTFTensor,
    params: TransportParameters,
    dt: float,
    decision: CanonicalDecision,
) -> AxisymmetricSTFTensor:
    """One explicit Euler step of the ℓ=2 transport equation.

        Θ^(n+1) = Θ^(n) + dt × ( -Γ Θ^(n) + Σ_2 σ )

    Parameters
    ----------
    theta : AxisymmetricSTFTensor
        Current Θ^(s)_ab.
    params : TransportParameters
        Species, Γ, Σ_2, σ.
    dt : float
        Time step. Must be positive. Stability requires dt < 2/Γ for the
        damping part; the driven amplitude is determined by Σ_2 σ / Γ
        independent of dt.
    decision : CanonicalDecision
        Runtime gate.

    Returns
    -------
    AxisymmetricSTFTensor
        Θ^(s)_ab at the next time step.
    """
    require_allow_reduction(decision, context="euler_step")
    if dt <= 0:
        raise ValueError(f"dt must be positive, got {dt}")
    return _euler_step_unchecked(theta, params, dt)


# ============================================================================
# Section 5 - Analytic steady state
# ============================================================================

def compute_steady_state(
    params: TransportParameters,
    decision: CanonicalDecision,
) -> AxisymmetricSTFTensor:
    """Analytic steady-state Θ_∞ = Σ_2 σ / Γ.

    Valid when σ is time-independent. For photons this reproduces D3's
    `compute_quasi_static_theta` exactly (setting Γ = τ̇, Σ_2 = Σ^(γ)_2).
    For neutrinos it gives the free-streaming quasi-steady amplitude
    Θ^(ν) ~ (Σ^(ν)_2 / H) σ that drives the N_2/F_2 ≈ 28 result at
    recombination (ch05 §nu-dominance).
    """
    require_allow_reduction(decision, context="compute_steady_state")
    if params.damping_rate <= 0:
        raise ValueError(
            f"damping_rate must be positive for steady-state, "
            f"got {params.damping_rate}"
        )
    amp_ss = (
        params.shear_coefficient * params.shear.amplitude
        / params.damping_rate
    )
    return AxisymmetricSTFTensor(amplitude=amp_ss, axis=params.shear.axis)


# ============================================================================
# Section 6 - Integration to steady state
# ============================================================================

@dataclass(frozen=True)
class IntegrationResult:
    """Outcome of `integrate_to_steady_state`.

    Attributes
    ----------
    final_state : AxisymmetricSTFTensor
        Last Θ^(s)_ab reached.
    steps_taken : int
        Number of Euler steps actually executed.
    converged : bool
        True iff the relative-change criterion was met before max_steps.
    final_residual : float
        |Θ^(n+1) - Θ^(n)| / max(|Θ^(n+1)|, floor) from the last step.
    steady_state_target : AxisymmetricSTFTensor
        Analytic Θ_∞ for reference.
    """
    final_state: AxisymmetricSTFTensor
    steps_taken: int
    converged: bool
    final_residual: float
    steady_state_target: AxisymmetricSTFTensor


def integrate_to_steady_state(
    initial: AxisymmetricSTFTensor,
    params: TransportParameters,
    dt: float,
    decision: CanonicalDecision,
    max_steps: int = 1000,
    tolerance: float = 1e-6,
) -> IntegrationResult:
    """Step until relative change < tolerance or max_steps reached.

    Convergence criterion (step-to-step relative change):

        |Θ^(n+1) - Θ^(n)| / max(|Θ^(n+1)|, 10⁻³⁰) < tolerance

    The 10⁻³⁰ floor avoids divide-by-zero when the trajectory passes through
    amplitude zero. On convergence the final state should be close to the
    analytic steady state Σ_2 σ / Γ.
    """
    require_allow_reduction(decision, context="integrate_to_steady_state")
    if dt <= 0:
        raise ValueError(f"dt must be positive, got {dt}")
    if max_steps < 1:
        raise ValueError(f"max_steps must be ≥ 1, got {max_steps}")
    if tolerance <= 0:
        raise ValueError(f"tolerance must be positive, got {tolerance}")
    if initial.axis != params.shear.axis:
        raise ValueError(
            f"initial axis {initial.axis} does not match "
            f"shear axis {params.shear.axis}"
        )

    # Analytic target for the report
    if params.damping_rate > 0:
        target_amp = (
            params.shear_coefficient * params.shear.amplitude
            / params.damping_rate
        )
    else:
        target_amp = float("inf")  # no damping → no steady state
    target = AxisymmetricSTFTensor(amplitude=target_amp, axis=initial.axis)

    state = initial
    residual = float("inf")
    converged = False
    steps_taken = 0

    for step in range(max_steps):
        new_state = _euler_step_unchecked(state, params, dt)
        denom = max(abs(new_state.amplitude), 1e-30)
        residual = abs(new_state.amplitude - state.amplitude) / denom
        state = new_state
        steps_taken = step + 1
        if residual < tolerance:
            converged = True
            break

    return IntegrationResult(
        final_state=state,
        steps_taken=steps_taken,
        converged=converged,
        final_residual=residual,
        steady_state_target=target,
    )


# ============================================================================
# Section 7 - Convenience diagnostics
# ============================================================================

def free_streaming_decay_factor(
    damping_rate: float,
    time: float,
) -> float:
    """exp(-Γ t) analytic decay factor for zero-source free streaming.

    If params.shear.amplitude = 0 (no source), the transport equation
    reduces to dΘ/dt = -Γ Θ with solution Θ(t) = Θ(0) exp(-Γt).
    """
    if damping_rate < 0 or time < 0:
        raise ValueError(
            f"damping_rate and time must be non-negative, "
            f"got damping_rate={damping_rate}, time={time}"
        )
    import math
    return math.exp(-damping_rate * time)
