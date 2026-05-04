"""
bass/los/flrw_bessel_projector.py   (Week 9-01)
===============================================

FLRW line-of-sight (LOS) projector: integrates scalar-mode source
functions against spherical-Bessel kernels to produce temperature and
E-mode polarization transfer functions.

Physics
-------
Temperature scalar transfer (Seljak-Zaldarriaga 1996):

    Δ_ℓ^T(k) = ∫_0^{η_0} dη  S_T(k, η)  j_ℓ[k(η_0 - η)]

E-mode polarization transfer (Kamionkowski-Kosowsky-Stebbins 1997,
Zaldarriaga-Seljak 1997):

    Δ_ℓ^E(k) = ∫_0^{η_0} dη  S_E(k, η)  P^E_ℓ[k(η_0 - η)]

    P^E_ℓ(kr) = √[(ℓ-1)ℓ(ℓ+1)(ℓ+2)] · j_ℓ(kr) / (kr)^2      (ℓ ≥ 2)
              = 0                                              (ℓ < 2)

Source assembly
---------------
S_T(η) = g(η) · [Θ_0(η) + Ψ(η) + (1/4) Π(η)]      (SW + polter)
        + e^{-κ(η)} · [Ψ̇(η) + Φ̇(η)]               (integrated Sachs-Wolfe)
        + d/dη [g(η) · v_b(η)]                     (Doppler)

S_E(η) = -(√6/4) · g(η) · Π(η)                     (W8-03 polter)

Design contract
---------------
This module is a PROJECTOR/INTEGRATOR only. Source-term evolution
(Θ_0, Ψ, Φ̇+Ψ̇, v_b) is NOT solved here — caller supplies each as a
callable η → float. That keeps the Bessel machinery decoupled from
future temperature/potential evolution (scheduled W10+).

SILENT OMISSION OF ISW/DOPPLER IS PROHIBITED. The source-terms
dataclass requires all five callables. Use
`FLRWSourceTerms.with_sw_polter_only(...)` to make the absence of
ISW/Doppler explicit (they become zero callables, not silent None).

Scope (narrow, declared)
------------------------
IN scope
  * Spherical Bessel j_ℓ evaluation (scalar, vector, pre-table lookup)
  * E-mode projection factor with (kr)^(ℓ-2)/(2ℓ+1)!! Taylor small-kr limit
  * η-quadrature (trapezoid O(h²) + Simpson O(h⁴))
  * Assembly of full S_T with SW + ISW + Doppler + polter; S_E with polter
  * Single-k transfer function output Δ_ℓ^T(k), Δ_ℓ^E(k)
  * Sharp-visibility analytic cross-check (Gaussian g limit)
  * Bessel orthogonality 0.1 % cross-check
  * η-grid utilities for flat ΛCDM

OUT of scope (declared; raise OutOfScopeError)
  * Bianchi m-mixing matrix propagator                → W9-02
  * Full Θ_0, Ψ, Φ scalar-mode evolution              → W10+ (here: analytic fixtures only)
  * Multi-k production grid + C_ℓ aggregation         → W10-01
  * B-mode (FLRW: identically zero)                    → W11+ Bianchi tensor
  * CMB lensing potential                              → far future
  * FFT / Limber approximation                         → optimization pass

References
----------
- Seljak & Zaldarriaga 1996, ApJ 469, 437 (LOS formulation)
- Kamionkowski, Kosowsky, Stebbins 1997, PRD 55, 7368 (E/B polarization)
- Zaldarriaga & Seljak 1997, PRD 55, 1830 (all-sky CMB polarization)
- Lewis & Challinor 2006 (CAMB LOS implementation)
- W8-03 visibility_polter_source (Π and g·Π assembly)
- MASTER_PROMPT_LIST_bass_py_v1.2.md §4 W9-01
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Tuple, Union

import numpy as np
from scipy import special as scipy_special
from scipy.integrate import simpson as scipy_simpson

from bass.recombination.reionization import CosmologyForRecombination
from bass.transport.visibility_polter_source import (
    C_IN_MPC_PER_S,
    conformal_time_at_z,
)


# ============================================================================
# Section 0 — Type aliases and tiny helpers
# ============================================================================

EtaCallable = Callable[[Union[float, np.ndarray]], Union[float, np.ndarray]]

_SQRT6 = np.sqrt(6.0)


def _zero_callable(eta: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """Explicit zero-valued source. Used to make the absence of ISW or
    Doppler contributions deliberate (never silent-None)."""
    eta_arr = np.asarray(eta, dtype=float)
    return np.zeros_like(eta_arr) if eta_arr.ndim else 0.0


def constant_callable(value: float) -> EtaCallable:
    """Factory: returns a callable that is `value` for any η."""
    def _const(eta):
        eta_arr = np.asarray(eta, dtype=float)
        if eta_arr.ndim == 0:
            return float(value)
        return np.full_like(eta_arr, value)
    return _const


def _eta_derivative(values: np.ndarray, eta_grid: np.ndarray) -> np.ndarray:
    """Differentiate a sampled η-series.

    Uniform grids use the fourth-order five-point stencil, including
    one-sided fourth-order boundary rows. Non-uniform or very short grids
    retain NumPy's stable variable-spacing finite difference.
    """

    eta = np.asarray(eta_grid, dtype=float)
    arr = np.asarray(values, dtype=float)
    if eta.ndim != 1 or arr.shape != eta.shape:
        raise ValueError("values and eta_grid must be matching 1-D arrays")
    if eta.size < 2:
        raise ValueError("eta_grid must contain at least two samples")
    if np.any(~np.isfinite(eta)) or np.any(~np.isfinite(arr)):
        raise ValueError("cannot differentiate non-finite η/source samples")
    spacing = np.diff(eta)
    if np.any(spacing <= 0.0):
        raise ValueError("eta_grid must be strictly increasing")

    h = float(spacing[0])
    uniform = bool(np.allclose(spacing, h, rtol=1.0e-10, atol=1.0e-14))
    if (not uniform) or eta.size < 5:
        return np.gradient(arr, eta, edge_order=2 if eta.size >= 3 else 1)

    deriv = np.empty_like(arr)
    deriv[0] = (
        -25.0 * arr[0] + 48.0 * arr[1] - 36.0 * arr[2]
        + 16.0 * arr[3] - 3.0 * arr[4]
    ) / (12.0 * h)
    deriv[1] = (
        -3.0 * arr[0] - 10.0 * arr[1] + 18.0 * arr[2]
        - 6.0 * arr[3] + arr[4]
    ) / (12.0 * h)
    deriv[2:-2] = (
        arr[:-4] - 8.0 * arr[1:-3] + 8.0 * arr[3:-1] - arr[4:]
    ) / (12.0 * h)
    deriv[-2] = (
        3.0 * arr[-1] + 10.0 * arr[-2] - 18.0 * arr[-3]
        + 6.0 * arr[-4] - arr[-5]
    ) / (12.0 * h)
    deriv[-1] = (
        25.0 * arr[-1] - 48.0 * arr[-2] + 36.0 * arr[-3]
        - 16.0 * arr[-4] + 3.0 * arr[-5]
    ) / (12.0 * h)
    return deriv


# ============================================================================
# Section 1 — Configuration
# ============================================================================

_ALLOWED_QUADRATURES = ("trapezoid", "simpson")


@dataclass(frozen=True)
class FLRWBesselConfig:
    """Immutable LOS projector configuration.

    Parameters
    ----------
    ell_max : int
        Highest multipole computed. Output Δ_ℓ arrays have shape
        (ell_max + 1,) covering ℓ = 0 … ell_max. For the E-mode
        projector, ℓ < 2 entries are zero by construction.
    eta_0_mpc : float
        Conformal time at the observer today, in Mpc. Must be positive.
    quadrature : str
        'trapezoid' (default, O(h²)) or 'simpson' (O(h⁴)). Simpson
        requires an odd number of η-grid samples.
    bessel_kr_small_cutoff : float
        Threshold below which the E-mode projection uses a Taylor
        expansion of j_ℓ(kr)/(kr)² for numerical stability. Default
        1e-3 matches the regime where double-precision cancellation
        in (kr)² becomes noticeable.
    use_lookup : bool
        When True, caller must supply `lookup_kr_grid`. Defaults False
        (on-the-fly j_ℓ via scipy.special.spherical_jn).
    lookup_kr_grid : Optional[np.ndarray]
        Monotone kr values for pre-tabulating j_ℓ across the requested
        ell-range. Ignored when `use_lookup` is False.
    """
    ell_max: int
    eta_0_mpc: float
    quadrature: str = "trapezoid"
    bessel_kr_small_cutoff: float = 1.0e-3
    use_lookup: bool = False
    lookup_kr_grid: Optional[np.ndarray] = None

    def __post_init__(self) -> None:
        if not isinstance(self.ell_max, int) or self.ell_max < 0:
            raise ValueError(f"ell_max must be non-negative int, got {self.ell_max}")
        if not (np.isfinite(self.eta_0_mpc) and self.eta_0_mpc > 0):
            raise ValueError(
                f"eta_0_mpc must be finite and positive, got {self.eta_0_mpc}"
            )
        if self.quadrature not in _ALLOWED_QUADRATURES:
            raise ValueError(
                f"quadrature must be one of {_ALLOWED_QUADRATURES}, "
                f"got {self.quadrature!r}"
            )
        if self.bessel_kr_small_cutoff <= 0:
            raise ValueError(
                "bessel_kr_small_cutoff must be positive"
            )
        if self.use_lookup and self.lookup_kr_grid is None:
            raise ValueError(
                "use_lookup=True requires lookup_kr_grid to be supplied"
            )


# ============================================================================
# Section 2 — Spherical Bessel evaluation
# ============================================================================

def spherical_bessel_at(ell: int, kr: float) -> float:
    """j_ℓ(kr) at scalar kr via scipy.special.spherical_jn.

    Raises
    ------
    ValueError if ell < 0 or kr < 0 (negative-argument convention is
    j_ℓ(-x) = (-1)^ℓ j_ℓ(x); we require the caller to be explicit).
    """
    if ell < 0:
        raise ValueError(f"ell must be non-negative, got {ell}")
    if kr < 0:
        raise ValueError(
            f"kr must be non-negative; got {kr}. "
            "Use explicit sign handling via (-1)^ell if needed."
        )
    return float(scipy_special.spherical_jn(ell, kr))


def spherical_bessel_vector(ell: int, kr_array: np.ndarray) -> np.ndarray:
    """j_ℓ(kr) vectorized over an array of kr values."""
    if ell < 0:
        raise ValueError(f"ell must be non-negative, got {ell}")
    kr = np.asarray(kr_array, dtype=float)
    if np.any(kr < 0):
        raise ValueError("all kr values must be non-negative")
    return scipy_special.spherical_jn(ell, kr)


def bessel_lookup_table(
    ell_max: int, kr_grid: np.ndarray,
) -> np.ndarray:
    """Pre-compute j_ℓ(kr) for ℓ = 0 … ell_max on `kr_grid`.

    Returns
    -------
    table : ndarray, shape (ell_max + 1, len(kr_grid))
        `table[ell, i]` = j_ℓ(kr_grid[i]).
    """
    if ell_max < 0:
        raise ValueError(f"ell_max must be non-negative, got {ell_max}")
    kr = np.asarray(kr_grid, dtype=float)
    if np.any(kr < 0):
        raise ValueError("all kr_grid values must be non-negative")
    table = np.zeros((ell_max + 1, kr.size))
    for ell in range(ell_max + 1):
        table[ell] = scipy_special.spherical_jn(ell, kr)
    return table


# ============================================================================
# Section 3 — E-mode projection factor
# ============================================================================

def _double_factorial_odd(n: int) -> float:
    """(2n+1)!! for non-negative n. Pure integer; returned as float."""
    result = 1.0
    for k in range(1, 2 * n + 2, 2):
        result *= k
    return result


def e_mode_projection_factor(
    ell: int, kr: Union[float, np.ndarray],
    small_cutoff: float = 1.0e-3,
) -> Union[float, np.ndarray]:
    """E-mode LOS projection kernel P^E_ℓ(kr) = √[(ℓ-1)ℓ(ℓ+1)(ℓ+2)] · j_ℓ(kr) / (kr)².

    For ℓ < 2, returns 0 (spin-2 minimum). At small kr where (kr)² in
    the denominator amplifies floating-point noise, a Taylor expansion
    j_ℓ(x) ≈ x^ℓ / (2ℓ+1)!! is used, giving

        P^E_ℓ(kr) ≈ √[(ℓ-1)ℓ(ℓ+1)(ℓ+2)] · (kr)^(ℓ-2) / (2ℓ+1)!!

    which is finite for ℓ = 2 (constant) and vanishes as (kr)^(ℓ-2)
    for ℓ > 2.

    Parameters
    ----------
    ell : int
        Multipole. For ell < 2, the factor is identically zero.
    kr : float or ndarray
        k·(η_0 − η). Must be non-negative.
    small_cutoff : float
        Threshold below which the Taylor expansion is applied.
    """
    if ell < 0:
        raise ValueError(f"ell must be non-negative, got {ell}")
    if ell < 2:
        kr_arr = np.asarray(kr, dtype=float)
        return float(0.0) if kr_arr.ndim == 0 else np.zeros_like(kr_arr)

    # Spin-2 prefactor √[(ℓ-1)ℓ(ℓ+1)(ℓ+2)]
    prefactor = np.sqrt((ell - 1) * ell * (ell + 1) * (ell + 2))

    kr_arr = np.asarray(kr, dtype=float)
    if np.any(kr_arr < 0):
        raise ValueError("all kr values must be non-negative")

    scalar_input = (kr_arr.ndim == 0)
    kr_flat = np.atleast_1d(kr_arr)

    result = np.empty_like(kr_flat, dtype=float)
    small_mask = kr_flat < small_cutoff
    large_mask = ~small_mask

    if np.any(large_mask):
        kr_large = kr_flat[large_mask]
        jl_large = scipy_special.spherical_jn(ell, kr_large)
        result[large_mask] = prefactor * jl_large / (kr_large ** 2)

    if np.any(small_mask):
        # Taylor: j_ℓ(x) / x² ≈ x^(ℓ-2) / (2ℓ+1)!!
        denom = _double_factorial_odd(ell)
        kr_small = kr_flat[small_mask]
        if ell == 2:
            # Constant limit: j_2(x)/x² → 1/15 at x → 0
            result[small_mask] = prefactor / denom
        else:
            result[small_mask] = prefactor * (kr_small ** (ell - 2)) / denom

    return float(result[0]) if scalar_input else result


# ============================================================================
# Section 4 — Source-term contract (all-callables, no silent omissions)
# ============================================================================

@dataclass(frozen=True)
class FLRWSourceTerms:
    """Five required η-callables that drive the scalar LOS source.

    All slots are mandatory. Use the factory constructors to make any
    intentional zero explicit (e.g., `with_sw_polter_only` sets ISW
    and Doppler terms to the zero callable).

    Slots
    -----
    theta_0 : η → Θ_0(η)
        Temperature monopole amplitude. In a full treatment this is
        evolved by the photon fluid hierarchy (W10+).
    psi : η → Ψ(η)
        Newtonian-gauge potential amplitude. Evolves via Einstein
        equations (W10+). In W9-01 test fixtures, analytic MD-limit
        forms are used.
    phi_dot_plus_psi_dot : η → (Φ̇ + Ψ̇)(η)
        ISW driver. Non-zero during dark-energy era and (early) radiation
        era; zero in pure matter domination. REQUIRED — pass
        `_zero_callable` via `with_sw_polter_only(...)` if intentionally
        excluded.
    v_b : η → v_b(η)
        Baryon peculiar velocity at mode k. Non-zero at recombination;
        drives Doppler term via d/dη[g·v_b].
    pi : η → Π(η) = Θ_2(η) − √6 E_2(η)
        PSTF combined quadrupole source. In production, supplied by
        W8-03 `g_weighted_pi_pstf` composed with the Θ_2/E_2 evolution
        track. Appears in BOTH S_T (as Π/4) and S_E (as -(√6/4)Π).
    """
    theta_0: EtaCallable
    psi: EtaCallable
    phi_dot_plus_psi_dot: EtaCallable
    v_b: EtaCallable
    pi: EtaCallable

    @classmethod
    def with_all(
        cls,
        theta_0: EtaCallable,
        psi: EtaCallable,
        phi_dot_plus_psi_dot: EtaCallable,
        v_b: EtaCallable,
        pi: EtaCallable,
    ) -> "FLRWSourceTerms":
        """Full-physics factory: all five source callables required."""
        return cls(
            theta_0=theta_0, psi=psi,
            phi_dot_plus_psi_dot=phi_dot_plus_psi_dot,
            v_b=v_b, pi=pi,
        )

    @classmethod
    def with_sw_polter_only(
        cls,
        theta_0: EtaCallable,
        psi: EtaCallable,
        pi: EtaCallable,
    ) -> "FLRWSourceTerms":
        """Explicit-zero factory for SW + polter only.

        ISW and Doppler are set to `_zero_callable`. Use this ONLY when
        you have a deliberate reason to suppress those terms (e.g., a
        sharp-visibility analytic cross-check). Silent None is not
        available; this factory documents the omission in code.
        """
        return cls(
            theta_0=theta_0, psi=psi,
            phi_dot_plus_psi_dot=_zero_callable,
            v_b=_zero_callable, pi=pi,
        )

    @classmethod
    def with_isw_only(
        cls, phi_dot_plus_psi_dot: EtaCallable,
    ) -> "FLRWSourceTerms":
        """Isolation factory: only ISW active. Temperature monopole,
        potential, Doppler, and polter all zero. Used for ISW
        activation tests."""
        return cls(
            theta_0=_zero_callable, psi=_zero_callable,
            phi_dot_plus_psi_dot=phi_dot_plus_psi_dot,
            v_b=_zero_callable, pi=_zero_callable,
        )

    @classmethod
    def with_doppler_only(cls, v_b: EtaCallable) -> "FLRWSourceTerms":
        """Isolation factory: only Doppler term active."""
        return cls(
            theta_0=_zero_callable, psi=_zero_callable,
            phi_dot_plus_psi_dot=_zero_callable,
            v_b=v_b, pi=_zero_callable,
        )

    @classmethod
    def zeros(cls) -> "FLRWSourceTerms":
        """All-zero sources. Used for API-shape tests."""
        return cls(
            theta_0=_zero_callable, psi=_zero_callable,
            phi_dot_plus_psi_dot=_zero_callable,
            v_b=_zero_callable, pi=_zero_callable,
        )


# ============================================================================
# Section 5 — Source assembly (SW + ISW + Doppler + polter)
# ============================================================================

def build_temperature_source(
    eta_grid: np.ndarray,
    sources: FLRWSourceTerms,
    visibility_g: EtaCallable,
    kappa_of_eta: EtaCallable,
) -> np.ndarray:
    """Assemble S_T(η) on `eta_grid`.

        S_T = g · [Θ_0 + Ψ + Π/4]     (SW + polter)
             + e^{−κ} · [Ψ̇ + Φ̇]     (ISW)
             + d/dη [g · v_b]         (Doppler)

    Doppler derivative uses a fourth-order five-point finite difference on
    uniform η grids, with a variable-spacing finite-difference fallback for
    short or non-uniform grids.
    """
    eta_grid = np.asarray(eta_grid, dtype=float)
    if eta_grid.ndim != 1 or eta_grid.size < 2:
        raise ValueError("eta_grid must be 1-D with >= 2 entries")

    g_arr = np.asarray(visibility_g(eta_grid), dtype=float)
    kappa_arr = np.asarray(kappa_of_eta(eta_grid), dtype=float)
    theta0_arr = np.asarray(sources.theta_0(eta_grid), dtype=float)
    psi_arr = np.asarray(sources.psi(eta_grid), dtype=float)
    phi_psi_dot_arr = np.asarray(
        sources.phi_dot_plus_psi_dot(eta_grid), dtype=float,
    )
    vb_arr = np.asarray(sources.v_b(eta_grid), dtype=float)
    pi_arr = np.asarray(sources.pi(eta_grid), dtype=float)

    # SW + polter
    sw_polter = g_arr * (theta0_arr + psi_arr + 0.25 * pi_arr)
    # ISW: exp-damped potential derivative
    isw = np.exp(-kappa_arr) * phi_psi_dot_arr
    # Doppler: numerical derivative of g·v_b
    gvb = g_arr * vb_arr
    doppler = _eta_derivative(gvb, eta_grid)

    return sw_polter + isw + doppler


def build_polarization_source(
    eta_grid: np.ndarray,
    sources: FLRWSourceTerms,
    visibility_g: EtaCallable,
) -> np.ndarray:
    """Assemble S_E(η) = -(√6/4) g(η) Π(η) on `eta_grid`.

    Only the polter term contributes to scalar-mode E polarization;
    SW/ISW/Doppler are temperature-only. This assembly matches W8-03
    `g_weighted_pi_pstf` up to the spin-2 prefactor.
    """
    eta_grid = np.asarray(eta_grid, dtype=float)
    g_arr = np.asarray(visibility_g(eta_grid), dtype=float)
    pi_arr = np.asarray(sources.pi(eta_grid), dtype=float)
    return -(_SQRT6 / 4.0) * g_arr * pi_arr


def build_scalar_sources_pair(
    eta_grid: np.ndarray,
    sources: FLRWSourceTerms,
    visibility_g: EtaCallable,
    kappa_of_eta: EtaCallable,
) -> Tuple[np.ndarray, np.ndarray]:
    """Assemble ``(S_T, S_E)`` together on one η grid.

    This is the paired equivalent of ``build_temperature_source`` plus
    ``build_polarization_source``. It evaluates the shared visibility
    and quadrupole source once and then forms both arrays with the same
    algebra, so the result is identical for pure source callables while
    avoiding duplicate interpolation in production LoS runs.
    """
    eta_grid = np.asarray(eta_grid, dtype=float)
    if eta_grid.ndim != 1 or eta_grid.size < 2:
        raise ValueError("eta_grid must be 1-D with >= 2 entries")

    g_arr = np.asarray(visibility_g(eta_grid), dtype=float)
    kappa_arr = np.asarray(kappa_of_eta(eta_grid), dtype=float)
    theta0_arr = np.asarray(sources.theta_0(eta_grid), dtype=float)
    psi_arr = np.asarray(sources.psi(eta_grid), dtype=float)
    phi_psi_dot_arr = np.asarray(
        sources.phi_dot_plus_psi_dot(eta_grid), dtype=float,
    )
    vb_arr = np.asarray(sources.v_b(eta_grid), dtype=float)
    pi_arr = np.asarray(sources.pi(eta_grid), dtype=float)

    sw_polter = g_arr * (theta0_arr + psi_arr + 0.25 * pi_arr)
    isw = np.exp(-kappa_arr) * phi_psi_dot_arr
    doppler = _eta_derivative(g_arr * vb_arr, eta_grid)
    source_T = sw_polter + isw + doppler
    source_E = -(_SQRT6 / 4.0) * g_arr * pi_arr
    return source_T, source_E


# ============================================================================
# Section 6 — Quadrature wrapper
# ============================================================================

def _integrate(
    integrand: np.ndarray, eta_grid: np.ndarray, quadrature: str,
) -> float:
    """Dispatch to the requested quadrature scheme."""
    if quadrature == "trapezoid":
        return float(np.trapezoid(integrand, eta_grid))
    if quadrature == "simpson":
        if eta_grid.size % 2 == 0:
            raise ValueError(
                "Simpson's rule requires an odd number of samples "
                f"(even-length input: {eta_grid.size})"
            )
        return float(scipy_simpson(integrand, x=eta_grid))
    raise ValueError(f"unknown quadrature {quadrature!r}")


def _integrate_rows(
    integrand_rows: np.ndarray,
    eta_grid: np.ndarray,
    quadrature: str,
) -> np.ndarray:
    """Apply the configured η-quadrature to rows shaped ``(n_row, n_eta)``."""
    rows = np.asarray(integrand_rows, dtype=float)
    if rows.ndim != 2:
        raise ValueError("integrand_rows must be 2-D with shape (n_row, n_eta)")
    if rows.shape[1] != eta_grid.size:
        raise ValueError(
            "integrand row width must match eta_grid size "
            f"({rows.shape[1]} != {eta_grid.size})"
        )
    if quadrature == "trapezoid":
        return np.asarray(np.trapezoid(rows, x=eta_grid, axis=1), dtype=float)
    if quadrature == "simpson":
        if eta_grid.size % 2 == 0:
            raise ValueError(
                "Simpson's rule requires an odd number of samples "
                f"(even-length input: {eta_grid.size})"
            )
        return np.asarray(scipy_simpson(rows, x=eta_grid, axis=1), dtype=float)
    raise ValueError(f"unknown quadrature {quadrature!r}")


# ============================================================================
# Section 7 — Transfer function projectors
# ============================================================================

def project_temperature_transfer(
    k: float,
    source_T_array: np.ndarray,
    eta_grid: np.ndarray,
    config: FLRWBesselConfig,
) -> np.ndarray:
    """Compute Δ_ℓ^T(k) = ∫ dη S_T(η) j_ℓ[k(η_0 − η)]  for ℓ = 0 … ell_max.

    Parameters
    ----------
    k : float
        Wavenumber in 1/Mpc (must be non-negative).
    source_T_array : ndarray, shape (N,)
        S_T(η) sampled on `eta_grid`. Caller provides this via
        `build_temperature_source` or equivalent.
    eta_grid : ndarray, shape (N,)
        Monotonically increasing η samples. Values must satisfy
        0 ≤ η ≤ config.eta_0_mpc.
    config : FLRWBesselConfig

    Returns
    -------
    Delta_T : ndarray, shape (ell_max + 1,)
        Temperature transfer coefficients Δ_ℓ^T(k), ℓ = 0 … ell_max.
    """
    if k < 0 or not np.isfinite(k):
        raise ValueError(f"k must be non-negative finite, got {k}")
    eta_grid = np.asarray(eta_grid, dtype=float)
    source_T_array = np.asarray(source_T_array, dtype=float)
    if source_T_array.shape != eta_grid.shape:
        raise ValueError(
            "source_T_array and eta_grid must have matching shapes"
        )
    if np.any(eta_grid < 0) or np.any(eta_grid > config.eta_0_mpc):
        raise ValueError(
            f"eta_grid must lie in [0, {config.eta_0_mpc}]"
        )
    if not np.all(np.diff(eta_grid) >= 0):
        raise ValueError("eta_grid must be monotonically non-decreasing")

    kr_array = k * (config.eta_0_mpc - eta_grid)

    Delta_T = np.zeros(config.ell_max + 1, dtype=float)
    for ell in range(config.ell_max + 1):
        jl = spherical_bessel_vector(ell, kr_array)
        integrand = source_T_array * jl
        Delta_T[ell] = _integrate(integrand, eta_grid, config.quadrature)
    return Delta_T


def project_polarization_transfer(
    k: float,
    source_E_array: np.ndarray,
    eta_grid: np.ndarray,
    config: FLRWBesselConfig,
) -> np.ndarray:
    """Compute Δ_ℓ^E(k) = ∫ dη S_E(η) P^E_ℓ[k(η_0 − η)]  for ℓ = 0 … ell_max.

    ℓ < 2 entries are identically zero (spin-2 minimum).
    """
    if k < 0 or not np.isfinite(k):
        raise ValueError(f"k must be non-negative finite, got {k}")
    eta_grid = np.asarray(eta_grid, dtype=float)
    source_E_array = np.asarray(source_E_array, dtype=float)
    if source_E_array.shape != eta_grid.shape:
        raise ValueError(
            "source_E_array and eta_grid must have matching shapes"
        )
    if np.any(eta_grid < 0) or np.any(eta_grid > config.eta_0_mpc):
        raise ValueError(
            f"eta_grid must lie in [0, {config.eta_0_mpc}]"
        )

    kr_array = k * (config.eta_0_mpc - eta_grid)

    Delta_E = np.zeros(config.ell_max + 1, dtype=float)
    for ell in range(2, config.ell_max + 1):
        proj = e_mode_projection_factor(
            ell, kr_array, small_cutoff=config.bessel_kr_small_cutoff,
        )
        integrand = source_E_array * proj
        Delta_E[ell] = _integrate(integrand, eta_grid, config.quadrature)
    return Delta_E


def project_scalar_transfer_pair(
    k: float,
    source_T_array: np.ndarray,
    source_E_array: np.ndarray,
    eta_grid: np.ndarray,
    config: FLRWBesselConfig,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute scalar Δ_ℓ^T and Δ_ℓ^E together for one k.

    This is a physics-preserving fast path for callers that need both
    transfer arrays on the same η grid. It validates the shared inputs
    once, builds ``kr = k(η_0-η)`` once, and reuses each ``j_ℓ(kr)``
    evaluation for the temperature integral and the large-kr part of
    the E-mode kernel. The returned arrays use the same quadrature as
    calling ``project_temperature_transfer`` and
    ``project_polarization_transfer`` separately; row-vectorized
    accumulation can differ from the separate path only at double
    precision round-off.
    """
    if k < 0 or not np.isfinite(k):
        raise ValueError(f"k must be non-negative finite, got {k}")
    eta_grid = np.asarray(eta_grid, dtype=float)
    source_T_array = np.asarray(source_T_array, dtype=float)
    source_E_array = np.asarray(source_E_array, dtype=float)
    if source_T_array.shape != eta_grid.shape:
        raise ValueError("source_T_array and eta_grid must have matching shapes")
    if source_E_array.shape != eta_grid.shape:
        raise ValueError("source_E_array and eta_grid must have matching shapes")
    if np.any(eta_grid < 0) or np.any(eta_grid > config.eta_0_mpc):
        raise ValueError(f"eta_grid must lie in [0, {config.eta_0_mpc}]")
    if not np.all(np.diff(eta_grid) >= 0):
        raise ValueError("eta_grid must be monotonically non-decreasing")

    kr_array = k * (config.eta_0_mpc - eta_grid)
    ell_values = np.arange(config.ell_max + 1, dtype=int)[:, None]
    jl_table = scipy_special.spherical_jn(ell_values, kr_array[None, :])

    delta_T = np.zeros(config.ell_max + 1, dtype=float)
    delta_T[:] = _integrate_rows(
        source_T_array[None, :] * jl_table,
        eta_grid,
        config.quadrature,
    )

    delta_E = np.zeros(config.ell_max + 1, dtype=float)
    if config.ell_max >= 2:
        proj = np.zeros_like(jl_table, dtype=float)
        small_mask = kr_array < config.bessel_kr_small_cutoff
        large_mask = ~small_mask
        ell_arr = np.arange(2, config.ell_max + 1, dtype=float)
        prefactors = np.sqrt(
            (ell_arr - 1.0) * ell_arr * (ell_arr + 1.0) * (ell_arr + 2.0)
        )
        if np.any(large_mask):
            kr_large = kr_array[large_mask]
            proj[2:, large_mask] = (
                prefactors[:, None]
                * jl_table[2:, large_mask]
                / (kr_large[None, :] ** 2)
            )
        if np.any(small_mask):
            kr_small = kr_array[small_mask]
            for ell in range(2, config.ell_max + 1):
                prefactor = prefactors[ell - 2]
                denom = _double_factorial_odd(ell)
                if ell == 2:
                    proj[ell, small_mask] = prefactor / denom
                else:
                    proj[ell, small_mask] = (
                        prefactor * (kr_small ** (ell - 2)) / denom
                    )
        delta_E[2:] = _integrate_rows(
            source_E_array[None, :] * proj[2:],
            eta_grid,
            config.quadrature,
        )

    return delta_T, delta_E


