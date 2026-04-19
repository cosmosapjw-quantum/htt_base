"""
bass/background/einstein_bianchi.py  (FB-0.1: Ellis convention)
================================================================

Bianchi background ODE integrator with full 10-type support.

Solves the Einstein-Bianchi system for the scale factor a(η) and shear
``Σ_±(η)`` in conformal time, with real cosmological parameters
(Planck 2018).

Convention (Ellis §18.3 / Wainwright-Ellis §18)
-----------------------------------------------
The stored shear is the **Ellis conformal shear** ``Σ_ab ≡ a σ_ab``
where ``σ_ab`` is the proper-time shear satisfying the Raychaudhuri
companion ``σ̇_ab + Θ σ_ab = S_proper,ab`` with ``Θ = 3 H``.

For Bianchi I flat (no spatial-curvature source) this yields
``σ_ab × a³ = const`` (Kasner), i.e. ``Σ_ab × a² = const``.

State variables
---------------
  a(η)     — scale factor
  Σ_+(η)   — Ellis conformal shear (plus mode): Σ_+ = a × σ_+
  Σ_-(η)   — Ellis conformal shear (minus mode)

Equations (unified across types; conformal-time derivation in
``docs/audits/AUDIT_PHASE_FB0_2026-04-19.md §2``):
  a'   = a × ℋ
  Σ_+' = -2 ℋ Σ_+ + ℋ² · S^{WE}_+(type, Σ, ℋ, a)
  Σ_-' = -2 ℋ Σ_- + ℋ² · S^{WE}_-(type, Σ, ℋ, a)

The ``-2 ℋ Σ`` decay term is the Ellis signature: the standard
``-3 H σ`` proper-time decay maps under ``Σ = a σ`` into
``dΣ/dη = -2 𝓗 Σ + a² S_proper``. The Wainwright-Ellis dimensionless
source ``S^{WE}`` is related to the proper-time source by
``S_proper = H² S^{WE}``; hence ``a² S_proper = 𝓗² S^{WE}`` in
conformal form. The helper ``compute_shear_source`` in
``shear_sources.py`` returns ``ℋ² × S^{WE}`` directly.

Frame: n^a-frame (Bianchi hypersurface normal).
Units: η in Mpc, H in km/s/Mpc, Σ in Mpc⁻¹.

History
-------
- pre-FB-0.1 (shipped since W1D3): tracked a non-Ellis Σ for which
  Type I preserved ``Σ × a = const`` (corresponding to ``σ × a² = const``,
  i.e. not Kasner). ``proper_shear_at_eta`` assumed Ellis ``Σ = a σ``
  and divided by ``a``, producing a convention mismatch downstream
  (LB-5 F2 carry-forward).
- FB-0.1 (2026-04-19): flipped to Ellis; downstream consumers already
  assumed ``Σ = a σ``, so this closes the mismatch.

References
----------
  Ellis, Maartens & MacCallum, *Relativistic Cosmology* (CUP 2012) §18.3
  Wainwright & Ellis, *Dynamical Systems in Cosmology* (CUP 1997) §6, §18
  Pontzen & Challinor, *PRD* 79, 103518 (2009) — VII_h spiral convention
"""
from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence, Tuple, Union

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


_V_HAT_E_DEFAULT: Tuple[float, float, float] = (1.0, 0.0, 0.0)
"""Default tilt direction (electron rest-frame spatial unit vector) aligned
with the first tetrad axis. Ellis §11.3 convention."""

_V_HAT_NORM_TOL: float = 1e-10
"""Absolute tolerance on |v̂_e|² - 1 at construction. Tight because the
caller is expected to supply a literal unit vector (not a noisy dynamical
output); any drift past this threshold is a user error, not integrator
noise."""


