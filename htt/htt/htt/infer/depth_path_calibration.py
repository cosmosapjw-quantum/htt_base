"""HTT-owned PR-284 premise evaluation and calibration decisions."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from typing import Hashable, Sequence

from common.depth_path import DepthPath, DepthPathError, revalidate_depth_path
from common.depth_path_calibration import (
    DepthPathCalibrationStatus,
    DepthPathDoobCalibration,
    DepthPathFiniteTargetLaw,
    DepthPathMatchedMockPlan,
    DepthPathReverseMartingaleReport,
    DepthPathSelectionContract,
    DepthPathThresholdContract,
    PR284_EVENT_COMPARISON,
    ReverseMartingalePremiseStatus,
    _build_depth_path_doob_calibration_contract,
    _build_depth_path_matched_mock_plan_contract,
    _build_depth_path_reverse_martingale_report_contract,
    revalidate_depth_path_finite_target_law,
    revalidate_depth_path_matched_mock_plan,
    revalidate_depth_path_reverse_martingale_report,
    revalidate_depth_path_selection_contract,
    revalidate_depth_path_threshold_contract,
)
from common.vector_tensor_statistical_foundations import (
    VectorTensorStatisticalFoundationError,
    certify_finite_partition_tower,
)


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise DepthPathError(f"{name} must be non-empty trimmed text")
    return value


def _texts(
    values: Sequence[object],
    name: str,
    *,
    minimum: int = 1,
    unique: bool = True,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise DepthPathError(f"{name} must be a sequence of text")
    result = tuple(_text(value, name) for value in values)
    if len(result) < minimum:
        raise DepthPathError(f"{name} must contain at least {minimum} value(s)")
    if unique and len(result) != len(set(result)):
        raise DepthPathError(f"{name} must not contain duplicates")
    return result


def _sha256_payload(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _fraction_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def _conditional_values(
    *,
    weights: tuple[Fraction, ...],
    target: tuple[Fraction, ...],
    labels: tuple[str, ...],
) -> tuple[Fraction, ...]:
    mass: dict[str, Fraction] = {}
    weighted: dict[str, Fraction] = {}
    for probability, value, label in zip(weights, target, labels, strict=True):
        mass[label] = mass.get(label, Fraction()) + probability
        weighted[label] = weighted.get(label, Fraction()) + probability * value
    if any(value <= 0 for value in mass.values()):
        raise DepthPathError("every conditional cell must have positive mass")
    conditional = {label: weighted[label] / mass[label] for label in mass}
    return tuple(conditional[label] for label in labels)


def build_depth_path_matched_mock_plan(
    *,
    plan_id: str,
    path: DepthPath,
    threshold_contract: DepthPathThresholdContract,
    preprocessing_id: str,
    estimator_id: str,
    registration_id: str,
    null_law_id: str,
    mock_generator_id: str,
    ensemble_policy_id: str,
    seed_policy_id: str,
    matching_variable_ids: Sequence[str],
    acceptance_rule_id: str,
    multiplicity_rule_id: str,
) -> DepthPathMatchedMockPlan:
    resolved_path = revalidate_depth_path(path)
    threshold = revalidate_depth_path_threshold_contract(threshold_contract)
    return _build_depth_path_matched_mock_plan_contract(
        plan_id=plan_id,
        path_content_id=resolved_path.content_id,
        threshold_contract_content_id=threshold.content_id,
        preprocessing_id=preprocessing_id,
        estimator_id=estimator_id,
        registration_id=registration_id,
        null_law_id=null_law_id,
        mock_generator_id=mock_generator_id,
        ensemble_policy_id=ensemble_policy_id,
        seed_policy_id=seed_policy_id,
        matching_variable_ids=tuple(matching_variable_ids),
        acceptance_rule_id=acceptance_rule_id,
        multiplicity_rule_id=multiplicity_rule_id,
    )


def build_depth_path_reverse_martingale_report(
    *,
    report_id: str,
    path: DepthPath,
    threshold_contract: DepthPathThresholdContract,
    finite_target_law: DepthPathFiniteTargetLaw,
    selection_contract: DepthPathSelectionContract,
    path_partitions: Sequence[Sequence[Hashable]],
    sigma_field_ids: Sequence[str],
    filtration_id: str,
    preprocessing_id: str,
    estimator_id: str,
    premise_evidence_id: str,
) -> DepthPathReverseMartingaleReport:
    """Replay one exact finite decreasing filtration and seal its diagnostic."""

    resolved_path = revalidate_depth_path(path)
    threshold = revalidate_depth_path_threshold_contract(threshold_contract)
    law = revalidate_depth_path_finite_target_law(finite_target_law)
    selection = revalidate_depth_path_selection_contract(selection_contract)
    if selection.finite_target_law.content_id != law.content_id:
        raise DepthPathError("selection contract is not bound to the finite law")
    mean = sum(
        probability * value
        for probability, value in zip(law.weights, law.common_target, strict=True)
    )
    if mean != 0:
        raise DepthPathError("common target must be exactly centered")
    second_moment = sum(
        probability * value * value
        for probability, value in zip(law.weights, law.common_target, strict=True)
    )
    if second_moment <= 0:
        raise DepthPathError("common target requires a positive second moment")

    if isinstance(path_partitions, (str, bytes)):
        raise DepthPathError("path_partitions must be a sequence of partitions")
    try:
        partitions = tuple(
            _texts(
                tuple(row),
                "path_partitions",
                minimum=len(law.atom_ids),
                unique=False,
            )
            for row in path_partitions
        )
    except TypeError as exc:
        raise DepthPathError("every path partition must be a sequence") from exc
    if len(partitions) != len(resolved_path.strata) or any(
        len(row) != len(law.atom_ids) for row in partitions
    ):
        raise DepthPathError("one atom-aligned partition is required per path stratum")
    sigma_fields = _texts(
        sigma_field_ids,
        "sigma_field_ids",
        minimum=len(resolved_path.strata),
    )
    if len(sigma_fields) != len(resolved_path.strata):
        raise DepthPathError("one sigma_field_id is required per path stratum")
    _text(filtration_id, "filtration_id")
    _text(preprocessing_id, "preprocessing_id")
    _text(estimator_id, "estimator_id")
    _text(premise_evidence_id, "premise_evidence_id")

    try:
        tower = certify_finite_partition_tower(
            weights=law.weights,
            common_target=law.common_target,
            partitions=tuple(reversed(partitions)),
        )
    except VectorTensorStatisticalFoundationError as exc:
        raise DepthPathError(
            f"path partitions do not form the required decreasing filtration: {exc}"
        ) from exc
    conditionals = tuple(
        _conditional_values(
            weights=law.weights,
            target=law.common_target,
            labels=partition,
        )
        for partition in partitions
    )
    selected_index = selection.selected_atom_index
    path_values = tuple(row[selected_index] for row in conditionals)
    path_maximum = max(abs(value) for value in path_values)
    tower_payload = {
        "atom_count": tower.atom_count,
        "conditional_expectations": [list(row) for row in tower.conditional_expectations],
        "exact_equalities": list(tower.exact_equalities),
        "rung_count": tower.rung_count,
        "schema": "PR284_EXACT_FINITE_TOWER_REPLAY_V1",
    }
    tower_content_id = _sha256_payload(tower_payload)
    path_maximum_content_id = _sha256_payload(
        {
            "path_values": [_fraction_text(value) for value in path_values],
            "selected_atom_id": selection.selected_atom_id,
            "selection_contract_content_id": selection.content_id,
            "value": _fraction_text(path_maximum),
        }
    )
    return _build_depth_path_reverse_martingale_report_contract(
        path=resolved_path,
        report_id=report_id,
        path_content_id=resolved_path.content_id,
        stratum_content_ids=tuple(value.content_id for value in resolved_path.strata),
        threshold_contract=threshold,
        filtration_id=filtration_id,
        filtration_direction="DECREASING",
        preprocessing_id=preprocessing_id,
        estimator_id=estimator_id,
        premise_evidence_id=premise_evidence_id,
        premise_status=ReverseMartingalePremiseStatus.PROVED_FINITE_REGISTERED_PATH,
        finite_target_law=law,
        selection_contract=selection,
        path_partitions=partitions,
        sigma_field_ids=sigma_fields,
        path_values=path_values,
        path_maximum_abs=path_maximum,
        path_maximum_content_id=path_maximum_content_id,
        target_second_moment=second_moment,
        exact_tower_equalities=tuple(tower.exact_equalities),
        exact_tower_report_content_id=tower_content_id,
        unresolved_reasons=(),
        matched_mock_plan=None,
    )


def build_unproved_depth_path_reverse_martingale_report(
    *,
    report_id: str,
    path: DepthPath,
    threshold_contract: DepthPathThresholdContract,
    filtration_id: str,
    preprocessing_id: str,
    estimator_id: str,
    premise_evidence_id: str,
    unresolved_reasons: Sequence[str],
    matched_mock_plan: DepthPathMatchedMockPlan | None,
) -> DepthPathReverseMartingaleReport:
    """Seal an honest no-bound status and its preregistered mock design."""

    resolved_path = revalidate_depth_path(path)
    threshold = revalidate_depth_path_threshold_contract(threshold_contract)
    _text(filtration_id, "filtration_id")
    _text(preprocessing_id, "preprocessing_id")
    _text(estimator_id, "estimator_id")
    _text(premise_evidence_id, "premise_evidence_id")
    reasons = _texts(
        unresolved_reasons,
        "unresolved_reasons",
        minimum=1,
        unique=False,
    )
    if type(matched_mock_plan) is not DepthPathMatchedMockPlan:
        raise DepthPathError("matched_mock_plan must be an exact registered plan")
    plan = revalidate_depth_path_matched_mock_plan(matched_mock_plan)
    if (
        plan.path_content_id != resolved_path.content_id
        or plan.threshold_contract_content_id != threshold.content_id
        or plan.preprocessing_id != preprocessing_id
        or plan.estimator_id != estimator_id
    ):
        raise DepthPathError("matched_mock_plan is not bound to the unproved report")
    return _build_depth_path_reverse_martingale_report_contract(
        path=resolved_path,
        report_id=report_id,
        path_content_id=resolved_path.content_id,
        stratum_content_ids=tuple(value.content_id for value in resolved_path.strata),
        threshold_contract=threshold,
        filtration_id=filtration_id,
        filtration_direction="DECREASING",
        preprocessing_id=preprocessing_id,
        estimator_id=estimator_id,
        premise_evidence_id=premise_evidence_id,
        premise_status=ReverseMartingalePremiseStatus.UNPROVED_REQUIRES_MATCHED_MOCKS,
        finite_target_law=None,
        selection_contract=None,
        path_partitions=(),
        sigma_field_ids=(),
        path_values=(),
        path_maximum_abs=None,
        path_maximum_content_id=None,
        target_second_moment=None,
        exact_tower_equalities=(),
        exact_tower_report_content_id=None,
        unresolved_reasons=reasons,
        matched_mock_plan=plan,
    )


def build_depth_path_doob_calibration(
    *,
    calibration_id: str,
    report: DepthPathReverseMartingaleReport,
    threshold_contract: DepthPathThresholdContract,
    preprocessing_id: str | None = None,
    estimator_id: str | None = None,
) -> DepthPathDoobCalibration:
    """Derive either the exact conservative bound or a mock-required status."""

    resolved_report = revalidate_depth_path_reverse_martingale_report(report)
    threshold = revalidate_depth_path_threshold_contract(threshold_contract)
    if resolved_report.threshold_contract.content_id != threshold.content_id:
        raise DepthPathError("threshold contract does not match the report")
    resolved_preprocessing = (
        resolved_report.preprocessing_id
        if preprocessing_id is None
        else _text(preprocessing_id, "preprocessing_id")
    )
    resolved_estimator = (
        resolved_report.estimator_id
        if estimator_id is None
        else _text(estimator_id, "estimator_id")
    )
    if resolved_preprocessing != resolved_report.preprocessing_id:
        raise DepthPathError("preprocessing identity does not match the report")
    if resolved_estimator != resolved_report.estimator_id:
        raise DepthPathError("estimator identity does not match the report")

    if (
        resolved_report.premise_status
        is ReverseMartingalePremiseStatus.PROVED_FINITE_REGISTERED_PATH
    ):
        second = resolved_report.target_second_moment
        maximum_squared = resolved_report.path_maximum_abs**2
        threshold_squared = threshold.multiplier**2 * second
        probability_bound = min(
            Fraction(1, 1),
            Fraction(1, 1) / (threshold.multiplier**2),
        )
        status = (
            DepthPathCalibrationStatus.BOUND_AVAILABLE_CONDITIONAL_PROVED_PREMISE
        )
        path_exceeds = maximum_squared >= threshold_squared
    else:
        second = None
        maximum_squared = None
        threshold_squared = None
        probability_bound = None
        status = DepthPathCalibrationStatus.MATCHED_MOCKS_REQUIRED
        path_exceeds = None
    return _build_depth_path_doob_calibration_contract(
        calibration_id=calibration_id,
        report=resolved_report,
        threshold_contract=threshold,
        preprocessing_id=resolved_preprocessing,
        estimator_id=resolved_estimator,
        status=status,
        probability_upper_bound=probability_bound,
        target_second_moment=second,
        threshold_squared=threshold_squared,
        path_maximum_squared=maximum_squared,
        path_exceeds_threshold=path_exceeds,
        event_comparison=PR284_EVENT_COMPARISON,
    )


__all__ = [
    "build_depth_path_doob_calibration",
    "build_depth_path_matched_mock_plan",
    "build_depth_path_reverse_martingale_report",
    "build_unproved_depth_path_reverse_martingale_report",
]
