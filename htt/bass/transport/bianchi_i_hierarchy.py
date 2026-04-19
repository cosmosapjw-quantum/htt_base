"""
bass/transport/bianchi_i_hierarchy.py  (Week 5-C)
====================================================

Full Bianchi I anisotropic hierarchy with m ∈ {0, ±2} azimuthal channels.

Motivation
----------
W5-A/W5-B restricted to axisymmetric shear: a single amplitude along one
symmetry axis. Full Bianchi I has a diagonal shear tensor with THREE
eigenvalues and the trace-free constraint σ_xx + σ_yy + σ_zz = 0, leaving
TWO independent DOF. In the principal-axis frame, these excite:

    m = 0   channel  ←  σ_zz  (and − (σ_xx+σ_yy)/2)
    m = ±2  channel  ←  (σ_xx − σ_yy) / 2

The m = ±1 channels are NOT excited when σ is diagonal in the principal
frame — they need off-diagonal σ_xy, σ_xz, σ_yz components, which are
beyond the Bianchi I scope.

Structure of each m-channel
---------------------------
Each m value produces an independent linear hierarchy with state
    Θ_{|m|}^m,  Θ_{|m|+1}^m,  …,  Θ_{L_max}^m
(length = L_max + 1 − |m|). Streaming couples neighbouring ℓ within the
same m:

    dΘ_ℓ^m/dt = −Γ Θ_ℓ^m + k_eff[α_ℓ^m Θ_{ℓ-1}^m − β_ℓ^m Θ_{ℓ+1}^m]
                + Σ_2 s^{(m)} δ_{ℓ,max(2,|m|)}

with the m-dependent PSTF coupling coefficients

    α_ℓ^m = √(ℓ² − m²) / (2ℓ+1),   β_ℓ^m = √((ℓ+1)² − m²) / (2ℓ+1)

At m = 0: α_ℓ^0 = ℓ/(2ℓ+1), β_ℓ^0 = (ℓ+1)/(2ℓ+1) — recovers W5-A exactly.

Reduction to axisymmetric
-------------------------
When σ_xx = σ_yy (axisymmetric), the s_plus amplitude vanishes, so the
m=±2 channels carry no source and evolve trivially to zero. The m=0
channel alone carries all the physics, and its hierarchy is bit-exact
identical to W5-A. This is verified in `TestAxisymmetricReduction`.

No gating on pure-arithmetic helpers
------------------------------------
`DiagonalShearTensor`, `decompose_shear_to_m_channels`, streaming and
source matrix builders are pure math — no gating. The five public
steady-state entries (one per m-channel + one aggregated + two factories)
gate via the W3 `CanonicalDecision` contract, reusing W5-A/W5-B helpers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

import numpy as np

from bass.transport.ray_transport import (
    TransportSpecies, SIGMA_2_NEUTRINO_FD,
    photon_damping_rate, neutrino_damping_rate,
)
from bass.collision.thomson_tensor import SIGMA_2_PHOTON_BE
from bass.runtime.canonical_decision import (
    CanonicalDecision, require_allow_reduction,
)


# ============================================================================
# Section 1 - DiagonalShearTensor
# ============================================================================

@dataclass(frozen=True)
class DiagonalShearTensor:
    """Diagonal shear σ_ab = diag(σ_xx, σ_yy, σ_zz) with trace-free enforced.

    Attributes
    ----------
    sigma_xx, sigma_yy, sigma_zz : float
        Eigenvalues. Constraint: σ_xx + σ_yy + σ_zz = 0 to within `trace_atol`.
    trace_atol : float
        Absolute tolerance on the trace-free check.

    Convenience properties
    ----------------------
    s_0       : σ_zz (the "axial" DOF)
    s_plus    : (σ_xx - σ_yy) / 2 (the "transverse anisotropy" DOF)
    is_axisymmetric_xy : True iff |s_plus| < trace_atol (σ_xx ≃ σ_yy)
    """
    sigma_xx: float
    sigma_yy: float
    sigma_zz: float
    trace_atol: float = 1e-12

    def __post_init__(self) -> None:
        trace = self.sigma_xx + self.sigma_yy + self.sigma_zz
        if abs(trace) > self.trace_atol:
            raise ValueError(
                f"shear tensor must be trace-free, "
                f"got σ_xx+σ_yy+σ_zz = {trace} (atol={self.trace_atol})"
            )

    @property
    def s_0(self) -> float:
        """Axial DOF: σ_zz itself."""
        return self.sigma_zz

    @property
    def s_plus(self) -> float:
        """Transverse-anisotropy DOF: (σ_xx − σ_yy)/2."""
        return 0.5 * (self.sigma_xx - self.sigma_yy)

    @property
    def is_axisymmetric_xy(self) -> bool:
        """True iff σ_xx = σ_yy to within trace_atol (⇔ m=±2 channel inert)."""
        return abs(self.s_plus) < self.trace_atol

    def to_diagonal_array(self) -> np.ndarray:
        """Return (3,) array [σ_xx, σ_yy, σ_zz]."""
        return np.array([self.sigma_xx, self.sigma_yy, self.sigma_zz])


def make_axisymmetric_shear(
    s_zz: float, trace_atol: float = 1e-12,
) -> DiagonalShearTensor:
    """Factory: σ_zz = s_zz, σ_xx = σ_yy = -s_zz/2 (axisymmetric about z)."""
    return DiagonalShearTensor(
        sigma_xx=-0.5 * s_zz,
        sigma_yy=-0.5 * s_zz,
        sigma_zz=s_zz,
        trace_atol=trace_atol,
    )


# ============================================================================
# Section 2 - m-channel decomposition
# ============================================================================

@dataclass(frozen=True)
class MChannelAmplitudes:
    """Shear source amplitudes per m-channel (ℓ=2).

    Attributes
    ----------
    s_m0 : float
        Source strength in the m=0 channel (drives axial quadrupole).
    s_m2 : float
        Source strength in the m=±2 channels (drives transverse anisotropy).
        Shared magnitude for both m = +2 and m = −2 (real-valued decomp).
    """
    s_m0: float
    s_m2: float


def decompose_shear_to_m_channels(
    shear: DiagonalShearTensor,
) -> MChannelAmplitudes:
    """Decompose a diagonal shear into (m=0, m=±2) amplitude components.

    Convention: we parametrize with the two independent DOF directly,
        s_m0 = σ_zz      (the z-axis eigenvalue)
        s_m2 = s_plus    (the xy-anisotropy DOF)

    This preserves the physical magnitudes without embedding Wigner
    normalization factors; normalization absorption is a W6+ concern
    once the full Wigner-3j coupling to ℓ ≥ 3 is implemented.
    """
    return MChannelAmplitudes(s_m0=shear.s_0, s_m2=shear.s_plus)


# ============================================================================
# Section 3 - m-channel streaming matrix
# ============================================================================

def pstf_coupling_coeffs(ell: int, m: int) -> tuple:
    """(α_ℓ^m, β_ℓ^m) = (√(ℓ²-m²)/(2ℓ+1), √((ℓ+1)²-m²)/(2ℓ+1)).

    α is the coupling from ℓ to ℓ-1, β is from ℓ to ℓ+1.
    Returns (0, 0) for invalid (ℓ < |m|).
    """
    if ell < abs(m):
        return 0.0, 0.0
    m_sq = m * m
    alpha = np.sqrt(max(ell * ell - m_sq, 0.0)) / (2.0 * ell + 1.0)
    beta = np.sqrt((ell + 1.0) ** 2 - m_sq) / (2.0 * ell + 1.0)
    return float(alpha), float(beta)


def build_m_streaming_matrix(
    k_eff: float, ell_max: int, m: int,
) -> np.ndarray:
    """Streaming coupling matrix for a single m-channel.

    Shape (ell_max + 1 - |m|, same). The row/column index i corresponds
    to ell = |m| + i. Absorbing boundary at ell_max (β coupling to
    ell_max+1 dropped).

    Entries:
        M[i, i-1] = + k_eff × α_{|m|+i}^m
        M[i, i+1] = − k_eff × β_{|m|+i}^m
        all other entries zero (diagonal handled by damping, not M).
    """
    if ell_max < 0:
        raise ValueError(f"ell_max must be ≥ 0, got {ell_max}")
    if k_eff < 0:
        raise ValueError(f"k_eff must be ≥ 0, got {k_eff}")

    abs_m = abs(m)
    if abs_m > ell_max:
        raise ValueError(
            f"|m| = {abs_m} > ell_max = {ell_max}; no multipoles"
        )

    dim = ell_max + 1 - abs_m
    M = np.zeros((dim, dim))
    for i in range(dim):
        ell = abs_m + i
        alpha, beta = pstf_coupling_coeffs(ell, m)
        if i - 1 >= 0:
            M[i, i - 1] = k_eff * alpha
        if i + 1 < dim:
            M[i, i + 1] = -k_eff * beta
    return M


def build_m_source_vector(
    s_amp: float, ell_max: int, m: int, shear_coefficient: float,
) -> np.ndarray:
    """Source vector b[i] with δ at ell = max(2, |m|) for this m channel.

    The ℓ=2 quadrupole is the only allowed shear source entry. For m=0
    and m=±2 the source lands at ℓ=2 regardless (|m| ≤ 2). For |m| > 2
    (not excited by diagonal shear — reserved for W6+ off-diagonal
    extensions), the source amplitude is zero.
    """
    abs_m = abs(m)
    dim = ell_max + 1 - abs_m
    b = np.zeros(dim)
    if abs_m <= 2 and ell_max >= 2:
        source_ell = 2
        i_source = source_ell - abs_m  # index of ell=2 within this m-channel
        b[i_source] = shear_coefficient * s_amp
    return b


# ============================================================================
# Section 4 - m-channel state container
# ============================================================================

@dataclass(frozen=True)
class MChannelState:
    """Amplitudes in one m-channel: Θ_{|m|}^m, Θ_{|m|+1}^m, …, Θ_{L_max}^m."""
    m: int
    amplitudes: np.ndarray   # shape (L_max + 1 − |m|,)

    def __post_init__(self) -> None:
        if self.amplitudes.ndim != 1:
            raise ValueError(
                f"amplitudes must be 1D, got shape {self.amplitudes.shape}"
            )
        if self.amplitudes.size < 1:
            raise ValueError("amplitudes must be non-empty")

    @property
    def ell_max(self) -> int:
        return int(self.amplitudes.size) - 1 + abs(self.m)

    @property
    def ell_min(self) -> int:
        return abs(self.m)

    def ell(self, ell_val: int) -> float:
        """Amplitude at multipole level ell_val."""
        if ell_val < self.ell_min or ell_val > self.ell_max:
            raise IndexError(
                f"ell={ell_val} outside [{self.ell_min}, {self.ell_max}] "
                f"for m={self.m}"
            )
        return float(self.amplitudes[ell_val - self.ell_min])


# ============================================================================
# Section 5 - Bianchi I hierarchy parameters
# ============================================================================

@dataclass(frozen=True)
class BianchiHierarchyParameters:
    """Inputs for the full Bianchi I m={0, ±2} hierarchy.

    Attributes
    ----------
    species : TransportSpecies
    damping_rate : float        Γ (uniform across ℓ and m)
    shear : DiagonalShearTensor Trace-free eigenvalue triplet
    shear_coefficient : float   Σ_2 (species-dependent)
    k_eff : float               k/S in the hierarchy
    ell_max : int               Highest multipole retained (shared across m)
    """
    species: TransportSpecies
    damping_rate: float
    shear: DiagonalShearTensor
    shear_coefficient: float
    k_eff: float
    ell_max: int

    def __post_init__(self) -> None:
        if self.damping_rate < 0:
            raise ValueError(
                f"damping_rate must be ≥ 0, got {self.damping_rate}"
            )
        if self.shear_coefficient < 0:
            raise ValueError(
                f"shear_coefficient must be ≥ 0, "
                f"got {self.shear_coefficient}"
            )
        if self.k_eff < 0:
            raise ValueError(f"k_eff must be ≥ 0, got {self.k_eff}")
        if self.ell_max < 2:
            raise ValueError(
                f"ell_max must be ≥ 2 (for m=±2 channels), got {self.ell_max}"
            )


def make_photon_bianchi_parameters(
    n_e_sigmaT: float,
    shear: DiagonalShearTensor,
    k_eff: float,
    ell_max: int,
    decision: CanonicalDecision,
) -> BianchiHierarchyParameters:
    """Factory: photon Bianchi I parameters with default Σ^(γ)_2."""
    gamma = photon_damping_rate(n_e_sigmaT, decision)
    return BianchiHierarchyParameters(
        species=TransportSpecies.PHOTON,
        damping_rate=gamma,
        shear=shear,
        shear_coefficient=SIGMA_2_PHOTON_BE,
        k_eff=k_eff,
        ell_max=ell_max,
    )


def make_neutrino_bianchi_parameters(
    hubble_rate: float,
    shear: DiagonalShearTensor,
    k_eff: float,
    ell_max: int,
    decision: CanonicalDecision,
) -> BianchiHierarchyParameters:
    """Factory: neutrino Bianchi I parameters with default Σ^(ν)_2."""
    gamma = neutrino_damping_rate(hubble_rate, decision)
    return BianchiHierarchyParameters(
        species=TransportSpecies.NEUTRINO,
        damping_rate=gamma,
        shear=shear,
        shear_coefficient=SIGMA_2_NEUTRINO_FD,
        k_eff=k_eff,
        ell_max=ell_max,
    )


# ============================================================================
# Section 6 - Per-channel steady-state solver
# ============================================================================

def _m_channel_system(
    params: BianchiHierarchyParameters, m: int, s_amp: float,
) -> tuple:
    """Build (A_m, b_m) = (M_m - Γ I, source_m) for one m-channel."""
    M = build_m_streaming_matrix(params.k_eff, params.ell_max, m)
    b = build_m_source_vector(
        s_amp, params.ell_max, m, params.shear_coefficient,
    )
    dim = M.shape[0]
    A = M - params.damping_rate * np.eye(dim)
    return A, b


def compute_m_channel_steady_state(
    params: BianchiHierarchyParameters,
    m: int,
    decision: CanonicalDecision,
) -> MChannelState:
    """Analytic steady state for one m-channel: (Γ I − M_m) Θ_m = b_m.

    Reads the shear amplitude appropriate for m via
    `decompose_shear_to_m_channels`. For |m| not in {0, 2} the source
    is zero, so Θ = 0 trivially — useful for consistency checks.
    """
    require_allow_reduction(
        decision, context="compute_m_channel_steady_state",
    )
    amps = decompose_shear_to_m_channels(params.shear)
    if m == 0:
        s = amps.s_m0
    elif abs(m) == 2:
        s = amps.s_m2
    else:
        s = 0.0

    A, b = _m_channel_system(params, m, s)
    if params.damping_rate <= 0 and params.k_eff == 0:
        raise ValueError(
            "Γ = 0 and k_eff = 0 gives trivial null dynamics — no "
            "unique steady state"
        )
    Theta = np.linalg.solve(-A, b)
    return MChannelState(m=m, amplitudes=Theta)


# ============================================================================
# Section 7 - Full Bianchi hierarchy result
# ============================================================================

@dataclass(frozen=True)
class BianchiHierarchyResult:
    """Steady-state Bianchi I result across m ∈ {0, +2, −2}.

    Attributes
    ----------
    channels : dict
        {m: MChannelState} with m ∈ {0, +2, -2}.
    shear : DiagonalShearTensor
        Input shear for provenance.

    Diagnostic properties
    ---------------------
    quadrupole_power : the sum over m of |Θ_2^m|² at ℓ=2
    """
    channels: Dict[int, MChannelState]
    shear: DiagonalShearTensor

    def ell_max(self) -> int:
        """Maximum ℓ across all channels."""
        if not self.channels:
            return 0
        return max(s.ell_max for s in self.channels.values())

    def theta_at(self, ell: int, m: int) -> float:
        """Return Θ_ℓ^m or 0 if (ℓ, m) is out of range."""
        if m not in self.channels:
            return 0.0
        ch = self.channels[m]
        if ell < ch.ell_min or ell > ch.ell_max:
            return 0.0
        return ch.ell(ell)

    def quadrupole_power(self) -> float:
        """Σ_m |Θ_2^m|² — the total quadrupole magnitude."""
        total = 0.0
        for m, ch in self.channels.items():
            if 2 >= ch.ell_min and 2 <= ch.ell_max:
                total += ch.ell(2) ** 2
        return float(total)


def compute_bianchi_i_steady_state(
    params: BianchiHierarchyParameters,
    decision: CanonicalDecision,
) -> BianchiHierarchyResult:
    """Full Bianchi I steady state across all excited m-channels.

    Solves 3 independent linear systems (m = 0, +2, −2) and aggregates
    the results. For diagonal shear in the principal frame, the m = ±2
    channels have equal-magnitude source amplitudes (s_plus is real),
    so `m=+2` and `m=-2` components are identical.
    """
    require_allow_reduction(
        decision, context="compute_bianchi_i_steady_state",
    )
    channels: Dict[int, MChannelState] = {}
    for m in (0, +2, -2):
        channels[m] = compute_m_channel_steady_state(params, m, decision)
    return BianchiHierarchyResult(channels=channels, shear=params.shear)