# ============================================================================
# Section 8 — W8-03 convenience integration
# ============================================================================

def project_polarization_transfer_from_pi_callable(
    k: float,
    pi_of_eta: EtaCallable,
    g_of_eta: EtaCallable,
    eta_grid: np.ndarray,
    config: FLRWBesselConfig,
) -> np.ndarray:
    """Convenience wrapper: build S_E = -(√6/4) g(η) Π(η) and project.

    Intended for callers who already have Π(η) (the W8-03 combined
    source) and a visibility function g(η) — typically from
    `VisibilityPolterConfig.recomb_interp.query_visibility` composed
    with a z ↔ η map. This avoids the `FLRWSourceTerms` boilerplate
    when only E-mode polter propagation matters.
    """
    eta_grid = np.asarray(eta_grid, dtype=float)
    g_arr = np.asarray(g_of_eta(eta_grid), dtype=float)
    pi_arr = np.asarray(pi_of_eta(eta_grid), dtype=float)
    S_E = -(_SQRT6 / 4.0) * g_arr * pi_arr
    return project_polarization_transfer(k, S_E, eta_grid, config)


# ============================================================================
# Section 9 — Analytic cross-checks
# ============================================================================

def sachs_wolfe_analytic_transfer(
    k: float,
    eta_star_mpc: float,
    theta0_plus_psi_at_star: float,
    config: FLRWBesselConfig,
) -> np.ndarray:
    """Sharp-visibility limit: Δ_ℓ^T(k) = [Θ_0 + Ψ]_* · j_ℓ[k(η_0 − η_*)].

    In the limit g(η) → δ(η − η_*), Π = 0, ISW = 0, Doppler = 0, the
    temperature LOS integral collapses to this exact expression. Used
    as the analytic reference that `project_temperature_transfer`
    must recover when fed a narrow-Gaussian g centered on η_*.
    """
    if not np.isfinite(eta_star_mpc) or eta_star_mpc <= 0:
        raise ValueError("eta_star_mpc must be positive finite")
    if eta_star_mpc >= config.eta_0_mpc:
        raise ValueError("eta_star_mpc must be < eta_0_mpc")

    kr_star = k * (config.eta_0_mpc - eta_star_mpc)
    Delta_T = np.zeros(config.ell_max + 1, dtype=float)
    for ell in range(config.ell_max + 1):
        Delta_T[ell] = theta0_plus_psi_at_star * spherical_bessel_at(
            ell, kr_star,
        )
    return Delta_T


