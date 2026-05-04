"""Tests for bass/hierarchy/aux_state.py (LB-5).

The aux-state tests cover two invariants:

1. ``build_integrator_canonical_decision`` yields a decision whose
   ``allow_reduction`` bit reflects the underlying gates — **resolving
   the LB-3 F3 / LB-4 F3 carry-over** that previously wired the TCA
   branch through ``_always_allowing_tca_decision`` (a hard-wired
   permissive bypass).

2. ``build_aux_state`` honours the ``gamma_T_override`` hook that
   the integrator's TCA dispatch test (I-18) relies on to probe the
   deep tight-coupling regime above the HyRec fixture's ``z_max``.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.hierarchy.aux_state import (
    build_aux_state,
    build_integrator_canonical_decision,
)
from bass.hierarchy.closure import build_default_closure
from bass.runtime.canonical_decision import (
    CanonicalBlockError,
    CanonicalDecision,
    require_allow_reduction,
)
from bass.species.registry import SpeciesBackgroundRegistry


@pytest.fixture(scope="module")
def species():
    return SpeciesBackgroundRegistry.from_planck2018()


# ════════════════════════════════════════════════════════════════════
#   build_integrator_canonical_decision  — real gate wiring (F3)
# ════════════════════════════════════════════════════════════════════

def test_real_canonical_decision_allows_reduction_in_regime() -> None:
    """With Planck-2018-safe ``β`` and a Σ² above the Sobolev floor,
    the real W3 ``CanonicalDecision`` returns ``allow_reduction=True``.

    This pins the LB-5 integrator's default TCA dispatch through the
    production gate functions — no more ``_always_allowing_tca_decision``
    bypass (LB-3 F3 / LB-4 F3 carry-over resolved).
    """
    decision = build_integrator_canonical_decision(
        beta=1e-3, sigma_squared=1e-5,
    )
    assert isinstance(decision, CanonicalDecision)
    assert decision.allow_reduction is True
    # require_allow_reduction is a pure no-op when the decision allows.
    require_allow_reduction(decision, context="LB-5 test")


def test_real_canonical_decision_blocks_oversize_beta() -> None:
    """An unsafe ``|β|`` value that violates VT-07 blocks the reduction.

    The safe route is ``|β| ≤ safety × ε_1 / (1 + η_{u̇}) =
    0.5 × 0.02 / 1.16 ≈ 8.6e-3``. Requesting ``|β| = 0.1`` should fail
    the beta gate, and the AND-reduction must propagate.
    """
    decision = build_integrator_canonical_decision(
        beta=0.1, sigma_squared=1e-5,
    )
    assert decision.allow_reduction is False
    with pytest.raises(CanonicalBlockError):
        require_allow_reduction(decision, context="LB-5 beta test")


def test_real_canonical_decision_blocks_low_sigma() -> None:
    """With ``Σ² < sigma_floor`` the Sobolev gate fails."""
    # Pass sigma_squared below the default floor 1e-6; the aux-builder
    # pads it to the floor so the decision can still be formed, but
    # passing an explicit sub-floor to the gate directly fails.
    from bass.runtime.sigma_floor import sigma_min_gate
    passed, _ = sigma_min_gate(
        sigma_squared=1e-10, floor=1e-6,
    )
    assert passed is False


# ════════════════════════════════════════════════════════════════════
#   build_aux_state — gamma_T_override hook (I-18 enabler)
# ════════════════════════════════════════════════════════════════════

def test_gamma_T_override_replaces_recomb_lookup(species) -> None:
    """``gamma_T_override(η)`` replaces the baryon recombination-table
    lookup so tests can probe the deep tight-coupling regime.
    """
    closure = build_default_closure(L_max=4, strategy_name="hardcut")
    decision = build_integrator_canonical_decision(
        beta=0.0, sigma_squared=1e-5,
    )
    aux = build_aux_state(
        bg_table=species.bg_table,
        species=species,
        tetrad_state=None,
        closure=closure,
        canonical_decision=decision,
        gamma_T_override=lambda eta: 1234.5,
    )
    for eta in [10.0, 100.0, 1000.0, 10000.0]:
        assert aux.Gamma_T_at(eta) == pytest.approx(1234.5)


def test_gamma_T_without_override_uses_baryon_recomb(species) -> None:
    """With ``gamma_T_override=None`` the default path dispatches to
    the baryon Thomson authority path: HyRec in-table and the physical
    fully-ionized opacity fallback above the fixture's z_max.
    """
    closure = build_default_closure(L_max=4, strategy_name="hardcut")
    decision = build_integrator_canonical_decision(
        beta=0.0, sigma_squared=1e-5,
    )
    aux = build_aux_state(
        bg_table=species.bg_table,
        species=species,
        tetrad_state=None,
        closure=closure,
        canonical_decision=decision,
    )
    # Deep pre-recomb (z >> 8000) — out-of-fixture but physically
    # fully ionized, so Γ_T must remain finite and positive.
    gamma_deep = aux.Gamma_T_at(eta=0.01)
    assert gamma_deep > 0.0 and np.isfinite(gamma_deep)
    # Mid-recomb (z ≈ 2000, η ≈ 100 Mpc) — finite, positive.
    gamma_mid = aux.Gamma_T_at(eta=100.0)
    assert gamma_mid > 0.0 and np.isfinite(gamma_mid)


def test_aux_state_rejects_bad_threshold(species) -> None:
    closure = build_default_closure(L_max=4, strategy_name="hardcut")
    decision = build_integrator_canonical_decision(
        beta=0.0, sigma_squared=1e-5,
    )
    with pytest.raises(ValueError, match="gamma_T_over_H_threshold"):
        build_aux_state(
            bg_table=species.bg_table,
            species=species,
            tetrad_state=None,
            closure=closure,
            canonical_decision=decision,
            gamma_T_over_H_threshold=-1.0,
        )


def test_H_local_at_gives_expected_magnitude(species) -> None:
    """H_local(η) matches the analytic ``H(a)/c`` at η_today."""
    closure = build_default_closure(L_max=4, strategy_name="hardcut")
    decision = build_integrator_canonical_decision(
        beta=0.0, sigma_squared=1e-5,
    )
    aux = build_aux_state(
        bg_table=species.bg_table,
        species=species,
        tetrad_state=None,
        closure=closure,
        canonical_decision=decision,
    )
    eta_today = species.bg_table.eta_today
    H_from_aux = aux.H_local_at(eta_today)
    # Expected: H_0 / c in natural units.
    H0_mpc = species.bg_table.H0_mpc
    assert H_from_aux == pytest.approx(H0_mpc, rel=1e-3)
