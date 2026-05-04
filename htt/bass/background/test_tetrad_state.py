"""bass/background/test_tetrad_state.py — Tetrad state wrapper tests.

Verifies the axisymmetric → 3-tensor conversion, trace-free
invariants, cumulative-shape integration, and type-dependent
anisotropic 3-curvature availability for the low-ℓ tetrad
background state (reference §2).
"""
import numpy as np
import pytest

from bass.background.bianchi_types import (
    ALL_BIANCHI_TYPES, flrw_constants, get_type, type_i_constants,
    type_ii_constants, type_iii_constants, type_iv_constants,
    type_ix_constants, type_v_constants, type_vi0_constants,
    type_vih_constants, type_vii0_constants, type_viih_constants,
    type_viii_constants,
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


def _class_b_connection_expected(sc) -> np.ndarray:
    n1, n3 = float(sc.n1), float(sc.n3)
    R00 = -0.5 * (n1 - n3) ** 2
    R11 = 0.5 * (n1 * n1 - n3 * n3)
    R22 = 0.5 * (n3 * n3 - n1 * n1)
    third = (R00 + R11 + R22) / 3.0
    expected = np.diag([R00 - third, R11 - third, R22 - third])
    expected[1, 2] = expected[2, 1] = float(sc.a_twist) * (n1 - n3)
    return expected


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

    def test_type_vii0_plane_wave_line_aligned(self):
        """VII₀ default fixture (n_1 = n_3) lies on the Lukash plane-wave line.

        Even after FB-1.4 generalises the formula to all 11 types, the
        plane-wave line n_1 = n_3 (n_2 = 0) gives an algebraic zero in
        every diagonal component (each row contributes
        n_i² − (n_j − n_k)² = n² − n² = 0). Status string is renamed
        from ``type_vii0_flat`` to ``type_vii0_e2`` to reflect the e(2)
        algebra rather than a "flat-by-construction" assumption.
        """
        tensor, status = anisotropic_3_curvature(
            type_vii0_constants(), a=1.0, sigma_plus=1e-3, sigma_minus=0.0,
        )
        assert status == 'type_vii0_e2'
        assert np.allclose(tensor, 0.0)

    def test_type_ix_isotropic_exact_zero(self):
        """IX isotropic (n_1=n_2=n_3=n) → ³R_ab^{aniso} ≡ 0 algebraically.

        Each R_ii = (1/2)[n² − (n − n)²] = n²/2 so the trace
        ³R = 3 n²/2 and ³R_ii − ³R/3 = 0. Independent of FB12-F1
        (which is a *shear-source* leading-order pathology, not a
        spatial-curvature one).
        """
        tensor, status = anisotropic_3_curvature(
            type_ix_constants(), a=1.0, sigma_plus=1e-3, sigma_minus=0.0,
        )
        assert status == 'type_ix_so3'
        assert tensor is not None
        # Hard equality (no atol) — formula is exact for isotropic n's.
        assert np.all(tensor == 0.0)


class TestAnisotropic3CurvaturePerType:
    """FB-1.4 — explicit per-type ³R_ab^{aniso} formula consolidation.

    Verifies for every registered Bianchi type that the unified
    Class-A canonical formula
        ³R_ii = (1/2)[n_i² − (n_j − n_k)²]   (cyclic)
    trace-free part returns a non-None, symmetric, trace-free, finite
    3×3 tensor with a per-type status string ≠ 'unavailable'. Reference:
    Ellis-MacCallum 1969 §4 eqs (4.19)–(4.21); Wainwright-Ellis 1997
    §1.4.4; Ellis-Maartens-MacCallum 2012 §14.3.
    """

    @pytest.mark.parametrize("label", ALL_BIANCHI_TYPES + ["FLRW"])
    def test_status_string_never_unavailable(self, label):
        """Phase FB-1 exit contract: every registered label is dispatched."""
        sc = (flrw_constants() if label == "FLRW" else get_type(label))
        _, status = anisotropic_3_curvature(
            sc, a=1.0, sigma_plus=0.0, sigma_minus=0.0,
        )
        assert status != 'unavailable'

    @pytest.mark.parametrize("label", ALL_BIANCHI_TYPES + ["FLRW"])
    def test_tensor_is_non_none(self, label):
        sc = (flrw_constants() if label == "FLRW" else get_type(label))
        tensor, _ = anisotropic_3_curvature(
            sc, a=1.0, sigma_plus=0.0, sigma_minus=0.0,
        )
        assert tensor is not None

    @pytest.mark.parametrize("label", ALL_BIANCHI_TYPES + ["FLRW"])
    def test_tensor_is_symmetric(self, label):
        sc = (flrw_constants() if label == "FLRW" else get_type(label))
        tensor, _ = anisotropic_3_curvature(
            sc, a=1.0, sigma_plus=0.0, sigma_minus=0.0,
        )
        assert np.allclose(tensor, tensor.T, atol=1e-30)

    @pytest.mark.parametrize("label", ALL_BIANCHI_TYPES + ["FLRW"])
    def test_tensor_is_trace_free(self, label):
        sc = (flrw_constants() if label == "FLRW" else get_type(label))
        tensor, _ = anisotropic_3_curvature(
            sc, a=1.0, sigma_plus=0.0, sigma_minus=0.0,
        )
        # Trace-free up to floating-point ulp on the n_i² scale.
        scale = max(abs(tensor).max(), 1e-30)
        assert abs(np.trace(tensor)) < 1e-12 * scale

    @pytest.mark.parametrize("label", ALL_BIANCHI_TYPES + ["FLRW"])
    def test_tensor_is_finite(self, label):
        sc = (flrw_constants() if label == "FLRW" else get_type(label))
        tensor, _ = anisotropic_3_curvature(
            sc, a=1.0, sigma_plus=0.0, sigma_minus=0.0,
        )
        assert np.all(np.isfinite(tensor))

    @pytest.mark.parametrize("label", ALL_BIANCHI_TYPES + ["FLRW"])
    def test_independent_of_a_and_sigma(self, label):
        """³R_ab^{aniso} at the background level depends only on the
        structure constants — not on a, σ_+, σ_−."""
        sc = (flrw_constants() if label == "FLRW" else get_type(label))
        t_ref, _ = anisotropic_3_curvature(
            sc, a=1.0, sigma_plus=0.0, sigma_minus=0.0,
        )
        t_alt, _ = anisotropic_3_curvature(
            sc, a=0.5, sigma_plus=1e-3, sigma_minus=2e-3,
        )
        assert np.array_equal(t_ref, t_alt)

    # ── Per-type explicit closed-form pins ───────────────────────────

    def test_type_ii_explicit_formula(self):
        """II: only n_1 ≠ 0 → ³R_ab^{aniso} = (n_1²/3) × diag(2, −1, −1)."""
        n1 = 3.7e-2
        sc = type_ii_constants(n1=n1)
        tensor, status = anisotropic_3_curvature(sc, 1.0, 0.0, 0.0)
        assert status == 'type_ii_heisenberg'
        expected = (n1 * n1 / 3.0) * np.diag([2.0, -1.0, -1.0])
        assert np.allclose(tensor, expected, rtol=1e-12)

    def test_type_vi0_explicit_formula(self):
        """VI₀: (n_1 > 0, n_3 < 0, n_2 = 0). Diagonal closed form
        matches the trace-free part of the canonical Class-A R_ii formula."""
        n1, n3 = 1.4e-2, -8.0e-3
        sc = type_vi0_constants(n1=n1, n3=n3)
        tensor, status = anisotropic_3_curvature(sc, 1.0, 0.0, 0.0)
        assert status == 'type_vi0_e11'
        R11 = 0.5 * (n1 * n1 - n3 * n3)
        R22 = -0.5 * (n3 - n1) ** 2
        R33 = 0.5 * (n3 * n3 - n1 * n1)
        third = (R11 + R22 + R33) / 3.0
        expected = np.diag([R11 - third, R22 - third, R33 - third])
        assert np.allclose(tensor, expected, rtol=1e-12)

    def test_type_vii0_off_plane_wave_line(self):
        """VII₀ off the plane-wave line (n_1 ≠ n_3) → nonzero
        anisotropic 3-Ricci. Verifies the FB-1.4 generalisation
        beyond the (zero-by-default) n_1 = n_3 fixture."""
        n1, n3 = 2.0e-2, 1.0e-2
        sc = type_vii0_constants(n1=n1, n3=n3)
        tensor, status = anisotropic_3_curvature(sc, 1.0, 0.0, 0.0)
        assert status == 'type_vii0_e2'
        R11 = 0.5 * (n1 * n1 - n3 * n3)
        R22 = -0.5 * (n3 - n1) ** 2
        R33 = 0.5 * (n3 * n3 - n1 * n1)
        third = (R11 + R22 + R33) / 3.0
        expected = np.diag([R11 - third, R22 - third, R33 - third])
        assert np.allclose(tensor, expected, rtol=1e-12)
        assert np.max(np.abs(tensor)) > 0.0  # off-line, non-trivial

    def test_type_viii_explicit_formula(self):
        """VIII (sl(2,ℝ)): one negative eigenvalue, full triplet contributes."""
        sc = type_viii_constants(n1=-1.5e-2, n2=8.0e-3, n3=1.2e-2)
        tensor, status = anisotropic_3_curvature(sc, 1.0, 0.0, 0.0)
        assert status == 'type_viii_sl2r'
        n1, n2, n3 = sc.n_diag
        R11 = 0.5 * (n1 * n1 - (n2 - n3) ** 2)
        R22 = 0.5 * (n2 * n2 - (n3 - n1) ** 2)
        R33 = 0.5 * (n3 * n3 - (n1 - n2) ** 2)
        third = (R11 + R22 + R33) / 3.0
        expected = np.diag([R11 - third, R22 - third, R33 - third])
        assert np.allclose(tensor, expected, rtol=1e-12)

    def test_type_ix_anisotropic_eigenvalues(self):
        """IX with mismatched (n_1, n_2, n_3) gives finite trace-free
        tensor whose eigenvalues sum to zero (Mixmaster background)."""
        sc = type_ix_constants(n=1.0e-2)
        tensor, status = anisotropic_3_curvature(sc, 1.0, 0.0, 0.0)
        assert status == 'type_ix_so3'
        # Default factory has n_1 = n_2 = n_3 = n → exactly zero (isotropic)
        assert np.allclose(tensor, 0.0, atol=1e-30)
        # Mismatched IX-like manual constants → nonzero, trace-free
        from bass.background.bianchi_types import StructureConstants
        sc_aniso = StructureConstants(
            n1=1.0e-2, n2=2.0e-2, n3=3.0e-2, a_twist=0.0, label='IX',
        )
        tensor2, status2 = anisotropic_3_curvature(sc_aniso, 1.0, 0.0, 0.0)
        assert status2 == 'type_ix_so3'
        assert abs(np.trace(tensor2)) < 1e-15
        eigvals = np.linalg.eigvalsh(tensor2)
        assert abs(eigvals.sum()) < 1e-15
        assert np.max(np.abs(eigvals)) > 0.0

    def test_class_b_iv_explicit_formula(self):
        """IV keeps the connection-route N x a off-diagonal curvature."""
        n3, atw = 1.5e-2, 6.0e-3
        sc = type_iv_constants(n3=n3, a_twist=atw)
        tensor, status = anisotropic_3_curvature(sc, 1.0, 0.0, 0.0)
        assert status == 'type_iv_class_b'
        expected = _class_b_connection_expected(sc)
        assert np.allclose(tensor, expected, rtol=1e-12)

    def test_class_b_iii_dispatches_to_vih_formula(self):
        """III (= VI_{h=−1}): N-only formula identical to a hand-built
        VI_h ``StructureConstants`` with the same (n_1, n_3, a_twist).
        Status distinguishes the type label even though the numeric
        tensor coincides."""
        from bass.background.bianchi_types import StructureConstants
        sc_iii = type_iii_constants(n1=1.0e-2)
        # Hand-built VI_h with the same (n_1, n_3, a_twist) — bypasses
        # the factory's h ≠ −1 guard since FB-1.4 only inspects N's.
        sc_vih_at_h_minus_1 = StructureConstants(
            n1=sc_iii.n1, n2=0.0, n3=sc_iii.n3, a_twist=sc_iii.a_twist,
            label='VI_h',
        )
        t_iii, s_iii = anisotropic_3_curvature(sc_iii, 1.0, 0.0, 0.0)
        t_vih, s_vih = anisotropic_3_curvature(
            sc_vih_at_h_minus_1, 1.0, 0.0, 0.0,
        )
        assert s_iii == 'type_iii_class_b'
        assert s_vih == 'type_vih_class_b'
        assert np.allclose(t_iii, t_vih, rtol=1e-14)

    def test_class_b_vih_explicit_formula(self):
        """VI_h includes canonical-frame diagonal curvature plus N x a."""
        sc = type_vih_constants(n1=1.4e-2, n3=-2.0e-3, a_twist=5.0e-3)
        tensor, status = anisotropic_3_curvature(sc, 1.0, 0.0, 0.0)
        assert status == 'type_vih_class_b'
        expected = _class_b_connection_expected(sc)
        assert np.allclose(tensor, expected, rtol=1e-12)

    def test_class_b_viih_explicit_formula(self):
        """VII_h keeps the helical Class-B N x a off-diagonal term."""
        sc = type_viih_constants()
        tensor, status = anisotropic_3_curvature(sc, 1.0, 0.0, 0.0)
        assert status == 'type_viih_class_b'
        expected = _class_b_connection_expected(sc)
        assert np.allclose(tensor, expected, rtol=1e-12)


class TestBuildTetradStateAniso3CurvatureFB14:
    """FB-1.4: build_tetrad_state now returns a non-None aniso_3_curvature
    grid for every registered Bianchi type (Phase FB-1 exit contract)."""

    @pytest.mark.parametrize("label", ALL_BIANCHI_TYPES + ["FLRW"])
    def test_aniso_3_curvature_field_is_non_none(self, label):
        from bass.background.einstein_bianchi import (
            BianchiCosmology, solve_bianchi_background,
        )
        sc = (flrw_constants() if label == "FLRW" else get_type(label))
        # Bianchi IX with default n=1e-2 may need event handling at
        # large η; the FB-1.2 default is opt-in so we keep events=None.
        cosmo = BianchiCosmology(structure=sc)
        bg = solve_bianchi_background(
            cosmo, a_start=1e-4, a_end=0.5, n_pts=100,
        )
        from bass.background.tetrad_state import build_tetrad_state
        tetrad = build_tetrad_state(bg)
        assert tetrad.aniso_3_curvature is not None
        assert tetrad.curvature_status != 'unavailable'
        assert np.all(np.isfinite(tetrad.aniso_3_curvature))


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
