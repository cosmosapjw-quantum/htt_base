#!/usr/bin/env python3
"""Independent exact-arithmetic and constructor-bypass oracle for PR-284."""

from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import sys


ROOT = Path.cwd().resolve()
for relative in ("htt", "htt/htt", "htt/src"):
    sys.path.insert(0, str(ROOT / relative))

from common.depth_path_calibration import (  # noqa: E402
    ReverseMartingalePremiseStatus,
    _build_depth_path_reverse_martingale_report_contract,
    build_depth_path_finite_target_law,
    build_depth_path_selection_contract,
    build_depth_path_threshold_contract,
)
from htt.infer.depth_path_calibration import (  # noqa: E402
    build_depth_path_doob_calibration,
)


def frac(text: str) -> Fraction:
    return Fraction(text)


def conditional_values(
    weights: tuple[Fraction, ...],
    target: tuple[Fraction, ...],
    labels: tuple[str, ...],
) -> tuple[Fraction, ...]:
    mass: dict[str, Fraction] = {}
    weighted: dict[str, Fraction] = {}
    for probability, value, label in zip(weights, target, labels, strict=True):
        mass[label] = mass.get(label, Fraction()) + probability
        weighted[label] = weighted.get(label, Fraction()) + probability * value
    means = {label: weighted[label] / mass[label] for label in mass}
    return tuple(means[label] for label in labels)


def check_receipt_exactness() -> dict[str, str | bool]:
    receipt = json.loads(
        (ROOT / "docs/generated/pr284_depth_path_doob_receipt.json").read_text()
    )
    fixture = receipt["proved_fixture"]
    law = fixture["finite_target_law"]
    report = fixture["report"]
    calibration = fixture["calibration"]
    weights = tuple(frac(value) for value in law["weights"])
    target = tuple(frac(value) for value in law["common_target"])
    partitions = tuple(tuple(row) for row in report["path_partitions"])

    assert sum(weights, Fraction()) == 1
    assert sum(p * x for p, x in zip(weights, target, strict=True)) == 0
    second = sum(p * x * x for p, x in zip(weights, target, strict=True))
    assert second == frac(report["target_second_moment"])

    for fine, coarse in zip(partitions[:-1], partitions[1:], strict=True):
        fine_to_coarse: dict[str, str] = {}
        for fine_label, coarse_label in zip(fine, coarse, strict=True):
            previous = fine_to_coarse.setdefault(fine_label, coarse_label)
            assert previous == coarse_label

    conditionals = tuple(
        conditional_values(weights, target, partition) for partition in partitions
    )
    selected = report["selection_contract"]["selected_atom_index"]
    path_values = tuple(row[selected] for row in conditionals)
    maximum = max(abs(value) for value in path_values)
    assert path_values == tuple(frac(value) for value in report["path_values"])
    assert maximum == frac(report["path_maximum_abs"])

    multiplier = frac(report["threshold_contract"]["multiplier"])
    threshold_squared = multiplier * multiplier * second
    bound = min(Fraction(1), Fraction(1) / (multiplier * multiplier))
    atom_maxima = tuple(
        max(abs(row[index]) for row in conditionals) for index in range(len(target))
    )
    event_probability = sum(
        probability
        for probability, atom_maximum in zip(weights, atom_maxima, strict=True)
        if atom_maximum * atom_maximum >= threshold_squared
    )
    assert threshold_squared == frac(calibration["threshold_squared"])
    assert bound == frac(calibration["probability_upper_bound"])
    assert event_probability == frac(fixture["exact_event_probability"])
    assert event_probability <= bound
    assert calibration["path_exceeds_threshold"] is (
        maximum * maximum >= threshold_squared
    )

    fallback = receipt["unproved_fixture"]
    assert fallback["matched_mocks_executed"] is False
    assert fallback["probability_bound"] is None
    assert fallback["calibration"]["probability_upper_bound"] is None
    assert fallback["calibration"]["status"] == "MATCHED_MOCKS_REQUIRED"
    return {
        "centered": True,
        "second_moment": str(second),
        "selected_path_maximum": str(maximum),
        "threshold_squared": str(threshold_squared),
        "event_probability": str(event_probability),
        "doob_bound": str(bound),
        "matched_mock_abstention": True,
    }


def reproduce_constructor_bypass() -> dict[str, str | bool]:
    law = build_depth_path_finite_target_law(
        law_id="FORGED-NONCENTERED-LAW",
        common_target_id="FORGED-NONCENTERED-TARGET",
        atom_ids=("atom-a", "atom-b"),
        weights=(Fraction(1, 2), Fraction(1, 2)),
        common_target=(Fraction(1), Fraction(3)),
        registration_id="caller-text-only",
    )
    selection = build_depth_path_selection_contract(
        selection_id="FORGED-SELECTION",
        finite_target_law=law,
        selected_atom_id="atom-a",
        selected_atom_index=0,
        selection_rule_id="caller-text-only",
        registration_id="caller-text-only",
    )
    threshold = build_depth_path_threshold_contract(
        contract_id="FORGED-THRESHOLD",
        multiplier=Fraction(2),
        registration_id="caller-text-only",
    )
    true_mean = sum(
        probability * value
        for probability, value in zip(law.weights, law.common_target, strict=True)
    )
    true_second = sum(
        probability * value * value
        for probability, value in zip(law.weights, law.common_target, strict=True)
    )
    assert true_mean == 2
    assert true_second == 5

    report = _build_depth_path_reverse_martingale_report_contract(
        report_id="FORGED-PROVED-REPORT",
        path_content_id="sha256:not-a-real-path",
        stratum_content_ids=("sha256:not-a-real-stratum-1", "sha256:not-a-real-stratum-2"),
        threshold_contract=threshold,
        filtration_id="caller-text-only",
        filtration_direction="DECREASING",
        preprocessing_id="caller-text-only",
        estimator_id="caller-text-only",
        premise_evidence_id="caller-text-only",
        premise_status=ReverseMartingalePremiseStatus.PROVED_FINITE_REGISTERED_PATH,
        finite_target_law=law,
        selection_contract=selection,
        path_partitions=(("fine-a", "fine-b"), ("coarse", "coarse")),
        sigma_field_ids=("caller-F1", "caller-F2"),
        path_values=(Fraction(1), Fraction(0)),
        path_maximum_abs=Fraction(1),
        path_maximum_content_id="sha256:caller-supplied-path-maximum",
        target_second_moment=Fraction(1),
        exact_tower_equalities=(True,),
        exact_tower_report_content_id="sha256:caller-supplied-tower",
        unresolved_reasons=(),
        matched_mock_plan=None,
    )
    calibration = build_depth_path_doob_calibration(
        calibration_id="FORGED-FREE-BOUND",
        report=report,
        threshold_contract=threshold,
    )
    assert report.premise_status is ReverseMartingalePremiseStatus.PROVED_FINITE_REGISTERED_PATH
    assert report.target_second_moment == 1 != true_second
    assert calibration.probability_upper_bound == Fraction(1, 4)
    return {
        "bypass_reproduced": True,
        "true_mean": str(true_mean),
        "true_second_moment": str(true_second),
        "sealed_false_second_moment": str(report.target_second_moment),
        "emitted_bound": str(calibration.probability_upper_bound),
        "emitted_status": calibration.status.value,
    }


def main() -> int:
    payload = {
        "oracle": "A-PR284-PHYSMATH-CONSTRUCTOR-BYPASS-V1",
        "receipt_exactness": check_receipt_exactness(),
        "constructor_bypass": reproduce_constructor_bypass(),
        "verdict": "BLOCKER_REPRODUCED",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
