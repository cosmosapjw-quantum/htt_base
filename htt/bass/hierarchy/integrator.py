"""bass/hierarchy/integrator.py (LB-5) — unified Lowell-Bianchi driver.

``LowellBianchiIntegrator.run`` wires the LB-1 species backgrounds,
LB-2 PSTF multipole hierarchy, LB-3 closure strategies, and LB-4
Thomson collision operator into one ``scipy.integrate.solve_ivp``
call on a single η-grid, producing the background scale factor,
tetrad shear, photon temperature tower, photon E-mode tower, and
reduced neutrino fluid simultaneously.

The RHS is assembled by ``combined_rhs`` which:

1. Packs ``(a, Σ_+, Σ_−)`` into the head of the state vector and
   advances them via the Einstein-Bianchi formulas reused verbatim
   from ``bass/background/einstein_bianchi.py`` (Wainwright-Ellis
   shear source + Friedmann; no re-derivation).
2. Runs ``hierarchy_rhs_photon`` for the temperature tower with
   ``ThomsonPSTFCollisionOperator`` sourced by ``τ̇(η)`` from the
   baryon species recombination table.
3. Runs ``hierarchy_rhs_photon`` again for the E-mode tower with
   ``EModeThomsonCollisionOperator`` sourced by the current temperature
   ``Π_2`` slab.
4. Runs ``neutrino_reduced_rhs`` for the ``(Δ_ν, q_ν, π_ν, G_3)``
   block.
5. If the configured closure is ``TCAClosure`` **and** ``Γ_T/H``
   exceeds the threshold at the current η, replaces the axisymmetric
   ``m = 0`` slots of ``Π_2`` and ``E_2`` with the W6-04 algebraic
   prediction (spec §10.6) — a DAE-style substitution that pins the
   ODE trajectory to the algebraic envelope in the tight-coupling
   limit. The real ``CanonicalDecision`` bundled in ``IntegratorAuxState``
   is threaded to the ``solve_tca_closure`` call (resolves the LB-3
   F3 / LB-4 F3 audit carry-over).

References
----------
- ``docs/lowell_bianchi/05_integrator_spec.md §1–§11`` (complete
  spec).
- Ma-Bertschinger 1995 §8 (combined FLRW Boltzmann integration).
- Ellis §6 (conservation laws); Ellis §18.3 (Bianchi background
  integrator).
- Hindmarsh 1983 (LSODA automatic stiffness switching); Hamilton
  2001 (CAMB tolerance conventions).
- Press-Teukolsky *Numerical Recipes* Ch 17 (stiff ODE solvers).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

import numpy as np
from scipy.integrate import solve_ivp

from bass.background.einstein_bianchi import (
    BianchiCosmology, flrw_cosmology,
)
from bass.background.tetrad_state import TetradBackgroundState
from bass.collision.polarization import PolarizationHierarchyState
from bass.collision.thomson_pstf import (
    EModeThomsonAux,
    EModeThomsonCollisionOperator,
    ThomsonAux,
    ThomsonPSTFCollisionOperator,
)
from bass.hierarchy.aux_state import (
    IntegratorAuxState,
    build_aux_state,
    build_integrator_canonical_decision,
)
from bass.hierarchy.closure import TCAClosure, build_default_closure
from bass.hierarchy.closure_interface import ClosureStrategy
from bass.hierarchy.collision_interface import ZeroCollisionOperator
from bass.hierarchy.event_detection import detect_critical_events
from bass.hierarchy.hierarchy_rhs import hierarchy_rhs_photon
from bass.hierarchy.ic import zero_IC
from bass.hierarchy.neutrino_reduced import neutrino_reduced_rhs
from bass.hierarchy.pack_unpack import (
    NEUTRINO_REDUCED_SIZE,
    combined_total_size,
    slice_a,
    slice_neutrino_reduced,
    slice_photon_E,
    slice_photon_T,
    slice_sigma_pm,
    unpack_combined_state,
)
from bass.hierarchy.pstf_tensor import (
    PSTFHierarchyState,
    hierarchy_total_size,
    unpack_hierarchy,
)
from bass.recombination.recombination_ingest import (
    RecombinationInterp, build_interpolators, load_recombination_table,
)
from bass.species.registry import SpeciesBackgroundRegistry
from bass.transport.shear_sources import compute_shear_source


__all__ = [
    "IntegratorConfig",
    "IntegrationResult",
    "LowellBianchiIntegrator",
    "combined_rhs",
]


C_KMS: float = 299792.458


# ════════════════════════════════════════════════════════════════════
#   Public dataclasses (spec §9.2)
# ════════════════════════════════════════════════════════════════════

@dataclass
class IntegratorConfig:
    """User-facing configuration for one LB-5 integration.

    Defaults match spec §9.2 (Planck-2018 FLRW, ``L_max = 6``,
    ``rtol = 1e-6, atol = 1e-12``).
    """

    L_max: int = 6
    eta_initial_mpc: float = 0.5
    eta_final_mpc: float = 14147.0
    n_output: int = 2000
    rtol: float = 1e-6
    atol: float = 1e-12
    bianchi_cosmo: BianchiCosmology = field(default_factory=flrw_cosmology)
    Sigma_plus_initial: float = 0.0
    Sigma_minus_initial: float = 0.0
    closure_strategy: Optional[ClosureStrategy] = None
    collision_T: Optional[ThomsonPSTFCollisionOperator] = None
    collision_E: Optional[EModeThomsonCollisionOperator] = None
    gamma_T_over_H_threshold: float = 100.0
    solver_method: str = "LSODA"
    gamma_T_override: Optional[Callable[[float], float]] = None
    max_step_factor: int = 1000
    """V5 Round-17 P3.5 perf knob (2026-04-27): the ``max_step`` argument
    to ``solve_ivp`` is set to ``(eta_final - eta_initial) / max_step_factor``.
    The legacy default 1000 forces ≥1000 sub-steps across the cosmological
    range, ensuring fine sampling of the recombination peak (~19 Mpc FWHM
    on η ∈ [261, 14147] Mpc gives Δη_max ≈ 14 Mpc per step). Diagnostic
    callers that don't need recombination-resolution can lower this
    factor — values around 100 reduce the artificial floor and let LSODA
    pick its own coarse steps in the smooth ISW regime, ~3× faster
    overall. Production / regression callers should leave this at 1000."""
    adiabatic_mode_seed: bool = False
    """V5 step-4b-(a) super-horizon adiabatic IC switch. When True,
    ``_build_seed_projection`` calls ``build_flrw_regular_seed(...,
    adiabatic=True)`` which sets the correct adiabatic ratios
    (``δ_γ:δ_b:δ_c:δ_ν = 4/3:1:1:4/3``, ``θ = 0``) in the canonical
    tracking surface. Note: the ACTUAL solver IC is supplied by
    ``make_camb_regular_adiabatic_seed`` (Lowell §13.2) at each k;
    this flag only toggles the canonical tracking placeholder. The
    physics-determining knob is ``primordial_b_k_sq`` below."""
    primordial_b_k_sq: float = 1.0
    """**Linear primordial curvature amplitude** ``C ≈ ζ`` of the Lowell
    §13.2 regular-adiabatic seed (Ma-Bertschinger 1995 §7 eq. 96;
    Lewis-Challinor 2002 App. C). Despite the historical ``_sq`` suffix
    (which dates to the CAMB Notes ``χ_0 = -1`` geometric ``β² = 1``
    convention in flat FLRW), every leading-order seed perturbation
    enters this parameter linearly — confirmed by the V5-RUNTIME Round-12
    4-cycle external audit (2026-04-25) and Round-17 audit verdict
    (2026-04-27).

    Conventions:
      - ``primordial_b_k_sq = 1.0`` (legacy default): unit-amplitude
        probe; matches the CAMB Notes ``χ_0 = -1`` reference convention.
        All leading-order seed entries are O(1) at this amplitude.
      - ``primordial_b_k_sq = ζ`` (some primordial curvature value):
        physical amplitude. The C_ℓ assembly then pairs ``α(k)`` (the
        per-unit-ζ transfer extracted from this seed) with
        ``P_R(k) = ⟨ζ²⟩`` per the canonical
        ``C_ℓ = 4π ∫ d ln k · P_R(k) · |α|²``.

    Do NOT pass ``A_s × (k/k_pivot)^(n_s-1)`` here. That value
    (~ 2.1 × 10⁻⁹) is the *variance* spectrum ``P_R(k) = ⟨ζ²⟩``, not the
    linear amplitude. Doing so would produce a meaningless seed value
    that under-runs the linear-extraction probe range by ~10⁹.

    See `htt/bass/perturbation/regular_adiabatic_ic.py:111-135` for the
    same docstring on the parameter at its load-bearing entry point, and
    `htt/bass/spectrum/flrw_pipeline.py:143-158` for the pipeline-level
    docstring. All three must remain consistent."""
    """Test hook: override the species-layer ``Γ_T(η)`` with a caller-
    supplied callable. Used by tests that need to probe the deep
    tight-coupling regime beyond the HyRec fixture's ``z_max = 8000``
    horizon. Leave ``None`` in production — the default path uses
    the baryon species' recombination table."""

    def __post_init__(self) -> None:
        if self.L_max < 2:
            raise ValueError(
                f"L_max must be ≥ 2 (E-mode tower requires ℓ≥2 storage); "
                f"got {self.L_max}"
            )
        if self.eta_initial_mpc <= 0:
            raise ValueError(
                f"eta_initial_mpc must be positive, got {self.eta_initial_mpc}"
            )
        if self.eta_final_mpc <= self.eta_initial_mpc:
            raise ValueError(
                f"eta_final_mpc ({self.eta_final_mpc}) must exceed "
                f"eta_initial_mpc ({self.eta_initial_mpc})"
            )
        if self.n_output < 10:
            raise ValueError(
                f"n_output must be ≥ 10, got {self.n_output}"
            )
        if self.rtol <= 0 or self.atol < 0:
            raise ValueError(
                f"rtol/atol must be positive/non-negative, got "
                f"rtol={self.rtol}, atol={self.atol}"
            )

    # ------------------------------------------------------------------
    # Tilt-kinematics accessors (FB-0.2)
    # ------------------------------------------------------------------
    #
    # ``bianchi_cosmo`` is the single source of truth for the tilt
    # parameters (``beta``, ``v_hat_e``); these properties are
    # **read-only** surfaces that downstream consumers (TCA / closure
    # guards, tilted-visibility wiring in FB-3, boosted Thomson kernel
    # in FB-4) use to look up the kinematic state without reaching into
    # ``IntegratorConfig.bianchi_cosmo.*`` directly. Keeping them as
    # properties rather than fields avoids duplication and prevents the
    # two surfaces from drifting out of sync.
    # Reference: lowell §11.3; ``00_conventions §2`` (frame split rule).

    @property
    def tilt_rapidity(self) -> float:
        """Tilt rapidity ``β`` forwarded from ``bianchi_cosmo.beta``.

        The boost factor in the tilted Thomson / visibility pipeline is
        ``B(η, ê) = cosh β + sinh β (ê·v̂_e)`` (lowell §11.3). ``β = 0``
        recovers the orthogonal limit bit-for-bit.
        """
        return float(self.bianchi_cosmo.beta)

    @property
    def tilt_direction(self) -> Tuple[float, float, float]:
        """Tilt direction unit vector ``v̂_e`` forwarded from
        ``bianchi_cosmo.v_hat_e``.

        Norm ``|v̂_e|² = 1`` is enforced at ``BianchiCosmology``
        construction; reading through this accessor therefore does not
        need to re-validate. ``00_conventions §2`` + FB-0.2 audit SSOT.
        """
        return self.bianchi_cosmo.v_hat_e


