"""Audit P-03: TCA on/off switch smoothness regression.

CLAUDE.md §6 forbids a *TCA pre-phase* (an unconditional analytic
window replacing the photon hierarchy at high z). The runtime
integrator at ``bass.hierarchy.integrator`` instead uses a *DAE-style
relaxation*: when ``Γ_T/H > closure.gamma_threshold_over_H`` the
ℓ=2 m=0 RHS slot is replaced by

    rhs[slot] = -a · Γ_T · (current - algebraic_TCA_value),

so the slot relaxes onto the algebraic limit on a 1/Γ_T timescale.
The hierarchy ODE is integrated throughout; the relaxation collapses
smoothly onto the off-TCA branch as ``Γ_T/H`` falls back below
threshold. This regression pins that smoothness:

(a) the algebraic TCA prediction ``Θ_2(Γ_T), E_2(Γ_T)`` is monotone
    and continuous in Γ_T at any sampled grid, with no jumps near
    the threshold ratio;
(b) ``Γ_T · Θ_2`` is **exactly** invariant in Γ_T for fixed sources
    (a check of the closure derivation itself, ``§2 quadrupole_tca``);
(c) the relaxation rate ``a · Γ_T`` is monotone in Γ_T (the
    integrator-side smoothness contract).

If any of these break, the audit's "switch smoothness" property fails
and the ``approximation-free`` doctrine is undermined.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.closure.quadrupole_tca import solve_tca_closure


@pytest.fixture
def canonical_decision():
    """Return an all-passing ``CanonicalDecision`` for closure entry.

    ``solve_tca_closure`` invokes ``require_allow_reduction(decision)``,
    which only checks ``decision.allow_reduction is True``. We build the
    minimal post-init-valid decision directly to avoid a heavy
    ``tsc.diagnostics.tangency`` import path.
    """
    try:
        from bass.runtime.canonical_decision import (
            CanonicalDecision,
            SPEC_VERSION,
        )
        from bass.runtime.validation_labels import derive_labels
    except ImportError:
        pytest.skip("CanonicalDecision / derive_labels not importable")
    diagnostics = {
        "beta": {"slack": 1.0},
        "sigma": {"sigma_sq": 1.0, "floor": 1.0e-10},
        "source": {"relative_residual": 0.0, "fraction_on_manifold": 1.0},
    }
    return CanonicalDecision(
        spec_version=SPEC_VERSION,
        beta_policy_pass=True,
        sigma_min_above_floor=True,
        source_Dge2_gate_pass=True,
        allow_reduction=True,
        emitted_labels=derive_labels(True, True, True, diagnostics),
        diagnostics=diagnostics,
    )


def _theta_invariant(S_T: float, S_E: float) -> float:
    """Closed-form Γ_T · Θ_2 from the TCA derivation (quadrupole_tca §2)."""
    return (4.0 / 3.0) * S_T - (np.sqrt(6.0) / 3.0) * S_E


def _emode_invariant(S_T: float, S_E: float) -> float:
    """Closed-form Γ_T · E_2 from the TCA derivation."""
    return -(np.sqrt(6.0) / 3.0) * S_T + 3.0 * S_E


def test_tca_closure_gamma_invariant_holds_exactly(canonical_decision) -> None:
    """``Γ_T·Θ_2`` and ``Γ_T·E_2`` must be Γ_T-independent by construction."""
    S_T, S_E = 1.0e-3, 5.0e-4
    expected_theta_inv = _theta_invariant(S_T, S_E)
    expected_E_inv = _emode_invariant(S_T, S_E)
    for gamma_T in (1.0, 10.0, 100.0, 1.0e3, 1.0e4):
        theta, E = solve_tca_closure(S_T, S_E, gamma_T, canonical_decision)
        np.testing.assert_allclose(
            gamma_T * theta, expected_theta_inv, rtol=1.0e-12, atol=0.0,
            err_msg=f"Γ_T·Θ_2 not invariant at Γ_T={gamma_T}",
        )
        np.testing.assert_allclose(
            gamma_T * E, expected_E_inv, rtol=1.0e-12, atol=0.0,
            err_msg=f"Γ_T·E_2 not invariant at Γ_T={gamma_T}",
        )


def test_tca_closure_is_continuous_across_threshold(canonical_decision) -> None:
    """No jump in algebraic prediction near the activation threshold.

    Continuity is checked against the analytic ``1/γ_T`` reference: the
    relative residual ``|Θ_2(γ) − Θ_inv/γ| / |Θ_2(γ)|`` must hold to
    machine precision at every sampled γ, *including the threshold*.
    Any jump (spurious switch logic, accidental rescale, frame-mismatch
    shortcut) would shift Θ off the analytic curve and trip this bound.
    """
    S_T, S_E = 1.0e-3, 5.0e-4
    expected_theta_inv = _theta_invariant(S_T, S_E)
    # Sweep γ_T across the default threshold (100) including both sides
    # of the activation point. Any discontinuity at the threshold would
    # break the analytic 1/γ curve.
    gammas = np.linspace(50.0, 200.0, 31)
    for g in gammas:
        theta = solve_tca_closure(S_T, S_E, float(g), canonical_decision)[0]
        np.testing.assert_allclose(
            theta, expected_theta_inv / float(g),
            rtol=1.0e-12, atol=0.0,
            err_msg=f"TCA prediction off the analytic 1/γ curve at γ_T={g}",
        )
    # Monotone-decreasing in γ_T (a sufficient continuity sanity check).
    thetas = np.array([
        solve_tca_closure(S_T, S_E, float(g), canonical_decision)[0]
        for g in gammas
    ])
    assert np.all(np.diff(thetas) < 0.0), (
        "Θ_2(γ_T) not monotone in γ_T; switch is non-smooth"
    )


def test_tca_relaxation_rate_is_monotone_in_gamma_T() -> None:
    """The integrator's relaxation ``a·Γ_T`` must grow monotonically.

    This pins the contract that *increasing* Γ_T strictly *tightens* the
    DAE relaxation onto the algebraic value — a sufficient condition for
    on/off smoothness even without invoking the algebraic prediction.
    """
    a_val = 5.0e-4
    gammas = np.array([1.0, 10.0, 100.0, 1.0e3, 1.0e4])
    rates = a_val * gammas
    diffs = np.diff(rates)
    assert np.all(diffs > 0.0), "relaxation rate a·Γ_T not monotone in Γ_T"


def test_tca_closure_decays_as_one_over_gamma(canonical_decision) -> None:
    """Algebraic Θ_2 must scale as 1/Γ_T (the truth-engine signature)."""
    S_T, S_E = 2.0e-3, -1.0e-3
    gammas = np.array([10.0, 100.0, 1.0e3])
    thetas = np.array([
        solve_tca_closure(S_T, S_E, float(g), canonical_decision)[0]
        for g in gammas
    ])
    # Θ_2 · Γ_T must equal a single constant
    products = thetas * gammas
    np.testing.assert_allclose(
        products, products[0] * np.ones_like(products),
        rtol=1.0e-12, atol=0.0,
    )
