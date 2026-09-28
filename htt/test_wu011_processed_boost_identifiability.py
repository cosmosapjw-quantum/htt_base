"""RED/GREEN contracts for the WU-011 Task-7B identifiability atlas."""

from __future__ import annotations

import math

import numpy as np
import pytest


pytest.importorskip("healpy", reason="healpy is required by WU-011 Task-7B")
pytestmark = pytest.mark.requires_healpy


def _api():
    try:
        from obsstat import processed_boost_identifiability as api
    except ImportError as exc:
        pytest.fail(f"WU-011 Task-7B API missing: {exc}", pytrace=False)
    return api


@pytest.fixture(scope="module")
def smoke_atlas():
    return _api().build_task7b_atlas(source_revision="0" * 40, profile="SMOKE")


def test_task7b_case_registry_and_terminals_are_frozen() -> None:
    api = _api()
    assert api.CI_CORE_CASE_IDS == (
        "FULL_IDENTITY",
        "BINARY_Z_IDENTITY",
        "APODIZED_Z_NARROW_IDENTITY",
        "APODIZED_Z_REFERENCE_IDENTITY",
        "APODIZED_Z_WIDE_IDENTITY",
        "APODIZED_Z_REFERENCE_MATCHED_GAUSSIAN",
        "APODIZED_Z_REFERENCE_GAUSSIAN",
    )
    assert api.Task7BTerminal.PASS_TASK7B_ATLAS_CANDIDATE_FOUND.value
    assert api.Task7BTerminal.PASS_TASK7B_ATLAS_NO_CANDIDATE.value
    assert api.Task7BTerminal.BLOCKED_BY_EXTENDED_BAND_FAILURE.value


def test_task7b_atlas_has_invariant_sector_diagnostics(smoke_atlas) -> None:
    api = _api()
    assert smoke_atlas.profile == "SMOKE"
    assert tuple(case.case_id for case in smoke_atlas.cases) == api.CI_CORE_CASE_IDS
    assert smoke_atlas.terminal in {
        api.Task7BTerminal.PASS_TASK7B_ATLAS_CANDIDATE_FOUND,
        api.Task7BTerminal.PASS_TASK7B_ATLAS_NO_CANDIDATE,
    }
    assert smoke_atlas.content_id.startswith("sha256:")

    for case in smoke_atlas.cases:
        assert case.jacobian_rank == 48
        assert math.isfinite(case.jacobian_nonzero_condition)
        assert case.jacobian_nonzero_condition >= 1.0
        assert sum(case.source_sector_frobenius_fractions) == pytest.approx(
            1.0, rel=0.0, abs=2.0e-12
        )
        assert sum(case.weak_mode_sector_weights) == pytest.approx(
            1.0, rel=0.0, abs=2.0e-12
        )
        assert 0.0 < case.f_sky_mean <= 1.0
        assert 0.0 < case.f_sky_quadratic <= 1.0
        assert 0.0 < case.f_sky_effective <= 1.0
        assert 0.0 <= case.transition_fraction <= 1.0
        assert case.ell6_neighbor_norm > 0.0
        assert case.ell6_alias_norm >= 0.0
        assert case.tail.cumulative_metric_frobenius >= 0.0
        assert case.tail.cumulative_tail_to_neighbor >= 0.0
        assert 0.0 <= case.tail.projection_fraction_into_registered_image <= 1.0
        assert 0.0 <= case.tail.minimum_principal_angle_degrees <= 90.0
        assert tuple(block.source_ell for block in case.tail.blocks) == (7, 8)
        assert all(block.content_id.startswith("sha256:") for block in case.tail.blocks)


def test_task7b_fullsky_is_a_zero_control_for_extended_source_tail(smoke_atlas) -> None:
    full = smoke_atlas.cases[0]
    cut = next(
        case
        for case in smoke_atlas.cases
        if case.case_id == "APODIZED_Z_REFERENCE_IDENTITY"
    )
    assert full.mask_kind == "FULL"
    assert full.transfer_kind == "IDENTITY"
    assert full.tail.cumulative_metric_frobenius < cut.tail.cumulative_metric_frobenius
    assert full.tail.cumulative_tail_to_neighbor < cut.tail.cumulative_tail_to_neighbor


def test_task7b_candidate_registry_matches_preregistered_floors(smoke_atlas) -> None:
    expected = tuple(
        case.case_id
        for case in smoke_atlas.cases
        if case.mask_kind != "FULL"
        and case.jacobian_rank == 48
        and case.jacobian_nonzero_condition <= 100.0
        and case.ell6_alias_to_neighbor <= 1.0
        and case.tail.cumulative_tail_to_neighbor <= 1.0
    )
    assert smoke_atlas.candidate_case_ids == expected
    if expected:
        assert (
            smoke_atlas.terminal
            == _api().Task7BTerminal.PASS_TASK7B_ATLAS_CANDIDATE_FOUND
        )
    else:
        assert (
            smoke_atlas.terminal
            == _api().Task7BTerminal.PASS_TASK7B_ATLAS_NO_CANDIDATE
        )


def test_task7b_artifact_roundtrip_is_content_bound(smoke_atlas, tmp_path) -> None:
    api = _api()
    target = tmp_path / "task7b"
    bundle = api.write_task7b_artifacts(smoke_atlas, target)
    verified = api.verify_task7b_artifacts(target)
    assert bundle.manifest_sha256 == verified["manifest_sha256"]
    assert verified["source_revision"] == "0" * 40
    assert verified["profile"] == "SMOKE"
    assert verified["terminal"] == smoke_atlas.terminal.value
    assert verified["manifest_entries"] >= 11
    expected = {
        "terminal.json",
        "summary.json",
        "cases.csv",
        "sector_participation.csv",
        "extended_source_leakage.csv",
        "condition_vs_mask.png",
        "alias_and_tail_vs_case.png",
        "weak_mode_sector_weights.png",
        "source_sector_frobenius_fractions.png",
        "extended_leakage_decay.png",
        "SHA256SUMS",
    }
    assert expected.issubset({path.name for path in target.iterdir()})


def test_task7b_wolfram_fullsky_trace_reference_is_sealed() -> None:
    api = _api()
    reference = api.task7b_fullsky_reference()
    np.testing.assert_array_equal(
        reference.trace_by_source_ell,
        np.array([8.0, 27.0, 91.0, 189.0, 125.0, 216.0]),
    )
    assert reference.total_metric_frobenius_square == 656.0
    np.testing.assert_allclose(
        reference.sector_fractions,
        np.array([1.0 / 82.0, 27.0 / 656.0, 91.0 / 656.0,
                  189.0 / 656.0, 125.0 / 656.0, 27.0 / 82.0]),
        rtol=0.0,
        atol=0.0,
    )
    assert reference.nonzero_condition_number == pytest.approx(math.sqrt(63.0 / 8.0))
