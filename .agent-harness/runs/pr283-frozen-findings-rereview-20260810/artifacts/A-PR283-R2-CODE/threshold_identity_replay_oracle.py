"""Independent executable oracle for the frozen PR-283 threshold repair."""

from __future__ import annotations

from copy import copy
import json
from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(ROOT / "htt/src"), str(ROOT / "htt"), str(ROOT)]
namespace = runpy.run_path(
    ROOT / "tests/contracts/test_weak_identification.py",
    run_name="pr283_r2_code_oracle_fixture",
)

OpenSetResponseError = namespace["OpenSetResponseError"]
OpenSetClassificationStatus = namespace["OpenSetClassificationStatus"]
SourceSeparationGateStatus = namespace["SourceSeparationGateStatus"]
source_separation_gate_from_pr256 = namespace["source_separation_gate_from_pr256"]
source_fixture = namespace["_source_fixture"]
normalizer = namespace["_normalizer"]
thresholds = namespace["_thresholds"]
classify = namespace["_classify"]

report, classes, equivalence, default_gate, covariance = source_fixture(
    global_amplitude=0.005,
)
default_classification = classify(
    classes,
    equivalence,
    default_gate,
    covariance,
)
assert default_gate.status is SourceSeparationGateStatus.WEAKLY_IDENTIFIED
assert default_classification.status is OpenSetClassificationStatus.TYPE_UNIDENTIFIED
assert default_classification.candidate_class_id is None

recreated_registered_contract = thresholds()
replayed_gate = source_separation_gate_from_pr256(
    report,
    classes=classes,
    covariance=covariance,
    nuisance_tangent=None,
    normalizer=normalizer(),
    threshold_contract=recreated_registered_contract,
)
assert replayed_gate == default_gate

outcomes: dict[str, object] = {
    "schema": "htt.pr283.r2_code_threshold_identity_oracle.v1",
    "default": {
        "gate_status": default_gate.status.value,
        "classification_status": default_classification.status.value,
        "candidate_class_id": default_classification.candidate_class_id,
        "threshold_contract_id": (
            default_gate.source_separation_decision.threshold_contract.contract_id
        ),
    },
    "content_equivalent_registered_contract": {
        "accepted": True,
        "equal_gate": replayed_gate == default_gate,
        "threshold_contract_id": recreated_registered_contract.contract_id,
    },
}

for case_id, mutant_report, mutant_normalizer, mutant_threshold in (
    (
        "alternate_singular_threshold",
        report,
        normalizer(),
        thresholds(relative_singular=0.001),
    ),
    (
        "source_report_drift",
        copy(report),
        normalizer(),
        thresholds(),
    ),
    (
        "normalizer_coordinate_map_drift",
        report,
        normalizer(global_scale=0.5),
        thresholds(),
    ),
):
    if case_id == "source_report_drift":
        object.__setattr__(mutant_report, "joint_singular_values", (1.0, 1.0))
    try:
        source_separation_gate_from_pr256(
            mutant_report,
            classes=classes,
            covariance=covariance,
            nuisance_tangent=None,
            normalizer=mutant_normalizer,
            threshold_contract=mutant_threshold,
        )
    except OpenSetResponseError as exc:
        outcomes[case_id] = {
            "accepted": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    else:
        raise AssertionError(f"{case_id} did not fail closed")

assert "registered PR-283" in outcomes["alternate_singular_threshold"]["error"]
assert "exact replay" in outcomes["source_report_drift"]["error"]
assert "exact replay" in outcomes["normalizer_coordinate_map_drift"]["error"]
encoded = json.dumps(outcomes, sort_keys=True, indent=2) + "\n"
output = Path(__file__).with_suffix(".json")
output.write_text(encoded, encoding="utf-8")
print(encoded, end="")
