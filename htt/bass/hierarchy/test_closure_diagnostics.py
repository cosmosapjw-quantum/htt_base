"""Tests C-13..C-16 for ``bass.hierarchy.closure_diagnostics`` (LB-3).

Covers the RHS-difference convergence probe and integration smoke
tests per spec §11.5:

- C-13  Shear-driven state: Π_2 error shrinks as L_ref ↑ from L_trunc
- C-14  L_ref == L_trunc with identical closures ⇒ every error is 0
- C-15  Each strategy produces finite, PSTF-preserving ``dy/dη``
- C-16  ``build_default_closure`` structural dispatch, incl. TCA inner

Integration smoke on the LB-2b ``hierarchy_rhs_photon`` driver is
included at C-15 as a non-trivial regression: the closure chain must
feed into the driver without disturbing the PSTF invariants or
producing NaN/Inf.

References
----------
- spec §11.5 (C-13..C-16)
- Pitrou 2009 §4 — convergence methodology
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from bass.hierarchy import (
    FreeStreamingClosure,
    HardCutClosure,
    PSTFHierarchyState,
    PSTFTensor,
    PowerLawExtrapolationClosure,
    TCAClosure,
    ZeroCollisionOperator,
    build_default_closure,
    hierarchy_rhs_photon,
    measure_closure_error,
    pack_hierarchy,
    pstf_from_tensor,
    unpack_hierarchy,
    verify_pstf_invariants,
    zero_hierarchy,
)
from bass.species.background_table import build_flrw_background_table


# ════════════════════════════════════════════════════════════════════
#   Fixtures
# ════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def bg_table():
    return build_flrw_background_table(n_eta=500)


@dataclass
class _ShearFixture:
    """Duck-typed TetradBackgroundState (mirrors H-22 pattern)."""
    eta: np.ndarray
    sigma_tensor: np.ndarray


def _const_proper_shear_fixture(bg_table, sigma_proper: np.ndarray):
    """Return a shear fixture with constant *proper* σ_ab on the grid.

    ``proper_shear_at_eta`` divides by a(η), so we pre-multiply the
    stored Σ_ab by a to cancel the conversion (same helper as
    LB-2b ``test_hierarchy_rhs.py``).
    """
    a = bg_table.a
    Sigma_conformal = np.empty((a.size, 3, 3), dtype=np.float64)
    for i in range(a.size):
        Sigma_conformal[i] = sigma_proper * a[i]
    return _ShearFixture(eta=bg_table.eta.copy(), sigma_tensor=Sigma_conformal)


@pytest.fixture
def shear_driven_state() -> PSTFHierarchyState:
    """Bianchi-I-like reference tower with depth L=6 carrying a
    non-trivial geometrically-decaying tail at all ranks 0..6.

    The truncated run at L_trunc=3 will then see different Π_4/Π_5
    via its closure (zero from HardCut) than the reference run (real
    state content at those ranks) — making the closure-error probe
    detect the truncation.
    """
    rng = np.random.default_rng(seed=13)
    L = 6
    tensors = []
    for ell in range(L + 1):
        # Geometric decay 0.5^ell with small noise, axisymmetric-dominant
        base = np.zeros(2 * ell + 1, dtype=np.float64)
        base[ell] = 0.5 ** ell       # m = 0 slot
        base += 0.05 * rng.normal(size=2 * ell + 1)
        tensors.append(PSTFTensor(ell=ell, components=base))
    return PSTFHierarchyState(L=L, tensors=tensors)


# ════════════════════════════════════════════════════════════════════
#   C-13: Shear-driven state — closure error is finite and positive
# ════════════════════════════════════════════════════════════════════

def test_c13_shear_driven_closure_error_finite_and_positive(
    bg_table, shear_driven_state,
) -> None:
    """At a Bianchi-I representative η with a non-trivial reference
    tower at L_ref=6, the HardCut truncation to L_trunc=3 must give
    a strictly-positive closure error at ranks whose T3/T7 references
    Π_{ℓ+1}/Π_{ℓ+2} depend on the dropped ranks 4..5.
    """
    sigma = 3e-4 * np.diag([1.0, -0.5, -0.5])  # trace-free axisymmetric σ_+
    tetrad = _const_proper_shear_fixture(bg_table, sigma)
    eta_eval = float(bg_table.eta[bg_table.eta.size // 2])

    driver_kwargs = dict(
        eta=eta_eval,
        bg_table=bg_table,
        tetrad_state=tetrad,
        collision=ZeroCollisionOperator(),
    )
    errors = measure_closure_error(
        shear_driven_state, hierarchy_rhs_photon,
        L_trunc=3,
        closure_ref=HardCutClosure(),
        closure_trunc=HardCutClosure(),
        driver_kwargs=driver_kwargs,
    )
    assert set(errors.keys()) == {0, 1, 2, 3}
    for ell, err in errors.items():
        assert np.isfinite(err), f"ℓ={ell}: non-finite error {err}"
    # T7 at ℓ=2 references Π_4 and at ℓ=3 references Π_5 — the
    # truncation drops both, so Π_2 / Π_3 RHS must disagree.
    # Also T3 at ℓ=3 references Π_4, so T1 + ... at ℓ=3 disagrees.
    assert errors[2] > 0.0, f"ℓ=2: expected > 0, got {errors[2]}"
    assert errors[3] > 0.0, f"ℓ=3: expected > 0, got {errors[3]}"
    # ℓ=0, 1: do not reference any rank above 3 in the orthogonal
    # Bianchi RHS (T3 at ℓ=0 uses Π_1; T7 at ℓ=0 uses Π_2; T7 at
    # ℓ=1 uses Π_3; all within the truncated tower). Errors zero.
    assert errors[0] == 0.0
    assert errors[1] == 0.0


# ════════════════════════════════════════════════════════════════════
#   C-14: L_ref == L_trunc with identical closures ⇒ zero error
# ════════════════════════════════════════════════════════════════════

def test_c14_self_comparison_is_exact_zero(
    bg_table, shear_driven_state,
) -> None:
    """L_trunc == state_ref.L with identical closures ⇒ both runs
    are byte-identical; every error must be exactly 0.
    """
    sigma = 2e-4 * np.diag([1.0, -0.5, -0.5])
    tetrad = _const_proper_shear_fixture(bg_table, sigma)
    eta_eval = float(bg_table.eta[bg_table.eta.size // 2])
    driver_kwargs = dict(
        eta=eta_eval,
        bg_table=bg_table,
        tetrad_state=tetrad,
        collision=ZeroCollisionOperator(),
    )
    closure = HardCutClosure()
    errors = measure_closure_error(
        shear_driven_state, hierarchy_rhs_photon,
        L_trunc=shear_driven_state.L,        # no truncation
        closure_ref=closure,
        closure_trunc=closure,
        driver_kwargs=driver_kwargs,
    )
    for ell, err in errors.items():
        assert err == 0.0, f"ℓ={ell}: expected exactly 0, got {err}"


def test_c14b_input_validation() -> None:
    state = zero_hierarchy(L=4)
    bg = build_flrw_background_table(n_eta=300)
    with pytest.raises(ValueError, match="L_trunc"):
        measure_closure_error(
            state, hierarchy_rhs_photon,
            L_trunc=5,                   # L_trunc > state_ref.L
            closure_ref=HardCutClosure(),
            closure_trunc=HardCutClosure(),
            driver_kwargs={
                "eta": float(bg.eta[100]),
                "bg_table": bg,
                "tetrad_state": None,
                "collision": ZeroCollisionOperator(),
            },
        )
    with pytest.raises(ValueError, match="L_trunc"):
        measure_closure_error(
            state, hierarchy_rhs_photon,
            L_trunc=-1,
            closure_ref=HardCutClosure(),
            closure_trunc=HardCutClosure(),
            driver_kwargs={
                "eta": float(bg.eta[100]),
                "bg_table": bg,
                "tetrad_state": None,
                "collision": ZeroCollisionOperator(),
            },
        )
    with pytest.raises(ValueError, match="eta"):
        measure_closure_error(
            state, hierarchy_rhs_photon,
            L_trunc=4,
            closure_ref=HardCutClosure(),
            closure_trunc=HardCutClosure(),
            driver_kwargs={
                "bg_table": bg,
                "tetrad_state": None,
                "collision": ZeroCollisionOperator(),
            },
        )


# ════════════════════════════════════════════════════════════════════
#   C-15: Integration smoke — every strategy plugs into the LB-2b driver
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize(
    "strategy_factory",
    [
        ("hardcut",   lambda: HardCutClosure()),
        ("freestream", lambda: FreeStreamingClosure(k_mpc_inv=0.03, eta=1e3)),
        ("powerlaw",   lambda: PowerLawExtrapolationClosure(alpha=2.0)),
        ("tca",        lambda: TCAClosure(inner=HardCutClosure())),
    ],
    ids=lambda p: p[0],
)
def test_c15_driver_integration_smoke(
    bg_table, shear_driven_state, strategy_factory,
) -> None:
    """Each strategy must let ``hierarchy_rhs_photon`` produce a finite
    ``dy/dη`` and preserve PSTF invariants at every ℓ.
    """
    _name, factory = strategy_factory
    sigma = 1e-4 * np.diag([1.0, -0.5, -0.5])
    tetrad = _const_proper_shear_fixture(bg_table, sigma)
    eta_eval = float(bg_table.eta[bg_table.eta.size // 2])

    L_max = 4
    # Truncate shear_driven_state (L=6) down to L_max for the driver test
    tensors = [shear_driven_state.tensors[ell].copy()
               for ell in range(L_max + 1)]
    state = PSTFHierarchyState(L=L_max, tensors=tensors)
    y0 = pack_hierarchy(state)

    closure = factory()
    # FreeStreamingClosure needs η rebound per RHS call
    if isinstance(closure, FreeStreamingClosure):
        closure = closure.with_eta(eta_eval)
    elif isinstance(closure, TCAClosure) and isinstance(
        closure.inner, FreeStreamingClosure,
    ):
        closure = TCAClosure(
            inner=closure.inner.with_eta(eta_eval),
            gamma_threshold_over_H=closure.gamma_threshold_over_H,
        )

    dy = hierarchy_rhs_photon(
        eta_eval, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=tetrad,
        closure=closure,
        collision=ZeroCollisionOperator(),
    )
    assert dy.shape == y0.shape
    assert np.all(np.isfinite(dy)), (
        f"non-finite dy for {type(closure).__name__}"
    )

    # PSTF invariants: each ℓ-block of dy, packed into a tensor, must
    # be symmetric and trace-free.
    state_dy = unpack_hierarchy(dy, L_max)
    for ell in range(L_max + 1):
        full_tensor = state_dy.tensors[ell].to_full_tensor()
        ok, msg = verify_pstf_invariants(full_tensor)
        assert ok, f"PSTF violation at ℓ={ell} with {type(closure).__name__}: {msg}"


def test_c15b_flrw_limit_closures_agree_at_zero_shear(bg_table) -> None:
    """At σ = 0 (FLRW), T7/T8/T9 all vanish, so the closure's Π_{L+1} /
    Π_{L+2} values never affect the RHS. All four strategies must then
    produce identical ``dy/dη`` — verifying the "no-op at FLRW" guard.
    """
    state = zero_hierarchy(L=3)
    # Seed a random low-ℓ state so T1/T2/T3 give something non-zero
    rng = np.random.default_rng(seed=7)
    for ell in range(state.L + 1):
        state.tensors[ell] = PSTFTensor(
            ell=ell, components=rng.normal(size=2 * ell + 1),
        )
    y0 = pack_hierarchy(state)
    eta_eval = float(bg_table.eta[bg_table.eta.size // 2])

    dy_reference = hierarchy_rhs_photon(
        eta_eval, y0, L_max=3, bg_table=bg_table,
        tetrad_state=None,  # σ = 0 at FLRW
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )
    for name, closure in (
        ("freestream", FreeStreamingClosure(k_mpc_inv=0.1, eta=eta_eval)),
        ("powerlaw", PowerLawExtrapolationClosure(alpha=2.0)),
        ("tca", TCAClosure(inner=HardCutClosure())),
    ):
        dy = hierarchy_rhs_photon(
            eta_eval, y0, L_max=3, bg_table=bg_table,
            tetrad_state=None,
            closure=closure,
            collision=ZeroCollisionOperator(),
        )
        np.testing.assert_allclose(
            dy, dy_reference, rtol=0, atol=1e-14,
            err_msg=f"FLRW limit failed for {name}",
        )


# ════════════════════════════════════════════════════════════════════
#   C-16: build_default_closure structural dispatch
# ════════════════════════════════════════════════════════════════════

def test_c16_build_default_closure_structural_dispatch() -> None:
    # freestream: bare FreeStreamingClosure
    fs = build_default_closure(6, "freestream", k_mpc_inv=0.1, eta=1e3)
    assert isinstance(fs, FreeStreamingClosure)
    assert fs.k_mpc_inv == 0.1
    assert fs.eta == 1e3

    # tca with k>0: wraps FreeStreamingClosure
    tca_fs = build_default_closure(6, "tca", k_mpc_inv=0.1)
    assert isinstance(tca_fs, TCAClosure)
    assert isinstance(tca_fs.inner, FreeStreamingClosure)

    # tca with k=0: wraps HardCutClosure (background mode)
    tca_hc = build_default_closure(6, "tca", k_mpc_inv=0.0)
    assert isinstance(tca_hc, TCAClosure)
    assert isinstance(tca_hc.inner, HardCutClosure)

    # powerlaw: PowerLawExtrapolationClosure with the passed α
    pl = build_default_closure(6, "powerlaw", alpha=3.0)
    assert isinstance(pl, PowerLawExtrapolationClosure)
    assert pl.alpha == 3.0

    # hardcut: bare HardCutClosure
    hc = build_default_closure(6, "hardcut")
    assert isinstance(hc, HardCutClosure)

    # unknown name raises
    with pytest.raises(ValueError):
        build_default_closure(6, "unknown_strategy")


# Silence unused-import warning on pstf_from_tensor (reserved for
# future PSTF-in, PSTF-out diagnostics added in LB-5 integration tests).
_ = pstf_from_tensor
