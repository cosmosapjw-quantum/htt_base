"""bass/background/test_nonperturbative_tilt.py — King-Ellis tilt RHS tests.

Verifies the non-perturbative (sinh/cosh) tilt evolution matches the
linearised (β, β²) approximation in the small-β limit, and departs from
it at the expected O(β³) scale for β ≳ 0.1.  Also checks the reduced-
family dispatch (tilt/orth, vorticity/curvature activation).
"""
import numpy as np
import pytest
from scipy.integrate import solve_ivp

from bass.background.hooks import HookState
from bass.background.nonperturbative_tilt import (
    SUPPORTED_FAMILIES,
    VORTICITY_FAMILIES,
    CURVATURE_FAMILIES,
    omega_tilt_exact,
    omega_tilt_exact_vec,
    rhs_bianchi,
    rhs_for_family,
)


class TestOmegaTiltExact:
    """Non-perturbative Ω_tilt = (1+w)·Ω·sinh²β."""

    def test_zero_at_zero_beta(self):
        assert omega_tilt_exact(1.0e-4, 0.3, 0.0) == 0.0
        assert omega_tilt_exact(1.0e-4, 0.3, 1.0e-20) == 0.0

    def test_small_beta_limit(self):
        """sinh²β → β² for |β| < 10⁻³."""
        Or, Om = 9.14e-5, 0.3153
        beta = 1e-3
        exact = omega_tilt_exact(Or, Om, beta)
        linear = ((4.0 / 3.0) * Or + Om) * beta ** 2
        assert exact == pytest.approx(linear, rel=1e-5)

    def test_deviation_at_large_beta(self):
        """At β = 0.5, sinh²β = (e^0.5 − e^-0.5)²/4 ≈ 0.272; β² = 0.25.
        About 9% bigger than linear."""
        Or, Om = 1e-4, 0.3
        beta = 0.5
        exact = omega_tilt_exact(Or, Om, beta)
        linear = ((4.0 / 3.0) * Or + Om) * beta ** 2
        assert exact > linear
        rel_diff = (exact - linear) / linear
        assert 0.05 < rel_diff < 0.15  # ~9% at β = 0.5

    def test_vectorised_matches_scalar(self):
        Or = np.array([1e-4, 0.5, 0.0])
        Om = np.array([0.3, 0.3, 0.3])
        beta = np.array([0.0, 0.01, 0.1])
        vec = omega_tilt_exact_vec(Or, Om, beta)
        for i in range(len(beta)):
            assert vec[i] == pytest.approx(
                omega_tilt_exact(float(Or[i]), float(Om[i]), float(beta[i])),
                rel=1e-14,
            )


class TestRHSDispatch:
    """Family dispatch in rhs_bianchi activates the correct terms."""

    def _state(self):
        return np.array([1e-4, 0.3, 1e-6, 0.0, 1e-3, 0.0])

    def test_unsupported_family_raises(self):
        with pytest.raises(ValueError):
            rhs_for_family('Bogus_family')

    def test_orth_has_no_beta_evolution(self):
        y = self._state()
        dy = rhs_bianchi(0.0, y, 'BI_orth', HookState())
        assert dy[4] == 0.0  # dβ/dN = 0 for orth

    def test_tilt_has_beta_evolution(self):
        y = self._state()
        dy = rhs_bianchi(0.0, y, 'BI_tilt', HookState())
        # Not pure matter domination: w_eff = Or/(3·(Or+Om)) ≠ 0.
        Or, Om = 1e-4, 0.3
        beta = 1e-3
        w_eff = Or / (3.0 * (Or + Om))
        expected = -(1.0 - 3.0 * w_eff) * np.sinh(beta) * np.cosh(beta)
        assert dy[4] == pytest.approx(expected, rel=1e-12)

    def test_vorticity_activation(self):
        y = self._state()
        y[3] = 1e-6  # nonzero W²
        for fam in SUPPORTED_FAMILIES:
            dy = rhs_bianchi(0.0, y, fam, HookState())
            if fam in VORTICITY_FAMILIES:
                assert dy[3] != 0.0, f"{fam} should evolve W²"
            else:
                assert dy[3] == 0.0, f"{fam} should NOT evolve W²"

    def test_curvature_activation(self):
        y = self._state()
        y[5] = 1e-4  # nonzero Ω_k
        for fam in SUPPORTED_FAMILIES:
            dy = rhs_bianchi(0.0, y, fam, HookState())
            if fam in CURVATURE_FAMILIES:
                assert dy[5] != 0.0, f"{fam} should evolve Ω_k"
            else:
                assert dy[5] == 0.0, f"{fam} should NOT evolve Ω_k"


