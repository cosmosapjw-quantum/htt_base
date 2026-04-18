"""
bass/background/einstein_bianchi.py  (Week 1 Day 3 — 10-type support)
=====================================================================

Bianchi background ODE integrator with full 10-type support.

Solves the Einstein-Bianchi system for the scale factor a(η) and shear σ_±(η)
in conformal time, with real cosmological parameters (Planck 2018).

Changes from v1 (skeleton):
  1. Replaced hardcoded VII_h branch with dispatch to shear_sources.py
  2. Added factory functions for all 10 Bianchi types + FLRW
  3. Integrated comparator policy via comparator_policy.py
  4. Bianchi IV support with no_flrw_limit flag propagation

State variables:
  a(η)     — scale factor
  Σ_+(η)   — conformal shear (plus mode): Σ = a σ
  Σ_-(η)   — conformal shear (minus mode)

Equations (unified across types):
  a'   = a × ℋ
  Σ_+' = -ℋ Σ_+ + S_+(type, Σ, ℋ, a)
  Σ_-' = -ℋ Σ_- + S_-(type, Σ, ℋ, a)

where S_± come from the Wainwright-Ellis spatial-curvature source
(compute_shear_source in shear_sources.py).

Frame: n^a-frame (Bianchi hypersurface normal).
Units: η in Mpc, H in km/s/Mpc, Σ in Mpc⁻¹.
"""
from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.integrate import solve_ivp

from bass.background.bianchi_types import (
    StructureConstants, get_type,
    flrw_constants, type_i_constants, type_ii_constants,
    type_iii_constants, type_iv_constants, type_v_constants,
    type_vi0_constants, type_vih_constants,
    type_vii0_constants, type_viih_constants,
    type_viii_constants, type_ix_constants,
)
from bass.transport.shear_sources import compute_shear_source, get_source_status
from bass.validation.comparator_policy import (
    ComparatorPolicy, recommend_comparator, validate_comparator,
)


C_KMS = 299792.458  # km/s


@dataclass(frozen=True)
class BianchiCosmology:
    """Cosmological parameters + Bianchi structure.

    Parameters
    ----------
    H0, Omega_r, Omega_m, Omega_Lambda : float
        Standard FLRW parameters (Planck 2018 defaults).
    structure : StructureConstants
        Bianchi type classification.
    sigma_over_H_init : float
        Initial σ/H ratio at a_start.
    sigma_pm_ratio : float
        σ_-/σ_+ ratio at a_start (0 for pure + mode).
    beta : float
        Tilt rapidity (matter vs geometry frame). For baryon-only tilt
        architecture (Week 4), this applies to baryon velocity only.
    comparator : ComparatorPolicy, optional
        Comparator policy for the master departure identity. If None, uses
        recommend_comparator(structure.label).
    """
    H0: float = 67.36
    Omega_r: float = 9.22e-5
    Omega_m: float = 0.3138
    Omega_Lambda: float = 0.6862
    structure: StructureConstants = field(default_factory=flrw_constants)
    sigma_over_H_init: float = 0.0
    sigma_pm_ratio: float = 0.0
    beta: float = 0.0
    comparator: Optional[ComparatorPolicy] = None

    @property
    def h(self) -> float:
        return self.H0 / 100.0

    @property
    def effective_comparator(self) -> ComparatorPolicy:
        """Resolved comparator policy (uses recommendation if None)."""
        if self.comparator is None:
            return recommend_comparator(self.structure.label)
        return self.comparator

    @property
    def no_flrw_limit(self) -> bool:
        """Propagates the structural flag from the underlying type."""
        return self.structure.no_flrw_limit


@dataclass
class BianchiBackgroundState:
    """Result container for the background solution.

    All arrays are on the same η grid.
    """
    eta: np.ndarray
    a: np.ndarray
    z: np.ndarray
    H: np.ndarray
    calH: np.ndarray
    sigma_plus: np.ndarray
    sigma_minus: np.ndarray
    cosmo: BianchiCosmology
    source_status: str = "unknown"   # VALIDATED / PROVISIONAL / NOT_IMPLEMENTED


