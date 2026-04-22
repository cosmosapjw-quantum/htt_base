"""FB-2.4 — hierarchy RHS driver regression sweep (Phase FB-2 exit).

Validates the FB-2.4 wire-up of ``tetrad_state.aniso_3_curvature``
into ``T1_expansion`` / ``T2_gradient`` via ``hierarchy_rhs_photon``:

- **FLRW / flat regression** (``TestHierarchyRhsFlatBitIdentical``):
  FLRW and Type I both have ``aniso_3_curvature ≡ 0``, so the FB-2.4
  driver path must reproduce the LB-6 ``tetrad_state=None`` output
  bit-for-bit. Preserves the LB-6 sealed baseline.
- **11-type finite-ness sweep**
  (``TestPhaseFB2ExitRegression``): every registered Bianchi type +
  FLRW must produce a finite, shape-consistent ``dy/dη`` at β=0 with
  a representative seeded PSTF tower.
- **Class-B Ricci pin** (``TestClassBRicciContributionNonzero``):
  III / IV / VI_h / VII_h all have non-zero ``³R_ab^{aniso}``, so
  the T1 curved-space correction must yield a *non-zero difference*
  between the FB-2.4 driver path and the legacy LB-6
  ``tetrad_state=None`` path when the tower has a non-trivial
  rank-≥1 component.
- **T4/T5/T6 β=0 structural hook**
  (``TestKinematicHooksZeroAtBeta0``): with ``A = ω = 0`` (the β=0
  orthogonal default), the driver passes zero vectors to T4/T5/T6
  and those terms contribute zero to the RHS. The kwargs are
  structurally wired; FB-3 will activate them with non-zero values.

Reference — Ellis-Maartens-MacCallum 2012 §16 (nine-term hierarchy);
``docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-2.4``;
``docs/audits/AUDIT_PHASE_FB2_2026-04-19.md`` FB-2.4 supplement.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from bass.background.bianchi_types import ALL_BIANCHI_TYPES, flrw_constants
from bass.background.einstein_bianchi import (
    BianchiCosmology,
    solve_bianchi_background,
)
from bass.background.tetrad_state import build_tetrad_state
from bass.hierarchy import (
    HardCutClosure,
    PSTFTensor,
    ZeroCollisionOperator,
    hierarchy_rhs_photon,
    hierarchy_total_size,
    pack_hierarchy,
    zero_hierarchy,
)
from bass.hierarchy.hierarchy_rhs import aniso_ricci_at_eta
from bass.species.background_table import build_flrw_background_table


@dataclass(frozen=True)
class _ConstantRicciFixture:
    eta: np.ndarray
    aniso_3_curvature: np.ndarray


# ════════════════════════════════════════════════════════════════════
#   Shared fixtures
# ════════════════════════════════════════════════════════════════════

def _seeded_tower(L_max: int, seed: int, scale: float = 1.0) -> np.ndarray:
    """Build a deterministic PSTF tower with non-trivial ℓ ≥ 1 content.

    Rank-0 / 1 / 2 slots get non-zero PSTF components so T1 (at every
    ℓ) and T8 (ℓ = 2 anchor) both have something to contract. The
    ``scale`` parameter sets the amplitude — default ``1.0`` gives
    components of order unity (useful for Ricci-coupling pins where
    the physical amplitude of Π is cancelled out of the linear-RHS
    validity check).
    """
    rng = np.random.default_rng(seed)
    state = zero_hierarchy(L_max)
    for ell in range(L_max + 1):
        comp = rng.normal(size=2 * ell + 1) * scale
        state.tensors[ell] = PSTFTensor(ell=ell, components=comp)
    return pack_hierarchy(state)


def _build_tetrad(label: str):
    """Construct a TetradBackgroundState for a label at β=0 orthogonal.

    Uses the same coarse-grid parameters as
    ``TestBuildTetradStateAniso3CurvatureFB14`` (100 η samples,
    ``a_start=1e-4``, ``a_end=0.5``) to keep the sweep fast.
    """
    from bass.background.bianchi_types import get_type
    sc = flrw_constants() if label == "FLRW" else get_type(label)
    cosmo = BianchiCosmology(structure=sc)
    bg = solve_bianchi_background(
        cosmo, a_start=1e-4, a_end=0.5, n_pts=100,
    )
    return build_tetrad(bg) if False else build_tetrad_state(bg)


@pytest.fixture(scope="module")
def bg_table():
    return build_flrw_background_table(n_eta=400)


def test_constant_2d_aniso_ricci_fixture_bypasses_spline() -> None:
    """A constant 2D Ricci tensor should be returned directly."""
    ricci = np.array(
        [
            [2.0, -0.3, 0.1],
            [-0.3, -1.0, 0.2],
            [0.1, 0.2, -1.0],
        ],
        dtype=np.float64,
    )
    tetrad = _ConstantRicciFixture(
        eta=np.linspace(1.0, 5.0, 4, dtype=np.float64),
        aniso_3_curvature=ricci,
    )
    recovered = aniso_ricci_at_eta(3.0, tetrad)
    assert recovered is not None
    assert np.array_equal(recovered, ricci)


# ════════════════════════════════════════════════════════════════════
#   TestHierarchyRhsFlatBitIdentical — LB-6 regression (FLRW / Type I)
# ════════════════════════════════════════════════════════════════════

class TestHierarchyRhsFlatBitIdentical:
    """FLRW and Type I have ``³R_ab^{aniso} ≡ 0``; the FB-2.4 driver
    path must reproduce the legacy ``tetrad_state=None`` output
    bit-for-bit (``rtol = 0, atol = 1e-15``).

    Together these two cases seal the LB-6 contract: no anisotropic
    curvature ⇒ no behaviour change.
    """

    @pytest.mark.parametrize("label", ["FLRW", "I"])
    def test_flat_tetrad_bit_identical_to_none(self, label, bg_table):
        L_max = 3
        y0 = _seeded_tower(L_max, seed=24)
        eta_mid = bg_table.eta[bg_table.eta.size // 2]

        dy_none = hierarchy_rhs_photon(
            eta_mid, y0, L_max=L_max, bg_table=bg_table,
            tetrad_state=None, closure=HardCutClosure(),
            collision=ZeroCollisionOperator(),
        )

        tetrad = _build_tetrad(label)
        dy_flat = hierarchy_rhs_photon(
            eta_mid, y0, L_max=L_max, bg_table=bg_table,
            tetrad_state=tetrad, closure=HardCutClosure(),
            collision=ZeroCollisionOperator(),
        )

        # Flat tetrad adds (i) zero σ contribution and (ii) zero ³R
        # contribution, so the difference must be zero to machine
        # precision (the shared bg_table supplies a/θ identically).
        diff = np.max(np.abs(dy_flat - dy_none))
        assert diff < 1e-14, (
            f"{label} flat-tetrad path differs from None-path by "
            f"{diff:.3e}; expected bit-identical"
        )


# ════════════════════════════════════════════════════════════════════
#   TestPhaseFB2ExitRegression — 11-type × β=0 finite-ness sweep
# ════════════════════════════════════════════════════════════════════

class TestPhaseFB2ExitRegression:
    """Phase FB-2 exit — every registered label (11 Bianchi + FLRW)
    yields a finite, shape-consistent hierarchy RHS at β=0.

    At β=0 orthogonal the tilt vector ``v_a`` is zero, so ``A_a`` and
    ``ω_a`` passed by the driver default to zero vectors: T4/T5/T6
    contribute zero. σ is evolved from ``sigma_over_H_init`` by
    ``solve_bianchi_background`` and is generally non-zero at mid-η,
    so T7/T8/T9 carry real values; T1 may also have a non-zero
    curved-space piece on Class-A/Class-B anisotropic labels.
    """

    @pytest.mark.parametrize("label", ALL_BIANCHI_TYPES + ["FLRW"])
    def test_dy_is_finite_and_shape_preserving(self, label, bg_table):
        L_max = 3
        y0 = _seeded_tower(L_max, seed=2 + hash(label) % 1000)
        eta_mid = bg_table.eta[bg_table.eta.size // 2]

        tetrad = _build_tetrad(label)
        # Each build uses its own bg_table (from solve_bianchi_background);
        # for the RHS finite-ness check we use the shared FLRW bg_table
        # because only interp_a / interp_Theta are consulted and the
        # bg_table's η grid is a superset of the tetrad's.
        dy = hierarchy_rhs_photon(
            eta_mid, y0, L_max=L_max, bg_table=bg_table,
            tetrad_state=tetrad, closure=HardCutClosure(),
            collision=ZeroCollisionOperator(),
        )

        assert dy.shape == y0.shape, (
            f"{label}: dy shape {dy.shape} != y0 shape {y0.shape}"
        )
        assert np.all(np.isfinite(dy)), (
            f"{label}: non-finite entries in dy (min={dy.min()}, "
            f"max={dy.max()})"
        )


# ════════════════════════════════════════════════════════════════════
#   TestClassBRicciContributionNonzero — T1 curved-space correction
# ════════════════════════════════════════════════════════════════════

class TestClassBRicciContributionNonzero:
    """Class-B types (III / IV / VI_h / VII_h) have non-zero
    ``³R_ab^{aniso}`` at the PC-frame defaults, so the FB-2.4 driver
    path must yield a *non-zero* RHS difference from the LB-6
    ``aniso_ricci=None`` path when the tower carries non-trivial
    rank-≥1 PSTF content. Anchors the T1 Ricci coupling wire-up.
    """

    @pytest.mark.parametrize("label", ["III", "IV", "VI_h", "VII_h"])
    def test_class_b_t1_ricci_rhs_norm_nonzero(self, label, bg_table):
        L_max = 3
        # Scale tower amplitude up to unity so the Ricci-coupling pin
        # is robust against structure-constant smallness (``n ~ 1e-2``
        # at the PC-frame defaults → ``³R_aniso ~ 1e-4 Mpc⁻²``).
        y0 = _seeded_tower(L_max, seed=100, scale=1.0)
        eta_mid = bg_table.eta[bg_table.eta.size // 2]

        tetrad = _build_tetrad(label)
        assert tetrad.aniso_3_curvature is not None
        # Sanity — the anisotropic 3-Ricci is numerically non-trivial
        # at mid-η (ℓ ≥ 1 coupling target).
        ricci_mid = aniso_ricci_at_eta(eta_mid, tetrad)
        assert ricci_mid is not None
        assert np.linalg.norm(ricci_mid) > 1e-12, (
            f"{label}: expected non-trivial ³R_aniso at mid-η, got "
            f"frob={np.linalg.norm(ricci_mid):.3e}"
        )

        dy_with = hierarchy_rhs_photon(
            eta_mid, y0, L_max=L_max, bg_table=bg_table,
            tetrad_state=tetrad, closure=HardCutClosure(),
            collision=ZeroCollisionOperator(),
        )

        # Duck-type tetrad copy with aniso_3_curvature set to zeros —
        # this isolates the T1 Ricci contribution without touching the
        # σ (T7/T8/T9) path.
        import dataclasses as _dc
        tetrad_noricci = _dc.replace(
            tetrad,
            aniso_3_curvature=np.zeros_like(tetrad.aniso_3_curvature),
        )
        dy_without = hierarchy_rhs_photon(
            eta_mid, y0, L_max=L_max, bg_table=bg_table,
            tetrad_state=tetrad_noricci, closure=HardCutClosure(),
            collision=ZeroCollisionOperator(),
        )

        delta_norm = np.linalg.norm(dy_with - dy_without)
        assert delta_norm > 1e-10, (
            f"{label}: T1 aniso-Ricci contribution vanished "
            f"(|Δdy| = {delta_norm:.3e}) — driver wire-up regression?"
        )


# ════════════════════════════════════════════════════════════════════
#   TestKinematicHooksZeroAtBeta0 — T4/T5/T6 structural wire-up
# ════════════════════════════════════════════════════════════════════

class TestKinematicHooksZeroAtBeta0:
    """At β=0 orthogonal, ``A_a = ω_a = 0`` (default kwargs). The
    FB-2.4 driver is expected to forward zero vectors to T4/T5/T6
    and those terms must contribute exactly zero to the RHS.

    Passing a non-zero A / ω via the kwargs must yield a *different*
    RHS — proving the kwargs are structurally wired (ready for FB-3).
    """

    def test_zero_kinematic_vectors_unchanged_vs_defaults(self, bg_table):
        """Explicit zero vectors must reproduce the default-None path."""
        L_max = 3
        y0 = _seeded_tower(L_max, seed=41)
        eta_mid = bg_table.eta[bg_table.eta.size // 2]

        dy_default = hierarchy_rhs_photon(
            eta_mid, y0, L_max=L_max, bg_table=bg_table,
            tetrad_state=None, closure=HardCutClosure(),
            collision=ZeroCollisionOperator(),
        )
        dy_zero_kin = hierarchy_rhs_photon(
            eta_mid, y0, L_max=L_max, bg_table=bg_table,
            tetrad_state=None, closure=HardCutClosure(),
            collision=ZeroCollisionOperator(),
            accel_vector=np.zeros(3),
            vorticity_vector=np.zeros(3),
        )
        assert np.allclose(dy_default, dy_zero_kin, rtol=0, atol=1e-15)

    def test_nonzero_accel_changes_rhs(self, bg_table):
        """Non-zero A_a must produce a non-zero RHS difference (proof
        that the driver actually forwards the kwarg into T4/T5)."""
        L_max = 3
        y0 = _seeded_tower(L_max, seed=41)
        eta_mid = bg_table.eta[bg_table.eta.size // 2]

        dy_no_accel = hierarchy_rhs_photon(
            eta_mid, y0, L_max=L_max, bg_table=bg_table,
            tetrad_state=None, closure=HardCutClosure(),
            collision=ZeroCollisionOperator(),
        )
        dy_with_accel = hierarchy_rhs_photon(
            eta_mid, y0, L_max=L_max, bg_table=bg_table,
            tetrad_state=None, closure=HardCutClosure(),
            collision=ZeroCollisionOperator(),
            accel_vector=np.array([1e-2, 0.0, 0.0]),
        )
        delta = np.linalg.norm(dy_with_accel - dy_no_accel)
        assert delta > 1e-12, (
            f"Non-zero accel produced no RHS change (Δ = {delta:.3e}); "
            "T4/T5 kwarg forwarding regression"
        )

    def test_nonzero_vorticity_changes_rhs(self, bg_table):
        """Non-zero ω_a must produce a non-zero RHS difference (proof
        that the driver actually forwards the kwarg into T6)."""
        L_max = 3
        y0 = _seeded_tower(L_max, seed=41)
        eta_mid = bg_table.eta[bg_table.eta.size // 2]

        dy_no_vort = hierarchy_rhs_photon(
            eta_mid, y0, L_max=L_max, bg_table=bg_table,
            tetrad_state=None, closure=HardCutClosure(),
            collision=ZeroCollisionOperator(),
        )
        dy_with_vort = hierarchy_rhs_photon(
            eta_mid, y0, L_max=L_max, bg_table=bg_table,
            tetrad_state=None, closure=HardCutClosure(),
            collision=ZeroCollisionOperator(),
            vorticity_vector=np.array([0.0, 1e-2, 0.0]),
        )
        delta = np.linalg.norm(dy_with_vort - dy_no_vort)
        assert delta > 1e-12, (
            f"Non-zero vorticity produced no RHS change (Δ = {delta:.3e}); "
            "T6 kwarg forwarding regression"
        )


# ════════════════════════════════════════════════════════════════════
#   aniso_ricci_at_eta — helper contract
# ════════════════════════════════════════════════════════════════════

class TestAnisoRicciAtEta:
    """Contract tests for the FB-2.4 ``aniso_ricci_at_eta`` helper."""

    def test_none_tetrad_returns_none(self):
        assert aniso_ricci_at_eta(10.0, None) is None

    def test_missing_aniso_field_returns_none(self):
        """When ``aniso_3_curvature`` is ``None`` on the tetrad state
        (unavailable curvature status), the helper returns None —
        preserving the LB-6 bit-identical path."""
        class _Stub:
            eta = np.linspace(1.0, 100.0, 5)
            aniso_3_curvature = None
        assert aniso_ricci_at_eta(50.0, _Stub()) is None

    def test_non_none_interpolation_returns_symmetric_3x3(self):
        """When ``aniso_3_curvature`` is populated the helper returns
        a (3,3) tensor. For a constant-in-η Ricci grid the
        interpolation is exact."""
        eta_grid = np.linspace(1.0, 100.0, 10)
        ricci = np.array([
            [[2.0, 1.0, 0.0], [1.0, -1.0, 0.0], [0.0, 0.0, -1.0]]
        ] * 10)

        class _Stub:
            pass
        s = _Stub()
        s.eta = eta_grid
        s.aniso_3_curvature = ricci

        out = aniso_ricci_at_eta(50.0, s)
        assert out is not None
        assert out.shape == (3, 3)
        assert np.allclose(out, ricci[0], atol=1e-12)

    def test_out_of_grid_clamps_to_endpoint(self):
        """η outside the grid clamps to the endpoint Ricci
        (same convention as ``proper_shear_at_eta``)."""
        eta_grid = np.linspace(1.0, 100.0, 5)
        ricci = np.tile(np.eye(3) - np.trace(np.eye(3)) / 3.0 * np.eye(3),
                        (5, 1, 1))
        # Make it actually non-trivial (diagonal trace-free):
        ricci = np.tile(np.diag([1.0, -0.5, -0.5]), (5, 1, 1))
        ricci[-1] = np.diag([2.0, -1.0, -1.0])

        class _Stub:
            pass
        s = _Stub()
        s.eta = eta_grid
        s.aniso_3_curvature = ricci

        # Beyond η=100 → clamp to last
        out_high = aniso_ricci_at_eta(500.0, s)
        assert out_high is not None
        assert np.allclose(out_high, ricci[-1], atol=1e-12)