def bessel_sum_rule(x: float, ell_max: int) -> float:
    """Partial Bessel sum Σ_{ℓ=0}^{ell_max} (2ℓ+1) j_ℓ²(x).

    Identity (completeness of spherical harmonics expansion):

        Σ_{ℓ=0}^{∞} (2ℓ+1) j_ℓ²(x) = 1     for all x ≥ 0.

    For fixed x, partial sums converge quickly once ell_max > x. This
    is a PROPER (finite, closed-form) Bessel identity — unlike the
    continuum orthogonality ∫ k² j_ℓ² dk which is δ-distributional
    and does not admit an unambiguous finite-r identity.

    Returns the partial sum; compare against 1.0.
    """
    if x < 0 or ell_max < 0:
        raise ValueError("x and ell_max must be non-negative")
    total = 0.0
    for ell in range(ell_max + 1):
        jl = scipy_special.spherical_jn(ell, x)
        total += (2 * ell + 1) * jl * jl
    return float(total)


# ============================================================================
# Section 10 — η-grid utilities (flat ΛCDM)
# ============================================================================

def build_eta_grid_linear(
    eta_min_mpc: float, eta_max_mpc: float, n_points: int,
) -> np.ndarray:
    """Uniformly spaced η samples on [eta_min, eta_max]. Length = n_points.

    For Simpson's rule, pass an odd `n_points` (the projector will
    raise otherwise).
    """
    if n_points < 2:
        raise ValueError("n_points >= 2 required")
    if not (0 <= eta_min_mpc < eta_max_mpc):
        raise ValueError("0 <= eta_min < eta_max required")
    return np.linspace(eta_min_mpc, eta_max_mpc, n_points)


