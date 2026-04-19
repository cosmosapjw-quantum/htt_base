"""Tests for bass/hierarchy/tilt_kinematics.py (FB-3.2).

Covers the two non-negotiable invariants of the wire-up rotation:

- **β = 0 anchor**: ``accel_from_tilt`` and ``vorticity_from_tilt``
  return fresh ``np.zeros(3)`` for every structure constants / v̂_e
  combination, so a caller feeding these through
  ``hierarchy_rhs_photon`` at β = 0 reproduces the FB-2.4 regression
  byte-for-byte (commit ``d7d25da``).
- **β > 0 kinematic content**: the adapters return the expected
  closed-form leading pieces (``γ² v^a`` for the tilt acceleration,
  ``(1/2) a × v`` for the Class B vorticity, zero for Class A
  vorticity).

Test ledger
-----------

- K-01..K-02 : β = 0 bit-identical across FLRW + the 11 Bianchi types.
- K-03      : β > 0 ``accel_from_tilt`` closed-form (γ² v^a).
- K-04      : β > 0 Class A vorticity = zeros (6 types).
- K-05      : β > 0 Class B vorticity = (1/2) a × v (5 types).
- K-06      : shape (3,) guarantee on every branch.
- K-07      : fresh-copy guard (mutating one output must not leak into
              the next call).
- K-08      : ``structure=None`` (explicit) at β > 0 → zeros.
- K-09      : β = 0 full driver byte-identical to FB-2.4 anchor
              (no-kwargs baseline).
- K-10      : β > 0 full driver output is finite and differs from the
              β = 0 anchor (non-trivial T4/T5/T6 activation).
- K-11      : β > 0 Class B full driver activates T6 (vorticity) —
              output differs vs. Class A counterpart.
- K-12      : FB-3.1 P2 overlap — the composition rule
              ``TiltedSpeciesParams(v = β · v̂_e)`` matches
              ``TiltedSpeciesBackground(β, v̂_e).v_vector(η)``.
- K-13      : eta-independence at the FB-3.2 surface (vector is time-
              invariant per contract).
- K-14      : ValueError never raised at the adapter boundary when
              β ∈ [0, 1) + well-formed v̂_e (delegate guard coverage to
              ``test_tilted.py``).
- K-15      : Levi-Civita sign convention pin on Class B vorticity.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.background.bianchi_types import (
    ALL_BIANCHI_TYPES,
    CLASS_A_TYPES,
    CLASS_B_TYPES,
    flrw_constants,
    get_type,
)
from bass.hierarchy.closure_interface import HardCutClosure
from bass.hierarchy.collision_interface import ZeroCollisionOperator
from bass.hierarchy.hierarchy_rhs import hierarchy_rhs_photon
from bass.hierarchy.pstf_tensor import (
    PSTFTensor,
    hierarchy_total_size,
    pack_hierarchy,
    zero_hierarchy,
)
from bass.hierarchy.tilt_kinematics import (
    accel_from_tilt,
    vorticity_from_tilt,
)
from bass.species.registry import SpeciesBackgroundRegistry
from bass.species.base import SpeciesLabel
from bass.species.tilted import TiltedSpeciesBackground, V_HAT_E_DEFAULT
from bass.tilt.species_tilt import TiltedSpeciesParams


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def registry() -> SpeciesBackgroundRegistry:
    return SpeciesBackgroundRegistry.from_planck2018()


@pytest.fixture(scope="module")
def bg_table(registry: SpeciesBackgroundRegistry):
    return registry.bg_table


@pytest.fixture(scope="module")
def photon(registry: SpeciesBackgroundRegistry):
    return registry[SpeciesLabel.PHOTON]


@pytest.fixture(scope="module")
def eta_sample(bg_table) -> float:
    # Pick a mid-grid η inside the physical domain.
    return float(bg_table.eta[bg_table.eta.size // 2])


# Every type label we need to sweep (FLRW + 11 Bianchi types).
_ALL_LABELS = ("FLRW",) + tuple(ALL_BIANCHI_TYPES)


# ──────────────────────────────────────────────────────────────────────
# K-01, K-02 : β = 0 bit-identical across all structure-constant labels.
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("label", _ALL_LABELS)
def test_K01_accel_beta_zero_returns_zeros(photon, eta_sample, label):
    structure = get_type(label)  # noqa: F841 — adapter reads no attribute at β=0
    tilted = TiltedSpeciesBackground(base=photon, beta=0.0)
    out = accel_from_tilt(tilted, eta_sample)
    assert out.shape == (3,)
    np.testing.assert_array_equal(out, np.zeros(3))


@pytest.mark.parametrize("label", _ALL_LABELS)
def test_K02_vorticity_beta_zero_returns_zeros(photon, eta_sample, label):
    structure = get_type(label)
    tilted = TiltedSpeciesBackground(base=photon, beta=0.0)
    out = vorticity_from_tilt(tilted, eta_sample, structure=structure)
    assert out.shape == (3,)
    np.testing.assert_array_equal(out, np.zeros(3))


# ──────────────────────────────────────────────────────────────────────
# K-03 : β > 0 accel = γ² v^a.
# ──────────────────────────────────────────────────────────────────────


def test_K03_accel_closed_form_beta_positive(photon, eta_sample):
    beta = 0.25
    v_hat = (1.0, 0.0, 0.0)
    tilted = TiltedSpeciesBackground(base=photon, beta=beta, v_hat_e=v_hat)
    out = accel_from_tilt(tilted, eta_sample)
    gamma_sq = 1.0 / (1.0 - beta * beta)
    expected = np.array(
        [gamma_sq * beta * v_hat[0], gamma_sq * beta * v_hat[1], gamma_sq * beta * v_hat[2]],
        dtype=np.float64,
    )
    np.testing.assert_allclose(out, expected, rtol=0.0, atol=0.0)


# ──────────────────────────────────────────────────────────────────────
# K-04 : β > 0 vorticity is zero for every Class A type (a_twist = 0).
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("label", CLASS_A_TYPES)
def test_K04_vorticity_class_A_is_zero_at_beta_positive(
    photon, eta_sample, label,
):
    structure = get_type(label)
    assert structure.a_twist == 0.0  # sanity
    tilted = TiltedSpeciesBackground(base=photon, beta=0.3)
    out = vorticity_from_tilt(tilted, eta_sample, structure=structure)
    np.testing.assert_array_equal(out, np.zeros(3))


# ──────────────────────────────────────────────────────────────────────
# K-05 : β > 0 vorticity = (1/2) a × v for Class B.
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("label", CLASS_B_TYPES)
def test_K05_vorticity_class_B_closed_form(photon, eta_sample, label):
    structure = get_type(label)
    assert structure.a_twist != 0.0
    beta = 0.2
    v_hat = (1.0, 0.0, 0.0)
    tilted = TiltedSpeciesBackground(base=photon, beta=beta, v_hat_e=v_hat)
    out = vorticity_from_tilt(tilted, eta_sample, structure=structure)
    a_vec = np.array([0.0, structure.a_twist, 0.0], dtype=np.float64)
    v_spatial = np.array([beta * v_hat[0], beta * v_hat[1], beta * v_hat[2]])
    expected = 0.5 * np.cross(a_vec, v_spatial)
    np.testing.assert_allclose(out, expected, rtol=0.0, atol=0.0)


# ──────────────────────────────────────────────────────────────────────
# K-06 : shape guarantee on every branch.
# ──────────────────────────────────────────────────────────────────────


def test_K06_shape_guarantee(photon, eta_sample):
    t0 = TiltedSpeciesBackground(base=photon, beta=0.0)
    tp = TiltedSpeciesBackground(base=photon, beta=0.5)
    assert accel_from_tilt(t0, eta_sample).shape == (3,)
    assert accel_from_tilt(tp, eta_sample).shape == (3,)
    struct_A = get_type("I")
    struct_B = get_type("V")
    assert vorticity_from_tilt(t0, eta_sample, structure=None).shape == (3,)
    assert vorticity_from_tilt(t0, eta_sample, structure=struct_A).shape == (3,)
    assert vorticity_from_tilt(tp, eta_sample, structure=struct_B).shape == (3,)


# ──────────────────────────────────────────────────────────────────────
# K-07 : fresh copy on β = 0 path (caller mutation safety).
# ──────────────────────────────────────────────────────────────────────


def test_K07_fresh_copy_on_beta_zero(photon, eta_sample):
    t0 = TiltedSpeciesBackground(base=photon, beta=0.0)
    a1 = accel_from_tilt(t0, eta_sample)
    a1[0] = 1.0  # caller mutation MUST NOT leak into next call.
    a2 = accel_from_tilt(t0, eta_sample)
    np.testing.assert_array_equal(a2, np.zeros(3))

    structure = get_type("V")
    o1 = vorticity_from_tilt(t0, eta_sample, structure=structure)
    o1[1] = 7.0
    o2 = vorticity_from_tilt(t0, eta_sample, structure=structure)
    np.testing.assert_array_equal(o2, np.zeros(3))


# ──────────────────────────────────────────────────────────────────────
# K-08 : explicit structure=None at β > 0 returns zeros (do-nothing path).
# ──────────────────────────────────────────────────────────────────────


def test_K08_vorticity_structure_none_is_zero(photon, eta_sample):
    tilted = TiltedSpeciesBackground(base=photon, beta=0.3)
    out = vorticity_from_tilt(tilted, eta_sample, structure=None)
    np.testing.assert_array_equal(out, np.zeros(3))


# ──────────────────────────────────────────────────────────────────────
# K-09 : β = 0 full driver byte-identical to the FB-2.4 no-kwargs anchor.
#
# This is the regression contract: the new adapter chain, when fed a
# β = 0 species, must not alter a single bit of hierarchy_rhs_photon's
# output compared to the FB-2.4 call that passed neither kwarg.
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("label", _ALL_LABELS)
def test_K09_driver_beta_zero_bit_identical_to_fb24(
    photon, bg_table, eta_sample, label,
):
    structure = get_type(label)
    L_max = 3
    rng = np.random.default_rng(abs(hash(label)) % (2**31))
    state = zero_hierarchy(L_max)
    for ell in range(L_max + 1):
        state.tensors[ell] = PSTFTensor(
            ell=ell,
            components=rng.normal(size=2 * ell + 1),
        )
    y0 = pack_hierarchy(state)

    # FB-2.4 anchor: no tilt kwargs at all.
    dy_anchor = hierarchy_rhs_photon(
        eta_sample,
        y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )

    # FB-3.2 path: β = 0 adapter output → kwargs. Must be byte-identical.
    tilted = TiltedSpeciesBackground(base=photon, beta=0.0)
    dy_fb32 = hierarchy_rhs_photon(
        eta_sample,
        y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        accel_vector=accel_from_tilt(tilted, eta_sample),
        vorticity_vector=vorticity_from_tilt(
            tilted, eta_sample, structure=structure,
        ),
    )

    assert np.array_equal(dy_fb32, dy_anchor), (
        f"β=0 adapter-fed driver drifted from FB-2.4 anchor on label "
        f"{label!r}; max |Δ| = {np.max(np.abs(dy_fb32 - dy_anchor))!r}"
    )


# ──────────────────────────────────────────────────────────────────────
# K-10 : β > 0 driver output is finite and differs from the β = 0 anchor.
# ──────────────────────────────────────────────────────────────────────


def test_K10_driver_beta_positive_is_finite_and_differs(
    photon, bg_table, eta_sample,
):
    L_max = 3
    rng = np.random.default_rng(10)
    state = zero_hierarchy(L_max)
    for ell in range(L_max + 1):
        state.tensors[ell] = PSTFTensor(
            ell=ell,
            components=rng.normal(size=2 * ell + 1),
        )
    y0 = pack_hierarchy(state)

    structure = get_type("I")  # Class A, no vorticity contribution.

    t0 = TiltedSpeciesBackground(base=photon, beta=0.0)
    dy0 = hierarchy_rhs_photon(
        eta_sample, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        accel_vector=accel_from_tilt(t0, eta_sample),
        vorticity_vector=vorticity_from_tilt(
            t0, eta_sample, structure=structure,
        ),
    )

    tp = TiltedSpeciesBackground(base=photon, beta=0.1)
    dy_p = hierarchy_rhs_photon(
        eta_sample, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        accel_vector=accel_from_tilt(tp, eta_sample),
        vorticity_vector=vorticity_from_tilt(
            tp, eta_sample, structure=structure,
        ),
    )

    assert np.all(np.isfinite(dy_p))
    # T4 / T5 pick up a γ² v^a acceleration at β > 0.
    assert not np.array_equal(dy_p, dy0)


# ──────────────────────────────────────────────────────────────────────
# K-11 : Class B driver activates T6 — output differs from Class A
# counterpart at β > 0 (pins the vorticity routing).
# ──────────────────────────────────────────────────────────────────────


def test_K11_class_B_driver_differs_from_class_A(
    photon, bg_table, eta_sample,
):
    L_max = 3
    rng = np.random.default_rng(11)
    state = zero_hierarchy(L_max)
    for ell in range(L_max + 1):
        state.tensors[ell] = PSTFTensor(
            ell=ell,
            components=rng.normal(size=2 * ell + 1),
        )
    y0 = pack_hierarchy(state)

    beta = 0.1
    # v_hat_e aligned away from the a_twist axis so (a × v) ≠ 0.
    v_hat = (1.0, 0.0, 0.0)
    tilted = TiltedSpeciesBackground(base=photon, beta=beta, v_hat_e=v_hat)

    struct_A = get_type("I")
    struct_B = get_type("V")
    assert struct_A.a_twist == 0.0
    assert struct_B.a_twist != 0.0

    dy_A = hierarchy_rhs_photon(
        eta_sample, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        accel_vector=accel_from_tilt(tilted, eta_sample),
        vorticity_vector=vorticity_from_tilt(
            tilted, eta_sample, structure=struct_A,
        ),
    )
    dy_B = hierarchy_rhs_photon(
        eta_sample, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        accel_vector=accel_from_tilt(tilted, eta_sample),
        vorticity_vector=vorticity_from_tilt(
            tilted, eta_sample, structure=struct_B,
        ),
    )

    assert np.all(np.isfinite(dy_A))
    assert np.all(np.isfinite(dy_B))
    # The acceleration piece is identical (species-only); only ω differs.
    assert not np.array_equal(dy_A, dy_B)


# ──────────────────────────────────────────────────────────────────────
# K-12 : FB-3.1 P2 overlap — composition rule vs Y-Block TiltedSpeciesParams.
# ──────────────────────────────────────────────────────────────────────


def test_K12_p2_overlap_composition_rule(photon, eta_sample):
    """The LB-1 surface ``TiltedSpeciesBackground(β, v̂_e)`` and the
    Y-Block surface ``TiltedSpeciesParams(v)`` coincide exactly under
    the composition ``v = β · v̂_e`` (FB-3.1 §5 P2 overlap).
    """
    beta = 0.4
    v_hat = (0.0, 1.0, 0.0)
    tilted = TiltedSpeciesBackground(base=photon, beta=beta, v_hat_e=v_hat)

    # Y-Block surface: v is the 3-velocity directly.
    v_expected = np.array(
        [beta * v_hat[0], beta * v_hat[1], beta * v_hat[2]],
        dtype=np.float64,
    )
    y_params = TiltedSpeciesParams(
        rho_hat=1.0, p_hat=1.0 / 3.0, v=v_expected, label="photon",
    )

    # The composition rule: FB-3.1's v_vector(η) at any η reproduces
    # the Y-Block v-field by construction.
    v_fb31 = np.asarray(tilted.v_vector(float(eta_sample)), dtype=np.float64)
    np.testing.assert_allclose(v_fb31, y_params.v, rtol=0.0, atol=0.0)

    # And the Lorentz factors coincide.
    assert tilted.gamma == pytest.approx(y_params.gamma, rel=1e-15)


# ──────────────────────────────────────────────────────────────────────
# K-13 : η-independence (FB-3.2 surface only; FB-3.3 will break this).
# ──────────────────────────────────────────────────────────────────────


def test_K13_eta_independent_at_fb32(photon, bg_table):
    tilted = TiltedSpeciesBackground(base=photon, beta=0.15)
    structure = get_type("V")
    eta1 = float(bg_table.eta[5])
    eta2 = float(bg_table.eta[50])
    np.testing.assert_array_equal(
        accel_from_tilt(tilted, eta1),
        accel_from_tilt(tilted, eta2),
    )
    np.testing.assert_array_equal(
        vorticity_from_tilt(tilted, eta1, structure=structure),
        vorticity_from_tilt(tilted, eta2, structure=structure),
    )


# ──────────────────────────────────────────────────────────────────────
# K-14 : Admissible β / v̂_e inputs do not raise at the adapter surface.
# ──────────────────────────────────────────────────────────────────────


def test_K14_admissible_inputs_do_not_raise(photon, eta_sample):
    struct_A = get_type("I")
    struct_B = get_type("V")
    for beta in (0.0, 1e-6, 0.01, 0.1, 0.5, 0.9):
        tilted = TiltedSpeciesBackground(base=photon, beta=beta)
        # Both adapters must return finite (3,) on every admissible β.
        a = accel_from_tilt(tilted, eta_sample)
        oA = vorticity_from_tilt(tilted, eta_sample, structure=struct_A)
        oB = vorticity_from_tilt(tilted, eta_sample, structure=struct_B)
        assert np.all(np.isfinite(a))
        assert np.all(np.isfinite(oA))
        assert np.all(np.isfinite(oB))


# ──────────────────────────────────────────────────────────────────────
# K-15 : Levi-Civita sign convention on Class B vorticity.
#
# With a = (0, a_twist, 0) and v = (β, 0, 0), ω = (1/2) a × v =
# (1/2)(a2·v3 − a3·v2, a3·v1 − a1·v3, a1·v2 − a2·v1)
# = (1/2)(0, 0, a_twist·β·(−1))    (because a_2 = a_twist, v_1 = β)
# The third component is -(1/2) · a_twist · β; the first two are 0.
# Pins the right-handed ε convention used in ``np.cross``.
# ──────────────────────────────────────────────────────────────────────


def test_K15_vorticity_levi_civita_sign(photon, eta_sample):
    structure = get_type("V")  # a_twist > 0 for Type V
    beta = 0.2
    tilted = TiltedSpeciesBackground(
        base=photon, beta=beta, v_hat_e=(1.0, 0.0, 0.0),
    )
    out = vorticity_from_tilt(tilted, eta_sample, structure=structure)
    expected = np.array(
        [0.0, 0.0, -0.5 * structure.a_twist * beta], dtype=np.float64,
    )
    np.testing.assert_allclose(out, expected, rtol=0.0, atol=0.0)