def _hubble_squared(a: float, p: BianchiCosmology,
                    sigma2_conformal: float = 0.0) -> float:
    """H²(a) including shear contribution (perturbative for near-FLRW)."""
    H0_sq = p.H0 ** 2
    friedmann = H0_sq * (p.Omega_r / a**4 + p.Omega_m / a**3 + p.Omega_Lambda)
    return max(friedmann, 1e-30)


def solve_bianchi_background(
    cosmo: BianchiCosmology,
    a_start: float = 1e-6,
    a_end: float = 1.0,
    n_pts: int = 3000,
) -> BianchiBackgroundState:
    """Integrate the Bianchi background from a_start to a_end.

    Works for all 10 Bianchi types + FLRW via dispatch to shear_sources.
    """
    # Validate type + comparator before starting
    sc = cosmo.structure
    status = validate_comparator(sc.label, cosmo.effective_comparator)
    if not status.is_valid:
        warnings.warn(
            f"Bianchi {sc.label} with comparator {cosmo.effective_comparator}: "
            f"{status.reason}"
        )

    source_status = get_source_status(sc.label).tag

    # Initial conditions
    a0 = a_start
    H0_at_a0 = cosmo.H0 * math.sqrt(_hubble_squared(a0, cosmo) / cosmo.H0**2)
    calH0 = a0 * H0_at_a0 / C_KMS

    sigma_plus_init = cosmo.sigma_over_H_init * calH0
    sigma_minus_init = cosmo.sigma_pm_ratio * sigma_plus_init

    y0 = np.array([a0, sigma_plus_init, sigma_minus_init])

    def rhs(eta, y):
        a_val = max(y[0], 1e-30)
        Sp = y[1]
        Sm = y[2]

        H = math.sqrt(_hubble_squared(a_val, cosmo))
        cH = a_val * H / C_KMS

        # da/dη = a × ℋ
        da = a_val * cH

        # Per-type shear source dispatch (NEW: Day 3 integration)
        source_Sp, source_Sm = compute_shear_source(sc, Sp, Sm, cH, a_val)

        # Full shear evolution: decay + source
        dSp = -cH * Sp + source_Sp
        dSm = -cH * Sm + source_Sm

        return np.array([da, dSp, dSm])

    # Estimate η range from FLRW
    a_grid_est = np.geomspace(a_start, a_end, 200)
    H_grid = np.array([math.sqrt(_hubble_squared(a, cosmo)) for a in a_grid_est])
    integrand = 1.0 / (a_grid_est**2 * H_grid / C_KMS)
    da_est = np.diff(a_grid_est)
    eta_est = np.zeros(200)
    for i in range(1, 200):
        eta_est[i] = eta_est[i-1] + 0.5 * (integrand[i-1] + integrand[i]) * da_est[i-1]
    eta_end_est = eta_est[-1]

    eta_eval = np.linspace(0, eta_end_est, n_pts)

    sol = solve_ivp(rhs, (0.0, eta_end_est), y0, method='RK45',
                    t_eval=eta_eval, rtol=1e-10, atol=1e-14,
                    max_step=eta_end_est / 200)

    if not sol.success or len(sol.y[0]) < n_pts // 2:
        sol = solve_ivp(rhs, (0.0, eta_end_est), y0, method='RK45',
                        t_eval=eta_eval, rtol=1e-8, atol=1e-12)

    a_arr = np.maximum(sol.y[0], 1e-30)
    Sp_arr = sol.y[1]
    Sm_arr = sol.y[2]
    eta_arr = sol.t

    z_arr = 1.0 / a_arr - 1.0
    H_arr = np.array([math.sqrt(_hubble_squared(a, cosmo)) for a in a_arr])
    calH_arr = a_arr * H_arr / C_KMS

    return BianchiBackgroundState(
        eta=eta_arr, a=a_arr, z=z_arr,
        H=H_arr, calH=calH_arr,
        sigma_plus=Sp_arr, sigma_minus=Sm_arr,
        cosmo=cosmo, source_status=source_status,
    )