@dataclass
class IntegrationResult:
    """Full output bundle (spec §9.2)."""

    eta: np.ndarray
    a: np.ndarray
    Sigma_plus: np.ndarray
    Sigma_minus: np.ndarray
    photon_T_tower: np.ndarray
    photon_E_tower: np.ndarray
    neutrino_reduced: np.ndarray
    critical_events: dict
    config: IntegratorConfig
    solver_info: dict
    tca_active_mask: np.ndarray = field(repr=False)
    photon_T_history_by_mode_label: object | None = field(default=None, repr=False)
    photon_E_history_by_mode_label: object | None = field(default=None, repr=False)
    neutrino_tower: np.ndarray | None = field(default=None, repr=False)
    neutrino_history_by_mode_label: object | None = field(default=None, repr=False)
    photon_B_tower: np.ndarray | None = field(default=None, repr=False)
    photon_B_history_by_mode_label: object | None = field(default=None, repr=False)
    baryon_local_history: np.ndarray | None = field(default=None, repr=False)
    cdm_local_history: np.ndarray | None = field(default=None, repr=False)
    residual_local_history: np.ndarray | None = field(default=None, repr=False)
    residual_harmonic_history: np.ndarray | None = field(default=None, repr=False)
    residual_source_history: np.ndarray | None = field(default=None, repr=False)
    baryon_local_history_by_mode_label: object | None = field(default=None, repr=False)
    cdm_local_history_by_mode_label: object | None = field(default=None, repr=False)
    source_history: np.ndarray | None = field(default=None, repr=False)
    source_history_by_mode_label: object | None = field(default=None, repr=False)
    layout_auxiliary_bundle: object | None = field(default=None, repr=False)
    runtime_execution_trace: object | None = field(default=None, repr=False)

    @property
    def L_max(self) -> int:
        return self.config.L_max

    def pi_ell_m(self, ell: int, m: int = 0) -> np.ndarray:
        """Return ``Π_ℓ(η)`` at the ``m``-th packed slot across the output grid.

        Convenience for plotting / diagnostics; packing index mapping
        is the real-spherical-harmonic ``i = ℓ + m`` (``00_conventions
        §5``).
        """
        if ell < 0 or ell > self.L_max:
            raise ValueError(
                f"ell must be in [0, {self.L_max}], got {ell}"
            )
        if abs(m) > ell:
            raise ValueError(
                f"|m| must be ≤ ell={ell}, got m={m}"
            )
        offset = sum(2 * l + 1 for l in range(ell))
        return self.photon_T_tower[:, offset + (ell + m)].copy()

    def e_ell_m(self, ell: int, m: int = 0) -> np.ndarray:
        """Return ``E_ℓ(η)`` at the ``m``-th packed slot."""
        if ell < 2 or ell > self.L_max:
            raise ValueError(
                f"ell must be in [2, {self.L_max}], got {ell}"
            )
        if abs(m) > ell:
            raise ValueError(
                f"|m| must be ≤ ell={ell}, got m={m}"
            )
        offset = sum(2 * l + 1 for l in range(ell))
        return self.photon_E_tower[:, offset + (ell + m)].copy()

    def nu_ell_m(self, ell: int, m: int = 0) -> np.ndarray:
        """Return the neutrino PSTF tower component when available."""
        if self.neutrino_tower is None:
            raise ValueError("IntegrationResult does not carry a neutrino_tower")
        if ell < 0 or ell > self.L_max:
            raise ValueError(
                f"ell must be in [0, {self.L_max}], got {ell}"
            )
        if abs(m) > ell:
            raise ValueError(
                f"|m| must be ≤ ell={ell}, got m={m}"
            )
        offset = sum(2 * l + 1 for l in range(ell))
        return self.neutrino_tower[:, offset + (ell + m)].copy()

    def b_ell_m(self, ell: int, m: int = 0) -> np.ndarray:
        """Return the B-mode PSTF tower component when available."""
        if self.photon_B_tower is None:
            raise ValueError("IntegrationResult does not carry a photon_B_tower")
        if ell < 0 or ell > self.L_max:
            raise ValueError(
                f"ell must be in [0, {self.L_max}], got {ell}"
            )
        if abs(m) > ell:
            raise ValueError(
                f"|m| must be ≤ ell={ell}, got m={m}"
            )
        offset = sum(2 * l + 1 for l in range(ell))
        return self.photon_B_tower[:, offset + (ell + m)].copy()