@dataclass(frozen=True)
class BianchiCosmology:
    """Cosmological parameters + Bianchi structure + tilt kinematics.

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
        Tilt rapidity between the matter frame ``u_e^a`` and the Bianchi
        normal ``n^a`` (lowell §11.3 / Ellis §5.3). The boost factor that
        appears in the tilted visibility (LB-4 Layer A) and the
        non-perturbative collision kernel (FB-4) is
        ``B(η, ê) = cosh β + sinh β (ê·v̂_e)``. ``β = 0`` recovers the
        orthogonal (n-frame = u_e-frame) limit bit-for-bit.
    v_hat_e : tuple of three floats
        Tilt direction — the **spatial unit vector** that defines the
        matter-frame boost axis relative to the n^a tetrad axes. Must
        satisfy ``|v̂_e|² = 1`` to within ``_V_HAT_NORM_TOL`` at
        construction. Default is the first tetrad axis ``(1, 0, 0)``
        (``00_conventions §2`` frame-split rule + §5.4 basis alignment
        rule). See FB-0.2 audit for the SSOT derivation.
    comparator : ComparatorPolicy, optional
        Comparator policy for the master departure identity. If None, uses
        recommend_comparator(structure.label).

    Notes
    -----
    ``beta`` and ``v_hat_e`` together parametrise the tilted-sector kinematics
    referenced by the FB plan (``FULL_BIANCHI_COVERAGE_PLAN.md §4``):

    - FB-0.2 (this dataclass): **field exposure only** — β=0 / v̂_e=(1,0,0)
      default preserves LB-5 / LB-6 regression bit-for-bit.
    - FB-3.1+: non-perturbative Lorentz boost wired into
      ``TiltedSpeciesBackground`` / PSTF moments.
    - FB-4: direction-dependent Thomson kernel Layer B.

    References
    ----------
    - Ellis, Maartens & MacCallum 2012, §5.3, §11.3 (tilted congruences).
    - King & Ellis 1973, *CMP* 31, 209 (tilted-fluid algebra).
    - lowell §11.3 (tilted visibility primitives).
    - ``docs/lowell_bianchi/00_conventions.md §2`` (frame split rule).
    """
    H0: float = 67.36
    Omega_r: float = 9.22e-5
    Omega_m: float = 0.3138
    Omega_Lambda: float = 0.6862
    structure: StructureConstants = field(default_factory=flrw_constants)
    sigma_over_H_init: float = 0.0
    sigma_pm_ratio: float = 0.0
    beta: float = 0.0
    v_hat_e: Tuple[float, float, float] = _V_HAT_E_DEFAULT
    comparator: Optional[ComparatorPolicy] = None

    def __post_init__(self) -> None:
        # Accept any 3-element iterable (tuple, list, ndarray) and
        # normalise storage to a tuple of floats for hashability under
        # the ``frozen=True`` contract. Validate the unit-norm invariant
        # eagerly — a silent renormalisation would hide user errors and
        # couple the tilted-sector surface to floating-point noise.
        v_raw = tuple(float(x) for x in self.v_hat_e)
        if len(v_raw) != 3:
            raise ValueError(
                f"v_hat_e must have exactly three components; got "
                f"{len(v_raw)} from input {self.v_hat_e!r}"
            )
        norm_sq = v_raw[0] ** 2 + v_raw[1] ** 2 + v_raw[2] ** 2
        if abs(norm_sq - 1.0) > _V_HAT_NORM_TOL:
            raise ValueError(
                f"v_hat_e must be a unit vector (|v̂_e|² = 1); got "
                f"|v̂_e|² = {norm_sq!r} from input {self.v_hat_e!r} "
                f"(tolerance {_V_HAT_NORM_TOL:.1e}). "
                f"See 00_conventions §2 + FB-0.2 audit for the SSOT."
            )
        object.__setattr__(self, "v_hat_e", v_raw)

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

    ``terminated_by_event`` and ``event_eta`` are populated when the
    integrator is given an ``events=`` argument (FB-1.2 D5 dispatch for
    Bianchi IX recollapse). Default ``False`` / empty preserves the pre
    FB-1.2 surface bit-for-bit for callers that pass no event.
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
    terminated_by_event: bool = False
    event_eta: Tuple[float, ...] = ()


def _hubble_squared(a: float, p: BianchiCosmology,
                    sigma2_conformal: float = 0.0) -> float:
    """H²(a) including shear contribution (perturbative for near-FLRW)."""
    H0_sq = p.H0 ** 2
    friedmann = H0_sq * (p.Omega_r / a**4 + p.Omega_m / a**3 + p.Omega_Lambda)
    return max(friedmann, 1e-30)


EventFunc = Callable[[float, np.ndarray], float]


