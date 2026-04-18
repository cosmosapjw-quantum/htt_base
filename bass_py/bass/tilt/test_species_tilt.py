"""bass/tilt/test_species_tilt.py — Tilted-species decomposition tests.

Verifies the exact-γ formulas of reference §3.2 and their small-v
limits, the trace-free structure of π_ab, and the Bianchi total-
momentum constraint from structure constants.
"""
import numpy as np
import pytest

from bass.background.bianchi_types import (
    flrw_constants, type_i_constants, type_v_constants,
)
from bass.tilt.species_tilt import (
    TiltedSpeciesDecomposition,
    TiltedSpeciesParams,
    decompose_tilted_species,
    small_tilt_limit,
    total_momentum_constraint,
)


# ════════════════════════════════════════════════════════════════════
# TiltedSpeciesParams basics
# ════════════════════════════════════════════════════════════════════

class TestParams:

    def test_zero_velocity_ok(self):
        p = TiltedSpeciesParams(rho_hat=1.0, p_hat=0.0, v=np.zeros(3))
        assert p.v_sq == 0.0
        assert p.gamma == pytest.approx(1.0)

    def test_small_velocity_gamma(self):
        p = TiltedSpeciesParams(
            rho_hat=1.0, p_hat=0.0, v=np.array([0.01, 0.0, 0.0]),
        )
        expected_gamma = 1.0 / np.sqrt(1.0 - 1e-4)
        assert p.gamma == pytest.approx(expected_gamma, rel=1e-14)

    def test_w_radiation(self):
        p = TiltedSpeciesParams(rho_hat=3.0, p_hat=1.0, v=np.zeros(3))
        assert p.w == pytest.approx(1.0 / 3.0)

    def test_w_dust(self):
        p = TiltedSpeciesParams(rho_hat=1.0, p_hat=0.0, v=np.zeros(3))
        assert p.w == 0.0

    def test_rejects_wrong_shape(self):
        with pytest.raises(ValueError):
            TiltedSpeciesParams(
                rho_hat=1.0, p_hat=0.0, v=np.array([0.0, 0.0]),
            )

    def test_rejects_superluminal(self):
        with pytest.raises(ValueError):
            TiltedSpeciesParams(
                rho_hat=1.0, p_hat=0.0, v=np.array([1.0, 0.0, 0.0]),
            )


# ════════════════════════════════════════════════════════════════════
# Exact decomposition
# ════════════════════════════════════════════════════════════════════

class TestExactDecomposition:
    """Exact μ_s, q_a, p_s, π_ab for general γ."""

    def test_zero_velocity_gives_isotropic(self):
        """v = 0: μ = ρ̂, q = 0, p = p̂, π = 0."""
        p = TiltedSpeciesParams(rho_hat=1.0, p_hat=0.5, v=np.zeros(3))
        d = decompose_tilted_species(p)
        assert d.mu == pytest.approx(1.0)
        assert np.allclose(d.q, 0.0)
        assert d.p == pytest.approx(0.5)
        assert np.allclose(d.pi, 0.0)

    def test_radiation_large_boost(self):
        """γ² = 1/(1−v²); at v = 0.5, γ² = 4/3. For radiation (w = 1/3):
            μ = (4/3)(ρ̂ + p̂) − p̂ = (4/3)(4/3 ρ̂) − ρ̂/3
              = 16/9 ρ̂ − 1/3 ρ̂ = (16/9 − 3/9) ρ̂ = 13/9 ρ̂
        """
        v = np.array([0.5, 0.0, 0.0])
        rho = 3.0
        p_hat = 1.0
        par = TiltedSpeciesParams(rho_hat=rho, p_hat=p_hat, v=v)
        d = decompose_tilted_species(par)
        gamma_sq = 1.0 / (1.0 - 0.25)
        expected_mu = gamma_sq * (rho + p_hat) - p_hat
        assert d.mu == pytest.approx(expected_mu, rel=1e-14)

    def test_pi_symmetric_traceless(self):
        """π_ab is symmetric and trace-free by construction."""
        v = np.array([0.1, 0.05, 0.03])
        par = TiltedSpeciesParams(rho_hat=1.0, p_hat=0.0, v=v)
        d = decompose_tilted_species(par)
        assert np.allclose(d.pi, d.pi.T)
        assert abs(d.trace_pi) < 1e-14

    def test_q_parallel_to_v(self):
        """q_a = γ² (ρ̂ + p̂) v_a — colinear with v."""
        v = np.array([0.1, 0.2, 0.05])
        par = TiltedSpeciesParams(rho_hat=1.0, p_hat=0.0, v=v)
        d = decompose_tilted_species(par)
        # Direction: q/|q| = v/|v|
        q_dir = d.q / np.linalg.norm(d.q)
        v_dir = v / np.linalg.norm(v)
        assert np.allclose(q_dir, v_dir, atol=1e-14)

    def test_pressure_enhancement(self):
        """p_s ≥ p̂ whenever v ≠ 0 and ρ̂ + p̂ > 0."""
        v = np.array([0.1, 0.0, 0.0])
        par = TiltedSpeciesParams(rho_hat=1.0, p_hat=0.3, v=v)
        d = decompose_tilted_species(par)
        assert d.p > par.p_hat