# ════════════════════════════════════════════════════════════════════
#   Combined RHS
# ════════════════════════════════════════════════════════════════════

def _bg_rhs(
    a: float, Sp: float, Sm: float, cosmo: BianchiCosmology,
) -> Tuple[float, float, float]:
    """Einstein-Bianchi background RHS — Ellis convention (FB-0.1).

    Reuses ``einstein_bianchi`` arithmetic (same Friedmann, same ℋ,
    same dispatched ``compute_shear_source``). The Ellis conformal
    shear ``Σ_ab = a σ_ab`` obeys
    ``dΣ/dη = -2 ℋ Σ + ℋ² · S^{WE}(type)``; the helper already
    returns the full ``ℋ² × S^{WE}`` term.

    Reference: ``bass/background/einstein_bianchi.py``; Ellis §18.3;
    spec §3; ``docs/audits/AUDIT_PHASE_FB0_2026-04-19.md §2``.
    """
    a_val = max(a, 1e-30)
    H0_sq = cosmo.H0 ** 2
    friedmann = H0_sq * (
        cosmo.Omega_r / a_val ** 4
        + cosmo.Omega_m / a_val ** 3
        + cosmo.Omega_Lambda
    )
    H = math.sqrt(max(friedmann, 1e-30))
    calH = a_val * H / C_KMS

    da = a_val * calH
    source_Sp, source_Sm = compute_shear_source(
        cosmo.structure, Sp, Sm, calH, a_val,
    )
    # Ellis decay: ``Σ × a² = const`` for Type I (Kasner).
    dSp = -2.0 * calH * Sp + source_Sp
    dSm = -2.0 * calH * Sm + source_Sm
    return da, dSp, dSm