def solve_bianchi_background(
    cosmo: BianchiCosmology,
    a_start: float = 1e-6,
    a_end: float = 1.0,
    n_pts: int = 3000,
    events: Optional[Union[EventFunc, Sequence[EventFunc]]] = None,
) -> BianchiBackgroundState:
    """Integrate the Bianchi background from a_start to a_end.

    Works for all 10 Bianchi types + FLRW via dispatch to shear_sources.

    Parameters
    ----------
    cosmo, a_start, a_end, n_pts : see class-level docstring.
    events : callable or list of callables, optional
        Forwarded to ``scipy.integrate.solve_ivp``'s ``events=`` parameter
        (FB plan §6 D5 — event-terminated integration for Bianchi IX
        recollapse). Each callable has signature ``event(eta, y) -> float``
        where a sign change triggers the event; set the ``terminal`` and
        ``direction`` attributes on the callable per SciPy conventions.
        Default ``None`` preserves the pre FB-1.2 behaviour bit-for-bit.
        Use ``bianchi_ix_recollapse_event(cosmo)`` as the canonical IX
        event factory.
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

        # Per-type shear source dispatch. The helper returns
        # ``ℋ² × S^{WE}(type)`` in Ellis conformal units (FB-0.1).
        source_Sp, source_Sm = compute_shear_source(sc, Sp, Sm, cH, a_val)

        # Ellis shear evolution (FB-0.1):
        #   dΣ_ab/dη = -2 𝓗 Σ_ab + 𝓗² S^{WE}(type)
        # Preserves ``Σ × a² = const`` in Type I flat (Kasner).
        dSp = -2.0 * cH * Sp + source_Sp
        dSm = -2.0 * cH * Sm + source_Sm

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

    ivp_kwargs = {}
    if events is not None:
        ivp_kwargs["events"] = events

    sol = solve_ivp(rhs, (0.0, eta_end_est), y0, method='RK45',
                    t_eval=eta_eval, rtol=1e-10, atol=1e-14,
                    max_step=eta_end_est / 200, **ivp_kwargs)

    if not sol.success or len(sol.y[0]) < n_pts // 2:
        # Retry on looser tolerance — except when the integrator stopped
        # early because an event fired (sol.status == 1). That is the
        # intended terminal outcome for Bianchi IX recollapse (FB-1.2
        # D5 dispatch) and must not be retried.
        if sol.status != 1:
            sol = solve_ivp(rhs, (0.0, eta_end_est), y0, method='RK45',
                            t_eval=eta_eval, rtol=1e-8, atol=1e-12,
                            **ivp_kwargs)

    a_arr = np.maximum(sol.y[0], 1e-30)
    Sp_arr = sol.y[1]
    Sm_arr = sol.y[2]
    eta_arr = sol.t

    z_arr = 1.0 / a_arr - 1.0
    H_arr = np.array([math.sqrt(_hubble_squared(a, cosmo)) for a in a_arr])
    calH_arr = a_arr * H_arr / C_KMS

    terminated_by_event = bool(getattr(sol, "t_events", None)) and any(
        len(te) > 0 for te in sol.t_events
    )
    event_eta: Tuple[float, ...] = ()
    if terminated_by_event:
        event_eta = tuple(
            float(te[0]) for te in sol.t_events if len(te) > 0
        )

    return BianchiBackgroundState(
        eta=eta_arr, a=a_arr, z=z_arr,
        H=H_arr, calH=calH_arr,
        sigma_plus=Sp_arr, sigma_minus=Sm_arr,
        cosmo=cosmo, source_status=source_status,
        terminated_by_event=terminated_by_event,
        event_eta=event_eta,
    )


def bianchi_ix_recollapse_event(
    cosmo: BianchiCosmology,
    floor: float = 0.0,
) -> EventFunc:
    """Factory for a ``solve_ivp`` event that terminates on Bianchi IX
    recollapse.

    Returns a callable ``event(eta, y)`` that evaluates to
    ``a × H / C_KMS − floor`` (= ℋ − floor). A sign change (decreasing)
    signals the instant the universe stops expanding — the operative
    definition of recollapse in conformal-time integration (``a' = a × ℋ``).

    Usage
    -----
    >>> cosmo = type_ix_cosmology(n=1e-2)
    >>> event = bianchi_ix_recollapse_event(cosmo)
    >>> bg = solve_bianchi_background(cosmo, events=event)

    With the production Planck-2018 FLRW background H(a) > 0 always, so
    this event does not fire during canonical IX integration — it is
    wired in for FB-5 / FB-6 Mixmaster / BKL work where ``H²`` may pick
    up a negative spatial-curvature contribution sufficient to drive ℋ
    through zero. The ``floor`` parameter allows synthetic triggering
    for smoke tests (``floor > 0`` fires early).

    Parameters
    ----------
    cosmo : BianchiCosmology
        Used to evaluate ``H(a)`` via the same Friedmann callback the
        integrator uses; keeps the event synchronous with the RHS.
    floor : float, default 0.0
        Threshold for the crossing. Real recollapse is ℋ = 0; tests set
        ``floor > 0`` to force the event on a realistic FLRW background.

    References
    ----------
    Wainwright & Ellis 1997 §18 (Type IX recollapse in the Kasner-
    compact attractor); FB plan §6 D5; SciPy ``solve_ivp`` event API.
    """
    def event(eta: float, y: np.ndarray) -> float:
        a_val = max(float(y[0]), 1e-30)
        H = math.sqrt(_hubble_squared(a_val, cosmo))
        calH = a_val * H / C_KMS
        return calH - floor

    event.terminal = True
    event.direction = -1  # only a decreasing crossing (expansion → halt)
    return event


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


def flrw_cosmology(
    beta: float = 0.0,
    v_hat_e: Tuple[float, float, float] = _V_HAT_E_DEFAULT,
) -> BianchiCosmology:
    """Planck 2018 ΛCDM (FLRW limit: σ = 0).

    ``beta`` / ``v_hat_e`` are accepted for API symmetry with the Bianchi
    factories (FB-0.2); they have no dynamical effect in the orthogonal
    FLRW limit until the tilted sector comes online (FB-3/FB-4).
    """
    return BianchiCosmology(
        **_PLANCK18,
        structure=flrw_constants(),
        sigma_over_H_init=0.0,
        beta=beta, v_hat_e=v_hat_e,
    )


def type_i_cosmology(sigma_over_H_init: float = 1e-4,
                     beta: float = 0.0,
                     v_hat_e: Tuple[float, float, float] = _V_HAT_E_DEFAULT,
                     ) -> BianchiCosmology:
    """Type I (abelian, no curvature)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_i_constants(),
        sigma_over_H_init=sigma_over_H_init, beta=beta, v_hat_e=v_hat_e,
    )


