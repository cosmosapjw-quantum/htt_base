"""RED/GREEN contracts for the WU-011 Task-7C nuisance-span atlas."""

from __future__ import annotations

import math

import numpy as np
import pytest


pytest.importorskip("healpy", reason="healpy is required by WU-011 Task-7C")
pytestmark = pytest.mark.requires_healpy


def _api():
    try:
        from obsstat import processed_boost_nuisance_span as api
    except ImportError as exc:
        pytest.fail(f"WU-011 Task-7C API missing: {exc}", pytrace=False)
    return api


def test_task7c_registries_and_terminals_are_frozen() -> None:
    api = _api()
    assert api.DIRECTION_IDS == (
        "X",
        "Y",
        "Z",
        "D111",
        "D1M11",
        "D11M1",
    )
    assert api.CORE_SOURCE_CUTOFFS == (9, 12, 16)
    assert api.Task7CTerminal.PASS_TASK7C_MODEL_FREE_IDENTIFIED_SUBSPACE.value
    assert api.Task7CTerminal.PASS_TASK7C_MODEL_FREE_NO_IDENTIFIED_SUBSPACE.value
    assert api.Task7CTerminal.PASS_TASK7C_SOURCE_BAND_NOT_CONVERGED.value
    assert api.Task7CTerminal.BLOCKED_BY_DIRECTIONAL_METRIC_FAILURE.value
    assert api.Task7CTerminal.BLOCKED_BY_CUTOFF_CONSTRUCTION.value
    assert api.Task7CTerminal.BLOCKED_BY_ARTIFACT_INTEGRITY.value


def test_task7c_direction_registry_is_unit_and_immutable() -> None:
    api = _api()
    registry = api.direction_registry()
    assert tuple(registry) == api.DIRECTION_IDS
    for direction_id in api.DIRECTION_IDS:
        vector = registry[direction_id]
        assert vector.shape == (3,)
        assert np.linalg.norm(vector) == pytest.approx(1.0, rel=0.0, abs=2.0e-15)
        assert vector.flags.writeable is False


def test_directional_contraction_and_metric_whitening_are_exactly_ordered() -> None:
    api = _api()
    tensor = np.arange(36, dtype=np.float64).reshape(3, 4, 3) / 17.0
    direction = api.direction_registry()["D1M11"]
    contracted = api.contract_directional_tensor(tensor, direction)
    np.testing.assert_allclose(
        contracted,
        np.einsum("i,ioj->oj", direction, tensor),
        rtol=0.0,
        atol=0.0,
    )
    source_metric = np.array([1.0, 2.0, 5.0])
    output_metric = np.array([1.0, 2.0, 2.0, 4.0])
    whitened = api.metric_whiten_directional_matrix(
        contracted,
        source_metric_diagonal=source_metric,
        output_metric_diagonal=output_metric,
    )
    expected = (
        np.sqrt(output_metric)[:, None]
        * contracted
        / np.sqrt(source_metric)[None, :]
    )
    np.testing.assert_allclose(whitened, expected, rtol=0.0, atol=0.0)
    assert contracted.flags.writeable is False
    assert whitened.flags.writeable is False