def _ell2_m0_slot_offset(L_max: int) -> int:
    """Offset (within a flat photon tower) of the ``(ℓ=2, m=0)`` slot.

    ``Σ_{ℓ=0,1} (2ℓ+1) + (ell + m) = 1 + 3 + 2 = 6`` for ``m = 0``.
    """
    _ = L_max  # invariant across L_max ≥ 2
    return 1 + 3 + 2


def combined_rhs(
    eta: float,
    y: np.ndarray,
    *,
    L_max: int,
    aux_state: IntegratorAuxState,
    cosmo: BianchiCosmology,
    tca_tracker: Optional[List[bool]] = None,
) -> np.ndarray:
    """Assemble ``dy/dη`` for the combined LB-5 state vector.

    Reference: spec §3; docstring of this module for the 5-step
    breakdown.
    """
    state = unpack_combined_state(y, L_max=L_max)
    out = np.empty_like(y)

    # (1) Background (a, Σ_+, Σ_-)
    da, dSp, dSm = _bg_rhs(state.a, state.Sigma_plus, state.Sigma_minus, cosmo)
    out[slice_a(L_max)] = da
    out[slice_sigma_pm(L_max)] = [dSp, dSm]

    # (2) Photon temperature hierarchy (with Thomson collision)
    Gamma_T = aux_state.Gamma_T_at(eta)
    v_b = aux_state.v_b_dipole

    aux_T = ThomsonAux(
        E_state=state.photon_E,
        v_b_real_sph=v_b,
        Gamma_T=float(Gamma_T),
    )
    rhs_T = hierarchy_rhs_photon(
        eta,
        state.photon_T.as_flat(),
        L_max=L_max,
        bg_table=aux_state.bg_table,
        tetrad_state=aux_state.tetrad_state,
        closure=aux_state.closure,
        collision=aux_state.collision_T,
        collision_aux=aux_T,
    )

    # (3) Photon E-mode hierarchy (with E-mode Thomson collision)
    aux_E = EModeThomsonAux(
        Pi_2_packed=state.photon_T.tensors[2].components.copy(),
        Gamma_T=float(Gamma_T),
    )
    rhs_E = hierarchy_rhs_photon(
        eta,
        state.photon_E.E.as_flat(),
        L_max=L_max,
        bg_table=aux_state.bg_table,
        tetrad_state=aux_state.tetrad_state,
        closure=aux_state.closure,
        collision=aux_state.collision_E,
        collision_aux=aux_E,
    )

    # (4) Neutrino reduced fluid
    rhs_nu = neutrino_reduced_rhs(
        eta,
        state.neutrino_reduced,
        bg_table=aux_state.bg_table,
    )

    # (5) Optional TCA dispatch at ℓ=2 m=0
    tca_active = False
    if isinstance(aux_state.closure, TCAClosure) and Gamma_T > 0.0:
        H_local = aux_state.H_local_at(eta)
        if (H_local > 0.0
                and Gamma_T / H_local > aux_state.gamma_T_over_H_threshold):
            tca_active = True
            # Compute the non-collision sources at ℓ=2 m=0 by running
            # the hierarchy RHS once with ZeroCollisionOperator and
            # extracting the proper-time derivative (divide by a).
            rhs_T_free = hierarchy_rhs_photon(
                eta,
                state.photon_T.as_flat(),
                L_max=L_max,
                bg_table=aux_state.bg_table,
                tetrad_state=aux_state.tetrad_state,
                closure=aux_state.closure,
                collision=ZeroCollisionOperator(),
                collision_aux=None,
            )
            rhs_E_free = hierarchy_rhs_photon(
                eta,
                state.photon_E.E.as_flat(),
                L_max=L_max,
                bg_table=aux_state.bg_table,
                tetrad_state=aux_state.tetrad_state,
                closure=aux_state.closure,
                collision=ZeroCollisionOperator(),
                collision_aux=None,
            )
            slot = _ell2_m0_slot_offset(L_max)
            a_val = aux_state.a_at(eta)
            # In η-prime parameterisation Π' = a × Π̇ = a × (K − sum_T).
            # With K = 0 we have Π'_free = −a × sum_T, so S_T = -rhs_T_free/a
            # in Ma-Bertschinger / W6-04 convention (the non-collision
            # RHS going onto the LHS as the source +S_T).
            if a_val <= 0.0:
                raise RuntimeError(
                    f"a(η) must be positive, got {a_val} at η={eta}"
                )
            S_T_src = float(rhs_T_free[slot]) / a_val * (-1.0)
            S_E_src = float(rhs_E_free[slot]) / a_val * (-1.0)
            # Ask TCAClosure for the algebraic (Θ_2, E_2) — routed
            # through the real CanonicalDecision held in aux_state.
            theta_2_alg, E_2_alg = _algebraic_tca_scalars(
                closure=aux_state.closure,
                decision=aux_state.canonical_decision,
                S_T=S_T_src,
                S_E=S_E_src,
                Gamma_T=float(Gamma_T),
                H_local=float(H_local),
            )
            # DAE-style substitution: pin the Π_2 and E_2 m=0 slots to
            # the algebraic prediction by overwriting their RHS slots
            # with a relaxation term that collapses the gap in ≲ 1/Γ_T.
            # This is the "Π_2 ODE disable" dispatch mandated by spec
            # §3.2 / spec §10.6.
            current_Pi2 = float(state.photon_T.tensors[2].components[2])
            current_E2 = float(state.photon_E.E.tensors[2].components[2])
            # Relaxation rate: η-prime convention ``Π'(η) = a × Π̇``.
            # Target time constant ``1/Γ_T``: ``Π̇ = -Γ_T (Π - Π_alg)``
            # so ``Π' = -a × Γ_T × (Π - Π_alg)``.
            relax_rate = a_val * float(Gamma_T)
            rhs_T[slot] = -relax_rate * (current_Pi2 - theta_2_alg)
            rhs_E[slot] = -relax_rate * (current_E2 - E_2_alg)

    if tca_tracker is not None:
        tca_tracker.append(bool(tca_active))

    # Assemble
    out[slice_photon_T(L_max)] = rhs_T
    out[slice_photon_E(L_max)] = rhs_E
    out[slice_neutrino_reduced(L_max)] = rhs_nu
    return out


