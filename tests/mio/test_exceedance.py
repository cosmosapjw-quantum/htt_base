from __future__ import annotations

import dataclasses
import json

import pytest

from common.transfer_registry import TransferFunctionSpec, TransferValidRange
from mio.formalism.budget_spec import BudgetPolicy, BudgetSpec, BudgetUse
from mio.formalism.departure_bundle import build_departure_bundle
from mio.formalism.exceedance import (
    ExceedanceCurve,
    MeasureKind,
    ThresholdPolicy,
    build_exceedance_curve,
    build_exceedance_curve_from_filling_fraction,
    build_exceedance_curve_from_normalized_scores,
)
from mio.formalism.filling_fraction import build_certified_filling_fraction
from mio.formalism.normalized_score import build_normalized_score

_GENERATING_COMMAND = "pytest tests/mio/test_exceedance.py"
_WORKTREE_STATE = "test-fixture"
_THRESHOLD_METADATA = {
    "registration_status": "pre_registered",
    "selection_rule": "threshold grid fixed before diagnostic scan",
    "registration_hash": "sha256:threshold-plan",
}


def _external_transfer_metadata(transfer_id: str) -> dict[str, object]:
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
    return spec.to_metadata()


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
        "denominator_label": "linear MES reference denominator",
        "comparator": "CMB_FLRW_reference",
        "frame": "normal_frame",
        "units": "dimensionless_hubble_normalized",
        "config_hash": f"cfg-budget-{denominator_value}",
        "input_hashes": (f"budget-input-{denominator_value}",),
        "assumptions": ("linear MES denominator for diagnostic ratios",),
        "admissible_uses": (
            BudgetUse.DENOMINATOR_SENSITIVITY,
            BudgetUse.SIGNED_PROJECTION_NORMALIZATION,
            BudgetUse.CERTIFIED_FILLING_CEILING,
            BudgetUse.EXCEEDANCE_THRESHOLD,
        ),
        "is_admissible_ceiling": True,
    }
    values.update(overrides)
    return BudgetSpec(**values)


def _q_score(x_c: float, denominator: float = 1.0):
    return build_normalized_score(
        _bundle(x_c),
        _budget(
            denominator,
            admissible_uses=(
                BudgetUse.DENOMINATOR_SENSITIVITY,
                BudgetUse.SIGNED_PROJECTION_NORMALIZATION,
                BudgetUse.EXCEEDANCE_THRESHOLD,
            ),
            is_admissible_ceiling=False,
        ),
        numerator_policy="absolute",
    )


def _f_score():
    return build_certified_filling_fraction(
        (_bundle(0.2), _bundle(0.6)),
        (_budget(1.0), _budget(1.2)),
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )


def test_pi_curve_only_payload_is_exceedance_not_truth_probability() -> None:
    curve = build_exceedance_curve(
        (0.1, 0.4, 0.9),
        source_score_label="Q",
        input_hashes=("samples-input",),
        measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
        thresholds=(0.0, 0.5, 1.0),
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
        artifact_metadata={"report_role": "Pi diagnostic curve"},
    )

    payload = curve.as_payload()
    payload_text = json.dumps(payload, sort_keys=True).lower()

    assert dataclasses.is_dataclass(curve)
    assert payload["score_label"] == "Pi"
    assert payload["score_kind"] == "exceedance_curve"
    assert payload["target"] == "Q"
    assert payload["measure_kind"] == "sample_distribution"
    assert payload["threshold_policy"] == "curve_only"
    assert payload["threshold_registration_status"] == "curve_only_no_selected_threshold"
    assert payload["selected_threshold"] is None
    assert payload["threshold_values"] == [0.0, 0.5, 1.0]
    assert payload["threshold_grid"] == [0.0, 0.5, 1.0]
    assert payload["look_elsewhere_trials"] == 1
    assert payload["display_metadata"]["requires_measure_kind"] is True
    assert payload["display_metadata"]["measure_kind"] == "sample_distribution"
    assert payload["display_metadata"]["threshold_policy"] == "curve_only"
    assert payload["display_metadata"]["threshold_registration_status"] == (
        "curve_only_no_selected_threshold"
    )
    assert payload["display_metadata"]["look_elsewhere_trials"] == 1
    assert payload["display_metadata"]["calibration_status"] == (
        "raw_exceedance_only_uncalibrated_no_p_value"
    )
    assert payload["display_metadata"]["covariance_status"] == "not_statistical"
    assert payload["display_metadata"]["null_mock_status"] == "not_statistical"
    assert payload["display_metadata"]["p_value_interpretation_status"] == (
        "blocked_exceedance_not_p_value"
    )
    assert payload["calibration_status"] == (
        "raw_exceedance_only_uncalibrated_no_p_value"
    )
    assert payload["exceedance_counts"] == [3, 1, 0]
    assert payload["exceedance_fractions"] == pytest.approx([1.0, 1 / 3, 0.0])
    assert payload["pi_grid"] == pytest.approx([1.0, 1 / 3, 0.0])
    assert payload["sample_count"] == 3
    assert payload["valid_sample_count"] == 3
    assert payload["invalid_sample_count"] == 0
    assert payload["invalid_sample_reasons"] == []
    assert payload["exceedance_rule"] == "sample_value > threshold"
    assert payload["owner"] == "MIO"
    assert payload["implementation_scope"] == "mio"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["generating_command"] == _GENERATING_COMMAND
    assert payload["worktree_state"] == _WORKTREE_STATE
    for forbidden in (
        "posterior",
        "evidence",
        "family_id",
        "geometry",
        "native_validated",
        "probability_anisotropy_true",
    ):
        assert forbidden not in payload_text


