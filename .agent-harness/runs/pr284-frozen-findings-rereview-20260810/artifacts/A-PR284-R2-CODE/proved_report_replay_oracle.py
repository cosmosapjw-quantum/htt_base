"""Independent affected-cell oracle for the repaired PR-284 report replay."""

from __future__ import annotations

from copy import copy
from fractions import Fraction
import json
from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(ROOT / "htt/src"), str(ROOT / "htt"), str(ROOT)]
fixtures = runpy.run_path(
    ROOT / "tests/contracts/test_depth_path_doob_calibration.py",
    run_name="pr284_r2_code_oracle_fixture",
)

import common.depth_path_calibration as contracts
from common.depth_path import DepthPathError
from htt import infer as public_api
from htt.infer import depth_path_calibration as implementation


def report_kwargs(report: contracts.DepthPathReverseMartingaleReport) -> dict[str, object]:
    return {
        "report_id": report.report_id,
        "path_content_id": report.path_content_id,
        "stratum_content_ids": report.stratum_content_ids,
        "threshold_contract": report.threshold_contract,
        "filtration_id": report.filtration_id,
        "filtration_direction": report.filtration_direction,
        "preprocessing_id": report.preprocessing_id,
        "estimator_id": report.estimator_id,
        "premise_evidence_id": report.premise_evidence_id,
        "premise_status": report.premise_status,
        "finite_target_law": report.finite_target_law,
        "selection_contract": report.selection_contract,
        "path_partitions": report.path_partitions,
        "sigma_field_ids": report.sigma_field_ids,
        "path_values": report.path_values,
        "path_maximum_abs": report.path_maximum_abs,
        "path_maximum_content_id": report.path_maximum_content_id,
        "target_second_moment": report.target_second_moment,
        "exact_tower_equalities": report.exact_tower_equalities,
        "exact_tower_report_content_id": report.exact_tower_report_content_id,
        "unresolved_reasons": report.unresolved_reasons,
        "matched_mock_plan": report.matched_mock_plan,
    }


def expect_constructor_rejection(case_id: str, **overrides: object) -> dict[str, object]:
    kwargs = report_kwargs(authentic_report)
    kwargs.update(overrides)
    try:
        contracts._build_depth_path_reverse_martingale_report_contract(**kwargs)
    except DepthPathError as exc:
        return {"accepted": False, "error_type": type(exc).__name__, "error": str(exc)}
    raise AssertionError(f"constructor mutation survived: {case_id}")


def expect_revalidation_rejection(case_id: str, **overrides: object) -> dict[str, object]:
    mutant = copy(authentic_report)
    for name, value in overrides.items():
        object.__setattr__(mutant, name, value)
    object.__setattr__(
        mutant,
        "_identity_seal",
        contracts._sha256_payload(mutant._payload_unchecked()),
    )
    try:
        contracts.revalidate_depth_path_reverse_martingale_report(mutant)
    except DepthPathError as exc:
        if "identity drifted" in str(exc):
            raise AssertionError(f"{case_id} was stopped only by the content seal") from exc
        return {"accepted": False, "error_type": type(exc).__name__, "error": str(exc)}
    raise AssertionError(f"resealed revalidation mutation survived: {case_id}")


authentic_report = fixtures["_proved_report"]()
authentic_replay = contracts.revalidate_depth_path_reverse_martingale_report(
    authentic_report
)
authentic_calibration = public_api.build_depth_path_doob_calibration(
    calibration_id="PR284-R2-AUTHENTIC-CALIBRATION",
    report=authentic_replay,
    threshold_contract=fixtures["_threshold"](),
)
assert authentic_report.path_values == (Fraction(-3), Fraction(-2), Fraction(0))
assert authentic_report.path_maximum_abs == Fraction(3)
assert authentic_report.target_second_moment == Fraction(5)
assert authentic_calibration.probability_upper_bound == Fraction(1, 4)
assert public_api.build_depth_path_doob_calibration is implementation.build_depth_path_doob_calibration
assert public_api.DepthPathReverseMartingaleReport is contracts.DepthPathReverseMartingaleReport

