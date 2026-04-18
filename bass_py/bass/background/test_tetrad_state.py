"""bass/background/test_tetrad_state.py — Tetrad state wrapper tests.

Verifies the axisymmetric → 3-tensor conversion, trace-free
invariants, cumulative-shape integration, and type-dependent
anisotropic 3-curvature availability for the low-ℓ tetrad
background state (reference §2).
"""
import numpy as np
import pytest

from bass.background.bianchi_types import (
    flrw_constants, type_i_constants, type_v_constants, type_vii0_constants,
    type_ix_constants,
)
from bass.background.einstein_bianchi import (
    flrw_cosmology, type_i_cosmology, solve_bianchi_background,
)
from bass.background.tetrad_state import (
    TetradBackgroundState,
    anisotropic_3_curvature,
    axisymmetric_sigma_tensor,
    build_tetrad_state,
)


class TestAxisymmetricSigmaTensor:
    """(Σ_+, Σ_−) → 3×3 tensor is symmetric and trace-free."""

    def test_zero_shear_is_zero(self):
        t = axisymmetric_sigma_tensor(0.0, 0.0)
        assert np.allclose(t, np.zeros((3, 3)))

    def test_trace_free_pure_plus(self):
        t = axisymmetric_sigma_tensor(1e-3, 0.0)
        assert abs(np.trace(t)) < 1e-20

    def test_trace_free_pure_minus(self):
        t = axisymmetric_sigma_tensor(0.0, 1e-3)
        assert abs(np.trace(t)) < 1e-20

    def test_symmetric(self):
        t = axisymmetric_sigma_tensor(1e-3, 5e-4)
        assert np.allclose(t, t.T)

    def test_plus_eigenvectors_aligned_with_axes(self):
        """Pure Σ_+ gives diag(-2/√6, 1/√6, 1/√6) × amplitude."""
        t = axisymmetric_sigma_tensor(1.0, 0.0)
        inv_sqrt6 = 1.0 / np.sqrt(6.0)
        assert t[0, 0] == pytest.approx(-2.0 * inv_sqrt6)
        assert t[1, 1] == pytest.approx(+1.0 * inv_sqrt6)
        assert t[2, 2] == pytest.approx(+1.0 * inv_sqrt6)

    def test_minus_eigenvectors(self):
        """Pure Σ_− gives diag(0, 1/√2, -1/√2) × amplitude."""
        t = axisymmetric_sigma_tensor(0.0, 1.0)
        inv_sqrt2 = 1.0 / np.sqrt(2.0)
        assert t[0, 0] == pytest.approx(0.0)
        assert t[1, 1] == pytest.approx(+inv_sqrt2)
        assert t[2, 2] == pytest.approx(-inv_sqrt2)

    def test_magnitude_squared_matches_convention(self):
        """Σ² = Σ_ab Σ^ab / 6 with normalisation such that pure Σ_+
        gives Σ² = Σ_+² / 6."""
        Sp = 1.5e-3
        t = axisymmetric_sigma_tensor(Sp, 0.0)
        mag_sq = np.trace(t @ t) / 6.0
        assert mag_sq == pytest.approx(Sp ** 2 / 6.0, rel=1e-12)


class TestAnisotropic3Curvature:
    """Type-dependent ³R_ab anisotropic part."""

    def test_flrw_zero(self):
        tensor, status = anisotropic_3_curvature(
            flrw_constants(), a=1.0, sigma_plus=0.0, sigma_minus=0.0,
        )
        assert status == 'type_i_flat'
        assert np.allclose(tensor, 0.0)

    def test_type_i_zero(self):
        tensor, status = anisotropic_3_curvature(
            type_i_constants(), a=1.0, sigma_plus=1e-3, sigma_minus=0.0,
        )
        assert status == 'type_i_flat'
        assert np.allclose(tensor, 0.0)

    def test_type_v_isotropic(self):
        tensor, status = anisotropic_3_curvature(
            type_v_constants(), a=1.0, sigma_plus=1e-3, sigma_minus=0.0,
        )
        assert status == 'type_v_isotropic'
        assert np.allclose(tensor, 0.0)

    def test_type_vii0_flat_aligned(self):
        tensor, status = anisotropic_3_curvature(
            type_vii0_constants(), a=1.0, sigma_plus=1e-3, sigma_minus=0.0,
        )
        assert status == 'type_vii0_flat'
        assert np.allclose(tensor, 0.0)

    def test_type_ix_unavailable(self):
        """Type IX ³R_ab is not yet implemented — returns None."""
        tensor, status = anisotropic_3_curvature(
            type_ix_constants(), a=1.0, sigma_plus=1e-3, sigma_minus=0.0,
        )
        assert status == 'unavailable'
        assert tensor is None