def _algebraic_tca_scalars(
    *,
    closure: TCAClosure,
    decision,
    S_T: float,
    S_E: float,
    Gamma_T: float,
    H_local: float,
) -> Tuple[float, float]:
    """Invoke ``solve_tca_closure`` through the real ``CanonicalDecision``
    (not ``_always_allowing_tca_decision``) held in the integrator's
    aux state. Resolves the LB-3 F3 / LB-4 F3 audit carry-over.

    Defers to ``TCAClosure.gamma_threshold_over_H`` for the activation
    threshold so callers cannot bypass the guard by passing a tiny
    ``Γ_T``; the ``RuntimeError`` is re-raised.

    Reference: ``bass/closure/quadrupole_tca.solve_tca_closure``;
    canonical_decision design spec §2.
    """
    from bass.closure.quadrupole_tca import solve_tca_closure
    if H_local <= 0 or not np.isfinite(H_local):
        raise ValueError(f"H_local must be positive finite, got {H_local}")
    if not np.isfinite(Gamma_T) or Gamma_T <= 0:
        raise ValueError(
            f"Gamma_T must be strictly positive for TCA algebraic "
            f"closure, got {Gamma_T}"
        )
    if Gamma_T / H_local < closure.gamma_threshold_over_H:
        raise RuntimeError(
            f"TCA inactive: Γ_T/H = {Gamma_T / H_local:.3e} < "
            f"threshold {closure.gamma_threshold_over_H:.3e}"
        )
    return solve_tca_closure(
        S_T=float(S_T),
        S_E=float(S_E),
        gamma_T=float(Gamma_T),
        decision=decision,
    )


