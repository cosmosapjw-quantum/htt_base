"""Tests for FB-3.5 β-gate reparametrisation.

Closes the FB-3.1 P2 carry (velocity vs rapidity parametrisation split)
by providing

- ``assert_tilt_admissible(β, v̂_e)`` — single SSOT admissibility gate
  used by ``TiltedSpeciesBackground.__post_init__`` and available for
  every downstream tilt consumer (FB-8 ``ObserverBoost``,
  FB-11 priors).
- ``velocity_to_rapidity(β)`` and ``rapidity_to_velocity(η)`` — the
  single-sourced conversion helpers between the two surfaces.
- ``TiltedSpeciesBackground.from_rapidity(base, η, v̂_e)`` — rapidity-
  input factory that delegates to the velocity ctor via the conversion
  helper.
- ``TiltedSpeciesBackground.rapidity`` — derived property; no new
  internal storage (the velocity anchor is preserved byte-for-byte).

Test ledger (R-01 .. R-14)
--------------------------
R-01 : ``velocity_to_rapidity(0.0) == 0.0`` exactly.
R-02 : ``rapidity_to_velocity(0.0) == 0.0`` exactly.
R-03 : round-trip ``tanh(atanh(β)) ≈ β`` across a sweep (rtol tight).
R-04 : round-trip ``atanh(tanh(η)) ≈ η`` across a sweep.
R-05 : ``velocity_to_rapidity`` raises on bad β (non-finite / negative / ≥1).
R-06 : ``rapidity_to_velocity`` raises on bad η (non-finite / negative).
R-07 : ``assert_tilt_admissible`` silent on admissible input.
R-08 : ``assert_tilt_admissible`` raises on each guard branch.
R-09 : ``TiltedSpeciesBackground.from_rapidity(..., η=0)`` produces
       β = 0 exactly (byte-identical to the velocity ctor at β = 0).
R-10 : ``from_rapidity(..., η > 0)`` and the derived ``.rapidity``
       property round-trip to the input rapidity.
R-11 : ``.rapidity`` at β = 0 returns exactly ``0.0``.
R-12 : FB-3.1 guards unchanged — test_T09 / T10 / T11 / T12 still pass
       the new gate-based ``__post_init__``.
R-13 : the shared gate is byte-behaviour compatible with the FB-3.1
       direct guards on each representative input.
R-14 : FB-3.2 anchor preservation — ``accel_from_tilt`` at β = 0 still
       returns ``np.zeros(3)`` after the gate refactor.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.hierarchy.tilt_kinematics import accel_from_tilt
from bass.species.base import SpeciesLabel
from bass.species.registry import SpeciesBackgroundRegistry
from bass.species.tilted import (
    TiltedSpeciesBackground,
    V_HAT_E_DEFAULT,
    V_HAT_NORM_TOL,
    assert_tilt_admissible,
    rapidity_to_velocity,
    velocity_to_rapidity,
)


@pytest.fixture(scope="module")
def registry():
    return SpeciesBackgroundRegistry.from_planck2018()


@pytest.fixture(scope="module")
def photon(registry):
    return registry[SpeciesLabel.PHOTON]


# ──────────────────────────────────────────────────────────────────────
# R-01 / R-02 : zero round-trips are exact
# ──────────────────────────────────────────────────────────────────────


def test_R01_velocity_to_rapidity_zero_exact():
    assert velocity_to_rapidity(0.0) == 0.0


def test_R02_rapidity_to_velocity_zero_exact():
    assert rapidity_to_velocity(0.0) == 0.0


# ──────────────────────────────────────────────────────────────────────
# R-03 / R-04 : round-trip fidelity across a sweep
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("beta", [1e-8, 1e-4, 0.01, 0.1, 0.3, 0.5, 0.7, 0.9, 0.99])
def test_R03_velocity_rapidity_round_trip(beta):
    rap = velocity_to_rapidity(beta)
    v2 = rapidity_to_velocity(rap)
    # atanh / tanh round-trip is not bit-exact in float64 but should
    # hold to machine precision.
    assert abs(v2 - beta) < 1e-14


@pytest.mark.parametrize("rap", [1e-8, 1e-4, 0.01, 0.1, 0.3, 0.5, 1.0, 2.0, 5.0])
def test_R04_rapidity_velocity_round_trip(rap):
    b = rapidity_to_velocity(rap)
    r2 = velocity_to_rapidity(b)
    # tanh saturates at large rap; atanh loses precision near 1.
    # Use a relative tolerance that scales with (1 + rap) to absorb
    # the saturated-regime precision loss without masking outright bugs.
    assert abs(r2 - rap) < 1e-13 * (1.0 + rap)


# ──────────────────────────────────────────────────────────────────────
# R-05 : velocity_to_rapidity guards
# ──────────────────────────────────────────────────────────────────────


def test_R05_velocity_to_rapidity_guards():
    with pytest.raises(ValueError, match=r"finite"):
        velocity_to_rapidity(float("nan"))
    with pytest.raises(ValueError, match=r"finite"):
        velocity_to_rapidity(float("inf"))
    with pytest.raises(ValueError, match=r"non-negative"):
        velocity_to_rapidity(-0.1)
    with pytest.raises(ValueError, match=r"superluminal"):
        velocity_to_rapidity(1.0)
    with pytest.raises(ValueError, match=r"superluminal"):
        velocity_to_rapidity(2.0)


# ──────────────────────────────────────────────────────────────────────
# R-06 : rapidity_to_velocity guards
# ──────────────────────────────────────────────────────────────────────


def test_R06_rapidity_to_velocity_guards():
    with pytest.raises(ValueError, match=r"finite"):
        rapidity_to_velocity(float("nan"))
    with pytest.raises(ValueError, match=r"finite"):
        rapidity_to_velocity(float("inf"))
    with pytest.raises(ValueError, match=r"non-negative"):
        rapidity_to_velocity(-0.1)


# ──────────────────────────────────────────────────────────────────────
# R-07 : gate silent on admissible input
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("beta", [0.0, 1e-6, 0.01, 0.3, 0.99])
@pytest.mark.parametrize(
    "v_hat",
    [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (-1.0, 0.0, 0.0)],
)
def test_R07_gate_silent_on_admissible(beta, v_hat):
    # Returns None without raising.
    assert assert_tilt_admissible(beta, v_hat) is None


# ──────────────────────────────────────────────────────────────────────
# R-08 : gate raises on each guard branch
# ──────────────────────────────────────────────────────────────────────


def test_R08_gate_raises_on_guards():
    with pytest.raises(ValueError, match=r"finite"):
        assert_tilt_admissible(float("nan"), V_HAT_E_DEFAULT)
    with pytest.raises(ValueError, match=r"non-negative"):
        assert_tilt_admissible(-0.1, V_HAT_E_DEFAULT)
    with pytest.raises(ValueError, match=r"superluminal"):
        assert_tilt_admissible(1.0, V_HAT_E_DEFAULT)
    with pytest.raises(ValueError, match=r"three components"):
        assert_tilt_admissible(0.1, (1.0, 0.0))
    with pytest.raises(ValueError, match=r"unit vector"):
        assert_tilt_admissible(0.1, (1.0, 1.0, 0.0))


# ──────────────────────────────────────────────────────────────────────
# R-09 : from_rapidity(..., η = 0) byte-identical to ctor at β = 0
# ──────────────────────────────────────────────────────────────────────


def test_R09_from_rapidity_zero_matches_ctor(photon):
    t_rap = TiltedSpeciesBackground.from_rapidity(
        base=photon, rapidity=0.0, v_hat_e=(0.0, 0.0, 1.0),
    )
    t_vel = TiltedSpeciesBackground(
        base=photon, beta=0.0, v_hat_e=(0.0, 0.0, 1.0),
    )
    assert t_rap.beta == t_vel.beta == 0.0
    assert t_rap.v_hat_e == t_vel.v_hat_e
    assert t_rap.gamma == t_vel.gamma == 1.0


# ──────────────────────────────────────────────────────────────────────
# R-10 : from_rapidity + .rapidity property round-trip
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("rap", [0.01, 0.1, 0.5, 1.0, 3.0])
def test_R10_from_rapidity_property_round_trip(photon, rap):
    t = TiltedSpeciesBackground.from_rapidity(base=photon, rapidity=rap)
    assert abs(t.rapidity - rap) < 1e-14
    # And the velocity is tanh(rap).
    assert abs(t.beta - float(np.tanh(rap))) < 1e-15


# ──────────────────────────────────────────────────────────────────────
# R-11 : .rapidity at β = 0 is exactly 0.0
# ──────────────────────────────────────────────────────────────────────


def test_R11_rapidity_at_beta_zero_is_exact(photon):
    t = TiltedSpeciesBackground(base=photon, beta=0.0)
    assert t.rapidity == 0.0


# ──────────────────────────────────────────────────────────────────────
# R-12 : FB-3.1 guards still trip via the new gate-based __post_init__
# ──────────────────────────────────────────────────────────────────────


def test_R12_fb31_guards_unchanged(photon):
    with pytest.raises(ValueError, match=r"superluminal"):
        TiltedSpeciesBackground(base=photon, beta=1.0)
    with pytest.raises(ValueError, match=r"superluminal"):
        TiltedSpeciesBackground(base=photon, beta=1.2)
    with pytest.raises(ValueError, match=r"non-negative"):
        TiltedSpeciesBackground(base=photon, beta=-0.1)
    with pytest.raises(ValueError, match=r"finite"):
        TiltedSpeciesBackground(base=photon, beta=float("nan"))
    with pytest.raises(ValueError, match=r"unit vector"):
        TiltedSpeciesBackground(base=photon, v_hat_e=(2.0, 0.0, 0.0))
    with pytest.raises(ValueError, match=r"three components"):
        TiltedSpeciesBackground(base=photon, v_hat_e=(1.0, 0.0))


# ──────────────────────────────────────────────────────────────────────
# R-13 : gate behaviour consistent with the direct guards
# ──────────────────────────────────────────────────────────────────────


def test_R13_gate_matches_direct_guards(photon):
    # Construct via gate, then ctor; both should behave the same on the
    # inputs (admissible → success; inadmissible → same exception class).
    for beta in (0.0, 0.01, 0.3, 0.9):
        for v_hat in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)):
            assert_tilt_admissible(beta, v_hat)
            # Ctor also succeeds.
            TiltedSpeciesBackground(base=photon, beta=beta, v_hat_e=v_hat)
    # Inadmissible cases
    for beta in (-0.1, 1.0, float("nan")):
        with pytest.raises(ValueError):
            assert_tilt_admissible(beta, V_HAT_E_DEFAULT)
        with pytest.raises(ValueError):
            TiltedSpeciesBackground(base=photon, beta=beta)


# ──────────────────────────────────────────────────────────────────────
# R-14 : FB-3.2 anchor preservation after gate refactor
# ──────────────────────────────────────────────────────────────────────


def test_R14_fb32_anchor_preserved(photon):
    t0 = TiltedSpeciesBackground(base=photon, beta=0.0)
    out = accel_from_tilt(t0, 1.0)
    np.testing.assert_array_equal(out, np.zeros(3))


# ──────────────────────────────────────────────────────────────────────
# R-15 : norm tolerance constant unchanged (regression pin on SSOT)
# ──────────────────────────────────────────────────────────────────────


def test_R15_norm_tolerance_ssot():
    assert V_HAT_NORM_TOL == 1e-10