def test_mio_pi_rejects_posterior_probability_language() -> None:
    with pytest.raises(ValueError, match="posterior|probability"):
        build_exceedance_curve(
            (0.1, 0.2),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            thresholds=(0.15,),
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
            artifact_metadata={
                "definition": "posterior probability P(Q>q|D)",
            },
        )

    with pytest.raises(ValueError, match="probability"):
        build_exceedance_curve(
            (0.1, 0.2),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            thresholds=(0.15,),
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
            caveats=("Pi is a probability of anisotropy",),
        )


def test_mio_pi_rejects_htt_posterior_pushforward_source_kind() -> None:
    with pytest.raises(ValueError, match="HTT posterior"):
        build_exceedance_curve(
            (0.1, 0.2),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            thresholds=(0.15,),
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
            source_kind="htt_posterior_pushforward_distribution",
        )


def test_pi_display_metadata_reports_look_elsewhere_trials() -> None:
    curve = build_exceedance_curve(
        (0.1, 0.4, 0.9),
        source_score_label="Q",
        input_hashes=("samples-input",),
        measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
        thresholds=(0.25, 0.75),
        look_elsewhere_trials=4,
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )
    payload = curve.as_payload()

    assert payload["look_elsewhere_trials"] == 4
    assert payload["display_metadata"]["look_elsewhere_trials"] == 4
    assert payload["display_metadata"]["threshold_grid"] == [0.25, 0.75]
    assert payload["display_metadata"]["source_score_label"] == "Q"
    assert payload["display_metadata"]["source_kind"] == "diagnostic_samples"
    assert "p_value_claim" in payload["display_metadata"]["blocked_use_codes"]

    with pytest.raises(ValueError, match="look_elsewhere_trials"):
        build_exceedance_curve(
            (0.1, 0.4),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            look_elsewhere_trials=0,
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


def test_pi_threshold_selection_requires_pre_registration_metadata() -> None:
    with pytest.raises(ValueError, match="selected_threshold"):
        build_exceedance_curve(
            (0.1, 0.4, 0.9),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            thresholds=(0.5,),
            selected_threshold=0.5,
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )

    with pytest.raises(ValueError, match="threshold_metadata"):
        build_exceedance_curve(
            (0.1, 0.4, 0.9),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            thresholds=(0.5,),
            threshold_policy=ThresholdPolicy.PRE_REGISTERED,
            selected_threshold=0.5,
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )

    curve = build_exceedance_curve(
        (0.1, 0.4, 0.9),
        source_score_label="Q",
        input_hashes=("samples-input",),
        measure_kind=MeasureKind.BOOTSTRAP_MOCK_DISTRIBUTION,
        thresholds=(0.5,),
        threshold_policy="pre_registered",
        covariance_statuses=("mock_covariance",),
        null_mock_statuses=("mock_calibrated",),
        threshold_metadata=_THRESHOLD_METADATA,
        selected_threshold=0.5,
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )

    assert curve.threshold_policy is ThresholdPolicy.PRE_REGISTERED
    assert curve.measure_kind is MeasureKind.BOOTSTRAP_MOCK_DISTRIBUTION
    assert curve.selected_threshold == pytest.approx(0.5)
    assert curve.selected_exceedance_fraction == pytest.approx(1 / 3)
    assert curve.as_payload()["threshold_metadata"] == _THRESHOLD_METADATA
    assert curve.as_payload()["threshold_registration_status"] == "pre_registered"


def test_pi_thresholds_are_sorted_unique_and_exceedance_is_monotone() -> None:
    curve = build_exceedance_curve(
        (0.4, 0.1, 0.9, 0.4),
        source_score_label="Q",
        input_hashes=("samples-input",),
        measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
        thresholds=(0.5, 0.0, 0.5, 1.0, 0.4),
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )

    assert curve.thresholds == pytest.approx((0.0, 0.4, 0.5, 1.0))
    assert curve.exceedance_counts == (4, 1, 1, 0)
    assert curve.exceedance_fractions == pytest.approx((1.0, 0.25, 0.25, 0.0))
    assert all(
        left >= right
        for left, right in zip(
            curve.exceedance_fractions[:-1],
            curve.exceedance_fractions[1:],
            strict=True,
        )
    )


@pytest.mark.parametrize(
    "samples, thresholds, message",
    [
        ((), (0.5,), "sample_values"),
        ((float("nan"),), (0.5,), "sample_values"),
        ((0.1,), (float("inf"),), "thresholds"),
    ],
)
def test_pi_rejects_empty_or_nonfinite_inputs(
    samples: tuple[float, ...],
    thresholds: tuple[float, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        build_exceedance_curve(
            samples,
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            thresholds=thresholds,
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


def test_pi_rejects_truth_probability_language() -> None:
    phrase = "probability that anisotropy is " + "true"

    with pytest.raises(ValueError, match="artifact_metadata"):
        build_exceedance_curve(
            (0.1, 0.4),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
            artifact_metadata={"caption": f"Pi is the {phrase}"},
        )

    with pytest.raises(ValueError, match="caveats"):
        ExceedanceCurve(
            sample_values=(0.1, 0.4),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
            caveats=("Pi provides HTT evidence",),
        )

    with pytest.raises(ValueError, match="artifact_metadata"):
        build_exceedance_curve(
            (0.1, 0.4),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
            artifact_metadata={"caption": "Pi " + "p-" + "value display"},
        )


def test_pi_curve_only_rejects_hidden_selected_threshold_metadata() -> None:
    with pytest.raises(ValueError, match="selected threshold"):
        build_exceedance_curve(
            (0.1, 0.4),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
            artifact_metadata={"selected_threshold": 0.4},
        )

    with pytest.raises(ValueError, match="selected threshold"):
        build_exceedance_curve(
            (0.1, 0.4),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
            source_metadata=({"selected_exceedance_fraction": 0.5},),
        )


def test_pi_requires_explicit_measure_kind() -> None:
    with pytest.raises(ValueError, match="measure_kind"):
        ExceedanceCurve(
            sample_values=(0.1,),
            source_score_label="Q",
            input_hashes=("samples-input",),
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


def test_pi_mock_and_null_measures_require_statistical_status_metadata() -> None:
    with pytest.raises(ValueError, match="null_ensemble"):
        build_exceedance_curve(
            (0.1, 0.4),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.NULL_ENSEMBLE,
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )

    curve = build_exceedance_curve(
        (0.1, 0.4),
        source_score_label="Q",
        input_hashes=("samples-input",),
        measure_kind=MeasureKind.NULL_ENSEMBLE,
        covariance_statuses=("null_covariance_attached",),
        null_mock_statuses=("matched_null_ensemble",),
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )

    assert curve.as_payload()["measure_kind"] == "null_ensemble"
    assert curve.as_payload()["covariance_status"] == "null_covariance_attached"
    assert curve.as_payload()["null_mock_status"] == "matched_null_ensemble"


def test_pi_preregistered_metadata_rejects_posthoc_or_result_fields() -> None:
    bad_metadata = {
        "registration_status": "pre_registered",
        "selection_rule": "choose after diagnostic scan",
        "registration_hash": "sha256:bad-plan",
    }
    with pytest.raises(ValueError, match="post-hoc"):
        build_exceedance_curve(
            (0.1, 0.4),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            thresholds=(0.2,),
            threshold_policy=ThresholdPolicy.PRE_REGISTERED,
            threshold_metadata=bad_metadata,
            selected_threshold=0.2,
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )

    with pytest.raises(ValueError, match="selected threshold"):
        build_exceedance_curve(
            (0.1, 0.4),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            thresholds=(0.2,),
            threshold_policy=ThresholdPolicy.PRE_REGISTERED,
            threshold_metadata={**_THRESHOLD_METADATA, "pi_value": 0.5},
            selected_threshold=0.2,
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


def test_pi_direct_transfer_provenance_requires_pr014_metadata() -> None:
    with pytest.raises(ValueError, match="transfer_spec_id"):
        build_exceedance_curve(
            (0.1,),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            source_transfer_sources=("AniCLASS_external",),
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )

    with pytest.raises(ValueError, match="native transfer"):
        build_exceedance_curve(
            (0.1,),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            source_transfer_sources=("BASS_native_validated",),
            source_transfer_spec_ids=("native.future",),
            source_transfer_metadata=(_external_transfer_metadata("native.future"),),
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )

    curve = build_exceedance_curve(
        (0.1,),
        source_score_label="Q",
        input_hashes=("samples-input",),
        measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
        source_transfer_sources=("AniCLASS_external",),
        source_transfer_spec_ids=("aniclass.pi.direct",),
        source_transfer_metadata=(_external_transfer_metadata("aniclass.pi.direct"),),
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )

    assert curve.as_payload()["transfer_source"] == "AniCLASS_external"
    assert curve.as_payload()["source_transfer_spec_ids"] == ["aniclass.pi.direct"]


def test_pi_rejects_source_kind_and_non_json_metadata_bypasses() -> None:
    with pytest.raises(ValueError, match="source_kind"):
        build_exceedance_curve(
            (0.1,),
            source_score_label="Q",
            source_kind="posterior_probability_samples",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )

    with pytest.raises(ValueError, match="JSON-compatible"):
        build_exceedance_curve(
            (0.1,),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            source_transfer_sources=("AniCLASS_external",),
            source_transfer_spec_ids=("aniclass.bad",),
            source_transfer_metadata=({"transfer_source": object()},),
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )

    payload = build_exceedance_curve(
        (0.1,),
        source_score_label="Q",
        input_hashes=("samples-input",),
        measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
        source_metadata=({"rank_status": "full_rank"},),
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    ).as_payload()

    json.dumps(payload, sort_keys=True, allow_nan=False)


def test_pi_from_q_scores_preserves_q_provenance() -> None:
    curve = build_exceedance_curve_from_normalized_scores(
        (_q_score(0.1), _q_score(0.4), _q_score(0.9)),
        thresholds=(0.25, 0.75),
        measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
        look_elsewhere_trials=3,
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )
    payload = curve.as_payload()

    assert payload["source_score_label"] == "Q"
    assert payload["source_kind"] == "normalized_score.q_value"
    assert payload["target"] == "Q"
    assert payload["measure_kind"] == "sample_distribution"
    assert payload["sample_values"] == pytest.approx([0.1, 0.4, 0.9])
    assert payload["exceedance_fractions"] == pytest.approx([2 / 3, 1 / 3])
    assert payload["transfer_source"] == "none"
    assert len(payload["source_config_hashes"]) == 3
    assert payload["source_metadata"][0]["numerator_policy"] == "absolute"
    assert payload["source_metadata"][0]["denominator_use"] == "exceedance_threshold"
    assert payload["look_elsewhere_trials"] == 3
    assert payload["display_metadata"]["look_elsewhere_trials"] == 3
    assert "x-input-0.1" in payload["input_hashes"]
    assert "budget-input-1.0" in payload["input_hashes"]


def test_pi_from_f_samples_preserves_f_source_without_ratio_summary() -> None:
    curve = build_exceedance_curve_from_filling_fraction(
        _f_score(),
        thresholds=(0.25, 0.75),
        measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )
    payload = curve.as_payload()

    assert payload["source_score_label"] == "F"
    assert payload["source_kind"] == "certified_filling_fraction.f_samples"
    assert payload["target"] == "F"
    assert payload["sample_values"] == pytest.approx([0.2, 0.5])
    assert payload["exceedance_fractions"] == pytest.approx([0.5, 0.0])
    assert "F_Bayes" not in payload
    assert payload["transfer_source"] == "none"


def test_pi_requires_generation_and_worktree_provenance() -> None:
    with pytest.raises(ValueError, match="generating_command"):
        ExceedanceCurve(
            sample_values=(0.1,),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            worktree_state=_WORKTREE_STATE,
        )

    with pytest.raises(ValueError, match="git_commit or worktree_state"):
        build_exceedance_curve(
            (0.1,),
            source_score_label="Q",
            input_hashes=("samples-input",),
            measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
            generating_command=_GENERATING_COMMAND,
        )


def test_active_formalism_hides_legacy_exceedance_contract() -> None:
    import mio.formalism as formalism
    import mio.legacy_projection as legacy

    assert not hasattr(formalism, "ExceedanceCurve")
    assert not hasattr(formalism, "build_exceedance_curve")
    assert legacy.ExceedanceCurve is ExceedanceCurve
    assert legacy.MeasureKind.SAMPLE_DISTRIBUTION.value == "sample_distribution"
    assert legacy.ThresholdPolicy.CURVE_ONLY.value == "curve_only"
    assert legacy.build_exceedance_curve is build_exceedance_curve
