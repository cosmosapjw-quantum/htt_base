"""
bass/transport/multipole_hierarchy.py  (Week 5-A, Day 1)
==========================================================

Multi-ℓ PSTF Boltzmann hierarchy with streaming coupling, damping, and
shear source — the multi-multipole extension of the W4D4 single-ℓ
`ray_transport.py`.

Scope
-----
Solves the axisymmetric ℓ=0..L_max hierarchy:

    d/dt Θ_ℓ = (k_eff / (2ℓ+1)) × [ℓ Θ_{ℓ-1} − (ℓ+1) Θ_{ℓ+1}]
                − Γ_ℓ Θ_ℓ
                + Σ_2 σ δ_{ℓ,2}                                            (*)

where:
- Θ_ℓ is the axisymmetric Teff scalar-amplitude multipole at level ℓ
- k_eff = k/S is the effective wavenumber (inverse length scale)
- Γ_ℓ is the species-dependent damping (uniform across ℓ for this skeleton)
- Σ_2 σ is the shear injection at ℓ=2 (from W4D4)
- Absorbing boundary: Θ_{L_max+1} ≡ 0, Θ_{-1} ≡ 0

This skeleton captures the three core physics mechanisms:
1. Free-streaming cascade: shear injection at ℓ=2 leaks to higher ℓ
2. Damping: Thomson (photon) vs Hubble (neutrino) controls the amplitude
3. PSTF coupling coefficients: ℓ/(2ℓ+1), (ℓ+1)/(2ℓ+1)

W5-A covers up to L_max ~ 10–20; higher L_max is a numerical-efficiency
question handled by implicit integrators in W5-B.

Relation to W4D4 `ray_transport.py`
------------------------------------
When k_eff = 0 and L_max = 2, the hierarchy decouples: Θ_0 and Θ_1 evolve
trivially (no source, pure damping), and Θ_2 satisfies the single-ℓ D4
equation Θ̇_2 = −Γ Θ_2 + Σ_2 σ. Bit-exact recovery is verified in the
test suite (`TestD4Consistency`).

References
----------
- Challinor & Lasenby 1999, Eq. 44 (Fourier-space PSTF hierarchy)
- ch05 §pstf-hierarchy (MDE general form)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from bass.collision.thomson_tensor import (
    AxisymmetricSTFTensor, SymmetryAxis,
    SIGMA_2_PHOTON_BE,
)
from bass.transport.ray_transport import (
    TransportSpecies,
    SIGMA_2_NEUTRINO_FD,
    photon_damping_rate,
    neutrino_damping_rate,
)
from bass.runtime.canonical_decision import (
    CanonicalDecision,
    require_allow_reduction,
)


# ============================================================================
# Section 1 - MultipoleState container
# ============================================================================

@dataclass(frozen=True)
class MultipoleState:
    """Axisymmetric multipole amplitude vector.

    Attributes
    ----------
    amplitudes : np.ndarray shape (L+1,)
        Θ_0, Θ_1, ..., Θ_L in scalar-amplitude form (rank-ℓ STF tensor
        amplitude on the common axis).
    axis : SymmetryAxis
        Shared symmetry axis of all multipoles.
    """
    amplitudes: np.ndarray
    axis: SymmetryAxis = SymmetryAxis.Z

    def __post_init__(self) -> None:
        if self.amplitudes.ndim != 1:
            raise ValueError(
                f"amplitudes must be 1D, got shape {self.amplitudes.shape}"
            )
        if self.amplitudes.size < 1:
            raise ValueError("amplitudes must be non-empty")

    @property
    def ell_max(self) -> int:
        return int(self.amplitudes.size) - 1

    @property
    def n_multipoles(self) -> int:
        return int(self.amplitudes.size)

    def ell(self, ell_index: int) -> float:
        """Scalar amplitude at level ell_index."""
        if ell_index < 0 or ell_index > self.ell_max:
            raise IndexError(
                f"ell_index {ell_index} out of [0, {self.ell_max}]"
            )
        return float(self.amplitudes[ell_index])

    def as_stf_at(self, ell_index: int) -> AxisymmetricSTFTensor:
        """Return the rank-2 STF tensor view at ℓ=ell_index.

        Only meaningful for ell_index = 2 (quadrupole) in the current
        axisymmetric skeleton. For general ℓ, the STF tensor form requires
        rank-ℓ construction, which is a W5+ extension.
        """
        if ell_index != 2:
            raise ValueError(
                f"as_stf_at currently supports only ell=2 (quadrupole), "
                f"got ell={ell_index}"
            )
        return AxisymmetricSTFTensor(
            amplitude=self.ell(ell_index), axis=self.axis,
        )


def zero_state(ell_max: int, axis: SymmetryAxis = SymmetryAxis.Z) -> MultipoleState:
    """Factory: zero MultipoleState with the given ell_max."""
    if ell_max < 0:
        raise ValueError(f"ell_max must be ≥ 0, got {ell_max}")
    return MultipoleState(
        amplitudes=np.zeros(ell_max + 1), axis=axis,
    )


# ============================================================================
# Section 2 - Hierarchy parameter container
# ============================================================================

@dataclass(frozen=True)
class HierarchyParameters:
    """Inputs needed to evolve the full hierarchy.

    Attributes
    ----------
    species : TransportSpecies
        PHOTON / NEUTRINO (used to dispatch default Σ_2).
    damping_rate : float
        Γ (scalar, uniform across ℓ in this skeleton).
    shear : AxisymmetricSTFTensor
        Background σ_ab (only amplitude matters for axisymmetric).
    shear_coefficient : float
        Σ_2 (species-dependent; default via species).
    k_eff : float
        Effective wavenumber k/S in the Fourier-space hierarchy.
        k_eff ≥ 0; k_eff = 0 reduces to uncoupled single-ℓ system
        (W4D4 case when L_max = 2).
    ell_max : int
        Highest multipole retained. Absorbing boundary at ell_max+1.
    """
    species: TransportSpecies
    damping_rate: float
    shear: AxisymmetricSTFTensor
    shear_coefficient: float
    k_eff: float
    ell_max: int

    def __post_init__(self) -> None:
        if self.damping_rate < 0:
            raise ValueError(f"damping_rate must be ≥ 0, got {self.damping_rate}")
        if self.shear_coefficient < 0:
            raise ValueError(
                f"shear_coefficient must be ≥ 0, got {self.shear_coefficient}"
            )
        if self.k_eff < 0:
            raise ValueError(f"k_eff must be ≥ 0, got {self.k_eff}")
        if self.ell_max < 0:
            raise ValueError(f"ell_max must be ≥ 0, got {self.ell_max}")


def make_photon_hierarchy_parameters(
    n_e_sigmaT: float,
    shear: AxisymmetricSTFTensor,
    k_eff: float,
    ell_max: int,
    decision: CanonicalDecision,
) -> HierarchyParameters:
    """Factory: photon hierarchy parameters with default Σ^(γ)_2."""
    gamma = photon_damping_rate(n_e_sigmaT, decision)
    return HierarchyParameters(
        species=TransportSpecies.PHOTON,
        damping_rate=gamma,
        shear=shear,
        shear_coefficient=SIGMA_2_PHOTON_BE,
        k_eff=k_eff,
        ell_max=ell_max,
    )


def make_neutrino_hierarchy_parameters(
    hubble_rate: float,
    shear: AxisymmetricSTFTensor,
    k_eff: float,
    ell_max: int,
    decision: CanonicalDecision,
) -> HierarchyParameters:
    """Factory: neutrino hierarchy parameters with default Σ^(ν)_2."""
    gamma = neutrino_damping_rate(hubble_rate, decision)
    return HierarchyParameters(
        species=TransportSpecies.NEUTRINO,
        damping_rate=gamma,
        shear=shear,
        shear_coefficient=SIGMA_2_NEUTRINO_FD,
        k_eff=k_eff,
        ell_max=ell_max,
    )


# ============================================================================
# Section 3 - Streaming coupling matrix
# ============================================================================

def build_streaming_matrix(k_eff: float, ell_max: int) -> np.ndarray:
    """PSTF free-streaming coupling matrix M of shape (L+1, L+1).

    Entries (axisymmetric, flat Bianchi I, Fourier mode k_eff):

        M[ℓ, ℓ-1] = + k_eff × ℓ / (2ℓ+1)          (coupling from below)
        M[ℓ, ℓ+1] = − k_eff × (ℓ+1) / (2ℓ+1)      (coupling from above)

    All other entries are zero. Diagonal is zero (damping is separate).

    Absorbing boundary: the column ell_max+1 is not present, so the
    coupling at ℓ = ell_max to "above" is truncated, corresponding to
    Θ_{ell_max+1} ≡ 0.
    """
    if ell_max < 0:
        raise ValueError(f"ell_max must be ≥ 0, got {ell_max}")
    if k_eff < 0:
        raise ValueError(f"k_eff must be ≥ 0, got {k_eff}")

    M = np.zeros((ell_max + 1, ell_max + 1))
    for ell in range(ell_max + 1):
        if ell - 1 >= 0:
            M[ell, ell - 1] = k_eff * ell / (2.0 * ell + 1.0)
        if ell + 1 <= ell_max:
            M[ell, ell + 1] = -k_eff * (ell + 1.0) / (2.0 * ell + 1.0)
    return M


def build_source_vector(params: HierarchyParameters) -> np.ndarray:
    """Source vector b[ℓ] = Σ_2 σ δ_{ℓ,2}.

    Shear enters only at ℓ=2 (ch05 Eq. MDE-general). If ell_max < 2 the
    vector is all zeros (no shear source).
    """
    b = np.zeros(params.ell_max + 1)
    if params.ell_max >= 2:
        b[2] = params.shear_coefficient * params.shear.amplitude
    return b


# ============================================================================
# Section 4 - Euler step and analytic steady state
# ============================================================================

def _euler_step_unchecked(
    state: MultipoleState,
    params: HierarchyParameters,
    dt: float,
) -> MultipoleState:
    """Private Euler step. No gate, no shape checks."""
    M = build_streaming_matrix(params.k_eff, params.ell_max)
    b = build_source_vector(params)
    dot = M @ state.amplitudes - params.damping_rate * state.amplitudes + b
    new_amps = state.amplitudes + dt * dot
    return MultipoleState(amplitudes=new_amps, axis=state.axis)


def euler_step_hierarchy(
    state: MultipoleState,
    params: HierarchyParameters,
    dt: float,
    decision: CanonicalDecision,
) -> MultipoleState:
    """One explicit Euler step of the multi-ℓ hierarchy (*).

    CFL-style stability note: the streaming eigenvalue spectrum scales as
    k_eff, so stability requires dt × max(k_eff, Γ) ≲ 2. Not enforced at
    the module boundary; responsibility of caller. Implicit integrators
    (W5-B) remove this restriction.

    Raises
    ------
    CanonicalBlockError if decision blocks reduction.
    ValueError if dt ≤ 0 or shape mismatch.
    """
    require_allow_reduction(decision, context="euler_step_hierarchy")
    if dt <= 0:
        raise ValueError(f"dt must be positive, got {dt}")
    if state.ell_max != params.ell_max:
        raise ValueError(
            f"state.ell_max ({state.ell_max}) != params.ell_max "
            f"({params.ell_max})"
        )
    if state.axis != params.shear.axis:
        raise ValueError(
            f"state axis {state.axis} != shear axis {params.shear.axis}"
        )
    return _euler_step_unchecked(state, params, dt)


def compute_steady_state_hierarchy(
    params: HierarchyParameters,
    decision: CanonicalDecision,
) -> MultipoleState:
    """Analytic steady-state solution: (Γ I - M) Θ_∞ = b.

    Solves the linear system for the stationary point of (*). Exists
    uniquely when (Γ I - M) is invertible. With Γ > 0 and k_eff ≥ 0, the
    diagonal dominance of Γ I typically ensures invertibility for small
    k_eff/Γ; at large k_eff the system can become stiff (condition
    number grows).
    """
    require_allow_reduction(
        decision, context="compute_steady_state_hierarchy",
    )
    if params.damping_rate <= 0 and params.k_eff == 0:
        raise ValueError(
            "Γ = 0 and k_eff = 0 gives trivial null dynamics — no "
            "unique steady state"
        )

    M = build_streaming_matrix(params.k_eff, params.ell_max)
    b = build_source_vector(params)
    I = np.eye(params.ell_max + 1)
    A = params.damping_rate * I - M
    try:
        Theta_inf = np.linalg.solve(A, b)
    except np.linalg.LinAlgError as e:
        raise ValueError(f"(Γ I - M) singular: {e}")
    return MultipoleState(amplitudes=Theta_inf, axis=params.shear.axis)


# ============================================================================
# Section 5 - Integration to steady state
# ============================================================================

@dataclass(frozen=True)
class HierarchyIntegrationResult:
    """Outcome of `integrate_hierarchy_to_steady_state`.

    Attributes
    ----------
    final_state : MultipoleState
    steps_taken : int
    converged : bool
    final_residual : float
        ||Θ^(n+1) - Θ^(n)|| / max(||Θ^(n+1)||, floor) from the last step.
    steady_state_target : MultipoleState
        Analytic linsolve reference.
    """
    final_state: MultipoleState
    steps_taken: int
    converged: bool
    final_residual: float
    steady_state_target: MultipoleState


def integrate_hierarchy_to_steady_state(
    initial: MultipoleState,
    params: HierarchyParameters,
    dt: float,
    decision: CanonicalDecision,
    max_steps: int = 5000,
    tolerance: float = 1e-6,
) -> HierarchyIntegrationResult:
    """Explicit Euler driver to steady state.

    Convergence: L2-norm relative change between successive steps < tol.
    """
    require_allow_reduction(
        decision, context="integrate_hierarchy_to_steady_state",
    )
    if dt <= 0:
        raise ValueError(f"dt must be positive, got {dt}")
    if max_steps < 1:
        raise ValueError(f"max_steps must be ≥ 1, got {max_steps}")
    if tolerance <= 0:
        raise ValueError(f"tolerance must be positive, got {tolerance}")
    if initial.ell_max != params.ell_max:
        raise ValueError(
            f"initial ell_max {initial.ell_max} != params ell_max "
            f"{params.ell_max}"
        )

    # Analytic target (use gated entry for safety — cheap)
    if params.damping_rate > 0 or params.k_eff > 0:
        target = compute_steady_state_hierarchy(params, decision)
    else:
        target = zero_state(params.ell_max, initial.axis)

    state = initial
    residual = float("inf")
    converged = False
    steps_taken = 0

    for step in range(max_steps):
        new_state = _euler_step_unchecked(state, params, dt)
        delta = new_state.amplitudes - state.amplitudes
        denom = max(float(np.linalg.norm(new_state.amplitudes)), 1e-30)
        residual = float(np.linalg.norm(delta)) / denom
        state = new_state
        steps_taken = step + 1
        if residual < tolerance:
            converged = True
            break

    return HierarchyIntegrationResult(
        final_state=state,
        steps_taken=steps_taken,
        converged=converged,
        final_residual=residual,
        steady_state_target=target,
    )


# ============================================================================
# Section 6 - Diagnostics
# ============================================================================

def cfl_max_dt(params: HierarchyParameters) -> float:
    """Approximate explicit-Euler stability bound dt_max = 2 / λ_max.

    λ_max of (Γ I - M) is bounded above by Γ + k_eff (from the max-row-sum
    norm). Returns 2 / (Γ + k_eff) as a conservative estimate.

    Use-case: choose dt well below this to keep explicit Euler stable.
    """
    denom = params.damping_rate + params.k_eff
    if denom <= 0:
        return float("inf")
    return 2.0 / denom