# ════════════════════════════════════════════════════════════════════
#   LowellBianchiIntegrator
# ════════════════════════════════════════════════════════════════════

class LowellBianchiIntegrator:
    """Main LB-5 driver (spec §9.2).

    ``run`` performs the ``solve_ivp`` call and returns an
    ``IntegrationResult`` with the full state-vector history plus
    the three critical-η events (``z_eq, z_*, eta_reion_midpoint``)
    attached via ``detect_critical_events``.
    """

    def __init__(
        self,
        config: IntegratorConfig,
        species: SpeciesBackgroundRegistry,
        tetrad_state: Optional[TetradBackgroundState] = None,
        canonical_decision=None,
    ):
        self.config = config
        self.species = species
        self.tetrad_state = tetrad_state

        # Build a real CanonicalDecision unless the caller supplies one
        # (tests may inject a custom decision; resolution of LB-3/LB-4
        # F3 is delivered by the default path using the real gates).
        if canonical_decision is None:
            canonical_decision = build_integrator_canonical_decision(
                beta=float(config.bianchi_cosmo.beta),
                sigma_squared=max(
                    (config.bianchi_cosmo.sigma_over_H_init) ** 2, 1e-12,
                ),
            )
        self.canonical_decision = canonical_decision

        # Wire the closure — default is TCAClosure(inner=HardCutClosure)
        # with threshold 100 (spec §10.6).
        closure = (
            config.closure_strategy
            if config.closure_strategy is not None
            else build_default_closure(
                L_max=config.L_max, strategy_name="tca",
                gamma_threshold_over_H=config.gamma_T_over_H_threshold,
            )
        )

        self.aux_state = build_aux_state(
            bg_table=species.bg_table,
            species=species,
            tetrad_state=tetrad_state,
            closure=closure,
            canonical_decision=canonical_decision,
            collision_T=config.collision_T,
            collision_E=config.collision_E,
            gamma_T_over_H_threshold=config.gamma_T_over_H_threshold,
            gamma_T_override=config.gamma_T_override,
        )

    # ------------------------------------------------------------------

    def initial_state(self) -> np.ndarray:
        """Return the packed ``y0`` vector from the config (zero-IC baseline)."""
        return zero_IC(
            L_max=self.config.L_max,
            a_initial=float(self.species.bg_table.interp_a(
                self.config.eta_initial_mpc)),
            Sigma_plus_initial=self.config.Sigma_plus_initial,
            Sigma_minus_initial=self.config.Sigma_minus_initial,
        )

    def run(self) -> IntegrationResult:
        """Execute the integration and return the full ``IntegrationResult``.

        Raises ``RuntimeError`` if ``solve_ivp`` does not reach
        ``eta_final_mpc`` or if post-processing detects a ``NaN/Inf``
        in the output arrays (spec §7.3, §8).
        """
        y0 = self.initial_state()
        eta_out = np.linspace(
            self.config.eta_initial_mpc,
            self.config.eta_final_mpc,
            self.config.n_output,
        )
        max_step = (
            self.config.eta_final_mpc - self.config.eta_initial_mpc
        ) / float(max(1, self.config.max_step_factor))
        tca_tracker: List[bool] = []

        def _rhs(eta, y):
            return combined_rhs(
                eta, y,
                L_max=self.config.L_max,
                aux_state=self.aux_state,
                cosmo=self.config.bianchi_cosmo,
                tca_tracker=tca_tracker,
            )

        sol = solve_ivp(
            _rhs,
            (self.config.eta_initial_mpc, self.config.eta_final_mpc),
            y0,
            t_eval=eta_out,
            method=self.config.solver_method,
            rtol=self.config.rtol,
            atol=self.config.atol,
            max_step=max_step,
        )

        if not sol.success:
            raise RuntimeError(
                f"solve_ivp failed: {sol.message} at η={sol.t[-1]}"
            )
        if np.any(~np.isfinite(sol.y)):
            raise RuntimeError(
                "solve_ivp produced non-finite entries — inspect "
                "IntegrationResult.solver_info."
            )

        y_out = sol.y  # shape (total_size, n_output)
        a_arr = y_out[slice_a(self.config.L_max)][0]
        Sp_arr = y_out[slice_sigma_pm(self.config.L_max)][0]
        Sm_arr = y_out[slice_sigma_pm(self.config.L_max)][1]
        T_tower = y_out[slice_photon_T(self.config.L_max)].T.copy()
        E_tower = y_out[slice_photon_E(self.config.L_max)].T.copy()
        nu_out = y_out[slice_neutrino_reduced(self.config.L_max)].T.copy()

        events = detect_critical_events(self.species, self.species.bg_table)

        # Retrospective TCA activation on the output grid (independent of
        # the internal tracker that sees every LSODA substep).
        tca_mask = self._compute_tca_mask(sol.t)

        solver_info = {
            "nfev": int(sol.nfev),
            "njev": int(sol.njev),
            "nlu": int(sol.nlu),
            "status": int(sol.status),
            "message": str(sol.message),
            "tca_tracker_len": len(tca_tracker),
            "tca_tracker_any_active": any(tca_tracker),
        }

        return IntegrationResult(
            eta=sol.t,
            a=a_arr,
            Sigma_plus=Sp_arr,
            Sigma_minus=Sm_arr,
            photon_T_tower=T_tower,
            photon_E_tower=E_tower,
            neutrino_reduced=nu_out,
            critical_events=events,
            config=self.config,
            solver_info=solver_info,
            tca_active_mask=tca_mask,
        )

    def _compute_tca_mask(self, etas: np.ndarray) -> np.ndarray:
        """Evaluate ``Γ_T(η)/H(η) > threshold`` on the output grid.

        Independent of the LSODA substep-level tracker — the mask here
        is the canonical "was TCA active at this η?" diagnostic.
        """
        mask = np.zeros(len(etas), dtype=bool)
        if not isinstance(self.aux_state.closure, TCAClosure):
            return mask
        for i, eta in enumerate(etas):
            try:
                Gamma = self.aux_state.Gamma_T_at(float(eta))
                H = self.aux_state.H_local_at(float(eta))
                if H > 0 and Gamma > 0:
                    mask[i] = (
                        Gamma / H > self.aux_state.gamma_T_over_H_threshold
                    )
            except Exception:
                mask[i] = False
        return mask


# Silence unused-import warnings on symbols that are re-exported by
# the public API for convenience (tests and gallery scripts consume
# these directly from the integrator module).
_ = PolarizationHierarchyState
_ = PSTFHierarchyState
_ = hierarchy_total_size
_ = unpack_hierarchy
_ = NEUTRINO_REDUCED_SIZE
_ = combined_total_size
_ = load_recombination_table
_ = build_interpolators
_ = RecombinationInterp
_ = Callable
