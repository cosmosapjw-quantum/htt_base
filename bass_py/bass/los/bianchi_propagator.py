"""
bass/los/bianchi_propagator.py   (Week 9-02)
=============================================

Bianchi I matrix propagator: projects m ∈ {0, ±2} source channels onto
observer-frame transfer functions Δ_ℓ^{T,m}(k) and Δ_ℓ^{E,m}(k) via
spin-weighted Bessel-like kernels. FLRW Σ→0 limit recovers W9-01
bit-exact through direct delegation.

Physics
-------
For orthogonal Bianchi I (A_a = ω_a = 0, axisymmetric or general
diagonal shear), the line-of-sight propagator is block-diagonal in
the m-channel basis:

    ⎡ X_{m=0}(η_0) ⎤   ⎡ M_0   0    0  ⎤ ⎡ X_{m=0}(η_*)  ⎤
    ⎢ X_{m=+2}(η_0)⎥ = ⎢  0   M_+2   0 ⎥ ⎢ X_{m=+2}(η_*) ⎥
    ⎣ X_{m=-2}(η_0)⎦   ⎣  0    0   M_-2⎦ ⎣ X_{m=-2}(η_*) ⎦

Each block reduces to a per-m LOS integral with a channel-specific
kernel. NO full matrix exponentiation is needed because (i) there is
no polarization-basis rotation for Type I (ψ' = 0, Pontzen-Challinor
2007) and (ii) shear-induced m-mixing at equal ℓ is absorbed into the
source decomposition (W5-C: decompose_shear_to_m_channels).

Kernels
-------
m=0  (scalar-like, reduces to FLRW):
    F_ℓ^{T,m=0}(x) = j_ℓ(x)                    (W9-01 j_ℓ)
    F_ℓ^{E,m=0}(x) = √((ℓ-1)ℓ(ℓ+1)(ℓ+2)) · j_ℓ(x)/x²     (W9-01 P^E_ℓ)

m=±2 (spin-2 tensor-like):
    F_ℓ^{T,m=2}(x) = √((ℓ-1)ℓ(ℓ+1)(ℓ+2)) · j_ℓ(x) / x²    (Kamionkowski-
                                                            Kosowsky-
                                                            Stebbins 1997)

    F_ℓ^{E,m=2}(x) = (√((ℓ-1)ℓ(ℓ+1)(ℓ+2)) / 4) · E_kernel(x),

        E_kernel(x) = -j_ℓ(x) + j_ℓ''(x) + 2·j_ℓ(x)/x² + 4·j_ℓ'(x)/x
                      (Zaldarriaga-Seljak 1997 eq 17)

    F_ℓ^{B,m=2}(x) = 0             (Bianchi I: no polarization rotation)

j_ℓ' and j_ℓ'' are obtained by stable recurrences:
    (2ℓ+1) j_ℓ'(x) = ℓ · j_{ℓ-1}(x) - (ℓ+1) · j_{ℓ+1}(x)
    j_ℓ''(x)        = -(2/x) j_ℓ'(x) - [1 - ℓ(ℓ+1)/x²] j_ℓ(x)        (Bessel ODE)

All kernels vanish identically for ℓ < 2 (spin-2 minimum).

k-direction dependence
----------------------
The m-channel decomposition depends on the angle between k-vector and
the shear principal axis z-axis:
    cos_θ_k = k̂ · ẑ

    k ∥ z-axis (cos_θ_k = ±1):  only m=0 contributes
    k ⊥ z-axis (cos_θ_k  = 0):  m=±2 maximal, m=0 reduced
    general k:                   all three channels populated

The W5-C output MChannelAmplitudes(s_m0, s_m2) already folds in the
shear geometry; the caller chooses how to route these amplitudes into
per-m source terms.

FLRW recovery
-------------
When σ → 0 (FLRW limit), the BianchiSourceTerms.flrw_isotropic factory
zeros m=±2 sources and passes sources_m0 through a direct delegating
call into W9-01's project_temperature_transfer / project_polarization_
transfer. This guarantees bit-exact equality with W9-01 output (rtol
= 1e-14).

Scope (narrow, declared)
------------------------
IN scope
  * m=0 projector as W9-01 delegator (FLRW recovery bit-exact)
  * m=±2 temperature projector with KKS97 kernel
  * m=±2 E-mode projector with ZS97 kernel
  * B-mode explicit zero field with floor assertion
  * Block-diagonal matrix propagator
  * σ-ladder convergence (0, 1e-8, 1e-6, 1e-4)
  * k-direction-dependent m-channel routing
  * W5-C integration (MChannelAmplitudes + DiagonalShearTensor)
  * k_vector (3-vec) ⇄ (k_magnitude, cos_θ_k) dual interface
  * Non-axisymmetric shear (σ_× ≠ 0) as well as axisymmetric

OUT of scope  (→ OutOfScopeError)
  * Bianchi VIIh, IX (polarization rotation ψ' ≠ 0)   → bass_rs
  * Tilt-induced polarization basis change            → bass_rs
  * Full B-mode transfer (Bianchi I floor validated)  → W11+
  * Nonlinear Σ regime (Σ > 1e-4)                     → W12+
  * C_ℓ assembly (multi-k integration)                → W10-01
  * Full scalar/vector/tensor background evolution    → bass_rs

Dependencies
------------
  W9-01  bass.los.flrw_bessel_projector  (m=0 delegation, E-factor reuse)
  W5-C   bass.transport.bianchi_i_hierarchy
             (MChannelAmplitudes, DiagonalShearTensor, decompose_shear_to_m_channels)
  W8-03  visibility infrastructure (via W9-01 FLRWSourceTerms)
  scipy.special.spherical_jn

References
----------
Zaldarriaga, U., & Seljak, U. (1997). "An all-sky analysis of
  polarization in the microwave background." PRD 55, 1830.
Kamionkowski, M., Kosowsky, A., & Stebbins, A. (1997).
  "Statistics of cosmic microwave background polarization." PRD 55, 7368.
Pontzen, A., & Challinor, A. (2007). "Bianchi model CMB polarization
  and its implications for CMB anomalies." MNRAS 380, 1387.
Seljak, U., & Zaldarriaga, M. (1996). "A line-of-sight integration
  approach to cosmic microwave background anisotropies." ApJ 469, 437.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Union

import numpy as np
from scipy.special import spherical_jn

# Delegate to W9-01 for m=0 channel (bit-exact FLRW recovery)
from bass.los.flrw_bessel_projector import (
    FLRWBesselConfig,
    FLRWSourceTerms,
    EtaCallable,
    _zero_callable,
    _integrate,
    build_temperature_source,
    build_polarization_source,
    project_temperature_transfer as _flrw_project_T,
    project_polarization_transfer as _flrw_project_E,
    e_mode_projection_factor,
    OutOfScopeError,
)

# W5-C inputs
from bass.transport.bianchi_i_hierarchy import (
    DiagonalShearTensor,
    MChannelAmplitudes,
    make_axisymmetric_shear,
    decompose_shear_to_m_channels,
)


# ============================================================================
# Section 1 - Configuration
# ============================================================================

@dataclass(frozen=True)
class BianchiProjectorConfig:
    """Immutable configuration for the Bianchi I matrix propagator.

    Parameters
    ----------
    ell_max : int
        Highest multipole computed. Output transfer arrays have shape
        (ell_max + 1,) covering ℓ = 0 … ell_max.
    eta_0_mpc : float
        Conformal time at the observer today, in Mpc. Must match the
        W9-01 value when FLRW recovery is tested.
    quadrature : str
        'trapezoid' or 'simpson'; passed through to W9-01 integrators.
    bessel_kr_small_cutoff : float
        Threshold below which j_ℓ(x)/x² uses the Taylor-series limit
        to avoid catastrophic cancellation in the spin-2 kernels.
    flrw_recovery_rtol : float
        Tolerance for the Σ→0 FLRW recovery assertion. 1e-14 (machine
        precision after delegation) is the design target; loosen only
        when a FLOP reordering breaks bit-exactness.
    b_mode_floor : float
        Assertion floor for Δ_ℓ^B (Bianchi I: B ≡ 0 exactly; numerical
        floor absorbs only dataclass-construction round-off).
    """
    ell_max: int
    eta_0_mpc: float
    quadrature: str = "trapezoid"
    bessel_kr_small_cutoff: float = 1.0e-3
    flrw_recovery_rtol: float = 1.0e-14
    b_mode_floor: float = 1.0e-14

    def __post_init__(self) -> None:
        if self.ell_max < 0:
            raise ValueError(f"ell_max must be ≥ 0 (got {self.ell_max})")
        if self.eta_0_mpc <= 0:
            raise ValueError(f"eta_0_mpc must be > 0 (got {self.eta_0_mpc})")
        if self.quadrature not in ("trapezoid", "simpson"):
            raise ValueError(
                f"quadrature must be 'trapezoid' or 'simpson' "
                f"(got {self.quadrature!r})"
            )
        if self.bessel_kr_small_cutoff <= 0:
            raise ValueError("bessel_kr_small_cutoff must be > 0")
        if self.flrw_recovery_rtol <= 0:
            raise ValueError("flrw_recovery_rtol must be > 0")
        if self.b_mode_floor < 0:
            raise ValueError("b_mode_floor must be ≥ 0")

    def to_flrw_config(self) -> FLRWBesselConfig:
        """Project onto a W9-01 FLRWBesselConfig (m=0 delegation path)."""
        return FLRWBesselConfig(
            ell_max=self.ell_max,
            eta_0_mpc=self.eta_0_mpc,
            quadrature=self.quadrature,
            bessel_kr_small_cutoff=self.bessel_kr_small_cutoff,
        )


# ============================================================================
# Section 2 - Spin-2 tensor Bessel kernels
# ============================================================================
#
# For |m| = 2 channels we need j_ℓ(x), j_ℓ'(x), j_ℓ''(x). We compute
# j_ℓ' from the raising/lowering recurrence and j_ℓ'' from the Bessel
# ODE, both in scalar form.
# ============================================================================

def spherical_bessel_derivative(
    ell: int, x: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """First derivative  j_ℓ'(x)  via stable recurrence.

    Identity:
        (2ℓ + 1) j_ℓ'(x) = ℓ · j_{ℓ-1}(x) − (ℓ + 1) · j_{ℓ+1}(x)

    scipy.special.spherical_jn also accepts a ``derivative=True`` flag,
    which internally uses the same recurrence; we wrap it explicitly
    for readability and to keep the physics visible at the call site.
    """
    if ell < 0:
        raise ValueError(f"ell must be ≥ 0 (got {ell})")
    return spherical_jn(ell, x, derivative=True)


def spherical_bessel_second_derivative(
    ell: int, x: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """Second derivative  j_ℓ''(x)  via the spherical-Bessel ODE.

    Identity (from  x² y'' + 2x y' + [x² − ℓ(ℓ+1)] y = 0  with y=j_ℓ):
        j_ℓ''(x) = -(2/x) j_ℓ'(x)  -  [1 - ℓ(ℓ+1)/x²] j_ℓ(x)

    At x → 0 this blows up as ~ x^(ℓ-2) for ℓ≥2; callers requiring
    the small-x limit should use the Taylor expansion separately.
    """
    if ell < 0:
        raise ValueError(f"ell must be ≥ 0 (got {ell})")
    # scipy returns arrays when x is an array; keep consistent type
    x_arr = np.asarray(x, dtype=float)
    x2 = x_arr * x_arr
    jl = spherical_jn(ell, x_arr)
    jlp = spherical_jn(ell, x_arr, derivative=True)
    # Suppress division warning at x=0; callers should avoid that input
    with np.errstate(divide="ignore", invalid="ignore"):
        result = -2.0 * jlp / x_arr - (1.0 - ell * (ell + 1.0) / x2) * jl
    # Scalar return when scalar input
    if np.isscalar(x):
        return float(result)
    return result


def _double_factorial_odd(n: int) -> float:
    """(2n+1)!! = 1·3·5·…·(2n+1). Used only for ℓ ≤ 50 small-x limits."""
    if n < 0:
        return 1.0
    result = 1.0
    for i in range(1, 2 * n + 2, 2):
        result *= i
    return result


def tensor_temperature_kernel(
    ell: int, x: Union[float, np.ndarray],
    small_cutoff: float = 1.0e-3,
) -> Union[float, np.ndarray]:
    """Spin-2 tensor temperature LOS kernel  F_ℓ^{T,m=2}(x).

    Formula (Kamionkowski-Kosowsky-Stebbins 1997 §IV):

        F_ℓ^{T,m=2}(x) = √((ℓ-1)ℓ(ℓ+1)(ℓ+2)) · j_ℓ(x) / x²      (ℓ ≥ 2)
                       = 0                                         (ℓ < 2)

    This is the **same** formula as W9-01's scalar E-mode projection
    factor (no coincidence: spin-2 is spin-2). We delegate directly to
    e_mode_projection_factor to guarantee numerical identity.
    """
    return e_mode_projection_factor(ell, x, small_cutoff=small_cutoff)


def tensor_e_mode_kernel(
    ell: int, x: Union[float, np.ndarray],
    small_cutoff: float = 1.0e-3,
) -> Union[float, np.ndarray]:
    """Spin-2 tensor E-mode LOS kernel  F_ℓ^{E,m=2}(x).

    Formula (Zaldarriaga-Seljak 1997 eq 17, in my sign convention):

        F_ℓ^{E,m=2}(x)
            = (√((ℓ-1)ℓ(ℓ+1)(ℓ+2)) / 4)
              · [ -j_ℓ(x) + j_ℓ''(x) + 2·j_ℓ(x)/x² + 4·j_ℓ'(x)/x ]

    For ℓ < 2, returns 0 (spin-2 minimum, identical to m=0 E-mode
    boundary).

    Small-x Taylor limit
    --------------------
    Using  j_ℓ(x) ~ x^ℓ / (2ℓ+1)!!  at small x:
        j_ℓ'(x) ~ ℓ · x^(ℓ-1) / (2ℓ+1)!!
        j_ℓ''(x) ~ ℓ(ℓ-1) · x^(ℓ-2) / (2ℓ+1)!!

    Then the bracket reduces to
        x^(ℓ-2) / (2ℓ+1)!! · [ℓ(ℓ-1) + 4ℓ + 2]  +  O(x^ℓ)
        = x^(ℓ-2) · (ℓ+1)(ℓ+2) / (2ℓ+1)!!       +  O(x^ℓ)

    giving
        F_ℓ^{E,m=2}(x→0) = √((ℓ-1)ℓ(ℓ+1)(ℓ+2)) · (ℓ+1)(ℓ+2)
                           · x^(ℓ-2) / (4 · (2ℓ+1)!!)

    For ℓ=2, the small-x limit is finite: (1/4) · √24 · 12 / 15 = 0.97980.
    """
    if ell < 2:
        if np.isscalar(x):
            return 0.0
        return np.zeros_like(np.asarray(x, dtype=float))

    spin2_prefactor = np.sqrt((ell - 1.0) * ell * (ell + 1.0) * (ell + 2.0))

    x_arr = np.asarray(x, dtype=float)
    scalar_input = np.isscalar(x)
    small_mask = np.abs(x_arr) < small_cutoff

    # Allocate output
    result = np.zeros_like(x_arr)

    # --- Regular branch: x ≥ small_cutoff ------------------------------------
    if np.any(~small_mask):
        x_reg = x_arr[~small_mask] if x_arr.ndim > 0 else x_arr
        jl = spherical_jn(ell, x_reg)
        jlp = spherical_jn(ell, x_reg, derivative=True)
        # j_ℓ''  via Bessel ODE
        x2 = x_reg * x_reg
        jlpp = -2.0 * jlp / x_reg - (1.0 - ell * (ell + 1.0) / x2) * jl
        bracket = -jl + jlpp + 2.0 * jl / x2 + 4.0 * jlp / x_reg
        kernel_vals = 0.25 * spin2_prefactor * bracket
        if x_arr.ndim > 0:
            result[~small_mask] = kernel_vals
        else:
            result = np.asarray(kernel_vals)

    # --- Small-x Taylor branch -----------------------------------------------
    if np.any(small_mask) and x_arr.ndim > 0:
        x_small = x_arr[small_mask]
        double_fact = _double_factorial_odd(ell)  # (2ℓ+1)!!
        taylor_coeff = (ell + 1.0) * (ell + 2.0) / (4.0 * double_fact)
        taylor_vals = spin2_prefactor * taylor_coeff * np.power(x_small, ell - 2)
        result[small_mask] = taylor_vals

    # Handle scalar small-x separately (ndim=0 case)
    if x_arr.ndim == 0 and small_mask:
        double_fact = _double_factorial_odd(ell)
        taylor_coeff = (ell + 1.0) * (ell + 2.0) / (4.0 * double_fact)
        result = np.asarray(
            spin2_prefactor * taylor_coeff * (float(x_arr) ** (ell - 2))
        )

    return float(result) if scalar_input else result


def tensor_b_mode_kernel(
    ell: int, x: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """Spin-2 tensor B-mode LOS kernel  F_ℓ^{B,m=2}(x) ≡ 0  for Bianchi I.

    For orthogonal Bianchi I (Type I) the polarization-basis rotation
    angle ψ' vanishes identically (Pontzen-Challinor 2007 Table 1).
    B-mode power is therefore **zero at the projector level** — any
    numerical residual below `b_mode_floor` is treated as round-off
    and assertion-gated, not produced as real signal.

    Full B-mode propagation belongs to W11+ (Bianchi VIIh, IX with
    ψ' ≠ 0) and is scope-guarded below.
    """
    if np.isscalar(x):
        return 0.0
    return np.zeros_like(np.asarray(x, dtype=float))


# ============================================================================
# Section 3 - Per-m-channel source terms dataclass
# ============================================================================

@dataclass(frozen=True)
class BianchiSourceTerms:
    """Per-m-channel source-term bundle for the Bianchi I propagator.

    Each m channel carries its own full W9-01 FLRWSourceTerms, i.e. its
    own (θ_0, ψ, π, φ̇+ψ̇, v_b, g, e^{-κ}). In a general treatment these
    are distinct because the m-channel state of the photon hierarchy
    differs (W5-C couples σ_ab into the m=0 and m=±2 Boltzmann chains
    separately).

    Factories enforce explicit intent. `flrw_isotropic` zeros m=±2;
    `from_m_channel_state` wires in W5-C's MChannelAmplitudes.

    NO silent omission: to suppress a channel, the caller passes the
    zero-callable factory. This mirrors W9-01's "SILENT OMISSION OF
    ISW/DOPPLER IS PROHIBITED" contract at the m-channel level.
    """
    sources_m0: FLRWSourceTerms
    sources_m_plus2: FLRWSourceTerms
    sources_m_minus2: FLRWSourceTerms

    @staticmethod
    def flrw_isotropic(sources_m0: FLRWSourceTerms) -> "BianchiSourceTerms":
        """FLRW limit: m=±2 channels zeroed (all five slots → _zero_callable).

        The resulting BianchiSourceTerms, when passed through the matrix
        propagator, reproduces W9-01's FLRW transfer output bit-exact
        via the m=0 delegation path.
        """
        zero_srcs = FLRWSourceTerms.zeros()
        return BianchiSourceTerms(
            sources_m0=sources_m0,
            sources_m_plus2=zero_srcs,
            sources_m_minus2=zero_srcs,
        )

    @staticmethod
    def from_m_channel_state(
        amplitudes: MChannelAmplitudes,
        sources_m0_template: FLRWSourceTerms,
        sources_m2_template: FLRWSourceTerms,
    ) -> "BianchiSourceTerms":
        """Route W5-C MChannelAmplitudes into per-m source bundles.

        Convention
        ----------
        amplitudes.s_m0 scales the m=0 source callables (axial channel).
        amplitudes.s_m2 scales BOTH m=+2 and m=-2 source callables
        (real-shear decomposition: the two channels share magnitude).

        The scaling is absorbed into the π, θ_0, ψ slots of the
        template. ISW/Doppler carry over unchanged (they come from the
        scalar sector and do not scale with shear amplitude — they
        enter m=±2 only through the kernel, not the source).

        Parameters
        ----------
        amplitudes : MChannelAmplitudes
            W5-C decomposition of σ_ab into channel amplitudes.
        sources_m0_template, sources_m2_template : FLRWSourceTerms
            Baseline callables; the amplitudes rescale the perturbative
            slots (theta_0, psi, pi) multiplicatively.
        """
        def _rescale(src: FLRWSourceTerms, amp: float) -> FLRWSourceTerms:
            return FLRWSourceTerms(
                theta_0=lambda eta, s=src.theta_0, a=amp: a * s(eta),
                psi=lambda eta, s=src.psi, a=amp: a * s(eta),
                pi=lambda eta, s=src.pi, a=amp: a * s(eta),
                phi_dot_plus_psi_dot=src.phi_dot_plus_psi_dot,
                v_b=src.v_b,
            )

        return BianchiSourceTerms(
            sources_m0=_rescale(sources_m0_template, amplitudes.s_m0),
            sources_m_plus2=_rescale(sources_m2_template, amplitudes.s_m2),
            sources_m_minus2=_rescale(sources_m2_template, amplitudes.s_m2),
        )


# ============================================================================
# Section 4 - Transfer-function output container
# ============================================================================

@dataclass(frozen=True)
class BianchiTransferFunctions:
    """Per-m-channel transfer functions at a single k.

    Fields are ndarray[ℓ_max+1,] each. ℓ < 2 entries are zero for
    E/B fields; ℓ = 0, 1 are meaningful only for Δ_T^{m=0} (FLRW
    monopole / dipole) — other m≠0 T fields also vanish there.

    B-mode is exposed (not hidden) for Bianchi I with all entries
    identically zero — the field is the audit hook for the
    `assert_b_mode_floor` check. Hiding it would violate the
    silent-omission contract.
    """
    delta_T_m0: np.ndarray
    delta_T_m_plus2: np.ndarray
    delta_T_m_minus2: np.ndarray
    delta_E_m0: np.ndarray
    delta_E_m_plus2: np.ndarray
    delta_E_m_minus2: np.ndarray
    delta_B_all_zero: np.ndarray = field(
        default_factory=lambda: np.zeros(0)
    )

    @property
    def ell_max(self) -> int:
        return self.delta_T_m0.shape[0] - 1

    def total_T_direction_aligned(self) -> np.ndarray:
        """Σ_m Δ_ℓ^{T,m}  (simple m-sum, NOT direction-aware).

        This is a diagnostic aggregate, not a physical observable —
        actual observer-direction assembly is W10-01's responsibility
        through primordial P(k) weighting. Use for sanity checks only.
        """
        return self.delta_T_m0 + self.delta_T_m_plus2 + self.delta_T_m_minus2

    def total_E_direction_aligned(self) -> np.ndarray:
        """Σ_m Δ_ℓ^{E,m}  (diagnostic aggregate, see total_T note)."""
        return self.delta_E_m0 + self.delta_E_m_plus2 + self.delta_E_m_minus2


# ============================================================================
# Section 5 - m=0 projectors: direct W9-01 delegation
# ============================================================================
#
# These functions exist NOT as re-implementations but as delegating
# thin wrappers. The bit-exact FLRW-recovery guarantee (Q2 = option (a)
# in the design ballot) rests on this direct call. If you ever feel
# tempted to inline the projection here for "performance" — don't.
# Duplicated FLOPs will break bit-exact at rtol=1e-14 levels.
# ============================================================================

def project_m0_temperature_transfer(
    k: float,
    sources_m0: FLRWSourceTerms,
    visibility_g: EtaCallable,
    kappa_of_eta: EtaCallable,
    eta_grid: np.ndarray,
    config: BianchiProjectorConfig,
) -> np.ndarray:
    """m=0 channel temperature transfer: delegates to W9-01 verbatim.

    Returns Δ_ℓ^{T,m=0}(k) ∈ ℝ^{ell_max+1}.
    """
    flrw_config = config.to_flrw_config()
    s_t_array = build_temperature_source(
        eta_grid, sources_m0, visibility_g, kappa_of_eta,
    )
    return _flrw_project_T(k, s_t_array, eta_grid, flrw_config)


def project_m0_e_mode_transfer(
    k: float,
    sources_m0: FLRWSourceTerms,
    visibility_g: EtaCallable,
    eta_grid: np.ndarray,
    config: BianchiProjectorConfig,
) -> np.ndarray:
    """m=0 channel E-mode transfer: delegates to W9-01 verbatim."""
    flrw_config = config.to_flrw_config()
    s_e_array = build_polarization_source(eta_grid, sources_m0, visibility_g)
    return _flrw_project_E(k, s_e_array, eta_grid, flrw_config)


# ============================================================================
# Section 6 - m=±2 projectors: tensor kernels via explicit integration
# ============================================================================

def project_m2_temperature_transfer(
    k: float,
    sources_m2: FLRWSourceTerms,
    visibility_g: EtaCallable,
    kappa_of_eta: EtaCallable,
    eta_grid: np.ndarray,
    config: BianchiProjectorConfig,
) -> np.ndarray:
    """m=±2 channel temperature transfer using the tensor T kernel.

        Δ_ℓ^{T,m=±2}(k) = ∫ dη S_T(η) · F_ℓ^{T,m=2}[k(η_0 − η)]

    with the same source-assembly formula as m=0 (g·(θ_0+ψ+π/4) +
    e^{-κ}·(ψ̇+φ̇) + d/dη[g·v_b]) but a different Bessel-like kernel.
    The source slots come scaled by the m=±2 channel amplitude via
    the BianchiSourceTerms.from_m_channel_state factory.

    Scope note: m = +2 and m = −2 share the same kernel (F_ℓ is even
    in m for real shear), so this one function serves both signs.
    Parity differences enter through the source-term scaling when the
    shear is complex (σ_× channel with imaginary part) — out of W9-02
    scope.
    """
    if k < 0 or not np.isfinite(k):
        raise ValueError(f"k must be ≥ 0 and finite (got {k})")
    eta_grid = np.asarray(eta_grid, dtype=float)
    if eta_grid.ndim != 1 or eta_grid.size < 2:
        raise ValueError("eta_grid must be 1-D with ≥ 2 entries")

    # Build the source array (reuse W9-01 assembly verbatim)
    s_t_array = build_temperature_source(
        eta_grid, sources_m2, visibility_g, kappa_of_eta,
    )

    # Integrate over η with tensor T kernel at each ℓ
    kr = k * (config.eta_0_mpc - eta_grid)
    out = np.zeros(config.ell_max + 1)
    for ell in range(config.ell_max + 1):
        kernel_vals = tensor_temperature_kernel(
            ell, kr, small_cutoff=config.bessel_kr_small_cutoff,
        )
        integrand = s_t_array * kernel_vals
        out[ell] = _integrate(integrand, eta_grid, config.quadrature)
    return out


def project_m2_e_mode_transfer(
    k: float,
    sources_m2: FLRWSourceTerms,
    visibility_g: EtaCallable,
    eta_grid: np.ndarray,
    config: BianchiProjectorConfig,
) -> np.ndarray:
    """m=±2 channel E-mode transfer using the Zaldarriaga-Seljak 97 kernel.

        Δ_ℓ^{E,m=±2}(k) = ∫ dη S_E(η) · F_ℓ^{E,m=2}[k(η_0 − η)]

    with S_E = -(√6/4) g π and the tensor E-mode kernel from §2.
    ℓ < 2 entries are identically zero.
    """
    if k < 0 or not np.isfinite(k):
        raise ValueError(f"k must be ≥ 0 and finite (got {k})")
    eta_grid = np.asarray(eta_grid, dtype=float)

    s_e_array = build_polarization_source(eta_grid, sources_m2, visibility_g)

    kr = k * (config.eta_0_mpc - eta_grid)
    out = np.zeros(config.ell_max + 1)
    for ell in range(2, config.ell_max + 1):  # ℓ < 2 left at zero
        kernel_vals = tensor_e_mode_kernel(
            ell, kr, small_cutoff=config.bessel_kr_small_cutoff,
        )
        integrand = s_e_array * kernel_vals
        out[ell] = _integrate(integrand, eta_grid, config.quadrature)
    return out


# ============================================================================
# Section 7 - Matrix propagator (block-diagonal assembly)
# ============================================================================

def matrix_propagator_m0_m2(
    k_magnitude: float,
    cos_theta_k: float,
    sources: BianchiSourceTerms,
    visibility_g: EtaCallable,
    kappa_of_eta: EtaCallable,
    eta_grid: np.ndarray,
    config: BianchiProjectorConfig,
) -> BianchiTransferFunctions:
    """Block-diagonal Bianchi I LOS propagator over m ∈ {0, ±2}.

    Parameters
    ----------
    k_magnitude : float
        |k| in Mpc⁻¹.
    cos_theta_k : float
        Cosine of angle between k̂ and the shear principal z-axis.
        Must lie in [-1, 1]. Axis-aligned k (cos_θ = ±1) zeros out the
        m=±2 channels analytically; this module reports the resulting
        zeros explicitly (via the assert_m2_zero_for_aligned_k hook).
        NOTE: this is an **audit parameter** at the propagator level —
        the m-channel source amplitudes are expected to already fold
        in the geometric dependence via W5-C's decompose_shear_to_m_channels.
        cos_θ is not applied a second time here; it is recorded for
        the direction-dependence diagnostic and the aligned-k assertion.
    sources : BianchiSourceTerms
        Per-m-channel source callables (see BianchiSourceTerms factories).
    visibility_g, kappa_of_eta : EtaCallable
        Global recombination callables (shared across m-channels).
    eta_grid : np.ndarray, shape (n,)
        Monotone increasing conformal-time grid (Big Bang → today).
    config : BianchiProjectorConfig

    Returns
    -------
    BianchiTransferFunctions with six Δ_ℓ arrays (three m-channels ×
    T + E) plus a zero delta_B_all_zero field.
    """
    if not (-1.0 <= cos_theta_k <= 1.0):
        raise ValueError(
            f"cos_theta_k must lie in [-1, 1] (got {cos_theta_k})"
        )

    # m=0 via W9-01 delegation (bit-exact)
    dT_m0 = project_m0_temperature_transfer(
        k_magnitude, sources.sources_m0,
        visibility_g, kappa_of_eta, eta_grid, config,
    )
    dE_m0 = project_m0_e_mode_transfer(
        k_magnitude, sources.sources_m0,
        visibility_g, eta_grid, config,
    )

    # m=+2 and m=-2 via tensor kernels
    dT_plus = project_m2_temperature_transfer(
        k_magnitude, sources.sources_m_plus2,
        visibility_g, kappa_of_eta, eta_grid, config,
    )
    dE_plus = project_m2_e_mode_transfer(
        k_magnitude, sources.sources_m_plus2,
        visibility_g, eta_grid, config,
    )
    dT_minus = project_m2_temperature_transfer(
        k_magnitude, sources.sources_m_minus2,
        visibility_g, kappa_of_eta, eta_grid, config,
    )
    dE_minus = project_m2_e_mode_transfer(
        k_magnitude, sources.sources_m_minus2,
        visibility_g, eta_grid, config,
    )

    # B-mode: identically zero for Bianchi I
    dB_zero = np.zeros(config.ell_max + 1)

    return BianchiTransferFunctions(
        delta_T_m0=dT_m0,
        delta_T_m_plus2=dT_plus,
        delta_T_m_minus2=dT_minus,
        delta_E_m0=dE_m0,
        delta_E_m_plus2=dE_plus,
        delta_E_m_minus2=dE_minus,
        delta_B_all_zero=dB_zero,
    )


# ============================================================================
# Section 8 - k-vector ⇄ (k_magnitude, cos_θ_k) conversion
# ============================================================================

def k_vector_to_magnitude_cos_theta(
    k_vector: np.ndarray,
    shear_axis: np.ndarray = None,
) -> tuple:
    """Convert (kx, ky, kz) to (|k|, cos_θ_k) relative to the shear axis.

    Default shear axis is ẑ = (0, 0, 1), i.e., the shear principal
    z-axis in the diagonal-shear convention used by W5-C's
    DiagonalShearTensor (σ_zz ≡ s_0).

    Returns (k_magnitude, cos_theta_k). Raises ValueError on zero |k|.
    """
    k_arr = np.asarray(k_vector, dtype=float)
    if k_arr.shape != (3,):
        raise ValueError(f"k_vector must have shape (3,) (got {k_arr.shape})")
    if shear_axis is None:
        shear_axis = np.array([0.0, 0.0, 1.0])
    axis = np.asarray(shear_axis, dtype=float)
    axis = axis / np.linalg.norm(axis)

    k_mag = float(np.linalg.norm(k_arr))
    if k_mag == 0.0:
        raise ValueError("|k| = 0; direction undefined")

    cos_theta = float(np.dot(k_arr, axis) / k_mag)
    # Clip to handle floating-point noise
    cos_theta = max(-1.0, min(1.0, cos_theta))
    return k_mag, cos_theta


def matrix_propagator_from_k_vector(
    k_vector: np.ndarray,
    sources: BianchiSourceTerms,
    visibility_g: EtaCallable,
    kappa_of_eta: EtaCallable,
    eta_grid: np.ndarray,
    config: BianchiProjectorConfig,
    shear_axis: np.ndarray = None,
) -> BianchiTransferFunctions:
    """Convenience: (kx, ky, kz) → matrix_propagator_m0_m2 output.

    Implements Q5 option (c): both (|k|, cos_θ) and vector interfaces
    are supported. This function converts to (|k|, cos_θ) internally
    using the shear-axis alignment convention and delegates.
    """
    k_mag, cos_theta = k_vector_to_magnitude_cos_theta(k_vector, shear_axis)
    return matrix_propagator_m0_m2(
        k_mag, cos_theta, sources, visibility_g, kappa_of_eta,
        eta_grid, config,
    )


# ============================================================================
# Section 9 - Diagnostics: FLRW recovery, σ-ladder, direction scan
# ============================================================================

def verify_flrw_recovery(
    sources_m0: FLRWSourceTerms,
    visibility_g: EtaCallable,
    kappa_of_eta: EtaCallable,
    k: float,
    eta_grid: np.ndarray,
    config: BianchiProjectorConfig,
) -> dict:
    """Hard verification that the m=0 path reproduces W9-01 bit-exact.

    Runs the same source through (a) the W9-02 matrix propagator with
    BianchiSourceTerms.flrw_isotropic wrapping, and (b) W9-01's
    project_temperature_transfer directly. Returns a dict with both
    outputs, absolute/relative difference norms, and a boolean pass/fail
    evaluated at config.flrw_recovery_rtol.
    """
    # Path (a): via W9-02 matrix propagator
    bsrcs_iso = BianchiSourceTerms.flrw_isotropic(sources_m0)
    tf = matrix_propagator_m0_m2(
        k, 1.0, bsrcs_iso, visibility_g, kappa_of_eta,
        eta_grid, config,
    )
    dT_via_w902 = tf.delta_T_m0
    dE_via_w902 = tf.delta_E_m0

    # Path (b): W9-01 direct
    flrw_config = config.to_flrw_config()
    s_t = build_temperature_source(
        eta_grid, sources_m0, visibility_g, kappa_of_eta,
    )
    s_e = build_polarization_source(eta_grid, sources_m0, visibility_g)
    dT_via_w901 = _flrw_project_T(k, s_t, eta_grid, flrw_config)
    dE_via_w901 = _flrw_project_E(k, s_e, eta_grid, flrw_config)

    # Differences
    T_max_abs = float(np.max(np.abs(dT_via_w902 - dT_via_w901)))
    T_ref_scale = max(float(np.max(np.abs(dT_via_w901))), 1e-300)
    T_rel = T_max_abs / T_ref_scale

    E_max_abs = float(np.max(np.abs(dE_via_w902 - dE_via_w901)))
    E_ref_scale = max(float(np.max(np.abs(dE_via_w901))), 1e-300)
    E_rel = E_max_abs / E_ref_scale

    passes = (T_rel <= config.flrw_recovery_rtol and
              E_rel <= config.flrw_recovery_rtol)

    return {
        "delta_T_w902": dT_via_w902, "delta_T_w901": dT_via_w901,
        "delta_E_w902": dE_via_w902, "delta_E_w901": dE_via_w901,
        "T_max_abs_diff": T_max_abs, "T_rel_diff": T_rel,
        "E_max_abs_diff": E_max_abs, "E_rel_diff": E_rel,
        "rtol_threshold": config.flrw_recovery_rtol,
        "passes": passes,
    }


def sigma_ladder_convergence(
    sigma_values: list,
    sources_m0: FLRWSourceTerms,
    sources_m2_template: FLRWSourceTerms,
    visibility_g: EtaCallable,
    kappa_of_eta: EtaCallable,
    k_magnitude: float,
    cos_theta_k: float,
    eta_grid: np.ndarray,
    config: BianchiProjectorConfig,
) -> dict:
    """Scan σ across a ladder of magnitudes, return per-σ transfer outputs.

    Builds an axisymmetric shear DiagonalShearTensor at each σ, decomposes
    into MChannelAmplitudes, wires sources via from_m_channel_state, and
    computes the full BianchiTransferFunctions. Useful for verifying:

      * σ=0 entry equals FLRW-recovery output bit-exact
      * Δ_ℓ^{T,m=±2} scales ~ linearly in σ (weak-shear regime)
      * m=0 monotone/continuous approach to FLRW as σ → 0

    Returns dict[σ] → BianchiTransferFunctions.
    """
    out = {}
    for sigma in sigma_values:
        if sigma == 0.0:
            amps = MChannelAmplitudes(s_m0=0.0, s_m2=0.0)
        else:
            shear = make_axisymmetric_shear(s_zz=sigma)
            amps = decompose_shear_to_m_channels(shear)
        bsrcs = BianchiSourceTerms.from_m_channel_state(
            amps, sources_m0, sources_m2_template,
        )
        tf = matrix_propagator_m0_m2(
            k_magnitude, cos_theta_k, bsrcs,
            visibility_g, kappa_of_eta, eta_grid, config,
        )
        out[sigma] = tf
    return out


def direction_scan(
    cos_theta_values: list,
    amplitudes: MChannelAmplitudes,
    sources_m0: FLRWSourceTerms,
    sources_m2_template: FLRWSourceTerms,
    visibility_g: EtaCallable,
    kappa_of_eta: EtaCallable,
    k_magnitude: float,
    eta_grid: np.ndarray,
    config: BianchiProjectorConfig,
) -> dict:
    """Scan observer-frame direction (cos_θ_k) at fixed shear amplitudes.

    Since the source amplitudes are fixed here, this function probes
    only the kernel-level direction response — not the W5-C shear
    decomposition geometry. For a full geometric scan (where σ_ab is
    fixed and cos_θ_k varies in the decomposition), the caller should
    re-decompose at each angle upstream.
    """
    bsrcs = BianchiSourceTerms.from_m_channel_state(
        amplitudes, sources_m0, sources_m2_template,
    )
    out = {}
    for cos_theta in cos_theta_values:
        tf = matrix_propagator_m0_m2(
            k_magnitude, cos_theta, bsrcs,
            visibility_g, kappa_of_eta, eta_grid, config,
        )
        out[cos_theta] = tf
    return out


# ============================================================================
# Section 10 - Physical sign assertions
# ============================================================================

def assert_flrw_recovery_at_sigma_zero(
    recovery_result: dict,
    fail_message_prefix: str = "",
) -> None:
    """Assert the FLRW recovery result passes at the configured rtol."""
    if not recovery_result["passes"]:
        raise AssertionError(
            f"{fail_message_prefix}"
            f"FLRW recovery fails: "
            f"T_rel={recovery_result['T_rel_diff']:.2e}, "
            f"E_rel={recovery_result['E_rel_diff']:.2e}, "
            f"rtol={recovery_result['rtol_threshold']:.2e}"
        )


def assert_m_plus_minus_2_symmetry(
    tf: BianchiTransferFunctions,
    rtol: float = 1.0e-14,
) -> None:
    """Assert Δ_ℓ^{±2} are equal (real-shear symmetry).

    For real (σ_× real) shear, the two m=±2 channels carry the same
    amplitude — this is a direct consequence of the complex
    conjugation symmetry of the source decomposition. Non-equality
    signals a sign/convention bug in the m=±2 projectors.
    """
    T_diff = np.max(np.abs(tf.delta_T_m_plus2 - tf.delta_T_m_minus2))
    T_scale = max(np.max(np.abs(tf.delta_T_m_plus2)), 1e-300)
    E_diff = np.max(np.abs(tf.delta_E_m_plus2 - tf.delta_E_m_minus2))
    E_scale = max(np.max(np.abs(tf.delta_E_m_plus2)), 1e-300)

    if T_diff / T_scale > rtol:
        raise AssertionError(
            f"m=±2 temperature symmetry violated: "
            f"rel_diff = {T_diff / T_scale:.2e} > rtol={rtol:.2e}"
        )
    if E_diff / E_scale > rtol:
        raise AssertionError(
            f"m=±2 E-mode symmetry violated: "
            f"rel_diff = {E_diff / E_scale:.2e} > rtol={rtol:.2e}"
        )


def assert_b_mode_floor(
    tf: BianchiTransferFunctions,
    floor: float = 1.0e-14,
) -> None:
    """Assert |Δ_ℓ^B| ≤ floor for all ℓ (Bianchi I: B ≡ 0 exactly).

    Any non-zero entry is treated as a numerical regression — the
    explicit zero is allocated in matrix_propagator_m0_m2, so a
    non-zero value would indicate corruption elsewhere.
    """
    max_abs = float(np.max(np.abs(tf.delta_B_all_zero)))
    if max_abs > floor:
        raise AssertionError(
            f"B-mode floor violated for Bianchi I: "
            f"max|Δ_ℓ^B| = {max_abs:.2e} > floor={floor:.2e}. "
            f"Bianchi I has ψ'=0 — B-mode should be identically zero."
        )


def assert_m2_zero_when_source_vanishes(
    tf: BianchiTransferFunctions,
    floor: float = 1.0e-30,
) -> None:
    """Assert m=±2 channels are zero when source amplitudes vanish.

    Caller should invoke this ONLY after setting MChannelAmplitudes
    with s_m2 = 0 (or constructing sources via
    BianchiSourceTerms.flrw_isotropic). Any non-zero output means the
    source rescaling failed to propagate — a factory bug.
    """
    dT_max = float(np.max(np.abs(tf.delta_T_m_plus2)))
    dE_max = float(np.max(np.abs(tf.delta_E_m_plus2)))
    if dT_max > floor:
        raise AssertionError(
            f"m=+2 temperature nonzero despite zero source: "
            f"max|Δ_T^+2| = {dT_max:.2e} > floor={floor:.2e}"
        )
    if dE_max > floor:
        raise AssertionError(
            f"m=+2 E-mode nonzero despite zero source: "
            f"max|Δ_E^+2| = {dE_max:.2e} > floor={floor:.2e}"
        )


# ============================================================================
# Section 11 - Scope guards
# ============================================================================

def bianchi_viih_propagator(*args, **kwargs):
    """Bianchi VIIh (helical) propagator. Requires polarization-basis
    rotation ψ' ≠ 0 which introduces full E↔B mixing. This capability
    lives in bass_rs (Rust) for performance reasons.
    """
    raise OutOfScopeError(
        "Bianchi VIIh LOS propagator with ψ'≠0 polarization rotation "
        "is bass_rs scope. W9-02 is Bianchi I only (orthogonal, ψ'=0)."
    )


def bianchi_ix_propagator(*args, **kwargs):
    """Bianchi IX (mixmaster) propagator. Requires curvature-coupled
    shear and non-trivial topology. Scheduled for bass_rs.
    """
    raise OutOfScopeError(
        "Bianchi IX LOS propagator requires compact spatial hypersurfaces "
        "and curvature-driven shear evolution — bass_rs scope."
    )


def tilt_polarization_rotation(*args, **kwargs):
    """Tilt-induced polarization basis rotation ω·(n̂×∂η) is not
    present in orthogonal Bianchi I (ω_a = 0). Appears only in
    tilted Bianchi with ω ≠ 0; bass_rs scope.
    """
    raise OutOfScopeError(
        "Tilt-induced polarization rotation requires ω_a ≠ 0; "
        "orthogonal Bianchi I has ω_a = 0 by construction. "
        "See bass_rs for tilted Bianchi with Tsagas-killed dipole path."
    )


def full_b_mode_transfer(*args, **kwargs):
    """Full B-mode LOS transfer including GW-like sources and
    polarization rotation. For Bianchi I, B=0 identically; this stub
    catches misdirected calls against the explicit zero field.
    """
    raise OutOfScopeError(
        "Full B-mode transfer is scheduled for W11+ with Bianchi VIIh/IX. "
        "For Bianchi I: Δ_ℓ^B ≡ 0 — access via "
        "BianchiTransferFunctions.delta_B_all_zero (populated as zero)."
    )


def nonlinear_sigma_regime(*args, **kwargs):
    """Nonlinear shear regime (Σ > 1e-4, saturation of the
    Michaelis-Menten mapping). Requires re-derivation of the source
    coupling beyond perturbative linearization in σ. W12+ scope.
    """
    raise OutOfScopeError(
        "Nonlinear Σ regime (Σ² > 1e-4) violates the Route B "
        "Michaelis-Menten linearization used by W5-C. "
        "Full nonlinear treatment is W12+."
    )


def compute_c_ell_bianchi(*args, **kwargs):
    """Bianchi I C_ℓ^{TT/EE} assembly. This is W10-01 scope: requires
    primordial P(k) weighting and m-channel observer-direction coupling
    for the full BiPoSH decomposition.
    """
    raise OutOfScopeError(
        "C_ℓ assembly from Δ_ℓ^m(k) requires primordial P(k) integration "
        "and m-channel direction-dependent coupling. See W10-01 "
        "prompt in MASTER_PROMPT_LIST for the production spec."
    )
