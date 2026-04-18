"""bass/species/background_table.py (LB-1) — shared FLRW η-grid table.

Produces the ``FLRWBackgroundTable`` consumed by every species
background class. All species share one instance so queries at the
same η return a consistent (a, 𝓗, Θ) triple.

The table is built by **analytic quadrature** of the flat ΛCDM
Friedmann equation,

    H(a)² = H_0² [ Ω_r/a⁴ + Ω_m/a³ + Ω_Λ ]          (Kolb §3.1)

and

    η(a) = ∫_{a_start}^{a} da' / (a'² H(a'))           (Baumann §2.3)

with integrand taken on a geometric a-grid and trapezoidal cumulation.
This is preferable to reusing ``solve_bianchi_background`` because:

1. It yields ``a[-1] ≡ 1.0`` exactly (required for test T-22 with
   tolerance 1e-12).
2. It uses the species-layer ``SpeciesConstants`` directly, avoiding
   the off-by-a-few-percent Planck-parameter drift in the legacy
   ``_PLANCK18`` dict inside ``bass.background.einstein_bianchi``.
3. It needs no ``scipy.integrate.solve_ivp`` machinery for a one-
   dimensional analytic problem.

Reference: Baumann §2.3 (Friedmann); Kolb §3.1.
LB-1 remains background-only; dynamical integration enters in LB-5.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

import numpy as np
from scipy.interpolate import CubicSpline

from bass.species.constants import SpeciesConstants, default_constants


_Number = Union[float, np.ndarray]


def _H_over_H0(a: np.ndarray, c: SpeciesConstants) -> np.ndarray:
    """H(a)/H_0 for flat ΛCDM (Kolb §3.1).

    Fully analytic, no tilt / shear corrections at LB-1 scope.
    """
    return np.sqrt(
        c.Omega_r_0 / a ** 4
        + c.Omega_m_0 / a ** 3
        + c.Omega_Lambda_0
    )


@dataclass(frozen=True)
class FLRWBackgroundTable:
    """η-sampled flat ΛCDM background (a, H, 𝓗, Θ) on a shared grid.

    All arrays have length ``N = len(eta)`` and correspond to the same
    (a_i, η_i) pairs. The natural-units convention is

        H_mpc   = H / c_km_s           [Mpc⁻¹]
        calH    = a × H_mpc            [Mpc⁻¹]
        Theta   = 3 × H_mpc            [Mpc⁻¹]  (proper expansion scalar)

    ``H0_mpc`` is the Hubble parameter today in natural units, used by
    ``SpeciesBackgroundRegistry.friedmann_residual``.

    Reference: Baumann §2.3; Kolb §3.1.
    """
    eta: np.ndarray           # [Mpc], monotonically increasing, eta[-1] ≡ eta_today
    a: np.ndarray             # dimensionless, a[-1] ≡ 1.0 exactly
    z: np.ndarray             # 1/a − 1
    H_mpc: np.ndarray         # Mpc⁻¹
    calH_mpc: np.ndarray      # Mpc⁻¹  (𝓗 = aH)
    Theta: np.ndarray         # Mpc⁻¹  (Θ = 3H = 3𝓗/a)
    H0_mpc: float             # Mpc⁻¹
    constants: SpeciesConstants = field(compare=False)

    _spline_a: CubicSpline = field(repr=False, hash=False, compare=False)
    _spline_calH: CubicSpline = field(repr=False, hash=False, compare=False)
    _spline_Theta: CubicSpline = field(repr=False, hash=False, compare=False)

    @property
    def eta_today(self) -> float:
        """η_0 ≡ η at which a = 1 (last grid point by construction)."""
        return float(self.eta[-1])

    @property
    def eta_min(self) -> float:
        return float(self.eta[0])

    def _check_in_range(self, eta: np.ndarray) -> None:
        lo, hi = self.eta_min, self.eta_today
        # Allow tiny rounding on the boundaries (1e-9 × hi) without
        # triggering a ValueError — the species rho/p methods are
        # continuous so a sub-ULP excursion is physically meaningless.
        tol = max(abs(hi) * 1e-12, 1e-12)
        if np.any(eta < lo - tol) or np.any(eta > hi + tol):
            raise ValueError(
                f"η outside background table range "
                f"[{lo:.6e}, {hi:.6e}]: "
                f"got min={np.min(eta):.6e}, max={np.max(eta):.6e}"
            )

    def _interp(self, eta: _Number, spline: CubicSpline) -> _Number:
        arr = np.asarray(eta, dtype=np.float64)
        was_scalar = arr.ndim == 0
        arr1d = np.atleast_1d(arr)
        self._check_in_range(arr1d)
        # Clip to strict range after tolerance check, so spline isn't
        # evaluated outside the strict domain.
        arr_clipped = np.clip(arr1d, self.eta_min, self.eta_today)
        out = spline(arr_clipped)
        if was_scalar:
            return float(out[0])
        return out

    def ensure_in_range(self, eta: _Number) -> None:
        """Raise ``ValueError`` if any value of ``eta`` falls outside the
        tabulated domain. Used by species whose closed-form output does
        not otherwise touch the interpolators (Λ, CDM pressure).
        """
        arr = np.atleast_1d(np.asarray(eta, dtype=np.float64))
        self._check_in_range(arr)

    def interp_a(self, eta: _Number) -> _Number:
        """Scale factor a at arbitrary η via cubic spline."""
        return self._interp(eta, self._spline_a)

    def interp_calH(self, eta: _Number) -> _Number:
        """Conformal Hubble 𝓗 = aH at arbitrary η via cubic spline."""
        return self._interp(eta, self._spline_calH)

    def interp_Theta(self, eta: _Number) -> _Number:
        """Proper expansion scalar Θ = 3H at arbitrary η via cubic spline.

        Reference: Ellis §4.2; ``00_conventions.md §3``.
        """
        return self._interp(eta, self._spline_Theta)

    def eta_at_a(self, a_target: float) -> float:
        """Invert a(η) to find η such that a(η) = a_target.

        Uses the tabulated arrays (monotone a) directly; no root-find.
        """
        if a_target < self.a[0] or a_target > self.a[-1]:
            raise ValueError(
                f"a_target={a_target} outside table range "
                f"[{self.a[0]:.6e}, {self.a[-1]:.6e}]"
            )
        return float(np.interp(a_target, self.a, self.eta))


def build_flrw_background_table(
    *,
    constants: Optional[SpeciesConstants] = None,
    a_start: float = 1.0e-8,
    n_eta: int = 4000,
) -> FLRWBackgroundTable:
    """Construct the shared FLRW η-grid table via analytic quadrature.

    Parameters
    ----------
    constants : SpeciesConstants, optional
        Physical constants bundle. Defaults to ``default_constants()``
        (Planck 2018 + SSOT, flat closure).
    a_start : float
        Starting scale factor. 1e-8 gives z ≈ 1e8, deep in the
        radiation era but well before e⁺e⁻ annihilation.
    n_eta : int
        Grid resolution. 4000 log-spaced points over 8 decades gives
        ``Δ log a ≈ 2e-3``, comfortably finer than the recombination
        width (``00_conventions.md §10``).

    Returns
    -------
    FLRWBackgroundTable
        Shared, immutable. ``a[-1] = 1.0`` exactly.

    Reference: Baumann §2.3 (conformal time); Kolb §3.1 (Friedmann).
    """
    c = constants if constants is not None else default_constants()

    if a_start <= 0.0 or a_start >= 1.0:
        raise ValueError(
            f"a_start must be in (0, 1); got {a_start}"
        )
    if n_eta < 100:
        raise ValueError(
            f"n_eta must be ≥ 100 for adequate resolution; got {n_eta}"
        )

    # Geometric grid in a, endpoint inclusive at a=1.
    a_grid = np.geomspace(a_start, 1.0, n_eta, endpoint=True)

    H_over_H0 = _H_over_H0(a_grid, c)
    H0_mpc = c.H0_mpc
    H_mpc = H0_mpc * H_over_H0                 # Mpc⁻¹

    # dη/da = 1 / (a² H)  with H in Mpc⁻¹
    integrand = 1.0 / (a_grid ** 2 * H_mpc)

    # Trapezoidal cumulative integral; η(a_start) ≡ 0 by convention.
    eta = np.zeros_like(a_grid)
    da = np.diff(a_grid)
    eta[1:] = np.cumsum(0.5 * (integrand[1:] + integrand[:-1]) * da)

    z = 1.0 / a_grid - 1.0
    calH = a_grid * H_mpc
    Theta = 3.0 * H_mpc

    # Cubic spline interpolators — natural BCs for stability.
    spline_a = CubicSpline(eta, a_grid, bc_type="natural")
    spline_calH = CubicSpline(eta, calH, bc_type="natural")
    spline_Theta = CubicSpline(eta, Theta, bc_type="natural")

    return FLRWBackgroundTable(
        eta=eta,
        a=a_grid,
        z=z,
        H_mpc=H_mpc,
        calH_mpc=calH,
        Theta=Theta,
        H0_mpc=H0_mpc,
        constants=c,
        _spline_a=spline_a,
        _spline_calH=spline_calH,
        _spline_Theta=spline_Theta,
    )
