"""PR-326 OBSSTAT direction-indexed dipole/STF estimator tests."""
from __future__ import annotations

import importlib
import math

import numpy as np
import pytest


def _modules():
    try:
        common = importlib.import_module("common.mes_directional_state")
        obsstat = importlib.import_module("htt.obsstat.mes_directional_moments")
    except ModuleNotFoundError:
        pytest.fail("PR-326 directional moment bridge is not implemented")
    return common, obsstat


def _lebedev_14() -> tuple[np.ndarray, np.ndarray]:
    axes = np.vstack((np.eye(3), -np.eye(3)))
    corners = np.asarray(
        [
            (sx, sy, sz)
            for sx in (-1.0, 1.0)
            for sy in (-1.0, 1.0)
            for sz in (-1.0, 1.0)
        ],
        dtype=float,
    ) / math.sqrt(3.0)
    directions = np.vstack((axes, corners))
    weights = np.concatenate(
        (
            np.full(6, 4.0 * math.pi / 15.0),
            np.full(8, 3.0 * math.pi / 10.0),
        )
    )
    return directions, weights


def _field(directions: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    vector = np.asarray((0.3, -0.4, 0.5))
    stf = np.asarray(
        ((0.2, 0.05, -0.03), (0.05, -0.1, 0.04), (-0.03, 0.04, -0.1))
    )
    values = 0.7 + directions @ vector + np.einsum(
        "ni,ij,nj->n", directions, stf, directions
    )
    return values, vector, stf


def _kwargs(common, directions, weights, values, *, parity=None):
    return {
        "directions": directions,
        "values": values,
        "weights": weights,
        "field_parity": parity or common.DirectionalFieldParity.SCALAR_EVEN,
        "field_quantity": "dimensionless directional morphology fixture",
        "field_units": "dimensionless",
        "field_bandlimit": 2,
        "direction_frame": "registered observer Cartesian frame",
        "direction_convention": common.DirectionConvention.RIGHT_HANDED_ACTIVE_O3,
        "mask_identity": "sha256:" + "1" * 64,
        "transfer_identity": "sha256:" + "2" * 64,
        "field_identity": "sha256:" + "3" * 64,
        "covariance_identity": "sha256:" + "4" * 64,
    }


def test_registered_full_sky_coefficients_recover_analytic_dipole_and_stf() -> None:
    common, obsstat = _modules()
    directions, weights = _lebedev_14()
    values, vector, stf = _field(directions)

    result = obsstat.estimate_full_sky_directional_moments(
        **_kwargs(common, directions, weights, values)
    )

    assert result.estimator_kind is common.DirectionalEstimatorKind.FULL_SKY_QUADRATURE
    assert result.dipole == pytest.approx(vector, abs=2e-15)
    assert np.asarray(result.stf2) == pytest.approx(stf, abs=2e-15)
    assert result.monopole == pytest.approx(0.7, abs=2e-15)
    assert result.vector_representation is common.VectorO3Representation.POLAR
    assert result.tensor_representation is common.TensorO3Representation.EVEN_STF2
    assert result.directional_semantics_status == (
        "DECLARED_UNVERIFIED_BANDLIMIT_AND_PARITY"
    )
    assert result.design_condition_number <= result.max_design_condition_number

    changed = weights.copy()
    changed[0] *= 1.01
    with pytest.raises(common.DirectionalBridgeError, match="full-sky quadrature"):
        obsstat.estimate_full_sky_directional_moments(
            **_kwargs(common, directions, changed, values)
        )


def test_masked_or_discrete_joint_fit_recovers_one_bound_design() -> None:
    common, obsstat = _modules()
    directions, weights = _lebedev_14()
    values, vector, stf = _field(directions)
    mask = np.ones(len(values), dtype=bool)
    mask[[1, 8, 11]] = False

    result = obsstat.estimate_joint_fit_directional_moments(
        **_kwargs(common, directions, weights, values),
        support_mask=mask,
    )

    assert result.estimator_kind is (
        common.DirectionalEstimatorKind.WEIGHTED_JOINT_HARMONIC_FIT
    )
    assert result.design_rank == 9
    assert result.design_condition_number <= result.max_design_condition_number
    assert result.weighted_residual_norm < 1e-12
    assert result.dipole == pytest.approx(vector, abs=2e-14)
    assert np.asarray(result.stf2) == pytest.approx(stf, abs=2e-14)
    assert result.support_size == int(mask.sum())
    assert result.estimator_identity != result.field_identity

    rank_deficient = np.zeros(len(values), dtype=bool)
    rank_deficient[:8] = True
    with pytest.raises(common.DirectionalBridgeError, match="BLOCKED_DIRECTIONAL_SUPPORT"):
        obsstat.estimate_joint_fit_directional_moments(
            **_kwargs(common, directions, weights, values),
            support_mask=rank_deficient,
        )


def test_o3_rotation_reflection_and_intrinsic_parity_are_explicit() -> None:
    common, obsstat = _modules()
    directions, weights = _lebedev_14()
    values, _, _ = _field(directions)
    baseline = obsstat.estimate_full_sky_directional_moments(
        **_kwargs(common, directions, weights, values)
    )
    rotation = np.asarray(
        ((0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    )
    reflection = np.diag((-1.0, 1.0, 1.0))

    for transform in (rotation, reflection):
        transformed = obsstat.estimate_full_sky_directional_moments(
            **_kwargs(common, directions @ transform.T, weights, values)
        )
        assert transformed.dipole == pytest.approx(
            transform @ np.asarray(baseline.dipole), abs=3e-15
        )
        assert np.asarray(transformed.stf2) == pytest.approx(
            transform @ np.asarray(baseline.stf2) @ transform.T, abs=3e-15
        )

    odd = obsstat.estimate_full_sky_directional_moments(
        **_kwargs(
            common,
            directions @ reflection.T,
            weights,
            -values,
            parity=common.DirectionalFieldParity.PSEUDOSCALAR_ODD,
        )
    )
    assert odd.vector_representation is common.VectorO3Representation.AXIAL
    assert odd.tensor_representation is common.TensorO3Representation.ODD_STF2
    assert odd.dipole == pytest.approx(
        np.linalg.det(reflection) * reflection @ np.asarray(baseline.dipole),
        abs=3e-15,
    )
    assert np.asarray(odd.stf2) == pytest.approx(
        np.linalg.det(reflection)
        * reflection
        @ np.asarray(baseline.stf2)
        @ reflection.T,
        abs=3e-15,
    )


def test_antipodal_psd_trace_one_realizability_is_scoped_and_fail_closed() -> None:
    common, obsstat = _modules()
    directions = np.vstack((np.eye(3), -np.eye(3)))
    probabilities = np.asarray((0.1, 0.15, 0.25, 0.1, 0.15, 0.25))
    certificate = obsstat.certify_antipodal_measure_moments(
        directions=directions,
        probability_weights=probabilities,
        support_identity="sha256:" + "5" * 64,
    )

    assert certificate.status == "PSD_TRACE_ONE_ZERO_MEAN_VERIFIED"
    assert certificate.mean == pytest.approx((0.0, 0.0, 0.0), abs=1e-15)
    assert np.asarray(certificate.second_moment) == pytest.approx(
        np.diag((0.2, 0.3, 0.5)), abs=1e-15
    )
    assert certificate.higher_moment_claim is False
    assert certificate.dynamical_attainability_claim is False

    with pytest.raises(common.DirectionalBridgeError, match="BLOCKED_MOMENT_REALIZABILITY"):
        common.certify_spherical_second_moment(
            mean=(0.0, 0.0, 0.0),
            second_moment=((1.1, 0.0, 0.0), (0.0, -0.1, 0.0), (0.0, 0.0, 0.0)),
            support_identity="sha256:" + "5" * 64,
        )


def test_directional_estimators_refuse_uncontrolled_higher_l_leakage() -> None:
    common, obsstat = _modules()
    directions, weights = _lebedev_14()
    values, _, _ = _field(directions)
    kwargs = _kwargs(common, directions, weights, values)
    kwargs["field_bandlimit"] = 3

    with pytest.raises(common.DirectionalBridgeError, match="DIRECTIONAL_LEAKAGE"):
        obsstat.estimate_full_sky_directional_moments(**kwargs)
    with pytest.raises(common.DirectionalBridgeError, match="DIRECTIONAL_LEAKAGE"):
        obsstat.estimate_joint_fit_directional_moments(
            **kwargs,
            support_mask=np.ones(len(values), dtype=bool),
        )


def test_declared_bandlimit_contradictions_fail_and_alias_risk_stays_unverified() -> None:
    common, obsstat = _modules()
    directions, weights = _lebedev_14()
    values, _, _ = _field(directions)

    for bandlimit in (0, 1):
        kwargs = _kwargs(common, directions, weights, values)
        kwargs["field_bandlimit"] = bandlimit
        with pytest.raises(common.DirectionalBridgeError, match="DIRECTIONAL_LEAKAGE"):
            obsstat.estimate_full_sky_directional_moments(**kwargs)

    z = directions[:, 2]
    ell4_values = (35.0 * z**4 - 30.0 * z**2 + 3.0) / 8.0
    aliased = obsstat.estimate_full_sky_directional_moments(
        **_kwargs(common, directions, weights, ell4_values)
    )
    assert np.linalg.norm(aliased.stf2) > 0.5
    assert aliased.directional_semantics_status == (
        "DECLARED_UNVERIFIED_BANDLIMIT_AND_PARITY"
    )


def test_frame_convention_and_declared_parity_are_identity_bound() -> None:
    common, obsstat = _modules()
    directions, weights = _lebedev_14()
    values, _, _ = _field(directions)
    baseline = obsstat.estimate_full_sky_directional_moments(
        **_kwargs(common, directions, weights, values)
    )

    changed_kwargs = _kwargs(common, directions, weights, values)
    changed_kwargs["direction_frame"] = "different registered Cartesian frame"
    changed = obsstat.estimate_full_sky_directional_moments(**changed_kwargs)
    assert changed.estimator_identity != baseline.estimator_identity

    odd = obsstat.estimate_full_sky_directional_moments(
        **_kwargs(
            common,
            directions,
            weights,
            values,
            parity=common.DirectionalFieldParity.PSEUDOSCALAR_ODD,
        )
    )
    assert odd.estimator_identity != baseline.estimator_identity
    assert odd.directional_semantics_status == (
        "DECLARED_UNVERIFIED_BANDLIMIT_AND_PARITY"
    )

    bad_kwargs = _kwargs(common, directions, weights, values)
    bad_kwargs["direction_convention"] = "LEFT_HANDED_PASSIVE"
    with pytest.raises(common.DirectionalBridgeError, match="direction_convention"):
        obsstat.estimate_full_sky_directional_moments(**bad_kwargs)


def test_near_singular_rank_nine_joint_design_is_refused() -> None:
    common, obsstat = _modules()
    rng = np.random.default_rng(326)
    xy = rng.normal(scale=1.0e-3, size=(20, 2))
    directions = np.column_stack((xy, np.ones(20)))
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    values = np.full(20, 0.7) + rng.normal(scale=1.0e-10, size=20)
    weights = np.ones(20)

    with pytest.raises(common.DirectionalBridgeError, match="ill-conditioned"):
        obsstat.estimate_joint_fit_directional_moments(
            **_kwargs(common, directions, weights, values),
            support_mask=np.ones(20, dtype=bool),
        )
