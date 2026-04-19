"""Tests for FB-3.3 — Einstein + tilt coupling on accel_from_tilt +
axi-symmetric boost-kernel seed.

Covers the non-negotiable invariants of the third FB-3 rotation:

- **FB-3.2 backward compatibility** — ``accel_from_tilt(tilted, eta)``
  without any of the new kwargs returns byte-identical output to the
  FB-3.2 anchor (commit ``fdb1d86``).
- **β=0 byte-identity** — on every FB-3.3 code path (kwargs variant,
  boost_kernel variant), β=0 returns the zero / identity branch
  byte-identically so the FB-2.4 anchor (commit ``d7d25da``) is
  preserved.
- **Additive closed-form** — the extended `accel_from_tilt` value
  matches the EMM eq (5.17) additive formula on synthetic
  ``bg_table`` / ``tetrad_state`` inputs.
- **Boost kernel** — β=0 identity; β>0 on-axis linear Challinor eq
  (26); off-axis NotImplementedError.

Test ledger
-----------
- M-01..M-03 : `accel_from_tilt` β=0 path byte-identity with new kwargs.
- M-04 : FB-3.2 backward compatibility (no kwargs).
- M-05 : Θ-piece additive closed form.
- M-06 : σ-piece additive closed form.
- M-07 : combined Θ + σ additive.
- M-08 : tetrad_state without bg_table raises ValueError.
- M-09 : boost-kernel β=0 identity on an arbitrary m=0 slice.
- M-10 : boost-kernel β>0 linear Challinor recurrence closed form.
- M-11 : boost-kernel off-axis → NotImplementedError.
- M-12 : boost-kernel β out of range → ValueError.
- M-13 : boost-kernel non-1D input → ValueError.
- M-14 : `is_axis_aligned` branch coverage.
- M-15 : boost-kernel fresh-copy guard.
- M-16 : boost-kernel shape preservation.
- M-17 : composition `accel_from_tilt` extended path vs manual sum.
- M-18 : driver byte-identity under FB-3.3 default-kwargs composition.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.background.bianchi_types import flrw_constants, get_type
from bass.background.einstein_bianchi import BianchiCosmology
from bass.background.tetrad_state import TetradBackgroundState
from bass.hierarchy.boost_kernel import (
    AXIS_ALIGNMENT_TOL,
    boost_project_axisymmetric,
    is_axis_aligned,
)
from bass.hierarchy.closure_interface import HardCutClosure
from bass.hierarchy.collision_interface import ZeroCollisionOperator
from bass.hierarchy.hierarchy_rhs import hierarchy_rhs_photon, proper_shear_at_eta
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
from bass.species.tilted import TiltedSpeciesBackground, V_HAT_E_DEFAULT


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def registry() -> SpeciesBackgroundRegistry:
    return SpeciesBackgroundRegistry.from_planck2018()


@pytest.fixture(scope="module")
def bg_table(registry):
    return registry.bg_table


@pytest.fixture(scope="module")
def photon(registry):
    return registry[SpeciesLabel.PHOTON]


@pytest.fixture(scope="module")
def eta_sample(bg_table) -> float:
    return float(bg_table.eta[bg_table.eta.size // 2])


def _axisymmetric_sigma_fixture(eta_grid: np.ndarray) -> TetradBackgroundState:
    """Build a tiny TetradBackgroundState with a non-zero but analytic
    conformal Σ_ab so σ-piece additivity can be checked against a
    closed form. Uses FLRW structure constants and a Σ that is
    diag(2/3, -1/3, -1/3)·s(η) (traceless by construction) with
    ``s(η) = const``. Scale factor tiny but positive so the
    conformal→proper conversion is well-defined.
    """
    N = eta_grid.size
    a_grid = 1e-6 * np.ones(N)
    s_val = 1.0e-4
    sigma_base = np.diag([2.0 / 3.0, -1.0 / 3.0, -1.0 / 3.0])
    sigma_conformal = s_val * np.broadcast_to(
        sigma_base[None, :, :], (N, 3, 3)
    ).copy()
    return TetradBackgroundState(
        eta=eta_grid,
        alpha=np.log(a_grid),
        a=a_grid,
        beta_tensor=np.zeros((N, 3, 3)),
        sigma_tensor=sigma_conformal,
        aniso_3_curvature=None,
        structure=flrw_constants(),
        curvature_status="type_i_flat",
        cosmo=BianchiCosmology(structure=flrw_constants()),
    )


# ──────────────────────────────────────────────────────────────────────
# M-01..M-03 : β=0 byte-identity on every new kwargs path
# ──────────────────────────────────────────────────────────────────────


def test_M01_accel_beta_zero_bg_table_only_is_zero(photon, bg_table, eta_sample):
    tilted = TiltedSpeciesBackground(base=photon, beta=0.0)
    out = accel_from_tilt(tilted, eta_sample, bg_table=bg_table)
    np.testing.assert_array_equal(out, np.zeros(3))


def test_M02_accel_beta_zero_both_kwargs_is_zero(photon, bg_table, eta_sample):
    fx = _axisymmetric_sigma_fixture(np.asarray(bg_table.eta, dtype=np.float64))
    tilted = TiltedSpeciesBackground(base=photon, beta=0.0)
    out = accel_from_tilt(
        tilted, eta_sample, bg_table=bg_table, tetrad_state=fx,
    )
    np.testing.assert_array_equal(out, np.zeros(3))


def test_M03_accel_beta_zero_preserves_fresh_copy(photon, bg_table, eta_sample):
    tilted = TiltedSpeciesBackground(base=photon, beta=0.0)
    out1 = accel_from_tilt(tilted, eta_sample, bg_table=bg_table)
    out1[0] = 1.0
    out2 = accel_from_tilt(tilted, eta_sample, bg_table=bg_table)
    np.testing.assert_array_equal(out2, np.zeros(3))


# ──────────────────────────────────────────────────────────────────────
# M-04 : FB-3.2 backward compatibility
# ──────────────────────────────────────────────────────────────────────


def test_M04_accel_no_kwargs_matches_fb32(photon, eta_sample):
    beta = 0.2
    tilted = TiltedSpeciesBackground(base=photon, beta=beta)
    out = accel_from_tilt(tilted, eta_sample)
    expected_fb32 = tilted.gamma_sq * np.asarray(
        tilted.v_vector(float(eta_sample)), dtype=np.float64,
    )
    np.testing.assert_allclose(out, expected_fb32, rtol=0.0, atol=0.0)


# ──────────────────────────────────────────────────────────────────────
# M-05 : Θ-piece additivity
# ──────────────────────────────────────────────────────────────────────


def test_M05_accel_theta_piece_closed_form(photon, bg_table, eta_sample):
    beta = 0.25
    tilted = TiltedSpeciesBackground(base=photon, beta=beta)
    v = np.asarray(tilted.v_vector(float(eta_sample)), dtype=np.float64)
    Theta = float(bg_table.interp_Theta(float(eta_sample)))
    expected = tilted.gamma_sq * v + tilted.gamma_sq * (Theta / 3.0) * v
    out = accel_from_tilt(tilted, eta_sample, bg_table=bg_table)
    np.testing.assert_allclose(out, expected, rtol=0.0, atol=0.0)


# ──────────────────────────────────────────────────────────────────────
# M-06 : σ-piece additivity
# ──────────────────────────────────────────────────────────────────────


def test_M06_accel_sigma_piece_closed_form(photon, bg_table, eta_sample):
    fx = _axisymmetric_sigma_fixture(np.asarray(bg_table.eta, dtype=np.float64))
    beta = 0.2
    v_hat = (1.0, 0.0, 0.0)  # axis-aligned so σ·v is analytic
    tilted = TiltedSpeciesBackground(base=photon, beta=beta, v_hat_e=v_hat)

    # Expected: FB-3.2 γ²v + γ² Θ/3 v + γ² σ·v
    v = np.asarray(tilted.v_vector(float(eta_sample)), dtype=np.float64)
    Theta = float(bg_table.interp_Theta(float(eta_sample)))
    a_val = float(bg_table.interp_a(float(eta_sample)))
    sigma = proper_shear_at_eta(float(eta_sample), fx, a_val)
    expected = (
        tilted.gamma_sq * v
        + tilted.gamma_sq * (Theta / 3.0) * v
        + tilted.gamma_sq * (sigma @ v)
    )
    out = accel_from_tilt(
        tilted, eta_sample, bg_table=bg_table, tetrad_state=fx,
    )
    np.testing.assert_allclose(out, expected, rtol=0.0, atol=0.0)


# ──────────────────────────────────────────────────────────────────────
# M-07 : combined Θ + σ additivity — same as M-06 with different beta
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("beta", [0.01, 0.1, 0.5])
def test_M07_accel_combined_theta_sigma_sweep(photon, bg_table, eta_sample, beta):
    fx = _axisymmetric_sigma_fixture(np.asarray(bg_table.eta, dtype=np.float64))
    tilted = TiltedSpeciesBackground(base=photon, beta=beta)
    v = np.asarray(tilted.v_vector(float(eta_sample)), dtype=np.float64)
    Theta = float(bg_table.interp_Theta(float(eta_sample)))
    a_val = float(bg_table.interp_a(float(eta_sample)))
    sigma = proper_shear_at_eta(float(eta_sample), fx, a_val)
    expected = (
        tilted.gamma_sq * v
        + tilted.gamma_sq * (Theta / 3.0) * v
        + tilted.gamma_sq * (sigma @ v)
    )
    out = accel_from_tilt(
        tilted, eta_sample, bg_table=bg_table, tetrad_state=fx,
    )
    assert np.all(np.isfinite(out))
    np.testing.assert_allclose(out, expected, rtol=0.0, atol=0.0)


# ──────────────────────────────────────────────────────────────────────
# M-08 : tetrad_state without bg_table → ValueError
# ──────────────────────────────────────────────────────────────────────


def test_M08_accel_tetrad_without_bg_table_raises(photon, bg_table, eta_sample):
    fx = _axisymmetric_sigma_fixture(np.asarray(bg_table.eta, dtype=np.float64))
    tilted = TiltedSpeciesBackground(base=photon, beta=0.1)
    with pytest.raises(ValueError, match=r"tetrad_state requires bg_table"):
        accel_from_tilt(tilted, eta_sample, tetrad_state=fx)


# ──────────────────────────────────────────────────────────────────────
# M-09 : boost-kernel β=0 identity
# ──────────────────────────────────────────────────────────────────────


def test_M09_boost_kernel_beta_zero_identity():
    coeffs = np.array([1.0, -0.3, 0.7, 0.05, 0.001], dtype=np.float64)
    out = boost_project_axisymmetric(coeffs, beta=0.0)
    np.testing.assert_array_equal(out, coeffs)
    assert out is not coeffs  # fresh copy


# ──────────────────────────────────────────────────────────────────────
# M-10 : boost-kernel β>0 linear Challinor recurrence
# ──────────────────────────────────────────────────────────────────────


def test_M10_boost_kernel_linear_challinor():
    coeffs = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
    beta = 0.1
    out = boost_project_axisymmetric(coeffs, beta=beta, v_hat_e=(1.0, 0.0, 0.0))

    expected = coeffs.copy()
    L = coeffs.size
    for ell in range(L):
        delta = 0.0
        if ell - 1 >= 0:
            delta += (ell / (2.0 * ell - 1.0)) * coeffs[ell - 1]
        if ell + 1 < L:
            delta -= ((ell + 1.0) / (2.0 * ell + 3.0)) * coeffs[ell + 1]
        expected[ell] = coeffs[ell] + beta * delta
    np.testing.assert_allclose(out, expected, rtol=0.0, atol=0.0)


# ──────────────────────────────────────────────────────────────────────
# M-11 : off-axis v̂_e → NotImplementedError
# ──────────────────────────────────────────────────────────────────────


def test_M11_boost_kernel_off_axis_raises():
    coeffs = np.array([1.0, 0.0, 0.0])
    # Clean off-axis direction (45° in the e1-e3 plane).
    v_hat = (1.0 / np.sqrt(2.0), 0.0, 1.0 / np.sqrt(2.0))
    with pytest.raises(NotImplementedError, match=r"off-axis"):
        boost_project_axisymmetric(coeffs, beta=0.1, v_hat_e=v_hat)


# ──────────────────────────────────────────────────────────────────────
# M-12 : β out of range → ValueError
# ──────────────────────────────────────────────────────────────────────


def test_M12_boost_kernel_beta_range():
    coeffs = np.ones(3)
    with pytest.raises(ValueError, match=r"0 ≤ β < 1"):
        boost_project_axisymmetric(coeffs, beta=-0.1)
    with pytest.raises(ValueError, match=r"0 ≤ β < 1"):
        boost_project_axisymmetric(coeffs, beta=1.0)
    with pytest.raises(ValueError, match=r"finite"):
        boost_project_axisymmetric(coeffs, beta=float("nan"))


# ──────────────────────────────────────────────────────────────────────
# M-13 : non-1D input → ValueError
# ──────────────────────────────────────────────────────────────────────


def test_M13_boost_kernel_shape_guard():
    coeffs_2d = np.ones((3, 3))
    with pytest.raises(ValueError, match=r"1-D"):
        boost_project_axisymmetric(coeffs_2d, beta=0.1)


# ──────────────────────────────────────────────────────────────────────
# M-14 : `is_axis_aligned`
# ──────────────────────────────────────────────────────────────────────


def test_M14_is_axis_aligned():
    assert is_axis_aligned((1.0, 0.0, 0.0))
    assert is_axis_aligned((0.0, 1.0, 0.0))
    assert is_axis_aligned((0.0, 0.0, 1.0))
    assert is_axis_aligned((-1.0, 0.0, 0.0))
    assert not is_axis_aligned((0.6, 0.8, 0.0))
    assert not is_axis_aligned(
        (np.cos(0.01), np.sin(0.01), 0.0)
    )  # slightly off-axis


# ──────────────────────────────────────────────────────────────────────
# M-15 : boost-kernel fresh-copy guard on β>0 path
# ──────────────────────────────────────────────────────────────────────


def test_M15_boost_kernel_fresh_copy_beta_positive():
    coeffs = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    out = boost_project_axisymmetric(coeffs, beta=0.1)
    out[0] = 42.0
    # Input unchanged
    np.testing.assert_array_equal(coeffs, np.array([1.0, 2.0, 3.0]))


# ──────────────────────────────────────────────────────────────────────
# M-16 : shape preservation
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("L_plus_1", [1, 2, 5, 10, 33])
def test_M16_boost_kernel_shape_preservation(L_plus_1):
    coeffs = np.linspace(0.0, 1.0, L_plus_1)
    out = boost_project_axisymmetric(coeffs, beta=0.05)
    assert out.shape == (L_plus_1,)


# ──────────────────────────────────────────────────────────────────────
# M-17 : composition — extended accel equals FB-3.2 + explicit deltas
# ──────────────────────────────────────────────────────────────────────


def test_M17_composition_sum(photon, bg_table, eta_sample):
    fx = _axisymmetric_sigma_fixture(np.asarray(bg_table.eta, dtype=np.float64))
    beta = 0.3
    tilted = TiltedSpeciesBackground(base=photon, beta=beta)
    fb32_piece = accel_from_tilt(tilted, eta_sample)
    extended = accel_from_tilt(
        tilted, eta_sample, bg_table=bg_table, tetrad_state=fx,
    )
    # Extended = FB-3.2 + Θ piece + σ piece; check extended - FB-3.2 ==
    # (Θ + σ) pieces
    delta = extended - fb32_piece
    v = np.asarray(tilted.v_vector(float(eta_sample)), dtype=np.float64)
    Theta = float(bg_table.interp_Theta(float(eta_sample)))
    a_val = float(bg_table.interp_a(float(eta_sample)))
    sigma = proper_shear_at_eta(float(eta_sample), fx, a_val)
    expected_delta = (
        tilted.gamma_sq * (Theta / 3.0) * v
        + tilted.gamma_sq * (sigma @ v)
    )
    np.testing.assert_allclose(delta, expected_delta, rtol=0.0, atol=0.0)


# ──────────────────────────────────────────────────────────────────────
# M-18 : driver byte-identity when FB-3.3 extended accel is β=0
# ──────────────────────────────────────────────────────────────────────


def test_M18_driver_byte_identity_beta_zero_extended(photon, bg_table, eta_sample):
    fx = _axisymmetric_sigma_fixture(np.asarray(bg_table.eta, dtype=np.float64))
    L_max = 3
    rng = np.random.default_rng(33)
    state = zero_hierarchy(L_max)
    for ell in range(L_max + 1):
        state.tensors[ell] = PSTFTensor(
            ell=ell,
            components=rng.normal(size=2 * ell + 1),
        )
    y0 = pack_hierarchy(state)

    # FB-2.4 / FB-3.2 anchor: no tilt kwargs.
    dy_anchor = hierarchy_rhs_photon(
        eta_sample, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
    )

    # FB-3.3 extended path with β=0: must stay byte-identical.
    tilted = TiltedSpeciesBackground(base=photon, beta=0.0)
    structure = get_type("V")
    dy_fb33 = hierarchy_rhs_photon(
        eta_sample, y0,
        L_max=L_max,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        collision=ZeroCollisionOperator(),
        accel_vector=accel_from_tilt(
            tilted, eta_sample, bg_table=bg_table, tetrad_state=fx,
        ),
        vorticity_vector=vorticity_from_tilt(
            tilted, eta_sample, structure=structure,
        ),
    )
    assert np.array_equal(dy_fb33, dy_anchor)