def build_eta_grid_log_in_z(
    cosmology: CosmologyForRecombination,
    z_lower: float = 0.0,
    z_upper: float = 2500.0,
    n_points: int = 401,
) -> np.ndarray:
    """η-grid that is log-spaced in (1+z), converted to η(z) via the
    cosmology's H(z).

    Log-spacing in (1+z) concentrates samples near recombination
    where the visibility function peaks, while keeping the total
    sample count modest. Returns η values in ascending order (smallest
    at high z, largest at z_lower).

    Parameters
    ----------
    cosmology : CosmologyForRecombination
        Provides H(z) for the flat-ΛCDM η(z) integration.
    z_lower, z_upper : float
        Redshift range endpoints.
    n_points : int
        Number of samples. Use an odd value if Simpson's rule will be used.
    """
    if z_lower < 0 or z_upper <= z_lower:
        raise ValueError("0 ≤ z_lower < z_upper required")
    log1pz = np.linspace(
        np.log(1.0 + z_upper), np.log(1.0 + z_lower), n_points,
    )
    z_samples = np.exp(log1pz) - 1.0
    # Convert each z to η via `conformal_time_at_z`
    eta_vals = np.array([
        conformal_time_at_z(z, cosmology, z_upper=max(z_upper * 2.0, 1.0e4))
        for z in z_samples
    ])
    # η is monotone increasing as z decreases: sort ascending
    order = np.argsort(eta_vals)
    return eta_vals[order]