def type_ii_cosmology(sigma_over_H_init: float = 1e-4,
                      n1: float = 1e-2, beta: float = 0.0,
                      v_hat_e: Tuple[float, float, float] = _V_HAT_E_DEFAULT,
                      ) -> BianchiCosmology:
    """Type II (Heisenberg, marginal: no FLRW limit)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_ii_constants(n1=n1),
        sigma_over_H_init=sigma_over_H_init, beta=beta, v_hat_e=v_hat_e,
    )


def type_iii_cosmology(sigma_over_H_init: float = 1e-4,
                       n1: float = 1e-2, beta: float = 0.0,
                       v_hat_e: Tuple[float, float, float] = _V_HAT_E_DEFAULT,
                       ) -> BianchiCosmology:
    """Type III = VI_{h=-1} (marginal: no FLRW limit)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_iii_constants(n1=n1),
        sigma_over_H_init=sigma_over_H_init, beta=beta, v_hat_e=v_hat_e,
    )


def type_iv_cosmology(sigma_over_H_init: float = 1e-4,
                      n3: float = 1e-2, a_twist: float = 1e-2,
                      beta: float = 0.0,
                      v_hat_e: Tuple[float, float, float] = _V_HAT_E_DEFAULT,
                      ) -> BianchiCosmology:
    """Type IV — cosmologically marginal, NO FLRW limit.

    Used as a falsifiability probe: pipeline should decisively exclude under
    near-FLRW data (see comparator_policy.bianchi_iv_falsifiability_probe).
    """
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_iv_constants(n3=n3, a_twist=a_twist),
        sigma_over_H_init=sigma_over_H_init, beta=beta, v_hat_e=v_hat_e,
        comparator=ComparatorPolicy.NULL,  # structured-null
    )


def type_v_cosmology(sigma_over_H_init: float = 0.0,
                     a_twist: float = 1e-2, beta: float = 0.0,
                     v_hat_e: Tuple[float, float, float] = _V_HAT_E_DEFAULT,
                     ) -> BianchiCosmology:
    """Type V (open FLRW analogue, k=-1 limit)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_v_constants(a_twist=a_twist),
        sigma_over_H_init=sigma_over_H_init, beta=beta, v_hat_e=v_hat_e,
    )


def type_vi0_cosmology(sigma_over_H_init: float = 1e-4,
                       n1: float = 1e-2, n3: float = -1e-2,
                       beta: float = 0.0,
                       v_hat_e: Tuple[float, float, float] = _V_HAT_E_DEFAULT,
                       ) -> BianchiCosmology:
    """Type VI_0 (marginal: no FLRW limit)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_vi0_constants(n1=n1, n3=n3),
        sigma_over_H_init=sigma_over_H_init, beta=beta, v_hat_e=v_hat_e,
    )


