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


@pytest.fixture(scope="module")
def smoke_atlas():
    return _api().build_task7c_atlas(source_revision="0" * 40, profile="SMOKE")


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


def test_task7c_source_block_cache_extends_beyond_task7b_cap() -> None:
    api = _api()
    operator = api.task7c_smoke_operator(processing_lmax=11)
    cache = api.ExtendedSourceBlockCache()
    first = cache.get(operator, source_ell=10)
    second = cache.get(operator, source_ell=10)
    assert first is second
    assert cache.build_count == 1
    assert first.source_ell == 10
    assert first.tensor.shape == (3, 32, 21)
    assert first.tensor.flags.writeable is False
    assert first.metric_frobenius_norm >= 0.0
    assert first.content_id.startswith("sha256:")
    with pytest.raises(api.ProcessedBoostError, match="raised source band"):
        cache.get(operator, source_ell=11)


def _convergence_records(api, *, survivor_rank: int, last_fraction: float, drift: float):
    records = []
    for direction_id in api.DIRECTION_IDS:
        lower_fraction = 0.0 if survivor_rank == 0 else 0.45
        upper_fraction = lower_fraction + drift
        records.append(
            api.Task7CConvergenceRecord(
                direction_id=direction_id,
                lower_cutoff=12,
                upper_cutoff=16,
                lower_high_rank=32,
                upper_high_rank=32,
                lower_surviving_rank=survivor_rank,
                upper_surviving_rank=survivor_rank,
                lower_surviving_fraction=lower_fraction,
                upper_surviving_fraction=upper_fraction,
                upper_last_frobenius_fraction=last_fraction,
                upper_last_operator_fraction=last_fraction,
            )
        )
    return tuple(records)


def test_task7c_terminal_classifier_distinguishes_scientific_terminals() -> None:
    api = _api()
    no_subspace = api.classify_task7c_convergence(
        _convergence_records(api, survivor_rank=0, last_fraction=0.05, drift=0.0)
    )
    assert no_subspace == api.Task7CTerminal.PASS_TASK7C_MODEL_FREE_NO_IDENTIFIED_SUBSPACE

    identified = api.classify_task7c_convergence(
        _convergence_records(api, survivor_rank=3, last_fraction=0.05, drift=0.01)
    )
    assert identified == api.Task7CTerminal.PASS_TASK7C_MODEL_FREE_IDENTIFIED_SUBSPACE

    unconverged = api.classify_task7c_convergence(
        _convergence_records(api, survivor_rank=3, last_fraction=0.20, drift=0.01)
    )
    assert unconverged == api.Task7CTerminal.PASS_TASK7C_SOURCE_BAND_NOT_CONVERGED

    mixed = list(
        _convergence_records(api, survivor_rank=3, last_fraction=0.05, drift=0.01)
    )
    mixed[-1] = api.Task7CConvergenceRecord(
        direction_id=api.DIRECTION_IDS[-1],
        lower_cutoff=12,
        upper_cutoff=16,
        lower_high_rank=32,
        upper_high_rank=32,
        lower_surviving_rank=0,
        upper_surviving_rank=0,
        lower_surviving_fraction=0.0,
        upper_surviving_fraction=0.0,
        upper_last_frobenius_fraction=0.05,
        upper_last_operator_fraction=0.05,
    )
    assert (
        api.classify_task7c_convergence(tuple(mixed))
        == api.Task7CTerminal.BLOCKED_BY_DIRECTIONAL_METRIC_FAILURE
    )


def test_task7c_smoke_atlas_has_cached_directional_geometry(smoke_atlas) -> None:
    api = _api()
    assert smoke_atlas.profile == "SMOKE"
    assert smoke_atlas.source_revision == "0" * 40
    assert tuple(case.case_id for case in smoke_atlas.cases) == api.SMOKE_CASE_IDS
    assert smoke_atlas.terminal in {
        api.Task7CTerminal.PASS_TASK7C_MODEL_FREE_IDENTIFIED_SUBSPACE,
        api.Task7CTerminal.PASS_TASK7C_MODEL_FREE_NO_IDENTIFIED_SUBSPACE,
        api.Task7CTerminal.PASS_TASK7C_SOURCE_BAND_NOT_CONVERGED,
        api.Task7CTerminal.BLOCKED_BY_DIRECTIONAL_METRIC_FAILURE,
    }
    assert smoke_atlas.content_id.startswith("sha256:")
    assert smoke_atlas.source_block_build_count == 5

    primary = smoke_atlas.cases[0]
    assert primary.source_cutoffs == (8, 9)
    assert len(primary.directional_results) == 2 * len(api.DIRECTION_IDS)
    for result in primary.directional_results:
        assert result.low_matrix.shape == (32, 48)
        assert result.high_matrix.shape == (32, (result.source_cutoff + 1) ** 2 - 49)
        assert result.geometry.low_rank <= 32
        assert result.geometry.high_rank <= 32
        assert result.geometry.surviving_rank <= result.geometry.low_rank
        assert 0.0 <= result.last_block_frobenius_fraction <= 1.0
        assert 0.0 <= result.last_block_operator_fraction <= 1.0
        np.testing.assert_allclose(
            result.geometry.nuisance_projector @ result.high_matrix,
            np.zeros_like(result.high_matrix),
            atol=2.0e-8,
        )
        np.testing.assert_allclose(
            result.geometry.surviving_low_matrix,
            result.geometry.nuisance_projector @ result.low_matrix,
            atol=2.0e-13,
        )
        if result.geometry.surviving_frobenius_fraction > 1.0e-12:
            assert sum(result.surviving_sector_fractions) == pytest.approx(
                1.0, abs=2.0e-11
            )
        else:
            assert sum(result.surviving_sector_fractions) == pytest.approx(
                0.0, abs=2.0e-11
            )


def test_task7c_artifact_roundtrip_is_content_bound(smoke_atlas, tmp_path) -> None:
    api = _api()
    target = tmp_path / "task7c"
    bundle = api.write_task7c_artifacts(smoke_atlas, target)
    verified = api.verify_task7c_artifacts(target)
    assert bundle.manifest_sha256 == verified["manifest_sha256"]
    assert verified["source_revision"] == "0" * 40
    assert verified["profile"] == "SMOKE"
    assert verified["terminal"] == smoke_atlas.terminal.value
    assert verified["manifest_entries"] >= 11
    expected = {
        "terminal.json",
        "summary.json",
        "directional_nuisance_span.csv",
        "source_block_norms.csv",
        "cutoff_convergence.csv",
        "matrices.npz",
        "survivor_rank_vs_cutoff.png",
        "surviving_fraction_vs_cutoff.png",
        "principal_angle_vs_cutoff.png",
        "source_block_decay.png",
        "resolution_comparison.png",
        "SHA256SUMS",
    }
    assert expected.issubset({path.name for path in target.iterdir()})