def test_nuisance_projection_recovers_orthogonal_and_full_span_limits() -> None:
    api = _api()
    low = np.array(
        [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0], [0.0, 0.0]]
    )
    orthogonal_high = np.array(
        [[0.0, 0.0], [0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]
    )
    orthogonal = api.analyse_whitened_nuisance_geometry(
        low,
        orthogonal_high,
        direction_id="X",
        source_cutoff=9,
    )
    assert orthogonal.low_rank == 2
    assert orthogonal.high_rank == 2
    assert orthogonal.surviving_rank == 2
    assert orthogonal.surviving_frobenius_fraction == pytest.approx(1.0)
    assert orthogonal.minimum_principal_angle_degrees == pytest.approx(90.0)
    assert orthogonal.maximum_principal_angle_degrees == pytest.approx(90.0)
    np.testing.assert_allclose(orthogonal.surviving_low_matrix, low)

    full = api.analyse_whitened_nuisance_geometry(
        low,
        np.eye(4),
        direction_id="X",
        source_cutoff=9,
    )
    assert full.low_rank == 2
    assert full.high_rank == 4
    assert full.surviving_rank == 0
    assert full.surviving_frobenius_fraction == pytest.approx(0.0, abs=1.0e-14)
    assert full.minimum_principal_angle_degrees == pytest.approx(0.0, abs=1.0e-12)
    assert full.maximum_principal_angle_degrees == pytest.approx(0.0, abs=1.0e-12)
    np.testing.assert_allclose(full.surviving_low_matrix, np.zeros_like(low), atol=1.0e-14)


def test_metric_reparameterization_preserves_image_geometry() -> None:
    api = _api()
    low_physical = np.array(
        [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [0.0, 1.0]]
    )
    high_physical = np.array(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 1.0, 1.0]]
    )
    output_metric = np.array([1.0, 2.0, 2.0, 4.0])
    low_metric = np.array([1.0, 2.0])
    high_metric = np.array([1.0, 2.0, 2.0])

    low_raw = (
        low_physical
        * np.sqrt(low_metric)[None, :]
        / np.sqrt(output_metric)[:, None]
    )
    high_raw = (
        high_physical
        * np.sqrt(high_metric)[None, :]
        / np.sqrt(output_metric)[:, None]
    )
    low_whitened = api.metric_whiten_directional_matrix(
        low_raw,
        source_metric_diagonal=low_metric,
        output_metric_diagonal=output_metric,
    )
    high_whitened = api.metric_whiten_directional_matrix(
        high_raw,
        source_metric_diagonal=high_metric,
        output_metric_diagonal=output_metric,
    )

    low_scale = np.array([2.0, 3.0])
    high_scale = np.array([5.0, 7.0, 11.0])
    low_whitened_reparameterized = api.metric_whiten_directional_matrix(
        low_raw * low_scale[None, :],
        source_metric_diagonal=low_metric * low_scale**2,
        output_metric_diagonal=output_metric,
    )
    high_whitened_reparameterized = api.metric_whiten_directional_matrix(
        high_raw * high_scale[None, :],
        source_metric_diagonal=high_metric * high_scale**2,
        output_metric_diagonal=output_metric,
    )
    np.testing.assert_allclose(
        low_whitened_reparameterized, low_whitened, rtol=0.0, atol=2.0e-15
    )
    np.testing.assert_allclose(
        high_whitened_reparameterized, high_whitened, rtol=0.0, atol=2.0e-15
    )

    reference = api.analyse_whitened_nuisance_geometry(
        low_whitened,
        high_whitened,
        direction_id="D111",
        source_cutoff=12,
    )
    transformed = api.analyse_whitened_nuisance_geometry(
        low_whitened_reparameterized,
        high_whitened_reparameterized,
        direction_id="D111",
        source_cutoff=12,
    )
    assert transformed.low_rank == reference.low_rank
    assert transformed.high_rank == reference.high_rank
    assert transformed.surviving_rank == reference.surviving_rank
    assert transformed.surviving_frobenius_fraction == pytest.approx(
        reference.surviving_frobenius_fraction, abs=2.0e-14
    )
    assert transformed.minimum_principal_angle_degrees == pytest.approx(
        reference.minimum_principal_angle_degrees, abs=2.0e-12
    )
    assert transformed.maximum_principal_angle_degrees == pytest.approx(
        reference.maximum_principal_angle_degrees, abs=2.0e-12
    )


def test_rank_threshold_shell_is_refused() -> None:
    api = _api()
    low = np.eye(3)
    high = np.diag([1.0, api.RANK_RELATIVE_THRESHOLD, 0.0])
    with pytest.raises(api.ProcessedBoostError, match="threshold shell"):
        api.analyse_whitened_nuisance_geometry(
            low,
            high,
            direction_id="Z",
            source_cutoff=9,
        )
