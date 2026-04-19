"""Tests C-01..C-12 for ``bass.hierarchy.closure`` (LB-3).

Covers the four closure strategies specified in
``docs/lowell_bianchi/03_closure_truncation_spec.md §11.1..§11.4``:

Protocol conformance / HardCut (§11.1):

- C-01  ``HardCutClosure().get_closure(state, L+1)`` returns zero
- C-02  Every LB-3 strategy ``isinstance(..., ClosureStrategy)``
- C-03  All four strategies return a PSTFTensor of requested rank and
        do not mutate the input state
- C-04  ``FreeStreamingClosure(k=0)`` degenerates to hard-cut

Numeric targets — FreeStream / PowerLaw (§11.2):

- C-05  Ma-Bertschinger 1995 eq (53) scalar recursion (``m = 0``)
- C-06  Recursion applied twice for the ``ell + 2`` closure slot
- C-07  PowerLaw scaling ``(L / (L+1))^α`` per component
- C-08  PowerLaw at ``L + 2`` scales by ``(L / (L+2))^α``

TCAClosure (§11.3):

- C-09  ``override_at_ell(ℓ)`` is True iff ℓ == 2
- C-10  ``algebraic_closure`` bit-identical to ``solve_tca_closure``
- C-11  Below threshold ``algebraic_closure`` raises RuntimeError
- C-12  ``get_closure`` delegates to ``inner`` strategy

References
----------
- spec §11.1..§11.4
- Ma-Bertschinger 1995 eq (53), (63), (64)
- ``bass/closure/quadrupole_tca.py`` (W6-04)
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.hierarchy import (
    ClosureStrategy,
    FreeStreamingClosure,
    HardCutClosure,
    PSTFHierarchyState,
    PSTFTensor,
    PowerLawExtrapolationClosure,
    TCAClosure,
    build_default_closure,
    zero_hierarchy,
    zero_pstf,
)
from bass.closure.quadrupole_tca import solve_tca_closure
from bass.runtime.canonical_decision import make_canonical_decision
from tsc.diagnostics.tangency import TangentKind, compute_D_diagnostic


# ════════════════════════════════════════════════════════════════════
#   Fixtures
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def populated_state() -> PSTFHierarchyState:
    """A non-trivial tower up to ℓ = 4 with distinguishable per-rank
    content so that slot-matching logic is testable.
    """
    rng = np.random.default_rng(seed=30303)
    tensors = []
    for ell in range(5):
        comp = rng.normal(size=2 * ell + 1)
        tensors.append(PSTFTensor(ell=ell, components=comp))
    return PSTFHierarchyState(L=4, tensors=tensors)


def _allowing_decision():
    tang = compute_D_diagnostic(
        G_field=lambda x: np.asarray(x, dtype=float),
        kind=TangentKind.ONE_FIELD,
        xi=0,
        eta=0.0,
    )
    return make_canonical_decision(
        beta_result=(True, {
            "beta": 1.36e-3, "beta_max": 8.62e-3, "slack": 7.26e-3,
            "eta_u_dot": 0.16, "safety_factor": 0.5, "epsilon_1": 0.02,
        }),
        sigma_result=(True, {
            "sigma_sq": 1e-5, "floor": 1e-6, "log_margin_decades": 1.0,
        }),
        tangency_result=tang,
    )


# ════════════════════════════════════════════════════════════════════
#   C-01: HardCut returns zero tensor at tower-top
# ════════════════════════════════════════════════════════════════════

def test_c01_hardcut_returns_zero_above_tower(populated_state) -> None:
    closure = HardCutClosure()
    for ell_req in (5, 6, 7):
        t = closure.get_closure(populated_state, ell_req)
        assert isinstance(t, PSTFTensor)
        assert t.ell == ell_req
        assert t.components.shape == (2 * ell_req + 1,)
        assert np.all(t.components == 0.0)


# ════════════════════════════════════════════════════════════════════
#   C-02: All LB-3 strategies satisfy the ClosureStrategy protocol
# ════════════════════════════════════════════════════════════════════

def test_c02_all_strategies_satisfy_protocol() -> None:
    strategies = [
        HardCutClosure(),
        FreeStreamingClosure(k_mpc_inv=0.1, eta=100.0),
        PowerLawExtrapolationClosure(alpha=2.0),
        TCAClosure(inner=HardCutClosure()),
    ]
    for strat in strategies:
        assert isinstance(strat, ClosureStrategy), (
            f"{type(strat).__name__} does not satisfy ClosureStrategy"
        )


# ════════════════════════════════════════════════════════════════════
#   C-03: Every strategy returns correct rank; state is not mutated
# ════════════════════════════════════════════════════════════════════

def test_c03_strategies_return_correct_rank_and_preserve_state(
    populated_state,
) -> None:
    strategies = [
        HardCutClosure(),
        FreeStreamingClosure(k_mpc_inv=0.2, eta=50.0),
        PowerLawExtrapolationClosure(alpha=2.5),
        TCAClosure(inner=HardCutClosure()),
    ]
    snapshot_components = [t.components.copy() for t in populated_state.tensors]
    for strat in strategies:
        for ell_req in (5, 6):
            out = strat.get_closure(populated_state, ell_req)
            assert isinstance(out, PSTFTensor)
            assert out.ell == ell_req
            assert out.components.shape == (2 * ell_req + 1,)
        # mutating returned tensor must not affect state
        out_mut = strat.get_closure(populated_state, 5)
        out_mut.components[:] = 1e6
    # state components unchanged
    for orig, now in zip(snapshot_components, populated_state.tensors):
        np.testing.assert_array_equal(orig, now.components)


def test_c03b_within_tower_returns_copy(populated_state) -> None:
    """Within-tower query must also return a defensive copy."""
    closure = FreeStreamingClosure(k_mpc_inv=1.0, eta=5.0)
    original = populated_state.tensors[2].components.copy()
    t = closure.get_closure(populated_state, 2)
    t.components[0] = 99.0
    np.testing.assert_array_equal(
        populated_state.tensors[2].components, original,
    )


# ════════════════════════════════════════════════════════════════════
#   C-04: FreeStreamingClosure with k = 0 degenerates to HardCut
# ════════════════════════════════════════════════════════════════════

def test_c04_freestream_k_zero_is_hardcut(populated_state) -> None:
    fs = FreeStreamingClosure(k_mpc_inv=0.0, eta=100.0)
    hc = HardCutClosure()
    for ell_req in (5, 6):
        fs_out = fs.get_closure(populated_state, ell_req)
        hc_out = hc.get_closure(populated_state, ell_req)
        np.testing.assert_allclose(
            fs_out.components, hc_out.components, rtol=0, atol=0,
        )


def test_c04b_freestream_eta_zero_is_hardcut(populated_state) -> None:
    """At eta=0 (k·η = 0), the closure must also return zero."""
    fs = FreeStreamingClosure(k_mpc_inv=1.0, eta=0.0)
    out = fs.get_closure(populated_state, 5)
    assert np.all(out.components == 0.0)


# ════════════════════════════════════════════════════════════════════
#   C-05: Ma-Bertschinger 1995 eq (53) scalar recursion
# ════════════════════════════════════════════════════════════════════

def test_c05_freestream_matches_ma_bertschinger_recursion() -> None:
    """Ma-Bertschinger 1995 §6 eq (53):
        Π_{L+1} = ((2L+1) / (kη)) Π_L − Π_{L-1}
    applied per m-slot in the real-SH packing.
    """
    # Build a tower with a known axisymmetric (m=0 only) profile.
    L = 4
    tensors = []
    for ell in range(L + 1):
        comp = np.zeros(2 * ell + 1, dtype=np.float64)
        comp[ell] = 1.0 + 0.37 * ell   # non-trivial per-rank values at m=0
        tensors.append(PSTFTensor(ell=ell, components=comp))
    state = PSTFHierarchyState(L=L, tensors=tensors)

    k = 0.03
    eta = 1.2e3
    fs = FreeStreamingClosure(k_mpc_inv=k, eta=eta)

    out = fs.get_closure(state, L + 1)
    # Expected m=0 scalar per MB eq 53
    expected_m0 = (
        (2 * L + 1) / (k * eta) * state.tensors[L].components[L]
        - state.tensors[L - 1].components[L - 1]
    )
    # Index L+1 in the length (2(L+1)+1 = 9) array is the m=0 slot
    assert np.isclose(out.components[L + 1], expected_m0, rtol=0, atol=1e-12)
    # Other slots contain only Π_L (no Π_{L-1} extension since m=0 axisym)
    for idx, val in enumerate(out.components):
        if idx == L + 1:
            continue
        # These slots only receive from Π_L[m] scaled by coeff if the m-slot
        # exists in both, but here Π_L is zero-except-m=0; same for Π_{L-1}.
        assert np.isclose(val, 0.0, atol=1e-12), (
            f"slot {idx}: expected ~0 for axisymmetric state, got {val}"
        )


def test_c05b_freestream_per_m_recursion_off_axis() -> None:
    """Per-m recursion: every m-slot picks up the scalar recursion using
    the matching slot in Π_L and Π_{L-1}.
    """
    L = 3
    # Hand-constructed: all ones → each m slot same magnitude
    tensors = [PSTFTensor(ell=ell, components=np.ones(2 * ell + 1))
               for ell in range(L + 1)]
    state = PSTFHierarchyState(L=L, tensors=tensors)
    k, eta = 2.0, 0.5
    coeff = (2 * L + 1) / (k * eta)     # = 7 / 1 = 7
    fs = FreeStreamingClosure(k_mpc_inv=k, eta=eta)
    out = fs.get_closure(state, L + 1)
    # For m in [-(L-1), +(L-1)] = [-2, +2]: coeff * 1 - 1 = coeff-1 = 6
    # For m = ±L = ±3: coeff * 1 - 0 = coeff = 7  (Π_{L-1} has no such m)
    # For m = ±(L+1) = ±4: 0 - 0 = 0
    expected = np.array([0.0, coeff, coeff - 1, coeff - 1, coeff - 1,
                         coeff - 1, coeff - 1, coeff, 0.0])
    np.testing.assert_allclose(out.components, expected, rtol=0, atol=1e-13)


# ════════════════════════════════════════════════════════════════════
#   C-06: Recursion applied twice for the ell+2 slot
# ════════════════════════════════════════════════════════════════════

def test_c06_freestream_two_step_recursion() -> None:
    """``get_closure(state, L+2)`` applies the MB recursion twice.

    Verified by hand-rolling the two-step calculation from Π_L and
    Π_{L-1} via an intermediate Π_{L+1}.
    """
    L = 3
    # Axisymmetric m=0 profile
    tensors = []
    for ell in range(L + 1):
        comp = np.zeros(2 * ell + 1, dtype=np.float64)
        comp[ell] = 1.0    # Π_0=1, Π_1[m=0]=1, Π_2[m=0]=1, Π_3[m=0]=1
        tensors.append(PSTFTensor(ell=ell, components=comp))
    state = PSTFHierarchyState(L=L, tensors=tensors)

    k, eta = 0.5, 10.0
    fs = FreeStreamingClosure(k_mpc_inv=k, eta=eta)

    # Step 1: Π_{L+1}[m=0] = (2L+1)/(kη) × Π_L[m=0] − Π_{L-1}[m=0]
    coeff_L = (2 * L + 1) / (k * eta)
    Pi_Lp1_m0 = coeff_L * 1.0 - 1.0
    # Step 2: Π_{L+2}[m=0] = (2(L+1)+1)/(kη) × Π_{L+1}[m=0] − Π_L[m=0]
    coeff_Lp1 = (2 * (L + 1) + 1) / (k * eta)
    Pi_Lp2_m0 = coeff_Lp1 * Pi_Lp1_m0 - 1.0

    out = fs.get_closure(state, L + 2)
    # Index (L+2) in the length-(2(L+2)+1) = 11 array is the m=0 slot
    assert np.isclose(out.components[L + 2], Pi_Lp2_m0, rtol=0, atol=1e-12), (
        f"got {out.components[L+2]}, expected {Pi_Lp2_m0}"
    )


# ════════════════════════════════════════════════════════════════════
#   C-07: PowerLaw scaling at L+1
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("alpha", [1.0, 2.0, 3.0, 2.7])
def test_c07_powerlaw_scaling_at_ell_plus_1(populated_state, alpha) -> None:
    pl = PowerLawExtrapolationClosure(alpha=alpha)
    L = populated_state.L
    out = pl.get_closure(populated_state, L + 1)

    scale = (L / (L + 1)) ** alpha
    # m-slots -L..+L of Π_L get lifted into indices (L+1 + m) = 1..2L+1
    for m in range(-L, L + 1):
        src = populated_state.tensors[L].components[L + m]
        dst = out.components[(L + 1) + m]
        assert np.isclose(dst, scale * src, rtol=0, atol=1e-14), (
            f"m={m}: dst={dst}, expected {scale * src}"
        )
    # Outer slots m = ±(L+1) should be zero
    assert out.components[0] == 0.0
    assert out.components[-1] == 0.0


# ════════════════════════════════════════════════════════════════════
#   C-08: PowerLaw scaling at L+2
# ════════════════════════════════════════════════════════════════════

def test_c08_powerlaw_scaling_at_ell_plus_2(populated_state) -> None:
    alpha = 2.0
    pl = PowerLawExtrapolationClosure(alpha=alpha)
    L = populated_state.L
    out = pl.get_closure(populated_state, L + 2)

    scale = (L / (L + 2)) ** alpha
    for m in range(-L, L + 1):
        src = populated_state.tensors[L].components[L + m]
        dst = out.components[(L + 2) + m]
        assert np.isclose(dst, scale * src, rtol=0, atol=1e-14)
    # Outer slots |m| = L+1, L+2 zero
    assert out.components[0] == 0.0
    assert out.components[1] == 0.0
    assert out.components[-1] == 0.0
    assert out.components[-2] == 0.0


def test_c08b_powerlaw_alpha_zero_raises() -> None:
    with pytest.raises(ValueError):
        PowerLawExtrapolationClosure(alpha=0.0)
    with pytest.raises(ValueError):
        PowerLawExtrapolationClosure(alpha=-1.0)


# ════════════════════════════════════════════════════════════════════
#   C-09: TCA override_at_ell
# ════════════════════════════════════════════════════════════════════

def test_c09_tca_override_at_ell_2_only() -> None:
    tca = TCAClosure(inner=HardCutClosure())
    assert tca.override_at_ell(2) is True
    for ell in (0, 1, 3, 4, 5, 6, 7, 8):
        assert tca.override_at_ell(ell) is False, (
            f"override should be False at ell={ell}"
        )
    with pytest.raises(ValueError):
        tca.override_at_ell(-1)


# ════════════════════════════════════════════════════════════════════
#   C-10: algebraic_closure bit-identical to solve_tca_closure
# ════════════════════════════════════════════════════════════════════

def test_c10_algebraic_closure_bit_identical_to_w604() -> None:
    S_T, S_E = 3.3e-7, -1.2e-7
    Gamma_T = 1.0            # Mpc⁻¹
    H_local = 1e-4           # Mpc⁻¹; Γ_T / H = 1e4 >> default threshold 100
    state = zero_hierarchy(L=4)
    tca = TCAClosure(inner=HardCutClosure(), gamma_threshold_over_H=100.0)

    theta_2_expected, E_2_expected = solve_tca_closure(
        S_T=S_T, S_E=S_E, gamma_T=Gamma_T, decision=_allowing_decision(),
    )
    pstf = tca.algebraic_closure(
        state, 2, 0.0,
        source_T=S_T, source_E=S_E, Gamma_T=Gamma_T, H_local=H_local,
    )
    # m = 0 slot (index 2 of the length-5 array) carries Θ_2
    assert np.isclose(pstf.components[2], theta_2_expected, rtol=0, atol=1e-14)
    for idx in (0, 1, 3, 4):
        assert pstf.components[idx] == 0.0

    # And the companion scalar method returns both (Θ_2, E_2) bit-identical
    theta_2_got, E_2_got = tca.tca_scalars(
        source_T=S_T, source_E=S_E, Gamma_T=Gamma_T, H_local=H_local,
    )
    assert theta_2_got == theta_2_expected
    assert E_2_got == E_2_expected


# ════════════════════════════════════════════════════════════════════
#   C-11: Below threshold, algebraic_closure raises
# ════════════════════════════════════════════════════════════════════

def test_c11_below_threshold_algebraic_closure_raises() -> None:
    tca = TCAClosure(inner=HardCutClosure(), gamma_threshold_over_H=100.0)
    state = zero_hierarchy(L=2)
    # Γ_T / H = 10 / 1 = 10 < 100
    with pytest.raises(RuntimeError, match="TCA inactive"):
        tca.algebraic_closure(
            state, 2, 0.0,
            source_T=1.0, source_E=0.0, Gamma_T=10.0, H_local=1.0,
        )


def test_c11b_algebraic_closure_rejects_non_quadrupole_ell() -> None:
    tca = TCAClosure(inner=HardCutClosure())
    state = zero_hierarchy(L=4)
    for ell in (0, 1, 3, 4):
        with pytest.raises(ValueError, match="handles ell=2 only"):
            tca.algebraic_closure(
                state, ell, 0.0,
                source_T=1.0, source_E=0.0, Gamma_T=1.0, H_local=1e-4,
            )


# ════════════════════════════════════════════════════════════════════
#   C-12: TCAClosure.get_closure delegates to inner
# ════════════════════════════════════════════════════════════════════

def test_c12_tca_get_closure_delegates_to_inner(populated_state) -> None:
    for inner in (HardCutClosure(),
                  FreeStreamingClosure(k_mpc_inv=1.0, eta=10.0),
                  PowerLawExtrapolationClosure(alpha=2.0)):
        tca = TCAClosure(inner=inner)
        for ell_req in (5, 6):
            inner_out = inner.get_closure(populated_state, ell_req)
            tca_out = tca.get_closure(populated_state, ell_req)
            np.testing.assert_allclose(
                tca_out.components, inner_out.components,
                rtol=0, atol=0,
            )
            assert tca_out.ell == inner_out.ell == ell_req


# ════════════════════════════════════════════════════════════════════
#   Factory + validation
# ════════════════════════════════════════════════════════════════════

def test_factory_returns_expected_types() -> None:
    assert isinstance(
        build_default_closure(4, "hardcut"), HardCutClosure,
    )
    assert isinstance(
        build_default_closure(4, "freestream", k_mpc_inv=0.1),
        FreeStreamingClosure,
    )
    assert isinstance(
        build_default_closure(4, "powerlaw", alpha=2.0),
        PowerLawExtrapolationClosure,
    )
    tca = build_default_closure(4, "tca", k_mpc_inv=0.1)
    assert isinstance(tca, TCAClosure)
    assert isinstance(tca.inner, FreeStreamingClosure)
    # k=0 'tca' path should wrap HardCut
    tca_bg = build_default_closure(4, "tca", k_mpc_inv=0.0)
    assert isinstance(tca_bg.inner, HardCutClosure)


def test_factory_unknown_strategy_raises() -> None:
    with pytest.raises(ValueError, match="Unknown strategy_name"):
        build_default_closure(4, "bogus")


def test_factory_case_insensitive_names() -> None:
    assert isinstance(
        build_default_closure(4, "HardCut"), HardCutClosure,
    )
    assert isinstance(
        build_default_closure(4, "  FREESTREAM "), FreeStreamingClosure,
    )


def test_factory_negative_L_raises() -> None:
    with pytest.raises(ValueError, match="L_max"):
        build_default_closure(-1, "hardcut")


# ════════════════════════════════════════════════════════════════════
#   Additional edge cases
# ════════════════════════════════════════════════════════════════════

def test_freestream_validates_inputs() -> None:
    with pytest.raises(ValueError):
        FreeStreamingClosure(k_mpc_inv=-0.1, eta=1.0)
    with pytest.raises(ValueError):
        FreeStreamingClosure(k_mpc_inv=float("nan"), eta=1.0)
    with pytest.raises(ValueError):
        FreeStreamingClosure(k_mpc_inv=0.1, eta=float("inf"))


def test_freestream_with_eta_returns_new_instance() -> None:
    fs = FreeStreamingClosure(k_mpc_inv=1.0, eta=0.0)
    fs2 = fs.with_eta(123.4)
    assert fs2.k_mpc_inv == fs.k_mpc_inv
    assert fs2.eta == 123.4
    assert fs.eta == 0.0     # original frozen


def test_negative_ell_rejected_by_all_strategies(populated_state) -> None:
    for strat in (
        FreeStreamingClosure(k_mpc_inv=1.0, eta=1.0),
        PowerLawExtrapolationClosure(alpha=2.0),
    ):
        with pytest.raises(ValueError):
            strat.get_closure(populated_state, -1)


def test_tca_rejects_bad_inner() -> None:
    class _NotAClosure:
        pass
    with pytest.raises(TypeError):
        TCAClosure(inner=_NotAClosure())
    with pytest.raises(ValueError):
        TCAClosure(inner=HardCutClosure(), gamma_threshold_over_H=-1.0)


# Silence unused-import warning on zero_pstf (kept for parity with the
# closure_interface test module).
_ = zero_pstf