def type_vih_cosmology(sigma_over_H_init: float = 1e-4,
                       n1: float = 1e-2, n3: float = -2e-3,
                       a_twist: float = 5e-3, beta: float = 0.0,
                       v_hat_e: Tuple[float, float, float] = _V_HAT_E_DEFAULT,
                       ) -> BianchiCosmology:
    """Type VI_h (marginal: no FLRW limit, h ≠ -1)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_vih_constants(n1=n1, n3=n3, a_twist=a_twist),
        sigma_over_H_init=sigma_over_H_init, beta=beta, v_hat_e=v_hat_e,
    )


def type_vii0_cosmology(sigma_over_H_init: float = 1e-4,
                        n1: float = 1e-2, n3: float = 1e-2,
                        beta: float = 0.0,
                        v_hat_e: Tuple[float, float, float] = _V_HAT_E_DEFAULT,
                        ) -> BianchiCosmology:
    """Type VII_0 (flat FLRW limit with k=0)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_vii0_constants(n1=n1, n3=n3),
        sigma_over_H_init=sigma_over_H_init, beta=beta, v_hat_e=v_hat_e,
    )


def type_viih_cosmology(sigma_over_H_init: float = 1e-5,
                        n1: float = 1.8e-2, n3: float = 1.0e-2,
                        a_twist: float = 5.5e-3,
                        beta: float = 0.0,
                        v_hat_e: Tuple[float, float, float] = _V_HAT_E_DEFAULT,
                        ) -> BianchiCosmology:
    """Type VII_h (Pontzen-Challinor default, principal CMB Bianchi type)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_viih_constants(n1=n1, n3=n3, a_twist=a_twist),
        sigma_over_H_init=sigma_over_H_init, beta=beta, v_hat_e=v_hat_e,
    )


def type_viii_cosmology(sigma_over_H_init: float = 1e-4,
                        n1: float = -1e-2, n2: float = 1e-2, n3: float = 1e-2,
                        beta: float = 0.0,
                        v_hat_e: Tuple[float, float, float] = _V_HAT_E_DEFAULT,
                        ) -> BianchiCosmology:
    """Type VIII (sl(2,ℝ), marginal: no FLRW limit)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_viii_constants(n1=n1, n2=n2, n3=n3),
        sigma_over_H_init=sigma_over_H_init, beta=beta, v_hat_e=v_hat_e,
    )


def type_ix_cosmology(sigma_over_H_init: float = 1e-4,
                      n: float = 1e-2, beta: float = 0.0,
                      v_hat_e: Tuple[float, float, float] = _V_HAT_E_DEFAULT,
                      ) -> BianchiCosmology:
    """Type IX (Mixmaster, k=+1 FLRW limit)."""
    return BianchiCosmology(
        **_PLANCK18,
        structure=type_ix_constants(n=n),
        sigma_over_H_init=sigma_over_H_init, beta=beta, v_hat_e=v_hat_e,
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
        Forwarded to the type-specific factory. All factories accept
        ``sigma_over_H_init`` (except ``FLRW`` which fixes it to 0),
        ``beta`` (tilt rapidity, default 0), and ``v_hat_e`` (tilt
        direction unit vector, default ``(1, 0, 0)``). Type-specific
        structure parameters (``n1``, ``n3``, ``a_twist``, ``n``, ...)
        are also forwarded per the type's signature.

    Returns
    -------
    BianchiCosmology
        Validated cosmology with canonical comparator policy applied and
        the FB-0.2 unit-norm ``v̂_e`` invariant enforced.

    Examples
    --------
    >>> make_cosmology("VII_h", beta=0.01, v_hat_e=(0.6, 0.8, 0.0))  # doctest: +SKIP
    BianchiCosmology(..., beta=0.01, v_hat_e=(0.6, 0.8, 0.0), ...)
    """
    if type_label not in COSMOLOGY_FACTORY:
        raise KeyError(
            f"Unknown cosmology type '{type_label}'. "
            f"Valid: {list(COSMOLOGY_FACTORY)}"
        )
    return COSMOLOGY_FACTORY[type_label](**kwargs)