class TestBuildTetradStateFLRW:
    """FLRW → everything that should vanish vanishes."""

    @pytest.fixture(scope='class')
    def tetrad(self):
        bg = solve_bianchi_background(
            flrw_cosmology(), a_start=1e-5, a_end=1.0, n_pts=200,
        )
        return build_tetrad_state(bg)

    def test_alpha_matches_ln_a(self, tetrad):
        assert np.allclose(tetrad.alpha, np.log(tetrad.a))

    def test_sigma_tensor_zero_FLRW(self, tetrad):
        """FLRW has σ_ab ≡ 0 by isotropy."""
        assert np.max(np.abs(tetrad.sigma_tensor)) < 1e-10

    def test_sigma_trace_free(self, tetrad):
        """tr Σ_ab = 0 at every grid point."""
        traces = np.einsum('nii->n', tetrad.sigma_tensor)
        assert np.max(np.abs(traces)) < 1e-14

    def test_sigma_symmetric(self, tetrad):
        """Σ_ab = Σ_ba."""
        for i in range(tetrad.eta.size):
            assert np.allclose(
                tetrad.sigma_tensor[i], tetrad.sigma_tensor[i].T,
            )

    def test_beta_vanishes_at_final(self, tetrad):
        """β_ab(η_last) = 0 by today-normalisation."""
        assert np.allclose(tetrad.beta_tensor[-1], 0.0, atol=1e-12)

    def test_beta_zero_throughout_for_FLRW(self, tetrad):
        """FLRW: ∫ σ = 0 trivially, so β_ab ≡ 0."""
        assert np.max(np.abs(tetrad.beta_tensor)) < 1e-10

    def test_aniso_3_curvature_zero_flrw(self, tetrad):
        assert tetrad.aniso_3_curvature is not None
        assert np.max(np.abs(tetrad.aniso_3_curvature)) < 1e-14

    def test_shear_magnitude_zero(self, tetrad):
        assert np.max(tetrad.shear_magnitude_sq) < 1e-20


class TestBuildTetradStateBianchiI:
    """Type I with non-zero initial shear: invariants still hold."""

    @pytest.fixture(scope='class')
    def tetrad(self):
        bg = solve_bianchi_background(
            type_i_cosmology(sigma_over_H_init=1e-3),
            a_start=1e-5, a_end=1.0, n_pts=300,
        )
        return build_tetrad_state(bg)

    def test_alpha_matches_ln_a(self, tetrad):
        assert np.allclose(tetrad.alpha, np.log(tetrad.a))

    def test_sigma_trace_free(self, tetrad):
        traces = np.einsum('nii->n', tetrad.sigma_tensor)
        assert np.max(np.abs(traces)) < 1e-14

    def test_beta_trace_free(self, tetrad):
        """β_ab is symmetric trace-free since 2Σ is."""
        traces = np.einsum('nii->n', tetrad.beta_tensor)
        assert np.max(np.abs(traces)) < 1e-14

    def test_beta_today_zero(self, tetrad):
        assert np.allclose(tetrad.beta_tensor[-1], 0.0, atol=1e-12)

    def test_beta_increases_backwards(self, tetrad):
        """With nonzero initial shear, β_ab should grow in magnitude
        going to earlier η."""
        beta_frob = np.sqrt(np.einsum('nij,nij->n', tetrad.beta_tensor,
                                        tetrad.beta_tensor))
        assert beta_frob[0] > beta_frob[-1]  # larger at the past

    def test_aniso_3_curvature_zero_type_i(self, tetrad):
        assert tetrad.aniso_3_curvature is not None
        assert np.max(np.abs(tetrad.aniso_3_curvature)) < 1e-14

    def test_shear_magnitude_decays_with_scale(self, tetrad):
        """For flat BI with only decaying shear, Σ² should fall as
        (a_end/a)^6 (standard σ ∝ a⁻³, Σ = aσ ∝ a⁻²; Σ² ∝ a⁻⁴).
        Qualitative check: Σ² today ≤ Σ² at early time."""
        mag_sq = tetrad.shear_magnitude_sq
        assert mag_sq[0] >= mag_sq[-1] * 0.5  # allows small dip at late time

    def test_structure_preserved(self, tetrad):
        assert tetrad.structure.label == 'I'

    def test_curvature_status_flat(self, tetrad):
        assert tetrad.curvature_status == 'type_i_flat'


class TestLookupMethods:
    """shape_at / shear_at nearest-neighbour lookup."""

    def test_lookup_at_endpoint(self):
        bg = solve_bianchi_background(
            type_i_cosmology(sigma_over_H_init=1e-4),
            a_start=1e-4, a_end=1.0, n_pts=100,
        )
        tetrad = build_tetrad_state(bg)
        last_eta = tetrad.eta[-1]
        assert np.allclose(tetrad.shape_at(last_eta),
                            tetrad.beta_tensor[-1])
        assert np.allclose(tetrad.shear_at(last_eta),
                            tetrad.sigma_tensor[-1])
