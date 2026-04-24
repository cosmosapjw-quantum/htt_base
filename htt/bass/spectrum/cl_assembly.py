"""
bass/spectrum/cl_assembly.py   (Week 10-01)
============================================

C_ℓ^{TT/EE/TE} angular power spectrum assembly from BianchiTransferFunctions.
Consumes per-k transfer functions (produced by W9-02 or analytic stubs),
weights by the primordial scalar power spectrum P_R(k), and integrates
over log-k. Output is converted to D_ℓ = ℓ(ℓ+1)C_ℓ T_CMB² / (2π) in
units of μK² (Planck convention).

Physics
-------
Isotropic (FLRW) case:

    C_ℓ^{TT} = 4π ∫ d(ln k)  P_R(k)  |Δ_ℓ^{T,m=0}(k)|²
    C_ℓ^{EE} = 4π ∫ d(ln k)  P_R(k)  |Δ_ℓ^{E,m=0}(k)|²
    C_ℓ^{TE} = 4π ∫ d(ln k)  P_R(k)  Δ_ℓ^{T,m=0}(k) · Δ_ℓ^{E,m=0}(k)

Anisotropic (Bianchi I, diagonal part):

    C_ℓ^{XY,diag} = 4π Σ_m ∫ d(ln k) P_R(k) Δ_ℓ^{X,m}(k) Δ_ℓ^{Y,m*}(k),
                    m ∈ {0, ±2}

Primordial scalar power spectrum (Planck 2018 baseline):

    P_R(k) = A_s (k / k_*)^(n_s − 1)

    A_s = 2.1e-9, n_s = 0.9649, k_* = 0.05 Mpc⁻¹.

D_ℓ conversion (Planck convention):

    D_ℓ^{XY} = [ℓ(ℓ+1) / (2π)] · C_ℓ^{XY} · T_CMB²,   T_CMB = 2.72548 K.

Route B Michaelis-Menten sentinel
---------------------------------
The production sentinel for axisymmetric Bianchi I shear:

    D_2(Σ²) = C_1 Σ² / (1 + C_2 Σ²),   C_1 = 1.753e7, C_2 = 6.825e5

At Σ² = 1e-8: D_2 = 0.1741 μK² (SSOT: bass_rs/d2_convention.rs).

Scope contract
--------------
This module is a **consumer** of transfer-function callables. It does
NOT compute Δ_ℓ(k) from first principles — no scalar mode evolution
solver lives here. bass_py's W10-01 is the Route B *lookup sentinel*
and the C_ℓ-assembly infrastructure. First-principles reproduction of
D_2 = 0.1741 μK² belongs to bass_rs (Rust) and future bass_py evolution
prompts.

IN scope
  * Isotropic C_ℓ^{TT/EE/TE} assembly (single m=0 channel)
  * Anisotropic Bianchi I diagonal C_ℓ (m=0, ±2 summation)
  * D_ℓ conversion with Planck T_CMB² normalization
  * Route B lookup sentinel (formula, not derivation)
  * Michaelis-Menten fitter (scipy.optimize.curve_fit)
  * log-k quadrature (trapezoid + Simpson)
  * High-ℓ convergence diagnostic
  * Injectable primordial P_R(k) callable

OUT of scope  (→ OutOfScopeError)
  * Off-diagonal C_{ℓm,ℓ'm'} / BiPoSH            → W11+
  * Transfer-function generation                  → W9-01, W9-02
  * First-principles D_2 reproduction             → bass_rs
  * CAMB V-gate cross-validation                  → W10-02
  * Lensing, foregrounds, non-Gaussian            → future
  * Full scalar mode evolution (Θ_0, Ψ solver)    → bass_rs

Dependencies
------------
  W9-02  bass.los.bianchi_propagator.BianchiTransferFunctions
  W9-01  bass.los.flrw_bessel_projector.OutOfScopeError
  bass.observational.planck_mes_bounds  (T_CMB_K, D_2 Planck reference)
  scipy.integrate.simpson, scipy.optimize.curve_fit, numpy

References
----------
Seljak, U., & Zaldarriaga, M. (1996). "A line-of-sight integration
  approach to CMB anisotropies." ApJ 469, 437.
Planck Collaboration (2018). "Planck 2018 results. X. Constraints on
  inflation." A&A 641, A10.  (A_s, n_s baseline)
Fixsen, D. J. (2009). "The temperature of the cosmic microwave
  background." ApJ 707, 916.  (T_CMB = 2.72548 ± 0.00057 K)
d2_convention.rs (bass_rs SSOT): C_1 = 1.753e7, C_2 = 6.825e5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Union

import numpy as np
from scipy.integrate import simpson
from scipy.optimize import curve_fit

from bass.los.bianchi_propagator import BianchiTransferFunctions
from bass.los.flrw_bessel_projector import OutOfScopeError
from bass.observational.planck_mes_bounds import T_CMB_K

# ============================================================================
# Route B Michaelis-Menten SSOT constants
# ============================================================================
#
# d2_convention.rs (bass_rs) is the authoritative SSOT. These values are
# mirrors for sentinel-evaluation purposes only — any cross-repo change
# must update both and trigger the anti-regression guard.
# ============================================================================

ROUTE_B_C1: float = 1.753e7
"""Michaelis-Menten numerator coefficient. SSOT: bass_rs/d2_convention.rs."""

ROUTE_B_C2: float = 6.825e5
"""Michaelis-Menten denominator coefficient. SSOT: bass_rs/d2_convention.rs."""

ROUTE_B_D2_AT_SIGMA2_1EM8: float = ROUTE_B_C1 * 1.0e-8 / (1.0 + ROUTE_B_C2 * 1.0e-8)
"""Sentinel value D_2(Σ² = 1e-8) = 0.17408... μK². Anti-regression guard."""


# ============================================================================
# Section 1 - Configuration
# ============================================================================

# Type alias: callable that returns a BianchiTransferFunctions at k
TransferFunctionAtK = Callable[[float], BianchiTransferFunctions]

# Type alias: callable for primordial power spectrum P_R(k)
PrimordialPowerCallable = Callable[[Union[float, np.ndarray]],
                                     Union[float, np.ndarray]]


@dataclass(frozen=True)
class CLAssemblyConfig:
    """Immutable configuration for C_ℓ assembly.

    Parameters
    ----------
    ell_max : int
        Highest multipole returned. Output arrays have shape (ell_max+1,).
    k_grid : np.ndarray
        Log-spaced k-grid in Mpc⁻¹. Default: 256 points, k ∈ [1e-4, 0.5]
        (CAMB-compatible range).
    A_s : float
        Primordial scalar amplitude at k_pivot. Planck 2018: 2.1e-9.
    n_s : float
        Primordial scalar spectral index. Planck 2018: 0.9649.
    k_pivot_mpc : float
        Pivot scale in Mpc⁻¹. Planck convention: 0.05.
    quadrature : str
        'trapezoid' (default, O(dlnk²)) or 'simpson' (O(dlnk⁴), requires
        odd grid length).
    T_CMB_K : float
        CMB monopole temperature; defaults to module-level T_CMB_K =
        2.72548 K (Fixsen 2009).
    primordial_pk_fn : Optional[Callable]
        If provided, overrides (A_s, n_s, k_pivot) to use this callable
        for P_R(k). Default None → uses the power-law from A_s, n_s.
    b_mode_floor : float
        Floor for C_ℓ^{BB} assertion (Bianchi I: identically zero).
    """
    ell_max: int
    k_grid: np.ndarray = field(
        default_factory=lambda: np.logspace(-4.0, np.log10(0.5), 256)
    )
    A_s: float = 2.1e-9
    n_s: float = 0.9649
    k_pivot_mpc: float = 0.05
    quadrature: str = "trapezoid"
    T_CMB_K: float = T_CMB_K
    primordial_pk_fn: Optional[PrimordialPowerCallable] = None
    b_mode_floor: float = 1.0e-14

    def __post_init__(self) -> None:
        if self.ell_max < 0:
            raise ValueError(f"ell_max must be ≥ 0 (got {self.ell_max})")
        if np.any(np.asarray(self.k_grid) <= 0):
            raise ValueError("k_grid entries must be > 0")
        if self.A_s <= 0:
            raise ValueError("A_s must be > 0")
        if self.k_pivot_mpc <= 0:
            raise ValueError("k_pivot_mpc must be > 0")
        if self.quadrature not in ("trapezoid", "simpson"):
            raise ValueError(
                f"quadrature must be 'trapezoid' or 'simpson' "
                f"(got {self.quadrature!r})"
            )
        if self.quadrature == "simpson" and self.k_grid.size % 2 == 0:
            raise ValueError(
                f"Simpson requires odd k_grid length "
                f"(got {self.k_grid.size})"
            )
        if self.T_CMB_K <= 0:
            raise ValueError("T_CMB_K must be > 0")
        if self.b_mode_floor < 0:
            raise ValueError("b_mode_floor must be ≥ 0")


# ============================================================================
# Section 2 - Primordial power spectrum
# ============================================================================

def primordial_power_spectrum(
    k_array: Union[float, np.ndarray],
    config: CLAssemblyConfig,
) -> Union[float, np.ndarray]:
    """Evaluate P_R(k) on the config-specified form.

    If config.primordial_pk_fn is None (default), uses the power-law
    P_R(k) = A_s (k/k_*)^(n_s - 1). Otherwise delegates to the
    injected callable.

    Returns
    -------
    P_R array of the same shape as k_array. Units: dimensionless
    (ΛCDM scalar-mode convention; the 4π from the sphere is absorbed
    into the assembly integral).
    """
    k = np.asarray(k_array, dtype=float)

    if config.primordial_pk_fn is not None:
        result = config.primordial_pk_fn(k)
        return np.asarray(result, dtype=float)

    # Default: single power-law
    ratio = k / config.k_pivot_mpc
    return config.A_s * np.power(ratio, config.n_s - 1.0)


# ============================================================================
# Section 3 - log-k quadrature helper
# ============================================================================

def _integrate_log_k(
    integrand_on_k: np.ndarray,
    k_grid: np.ndarray,
    quadrature: str,
) -> float:
    """∫ d(ln k) f(k) via the requested scheme.

    The conversion d(ln k) = dk / k means the quadrature runs over
    ln k with the integrand f(k) directly (no Jacobian multiplied by
    the caller).
    """
    ln_k = np.log(k_grid)
    if quadrature == "trapezoid":
        return float(np.trapezoid(integrand_on_k, ln_k))
    if quadrature == "simpson":
        return float(simpson(integrand_on_k, x=ln_k))
    raise ValueError(f"unknown quadrature: {quadrature!r}")


# ============================================================================
# Section 4 - Isotropic (FLRW) C_ℓ assembly
# ============================================================================

def assemble_cl_TT_isotropic(
    transfer_fn: TransferFunctionAtK,
    config: CLAssemblyConfig,
) -> np.ndarray:
    """C_ℓ^{TT} = 4π ∫ d(ln k) P_R(k) |Δ_ℓ^{T,m=0}(k)|².

    Parameters
    ----------
    transfer_fn : callable
        k → BianchiTransferFunctions. The m=0 field is consumed; m=±2
        fields are ignored (for isotropic assembly).

    Returns
    -------
    C_ℓ array of shape (ell_max+1,).
    """
    n_ell = config.ell_max + 1
    n_k = config.k_grid.size

    # Evaluate transfer on k-grid: shape (n_k, n_ell)
    delta_T_m0 = np.zeros((n_k, n_ell))
    for ik, k in enumerate(config.k_grid):
        tf = transfer_fn(float(k))
        # Truncate or pad to ell_max
        dT = tf.delta_T_m0
        delta_T_m0[ik, :min(n_ell, dT.size)] = dT[:n_ell]

    # Primordial weighting
    p_k = primordial_power_spectrum(config.k_grid, config)  # shape (n_k,)

    # Assemble per ℓ
    cl = np.zeros(n_ell)
    for ell in range(n_ell):
        integrand = p_k * delta_T_m0[:, ell] ** 2
        cl[ell] = 4.0 * np.pi * _integrate_log_k(
            integrand, config.k_grid, config.quadrature,
        )
    return cl


def assemble_cl_EE_isotropic(
    transfer_fn: TransferFunctionAtK,
    config: CLAssemblyConfig,
) -> np.ndarray:
    """C_ℓ^{EE} = 4π ∫ d(ln k) P_R(k) |Δ_ℓ^{E,m=0}(k)|².

    ℓ < 2 entries are identically zero because Δ_ℓ^{E,m=0} vanishes
    there (spin-2 minimum enforced by W9-01 projector).
    """
    n_ell = config.ell_max + 1
    n_k = config.k_grid.size

    delta_E_m0 = np.zeros((n_k, n_ell))
    for ik, k in enumerate(config.k_grid):
        tf = transfer_fn(float(k))
        dE = tf.delta_E_m0
        delta_E_m0[ik, :min(n_ell, dE.size)] = dE[:n_ell]

    p_k = primordial_power_spectrum(config.k_grid, config)

    cl = np.zeros(n_ell)
    for ell in range(n_ell):
        integrand = p_k * delta_E_m0[:, ell] ** 2
        cl[ell] = 4.0 * np.pi * _integrate_log_k(
            integrand, config.k_grid, config.quadrature,
        )
    return cl


def assemble_cl_TE_isotropic(
    transfer_fn: TransferFunctionAtK,
    config: CLAssemblyConfig,
) -> np.ndarray:
    """C_ℓ^{TE} = 4π ∫ d(ln k) P_R(k) Δ_ℓ^{T,m=0}(k) · Δ_ℓ^{E,m=0}(k).

    ℓ < 2 entries are zero. Sign follows the Δ_T · Δ_E product.
    """
    n_ell = config.ell_max + 1
    n_k = config.k_grid.size

    delta_T_m0 = np.zeros((n_k, n_ell))
    delta_E_m0 = np.zeros((n_k, n_ell))
    for ik, k in enumerate(config.k_grid):
        tf = transfer_fn(float(k))
        dT = tf.delta_T_m0
        dE = tf.delta_E_m0
        delta_T_m0[ik, :min(n_ell, dT.size)] = dT[:n_ell]
        delta_E_m0[ik, :min(n_ell, dE.size)] = dE[:n_ell]

    p_k = primordial_power_spectrum(config.k_grid, config)

    cl = np.zeros(n_ell)
    for ell in range(n_ell):
        integrand = p_k * delta_T_m0[:, ell] * delta_E_m0[:, ell]
        cl[ell] = 4.0 * np.pi * _integrate_log_k(
            integrand, config.k_grid, config.quadrature,
        )
    return cl


# ============================================================================
# Section 5 - Anisotropic Bianchi I diagonal C_ℓ assembly
# ============================================================================

def assemble_cl_TT_bianchi(
    transfer_fn: TransferFunctionAtK,
    config: CLAssemblyConfig,
) -> np.ndarray:
    """Diagonal C_ℓ^{TT} summed over m ∈ {0, ±2}:

        C_ℓ^{TT,diag} = 4π Σ_m ∫ d(ln k) P_R(k) |Δ_ℓ^{T,m}(k)|²

    Off-diagonal C_{ℓm,ℓ'm'} terms (BiPoSH) are NOT computed — scope
    guard `off_diagonal_biposh` redirects to W11+.

    FLRW recovery: when transfer_fn produces flrw_isotropic sources
    (m=±2 channels identically zero), this reduces to the same output
    as assemble_cl_TT_isotropic bit-exact.
    """
    n_ell = config.ell_max + 1
    n_k = config.k_grid.size

    delta_T_m0 = np.zeros((n_k, n_ell))
    delta_T_mp2 = np.zeros((n_k, n_ell))
    delta_T_mn2 = np.zeros((n_k, n_ell))
    for ik, k in enumerate(config.k_grid):
        tf = transfer_fn(float(k))
        delta_T_m0[ik, :min(n_ell, tf.delta_T_m0.size)] = tf.delta_T_m0[:n_ell]
        delta_T_mp2[ik, :min(n_ell, tf.delta_T_m_plus2.size)] = tf.delta_T_m_plus2[:n_ell]
        delta_T_mn2[ik, :min(n_ell, tf.delta_T_m_minus2.size)] = tf.delta_T_m_minus2[:n_ell]

    p_k = primordial_power_spectrum(config.k_grid, config)

    cl = np.zeros(n_ell)
    for ell in range(n_ell):
        integrand = p_k * (
            delta_T_m0[:, ell] ** 2
            + delta_T_mp2[:, ell] ** 2
            + delta_T_mn2[:, ell] ** 2
        )
        cl[ell] = 4.0 * np.pi * _integrate_log_k(
            integrand, config.k_grid, config.quadrature,
        )
    return cl


def assemble_cl_EE_bianchi(
    transfer_fn: TransferFunctionAtK,
    config: CLAssemblyConfig,
) -> np.ndarray:
    """Diagonal C_ℓ^{EE} summed over m ∈ {0, ±2}. ℓ < 2 entries zero."""
    n_ell = config.ell_max + 1
    n_k = config.k_grid.size

    delta_E_m0 = np.zeros((n_k, n_ell))
    delta_E_mp2 = np.zeros((n_k, n_ell))
    delta_E_mn2 = np.zeros((n_k, n_ell))
    for ik, k in enumerate(config.k_grid):
        tf = transfer_fn(float(k))
        delta_E_m0[ik, :min(n_ell, tf.delta_E_m0.size)] = tf.delta_E_m0[:n_ell]
        delta_E_mp2[ik, :min(n_ell, tf.delta_E_m_plus2.size)] = tf.delta_E_m_plus2[:n_ell]
        delta_E_mn2[ik, :min(n_ell, tf.delta_E_m_minus2.size)] = tf.delta_E_m_minus2[:n_ell]

    p_k = primordial_power_spectrum(config.k_grid, config)

    cl = np.zeros(n_ell)
    for ell in range(n_ell):
        integrand = p_k * (
            delta_E_m0[:, ell] ** 2
            + delta_E_mp2[:, ell] ** 2
            + delta_E_mn2[:, ell] ** 2
        )
        cl[ell] = 4.0 * np.pi * _integrate_log_k(
            integrand, config.k_grid, config.quadrature,
        )
    return cl


def assemble_cl_TE_bianchi(
    transfer_fn: TransferFunctionAtK,
    config: CLAssemblyConfig,
) -> np.ndarray:
    """Diagonal C_ℓ^{TE} summed over m ∈ {0, ±2}:

        C_ℓ^{TE,diag} = 4π Σ_m ∫ d(ln k) P_R(k) Δ_ℓ^{T,m} Δ_ℓ^{E,m*}

    Real-shear convention: all Δ are real, so the complex conjugate
    is trivial. For complex-shear extensions, re-derive.
    """
    n_ell = config.ell_max + 1
    n_k = config.k_grid.size

    T_m0 = np.zeros((n_k, n_ell)); E_m0 = np.zeros((n_k, n_ell))
    T_mp2 = np.zeros((n_k, n_ell)); E_mp2 = np.zeros((n_k, n_ell))
    T_mn2 = np.zeros((n_k, n_ell)); E_mn2 = np.zeros((n_k, n_ell))

    for ik, k in enumerate(config.k_grid):
        tf = transfer_fn(float(k))
        T_m0[ik, :min(n_ell, tf.delta_T_m0.size)] = tf.delta_T_m0[:n_ell]
        T_mp2[ik, :min(n_ell, tf.delta_T_m_plus2.size)] = tf.delta_T_m_plus2[:n_ell]
        T_mn2[ik, :min(n_ell, tf.delta_T_m_minus2.size)] = tf.delta_T_m_minus2[:n_ell]
        E_m0[ik, :min(n_ell, tf.delta_E_m0.size)] = tf.delta_E_m0[:n_ell]
        E_mp2[ik, :min(n_ell, tf.delta_E_m_plus2.size)] = tf.delta_E_m_plus2[:n_ell]
        E_mn2[ik, :min(n_ell, tf.delta_E_m_minus2.size)] = tf.delta_E_m_minus2[:n_ell]

    p_k = primordial_power_spectrum(config.k_grid, config)

    cl = np.zeros(n_ell)
    for ell in range(n_ell):
        integrand = p_k * (
            T_m0[:, ell] * E_m0[:, ell]
            + T_mp2[:, ell] * E_mp2[:, ell]
            + T_mn2[:, ell] * E_mn2[:, ell]
        )
        cl[ell] = 4.0 * np.pi * _integrate_log_k(
            integrand, config.k_grid, config.quadrature,
        )
    return cl


def assemble_cl_BB_bianchi(
    transfer_fn: TransferFunctionAtK,
    config: CLAssemblyConfig,
) -> np.ndarray:
    """C_ℓ^{BB} for Bianchi I. Identically zero by construction
    (ψ' = 0 → Δ_ℓ^{B,m} = 0 for all m at the W9-02 projector level).

    Returned as explicit zero array for API symmetry and assertion
    hook (assert_b_mode_cl_zero).
    """
    return np.zeros(config.ell_max + 1)


# ============================================================================
# Section 6 - D_ℓ conversion
# ============================================================================

def compute_dl(
    cl_array: np.ndarray,
    T_CMB_K: float = T_CMB_K,
) -> np.ndarray:
    """D_ℓ = ℓ(ℓ+1) C_ℓ T_CMB² / (2π), in units of μK².

    cl_array is indexed 0..ell_max. ℓ=0 and ℓ=1 entries are set to
    zero by the ℓ(ℓ+1) prefactor automatically — no issue with the
    conversion formula at those entries.

    Parameters
    ----------
    cl_array : np.ndarray
        C_ℓ in the dimensionless convention (as produced by the
        assemble_cl_* functions).
    T_CMB_K : float
        CMB temperature in Kelvin. Default Fixsen 2009 value.

    Returns
    -------
    D_ℓ array in μK².
    """
    cl = np.asarray(cl_array, dtype=float)
    n_ell = cl.size
    ell_arr = np.arange(n_ell, dtype=float)
    T_CMB_microK_sq = (T_CMB_K * 1.0e6) ** 2  # K² → μK²
    return ell_arr * (ell_arr + 1.0) / (2.0 * np.pi) * cl * T_CMB_microK_sq


# ============================================================================
# Section 7 - Route B Michaelis-Menten lookup sentinel
# ============================================================================

def route_b_d2_lookup(
    sigma_sq: Union[float, np.ndarray],
    C1: float = ROUTE_B_C1,
    C2: float = ROUTE_B_C2,
) -> Union[float, np.ndarray]:
    """Evaluate D_2(Σ²) via the Michaelis-Menten formula:

        D_2(Σ²) = C_1 Σ² / (1 + C_2 Σ²)

    At Σ² = 1e-8: D_2 = 0.17408... μK².

    SSOT: bass_rs/d2_convention.rs. Any cross-repo modification must
    update both constants and trigger the anti-regression guard
    `assert_d2_anti_regression_vs_route_b`.

    Parameters
    ----------
    sigma_sq : float or ndarray
        Dimensionless shear magnitude squared. Must be ≥ 0.
    """
    sigma_arr = np.asarray(sigma_sq, dtype=float)
    if np.any(sigma_arr < 0):
        raise ValueError("sigma_sq must be ≥ 0 (got negative entry)")
    result = C1 * sigma_arr / (1.0 + C2 * sigma_arr)
    if np.isscalar(sigma_sq):
        return float(result)
    return result


def assert_d2_anti_regression_vs_route_b(
    computed_d2: float,
    sigma_sq: float,
    rtol: float = 5.0e-3,
    C1: float = ROUTE_B_C1,
    C2: float = ROUTE_B_C2,
) -> None:
    """Compare a computed D_2 against the Route B lookup.

    Used as a regression guard when swapping out the transfer-function
    backend (e.g., W9-02 analytic mock → bass_rs first-principles).
    Tolerance 0.5% matches the d2_convention.rs guard floor.
    """
    expected = route_b_d2_lookup(sigma_sq, C1=C1, C2=C2)
    rel_err = abs(computed_d2 - expected) / max(abs(expected), 1.0e-30)
    if rel_err > rtol:
        raise AssertionError(
            f"D_2 anti-regression violated at Σ² = {sigma_sq:.2e}: "
            f"computed = {computed_d2:.6e}, Route B expected = {expected:.6e}, "
            f"rel_err = {rel_err:.2e} > rtol = {rtol:.2e}. "
            f"Check d2_convention.rs SSOT consistency."
        )


# ============================================================================
# Section 8 - Michaelis-Menten fitter
# ============================================================================

def _mm_model(sigma_sq: np.ndarray, C1: float, C2: float) -> np.ndarray:
    """D(Σ²) = C_1 Σ² / (1 + C_2 Σ²). Used as the curve_fit target."""
    return C1 * sigma_sq / (1.0 + C2 * sigma_sq)


def fit_michaelis_menten(
    sigma_sq_arr: np.ndarray,
    d_l_arr: np.ndarray,
    initial_guess: tuple = (1.0e7, 1.0e5),
    sigma_weights: Optional[np.ndarray] = None,
) -> dict:
    """Fit D = C_1 Σ² / (1 + C_2 Σ²) to (Σ²_i, D_i) data.

    Parameters
    ----------
    sigma_sq_arr : np.ndarray
        Σ² values (independent variable).
    d_l_arr : np.ndarray
        Measured D_ℓ values at those Σ² (typically D_2 from assemblies
        with varying shear input).
    initial_guess : (C1_0, C2_0)
        Starting point for scipy.optimize.curve_fit.
    sigma_weights : ndarray or None
        Per-point uncertainties (1/σ weighting in curve_fit); default
        None → uniform weights.

    Returns
    -------
    dict with keys:
        'C1', 'C2' : best-fit Michaelis-Menten coefficients
        'C1_err', 'C2_err' : 1-σ uncertainties from sqrt(diag(cov))
        'covariance' : full covariance matrix (2×2)
        'residuals' : D_fit - D_data
        'rms_residual' : sqrt(mean(residuals²))
    """
    s_arr = np.asarray(sigma_sq_arr, dtype=float)
    d_arr = np.asarray(d_l_arr, dtype=float)
    if s_arr.shape != d_arr.shape:
        raise ValueError("sigma_sq_arr and d_l_arr must have same shape")
    if s_arr.size < 2:
        raise ValueError("Need ≥ 2 data points for a 2-parameter fit")

    popt, pcov = curve_fit(
        _mm_model, s_arr, d_arr,
        p0=initial_guess, sigma=sigma_weights,
        absolute_sigma=(sigma_weights is not None),
    )
    C1_fit, C2_fit = popt
    errs = np.sqrt(np.diag(pcov))
    residuals = _mm_model(s_arr, C1_fit, C2_fit) - d_arr

    return {
        "C1": float(C1_fit), "C2": float(C2_fit),
        "C1_err": float(errs[0]), "C2_err": float(errs[1]),
        "covariance": pcov,
        "residuals": residuals,
        "rms_residual": float(np.sqrt(np.mean(residuals ** 2))),
    }


# ============================================================================
# Section 9 - Diagnostics: σ² scan, high-ℓ convergence
# ============================================================================

def sigma_squared_scan(
    sigma_sq_values: list,
    transfer_fn_factory: Callable[[float], TransferFunctionAtK],
    config: CLAssemblyConfig,
    which: str = "TT",
) -> dict:
    """Run the assembly at a ladder of Σ² values and return per-σ² C_ℓ.

    The `transfer_fn_factory(sigma_sq)` must return a
    TransferFunctionAtK callable configured for that Σ². This pattern
    keeps scan state out of the assembler while allowing arbitrary
    shear-to-transfer plumbing upstream.

    Parameters
    ----------
    which : str
        'TT', 'EE', 'TE', or 'BB'. Selects the assembler.
    """
    assembler_map = {
        "TT": assemble_cl_TT_bianchi,
        "EE": assemble_cl_EE_bianchi,
        "TE": assemble_cl_TE_bianchi,
        "BB": assemble_cl_BB_bianchi,
    }
    if which not in assembler_map:
        raise ValueError(f"which must be one of {list(assembler_map)} (got {which!r})")
    fn = assembler_map[which]
    out = {}
    for sigma_sq in sigma_sq_values:
        transfer_fn = transfer_fn_factory(sigma_sq)
        out[sigma_sq] = fn(transfer_fn, config)
    return out


def high_ell_convergence_diagnostic(
    transfer_fn: TransferFunctionAtK,
    ell_test: int,
    config: CLAssemblyConfig,
    k_max_values: Optional[list] = None,
) -> dict:
    """At fixed ℓ, recompute C_ℓ with progressively larger k_max.

    The integrand `P_R(k) |Δ_ℓ(k)|²` peaks near k ~ ℓ/η_*; beyond that
    scale the transfer function decays. The diagnostic reports
    plateau values: when the integral stops growing with k_max, the
    k-grid is sufficient for that ℓ.

    Returns
    -------
    dict: 'k_max_values', 'cl_values', 'relative_change'
          (fractional change between adjacent k_max_values).
    """
    if k_max_values is None:
        k_max_values = [0.01, 0.05, 0.1, 0.2, 0.5]

    cls = []
    for kmax in k_max_values:
        k_sub = config.k_grid[config.k_grid <= kmax]
        # Simpson requires odd; trim if needed
        if config.quadrature == "simpson" and k_sub.size % 2 == 0:
            k_sub = k_sub[:-1]
        if k_sub.size < 3:
            cls.append(0.0)
            continue
        subset_cfg = CLAssemblyConfig(
            ell_max=ell_test, k_grid=k_sub,
            A_s=config.A_s, n_s=config.n_s,
            k_pivot_mpc=config.k_pivot_mpc,
            quadrature=config.quadrature,
            T_CMB_K=config.T_CMB_K,
            primordial_pk_fn=config.primordial_pk_fn,
            b_mode_floor=config.b_mode_floor,
        )
        cl = assemble_cl_TT_isotropic(transfer_fn, subset_cfg)
        cls.append(cl[ell_test])

    cls_arr = np.asarray(cls, dtype=float)
    rel_change = np.zeros_like(cls_arr)
    for i in range(1, cls_arr.size):
        ref = max(abs(cls_arr[i]), 1.0e-30)
        rel_change[i] = abs(cls_arr[i] - cls_arr[i - 1]) / ref
    return {
        "k_max_values": list(k_max_values),
        "cl_values": cls_arr,
        "relative_change": rel_change,
    }


# ============================================================================
# Section 10 - Physical / sanity assertions
# ============================================================================

def assert_cl_tt_positivity(cl_tt: np.ndarray) -> None:
    """C_ℓ^{TT} ≥ 0 for all ℓ. Negative values signal a sign or
    quadrature bug (TT is variance — cannot be negative)."""
    negative_mask = cl_tt < 0
    if np.any(negative_mask):
        bad_ells = np.where(negative_mask)[0]
        raise AssertionError(
            f"C_ℓ^{{TT}} must be non-negative. "
            f"Negative entries at ℓ = {bad_ells.tolist()}, "
            f"min value = {cl_tt.min():.3e}"
        )


def assert_cl_ee_ell_lt_2_zero(
    cl_ee: np.ndarray,
    floor: float = 1.0e-30,
) -> None:
    """C_ℓ^{EE} must be zero for ℓ < 2 (spin-2 minimum). Any
    non-zero entry indicates a Δ_ℓ^{E} leak at sub-ℓ=2."""
    for ell in (0, 1):
        if abs(cl_ee[ell]) > floor:
            raise AssertionError(
                f"C_{ell}^{{EE}} = {cl_ee[ell]:.3e} exceeds floor {floor:.2e}; "
                f"E-mode must vanish below the spin-2 minimum."
            )


def assert_b_mode_cl_zero(
    cl_bb: np.ndarray,
    floor: float = 1.0e-14,
) -> None:
    """C_ℓ^{BB} ≡ 0 for Bianchi I."""
    max_abs = float(np.max(np.abs(cl_bb)))
    if max_abs > floor:
        raise AssertionError(
            f"C_ℓ^{{BB}} must be identically zero for Bianchi I "
            f"(ψ' = 0). max|C_ℓ^BB| = {max_abs:.2e} > floor = {floor:.2e}."
        )


# ============================================================================
# Section 11 - Scope guards
# ============================================================================

def off_diagonal_biposh(*args, **kwargs):
    """Off-diagonal C_{ℓm,ℓ'm'} / BiPoSH assembly. This is the
    direction-dependent signature of Bianchi anisotropy that requires
    Wigner-3j weighting of the m-channel products. Scheduled for W11+.
    """
    raise OutOfScopeError(
        "Off-diagonal BiPoSH C_{ℓm,ℓ'm'} assembly is W11+ scope. "
        "W10-01 computes only diagonal (m-summed) C_ℓ for Bianchi I."
    )


def camb_v_gate_comparison(*args, **kwargs):
    """CAMB validation gate: compare assembled D_ℓ against CAMB
    reference spectra (ΛCDM FLRW limit). Scheduled as W10-02.
    """
    raise OutOfScopeError(
        "CAMB V-gate comparison is W10-02 scope. W10-01 produces the "
        "D_ℓ outputs that W10-02 will validate against CAMB. See "
        "MASTER_PROMPT_LIST v1.2 §7."
    )


def full_scalar_mode_evolution(*args, **kwargs):
    """First-principles computation of Θ_0(k, η) and Ψ(k, η) from
    the Boltzmann-Einstein system. This is the machinery that would
    let bass_py reproduce D_2 = 0.1741 μK² without relying on the
    Route B lookup sentinel. bass_rs scope for the foreseeable future.
    """
    raise OutOfScopeError(
        "Full scalar mode evolution (Θ_0, Ψ solver) lives in bass_rs. "
        "bass_py W10-01 is the Route B lookup sentinel + assembly "
        "infrastructure — first-principles D_2 reproduction is not "
        "W10-01's role."
    )


def lensing_cl(*args, **kwargs):
    """CMB lensing power spectrum. Requires C_ℓ^{φφ} and lensed vs
    unlensed C_ℓ bookkeeping. Future scope.
    """
    raise OutOfScopeError(
        "CMB lensing C_ℓ requires C_ℓ^{φφ} computation and "
        "unlensed→lensed mapping. Future scope, not in W10-series."
    )


def tensor_mode_contribution(*args, **kwargs):
    """Tensor-mode (primordial GW) contribution to C_ℓ^{TT/EE/BB}.
    Distinct from Bianchi I shear; requires r (tensor-to-scalar ratio)
    and tensor transfer functions. Future scope.
    """
    raise OutOfScopeError(
        "Tensor-mode primordial GW contribution is a distinct physics "
        "channel from Bianchi I shear and requires its own transfer "
        "function machinery (W11+ or dedicated prompt)."
    )
