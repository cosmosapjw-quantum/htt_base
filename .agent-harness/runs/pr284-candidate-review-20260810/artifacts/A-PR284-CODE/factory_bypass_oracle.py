"""Reproduce the PR-284 proved-report private-builder bypass."""

from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(ROOT / "htt/src"), str(ROOT / "htt"), str(ROOT)]

fixtures = runpy.run_path(
    ROOT / "tests/contracts/test_depth_path_doob_calibration.py",
    run_name="pr284_code_oracle_fixture",
)

import common.depth_path_calibration as contracts
from common.depth_path import DepthPathError
from htt import infer as public_api
from htt.infer import depth_path_calibration as implementation


path = fixtures["_path"]()
threshold = fixtures["_threshold"]()
law = fixtures["_finite_law"](target=(0, 1, 2, 3))
selection = fixtures["_selection"](law)
invalid_partitions = (
    ("left", "left", "right", "right"),
    ("x", "y", "x", "y"),
    ("all", "all", "all", "all"),
)

try:
    implementation.build_depth_path_reverse_martingale_report(
        report_id="PR284-ORACLE-PUBLIC-REJECTION",
        path=path,
        threshold_contract=threshold,
        finite_target_law=law,
        selection_contract=selection,
        path_partitions=invalid_partitions,
        sigma_field_ids=("sigma-1", "sigma-2", "sigma-3"),
        filtration_id="oracle-invalid-filtration",
        preprocessing_id="oracle-preprocessing",
        estimator_id="oracle-estimator",
        premise_evidence_id="oracle-unproved-evidence",
    )
except DepthPathError as exc:
    public_rejection = str(exc)
else:
    raise AssertionError("public proved factory accepted an uncentered target")

assert "centered" in public_rejection
assert "_build_depth_path_reverse_martingale_report_contract" not in contracts.__all__
assert hasattr(contracts, "_build_depth_path_reverse_martingale_report_contract")

forged_report = contracts._build_depth_path_reverse_martingale_report_contract(
    report_id="PR284-ORACLE-FORGED-REPORT",
    path_content_id=path.content_id,
    stratum_content_ids=tuple(stratum.content_id for stratum in path.strata),
    threshold_contract=threshold,
    filtration_id="oracle-invalid-filtration",
    filtration_direction="DECREASING",
    preprocessing_id="oracle-preprocessing",
    estimator_id="oracle-estimator",
    premise_evidence_id="oracle-unproved-evidence",
    premise_status=contracts.ReverseMartingalePremiseStatus.PROVED_FINITE_REGISTERED_PATH,
    finite_target_law=law,
    selection_contract=selection,
    path_partitions=invalid_partitions,
    sigma_field_ids=("sigma-1", "sigma-2", "sigma-3"),
    path_values=(Fraction(0), Fraction(0), Fraction(0)),
    path_maximum_abs=Fraction(0),
    path_maximum_content_id="oracle-caller-supplied-maximum",
    target_second_moment=Fraction(1),
    exact_tower_equalities=(True, True),
    exact_tower_report_content_id="oracle-caller-supplied-tower",
    unresolved_reasons=(),
    matched_mock_plan=None,
)
contracts.revalidate_depth_path_reverse_martingale_report(forged_report)

forged_calibration = public_api.build_depth_path_doob_calibration(
    calibration_id="PR284-ORACLE-FORGED-CALIBRATION",
    report=forged_report,
    threshold_contract=threshold,
)
assert forged_calibration.status is contracts.DepthPathCalibrationStatus.BOUND_AVAILABLE_CONDITIONAL_PROVED_PREMISE
assert forged_calibration.probability_upper_bound == Fraction(1, 4)
assert forged_calibration.target_second_moment == Fraction(1)
assert public_api.build_depth_path_doob_calibration is implementation.build_depth_path_doob_calibration
assert public_api.DepthPathReverseMartingaleReport is contracts.DepthPathReverseMartingaleReport

payload = {
    "schema": "htt.pr284.code_factory_bypass_oracle.v1",
    "public_factory": {
        "accepted_invalid_premise": False,
        "error": public_rejection,
    },
    "private_builder_surface": {
        "module_attribute_reachable": True,
        "listed_in_all": False,
        "report_revalidation_accepted": True,
        "noncentered_target": [str(value) for value in law.common_target],
        "invalid_partitions": [list(row) for row in invalid_partitions],
        "caller_supplied_tower_equalities": list(forged_report.exact_tower_equalities),
        "caller_supplied_second_moment": str(forged_report.target_second_moment),
    },
    "public_calibration": {
        "status": forged_calibration.status.value,
        "probability_upper_bound": str(forged_calibration.probability_upper_bound),
        "target_second_moment": str(forged_calibration.target_second_moment),
    },
    "export_identity": {
        "calibration_factory_exact": True,
        "report_type_exact": True,
    },
}

encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
Path(__file__).with_suffix(".json").write_text(encoded, encoding="utf-8")
print(encoded, end="")