# ════════════════════════════════════════════════════════════════════
# Small-tilt limit consistency
# ════════════════════════════════════════════════════════════════════

class TestSmallTiltLimit:
    """The explicit leading-order formula matches the exact γ-series."""

    @pytest.mark.parametrize("v_scale", [1e-4, 1e-3, 1e-2])
    def test_mu_matches_leading(self, v_scale):
        """μ_exact − μ_leading = O(v⁴)."""
        v = np.array([v_scale, 0.0, 0.0])
        par = TiltedSpeciesParams(rho_hat=1.0, p_hat=0.0, v=v)
        d_exact = decompose_tilted_species(par)
        d_leading = small_tilt_limit(par)
        residual = abs(d_exact.mu - d_leading.mu)
        v_sq = v_scale ** 2
        # Leading difference is O(v⁴) — specifically rho_plus_p × v⁴ × γ⁴ / (1−v²)
        assert residual < 10.0 * v_sq ** 2

    @pytest.mark.parametrize("v_scale", [1e-4, 1e-3, 1e-2])
    def test_q_matches_leading(self, v_scale):
        """q_exact − q_leading = (γ² − 1)(ρ̂+p̂) v_a ≈ v³ × (ρ̂+p̂)."""
        v = np.array([v_scale, 0.0, 0.0])
        par = TiltedSpeciesParams(rho_hat=1.0, p_hat=0.0, v=v)
        d_exact = decompose_tilted_species(par)
        d_leading = small_tilt_limit(par)
        diff = np.linalg.norm(d_exact.q - d_leading.q)
        assert diff < 10.0 * v_scale ** 3

    @pytest.mark.parametrize("v_scale", [1e-4, 1e-3, 1e-2])
    def test_pi_matches_leading(self, v_scale):
        v = np.array([v_scale, 0.0, 0.0])
        par = TiltedSpeciesParams(rho_hat=1.0, p_hat=0.0, v=v)
        d_exact = decompose_tilted_species(par)
        d_leading = small_tilt_limit(par)
        frob = np.linalg.norm(d_exact.pi - d_leading.pi)
        # π correction is O(v⁴) × (ρ̂+p̂)
        assert frob < 10.0 * v_scale ** 4

    def test_leading_q_is_rho_plus_p_times_v(self):
        """Pure leading: q_a = (ρ̂ + p̂) v_a, no γ² factor."""
        v = np.array([0.001, 0.0, 0.0])
        par = TiltedSpeciesParams(rho_hat=2.0, p_hat=1.0, v=v)
        d = small_tilt_limit(par)
        assert d.q[0] == pytest.approx((2.0 + 1.0) * 0.001, rel=1e-14)


# ════════════════════════════════════════════════════════════════════
# Total momentum constraint
# ════════════════════════════════════════════════════════════════════

class TestTotalMomentumConstraint:
    """Reference eq 226: 8π P_i^(tot) from structure + shear."""

    def test_flrw_zero(self):
        """FLRW: no structure constants, no shear → P = 0."""
        P = total_momentum_constraint(
            flrw_constants(), np.zeros((3, 3)), alpha=0.0,
        )
        assert np.allclose(P, 0.0)

    def test_type_i_zero_by_structure(self):
        """Type I has n_i = a = 0, so C^i_{jk} ≡ 0, hence P = 0 for
        any shear."""
        sigma = np.diag([1.0, -0.5, -0.5])
        P = total_momentum_constraint(
            type_i_constants(), sigma, alpha=0.0,
        )
        assert np.allclose(P, 0.0, atol=1e-14)

    def test_type_v_with_aligned_shear(self):
        """Type V has a_y = a_twist ≠ 0, so C^i_{jk} is nonzero and
        a diagonal shear with σ_yy ≠ 0 produces a finite P_y."""
        tc = type_v_constants(a_twist=1e-2)
        sigma = np.diag([0.0, 1e-3, 0.0])
        P = total_momentum_constraint(tc, sigma, alpha=0.0)
        # At least one component nonzero; no strict expected magnitude
        # but we check the result is finite and the α scaling is right.
        assert np.all(np.isfinite(P))

    def test_alpha_scaling(self):
        """P ∝ e^{−α}: doubling α→α+ln2 halves P."""
        tc = type_v_constants(a_twist=1e-2)
        sigma = np.diag([0.0, 1e-3, 0.0])
        P1 = total_momentum_constraint(tc, sigma, alpha=0.0)
        P2 = total_momentum_constraint(tc, sigma, alpha=np.log(2.0))
        assert np.allclose(P2, 0.5 * P1, rtol=1e-12)

    def test_linear_in_shear(self):
        """P[σ + σ'] = P[σ] + P[σ'] (linearity in shear)."""
        tc = type_v_constants(a_twist=1e-2)
        s1 = np.diag([0.0, 1e-3, 0.0])
        s2 = np.diag([1e-3, 0.0, -1e-3])
        P1 = total_momentum_constraint(tc, s1, alpha=0.0)
        P2 = total_momentum_constraint(tc, s2, alpha=0.0)
        P12 = total_momentum_constraint(tc, s1 + s2, alpha=0.0)
        assert np.allclose(P12, P1 + P2, rtol=1e-12)