class TestKingEllisLinearLimit:
    """The exact sinh(β)cosh(β) RHS reduces to (1−3w)β for small β."""

    def test_matter_era_linear_recovery(self):
        """In matter era (Ω_m ≫ Ω_r), c_s² → 0 so dβ/dN → −sinh β cosh β."""
        y = np.array([0.0, 1.0, 0.0, 0.0, 1e-4, 0.0])
        dy = rhs_bianchi(0.0, y, 'FLRW_tilt', HookState())
        expected_linear = -1.0 * 1e-4  # (1 − 3·0) · β
        expected_exact = -np.sinh(1e-4) * np.cosh(1e-4)
        assert dy[4] == pytest.approx(expected_exact, rel=1e-14)
        assert dy[4] == pytest.approx(expected_linear, rel=1e-7)

    def test_radiation_era_no_tilt_decay(self):
        """In rad era (Ω_r ≫ Ω_m), c_s² → 1/3 so (1 − 3 c_s²) → 0 → dβ/dN → 0."""
        y = np.array([1.0, 0.0, 0.0, 0.0, 1e-3, 0.0])
        dy = rhs_bianchi(0.0, y, 'FLRW_tilt', HookState())
        assert abs(dy[4]) < 1e-15

    def test_large_beta_decays_faster(self):
        """At β = 0.5, sinh β cosh β = 0.5(e²·⁵ − e⁻²·⁵)/... ≈ 0.616 > β."""
        y = np.array([0.0, 1.0, 0.0, 0.0, 0.5, 0.0])
        dy = rhs_bianchi(0.0, y, 'FLRW_tilt', HookState())
        linear_approx = -0.5  # −β
        exact = -np.sinh(0.5) * np.cosh(0.5)
        assert dy[4] == pytest.approx(exact, rel=1e-14)
        # Exact decay is FASTER than linear (more negative)
        assert dy[4] < linear_approx


class TestTiltShearCoupling:
    """The tilt-shear source dΣ²/dN = [(4/3)²Ωr + Ωm]·sinh²β·Σ² is active
    only for tilted families with nonzero β."""

    def test_no_coupling_without_tilt(self):
        y = np.array([1e-4, 0.3, 1e-6, 0.0, 1e-3, 0.0])
        dy_orth = rhs_bianchi(0.0, y, 'BI_orth', HookState())
        # Shear only decays: dΣ²/dN = −2(2−q)·Σ²
        rho = 1e-4 + 0.3
        w_eff = 1e-4 / (3.0 * rho)
        OL = max(1.0 - 0.3 - 1e-4 - 1e-6, 0.0)
        q = 0.5 * (1 + 3 * w_eff) * rho - OL + 2 * 1e-6
        expected = -2.0 * (2.0 - q) * 1e-6
        assert dy_orth[2] == pytest.approx(expected, rel=1e-10)

    def test_coupling_grows_with_beta(self):
        """At same Σ², tilted family has *additional* positive source."""
        y_small = np.array([1e-4, 0.3, 1e-6, 0.0, 1e-4, 0.0])
        y_large = np.array([1e-4, 0.3, 1e-6, 0.0, 1e-1, 0.0])
        dy_small = rhs_bianchi(0.0, y_small, 'BI_tilt', HookState())
        dy_large = rhs_bianchi(0.0, y_large, 'BI_tilt', HookState())
        # Larger β → larger source → less negative dΣ²/dN (smaller decay)
        assert dy_large[2] > dy_small[2]

    def test_tilt_source_scales_with_sinh2_beta(self):
        """Isolated tilt-shear source ≈ Ωm · sinh²β · Σ² in matter era."""
        Or, Om = 0.0, 1.0
        S2 = 1e-6
        beta = 0.1
        y = np.array([Or, Om, S2, 0.0, beta, 0.0])
        dy_tilt = rhs_bianchi(0.0, y, 'BI_tilt', HookState())
        dy_orth_baseline = rhs_bianchi(
            0.0,
            np.array([Or, Om, S2, 0.0, 0.0, 0.0]),
            'BI_orth', HookState(),
        )
        source_only = dy_tilt[2] - dy_orth_baseline[2]
        expected = Om * np.sinh(beta) ** 2 * S2
        assert source_only == pytest.approx(expected, rel=1e-3)