noncentered_law = fixtures["_finite_law"](target=(0, 1, 2, 3))
noncentered_selection = fixtures["_selection"](noncentered_law)
selected_atom_3 = fixtures["_selection"](
    authentic_report.finite_target_law,
    selected_atom_index=3,
)

constructor_cases = {
    "noncentered_target": expect_constructor_rejection(
        "noncentered_target",
        finite_target_law=noncentered_law,
        selection_contract=noncentered_selection,
    ),
    "second_moment": expect_constructor_rejection(
        "second_moment",
        target_second_moment=Fraction(1),
    ),
    "decreasing_filtration": expect_constructor_rejection(
        "decreasing_filtration",
        path_partitions=(
            ("left", "left", "right", "right"),
            ("x", "y", "x", "y"),
            ("all", "all", "all", "all"),
        ),
    ),
    "selected_atom_path": expect_constructor_rejection(
        "selected_atom_path",
        selection_contract=selected_atom_3,
    ),
    "path_values": expect_constructor_rejection(
        "path_values",
        path_values=(Fraction(0), Fraction(0), Fraction(0)),
        path_maximum_abs=Fraction(0),
    ),
    "path_maximum": expect_constructor_rejection(
        "path_maximum",
        path_maximum_abs=Fraction(4),
    ),
    "tower_identity": expect_constructor_rejection(
        "tower_identity",
        exact_tower_report_content_id="sha256:caller-supplied-tower",
    ),
    "path_maximum_identity": expect_constructor_rejection(
        "path_maximum_identity",
        path_maximum_content_id="sha256:caller-supplied-maximum",
    ),
}

revalidation_cases = {
    "resealed_second_moment": expect_revalidation_rejection(
        "resealed_second_moment",
        target_second_moment=Fraction(1),
    ),
    "resealed_filtration": expect_revalidation_rejection(
        "resealed_filtration",
        path_partitions=(
            ("left", "left", "right", "right"),
            ("x", "y", "x", "y"),
            ("all", "all", "all", "all"),
        ),
    ),
    "resealed_path_values": expect_revalidation_rejection(
        "resealed_path_values",
        path_values=(Fraction(0), Fraction(0), Fraction(0)),
        path_maximum_abs=Fraction(0),
    ),
    "resealed_path_maximum": expect_revalidation_rejection(
        "resealed_path_maximum",
        path_maximum_abs=Fraction(4),
    ),
    "resealed_tower_identity": expect_revalidation_rejection(
        "resealed_tower_identity",
        exact_tower_report_content_id="sha256:caller-supplied-tower",
    ),
    "resealed_path_maximum_identity": expect_revalidation_rejection(
        "resealed_path_maximum_identity",
        path_maximum_content_id="sha256:caller-supplied-maximum",
    ),
}

payload = {
    "schema": "htt.pr284.r2_code_proved_report_replay_oracle.v1",
    "authentic_public_api": {
        "report_revalidated": authentic_replay.content_id == authentic_report.content_id,
        "path_values": [str(value) for value in authentic_report.path_values],
        "path_maximum_abs": str(authentic_report.path_maximum_abs),
        "target_second_moment": str(authentic_report.target_second_moment),
        "probability_upper_bound": str(authentic_calibration.probability_upper_bound),
        "factory_export_identity": True,
        "report_export_identity": True,
    },
    "constructor_cases": constructor_cases,
    "resealed_revalidation_cases": revalidation_cases,
}

assert all(not row["accepted"] for row in constructor_cases.values())
assert all(not row["accepted"] for row in revalidation_cases.values())
encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
Path(__file__).with_suffix(".json").write_text(encoded, encoding="utf-8")
print(encoded, end="")
