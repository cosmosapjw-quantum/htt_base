"""bass/closure/test_reference_cross_check.py — §10 ↔ W6-04 bridge.

Verifies that the low-ℓ Bianchi solver reference §10 quadrupole-aware
TCA closure matches the existing ``bass.closure.quadrupole_tca`` W6-04
implementation to machine precision, up to the documented sign
convention.

Reference §10 formulation:

    0 ≈ S_{2,T}^m + Γ_T [ -(9/10) Θ_2^m  -  (√6/10) E_2^m ]
    0 ≈ S_{2,E}^m + Γ_T [ -(2/5)  E_2^m  -  (3/(5√6)) Θ_2^m ]

    ⇒ Γ_T M · X = -S_ref

    with X = (Θ_2, E_2), M = [[9/10, √6/10], [3/(5√6), 2/5]].

    Θ_2 = -Γ_T^{-1} [ (4/3) S_T - (√6/3) S_E ]
    E_2 = -Γ_T^{-1} [ -(√6/3) S_T + 3 S_E ]

bass_py W6-04 (``solve_tca_closure``) uses the opposite sign
convention for S (Γ_T M · X = +S), giving the same (Θ_2, E_2) when
``S_bass = -S_ref``. The physical contents — the matrix M, the
eigenstructure, and the Π = Θ_2 + E_2 combination — are identical.
"""
import numpy as np
import pytest

from bass.closure.quadrupole_tca import (
    build_tca_matrix,
    solve_tca_closure,
    tca_closure_matrix_solve,
)
from bass.runtime.canonical_decision import (
    CanonicalDecision, make_canonical_decision,
)
from tsc.diagnostics.tangency import compute_D_diagnostic, TangentKind


# Helper: construct a "production-like" decision for TCA tests
def _on_manifold_G(x):
    return np.asarray(x, dtype=float)


def _allow_decision() -> CanonicalDecision:
    tang = compute_D_diagnostic(
        G_field=_on_manifold_G, kind=TangentKind.ONE_FIELD, xi=0, eta=0.0,
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


def _reference_closure_sign_flipped(
    S_T: float, S_E: float, gamma_T: float,
) -> tuple[float, float]:
    """Reference §10 analytic inverse, with S_ref = -S_bass sign flip.

    Returns (Θ_2, E_2) exactly as the reference formula produces for
    a given S_ref. Used to verify ``solve_tca_closure(S_bass)``
    equals ``reference(S_ref = -S_bass)`` — same (Θ_2, E_2).
    """
    inv_gamma = 1.0 / gamma_T
    sqrt6 = np.sqrt(6.0)
    theta_2 = -inv_gamma * ((4.0 / 3.0) * S_T - (sqrt6 / 3.0) * S_E)
    E_2 = -inv_gamma * (-(sqrt6 / 3.0) * S_T + 3.0 * S_E)
    return theta_2, E_2


class TestMatrixStructure:
    """Reference §10 matrix M = [[9/10, √6/10], [3/(5√6), 2/5]]."""

    def test_matrix_entries(self):
        gamma_T = 1.0
        M = build_tca_matrix(gamma_T) / gamma_T  # strip the Γ_T scaling
        sqrt6 = np.sqrt(6.0)
        expected = np.array([
            [9.0 / 10.0,   sqrt6 / 10.0],
            [3.0 / (5.0 * sqrt6),   2.0 / 5.0],
        ])
        assert np.allclose(M, expected, rtol=1e-14)

    def test_matrix_determinant(self):
        """det M = 9/10 × 2/5 − √6/10 × 3/(5√6) = 18/50 − 3/50 = 15/50 = 0.3."""
        M = build_tca_matrix(1.0)
        det = float(np.linalg.det(M))
        assert det == pytest.approx(0.3, rel=1e-14)

    def test_matrix_symmetric_after_sqrt_scaling(self):
        """The (Θ, E) coupling isn't symmetric in raw indices but is
        symmetric when expressed in Π = Θ_2 + E_2 amplitude basis.
        We don't test that rotation here; just confirm the raw matrix."""
        M = build_tca_matrix(1.0)
        assert M[0, 0] != M[1, 1]


class TestSignConventionEquivalence:
    """bass_py W6-04 (S_bass) ≡ reference §10 (S_ref = -S_bass)."""

    @pytest.mark.parametrize("S_T,S_E,gamma_T", [
        (1.0e-3, 0.0, 1.0),
        (0.0, 1.0e-3, 1.0),
        (1.0e-3, 5.0e-4, 10.0),
        (2.5e-3, -1.0e-3, 0.5),
        (-1.0e-3, 3.0e-4, 100.0),
    ])
    def test_closure_matches_reference(self, S_T, S_E, gamma_T):
        dec = _allow_decision()
        theta_bass, E_bass = solve_tca_closure(S_T, S_E, gamma_T, dec)
        theta_ref, E_ref = _reference_closure_sign_flipped(
            -S_T, -S_E, gamma_T,
        )
        assert theta_bass == pytest.approx(theta_ref, rel=1e-14)
        assert E_bass == pytest.approx(E_ref, rel=1e-14)

    def test_numerical_vs_analytic_inverse(self):
        """np.linalg.solve agrees with the closed-form inverse."""
        dec = _allow_decision()
        for S_T, S_E, gamma_T in [
            (1.0e-3, 5.0e-4, 1.0),
            (2.0e-3, -1.0e-3, 50.0),
        ]:
            analytic = solve_tca_closure(S_T, S_E, gamma_T, dec)
            numeric = tca_closure_matrix_solve(S_T, S_E, gamma_T, dec)
            assert analytic[0] == pytest.approx(numeric[0], rel=1e-12)
            assert analytic[1] == pytest.approx(numeric[1], rel=1e-12)


class TestLeadingOrderSubcases:
    """Specific reference §10 limits."""

    def test_ST_only_gives_reference_ratio(self):
        """With S_E = 0: Θ_2 = (4/3) S_T / Γ_T, E_2 = -(√6/3) S_T / Γ_T.
        Ratio E_2 / Θ_2 = -√6 / 4 is the canonical 'polter' signature
        of Thomson polarization coupling under TCA."""
        dec = _allow_decision()
        theta, E = solve_tca_closure(S_T=1.0e-3, S_E=0.0, gamma_T=1.0,
                                      decision=dec)
        ratio = E / theta
        assert ratio == pytest.approx(-np.sqrt(6.0) / 4.0, rel=1e-12)

    def test_SE_only_dominates(self):
        """With S_T = 0: E_2 = 3 S_E / Γ_T, the dominant channel."""
        dec = _allow_decision()
        theta, E = solve_tca_closure(S_T=0.0, S_E=1.0e-3, gamma_T=10.0,
                                      decision=dec)
        assert E == pytest.approx(3.0 * 1.0e-3 / 10.0, rel=1e-12)
        assert theta == pytest.approx(-(np.sqrt(6.0) / 3.0) * 1.0e-3 / 10.0,
                                       rel=1e-12)

    def test_amplitude_scales_inverse_gamma(self):
        """Doubling Γ_T halves both components for fixed S."""
        dec = _allow_decision()
        theta1, E1 = solve_tca_closure(1e-3, 5e-4, 1.0, dec)
        theta2, E2 = solve_tca_closure(1e-3, 5e-4, 2.0, dec)
        assert theta2 == pytest.approx(0.5 * theta1, rel=1e-14)
        assert E2 == pytest.approx(0.5 * E1, rel=1e-14)
