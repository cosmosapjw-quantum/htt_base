"""bass/hierarchy/test_nabla_dispatch_fb22.py (FB-2.2) — Class A II / VI_0
/ VIII ∇̃ axis-aligned dispatch + T1/T2 spatial-Ricci wire-up tests.

Covers the FB-2.2 deliverables:

1. Per-type ``∇̃`` dispatch for Class A II / VI_0 / VIII on their
   abelian-subalgebra axis-aligned subsets (pure plane-wave action).
2. Off-axis / generic modes raise ``NotImplementedError('FB-5.2')``.
3. ``scalar_laplacian_eigenvalue`` branches for II / VI_0 / VIII.
4. T1 / T2 accept an optional ``aniso_ricci_tensor`` kwarg; the
   coupling vanishes at ``³R_aniso = 0`` (preserving bit-identical
   FLRW / I / V / VII_0-symmetric / IX-isotropic regression) and is
   non-zero otherwise.
5. FB14-F1 consistency check — the Class B W-E
   ``(2/3) A²/(1+|h|)`` piece in ``S^{WE}_+`` scales with the twist
   parameter ``h`` as ``1/(1+|h|)`` and is sign-consistent.

Tolerances:

- ``∇̃`` eigenmode pins: rel 1e-12 (complex ``i k`` round-off at ε_mach).
- T1 Ricci coupling: rel 1e-12.
- T2 hook: background returns exactly the LB-2b base value
  (bit-identical when ``³R_aniso`` is supplied but ``∇̃ = 0``).
- FB14-F1 h-scaling: rel 1e-12 between two h-configured shear
  sources.

References
----------
- ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-2.2``.
- Wainwright & Ellis 1997 §1.4.4 (Class A Lie algebras — II /
  VI_0 / VIII abelian subalgebras).
- Ellis, Maartens, MacCallum 2012 §14.3 (spatial-Ricci coupling to
  the PSTF multipole hierarchy).
- ``docs/audits/AUDIT_PHASE_FB1_2026-04-19.md`` — FB14-F1 carry-
  forward declaration.
- ``docs/audits/AUDIT_PHASE_FB2_2026-04-19.md`` — FB-2.2 supplement.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from bass.background.bianchi_types import (
    flrw_constants,
    type_ii_constants,
    type_v_constants,
    type_vi0_constants,
    type_viii_constants,
    type_vih_constants,
    type_viih_constants,
)
from bass.background.tetrad_state import anisotropic_3_curvature
from bass.hierarchy.nabla_dispatch import (
    HarmonicMode,
    SUPPORTED_FB22_TYPES,
    SUPPORTED_TYPES,
    make_nabla_tilde,
    scalar_laplacian_eigenvalue,
)
from bass.hierarchy.terms import T1_expansion, T2_gradient, zero_nabla_operator
from bass.transport.shear_sources import source_VIh, source_VIIh


# ════════════════════════════════════════════════════════════════════
#   §1 — Type II (Heisenberg): axis-aligned on the center ``e_1``
# ════════════════════════════════════════════════════════════════════


class TestTypeIIHeisenbergAxisAligned:
    """Heisenberg Lie algebra: center = ``span{e_1}``.  FB-2.2 restricts
    the dispatch to modes with ``k_vec = (k_1, 0, 0)``.
    """

    def test_typeII_nabla_heisenberg_mode(self) -> None:
        """Axis-aligned scalar mode: ``∇̃_a Y = i k_a Y`` with
        ``k_vec = (k_1, 0, 0)``; rel 1e-12 agreement with the plane-
        wave reference."""
        sc = type_ii_constants(n1=2.5e-2)
        k_vec = np.array([0.17, 0.0, 0.0], dtype=np.float64)
        mode = HarmonicMode(type_label="II", k_vec=k_vec)
        op = make_nabla_tilde(sc, mode)
        scalar = np.array(1.0)
        grad = op(scalar, kind="gradient")
        np.testing.assert_allclose(grad, 1j * k_vec, rtol=1e-12, atol=1e-15)

    def test_typeII_divergence_rank1_returns_dot(self) -> None:
        sc = type_ii_constants(n1=1.0e-2)
        k_vec = np.array([0.31, 0.0, 0.0], dtype=np.float64)
        mode = HarmonicMode(type_label="II", k_vec=k_vec)
        op = make_nabla_tilde(sc, mode)
        V = np.array([1.0, -0.5, 2.0], dtype=np.float64)
        div = op(V, kind="divergence")
        expected = 1j * float(np.dot(k_vec, V))
        np.testing.assert_allclose(div, expected, rtol=1e-12, atol=1e-15)

    def test_typeII_scalar_laplacian_eigenvalue(self) -> None:
        """``λ = −k_1²`` on the Heisenberg center."""
        sc = type_ii_constants(n1=3.3e-2)
        k_vec = np.array([0.25, 0.0, 0.0], dtype=np.float64)
        mode = HarmonicMode(type_label="II", k_vec=k_vec)
        lam = scalar_laplacian_eigenvalue(sc, mode)
        assert lam == pytest.approx(-0.0625, rel=1e-12, abs=1e-14)

    def test_typeII_structure_rejects_nonpositive_n1(self) -> None:
        """FB-2.2 validator re-checks the class A Type II invariant
        ``n_1 > 0`` even if the factory already enforces it."""
        # We cannot build a Type II with n_1 ≤ 0 via the factory,
        # so we synthesise a label-only StructureConstants to exercise
        # the validator's internal check.
        from bass.background.bianchi_types import StructureConstants
        sc = StructureConstants(n1=0.0, n2=0.0, n3=0.0,
                                a_twist=0.0, label="II")
        mode = HarmonicMode(type_label="II",
                            k_vec=np.array([0.1, 0.0, 0.0]))
        with pytest.raises(ValueError, match="Type II requires n_1 > 0"):
            make_nabla_tilde(sc, mode)


# ════════════════════════════════════════════════════════════════════
#   §2 — Type VI_0 (e(1,1)): axis-aligned on ``span{e_1, e_3}``
# ════════════════════════════════════════════════════════════════════


class TestTypeVI0Ep11AxisAligned:
    """``e(1, 1)`` Lie algebra: ``[e_1, e_3] = n_2 e_2 = 0`` in PC
    frame.  FB-2.2 restricts modes to ``k_2 = 0`` where ``∇̃`` acts as
    a plane wave on the abelian ``(e_1, e_3)`` plane.
    """

    def test_typeVI0_nabla_mixed_sign_mode(self) -> None:
        """Plane wave on the abelian 2-plane with both ``k_1`` and
        ``k_3`` non-zero (the mixed-sign eigenvalue character of the
        ``e(1,1)`` background)."""
        sc = type_vi0_constants(n1=1.0e-2, n3=-2.0e-2)
        k_vec = np.array([0.2, 0.0, 0.4], dtype=np.float64)
        mode = HarmonicMode(type_label="VI_0", k_vec=k_vec)
        op = make_nabla_tilde(sc, mode)
        grad = op(np.array(1.0), kind="gradient")
        np.testing.assert_allclose(grad, 1j * k_vec, rtol=1e-12, atol=1e-15)

    def test_typeVI0_scalar_laplacian_eigenvalue(self) -> None:
        """``λ = −(k_1² + k_3²)`` on the 2-D abelian plane."""
        sc = type_vi0_constants(n1=1.0e-2, n3=-2.0e-2)
        k_vec = np.array([0.3, 0.0, 0.4], dtype=np.float64)
        mode = HarmonicMode(type_label="VI_0", k_vec=k_vec)
        lam = scalar_laplacian_eigenvalue(sc, mode)
        assert lam == pytest.approx(-(0.09 + 0.16), rel=1e-12, abs=1e-14)


# ════════════════════════════════════════════════════════════════════
#   §3 — Type VIII (sl(2,R)): axis-aligned on the hyperbolic Cartan
# ════════════════════════════════════════════════════════════════════


class TestTypeVIIISl2RAxisAligned:
    """``sl(2, ℝ)`` is semisimple rank-1: its Cartan subalgebra is
    1-D.  In the ``n_1 < 0, n_2, n_3 > 0`` convention, ``e_1`` is the
    hyperbolic direction; FB-2.2 restricts to ``k_vec = (k_1, 0, 0)``.
    """

    def test_typeVIII_nabla_sl2R_mode(self) -> None:
        sc = type_viii_constants(n1=-1.5e-2, n2=1.0e-2, n3=1.0e-2)
        k_vec = np.array([0.42, 0.0, 0.0], dtype=np.float64)
        mode = HarmonicMode(type_label="VIII", k_vec=k_vec)
        op = make_nabla_tilde(sc, mode)
        grad = op(np.array(1.0), kind="gradient")
        np.testing.assert_allclose(grad, 1j * k_vec, rtol=1e-12, atol=1e-15)

    def test_typeVIII_divergence_rank1(self) -> None:
        sc = type_viii_constants()
        k_vec = np.array([0.1, 0.0, 0.0], dtype=np.float64)
        mode = HarmonicMode(type_label="VIII", k_vec=k_vec)
        op = make_nabla_tilde(sc, mode)
        V = np.array([2.0, -1.0, 0.5], dtype=np.float64)
        div = op(V, kind="divergence")
        expected = 1j * float(np.dot(k_vec, V))
        np.testing.assert_allclose(div, expected, rtol=1e-12, atol=1e-15)

    def test_typeVIII_scalar_laplacian_eigenvalue(self) -> None:
        """``λ = −k_1²`` on the hyperbolic Cartan axis."""
        sc = type_viii_constants()
        k_vec = np.array([0.27, 0.0, 0.0], dtype=np.float64)
        mode = HarmonicMode(type_label="VIII", k_vec=k_vec)
        lam = scalar_laplacian_eigenvalue(sc, mode)
        assert lam == pytest.approx(-0.0729, rel=1e-12, abs=1e-14)


# ════════════════════════════════════════════════════════════════════
#   §4 — Off-axis modes on II / VI_0 / VIII raise FB-5.2
# ════════════════════════════════════════════════════════════════════


class TestFB22ClassAOffAxis:
    """Generic off-axis modes on II / VI_0 / VIII — the non-abelian
    directions of each Lie algebra — raise ``NotImplementedError``
    tagged FB-5.2 (the perturbation-sector harmonic-mode dispatch
    that will resolve the Wigner rotation / Grushin / SL(2, ℝ)
    principal series).
    """

    def test_typeII_off_axis_raises_fb52(self) -> None:
        sc = type_ii_constants()
        mode = HarmonicMode(
            type_label="II", k_vec=np.array([0.1, 0.2, 0.0])
        )
        with pytest.raises(NotImplementedError, match="FB-5.2"):
            make_nabla_tilde(sc, mode)
        with pytest.raises(NotImplementedError, match="FB-5.2"):
            scalar_laplacian_eigenvalue(sc, mode)

    def test_typeVI0_off_plane_raises_fb52(self) -> None:
        sc = type_vi0_constants()
        # k_2 ≠ 0: off the abelian (e_1, e_3) plane.
        mode = HarmonicMode(
            type_label="VI_0", k_vec=np.array([0.1, 0.05, 0.0])
        )
        with pytest.raises(NotImplementedError, match="FB-5.2"):
            make_nabla_tilde(sc, mode)

    def test_typeVIII_off_cartan_raises_fb52(self) -> None:
        sc = type_viii_constants()
        # Non-zero k_2 on the Cartan-restricted dispatch.
        mode = HarmonicMode(
            type_label="VIII", k_vec=np.array([0.1, 0.05, 0.0])
        )
        with pytest.raises(NotImplementedError, match="FB-5.2"):
            make_nabla_tilde(sc, mode)
        # Also check k_3 triggers the same guard.
        mode3 = HarmonicMode(
            type_label="VIII", k_vec=np.array([0.1, 0.0, 0.07])
        )
        with pytest.raises(NotImplementedError, match="FB-5.2"):
            make_nabla_tilde(sc, mode3)


# ════════════════════════════════════════════════════════════════════
#   §5 — T1 / T2 Ricci coupling tests
# ════════════════════════════════════════════════════════════════════


class TestT1RicciCoupling:
    """FB-2.2 adds an optional ``aniso_ricci_tensor`` kwarg to
    :func:`bass.hierarchy.terms.T1_expansion`.  The coupling vanishes
    whenever ``³R_ab^{aniso} = 0`` (FLRW / I / V / VII_0-symmetric /
    IX-isotropic) or ``ell = 0``; it is non-zero for II / VI_0 /
    VIII whose anisotropic 3-Ricci is non-trivial.
    """

    def test_T1_no_ricci_matches_base_expansion(self) -> None:
        """Default call (no ``aniso_ricci_tensor``) matches the LB-2b
        base form ``(4/3) Θ Π_ℓ`` bit-identically across all ranks —
        essential for FLRW regression preservation."""
        Theta = 3.2e-4
        for ell in range(0, 5):
            Pi = np.random.default_rng(123 + ell).standard_normal(
                (3,) * ell if ell > 0 else ()
            )
            # Make sure Π is (informally) PSTF; numerical content
            # doesn't matter for this invariance check.
            out_base = T1_expansion(ell, Pi, Theta)
            out_none = T1_expansion(ell, Pi, Theta, aniso_ricci_tensor=None)
            np.testing.assert_array_equal(out_base, out_none)

    def test_T1_zero_ricci_matches_base(self) -> None:
        """Passing ``aniso_ricci_tensor = zeros(3, 3)`` yields the
        same output as the default — the coupling correctly drops out
        at FLRW."""
        Theta = 1.5e-4
        R_zero = np.zeros((3, 3), dtype=np.float64)
        ell = 2
        Pi2 = np.eye(3) - np.eye(3).trace() / 3.0 * np.eye(3)
        out_base = T1_expansion(ell, Pi2, Theta)
        out_ricci_zero = T1_expansion(
            ell, Pi2, Theta, aniso_ricci_tensor=R_zero
        )
        np.testing.assert_allclose(
            out_base, out_ricci_zero, rtol=1e-14, atol=1e-16
        )

    def test_T1_typeII_ricci_contribution_nonzero(self) -> None:
        """Type II has ``³R_ab^{aniso} ≠ 0`` (diagonal, trace-free);
        the FB-2.2 coupling at ℓ ≥ 1 therefore produces a non-zero
        correction on top of the expansion term.  Exact form: the
        ``T8``-style contraction ``³R_{cb} Π_{...,b}`` with prefactor
        ``ℓ / (2ℓ+3)``, PSTF-projected."""
        sc = type_ii_constants(n1=2.0e-2)
        R, status = anisotropic_3_curvature(sc, 1.0, 0.0, 0.0)
        assert R is not None
        assert status == "type_ii_heisenberg"
        # ³R_ab^{aniso} is non-zero for Type II.
        assert np.linalg.norm(R) > 0.0
        # Build a ℓ = 2 PSTF tensor (trace-free symmetric).
        Pi2 = np.array([
            [2.0, 0.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, -1.0],
        ], dtype=np.float64)
        Theta = 1e-3
        out_base = T1_expansion(2, Pi2, Theta)
        out_ricci = T1_expansion(
            2, Pi2, Theta, aniso_ricci_tensor=R
        )
        # The correction is non-zero (Type II is the simplest case).
        assert np.linalg.norm(out_ricci - out_base) > 1e-8

    def test_T1_ell_zero_ignores_ricci(self) -> None:
        """At ``ℓ = 0`` no contraction index exists — the correction
        must vanish regardless of ``³R_ab^{aniso}`` values."""
        sc = type_vi0_constants(n1=2.0e-2, n3=-3.0e-2)
        R, _ = anisotropic_3_curvature(sc, 1.0, 0.0, 0.0)
        Pi0 = np.array(1.234)  # scalar monopole
        Theta = 1.0e-4
        out_base = T1_expansion(0, Pi0, Theta)
        out_with_R = T1_expansion(0, Pi0, Theta, aniso_ricci_tensor=R)
        np.testing.assert_allclose(out_base, out_with_R, rtol=1e-14)


class TestT2RicciHook:
    """The FB-2.2 ``aniso_ricci_tensor`` hook on
    :func:`bass.hierarchy.terms.T2_gradient` is a *structural hook*
    only: at background (``zero_nabla_operator``), ``∇̃ ³R_ab = 0``
    (the Ricci is spatially homogeneous in the left-invariant tetrad
    frame), so the contribution is identically zero.  FB-5.1 will
    wire in the complex-dtype harmonic-mode operator where the hook
    becomes load-bearing.
    """

    def test_T2_hook_zero_at_background_typeII(self) -> None:
        """Background ``zero_nabla_operator`` → T2 result is identical
        whether or not ``aniso_ricci_tensor`` is supplied."""
        sc = type_ii_constants()
        R, _ = anisotropic_3_curvature(sc, 1.0, 0.0, 0.0)
        Pi_0 = np.array(0.5)  # scalar
        out_base = T2_gradient(1, Pi_0, zero_nabla_operator)
        out_hook = T2_gradient(
            1, Pi_0, zero_nabla_operator, aniso_ricci_tensor=R
        )
        np.testing.assert_allclose(out_base, out_hook, rtol=1e-14, atol=0.0)

    def test_T2_hook_zero_at_background_ell2(self) -> None:
        sc = type_vi0_constants()
        R, _ = anisotropic_3_curvature(sc, 1.0, 0.0, 0.0)
        Pi_1 = np.array([0.1, -0.2, 0.3], dtype=np.float64)
        out_base = T2_gradient(2, Pi_1, zero_nabla_operator)
        out_hook = T2_gradient(
            2, Pi_1, zero_nabla_operator, aniso_ricci_tensor=R
        )
        np.testing.assert_allclose(out_base, out_hook, rtol=1e-14, atol=0.0)

    def test_T2_hook_bad_shape_rejected(self) -> None:
        """Wrong ``aniso_ricci_tensor`` shape surfaces a ``ValueError``
        rather than silently dispatching."""
        Pi_0 = np.array(0.5)
        bad_R = np.zeros((3, 3, 3), dtype=np.float64)
        with pytest.raises(ValueError, match=r"shape \(3, 3\)"):
            T2_gradient(
                1, Pi_0, zero_nabla_operator, aniso_ricci_tensor=bad_R
            )


# ════════════════════════════════════════════════════════════════════
#   §6 — FB14-F1 calibration: Class B S^{WE}_+ twist-coupled piece
# ════════════════════════════════════════════════════════════════════


class TestFB14F1ClassBTwistCorrection:
    """FB14-F1 (Phase FB-1.4 carry-forward, resolved in FB-2.2):
    verify that the Class B shear-source W-E ``(2/3) A²/(1+|h|)``
    piece in ``S^{WE}_+`` scales correctly with the twist parameter
    ``h``, and that the `+` sign (positive contribution to ``S_+``)
    distinguishes it from the pure N² piece (negative).

    The test varies ``h`` (via ``a_twist`` and ``n_3``) while holding
    ``n_1`` and ``A`` scales comparable, and pins the resulting
    ``h_factor = 1/(1+|h|)`` scaling between two configurations to
    rel 1e-12.

    Reference: Wainwright-Ellis 1997 §18 Table 11.1 Class B rows VI_h
    / VII_h; ``docs/audits/AUDIT_PHASE_FB1_2026-04-19.md §FB14-F1``
    declaration + ``docs/audits/AUDIT_PHASE_FB2_2026-04-19.md``
    FB-2.2 supplement.
    """

    def test_VIh_h_factor_scaling_pinned(self) -> None:
        """Two VI_h backgrounds that differ only in ``a_twist`` but
        share ``(n_1, n_3)``: the ``A²/(1+|h|)`` piece of ``S^{WE}_+``
        must scale exactly as ``a_twist²/(1+|h|)``."""
        calH = 1.0e-3
        n1, n3 = 1.0e-2, -2.0e-3
        a1 = 5.0e-3
        a2 = 8.0e-3
        sc1 = type_vih_constants(n1=n1, n3=n3, a_twist=a1)
        sc2 = type_vih_constants(n1=n1, n3=n3, a_twist=a2)
        dSp1, _ = source_VIh(sc1, 0.0, 0.0, calH, 1e-3)
        dSp2, _ = source_VIh(sc2, 0.0, 0.0, calH, 1e-3)
        # Subtract the N² piece (shared between sc1 and sc2 because
        # n_1, n_3 are the same).
        n_piece = -(2.0 / 3.0) * (n1 - n3) ** 2 * calH ** 2
        twist_1 = dSp1 - n_piece
        twist_2 = dSp2 - n_piece
        h1 = sc1.h_parameter
        h2 = sc2.h_parameter
        expected_1 = (2.0 / 3.0) * a1 ** 2 * calH ** 2 / (1.0 + abs(h1))
        expected_2 = (2.0 / 3.0) * a2 ** 2 * calH ** 2 / (1.0 + abs(h2))
        assert twist_1 == pytest.approx(expected_1, rel=1e-12, abs=1e-18)
        assert twist_2 == pytest.approx(expected_2, rel=1e-12, abs=1e-18)
        # And the sign is POSITIVE (pushes S_+ up).
        assert twist_1 > 0.0
        assert twist_2 > 0.0

    def test_VIIh_h_factor_scaling_pinned(self) -> None:
        """Analogous pin for VII_h: the ``A²/(1+h)`` piece (h > 0)."""
        calH = 1.0e-3
        n1, n3 = 1.8e-2, 1.0e-2
        sc1 = type_viih_constants(n1=n1, n3=n3, a_twist=5.5e-3)
        sc2 = type_viih_constants(n1=n1, n3=n3, a_twist=8.0e-3)
        # Zero out Σ inputs to isolate the W-E piece; the spiral term
        # is Σ-linear and vanishes at Σ_± = 0.
        dSp1, _ = source_VIIh(sc1, 0.0, 0.0, calH, 1e-3)
        dSp2, _ = source_VIIh(sc2, 0.0, 0.0, calH, 1e-3)
        n_piece = -(2.0 / 3.0) * (n1 - n3) ** 2 * calH ** 2
        twist_1 = dSp1 - n_piece
        twist_2 = dSp2 - n_piece
        h1 = sc1.h_parameter
        h2 = sc2.h_parameter
        expected_1 = (2.0 / 3.0) * sc1.a_twist ** 2 * calH ** 2 / (1.0 + h1)
        expected_2 = (2.0 / 3.0) * sc2.a_twist ** 2 * calH ** 2 / (1.0 + h2)
        assert twist_1 == pytest.approx(expected_1, rel=1e-12, abs=1e-18)
        assert twist_2 == pytest.approx(expected_2, rel=1e-12, abs=1e-18)
        assert twist_1 > 0.0
        assert twist_2 > 0.0

    def test_VIh_twist_piece_vanishes_at_zero_a(self) -> None:
        """In the limit ``a_twist → 0`` the FB14-F1 twist piece
        vanishes quadratically.  We pin the full closed-form scaling
        ``twist_l / twist_s = (a_l / a_s)² × (1+|h_s|)/(1+|h_l|)``
        which reduces to ``(a_l / a_s)²`` only as ``|h| → 0``.  Tests
        both the quadratic ``a²`` scaling and the ``1/(1+|h|)``
        denominator in one shot.
        """
        calH = 1.0e-3
        n1, n3 = 1.0e-2, -1.0e-2
        a_small = 1.0e-5
        a_larger = 2.0e-5
        sc_s = type_vih_constants(n1=n1, n3=n3, a_twist=a_small)
        sc_l = type_vih_constants(n1=n1, n3=n3, a_twist=a_larger)
        dSp_s, _ = source_VIh(sc_s, 0.0, 0.0, calH, 1e-3)
        dSp_l, _ = source_VIh(sc_l, 0.0, 0.0, calH, 1e-3)
        n_piece = -(2.0 / 3.0) * (n1 - n3) ** 2 * calH ** 2
        twist_s = dSp_s - n_piece
        twist_l = dSp_l - n_piece
        ratio = twist_l / twist_s
        # Closed-form expected ratio includes the 1/(1+|h|) factor.
        expected = (
            (a_larger / a_small) ** 2
            * (1.0 + abs(sc_s.h_parameter))
            / (1.0 + abs(sc_l.h_parameter))
        )
        # Looser tolerance than the h-factor pin tests because both
        # dSp_s and dSp_l are dominated by the N² piece (~1e-10) and
        # the twist piece is a ~1e-16 correction — catastrophic
        # cancellation limits the precision to ~1e-6.
        assert ratio == pytest.approx(expected, rel=1e-6)
        # And the scaling tends to (a_l/a_s)² = 4 as |h| → 0 (holds
        # to the 1e-5 precision set by our choice of a_twist values).
        assert abs(ratio - 4.0) < 5e-5


# ════════════════════════════════════════════════════════════════════
#   §7 — FB-2.2 dispatch coverage invariants (SUPPORTED_TYPES union)
# ════════════════════════════════════════════════════════════════════


def test_fb22_supported_types_contains_class_a_additions() -> None:
    """``SUPPORTED_FB22_TYPES`` exactly enumerates II / VI_0 / VIII."""
    assert set(SUPPORTED_FB22_TYPES) == {"II", "VI_0", "VIII"}


def test_fb22_supported_types_is_union_aggregate() -> None:
    """The runtime dispatch uses ``SUPPORTED_TYPES = FB21 ∪ FB22``.
    This test locks the aggregate label list so no label is silently
    dropped in later refactors."""
    expected = {"FLRW", "I", "V", "VII_0", "IX", "II", "VI_0", "VIII"}
    assert set(SUPPORTED_TYPES) == expected