# ============================================================================
# Section 11 — Physical sign assertions (v1.2 pattern)
# ============================================================================

def assert_sw_sign_at_low_ell(
    Delta_T: np.ndarray, theta0_plus_psi_sign: int,
) -> None:
    """At low ℓ with a narrow visibility, sign(Δ_ℓ^T) should track
    sign(Θ_0 + Ψ) at the surface of last scattering (for the dominant
    j_ℓ(kr_*) sign)."""
    if theta0_plus_psi_sign not in (-1, 0, +1):
        raise ValueError("theta0_plus_psi_sign must be ±1 or 0")
    if theta0_plus_psi_sign == 0:
        return  # no sign to check
    if Delta_T.size < 3:
        return
    # Check ℓ=0 (j_0(x) = sin(x)/x > 0 for small positive x)
    if theta0_plus_psi_sign > 0 and Delta_T[0] < 0:
        raise AssertionError(
            f"Δ_0^T has wrong sign for positive Θ_0+Ψ: {Delta_T[0]:.3e}"
        )
    if theta0_plus_psi_sign < 0 and Delta_T[0] > 0:
        raise AssertionError(
            f"Δ_0^T has wrong sign for negative Θ_0+Ψ: {Delta_T[0]:.3e}"
        )


def assert_e_mode_vanishes_for_ell_lt_2(Delta_E: np.ndarray) -> None:
    """The E-mode transfer must be identically zero for ℓ < 2."""
    if Delta_E.size >= 1 and Delta_E[0] != 0.0:
        raise AssertionError(f"Δ_0^E = {Delta_E[0]:.3e}, must be 0")
    if Delta_E.size >= 2 and Delta_E[1] != 0.0:
        raise AssertionError(f"Δ_1^E = {Delta_E[1]:.3e}, must be 0")


