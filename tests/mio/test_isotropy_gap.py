from __future__ import annotations

import dataclasses
import json
import math

import pytest

from common.transfer_registry import TransferFunctionSpec, TransferValidRange
from mio.formalism.budget_spec import BudgetPolicy, BudgetSpec, BudgetUse
from mio.formalism.departure_bundle import build_departure_bundle
from mio.formalism.filling_fraction import build_certified_filling_fraction
from mio.formalism.isotropy_gap import (
    DepthBinFRecord,
    DepthBinMetadata,
    IsotropyGap,
    build_depth_bin_f_record,
    build_isotropy_gap,
)

_GENERATING_COMMAND = "pytest tests/mio/test_isotropy_gap.py"
_WORKTREE_STATE = "test-fixture"
_FLOOR = 1.0e-3


def _external_transfer_metadata(
    transfer_id: str,
    **overrides: object,
) -> dict[str, object]:
    spec = TransferFunctionSpec(
        transfer_id=transfer_id,
        source="AniCLASS_external",
        family="BianchiI",
        valid_range=TransferValidRange(
            k_min=1.0e-5,
            k_max=0.2,
            ell_min=2,
            ell_max=30,
        ),
        observable_kind="scalar_summary",
        normalization="unit_primordial_curvature",
        calibration_status="external_calibrated",
        caveats=("external-transfer path", "transfer-conditional result"),
        source_ref=f"aniclass:{transfer_id}",
    )
    metadata = spec.to_metadata()
    metadata.update(overrides)
    return metadata


def _bundle(x_c: float, **overrides: object):
    values: dict[str, object] = {
        "components": {
            "Sigma2_std": x_c,
            "W2_std": 0.0,
            "Omega_tilt": 0.0,
            "Omega_k_aniso": 0.0,
        },
        "comparator": "CMB_FLRW_reference",
        "frame": "normal_frame",
        "units": "dimensionless_hubble_normalized",
        "config_hash": f"cfg-x-{x_c}",
        "input_hashes": (f"x-input-{x_c}",),
    }
    values.update(overrides)
    return build_departure_bundle(**values)


def _budget(denominator_value: float, **overrides: object) -> BudgetSpec:
    values: dict[str, object] = {
        "policy": BudgetPolicy.MES_LINEAR,
        "denominator_value": denominator_value,
        "denominator_label": "linear MES depth-gap reference denominator",
        "comparator": "CMB_FLRW_reference",
        "frame": "normal_frame",
        "units": "dimensionless_hubble_normalized",
        "config_hash": f"cfg-budget-{denominator_value}",
        "input_hashes": (f"budget-input-{denominator_value}",),
        "assumptions": ("linear MES denominator for G_F depth diagnostics",),
        "admissible_uses": (
            BudgetUse.DENOMINATOR_SENSITIVITY,
            BudgetUse.SIGNED_PROJECTION_NORMALIZATION,
            BudgetUse.CERTIFIED_FILLING_CEILING,
            BudgetUse.EXCEEDANCE_THRESHOLD,
            BudgetUse.DEPTH_GAP_REFERENCE,
        ),
        "is_admissible_ceiling": True,
    }
    values.update(overrides)
    return BudgetSpec(**values)


def _f_score(
    x_c: float,
    denominator: float,
    *,
    transfer_id: str | None = None,
    transfer_metadata: dict[str, object] | None = None,
    budget: BudgetSpec | None = None,
):
    bundle_kwargs: dict[str, object] = {}
    if transfer_id is not None:
        bundle_kwargs.update(
            transfer_source="AniCLASS_external",
            transfer_spec_id=transfer_id,
            transfer_metadata=(
                _external_transfer_metadata(transfer_id)
                if transfer_metadata is None
                else transfer_metadata
            ),
        )
    return build_certified_filling_fraction(
        (_bundle(x_c, **bundle_kwargs),),
        (budget if budget is not None else _budget(denominator),),
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )


def _f_score_samples(
    x_c_samples: tuple[float, ...],
    denominator_samples: tuple[float, ...],
):
    return build_certified_filling_fraction(
        tuple(_bundle(x_c) for x_c in x_c_samples),
        tuple(_budget(denominator) for denominator in denominator_samples),
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )


def _bin(
    bin_id: str,
    start: float,
    stop: float,
    *,
    covariance_status: str = "mock_covariance",
    null_mock_status: str = "mock_calibrated",
    denominator_evolution_status: str = "per_bin_denominator_recorded",
    covariance_metadata: dict[str, object] | None = None,
    null_metadata: dict[str, object] | None = None,
    **overrides: object,
) -> DepthBinMetadata:
    values: dict[str, object] = {
        "bin_id": bin_id,
        "depth_min": start,
        "depth_max": stop,
        "depth_unit": "redshift",
        "depth_convention": "z_cmb_bin_edges_left_closed_right_open",
        "selection_rule": "pre-registered redshift bin assignment",
        "selection_hash": f"sha256:selection-{bin_id}",
        "bin_assignment_hash": f"sha256:assignment-{bin_id}",
        "sky_support_status": "mask_weighted_directional_support",
        "mask_status": "masked_with_hash",
        "covariance_status": covariance_status,
        "covariance_metadata": {
            "covariance_hash": f"sha256:cov-{bin_id}",
            "shape": [2, 2],
            "estimator": "mock_bank",
            "off_diagonal_policy": "included",
            "calibration_status": "matched_calibrated",
        }
        if covariance_metadata is None
        else covariance_metadata,
        "null_mock_status": null_mock_status,
        "null_metadata": {
            "mock_bank_hash": f"sha256:null-{bin_id}",
            "calibration_status": "matched_calibrated",
        }
        if null_metadata is None
        else null_metadata,
        "denominator_evolution_status": denominator_evolution_status,
        "sample_count": 8,
    }
    values.update(overrides)
    return DepthBinMetadata(**values)


def _record(bin_id: str, start: float, stop: float, x_c: float, denominator: float):
    return build_depth_bin_f_record(
        _f_score(x_c, denominator),
        depth_bin=_bin(bin_id, start, stop),
    )


def test_gf_payload_emits_depth_metadata_and_diagnostic_claim_tier() -> None:
    gap = build_isotropy_gap(
        (
            _record("near", 0.0, 0.5, 0.2, 1.0),
            _record("far", 0.5, 1.0, 0.6, 1.0),
        ),
        reference_bin_id="near",
        comparison_bin_id="far",
        floor_value=_FLOOR,
        floor_label="pre_registered_positive_F_floor",
        floor_reason="stabilize log_g_F without altering raw F values",
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
        artifact_metadata={"report_role": "G_F depth diagnostic"},
    )

    payload = gap.as_payload()
    payload_text = json.dumps(payload, sort_keys=True).lower()

    assert dataclasses.is_dataclass(gap)
    assert payload["owner"] == "MIO"
    assert payload["implementation_scope"] == "mio"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["score_label"] == "G_F"
    assert payload["score_kind"] == "isotropy_depth_gap"
    assert payload["gap_formula"] == (
        "log_g_F=log(max(F_comparison,floor))-"
        "log(max(F_reference,floor)); G_F=exp(log_g_F)"
    )
    assert payload["G_F"] == pytest.approx(3.0)
    assert payload["log_g_F"] == pytest.approx(math.log(3.0))
    assert payload["raw_F_by_bin"] == {"near": pytest.approx(0.2), "far": pytest.approx(0.6)}
    assert payload["floor_applied_by_bin"] == {"near": False, "far": False}
    assert payload["depth_bin_count"] == 2
    assert payload["depth_bins"][0]["bin_id"] == "near"
    assert payload["depth_bins"][1]["bin_id"] == "far"
    assert payload["covariance_status"] == "mock_covariance"
    assert payload["null_mock_status"] == "mock_calibrated"
    assert payload["transfer_source"] == "none"
    assert payload["generating_command"] == _GENERATING_COMMAND
    assert payload["worktree_state"] == _WORKTREE_STATE
    for forbidden in (
        "posterior",
        "evidence",
        "family_id",
        "geometry",
        "native_validated",
    ):
        assert forbidden not in payload_text


