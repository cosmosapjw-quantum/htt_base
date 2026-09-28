"""RED/GREEN contracts for the WU-011 Task-7C matched full-sky control."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest


pytest.importorskip("healpy", reason="healpy is required by WU-011 Task-7C-A2")
pytestmark = pytest.mark.requires_healpy


@pytest.fixture(scope="module")
def matched_smoke_pair():
    from obsstat import processed_boost_matched_control as matched
    from obsstat import processed_boost_nuisance_span as span

    source_spec = span.task7c_case_specs("SMOKE")[0]
    source_case = span.build_task7c_case(source_spec)
    control_case = matched.build_matched_fullsky_control(source_spec)
    return matched, span, source_spec, source_case, control_case


def test_matched_control_changes_only_the_masked_estimator(
    matched_smoke_pair,
) -> None:
    _matched, span, source_spec, source_case, control_case = matched_smoke_pair

    assert source_spec.mask_kind == "APODIZED_Z_WIDE"
    assert control_case.source_case_id == source_spec.case_id
    assert control_case.nside == source_spec.nside
    assert control_case.processing_lmax == source_spec.processing_lmax
    assert control_case.transfer_kind == source_spec.transfer_kind
    assert control_case.source_cutoffs == source_spec.source_cutoffs
    assert control_case.mask_kind == "FULL"
    assert control_case.operator_id != source_case.operator_id
    assert control_case.source_block_build_count == max(source_spec.source_cutoffs) - 6

    for cutoff in source_spec.source_cutoffs:
        for direction_id in span.DIRECTION_IDS:
            control = control_case.result(direction_id, cutoff)
            assert control.high_matrix.shape == (
                32,
                span.high_source_dimension(cutoff),
            )
            assert control.high_matrix.flags.writeable is False
            assert control.content_id.startswith("sha256:")


def test_actual_fullsky_replay_floor_is_not_a_resolved_nuisance_image(
    matched_smoke_pair,
) -> None:
    from obsstat import processed_boost_rank_policy as rank_policy

    _matched, _span, source_spec, source_case, control_case = matched_smoke_pair
    direction_id = "X"
    cutoff = max(source_spec.source_cutoffs)
    source = source_case.result(direction_id, cutoff)
    control = control_case.result(direction_id, cutoff)

    result = rank_policy.analyse_control_anchored_nuisance_geometry(
        source.low_matrix,
        control.high_matrix,
        control.high_matrix,
        policy=rank_policy.RankPolicy(control_safety_factor=5.0),
    )

    assert result.rank_status is rank_policy.RankDecisionStatus.RESOLVED
    assert result.high_rank == 0
    assert result.surviving_rank == result.low_rank
    assert result.augmented_rank_increment == result.low_rank
    assert result.rank_identity_holds
    assert result.containment_witness is False
    assert result.surviving_frobenius_fraction == pytest.approx(1.0, abs=2.0e-13)


def test_source_case_uses_the_matched_control_in_the_rank_policy(
    matched_smoke_pair,
) -> None:
    from obsstat import processed_boost_rank_policy as rank_policy

    matched, _span, source_spec, source_case, control_case = matched_smoke_pair
    direction_id = "D111"
    cutoff = max(source_spec.source_cutoffs)
    control = control_case.result(direction_id, cutoff)
    policy = rank_policy.RankPolicy(control_safety_factor=5.0)

    result = matched.analyse_task7c_with_matched_fullsky_control(
        source_case,
        control_case,
        direction_id=direction_id,
        source_cutoff=cutoff,
        policy=policy,
    )

    expected_control_norm = float(np.linalg.svd(control.high_matrix, compute_uv=False)[0])
    assert result.source_case_id == source_case.case_id
    assert result.control_case_id == control_case.case_id
    assert result.direction_id == direction_id
    assert result.source_cutoff == cutoff
    assert result.source_operator_id == source_case.operator_id
    assert result.control_operator_id == control_case.operator_id
    assert result.geometry.high_control_operator_norm == pytest.approx(
        expected_control_norm,
        rel=2.0e-14,
        abs=0.0,
    )
    assert result.geometry.high_threshold >= policy.control_safety_factor * expected_control_norm
    assert result.content_id.startswith("sha256:")

    if result.geometry.rank_status is rank_policy.RankDecisionStatus.RESOLVED:
        assert result.geometry.rank_identity_holds
        assert result.geometry.containment_witness == (
            result.geometry.surviving_rank == 0
            and result.geometry.augmented_rank_increment == 0
        )
    else:
        assert result.geometry.containment_witness is None
        assert result.geometry.rank_identity_holds is None


def test_mismatched_control_metadata_fails_closed(matched_smoke_pair) -> None:
    matched, _span, source_spec, source_case, control_case = matched_smoke_pair
    mismatched = replace(
        control_case,
        processing_lmax=control_case.processing_lmax + 1,
    )

    with pytest.raises(matched.MatchedControlError, match="does not match"):
        matched.analyse_task7c_with_matched_fullsky_control(
            source_case,
            mismatched,
            direction_id="Z",
            source_cutoff=max(source_spec.source_cutoffs),
        )


def test_fullsky_source_is_refused_as_a_matched_control_target() -> None:
    from obsstat import processed_boost_matched_control as matched
    from obsstat import processed_boost_nuisance_span as span

    fullsky_spec = span.task7c_case_specs("SMOKE")[1]
    with pytest.raises(matched.MatchedControlError, match="cut-sky source"):
        matched.build_matched_fullsky_control(fullsky_spec)