def assert_transfer_finite_on_grid(Delta: np.ndarray) -> None:
    """Transfer function must be finite (no NaN/inf leakage from quadrature)."""
    if not np.all(np.isfinite(Delta)):
        bad = np.where(~np.isfinite(Delta))[0]
        raise AssertionError(
            f"non-finite entries in transfer function at ℓ ∈ {bad.tolist()}"
        )


# ============================================================================
# Section 12 — Convergence diagnostic
# ============================================================================

def convergence_halving_deta(
    k: float,
    source_T_fn: Callable[[np.ndarray], np.ndarray],
    eta_min_mpc: float, eta_max_mpc: float,
    n_points_coarse: int,
    config: FLRWBesselConfig,
) -> float:
    """Return max_ℓ |Δ_ℓ^T(fine) − Δ_ℓ^T(coarse)| / max_ℓ |Δ_ℓ^T(fine)|.

    Builds the coarse grid (`n_points_coarse` uniform samples), the
    fine grid (2·n_points_coarse − 1 samples → halved dη), computes
    both transfer arrays, and returns the relative change.

    For trapezoidal quadrature this should decay as O(dη²); for
    Simpson's rule as O(dη⁴).
    """
    coarse = build_eta_grid_linear(eta_min_mpc, eta_max_mpc, n_points_coarse)
    fine = build_eta_grid_linear(
        eta_min_mpc, eta_max_mpc, 2 * n_points_coarse - 1,
    )
    D_c = project_temperature_transfer(
        k, source_T_fn(coarse), coarse, config,
    )
    D_f = project_temperature_transfer(
        k, source_T_fn(fine), fine, config,
    )
    max_fine = np.max(np.abs(D_f))
    if max_fine == 0.0:
        return 0.0
    return float(np.max(np.abs(D_f - D_c)) / max_fine)


