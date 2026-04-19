"""bass/hierarchy/test_nabla_dispatch.py (FB-2.1) — per-type ∇̃ tests.

Validates the harmonic-mode dispatch of ``make_nabla_tilde`` and
``scalar_laplacian_eigenvalue`` for FLRW / I / V / VII_0 / IX, and
ensures the deferred types (II / VI_0 / VIII → FB-2.2;
III / IV / VI_h / VII_h → FB-2.3) raise an explicit
``NotImplementedError``.

Tolerances: exact eigenmode pins at rel 1e-12 (complex ``∇̃ = i k``
is evaluated in float64 × complex128, so round-off is at ε_mach).

References
----------
- ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-2.1``
- Harrison 1967 (hyperbolic harmonics); Lifshitz-Khalatnikov 1963 (IX).
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.background.bianchi_types import (
    flrw_constants,
    type_i_constants,
    type_ii_constants,
    type_iii_constants,
    type_iv_constants,
    type_ix_constants,
    type_v_constants,
    type_vi0_constants,
    type_vih_constants,
    type_vii0_constants,
    type_viih_constants,
    type_viii_constants,
)
from bass.hierarchy.nabla_dispatch import (
    DEFERRED_FB22_TYPES,
    DEFERRED_FB23_TYPES,
    HarmonicMode,
    SUPPORTED_FB21_TYPES,
    SUPPORTED_FB22_TYPES,
    SUPPORTED_FB23_TYPES,
    SUPPORTED_TYPES,
    make_nabla_tilde,
    scalar_laplacian_eigenvalue,
)


# ════════════════════════════════════════════════════════════════════
#   FLRW — plane-wave eigenmode
# ════════════════════════════════════════════════════════════════════

class TestFlrwPlaneWave:
    """FLRW is the reference: ∇̃_a Y_k = i k_a Y_k, ∇̃² Y_k = -|k|² Y_k.

    Reference: Ma-Bertschinger 1995 §4; Ellis-Maartens-MacCallum 2012 §16.1.
    """

    def test_flrw_nabla_plane_wave_eigenmode(self) -> None:
        """Gradient of a scalar amplitude 1 returns exactly i k (rel 1e-12)."""
        sc = flrw_constants()
        k_vec = np.array([0.1, 0.2, 0.3], dtype=np.float64)
        mode = HarmonicMode(type_label="FLRW", k_vec=k_vec)
        op = make_nabla_tilde(sc, mode)
        scalar = np.array(1.0)
        grad = op(scalar, kind="gradient")
        assert grad.shape == (3,)
        assert grad.dtype == np.complex128
        np.testing.assert_allclose(grad, 1j * k_vec, rtol=1e-12, atol=1e-15)

    def test_flrw_divergence_rank1_returns_dot_product(self) -> None:
        sc = flrw_constants()
        k_vec = np.array([0.1, 0.2, 0.3], dtype=np.float64)
        mode = HarmonicMode(type_label="FLRW", k_vec=k_vec)
        op = make_nabla_tilde(sc, mode)
        # Divergence of a rank-1 tensor V_a: ∇̃^a V_a = i k · V.
        V = np.array([1.0, -2.0, 0.5], dtype=np.float64)
        div = op(V, kind="divergence")
        assert div.shape == ()
        expected = 1j * float(np.dot(k_vec, V))
        np.testing.assert_allclose(div, expected, rtol=1e-12, atol=1e-15)

    def test_flrw_scalar_laplacian_eigenvalue(self) -> None:
        """∇̃² eigenvalue = -|k|² on FLRW (Ma-Bertschinger convention)."""
        sc = flrw_constants()
        k_vec = np.array([0.4, -0.3, 0.2], dtype=np.float64)
        mode = HarmonicMode(type_label="FLRW", k_vec=k_vec)
        lam = scalar_laplacian_eigenvalue(sc, mode)
        expected = -float(np.dot(k_vec, k_vec))
        assert lam == pytest.approx(expected, rel=1e-12, abs=1e-14)

    def test_flrw_gradient_rank2_prepends_index(self) -> None:
        """∇̃_a T_bc = i k_a T_bc — new axis at position 0."""
        sc = flrw_constants()
        k_vec = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        mode = HarmonicMode(type_label="FLRW", k_vec=k_vec)
        op = make_nabla_tilde(sc, mode)
        T = np.arange(9.0).reshape(3, 3)
        out = op(T, kind="gradient")
        assert out.shape == (3, 3, 3)
        np.testing.assert_allclose(
            out[0], 1j * T, rtol=1e-12, atol=1e-15
        )
        # k_vec = e_1 → only out[0] is populated.
        np.testing.assert_allclose(
            out[1], np.zeros_like(T, dtype=np.complex128), atol=1e-15
        )
        np.testing.assert_allclose(
            out[2], np.zeros_like(T, dtype=np.complex128), atol=1e-15
        )


# ════════════════════════════════════════════════════════════════════
#   Type I — flat anisotropic, identical to FLRW
# ════════════════════════════════════════════════════════════════════

class TestTypeIMatchesFlrw:
    """Bianchi I (n = a_twist = 0) has the same plane-wave spectrum as FLRW."""

    def test_typeI_nabla_matches_flrw(self) -> None:
        sc_i = type_i_constants()
        sc_flrw = flrw_constants()
        k_vec = np.array([0.2, -0.1, 0.05], dtype=np.float64)
        mode_i = HarmonicMode(type_label="I", k_vec=k_vec)
        mode_flrw = HarmonicMode(type_label="FLRW", k_vec=k_vec)
        op_i = make_nabla_tilde(sc_i, mode_i)
        op_flrw = make_nabla_tilde(sc_flrw, mode_flrw)
        scalar = np.array(2.0)
        np.testing.assert_allclose(
            op_i(scalar, kind="gradient"),
            op_flrw(scalar, kind="gradient"),
            rtol=1e-12,
            atol=1e-15,
        )
        V = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        np.testing.assert_allclose(
            op_i(V, kind="divergence"),
            op_flrw(V, kind="divergence"),
            rtol=1e-12,
            atol=1e-15,
        )

    def test_typeI_scalar_laplacian_matches_flrw(self) -> None:
        sc_i = type_i_constants()
        k_vec = np.array([0.3, 0.4, 0.5], dtype=np.float64)
        mode = HarmonicMode(type_label="I", k_vec=k_vec)
        lam = scalar_laplacian_eigenvalue(sc_i, mode)
        assert lam == pytest.approx(-float(np.dot(k_vec, k_vec)),
                                    rel=1e-12, abs=1e-14)


# ════════════════════════════════════════════════════════════════════
#   Type V — Harrison hyperbolic harmonic
# ════════════════════════════════════════════════════════════════════

class TestTypeVHyperbolic:
    """Harrison 1967 open-FLRW hyperbolic: ∇̃² Y = -(|k|² + a²) Y."""

    def test_typeV_nabla_hyperbolic_eigenmode(self) -> None:
        sc = type_v_constants(a_twist=0.02)
        k_vec = np.array([0.1, 0.0, 0.0], dtype=np.float64)
        mode = HarmonicMode(type_label="V", k_vec=k_vec)
        op = make_nabla_tilde(sc, mode)
        scalar = np.array(1.0)
        grad = op(scalar, kind="gradient")
        np.testing.assert_allclose(grad, 1j * k_vec, rtol=1e-12, atol=1e-15)

    def test_typeV_scalar_laplacian_includes_curvature_shift(self) -> None:
        """λ = -(k² + a²) — the hyperbolic-harmonic offset from the
        negatively-curved 3-space (Harrison 1967 eq 4.5)."""
        a_twist = 0.05
        sc = type_v_constants(a_twist=a_twist)
        k_vec = np.array([0.1, 0.2, 0.0], dtype=np.float64)
        mode = HarmonicMode(type_label="V", k_vec=k_vec)
        lam = scalar_laplacian_eigenvalue(sc, mode)
        expected = -(float(np.dot(k_vec, k_vec)) + a_twist ** 2)
        assert lam == pytest.approx(expected, rel=1e-12, abs=1e-14)

    def test_typeV_flrw_limit_as_a_vanishes(self) -> None:
        """In the a_twist → 0 limit (formally Type I / open FLRW flat
        limit), scalar_laplacian_eigenvalue → -|k|². We cannot build a
        Type V with a_twist = 0 (factory raises), so we instead pin
        the continuity: small a_twist reproduces FLRW eigenvalue to
        O(a²).
        """
        sc = type_v_constants(a_twist=1e-6)
        k_vec = np.array([0.4, -0.2, 0.1], dtype=np.float64)
        mode = HarmonicMode(type_label="V", k_vec=k_vec)
        lam = scalar_laplacian_eigenvalue(sc, mode)
        expected_flrw = -float(np.dot(k_vec, k_vec))
        assert abs(lam - expected_flrw) < 1e-10


# ════════════════════════════════════════════════════════════════════
#   Type VII_0 — plane wave with helical phase (symmetric-line reduction)
# ════════════════════════════════════════════════════════════════════

class TestTypeVII0Helical:
    """VII_0 on the symmetric line (n_1 = n_3) with mode aligned to e_2.

    Reference: Pontzen & Challinor 2007 eq (2.12) for the generic
    helical Q-mode; FB-2.1 restricts to the axis-aligned reduction
    where the helical phase is trivial.
    """

    def test_typeVII0_nabla_plane_wave_helical_phase_axis_aligned(self) -> None:
        """n_1 = n_3, k_vec = (0, k_2, 0) → FLRW-like action."""
        sc = type_vii0_constants(n1=1.0e-2, n3=1.0e-2)
        k_vec = np.array([0.0, 0.3, 0.0], dtype=np.float64)
        mode = HarmonicMode(type_label="VII_0", k_vec=k_vec)
        op = make_nabla_tilde(sc, mode)
        scalar = np.array(1.0)
        grad = op(scalar, kind="gradient")
        np.testing.assert_allclose(grad, 1j * k_vec, rtol=1e-12, atol=1e-15)

    def test_typeVII0_scalar_laplacian_matches_flrw_on_axis(self) -> None:
        sc = type_vii0_constants(n1=1.0e-2, n3=1.0e-2)
        k_vec = np.array([0.0, 0.42, 0.0], dtype=np.float64)
        mode = HarmonicMode(type_label="VII_0", k_vec=k_vec)
        lam = scalar_laplacian_eigenvalue(sc, mode)
        assert lam == pytest.approx(
            -float(np.dot(k_vec, k_vec)), rel=1e-12, abs=1e-14
        )

    def test_typeVII0_off_axis_mode_raises_fb52_notimplemented(self) -> None:
        """Non-axis-aligned mode on VII_0 → NotImplementedError('FB-5.2')."""
        sc = type_vii0_constants(n1=1.0e-2, n3=1.0e-2)
        # Non-axis-aligned: component along e_1 is non-zero.
        k_vec_offaxis = np.array([0.1, 0.2, 0.0], dtype=np.float64)
        mode = HarmonicMode(type_label="VII_0", k_vec=k_vec_offaxis)
        with pytest.raises(NotImplementedError, match="FB-5.2"):
            make_nabla_tilde(sc, mode)

    def test_typeVII0_asymmetric_line_raises_fb52_notimplemented(self) -> None:
        """n_1 ≠ n_3 (off the symmetric line) → NotImplementedError('FB-5.2')."""
        sc = type_vii0_constants(n1=1.0e-2, n3=2.0e-2)
        k_vec = np.array([0.0, 0.3, 0.0], dtype=np.float64)
        mode = HarmonicMode(type_label="VII_0", k_vec=k_vec)
        with pytest.raises(NotImplementedError, match="FB-5.2"):
            make_nabla_tilde(sc, mode)


# ════════════════════════════════════════════════════════════════════
#   Type IX — discrete S³ spectrum (Lifshitz-Khalatnikov 1963)
# ════════════════════════════════════════════════════════════════════

class TestTypeIXDiscreteS3:
    """Bianchi IX: closed S³ spatial sections, discrete scalar spectrum
    ``∇̃² Y_{ℓ,m} = -ℓ(ℓ+2) Y_{ℓ,m}`` with ℓ ≥ 1.
    """

    @pytest.mark.parametrize("ell", [1, 2, 3, 5, 8])
    def test_typeIX_nabla_discrete_S3_spectrum(self, ell: int) -> None:
        """λ = -ℓ(ℓ+2) independent of k_vec magnitude on IX."""
        sc = type_ix_constants(n=1.0e-2)
        # k_vec magnitude matches spin-1 eigenvalue √(ℓ(ℓ+2)).
        k_mag = np.sqrt(ell * (ell + 2))
        k_vec = np.array([k_mag, 0.0, 0.0], dtype=np.float64)
        mode = HarmonicMode(type_label="IX", k_vec=k_vec, ell=ell)
        lam = scalar_laplacian_eigenvalue(sc, mode)
        assert lam == pytest.approx(-float(ell * (ell + 2)),
                                    rel=1e-12, abs=1e-14)

    def test_typeIX_laplacian_independent_of_k_magnitude(self) -> None:
        """The S³ eigenvalue is dictated by ℓ alone — |k_vec| is just
        a direction scale (harmonic amplitude normalisation).
        """
        sc = type_ix_constants(n=1.0e-2)
        ell = 3
        expected = -float(ell * (ell + 2))
        for k_mag in (0.5, 1.0, 2.0, 10.0):
            mode = HarmonicMode(
                type_label="IX",
                k_vec=np.array([k_mag, 0.0, 0.0], dtype=np.float64),
                ell=ell,
            )
            lam = scalar_laplacian_eigenvalue(sc, mode)
            assert lam == pytest.approx(expected, rel=1e-12, abs=1e-14)

    def test_typeIX_gradient_acts_via_plane_wave_representation(self) -> None:
        """Gradient of the rank-0 amplitude returns i k_vec (plane-wave
        representation of the S³ spin-1 lift); higher-rank tensor
        harmonics on S³ are deferred to FB-5.1.
        """
        sc = type_ix_constants(n=1.0e-2)
        ell = 2
        k_mag = np.sqrt(ell * (ell + 2))
        k_vec = np.array([0.0, k_mag, 0.0], dtype=np.float64)
        mode = HarmonicMode(type_label="IX", k_vec=k_vec, ell=ell)
        op = make_nabla_tilde(sc, mode)
        scalar = np.array(1.0)
        grad = op(scalar, kind="gradient")
        np.testing.assert_allclose(grad, 1j * k_vec, rtol=1e-12, atol=1e-15)

    def test_typeIX_rejects_ell_zero_constant_mode(self) -> None:
        """ℓ = 0 is the constant mode on S³ — gradient identically zero.
        HarmonicMode rejects this as malformed (use zero_nabla_operator
        for the ℓ = 0 branch, which is the ``k = 0`` background).
        """
        with pytest.raises(ValueError, match=r"ell must be >= 1"):
            HarmonicMode(
                type_label="IX",
                k_vec=np.array([0.0, 0.0, 0.0]),
                ell=0,
            )

    def test_typeIX_missing_ell_raises(self) -> None:
        with pytest.raises(ValueError, match="requires an explicit ell"):
            HarmonicMode(
                type_label="IX",
                k_vec=np.array([1.0, 0.0, 0.0]),
                ell=None,
            )


# ════════════════════════════════════════════════════════════════════
#   Deferred types — explicit NotImplementedError branches
# ════════════════════════════════════════════════════════════════════

class TestDeferredTypesFB22:
    """FB-2.2 landed: Class A II / VI_0 / VIII are now supported on
    their abelian-subalgebra axis-aligned subsets. The pre-FB-2.2
    ``NotImplementedError('FB-2.2')`` path is extinct; its replacement
    is the FB-5.2 off-axis guard, exercised by the
    :class:`TestFB22ClassAOffAxis` suite in
    ``test_nabla_dispatch_fb22.py``.  These legacy tests now assert
    the **axis-aligned** happy path to pin the dispatch migration.
    """

    def test_typeII_axis_aligned_supported(self) -> None:
        sc = type_ii_constants()
        mode = HarmonicMode(type_label="II",
                            k_vec=np.array([0.1, 0.0, 0.0]))
        op = make_nabla_tilde(sc, mode)
        grad = op(np.array(1.0), kind="gradient")
        np.testing.assert_allclose(
            grad, 1j * mode.k_vec, rtol=1e-12, atol=1e-15
        )
        lam = scalar_laplacian_eigenvalue(sc, mode)
        assert lam == pytest.approx(-0.01, rel=1e-12, abs=1e-14)

    def test_typeVI0_axis_aligned_supported(self) -> None:
        sc = type_vi0_constants()
        mode = HarmonicMode(type_label="VI_0",
                            k_vec=np.array([0.1, 0.0, 0.0]))
        op = make_nabla_tilde(sc, mode)
        grad = op(np.array(1.0), kind="gradient")
        np.testing.assert_allclose(
            grad, 1j * mode.k_vec, rtol=1e-12, atol=1e-15
        )

    def test_typeVIII_axis_aligned_supported(self) -> None:
        sc = type_viii_constants()
        mode = HarmonicMode(type_label="VIII",
                            k_vec=np.array([0.1, 0.0, 0.0]))
        op = make_nabla_tilde(sc, mode)
        grad = op(np.array(1.0), kind="gradient")
        np.testing.assert_allclose(
            grad, 1j * mode.k_vec, rtol=1e-12, atol=1e-15
        )


class TestDeferredTypesPostFB23:
    """FB-2.3 landed: Class B III / IV / VI_h / VII_h are now supported
    on their abelian ``(e_1, e_3)`` 2-plane axis-aligned subsets. The
    pre-FB-2.3 ``NotImplementedError('FB-2.3')`` path is extinct; its
    replacement is the FB-5.2 off-axis guard, exercised by the
    ``TestFB23ClassBOffAxis`` suite in ``test_nabla_dispatch_fb23.py``.
    These legacy tests now assert the **axis-aligned** happy path to
    pin the dispatch migration.
    """

    def test_typeIII_axis_aligned_supported(self) -> None:
        sc = type_iii_constants()
        mode = HarmonicMode(type_label="III",
                            k_vec=np.array([0.1, 0.0, 0.0]))
        op = make_nabla_tilde(sc, mode)
        grad = op(np.array(1.0), kind="gradient")
        np.testing.assert_allclose(
            grad, 1j * mode.k_vec, rtol=1e-12, atol=1e-15
        )

    def test_typeIV_axis_aligned_supported(self) -> None:
        sc = type_iv_constants()
        mode = HarmonicMode(type_label="IV",
                            k_vec=np.array([0.1, 0.0, 0.0]))
        op = make_nabla_tilde(sc, mode)
        grad = op(np.array(1.0), kind="gradient")
        np.testing.assert_allclose(
            grad, 1j * mode.k_vec, rtol=1e-12, atol=1e-15
        )

    def test_typeVIh_axis_aligned_supported(self) -> None:
        sc = type_vih_constants()
        mode = HarmonicMode(type_label="VI_h",
                            k_vec=np.array([0.1, 0.0, 0.0]))
        op = make_nabla_tilde(sc, mode)
        grad = op(np.array(1.0), kind="gradient")
        np.testing.assert_allclose(
            grad, 1j * mode.k_vec, rtol=1e-12, atol=1e-15
        )

    def test_typeVIIh_axis_aligned_supported(self) -> None:
        sc = type_viih_constants()
        mode = HarmonicMode(type_label="VII_h",
                            k_vec=np.array([0.1, 0.0, 0.0]))
        op = make_nabla_tilde(sc, mode)
        grad = op(np.array(1.0), kind="gradient")
        np.testing.assert_allclose(
            grad, 1j * mode.k_vec, rtol=1e-12, atol=1e-15
        )


# ════════════════════════════════════════════════════════════════════
#   Contract — mode / structure label consistency
# ════════════════════════════════════════════════════════════════════

class TestModeStructureLabelContract:
    """Require mode.type_label == structure.label to prevent silent
    cross-wiring (e.g., passing an IX mode to an FLRW structure)."""

    def test_label_mismatch_raises(self) -> None:
        sc = flrw_constants()
        mode = HarmonicMode(type_label="I",
                            k_vec=np.array([0.1, 0.0, 0.0]))
        with pytest.raises(ValueError, match="does not match"):
            make_nabla_tilde(sc, mode)
        with pytest.raises(ValueError, match="does not match"):
            scalar_laplacian_eigenvalue(sc, mode)

    def test_nonfinite_k_vec_rejected(self) -> None:
        sc = flrw_constants()
        mode = HarmonicMode(
            type_label="FLRW",
            k_vec=np.array([np.nan, 0.0, 0.0]),
        )
        with pytest.raises(ValueError, match="finite"):
            make_nabla_tilde(sc, mode)

    def test_bad_k_vec_shape_rejected_at_mode_construction(self) -> None:
        with pytest.raises(ValueError, match=r"shape \(3,\)"):
            HarmonicMode(
                type_label="FLRW",
                k_vec=np.array([0.1, 0.0, 0.0, 0.0]),
            )


# ════════════════════════════════════════════════════════════════════
#   Coverage invariant — 11-type dispatch completeness
# ════════════════════════════════════════════════════════════════════

def test_fb21_dispatch_covers_all_11_bianchi_types_plus_flrw() -> None:
    """Every Bianchi type (+ FLRW) appears in exactly one of the
    dispatch sets (FB-2.1 / FB-2.2 / FB-2.3 supported). Prevents
    silent dispatch holes in future refactors.

    FB-2.2 moved II / VI_0 / VIII from ``DEFERRED_FB22_TYPES`` to
    ``SUPPORTED_FB22_TYPES``. FB-2.3 moved III / IV / VI_h / VII_h
    from ``DEFERRED_FB23_TYPES`` to ``SUPPORTED_FB23_TYPES``. Both
    DEFERRED tuples are now empty and retained only for backward-
    compat import paths.
    """
    all_labels = (
        set(SUPPORTED_FB21_TYPES)
        | set(SUPPORTED_FB22_TYPES)
        | set(SUPPORTED_FB23_TYPES)
        | set(DEFERRED_FB22_TYPES)
        | set(DEFERRED_FB23_TYPES)
    )
    expected = {
        "FLRW", "I", "II", "III", "IV", "V",
        "VI_0", "VI_h", "VII_0", "VII_h", "VIII", "IX",
    }
    assert all_labels == expected
    # Partition is disjoint — every label in exactly one SUPPORTED
    # bucket.
    assert set(SUPPORTED_FB21_TYPES).isdisjoint(set(SUPPORTED_FB22_TYPES))
    assert set(SUPPORTED_FB21_TYPES).isdisjoint(set(SUPPORTED_FB23_TYPES))
    assert set(SUPPORTED_FB22_TYPES).isdisjoint(set(SUPPORTED_FB23_TYPES))
    # The SUPPORTED_TYPES union is the FB-2.1 ∪ FB-2.2 ∪ FB-2.3
    # aggregate used by the hierarchy dispatch at runtime.
    assert set(SUPPORTED_TYPES) == (
        set(SUPPORTED_FB21_TYPES)
        | set(SUPPORTED_FB22_TYPES)
        | set(SUPPORTED_FB23_TYPES)
    )
    assert len(SUPPORTED_TYPES) == 12
    # Both DEFERRED tuples are drained after FB-2.3 landed.
    assert len(DEFERRED_FB22_TYPES) == 0
    assert len(DEFERRED_FB23_TYPES) == 0


# ════════════════════════════════════════════════════════════════════
#   Rank-0 divergence is not defined
# ════════════════════════════════════════════════════════════════════

def test_divergence_of_scalar_raises() -> None:
    sc = flrw_constants()
    mode = HarmonicMode(
        type_label="FLRW", k_vec=np.array([0.1, 0.0, 0.0])
    )
    op = make_nabla_tilde(sc, mode)
    with pytest.raises(ValueError, match="rank-0"):
        op(np.array(1.0), kind="divergence")


def test_invalid_kind_raises() -> None:
    sc = flrw_constants()
    mode = HarmonicMode(
        type_label="FLRW", k_vec=np.array([0.1, 0.0, 0.0])
    )
    op = make_nabla_tilde(sc, mode)
    with pytest.raises(ValueError, match="'gradient' or 'divergence'"):
        op(np.array(1.0), kind="curl")
