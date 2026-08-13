#!/usr/bin/env python3
"""Affected-cell exact-math rereview oracle for the frozen PR-284 R2 candidate."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path.cwd().resolve()
for relative in ("htt", "htt/htt", "htt/src"):
    sys.path.insert(0, str(ROOT / relative))

from common.depth_path import DepthPathError  # noqa: E402
from common.depth_path_calibration import (  # noqa: E402
    ReverseMartingalePremiseStatus,
    _build_depth_path_reverse_martingale_report_contract,
    build_depth_path_finite_target_law,
    build_depth_path_selection_contract,
    build_depth_path_threshold_contract,
)
from common.vector_tensor_statistical_foundations import (  # noqa: E402
    certify_finite_partition_tower,
)
from htt.infer.depth_path_calibration import (  # noqa: E402
    build_depth_path_doob_calibration,
)


def canonical_id(payload: object) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


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


def exact_components(
    *,
    target: tuple[Fraction, ...] = (Fraction(-1), Fraction(1)),
    partitions: tuple[tuple[str, ...], ...] = (
        ("atom-a", "atom-b"),
        ("all", "all"),
    ),
) -> dict[str, object]:
    weights = (Fraction(1, 2), Fraction(1, 2))
    law = build_depth_path_finite_target_law(
        law_id="R2-ORACLE-LAW",
        common_target_id="R2-ORACLE-TARGET",
        atom_ids=("atom-a", "atom-b"),
        weights=weights,
        common_target=target,
        registration_id="R2-ORACLE-LAW-REGISTRATION",
    )
    selection = build_depth_path_selection_contract(
        selection_id="R2-ORACLE-SELECTION",
        finite_target_law=law,
        selected_atom_id="atom-a",
        selected_atom_index=0,
        selection_rule_id="R2-ORACLE-FIRST-ATOM",
        registration_id="R2-ORACLE-SELECTION-REGISTRATION",
    )
    threshold = build_depth_path_threshold_contract(
        contract_id="R2-ORACLE-THRESHOLD",
        multiplier=Fraction(2),
        registration_id="R2-ORACLE-THRESHOLD-REGISTRATION",
    )
    conditionals = tuple(
        conditional_values(weights, target, partition) for partition in partitions
    )
    path_values = tuple(row[0] for row in conditionals)
    maximum = max(abs(value) for value in path_values)
    second = sum(
        probability * value * value
        for probability, value in zip(weights, target, strict=True)
    )
    tower = certify_finite_partition_tower(
        weights=weights,
        common_target=target,
        partitions=tuple(reversed(partitions)),
    )
    tower_id = canonical_id(
        {
            "atom_count": tower.atom_count,
            "conditional_expectations": [
                list(row) for row in tower.conditional_expectations
            ],
            "exact_equalities": list(tower.exact_equalities),
            "rung_count": tower.rung_count,
            "schema": "PR284_EXACT_FINITE_TOWER_REPLAY_V1",
        }
    )
    maximum_id = canonical_id(
        {
            "path_values": [
                f"{value.numerator}/{value.denominator}" for value in path_values
            ],
            "selected_atom_id": selection.selected_atom_id,
            "selection_contract_content_id": selection.content_id,
            "value": f"{maximum.numerator}/{maximum.denominator}",
        }
    )
    return {
        "law": law,
        "selection": selection,
        "threshold": threshold,
        "partitions": partitions,
        "path_values": path_values,
        "maximum": maximum,
        "second": second,
        "tower_equalities": tuple(tower.exact_equalities),
        "tower_id": tower_id,
        "maximum_id": maximum_id,
    }


def build_raw_report(
    components: dict[str, object],
    *,
    path_content_id: str = "sha256:no-registered-depth-path",
    stratum_content_ids: tuple[str, ...] = (
        "sha256:no-registered-stratum-1",
        "sha256:no-registered-stratum-2",
    ),
    target_second_moment: Fraction | None = None,
    path_partitions: tuple[tuple[str, ...], ...] | None = None,
):
    partitions = (
        components["partitions"] if path_partitions is None else path_partitions
    )
    return _build_depth_path_reverse_martingale_report_contract(
        report_id="R2-ORACLE-RAW-PROVED-REPORT",
        path_content_id=path_content_id,
        stratum_content_ids=stratum_content_ids,
        threshold_contract=components["threshold"],
        filtration_id="R2-ORACLE-CALLER-FILTRATION",
        filtration_direction="DECREASING",
        preprocessing_id="R2-ORACLE-CALLER-PREPROCESSING",
        estimator_id="R2-ORACLE-CALLER-ESTIMATOR",
        premise_evidence_id="R2-ORACLE-CALLER-PREMISE",
        premise_status=ReverseMartingalePremiseStatus.PROVED_FINITE_REGISTERED_PATH,
        finite_target_law=components["law"],
        selection_contract=components["selection"],
        path_partitions=partitions,
        sigma_field_ids=tuple(
            f"R2-ORACLE-CALLER-F{index + 1}" for index in range(len(partitions))
        ),
        path_values=components["path_values"],
        path_maximum_abs=components["maximum"],
        path_maximum_content_id=components["maximum_id"],
        target_second_moment=(
            components["second"]
            if target_second_moment is None
            else target_second_moment
        ),
        exact_tower_equalities=components["tower_equalities"],
        exact_tower_report_content_id=components["tower_id"],
        unresolved_reasons=(),
        matched_mock_plan=None,
    )


def expect_rejected(operation, marker: str) -> str:
    try:
        operation()
    except DepthPathError as exc:
        message = str(exc)
        assert marker in message, (marker, message)
        return message
    raise AssertionError(f"forgery was accepted; expected marker {marker!r}")


def check_named_remediations() -> dict[str, str]:
    noncentered = exact_components(target=(Fraction(1), Fraction(3)))
    noncentered_error = expect_rejected(
        lambda: build_raw_report(noncentered),
        "exactly centered",
    )

    centered = exact_components()
    second_error = expect_rejected(
        lambda: build_raw_report(centered, target_second_moment=Fraction(5)),
        "second moment does not match",
    )

    def nonfiltration() -> object:
        bad_partitions = (("left", "left"), ("x", "y"))
        bad = dict(centered)
        bad["partitions"] = bad_partitions
        bad["path_values"] = (Fraction(0), Fraction(-1))
        bad["maximum"] = Fraction(1)
        return build_raw_report(bad, path_partitions=bad_partitions)

    filtration_error = expect_rejected(nonfiltration, "decreasing filtration")
    return {
        "noncentered": noncentered_error,
        "false_second_moment": second_error,
        "nonfiltration": filtration_error,
    }


def check_authentic_receipt() -> dict[str, str | bool]:
    receipt = json.loads(
        (ROOT / "docs/generated/pr284_depth_path_doob_receipt.json").read_text()
    )
    fixture = receipt["proved_fixture"]
    law = fixture["finite_target_law"]
    report = fixture["report"]
    calibration = fixture["calibration"]
    weights = tuple(Fraction(value) for value in law["weights"])
    target = tuple(Fraction(value) for value in law["common_target"])
    partitions = tuple(tuple(row) for row in report["path_partitions"])
    conditionals = tuple(
        conditional_values(weights, target, partition) for partition in partitions
    )
    mean = sum(p * x for p, x in zip(weights, target, strict=True))
    second = sum(p * x * x for p, x in zip(weights, target, strict=True))
    selected = report["selection_contract"]["selected_atom_index"]
    path_values = tuple(row[selected] for row in conditionals)
    maximum = max(abs(value) for value in path_values)
    multiplier = Fraction(report["threshold_contract"]["multiplier"])
    threshold_squared = multiplier * multiplier * second
    bound = min(Fraction(1), Fraction(1) / (multiplier * multiplier))
    event_probability = sum(
        probability
        for index, probability in enumerate(weights)
        if max(abs(row[index]) for row in conditionals) ** 2 >= threshold_squared
    )
    assert mean == 0
    assert second == Fraction(report["target_second_moment"])
    assert path_values == tuple(Fraction(value) for value in report["path_values"])
    assert maximum == Fraction(report["path_maximum_abs"])
    assert threshold_squared == Fraction(calibration["threshold_squared"])
    assert bound == Fraction(calibration["probability_upper_bound"])
    assert event_probability == Fraction(fixture["exact_event_probability"])
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
        "mean_zero": True,
        "second_moment": str(second),
        "tower_equalities": all(report["exact_tower_equalities"]),
        "selected_path_maximum": str(maximum),
        "threshold_squared": str(threshold_squared),
        "inclusive_event_probability": str(event_probability),
        "doob_bound": str(bound),
        "matched_mock_abstention": True,
    }


def reproduce_residual_path_binding_bypass() -> dict[str, str | bool]:
    components = exact_components()
    report = build_raw_report(components)
    calibration = build_depth_path_doob_calibration(
        calibration_id="R2-ORACLE-FREE-PATH-BOUND",
        report=report,
        threshold_contract=components["threshold"],
    )
    assert report.path_content_id == "sha256:no-registered-depth-path"
    assert report.stratum_content_ids == (
        "sha256:no-registered-stratum-1",
        "sha256:no-registered-stratum-2",
    )
    assert calibration.probability_upper_bound == Fraction(1, 4)
    return {
        "residual_bypass_reproduced": True,
        "unverified_path_content_id": report.path_content_id,
        "unverified_stratum_ids_accepted": True,
        "caller_sigma_fields_accepted": True,
        "emitted_status": calibration.status.value,
        "emitted_bound": str(calibration.probability_upper_bound),
    }


def main() -> int:
    payload = {
        "oracle": "A-PR284-R2-PHYSMATH-AFFECTED-CELLS-V1",
        "named_remediations": check_named_remediations(),
        "authentic_receipt": check_authentic_receipt(),
        "residual_path_binding": reproduce_residual_path_binding_bypass(),
        "verdict": "RESIDUAL_BLOCKER_REPRODUCED",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
