"""RED/GREEN contracts for the WU-011 Task-7C control-floor rank policy."""

from __future__ import annotations

import numpy as np
import pytest


def _api():
    try:
        from obsstat import processed_boost_rank_policy as api
    except ImportError as exc:
        pytest.fail(
            f"WU-011 Task-7C rank-policy API missing: {exc}",
            pytrace=False,
        )
    return api


def _low_identity(output_dimension: int = 4) -> np.ndarray:
    return np.concatenate(
        (
            np.eye(output_dimension),
            np.zeros((output_dimension, 2)),
        ),
        axis=1,
    )


def test_high_source_dimension_and_registered_short_circuit_counts() -> None:
    api = _api()
    assert api.high_source_dimension(8) == 32
    assert api.high_source_dimension(9) == 51
    assert api.high_source_dimension(12) == 120
    assert api.high_source_dimension(16) == 240
    assert api.high_source_dimension(20) == 392
    with pytest.raises(api.RankPolicyError, match="cutoff"):
        api.high_source_dimension(6)


def test_relative_only_false_no_survivor_is_killed_by_control_floor() -> None:
    api = _api()
    low = _low_identity()
    numerical_floor = 1.0e-6 * np.eye(4)
    result = api.analyse_control_anchored_nuisance_geometry(
        low,
        numerical_floor,
        numerical_floor,
        policy=api.RankPolicy(control_safety_factor=5.0),
    )
    assert result.rank_status is api.RankDecisionStatus.RESOLVED
    assert result.high_rank == 0
    assert result.surviving_rank == 4
    assert result.augmented_rank_increment == 4
    assert result.rank_identity_holds
    assert result.containment_witness is False
    assert result.surviving_frobenius_fraction == pytest.approx(1.0)


def test_resolved_full_output_nuisance_is_a_containment_witness() -> None:
    api = _api()
    low = _low_identity()
    high = 0.2 * np.eye(4)
    control = 1.0e-6 * np.eye(4)
    result = api.analyse_control_anchored_nuisance_geometry(
        low,
        high,
        control,
        policy=api.RankPolicy(control_safety_factor=5.0),
    )
    assert result.rank_status is api.RankDecisionStatus.RESOLVED
    assert result.high_rank == 4
    assert result.surviving_rank == 0
    assert result.augmented_rank_increment == 0
    assert result.rank_identity_holds
    assert result.containment_witness is True
    assert result.surviving_frobenius_fraction <= 1.0e-14


def test_partial_nuisance_obeys_augmented_rank_identity() -> None:
    api = _api()
    low = np.concatenate((np.eye(5), np.zeros((5, 2))), axis=1)
    high = np.eye(5)[:, :3]
    control = np.zeros_like(high)
    result = api.analyse_control_anchored_nuisance_geometry(
        low,
        high,
        control,
    )
    assert result.rank_status is api.RankDecisionStatus.RESOLVED
    assert result.low_rank == 5
    assert result.high_rank == 3
    assert result.surviving_rank == 2
    assert result.augmented_rank_increment == 2
    assert result.rank_identity_holds
    assert result.containment_witness is False


def test_threshold_ambiguity_fails_closed() -> None:
    api = _api()
    low = _low_identity()
    control = 1.0e-6 * np.eye(4)
    # With s_ctrl=5, sigma=5e-6 lies exactly at the control threshold.
    high = 5.0e-6 * np.eye(4)
    result = api.analyse_control_anchored_nuisance_geometry(
        low,
        high,
        control,
        policy=api.RankPolicy(
            control_safety_factor=5.0,
            ambiguity_factor=2.0,
        ),
    )
    assert result.rank_status is api.RankDecisionStatus.AMBIGUOUS
    assert result.containment_witness is None
    assert result.rank_identity_holds is None