def test_log_gap_uses_explicit_floor_without_silent_clipping() -> None:
    gap = build_isotropy_gap(
        (
            _record("near", 0.0, 0.5, 0.0, 1.0),
            _record("far", 0.5, 1.0, 0.5, 1.0),
        ),
        reference_bin_id="near",
        comparison_bin_id="far",
        floor_value=0.05,
        floor_label="pre_registered_positive_F_floor",
        floor_reason="floor chosen before depth diagnostic",
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )

    payload = gap.as_payload()

    assert payload["raw_F_by_bin"]["near"] == pytest.approx(0.0)
    assert payload["effective_F_by_bin"]["near"] == pytest.approx(0.05)
    assert payload["floor_applied_by_bin"] == {"near": True, "far": False}
    assert payload["G_F"] == pytest.approx(10.0)
    assert math.isfinite(payload["log_g_F"])


@pytest.mark.parametrize(
    "bad_floor",
    [0.0, -1.0, 1.1, float("nan"), float("inf")],
)
def test_floor_policy_must_be_positive_finite(bad_floor: float) -> None:
    with pytest.raises(ValueError, match="floor_value"):
        build_isotropy_gap(
            (
                _record("near", 0.0, 0.5, 0.2, 1.0),
                _record("far", 0.5, 1.0, 0.6, 1.0),
            ),
            reference_bin_id="near",
            comparison_bin_id="far",
            floor_value=bad_floor,
            floor_label="pre_registered_positive_F_floor",
            floor_reason="floor chosen before depth diagnostic",
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


def test_depth_metadata_is_required_and_fail_closed_for_statistical_statuses() -> None:
    with pytest.raises(ValueError, match="covariance_status"):
        _bin("near", 0.0, 0.5, covariance_status="not_statistical")
    with pytest.raises(ValueError, match="covariance_status"):
        _bin("near", 0.0, 0.5, covariance_status="uncalibrated")
    with pytest.raises(ValueError, match="null_mock_status"):
        _bin("near", 0.0, 0.5, null_mock_status="not_statistical")
    with pytest.raises(ValueError, match="null_mock_status"):
        _bin("near", 0.0, 0.5, null_mock_status="uncalibrated")
    with pytest.raises(ValueError, match="covariance_metadata"):
        _bin("near", 0.0, 0.5, covariance_metadata={})
    with pytest.raises(ValueError, match="covariance_metadata.calibration_status"):
        _bin(
            "near",
            0.0,
            0.5,
            covariance_metadata={
                "covariance_hash": "sha256:cov-near",
                "shape": [2, 2],
                "estimator": "mock_bank",
                "calibration_status": "not_calibrated",
            },
        )
    with pytest.raises(ValueError, match="null_metadata.calibration_status"):
        _bin(
            "near",
            0.0,
            0.5,
            null_metadata={
                "mock_bank_hash": "sha256:null-near",
                "calibration_status": "not_calibrated",
            },
        )
    with pytest.raises(ValueError, match="depth"):
        _bin("near", 0.5, 0.5)


@pytest.mark.parametrize("bad_sample_count", [8.9, True, "12"])
def test_depth_sample_count_requires_an_exact_integer(bad_sample_count: object) -> None:
    with pytest.raises(ValueError, match="sample_count"):
        _bin(
            "near",
            0.0,
            0.5,
            sample_count=bad_sample_count,
        )


def test_depth_bins_must_be_ordered_unique_and_non_overlapping() -> None:
    with pytest.raises(ValueError, match="overlap"):
        build_isotropy_gap(
            (
                _record("near", 0.0, 0.6, 0.2, 1.0),
                _record("far", 0.5, 1.0, 0.6, 1.0),
            ),
            reference_bin_id="near",
            comparison_bin_id="far",
            floor_value=_FLOOR,
            floor_label="pre_registered_positive_F_floor",
            floor_reason="floor chosen before depth diagnostic",
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )

    with pytest.raises(ValueError, match="unique"):
        build_isotropy_gap(
            (
                _record("near", 0.0, 0.5, 0.2, 1.0),
                _record("near", 0.5, 1.0, 0.6, 1.0),
            ),
            reference_bin_id="near",
            comparison_bin_id="near",
            floor_value=_FLOOR,
            floor_label="pre_registered_positive_F_floor",
            floor_reason="floor chosen before depth diagnostic",
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


@pytest.mark.parametrize(
    ("reference_bin_id", "comparison_bin_id", "message"),
    [
        ("missing", "far", "reference_bin_id"),
        ("near", "missing", "comparison_bin_id"),
    ],
)
def test_depth_gap_requires_named_reference_and_comparison_bins(
    reference_bin_id: str,
    comparison_bin_id: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        build_isotropy_gap(
            (
                _record("near", 0.0, 0.5, 0.2, 1.0),
                _record("far", 0.5, 1.0, 0.6, 1.0),
            ),
            reference_bin_id=reference_bin_id,
            comparison_bin_id=comparison_bin_id,
            floor_value=_FLOOR,
            floor_label="pre_registered_positive_F_floor",
            floor_reason="floor chosen before depth diagnostic",
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


def test_depth_gap_requires_depth_gap_reference_budget_use() -> None:
    budget = _budget(
        1.0,
        admissible_uses=(
            BudgetUse.DENOMINATOR_SENSITIVITY,
            BudgetUse.SIGNED_PROJECTION_NORMALIZATION,
            BudgetUse.CERTIFIED_FILLING_CEILING,
        ),
    )

    with pytest.raises(ValueError, match="DEPTH_GAP_REFERENCE"):
        build_depth_bin_f_record(
            _f_score(0.2, 1.0, budget=budget),
            depth_bin=_bin("near", 0.0, 0.5),
        )


def test_depth_gap_splits_numerator_from_denominator_evolution() -> None:
    gap = build_isotropy_gap(
        (
            _record("near", 0.0, 0.5, 0.2, 1.0),
            _record("far", 0.5, 1.0, 0.2, 0.5),
        ),
        reference_bin_id="near",
        comparison_bin_id="far",
        floor_value=_FLOOR,
        floor_label="pre_registered_positive_F_floor",
        floor_reason="floor chosen before depth diagnostic",
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )

    payload = gap.as_payload()
    split = payload["denominator_evolution_split"]

    assert payload["raw_F_by_bin"] == {"near": pytest.approx(0.2), "far": pytest.approx(0.4)}
    assert split["x_C_depth_delta"] == pytest.approx(0.0)
    assert split["denominator_depth_delta"] == pytest.approx(-0.5)
    assert split["F_depth_delta"] == pytest.approx(0.2)
    assert split["denominator_value_by_bin"] == {
        "near": pytest.approx(1.0),
        "far": pytest.approx(0.5),
    }
    assert split["denominator_policy_by_bin"] == {
        "near": "MES_linear",
        "far": "MES_linear",
    }
    assert split["mean_summary_is_decompositional"] is False
    assert split["split_kind"] == "samplewise_values_plus_mean_summary"
    assert split["samplewise_x_C_by_bin"] == {
        "near": [pytest.approx(0.2)],
        "far": [pytest.approx(0.2)],
    }
    assert split["samplewise_denominator_value_by_bin"] == {
        "near": [pytest.approx(1.0)],
        "far": [pytest.approx(0.5)],
    }
    assert split["samplewise_F_by_bin"] == {
        "near": [pytest.approx(0.2)],
        "far": [pytest.approx(0.4)],
    }


def test_denominator_split_exposes_samplewise_ratio_provenance() -> None:
    near = build_depth_bin_f_record(
        _f_score_samples((0.25, 0.75), (1.0, 1.0)),
        depth_bin=_bin("near", 0.0, 0.5, sample_count=2),
    )
    far = build_depth_bin_f_record(
        _f_score_samples((0.4, 0.6), (0.5, 1.5)),
        depth_bin=_bin("far", 0.5, 1.0, sample_count=2),
    )

    gap = build_isotropy_gap(
        (near, far),
        reference_bin_id="near",
        comparison_bin_id="far",
        floor_value=_FLOOR,
        floor_label="pre_registered_positive_F_floor",
        floor_reason="floor chosen before depth diagnostic",
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )

    split = gap.as_payload()["denominator_evolution_split"]

    assert split["x_C_depth_delta"] == pytest.approx(0.0)
    assert split["denominator_depth_delta"] == pytest.approx(0.0)
    assert split["F_depth_delta"] == pytest.approx(0.1)
    assert split["mean_summary_is_decompositional"] is False
    assert split["samplewise_x_C_by_bin"] == {
        "near": [pytest.approx(0.25), pytest.approx(0.75)],
        "far": [pytest.approx(0.4), pytest.approx(0.6)],
    }
    assert split["samplewise_denominator_value_by_bin"] == {
        "near": [pytest.approx(1.0), pytest.approx(1.0)],
        "far": [pytest.approx(0.5), pytest.approx(1.5)],
    }
    assert split["samplewise_F_by_bin"] == {
        "near": [pytest.approx(0.25), pytest.approx(0.75)],
        "far": [pytest.approx(0.8), pytest.approx(0.4)],
    }
    assert split["sample_count_by_bin"] == {"near": 2, "far": 2}


def test_transfer_derived_depth_bins_preserve_external_provenance() -> None:
    gap = build_isotropy_gap(
        (
            build_depth_bin_f_record(
                _f_score(
                    0.2,
                    1.0,
                    transfer_id="aniclass.lowell.scalar.v1",
                ),
                depth_bin=_bin("near", 0.0, 0.5),
            ),
            build_depth_bin_f_record(
                _f_score(
                    0.6,
                    1.0,
                    transfer_id="aniclass.lowell.scalar.v1",
                ),
                depth_bin=_bin("far", 0.5, 1.0),
            ),
        ),
        reference_bin_id="near",
        comparison_bin_id="far",
        floor_value=_FLOOR,
        floor_label="pre_registered_positive_F_floor",
        floor_reason="floor chosen before depth diagnostic",
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )

    payload = gap.as_payload()

    assert payload["transfer_source"] == "AniCLASS_external"
    assert payload["transfer_spec_ids"] == ["aniclass.lowell.scalar.v1"]
    assert payload["transfer_metadata_by_bin"]["near"]["transfer_source"] == (
        "AniCLASS_external"
    )
    assert payload["transfer_metadata_hash_by_bin"]["near"] == (
        payload["transfer_metadata_hash_by_bin"]["far"]
    )
    assert "native_validated" not in json.dumps(payload, sort_keys=True)


def test_transfer_metadata_must_match_across_depth_bins() -> None:
    transfer_id = "aniclass.lowell.scalar.v1"
    with pytest.raises(ValueError, match="transfer_metadata"):
        build_isotropy_gap(
            (
                build_depth_bin_f_record(
                    _f_score(
                        0.2,
                        1.0,
                        transfer_id=transfer_id,
                        transfer_metadata=_external_transfer_metadata(transfer_id),
                    ),
                    depth_bin=_bin("near", 0.0, 0.5),
                ),
                build_depth_bin_f_record(
                    _f_score(
                        0.6,
                        1.0,
                        transfer_id=transfer_id,
                        transfer_metadata=_external_transfer_metadata(
                            transfer_id,
                            source_ref="aniclass:different-source-ref",
                        ),
                    ),
                    depth_bin=_bin("far", 0.5, 1.0),
                ),
            ),
            reference_bin_id="near",
            comparison_bin_id="far",
            floor_value=_FLOOR,
            floor_label="pre_registered_positive_F_floor",
            floor_reason="floor chosen before depth diagnostic",
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


def test_transfer_metadata_transfer_id_must_match_record_spec_id() -> None:
    with pytest.raises(ValueError, match="transfer_id"):
        build_isotropy_gap(
            (
                build_depth_bin_f_record(
                    _f_score(
                        0.2,
                        1.0,
                        transfer_id="aniclass.lowell.scalar.v1",
                        transfer_metadata=_external_transfer_metadata(
                            "aniclass.lowell.scalar.other"
                        ),
                    ),
                    depth_bin=_bin("near", 0.0, 0.5),
                ),
                build_depth_bin_f_record(
                    _f_score(
                        0.6,
                        1.0,
                        transfer_id="aniclass.lowell.scalar.v1",
                    ),
                    depth_bin=_bin("far", 0.5, 1.0),
                ),
            ),
            reference_bin_id="near",
            comparison_bin_id="far",
            floor_value=_FLOOR,
            floor_label="pre_registered_positive_F_floor",
            floor_reason="floor chosen before depth diagnostic",
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


def test_mixed_transfer_sources_are_not_comparable_as_gf() -> None:
    with pytest.raises(ValueError, match="transfer_source"):
        build_isotropy_gap(
            (
                build_depth_bin_f_record(
                    _f_score(
                        0.2,
                        1.0,
                        transfer_id="aniclass.lowell.scalar.v1",
                    ),
                    depth_bin=_bin("near", 0.0, 0.5),
                ),
                _record("far", 0.5, 1.0, 0.6, 1.0),
            ),
            reference_bin_id="near",
            comparison_bin_id="far",
            floor_value=_FLOOR,
            floor_label="pre_registered_positive_F_floor",
            floor_reason="floor chosen before depth diagnostic",
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


def test_mixed_transfer_specs_are_not_comparable_as_gf() -> None:
    with pytest.raises(ValueError, match="transfer_spec_id"):
        build_isotropy_gap(
            (
                build_depth_bin_f_record(
                    _f_score(
                        0.2,
                        1.0,
                        transfer_id="aniclass.lowell.scalar.v1",
                    ),
                    depth_bin=_bin("near", 0.0, 0.5),
                ),
                build_depth_bin_f_record(
                    _f_score(
                        0.6,
                        1.0,
                        transfer_id="aniclass.lowell.scalar.v2",
                    ),
                    depth_bin=_bin("far", 0.5, 1.0),
                ),
            ),
            reference_bin_id="near",
            comparison_bin_id="far",
            floor_value=_FLOOR,
            floor_label="pre_registered_positive_F_floor",
            floor_reason="floor chosen before depth diagnostic",
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


def test_gf_rejects_inference_tilt_family_geometry_and_native_claims() -> None:
    phrase_parts = (
        {"caption": "G_F is HTT " + "evidence"},
        {"caption": "G_F reports " + "global " + "tilt"},
        {"caption": "G_F reports " + "global-tilt"},
        {"caption": "G_F supports family " + "identification"},
        {"caption": "G_F supports family-identification"},
        {"caption": "G_F reports Bianchi " + "geometry"},
        {"caption": "G_F is a native " + "solver result"},
        {"caption": "external transfer " + "validated as " + "native"},
    )
    for metadata in phrase_parts:
        with pytest.raises(ValueError, match="artifact_metadata"):
            build_isotropy_gap(
                (
                    _record("near", 0.0, 0.5, 0.2, 1.0),
                    _record("far", 0.5, 1.0, 0.6, 1.0),
                ),
                reference_bin_id="near",
                comparison_bin_id="far",
                floor_value=_FLOOR,
                floor_label="pre_registered_positive_F_floor",
                floor_reason="floor chosen before depth diagnostic",
                generating_command=_GENERATING_COMMAND,
                worktree_state=_WORKTREE_STATE,
                artifact_metadata=metadata,
            )

    with pytest.raises(ValueError, match="caveats"):
        IsotropyGap(
            depth_bin_records=(
                _record("near", 0.0, 0.5, 0.2, 1.0),
                _record("far", 0.5, 1.0, 0.6, 1.0),
            ),
            reference_bin_id="near",
            comparison_bin_id="far",
            floor_value=_FLOOR,
            floor_label="pre_registered_positive_F_floor",
            floor_reason="floor chosen before depth diagnostic",
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
            caveats=("G_F creates a MIO " + "posterior",),
        )


def test_gf_requires_generation_and_worktree_provenance() -> None:
    with pytest.raises(ValueError, match="generating_command"):
        IsotropyGap(
            depth_bin_records=(
                _record("near", 0.0, 0.5, 0.2, 1.0),
                _record("far", 0.5, 1.0, 0.6, 1.0),
            ),
            reference_bin_id="near",
            comparison_bin_id="far",
            floor_value=_FLOOR,
            floor_label="pre_registered_positive_F_floor",
            floor_reason="floor chosen before depth diagnostic",
            worktree_state=_WORKTREE_STATE,
        )

    with pytest.raises(ValueError, match="git_commit or worktree_state"):
        build_isotropy_gap(
            (
                _record("near", 0.0, 0.5, 0.2, 1.0),
                _record("far", 0.5, 1.0, 0.6, 1.0),
            ),
            reference_bin_id="near",
            comparison_bin_id="far",
            floor_value=_FLOOR,
            floor_label="pre_registered_positive_F_floor",
            floor_reason="floor chosen before depth diagnostic",
            generating_command=_GENERATING_COMMAND,
        )


def test_formalism_package_exports_isotropy_gap_contract() -> None:
    import mio.formalism as formalism

    assert formalism.DepthBinMetadata is DepthBinMetadata
    assert formalism.DepthBinFRecord is DepthBinFRecord
    assert formalism.IsotropyGap is IsotropyGap
    assert formalism.build_depth_bin_f_record is build_depth_bin_f_record
    assert formalism.build_isotropy_gap is build_isotropy_gap
