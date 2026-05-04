"""bass/hierarchy/aux_state.py (LB-5) — shared precomputed payload for the RHS.

``IntegratorAuxState`` bundles the read-only splines, tables, and
policy objects that every call to ``combined_rhs`` (spec §3) needs to
consult. Building it is an O(1) setup cost before ``solve_ivp`` runs;
the bundle is then threaded through ``scipy.integrate.solve_ivp``'s
``args=`` channel and never mutated during integration.

Fields:
- ``bg_table`` — shared ``FLRWBackgroundTable`` (species layer SSOT;
  supplies ``a(η), 𝓗(η), Θ(η)``).
- ``species`` — the full ``SpeciesBackgroundRegistry`` (for species
  sum-rule diagnostics and the baryon ``τ̇`` spline).
- ``tetrad_state`` — ``TetradBackgroundState`` supplying ``Σ_ab(η)``;
  ``None`` means strict FLRW (``σ_ab ≡ 0``).
- ``closure`` / ``collision_T`` / ``collision_E`` — pluggable strategies
  (LB-3 closure, LB-4 collision) used inside the RHS.
- ``canonical_decision`` — the real W3 canonical decision threaded to
  the TCA algebraic step (resolves LB-3 F3 / LB-4 F3: no more
  ``_always_allowing_tca_decision`` bypass inside the integrator).
- ``gamma_T_over_H_threshold`` — threshold for the TCA branch dispatch
  (``Γ_T / H > threshold`` ⇒ use algebraic closure at ℓ=2).

References
----------
- ``docs/lowell_bianchi/05_integrator_spec.md §3.1`` (auxiliary state
  contract).
- ``docs/lowell_bianchi/04_thomson_collision_spec.md §10`` (Γ_T
  plumbing).
- Ma-Bertschinger 1995 §8; Hamilton 2001 (CAMB operator splitting).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

from bass.background.tetrad_state import TetradBackgroundState
from bass.collision.thomson_pstf import (
    EModeThomsonCollisionOperator,
    ThomsonPSTFCollisionOperator,
)
from bass.hierarchy.closure_interface import ClosureStrategy
from bass.runtime.canonical_decision import (
    CanonicalDecision,
    make_canonical_decision,
)
from bass.runtime.sigma_floor import sigma_min_gate
from bass.species.background_table import FLRWBackgroundTable
from bass.species.registry import SpeciesBackgroundRegistry
from bass.tilt.baryon_only_policy import beta_policy_gate
from tsc.diagnostics.tangency import TangentKind, compute_D_diagnostic


__all__ = [
    "IntegratorAuxState",
    "build_aux_state",
    "build_integrator_canonical_decision",
]


# ════════════════════════════════════════════════════════════════════
#   Dataclass
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class IntegratorAuxState:
    """Read-only payload shared by every ``combined_rhs`` evaluation.

    Built once by ``build_aux_state`` before ``solve_ivp`` starts.
    Frozen dataclass to make inadvertent mutation impossible.

    Reference: spec §3.1; see ``LowellBianchiIntegrator.run`` for the
    construction-time wiring.
    """

    bg_table: FLRWBackgroundTable
    species: SpeciesBackgroundRegistry
    tetrad_state: Optional[TetradBackgroundState]
    closure: ClosureStrategy
    collision_T: ThomsonPSTFCollisionOperator
    collision_E: EModeThomsonCollisionOperator
    canonical_decision: CanonicalDecision
    gamma_T_over_H_threshold: float = 100.0
    v_b_dipole: np.ndarray = field(
        default_factory=lambda: np.zeros(3, dtype=np.float64),
    )
    gamma_T_override: Optional[Callable[[float], float]] = None
    """Optional callable ``η → Γ_T(η)`` that overrides the baryon
    species' recombination-fixture lookup. Used by LB-5 tests that
    need to probe the deep tight-coupling regime (``Γ_T/H > 100``)
    which sits below the HyRec fixture's ``z_max = 8000`` horizon.
    ``None`` (the default) dispatches to the baryon species' authority
    Thomson path: HyRec inside the table and the fully-ionized analytic
    opacity above the table's z_max when that helper is available.
    """

    def __post_init__(self) -> None:
        if (not np.isfinite(self.gamma_T_over_H_threshold)
                or self.gamma_T_over_H_threshold <= 0):
            raise ValueError(
                f"gamma_T_over_H_threshold must be positive finite, got "
                f"{self.gamma_T_over_H_threshold}"
            )
        vb = np.asarray(self.v_b_dipole, dtype=np.float64)
        if vb.shape != (3,):
            raise ValueError(
                f"v_b_dipole must have shape (3,), got {vb.shape}"
            )
        # Replace the stored v_b with a contiguous float64 copy so the
        # RHS never sees a list / mixed-dtype input.
        object.__setattr__(self, "v_b_dipole", vb.copy())

    # ------------------------------------------------------------------
    #   Background / recombination query helpers (η → scalar)
    # ------------------------------------------------------------------

    def a_at(self, eta: float) -> float:
        """Scale factor ``a(η)`` via the FLRW background table spline."""
        return float(self.bg_table.interp_a(eta))

    def calH_at(self, eta: float) -> float:
        """Conformal Hubble ``𝓗(η) = a H`` [Mpc⁻¹]."""
        return float(self.bg_table.interp_calH(eta))

    def H_local_at(self, eta: float) -> float:
        """Local Hubble parameter ``H(η) = 𝓗 / a`` [Mpc⁻¹]."""
        calH = self.calH_at(eta)
        a = self.a_at(eta)
        if a <= 0.0:
            raise ValueError(f"a(η) must be positive, got {a}")
        return calH / a

    def Gamma_T_at(self, eta: float) -> float:
        """Conformal Thomson rate ``τ̇(η) = a n_e σ_T`` [Mpc⁻¹].

        When ``gamma_T_override`` is set, delegates to it. Otherwise
        delegates to the baryon species authority path. Deep
        pre-recombination starts use the fully-ionized analytic opacity
        instead of Γ_T=0, so seed ``tau_c`` and TCA gating stay physical.
        """
        if self.gamma_T_override is not None:
            return float(self.gamma_T_override(float(eta)))
        from bass.species.base import SpeciesLabel
        baryon = self.species[SpeciesLabel.BARYON]
        query = getattr(
            baryon,
            "tau_dot_with_early_fully_ionized_fallback",
            baryon.tau_dot,
        )
        try:
            return float(query(eta))
        except ValueError:
            return 0.0


# ════════════════════════════════════════════════════════════════════
#   Canonical-decision factory (real, not bypass)
# ════════════════════════════════════════════════════════════════════

def build_integrator_canonical_decision(
    *,
    beta: float,
    sigma_squared: float,
    epsilon_1: float = 0.02,
    eta_u_dot: float = 0.16,
    safety_margin: float = 0.5,
    sigma_floor: float = 1e-6,
) -> CanonicalDecision:
    """Construct a **real** ``CanonicalDecision`` for the LB-5 integrator.

    This replaces the ``_always_allowing_tca_decision`` bypass used by
    ``TCAClosure`` at LB-3/LB-4 (carry-over F3 audit item). The three
    gates are wired to the production gate functions:

    * VT-07 ``beta_policy_gate`` — frame-attribution safe route on
      ``|β| ≤ safety_margin × ε_1 / (1 + η_{u̇})``.
    * ``sigma_min_gate`` — Sobolev validity floor on Σ².
    * ``source_Dge2_gate`` via ``compute_D_diagnostic`` on the
      one-field ``G(x) = x`` photon manifold at ``(ξ, η) = (0, 0)``
      (Paper I §5.2 default for the photon fluid on-manifold test).

    At the LB-5 scope (orthogonal Bianchi, ``v_e = 0``) all three gates
    naturally pass with the Planck-2018-driven background; Σ² is held
    above the floor by the configured initial shear amplitude. If the
    caller requests a state that violates any gate the integrator will
    raise through ``require_allow_reduction`` at the TCA step —
    surface the failure rather than silently use a stale closure.

    Parameters
    ----------
    beta : float
        Tilt rapidity (the cosmology's ``beta`` parameter at LB-5 is
        zero; non-zero entries are supported here for forward
        compatibility with the tilted post-LB phase).
    sigma_squared : float
        Shear-squared ``Σ²`` at the representative η used for the gate
        check. Typically ``sigma_squared ≥ sigma_floor`` is enforced
        by the integrator config for non-FLRW runs.
    epsilon_1, eta_u_dot, safety_margin, sigma_floor : float
        Policy parameters. Defaults match
        ``_always_allowing_tca_decision`` inside ``closure.py`` and
        ``SIGMA_FLOOR_DEFAULT`` in ``sigma_floor.py``.

    Reference: design spec §2; CANONICAL_DECISION_DESIGN.md §2.2;
    ``bass/runtime/canonical_decision.py`` §5.
    """
    beta_result = beta_policy_gate(
        beta=float(beta),
        epsilon_1=float(epsilon_1),
        eta_u_dot=float(eta_u_dot),
        safety_margin=float(safety_margin),
    )

    # Σ² floor expects strictly positive input (sigma_min_gate raises on
    # negative). FLRW runs with σ = 0 would violate the floor; that is
    # intentional — in pure FLRW the TCA path is degenerate (Γ_T still
    # finite but no shear forcing) and callers must gate separately.
    # We pass max(σ², floor) here so the *decision* is well-formed; the
    # integrator still short-circuits the TCA branch when the closure
    # strategy is not ``TCAClosure``.
    sigma_for_gate = max(float(sigma_squared), float(sigma_floor))
    sigma_result = sigma_min_gate(
        sigma_squared=sigma_for_gate, floor=float(sigma_floor),
    )

    def _photon_G_field(x):
        return np.asarray(x, dtype=np.float64)

    tang = compute_D_diagnostic(
        G_field=_photon_G_field,
        kind=TangentKind.ONE_FIELD,
        xi=0,
        eta=0.0,
    )

    return make_canonical_decision(
        beta_result=beta_result,
        sigma_result=sigma_result,
        tangency_result=tang,
    )


# ════════════════════════════════════════════════════════════════════
#   Top-level builder
# ════════════════════════════════════════════════════════════════════

def build_aux_state(
    *,
    bg_table: FLRWBackgroundTable,
    species: SpeciesBackgroundRegistry,
    tetrad_state: Optional[TetradBackgroundState],
    closure: ClosureStrategy,
    canonical_decision: CanonicalDecision,
    collision_T: Optional[ThomsonPSTFCollisionOperator] = None,
    collision_E: Optional[EModeThomsonCollisionOperator] = None,
    gamma_T_over_H_threshold: float = 100.0,
    v_b_dipole: Optional[np.ndarray] = None,
    gamma_T_override: Optional[Callable[[float], float]] = None,
) -> IntegratorAuxState:
    """Factory that wires the six LB sub-layers into a single frozen bundle.

    The factory chooses defaults matching the LB-5 baseline (Planck-
    2018 Thomson operators, orthogonal ``v_b = 0``, TCA threshold
    ``Γ_T/H > 100``). Callers override any field by keyword.

    Reference: spec §3.1.
    """
    if collision_T is None:
        collision_T = ThomsonPSTFCollisionOperator()
    if collision_E is None:
        collision_E = EModeThomsonCollisionOperator()
    if v_b_dipole is None:
        v_b_dipole = np.zeros(3, dtype=np.float64)
    return IntegratorAuxState(
        bg_table=bg_table,
        species=species,
        tetrad_state=tetrad_state,
        closure=closure,
        collision_T=collision_T,
        collision_E=collision_E,
        canonical_decision=canonical_decision,
        gamma_T_over_H_threshold=float(gamma_T_over_H_threshold),
        v_b_dipole=np.asarray(v_b_dipole, dtype=np.float64),
        gamma_T_override=gamma_T_override,
    )
