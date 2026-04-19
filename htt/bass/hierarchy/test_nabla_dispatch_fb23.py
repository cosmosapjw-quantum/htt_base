"""bass/hierarchy/test_nabla_dispatch_fb23.py (FB-2.3) — Class B
III / IV / VI_h / VII_h ∇̃ twist-coupled axis-aligned dispatch.

Covers the FB-2.3 deliverables:

1. Per-type ``∇̃`` dispatch for Class B (III / IV / VI_h / VII_h) on
   each type's abelian ``(e_1, e_3)`` 2-plane axis-aligned subset —
   modes with ``k_2 = 0`` act as pure plane waves.
2. Off-plane modes (``k_2 ≠ 0``) raise
   ``NotImplementedError('FB-5.2')``.
3. ``scalar_laplacian_eigenvalue`` branches for each Class B type:
   ``λ = −(|k|² + a_twist² / (1 + |h|))`` — Harrison-V generalisation
   matching the FB14-F1 ``(2/3) A²/(1+|h|)`` denominator in
   ``S^{WE}_+`` and the PC 2007 spiral-damping factor for VII_h.
4. T1 Ricci coupling non-zero on III / IV / VI_h / VII_h since their
   anisotropic 3-Ricci is non-trivial (FB-1.4 class-A-unified
   formula).
5. h-parametrisation consistency: III (h = −1), IV (h = 0),
   VI_h / VII_h continuously indexed; VII_h spiral damping reduces
   to Harrison-V in the h → 0 limit.
6. Partition invariant: ``SUPPORTED_TYPES = FB21 ∪ FB22 ∪ FB23``
   covers all 11 Bianchi types + FLRW (12 labels, disjoint union).

Tolerances:

- ``∇̃`` eigenmode pins: rel 1e-12 (complex ``i k`` round-off at
  ε_mach).
- Laplacian eigenvalue pins: rel 1e-12.
- T1 Ricci coupling non-zero: norm > 1e-8 (physical tensor magnitude).

References
----------
- ``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-2.3``.
- Wainwright & Ellis 1997 §9.1 (Class B subfamilies).
- Harrison 1967 eq (4.5) (hyperbolic-harmonic twist offset; Type V
  reference for the ``a²`` shift).
- Pontzen & Challinor 2007 eq (2.12) (VII_h spiral harmonics).
- Ellis-Maartens-MacCallum 2012 §14.3 (spatial-Ricci coupling to the
  PSTF hierarchy).
- ``docs/audits/AUDIT_PHASE_FB2_2026-04-19.md`` — FB-2.3 supplement.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.background.bianchi_types import (
    type_iii_constants,
    type_iv_constants,
    type_v_constants,
    type_vih_constants,
    type_viih_constants,
)
from bass.background.tetrad_state import anisotropic_3_curvature
from bass.hierarchy.nabla_dispatch import (
    DEFERRED_FB23_TYPES,
    HarmonicMode,
    SUPPORTED_FB23_TYPES,
    SUPPORTED_TYPES,
    make_nabla_tilde,
    scalar_laplacian_eigenvalue,
)
from bass.hierarchy.terms import T1_expansion


# ════════════════════════════════════════════════════════════════════
#   §1 — Type III (h = -1 canonical): axis-aligned plane wave
# ════════════════════════════════════════════════════════════════════


class TestTypeIIIAxisAligned:
    """Type III ≡ VI_{h=-1}: ``(n_1, 0, n_3)`` with ``a_twist² = -n_1 n_3``.
    Abelian subalgebra ``span{e_1, e_3}``; axis-aligned ``k_2 = 0``.
    """

    def test_typeIII_nabla_axis_aligned(self) -> None:
        """Scalar plane wave on the abelian ``(e_1, e_3)`` plane."""
        sc = type_iii_constants(n1=1.5e-2)
        k_vec = np.array([0.23, 0.0, -0.15], dtype=np.float64)
        mode = HarmonicMode(type_label="III", k_vec=k_vec)
        op = make_nabla_tilde(sc, mode)
        grad = op(np.array(1.0), kind="gradient")
        np.testing.assert_allclose(grad, 1j * k_vec, rtol=1e-12, atol=1e-15)

    def test_typeIII_divergence_rank1(self) -> None:
        sc = type_iii_constants(n1=1.0e-2)
        k_vec = np.array([0.11, 0.0, -0.22], dtype=np.float64)
        mode = HarmonicMode(type_label="III", k_vec=k_vec)
        op = make_nabla_tilde(sc, mode)
        V = np.array([1.0, -0.5, 2.0], dtype=np.float64)
        div = op(V, kind="divergence")
        expected = 1j * float(np.dot(k_vec, V))
        np.testing.assert_allclose(div, expected, rtol=1e-12, atol=1e-15)

    def test_typeIII_laplacian_h_minus_one_half_offset(self) -> None:
        """Type III has ``|h| = 1`` canonical, so the twist offset is
        ``a² / 2``. Eigenvalue: ``λ = -(|k|² + a²/2)``."""
        sc = type_iii_constants(n1=2.0e-2)  # a_twist default = n1 = 2e-2
        k_vec = np.array([0.1, 0.0, 0.2], dtype=np.float64)
        mode = HarmonicMode(type_label="III", k_vec=k_vec)
        lam = scalar_laplacian_eigenvalue(sc, mode)
        expected = -(0.01 + 0.04 + (sc.a_twist ** 2) / 2.0)
        assert lam == pytest.approx(expected, rel=1e-12, abs=1e-18)


# ════════════════════════════════════════════════════════════════════
#   §2 — Type IV (h = 0 marginal): Harrison-V analogue
# ════════════════════════════════════════════════════════════════════


class TestTypeIVAxisAligned:
    """Type IV: ``(0, 0, n_3)`` with ``a_twist > 0``, ``h = 0``.
    The Laplacian offset reduces to the Harrison-V form
    ``λ = -(|k|² + a_twist²)`` (h-factor ``1/(1+|h|) = 1`` at
    ``|h| = 0``)."""

    def test_typeIV_nabla_axis_aligned(self) -> None:
        sc = type_iv_constants(n3=2.0e-2, a_twist=1.0e-2)
        k_vec = np.array([0.15, 0.0, 0.3], dtype=np.float64)
        mode = HarmonicMode(type_label="IV", k_vec=k_vec)
        op = make_nabla_tilde(sc, mode)
        grad = op(np.array(1.0), kind="gradient")
        np.testing.assert_allclose(grad, 1j * k_vec, rtol=1e-12, atol=1e-15)

    def test_typeIV_laplacian_matches_harrison_V(self) -> None:
        """At h = 0 the Class B Laplacian offset equals Harrison-V's
        ``-(|k|² + a²)``. Checked by running a Type IV mode and a
        Type V mode at the same ``a_twist`` and ``|k|`` and pinning the
        equality."""
        a_twist = 3.0e-3
        sc_iv = type_iv_constants(n3=1.0e-2, a_twist=a_twist)
        sc_v = type_v_constants(a_twist=a_twist)
        k_vec = np.array([0.12, 0.0, 0.08], dtype=np.float64)
        mode_iv = HarmonicMode(type_label="IV", k_vec=k_vec)
        mode_v = HarmonicMode(type_label="V", k_vec=k_vec)
        lam_iv = scalar_laplacian_eigenvalue(sc_iv, mode_iv)
        lam_v = scalar_laplacian_eigenvalue(sc_v, mode_v)
        assert lam_iv == pytest.approx(lam_v, rel=1e-12, abs=1e-18)


# ════════════════════════════════════════════════════════════════════
#   §3 — Type VI_h: h-parametrised hyperbolic-like Class B
# ════════════════════════════════════════════════════════════════════


class TestTypeVIhAxisAligned:
    """VI_h: ``(+, 0, −)`` with ``h = a²/(n_1 n_3) ∈ (−∞,−1) ∪ (−1,0)``.
    Abelian ``(e_1, e_3)`` plane: ``k_2 = 0``. Laplacian
    ``λ = -(|k|² + a² / (1 + |h|))``."""

    def test_typeVIh_nabla_on_abelian(self) -> None:
        sc = type_vih_constants(n1=1.0e-2, n3=-2.0e-3, a_twist=5.0e-3)
        k_vec = np.array([0.17, 0.0, -0.09], dtype=np.float64)
        mode = HarmonicMode(type_label="VI_h", k_vec=k_vec)
        op = make_nabla_tilde(sc, mode)
        grad = op(np.array(1.0), kind="gradient")
        np.testing.assert_allclose(grad, 1j * k_vec, rtol=1e-12, atol=1e-15)

    def test_typeVIh_laplacian_h_factor_denominator(self) -> None:
        """λ pins to ``-(k² + a²/(1+|h|))`` at rel 1e-12."""
        sc = type_vih_constants(n1=1.0e-2, n3=-2.0e-3, a_twist=5.0e-3)
        k_vec = np.array([0.3, 0.0, 0.4], dtype=np.float64)
        mode = HarmonicMode(type_label="VI_h", k_vec=k_vec)
        lam = scalar_laplacian_eigenvalue(sc, mode)
        h = sc.h_parameter
        expected = -(0.09 + 0.16 + (sc.a_twist ** 2) / (1.0 + abs(h)))
        assert lam == pytest.approx(expected, rel=1e-12, abs=1e-18)


# ════════════════════════════════════════════════════════════════════
#   §4 — Type VII_h: Pontzen-Challinor spiral (symmetric-line allowed)
# ════════════════════════════════════════════════════════════════════


class TestTypeVIIhAxisAligned:
    """VII_h: ``(+, 0, +)`` with ``h > 0``. Abelian ``(e_1, e_3)``
    plane axis-aligned ``k_2 = 0`` — the PC 2007 spiral helical phase
    trivialises on this subset. Laplacian ``λ = -(|k|² + a²/(1+h))``.
    """

    def test_typeVIIh_nabla_symmetric_axis_aligned(self) -> None:
        """Symmetric line ``n_1 = n_3`` + axis-aligned on the abelian
        plane — spiral phase vanishes; ``∇̃`` acts as a plane wave."""
        sc = type_viih_constants(n1=1.2e-2, n3=1.2e-2, a_twist=5.0e-3)
        k_vec = np.array([0.25, 0.0, 0.4], dtype=np.float64)
        mode = HarmonicMode(type_label="VII_h", k_vec=k_vec)
        op = make_nabla_tilde(sc, mode)
        grad = op(np.array(1.0), kind="gradient")
        np.testing.assert_allclose(grad, 1j * k_vec, rtol=1e-12, atol=1e-15)

    def test_typeVIIh_laplacian_spiral_damping(self) -> None:
        """VII_h spiral damping factor ``1/(1+h)`` on the twist offset."""
        sc = type_viih_constants(n1=1.8e-2, n3=1.0e-2, a_twist=5.5e-3)
        k_vec = np.array([0.1, 0.0, 0.2], dtype=np.float64)
        mode = HarmonicMode(type_label="VII_h", k_vec=k_vec)
        lam = scalar_laplacian_eigenvalue(sc, mode)
        h = sc.h_parameter
        expected = -(0.01 + 0.04 + (sc.a_twist ** 2) / (1.0 + h))
        assert lam == pytest.approx(expected, rel=1e-12, abs=1e-18)

    def test_typeVIIh_h_to_zero_limit_matches_harrison(self) -> None:
        """In the ``h → 0`` limit VII_h Laplacian → Harrison-V's
        ``-(|k|² + a²)``. Continuity check at small h."""
        # Large n₁ n₃ with small a_twist pushes h → 0.
        sc = type_viih_constants(n1=1.0e-1, n3=1.0e-1, a_twist=1.0e-6)
        k_vec = np.array([0.1, 0.0, 0.0], dtype=np.float64)
        mode = HarmonicMode(type_label="VII_h", k_vec=k_vec)
        lam = scalar_laplacian_eigenvalue(sc, mode)
        # Harrison-V at identical (a, k): λ_V = -(|k|² + a²)
        sc_v = type_v_constants(a_twist=sc.a_twist)
        mode_v = HarmonicMode(type_label="V", k_vec=k_vec)
        lam_v = scalar_laplacian_eigenvalue(sc_v, mode_v)
        assert abs(lam - lam_v) < 1e-12


# ════════════════════════════════════════════════════════════════════
#   §5 — Off-plane (k_2 ≠ 0) modes raise FB-5.2
# ════════════════════════════════════════════════════════════════════


class TestFB23ClassBOffAxis:
    """``k_2 ≠ 0`` on any Class B type → ``NotImplementedError('FB-5.2')``.
    The e_2 direction carries the ``a_α = (0, a_twist, 0)`` twist
    generator; generic modes require the FB-5.2 helical/Wigner lift.
    """

    @pytest.mark.parametrize("label,sc_fn", [
        ("III", type_iii_constants),
        ("IV", type_iv_constants),
        ("VI_h", type_vih_constants),
        ("VII_h", type_viih_constants),
    ])
    def test_class_b_off_plane_raises_fb52(self, label, sc_fn) -> None:
        sc = sc_fn()
        mode = HarmonicMode(
            type_label=label, k_vec=np.array([0.1, 0.05, 0.0])
        )
        with pytest.raises(NotImplementedError, match="FB-5.2"):
            make_nabla_tilde(sc, mode)
        with pytest.raises(NotImplementedError, match="FB-5.2"):
            scalar_laplacian_eigenvalue(sc, mode)


# ════════════════════════════════════════════════════════════════════
#   §6 — T1 Ricci coupling non-zero for every Class B type
# ════════════════════════════════════════════════════════════════════


class TestT1ClassBRicciCoupling:
    """FB-1.4 gave every Class B type a non-zero anisotropic 3-Ricci
    (the N-tensor contribution, since the twist sector is isotropic in
    the aligned frame). FB-2.3 inherits this automatically — the T1
    hook wired in FB-2.2 activates on Class B without code change.
    """

    @pytest.mark.parametrize("label,sc_fn", [
        ("III", type_iii_constants),
        ("IV", type_iv_constants),
        ("VI_h", type_vih_constants),
        ("VII_h", type_viih_constants),
    ])
    def test_T1_class_b_ricci_contribution_nonzero(self, label, sc_fn) -> None:
        sc = sc_fn()
        R, status = anisotropic_3_curvature(sc, 1.0, 0.0, 0.0)
        assert R is not None
        assert status.endswith("class_b")
        # ³R_aniso is non-zero for every default Class B configuration
        # (default parameters exclude the symmetric line for VII_h).
        assert np.linalg.norm(R) > 0.0
        # Build a ℓ = 2 PSTF probe (trace-free).
        Pi2 = np.array([
            [2.0, 0.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, -1.0],
        ], dtype=np.float64)
        Theta = 1.0e-3
        out_base = T1_expansion(2, Pi2, Theta)
        out_ricci = T1_expansion(2, Pi2, Theta, aniso_ricci_tensor=R)
        assert np.linalg.norm(out_ricci - out_base) > 1e-8


# ════════════════════════════════════════════════════════════════════
#   §7 — Class B parametrisation sweep (III vs VI_h vs VII_h limits)
# ════════════════════════════════════════════════════════════════════


class TestClassBHParametrisation:
    """Cross-type sanity checks on the ``1/(1+|h|)`` denominator."""

    def test_III_matches_VI_h_approaching_minus_one(self) -> None:
        """VI_h with h → -1 reproduces Type III's twist offset ``a²/2``.
        We cannot pass h = -1 exactly (factory rejects it), so we
        sample h near -1 and pin continuity to the rel tolerance set
        by our choice of h.
        """
        # Build a VI_h configuration with h very close to -1 (but not
        # exactly; the factory would reject).
        n1 = 1.0e-2
        n3 = -1.0e-2 * 1.0001  # slight perturbation so h = -0.9999
        a_twist = 1.0e-2
        sc_vih = type_vih_constants(n1=n1, n3=n3, a_twist=a_twist)
        k_vec = np.array([0.3, 0.0, 0.4], dtype=np.float64)
        mode = HarmonicMode(type_label="VI_h", k_vec=k_vec)
        lam_vih = scalar_laplacian_eigenvalue(sc_vih, mode)
        # III at comparable (n_1, a_twist) sets h exactly -1:
        sc_iii = type_iii_constants(n1=n1, a_twist=a_twist)
        mode_iii = HarmonicMode(type_label="III", k_vec=k_vec)
        lam_iii = scalar_laplacian_eigenvalue(sc_iii, mode_iii)
        # Rel 1e-4 since h = -0.9999 vs h = -1; the offset ratio is
        # (1 + 1) / (1 + 0.9999) ≈ 1.00005, so the two eigenvalues
        # differ by ~5e-5 × (a²/2) ≈ 2.5e-9, well within our tolerance.
        assert lam_vih == pytest.approx(lam_iii, rel=1e-4)

    def test_IV_and_V_match_at_identical_a_k(self) -> None:
        """Type IV at h = 0 and Type V (Harrison) at the same
        ``(a_twist, k_vec)`` produce identical Laplacian eigenvalues —
        this test complements §2 above by sweeping several k vectors.
        """
        a_twist = 2.5e-3
        for k_mag in (0.1, 0.3, 0.8, 1.5):
            k_vec = np.array([k_mag, 0.0, k_mag / 2.0], dtype=np.float64)
            sc_iv = type_iv_constants(n3=5.0e-3, a_twist=a_twist)
            sc_v = type_v_constants(a_twist=a_twist)
            mode_iv = HarmonicMode(type_label="IV", k_vec=k_vec)
            mode_v = HarmonicMode(type_label="V", k_vec=k_vec)
            lam_iv = scalar_laplacian_eigenvalue(sc_iv, mode_iv)
            lam_v = scalar_laplacian_eigenvalue(sc_v, mode_v)
            assert lam_iv == pytest.approx(lam_v, rel=1e-12, abs=1e-18)


# ════════════════════════════════════════════════════════════════════
#   §8 — Partition invariants (12 labels, disjoint union)
# ════════════════════════════════════════════════════════════════════


def test_fb23_supported_types_contains_class_b_additions() -> None:
    """``SUPPORTED_FB23_TYPES`` exactly enumerates the four Class B
    twist-coupled types."""
    assert set(SUPPORTED_FB23_TYPES) == {"III", "IV", "VI_h", "VII_h"}


def test_fb23_deferred_tuple_is_drained() -> None:
    """After FB-2.3 landed the ``DEFERRED_FB23_TYPES`` tuple is empty
    (retained only for backward-compat imports)."""
    assert len(DEFERRED_FB23_TYPES) == 0


def test_fb23_supported_types_covers_twelve_labels() -> None:
    """Aggregate dispatch: FB-2.1 ∪ FB-2.2 ∪ FB-2.3 = 12 labels
    (11 Bianchi types + FLRW), disjoint union."""
    expected = {
        "FLRW", "I", "II", "III", "IV", "V",
        "VI_0", "VI_h", "VII_0", "VII_h", "VIII", "IX",
    }
    assert set(SUPPORTED_TYPES) == expected
    assert len(SUPPORTED_TYPES) == 12


# ════════════════════════════════════════════════════════════════════
#   §9 — Sign-constraint validators reject malformed Class B
# ════════════════════════════════════════════════════════════════════


class TestClassBValidatorSignGuards:
    """The FB-2.3 per-type validators re-check the Class B sign
    invariants (``n_1 > 0``, ``n_3`` per type, ``a_twist > 0``) at
    dispatch time. If the user bypasses the factory and hands in a
    malformed ``StructureConstants`` instance, the dispatch should
    raise ``ValueError`` rather than silently returning a nonsense op.
    """

    def test_typeIII_requires_n1_positive(self) -> None:
        from bass.background.bianchi_types import StructureConstants
        sc = StructureConstants(
            n1=0.0, n2=0.0, n3=-1.0e-2, a_twist=1.0e-2, label="III"
        )
        mode = HarmonicMode(
            type_label="III", k_vec=np.array([0.1, 0.0, 0.0])
        )
        with pytest.raises(ValueError, match="Type III requires"):
            make_nabla_tilde(sc, mode)

    def test_typeIV_requires_n1_zero(self) -> None:
        from bass.background.bianchi_types import StructureConstants
        sc = StructureConstants(
            n1=1.0e-2, n2=0.0, n3=1.0e-2, a_twist=1.0e-2, label="IV"
        )
        mode = HarmonicMode(
            type_label="IV", k_vec=np.array([0.1, 0.0, 0.0])
        )
        with pytest.raises(ValueError, match="Type IV requires"):
            make_nabla_tilde(sc, mode)

    def test_typeVIIh_requires_n3_positive(self) -> None:
        from bass.background.bianchi_types import StructureConstants
        sc = StructureConstants(
            n1=1.0e-2, n2=0.0, n3=-1.0e-2, a_twist=1.0e-2, label="VII_h"
        )
        mode = HarmonicMode(
            type_label="VII_h", k_vec=np.array([0.1, 0.0, 0.0])
        )
        with pytest.raises(ValueError, match="Type VII_h requires"):
            make_nabla_tilde(sc, mode)

    def test_class_b_requires_a_twist_positive(self) -> None:
        """All Class B types need ``a_twist > 0`` (definitionally).
        The shared ``_validate_class_b_axis_aligned_k2_zero`` guard
        raises a uniform ``ValueError`` for non-positive twist."""
        from bass.background.bianchi_types import StructureConstants
        sc = StructureConstants(
            n1=1.0e-2, n2=0.0, n3=-1.0e-2, a_twist=0.0, label="VI_h"
        )
        mode = HarmonicMode(
            type_label="VI_h", k_vec=np.array([0.1, 0.0, 0.0])
        )
        with pytest.raises(ValueError, match="a_twist > 0"):
            make_nabla_tilde(sc, mode)