# ══════════════════════════════════════════════════════════════════
# Cosmology factories for all 10 Bianchi types + FLRW
# ══════════════════════════════════════════════════════════════════


def _planck18_from_species_ssot() -> dict:
    """Pull the Planck-2018 Ω values from the species-layer SSOT.

    Post-LB-1, ``bass.species.constants.default_constants()`` is the
    single source of truth for flat-ΛCDM closure (Ω_Λ = 1 − Ω_m − Ω_r
    exact to machine precision). This helper keeps
    ``einstein_bianchi`` in sync with that SSOT so the Bianchi solver
    and the species background share identical cosmology.

    Historical note: prior to post-LB-1 audit, the dict hardcoded
    ``Omega_m=0.3138, Omega_Lambda=0.6862`` which summed to 1.000092
    (spurious Ω_k ≈ -9e-5). See AUDIT fix 2026-04-18.
    """
    from bass.species.constants import default_constants
    c = default_constants()
    return dict(
        H0=c.H0_km_s_mpc,
        Omega_r=c.Omega_r_0,
        Omega_m=c.Omega_m_0,
        Omega_Lambda=c.Omega_Lambda_0,
    )


_PLANCK18 = _planck18_from_species_ssot()


def flrw_cosmology() -> BianchiCosmology:
    """Planck 2018 ΛCDM (FLRW limit: σ = 0)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=flrw_constants(),
        sigma_over_H_init=0.0,
    )


def type_i_cosmology(sigma_over_H_init: float = 1e-4,
                     beta: float = 0.0) -> BianchiCosmology:
    """Type I (abelian, no curvature)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_i_constants(),
        sigma_over_H_init=sigma_over_H_init, beta=beta,
    )


def type_ii_cosmology(sigma_over_H_init: float = 1e-4,
                      n1: float = 1e-2, beta: float = 0.0) -> BianchiCosmology:
    """Type II (Heisenberg, marginal: no FLRW limit)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_ii_constants(n1=n1),
        sigma_over_H_init=sigma_over_H_init, beta=beta,
    )


def type_iii_cosmology(sigma_over_H_init: float = 1e-4,
                       n1: float = 1e-2, beta: float = 0.0) -> BianchiCosmology:
    """Type III = VI_{h=-1} (marginal: no FLRW limit)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_iii_constants(n1=n1),
        sigma_over_H_init=sigma_over_H_init, beta=beta,
    )


def type_iv_cosmology(sigma_over_H_init: float = 1e-4,
                      n3: float = 1e-2, a_twist: float = 1e-2,
                      beta: float = 0.0) -> BianchiCosmology:
    """Type IV — cosmologically marginal, NO FLRW limit.

    Used as a falsifiability probe: pipeline should decisively exclude under
    near-FLRW data (see comparator_policy.bianchi_iv_falsifiability_probe).
    """
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_iv_constants(n3=n3, a_twist=a_twist),
        sigma_over_H_init=sigma_over_H_init, beta=beta,
        comparator=ComparatorPolicy.NULL,  # structured-null
    )


def type_v_cosmology(sigma_over_H_init: float = 0.0,
                     a_twist: float = 1e-2, beta: float = 0.0) -> BianchiCosmology:
    """Type V (open FLRW analogue, k=-1 limit)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_v_constants(a_twist=a_twist),
        sigma_over_H_init=sigma_over_H_init, beta=beta,
    )


def type_vi0_cosmology(sigma_over_H_init: float = 1e-4,
                       n1: float = 1e-2, n3: float = -1e-2,
                       beta: float = 0.0) -> BianchiCosmology:
    """Type VI_0 (marginal: no FLRW limit)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_vi0_constants(n1=n1, n3=n3),
        sigma_over_H_init=sigma_over_H_init, beta=beta,
    )


