"""Tests for FB-3.4 — dynamic vorticity feedback into hierarchy T6.

Extends the FB-3.2 static vorticity surface by adding an optional
``bg_table`` kwarg that multiplies the static piece by the EMM §6.4
dilution factor ``(a_today / a(η))²``. β = 0 and Class A paths remain
byte-identical short-circuits; FB-3.2 backward compatibility (no
kwargs) is preserved byte-for-byte.

Test ledger (V-01 .. V-10)
--------------------------
V-01 : FB-3.2 backward-compat — `bg_table=None` matches the static
       formula byte-identically.
V-02 : β = 0 short-circuit on FB-3.4 kwargs path.
V-03 : Class A short-circuit on FB-3.4 kwargs path (structure
       supplied, a_twist = 0, bg_table supplied).
V-04 : closed-form dilution: at β > 0 × Class B,
       `vorticity_from_tilt(bg_table=bg) = (1/2) a×v · (a_today/a(η))²`.
V-05 : dynamic η-dependence — two different η values give different
       vorticity magnitudes (unlike FB-3.2 static value).
V-06 : negative a(η) (pathological fixture) raises `ValueError`.
V-07 : driver β = 0 byte-identical under FB-3.4 extended kwargs.
V-08 : driver β > 0 × Class B produces finite dy and differs from
       the FB-3.2 static path.
V-09 : Class B dilution direction sign — at η < η_today (a < a_today)
       the dilution factor is > 1, so |ω_dynamic| > |ω_static|.
V-10 : η-sweep dilution monotonicity — as η → η_today, dilution → 1.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.background.bianchi_types import get_type
from bass.hierarchy.closure_interface import HardCutClosure
from bass.hierarchy.collision_interface import ZeroCollisionOperator
from bass.hierarchy.hierarchy_rhs import hierarchy_rhs_photon
from bass.hierarchy.pstf_tensor import (
    PSTFTensor,
    pack_hierarchy,
    zero_hierarchy,
)
from bass.hierarchy.tilt_kinematics import (
    accel_from_tilt,
    vorticity_from_tilt,
)
from bass.species.base import SpeciesLabel
from bass.species.registry import SpeciesBackgroundRegistry
from bass.species.tilted import TiltedSpeciesBackground


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def registry():
    return SpeciesBackgroundRegistry.from_planck2018()


@pytest.fixture(scope="module")
def bg_table(registry):
    return registry.bg_table


@pytest.fixture(scope="module")
def photon(registry):
    return registry[SpeciesLabel.PHOTON]


# ──────────────────────────────────────────────────────────────────────
# V-01 : FB-3.2 backward-compat
# ──────────────────────────────────────────────────────────────────────


def test_V01_backward_compat_no_bg_table(photon, bg_table):
    structure = get_type("V")
    tilted = TiltedSpeciesBackground(base=photon, beta=0.2)
    eta = float(bg_table.eta[500])

    out_no_kw = vorticity_from_tilt(tilted, eta, structure=structure)
    # Match the explicit FB-3.2 formula.
    v = np.asarray(tilted.v_vector(eta), dtype=np.float64)
    a_vec = np.array([0.0, structure.a_twist, 0.0], dtype=np.float64)
    expected = 0.5 * np.cross(a_vec, v)
    np.testing.assert_allclose(out_no_kw, expected, rtol=0.0, atol=0.0)


# ──────────────────────────────────────────────────────────────────────
# V-02 : β = 0 short-circuit
# ──────────────────────────────────────────────────────────────────────


def test_V02_beta_zero_short_circuit_fb34(photon, bg_table):
    structure = get_type("V")
    tilted = TiltedSpeciesBackground(base=photon, beta=0.0)
    eta = float(bg_table.eta[500])
    out = vorticity_from_tilt(
        tilted, eta, structure=structure, bg_table=bg_table,
    )
    np.testing.assert_array_equal(out, np.zeros(3))


# ──────────────────────────────────────────────────────────────────────
# V-03 : Class A short-circuit with bg_table supplied
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("label", ["I", "II", "VI_0", "VII_0", "VIII", "IX"])
def test_V03_class_A_short_circuit_fb34(photon, bg_table, label):
    structure = get_type(label)
    assert structure.a_twist == 0.0
    tilted = TiltedSpeciesBackground(base=photon, beta=0.3)
    eta = float(bg_table.eta[500])
    out = vorticity_from_tilt(
        tilted, eta, structure=structure, bg_table=bg_table,
    )
    np.testing.assert_array_equal(out, np.zeros(3))


# ──────────────────────────────────────────────────────────────────────
# V-04 : closed-form dilution
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("label", ["III", "IV", "V", "VI_h", "VII_h"])
def test_V04_dilution_closed_form(photon, bg_table, label):
    structure = get_type(label)
    assert structure.a_twist != 0.0
    beta = 0.2
    tilted = TiltedSpeciesBackground(base=photon, beta=beta)
    eta = float(bg_table.eta[500])
    out = vorticity_from_tilt(
        tilted, eta, structure=structure, bg_table=bg_table,
    )
    # Expected: (1/2) a × v × (a_today / a(η))²
    v = np.asarray(tilted.v_vector(eta), dtype=np.float64)
    a_vec = np.array([0.0, structure.a_twist, 0.0], dtype=np.float64)
    a_today = float(bg_table.interp_a(float(bg_table.eta_today)))
    a_at_eta = float(bg_table.interp_a(eta))
    expected = 0.5 * np.cross(a_vec, v) * (a_today / a_at_eta) ** 2
    np.testing.assert_allclose(out, expected, rtol=0.0, atol=0.0)


# ──────────────────────────────────────────────────────────────────────
# V-05 : dynamic η-dependence
# ──────────────────────────────────────────────────────────────────────


def test_V05_eta_dependence_non_trivial(photon, bg_table):
    structure = get_type("V")
    tilted = TiltedSpeciesBackground(base=photon, beta=0.2)
    eta_early = float(bg_table.eta[10])
    eta_late = float(bg_table.eta[-10])

    ω_early = vorticity_from_tilt(
        tilted, eta_early, structure=structure, bg_table=bg_table,
    )
    ω_late = vorticity_from_tilt(
        tilted, eta_late, structure=structure, bg_table=bg_table,
    )
    assert not np.array_equal(ω_early, ω_late)
    # At η_early, a(η) is small → dilution factor is large → |ω_early| > |ω_late|.
    assert np.linalg.norm(ω_early) > np.linalg.norm(ω_late)


# ──────────────────────────────────────────────────────────────────────
# V-06 : pathological a(η) <= 0 raises ValueError — tested via a mock
# ──────────────────────────────────────────────────────────────────────


def test_V06_non_positive_a_raises(photon, bg_table):
    class _MockBg:
        eta_today = float(bg_table.eta_today)
        def interp_a(self, eta):
            if float(eta) == float(bg_table.eta_today):
                return 1.0
            return -1.0  # pathological
    structure = get_type("V")
    tilted = TiltedSpeciesBackground(base=photon, beta=0.3)
    with pytest.raises(ValueError, match=r"non-positive"):
        vorticity_from_tilt(
            tilted, float(bg_table.eta[100]),
            structure=structure, bg_table=_MockBg(),
        )


# ──────────────────────────────────────────────────────────────────────
# V-07 : driver β = 0 byte-identical under extended kwargs
# ──────────────────────────────────────────────────────────────────────


def test_V07_driver_beta_zero_byte_identity(photon, bg_table):
    L_max = 3
    rng = np.random.default_rng(34)
    state = zero_hierarchy(L_max)
    for ell in range(L_max + 1):
        state.tensors[ell] = PSTFTensor(
            ell=ell, components=rng.normal(size=2 * ell + 1),
        )
    y0 = pack_hierarchy(state)
    eta = float(bg_table.eta[bg_table.eta.size // 2])

    dy_anchor = hierarchy_rhs_photon(
        eta, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )

    tilted = TiltedSpeciesBackground(base=photon, beta=0.0)
    structure = get_type("V")
    dy_fb34 = hierarchy_rhs_photon(
        eta, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        accel_vector=accel_from_tilt(tilted, eta),
        vorticity_vector=vorticity_from_tilt(
            tilted, eta, structure=structure, bg_table=bg_table,
        ),
    )
    assert np.array_equal(dy_fb34, dy_anchor)


# ──────────────────────────────────────────────────────────────────────
# V-08 : driver β > 0 Class B differs between FB-3.2 static and FB-3.4 dynamic
# ──────────────────────────────────────────────────────────────────────


def test_V08_driver_static_vs_dynamic_differs(photon, bg_table):
    L_max = 3
    rng = np.random.default_rng(38)
    state = zero_hierarchy(L_max)
    for ell in range(L_max + 1):
        state.tensors[ell] = PSTFTensor(
            ell=ell, components=rng.normal(size=2 * ell + 1),
        )
    y0 = pack_hierarchy(state)
    eta = float(bg_table.eta[bg_table.eta.size // 2])

    tilted = TiltedSpeciesBackground(base=photon, beta=0.15)
    structure = get_type("V")

    ω_static = vorticity_from_tilt(tilted, eta, structure=structure)
    ω_dynamic = vorticity_from_tilt(
        tilted, eta, structure=structure, bg_table=bg_table,
    )
    # At the mid-grid η, dilution factor is clearly not 1, so the two differ.
    assert not np.array_equal(ω_static, ω_dynamic)

    dy_static = hierarchy_rhs_photon(
        eta, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        accel_vector=accel_from_tilt(tilted, eta),
        vorticity_vector=ω_static,
    )
    dy_dynamic = hierarchy_rhs_photon(
        eta, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        accel_vector=accel_from_tilt(tilted, eta),
        vorticity_vector=ω_dynamic,
    )
    assert np.all(np.isfinite(dy_static))
    assert np.all(np.isfinite(dy_dynamic))
    assert not np.array_equal(dy_static, dy_dynamic)


# ──────────────────────────────────────────────────────────────────────
# V-09 : dilution direction sign (a < a_today → factor > 1)
# ──────────────────────────────────────────────────────────────────────


def test_V09_dilution_factor_greater_than_one_at_early_eta(photon, bg_table):
    structure = get_type("V")
    tilted = TiltedSpeciesBackground(base=photon, beta=0.2)
    eta_early = float(bg_table.eta[10])

    ω_dynamic = vorticity_from_tilt(
        tilted, eta_early, structure=structure, bg_table=bg_table,
    )
    ω_static = vorticity_from_tilt(
        tilted, eta_early, structure=structure,
    )
    # |ω_dynamic| > |ω_static| at early times.
    assert np.linalg.norm(ω_dynamic) > np.linalg.norm(ω_static)


# ──────────────────────────────────────────────────────────────────────
# V-10 : dilution monotonicity — closer to η_today, factor closer to 1
# ──────────────────────────────────────────────────────────────────────


def test_V10_dilution_monotone_towards_today(photon, bg_table):
    structure = get_type("V")
    tilted = TiltedSpeciesBackground(base=photon, beta=0.2)

    norms = []
    ratios = []
    for idx in (10, 100, 500, 900, bg_table.eta.size - 10):
        eta = float(bg_table.eta[idx])
        dyn = vorticity_from_tilt(
            tilted, eta, structure=structure, bg_table=bg_table,
        )
        stat = vorticity_from_tilt(tilted, eta, structure=structure)
        norms.append(np.linalg.norm(dyn))
        static_norm = np.linalg.norm(stat)
        ratios.append(np.linalg.norm(dyn) / static_norm if static_norm > 0 else 0.0)

    # ratios should decrease monotonically toward 1 as η approaches η_today.
    for i in range(len(ratios) - 1):
        assert ratios[i] >= ratios[i + 1] - 1e-12
    # Last ratio is close to (a(η_{-10}) / a_today)²... should be close to 1.
    assert ratios[-1] < ratios[0]