def test_image_geometry_is_invariant_under_source_reparameterization() -> None:
    api = _api()
    rng = np.random.default_rng(20260902)
    low = rng.normal(size=(8, 11))
    high = rng.normal(size=(8, 5))
    control = np.zeros_like(high)

    low_change = np.diag(np.geomspace(0.8, 1.2, low.shape[1]))
    high_change = np.diag(np.geomspace(0.8, 1.2, high.shape[1]))

    base = api.analyse_control_anchored_nuisance_geometry(
        low,
        high,
        control,
    )
    transformed = api.analyse_control_anchored_nuisance_geometry(
        low @ low_change,
        high @ high_change,
        control @ high_change,
    )

    assert base.rank_status is api.RankDecisionStatus.RESOLVED
    assert transformed.rank_status is api.RankDecisionStatus.RESOLVED
    assert base.high_rank == transformed.high_rank
    assert base.surviving_rank == transformed.surviving_rank
    assert base.augmented_rank_increment == transformed.augmented_rank_increment
    assert base.containment_witness == transformed.containment_witness


def test_matched_control_bridge_preserves_provenance_and_rank_identity() -> None:
    try:
        from obsstat import processed_boost_matched_control as matched
    except ImportError as exc:
        pytest.fail(
            f"WU-011 Task-7C matched-control bridge missing: {exc}",
            pytrace=False,
        )

    low = _low_identity()
    high = 0.2 * np.eye(4)
    control = 1.0e-6 * np.eye(4)
    result = matched.analyse_matched_control_matrices(
        low,
        high,
        control,
        source_case_id="CUTSKY_TEST",
        control_case_id="FULLSKY_MATCHED_TEST",
        direction_id="D111",
        source_cutoff=9,
        source_operator_id="sha256:" + "1" * 64,
        control_operator_id="sha256:" + "2" * 64,
    )

    assert result.source_case_id == "CUTSKY_TEST"
    assert result.control_case_id == "FULLSKY_MATCHED_TEST"
    assert result.direction_id == "D111"
    assert result.source_cutoff == 9
    assert result.source_operator_id == "sha256:" + "1" * 64
    assert result.control_operator_id == "sha256:" + "2" * 64
    assert result.geometry.rank_identity_holds
    assert result.geometry.containment_witness is True
    assert result.content_id.startswith("sha256:")


def _adjudication_rows(*, ambiguous: bool, containment: bool) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for factor in (2.0, 5.0, 10.0):
        for direction in ("X", "Z"):
            is_ambiguous = ambiguous and factor == 5.0 and direction == "X"
            rows.append(
                {
                    "direction_id": direction,
                    "source_cutoff": 9,
                    "control_safety_factor": factor,
                    "rank_status": "AMBIGUOUS" if is_ambiguous else "RESOLVED",
                    "high_rank": 3,
                    "surviving_rank": "" if is_ambiguous else (0 if containment else 1),
                    "augmented_rank_increment": "" if is_ambiguous else (0 if containment else 1),
                    "rank_identity_holds": "" if is_ambiguous else True,
                    "containment_witness": "" if is_ambiguous else containment,
                }
            )
    return rows


def test_matched_control_adjudication_fails_closed_on_ambiguity() -> None:
    try:
        from obsstat import processed_boost_matched_control_adjudication as audit
    except ImportError as exc:
        pytest.fail(
            f"WU-011 Task-7C matched-control adjudicator missing: {exc}",
            pytrace=False,
        )

    result = audit.adjudicate_rank_records(
        _adjudication_rows(ambiguous=True, containment=True),
        nominal_control_factor=5.0,
    )
    assert result.terminal is audit.MatchedControlAdjudicationTerminal.RANK_UNRESOLVED
    assert result.nominal_ambiguous_count == 1
    assert result.sensitivity_stable is False
    assert result.scientific_terminal_authorized is False


def test_matched_control_adjudication_separates_survivor_and_candidate() -> None:
    from obsstat import processed_boost_matched_control_adjudication as audit

    survivor = audit.adjudicate_rank_records(
        _adjudication_rows(ambiguous=False, containment=False),
        nominal_control_factor=5.0,
    )
    assert survivor.terminal is audit.MatchedControlAdjudicationTerminal.SURVIVOR_PRESENT
    assert survivor.sensitivity_stable is True
    assert survivor.nominal_survivor_count == 2
    assert survivor.scientific_terminal_authorized is False

    candidate = audit.adjudicate_rank_records(
        _adjudication_rows(ambiguous=False, containment=True),
        nominal_control_factor=5.0,
    )
    assert candidate.terminal is audit.MatchedControlAdjudicationTerminal.CONTAINMENT_CANDIDATE
    assert candidate.sensitivity_stable is True
    assert candidate.nominal_containment_count == 2
    assert candidate.scientific_terminal_authorized is False