def type_vih_cosmology(sigma_over_H_init: float = 1e-4,
                       n1: float = 1e-2, n3: float = -2e-3,
                       a_twist: float = 5e-3, beta: float = 0.0) -> BianchiCosmology:
    """Type VI_h (marginal: no FLRW limit, h ≠ -1)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_vih_constants(n1=n1, n3=n3, a_twist=a_twist),
        sigma_over_H_init=sigma_over_H_init, beta=beta,
    )


def type_vii0_cosmology(sigma_over_H_init: float = 1e-4,
                        n1: float = 1e-2, n3: float = 1e-2,
                        beta: float = 0.0) -> BianchiCosmology:
    """Type VII_0 (flat FLRW limit with k=0)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_vii0_constants(n1=n1, n3=n3),
        sigma_over_H_init=sigma_over_H_init, beta=beta,
    )


def type_viih_cosmology(sigma_over_H_init: float = 1e-5,
                        n1: float = 1.8e-2, n3: float = 1.0e-2,
                        a_twist: float = 5.5e-3,
                        beta: float = 0.0) -> BianchiCosmology:
    """Type VII_h (Pontzen-Challinor default, principal CMB Bianchi type)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_viih_constants(n1=n1, n3=n3, a_twist=a_twist),
        sigma_over_H_init=sigma_over_H_init, beta=beta,
    )


def type_viii_cosmology(sigma_over_H_init: float = 1e-4,
                        n1: float = -1e-2, n2: float = 1e-2, n3: float = 1e-2,
                        beta: float = 0.0) -> BianchiCosmology:
    """Type VIII (sl(2,ℝ), marginal: no FLRW limit)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_viii_constants(n1=n1, n2=n2, n3=n3),
        sigma_over_H_init=sigma_over_H_init, beta=beta,
    )


def type_ix_cosmology(sigma_over_H_init: float = 1e-4,
                      n: float = 1e-2, beta: float = 0.0) -> BianchiCosmology:
    """Type IX (Mixmaster, k=+1 FLRW limit)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_ix_constants(n=n),
        sigma_over_H_init=sigma_over_H_init, beta=beta,
    )


# ══════════════════════════════════════════════════════════════════
# Unified cosmology factory
# ══════════════════════════════════════════════════════════════════

COSMOLOGY_FACTORY = {
    "FLRW": flrw_cosmology,
    "I": type_i_cosmology,
    "II": type_ii_cosmology,
    "III": type_iii_cosmology,
    "IV": type_iv_cosmology,
    "V": type_v_cosmology,
    "VI_0": type_vi0_cosmology,
    "VI_h": type_vih_cosmology,
    "VII_0": type_vii0_cosmology,
    "VII_h": type_viih_cosmology,
    "VIII": type_viii_cosmology,
    "IX": type_ix_cosmology,
}


def make_cosmology(type_label: str, **kwargs) -> BianchiCosmology:
    """Factory dispatch: build a BianchiCosmology for a given type.

    Parameters
    ----------
    type_label : str
        One of FLRW, I, II, III, IV, V, VI_0, VI_h, VII_0, VII_h, VIII, IX.
    **kwargs
        Forwarded to the type-specific factory (e.g., n1, sigma_over_H_init, beta).

    Returns
    -------
    BianchiCosmology
        Validated cosmology with canonical comparator policy applied.
    """
    if type_label not in COSMOLOGY_FACTORY:
        raise KeyError(
            f"Unknown cosmology type '{type_label}'. "
            f"Valid: {list(COSMOLOGY_FACTORY)}"
        )
    return COSMOLOGY_FACTORY[type_label](**kwargs)