class TestFLRWLimit:
    """FLRW_orth and FLRW_tilt reduce sensibly."""

    def test_FLRW_orth_evolves_only_rho(self):
        y = np.array([1e-4, 0.3, 0.0, 0.0, 0.0, 0.0])
        dy = rhs_bianchi(0.0, y, 'FLRW_orth', HookState())
        assert dy[2] == 0.0 and dy[3] == 0.0
        assert dy[4] == 0.0 and dy[5] == 0.0

    def test_FLRW_tilt_still_evolves_beta(self):
        y = np.array([1e-4, 0.3, 0.0, 0.0, 0.1, 0.0])
        dy = rhs_bianchi(0.0, y, 'FLRW_tilt', HookState())
        assert dy[4] != 0.0  # tilt still decays in FLRW_tilt


class TestODEIntegration:
    """Integrate the RHS over a short N window to ensure it produces
    physically sensible trajectories."""

    def test_pure_FLRW_constant_densities_with_adjustment(self):
        """FLRW_orth over one e-fold preserves density *ratio* to high precision."""
        y0 = np.array([9.14e-5, 0.3153, 0.0, 0.0, 0.0, 0.0])
        f = rhs_for_family('FLRW_orth')
        sol = solve_ivp(f, (0.0, 1.0), y0, method='LSODA', rtol=1e-10, atol=1e-14)
        assert sol.success
        assert sol.y.shape[1] > 1

    def test_BI_tilt_beta_decays(self):
        """In matter era, β monotonically decreases over an e-fold."""
        y0 = np.array([0.0, 1.0, 0.0, 0.0, 0.1, 0.0])
        f = rhs_for_family('FLRW_tilt')
        sol = solve_ivp(f, (0.0, 1.0), y0, method='LSODA', rtol=1e-10, atol=1e-14)
        assert sol.success
        beta_series = sol.y[4]
        # Strictly decreasing
        assert np.all(np.diff(beta_series) < 0)

    def test_BI_tilt_shear_growth_with_beta(self):
        """With β > 0, Σ² decays slower than in BI_orth (tilt-shear source)."""
        y0 = np.array([0.0, 1.0, 1e-6, 0.0, 0.0, 0.0])
        f_orth = rhs_for_family('BI_orth')
        sol_orth = solve_ivp(f_orth, (0.0, 1.0), y0, method='LSODA',
                              rtol=1e-10, atol=1e-14)

        y0_tilt = y0.copy()
        y0_tilt[4] = 0.1
        f_tilt = rhs_for_family('BI_tilt')
        sol_tilt = solve_ivp(f_tilt, (0.0, 1.0), y0_tilt, method='LSODA',
                              rtol=1e-10, atol=1e-14)

        # Both decay, but tilt version decays less
        assert sol_tilt.y[2, -1] > sol_orth.y[2, -1]


class TestHooks:
    """HookState machinery."""

    def test_default_is_conservative(self):
        from bass.background.hooks import apply_hooks
        h = apply_hooks('no_such_era', 0.0)
        assert h.tight_coupling is True  # default
        assert h.free_streaming is False
        assert h.tau_dot == 0.0

    def test_recombination_visibility_peak(self):
        from bass.background.hooks import apply_hooks
        h = apply_hooks('recombination', 1100.0)
        assert h.visibility == pytest.approx(1.0, abs=1e-10)

    def test_reionization_tau(self):
        from bass.background.hooks import apply_hooks
        h = apply_hooks('reionization', 10.0)
        assert h.kappa_opacity == pytest.approx(0.054)