# ============================================================================
# Section 13 — Scope guards (deferred features)
# ============================================================================

class OutOfScopeError(NotImplementedError):
    """Raised when a caller requests machinery beyond W9-01."""


def bianchi_m_mixing(*args, **kwargs):
    """Not implemented in W9-01; scheduled for W9-02."""
    raise OutOfScopeError(
        "bianchi_m_mixing requires the matrix propagator (W9-02)"
    )


def full_scalar_mode_evolution(*args, **kwargs):
    """Not implemented in W9-01; Θ_0/Ψ/Φ full evolution is W10+."""
    raise OutOfScopeError(
        "full scalar-mode evolution (Θ_0, Ψ, Φ) is W10+; W9-01 "
        "accepts these as callable inputs but does not compute them"
    )


def compute_c_ell(*args, **kwargs):
    """Not implemented in W9-01; multi-k integration is W10-01."""
    raise OutOfScopeError(
        "compute_c_ell requires multi-k grid + P(k) (W10-01)"
    )


def b_mode_transfer(*args, **kwargs):
    """FLRW: B ≡ 0. Bianchi tensor-sector B-modes are W11+."""
    raise OutOfScopeError(
        "B-mode transfer is identically zero in FLRW; "
        "Bianchi tensor sector is W11+"
    )
