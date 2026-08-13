#!/usr/bin/env python3
"""Independent proper-subset and claim-ceiling oracle for PR-284 R4."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

from common.depth_path import DepthPathError, build_depth_path, build_mask_stratum, build_transport_kernel
from common.depth_path_calibration import DepthPathCalibrationStatus, build_depth_path_finite_target_law, build_depth_path_selection_contract, build_depth_path_threshold_contract
from common.sky_support import build_sky_support_from_mask
from htt.infer.depth_path_calibration import build_depth_path_doob_calibration, build_depth_path_matched_mock_plan, build_depth_path_reverse_martingale_report, build_unproved_depth_path_reverse_martingale_report


ROOT = Path(__file__).resolve().parents[5]
SPEC_PATH = ROOT / "docs/research_program/post_pr275/pr284_spec.yaml"
POLICY_PATH = ROOT / "docs/research_program/post_pr275/pr284_publication_policy.json"
RECEIPT_PATH = ROOT / "docs/generated/pr284_depth_path_doob_receipt.json"


def _canonical_hash(payload: dict[str, object], omitted: str) -> str:
    value = dict(payload)
    value.pop(omitted, None)
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _stratum(tag: str, depth: int, kept: tuple[int, ...]):
    mask = np.zeros(2, dtype=bool)
    mask[list(kept)] = True
    support = build_sky_support_from_mask(
        mask,
        coordinate_frame="GALACTIC",
        completeness_status="synthetic_fixture_complete",
        selection_mode=f"r4-oracle-{tag}",
        mock_coverage_status="synthetic_fixture_only",
        pixelization="PR284_R4_ORACLE_PIXELS",
    )
    return build_mask_stratum(
        stratum_id=f"R4-ORACLE-{tag}",
        depth_coordinate=depth,
        depth_unit="synthetic_depth",
        support_unit_ids=tuple(f"pixel-{index}" for index in kept),
        support_universe_size=2,
        sky_support=support,
        selection_id=f"sha256:r4-selection-{tag}",
        covariance_id=f"sha256:r4-covariance-{tag}",
        source_artifact_id=f"sha256:r4-source-{tag}",
        feature_names=("centered_scalar",),
        feature_unit="dimensionless_diagnostic",
        assumptions=("fresh R4 synthetic support oracle",),
    )


def _path(tag: str, target_kept: tuple[int, ...]):
    source = _stratum(f"{tag}-SOURCE", 1, (0, 1))
    target = _stratum(f"{tag}-TARGET", 2, target_kept)
    kernel = build_transport_kernel(
        transport_id=f"R4-ORACLE-{tag}-KERNEL",
        source=source,
        target=target,
        matrix=((1.0,),),
        mask_transport_id=f"sha256:r4-mask-{tag}",
        selection_transport_id=f"sha256:r4-selection-{tag}",
        covariance_transport_id=f"sha256:r4-covariance-{tag}",
        method_id="PR284-R4-ORACLE-IDENTITY",
        assumptions=("synthetic identity transport",),
    )
    return build_depth_path(
        path_id=f"PR284-R4-ORACLE-{tag}",
        strata=(source, target),
        kernels=(kernel,),
    )


def _law_and_selection():
    law = build_depth_path_finite_target_law(
        law_id="PR284-R4-ORACLE-LAW",
        common_target_id="PR284-R4-ORACLE-TARGET",
        atom_ids=("negative", "positive"),
        weights=(Fraction(1, 2), Fraction(1, 2)),
        common_target=(Fraction(-1), Fraction(1)),
        registration_id="sha256:r4-law-preregistered",
    )
    selection = build_depth_path_selection_contract(
        selection_id="PR284-R4-ORACLE-SELECTION",
        finite_target_law=law,
        selected_atom_id="negative",
        selected_atom_index=0,
        selection_rule_id="sha256:r4-first-atom-rule",
        registration_id="sha256:r4-selection-preregistered",
    )
    return law, selection


def main() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))

    expected_boundary = {
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "observed_data_executed": False,
        "public_use": False,
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
    }
    for key, expected in expected_boundary.items():
        assert spec[key] == receipt[key] == expected
    assert policy["claim_ceiling"] == "diagnostic_only"
    assert policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert spec["owner"] == receipt["owner"] == "HTT"
    assert set(spec["contributors"]) == set(receipt["contributors"]) == {"COMMON", "OBSSTAT", "MIO"}
    assert spec["runtime_contract"]["ownership"]["COMMON"].startswith("immutable path")
    assert spec["runtime_contract"]["ownership"]["HTT"] == "premise evaluation and calibration decision"
    assert spec["runtime_contract"]["ownership"]["MIO"] == "diagnostic path-consistency consumers only"

    assert receipt["receipt_content_sha256"] == _canonical_hash(receipt, "receipt_content_sha256")
    for binding in receipt["source_bindings"]:
        path = binding["path"]
        assert not path.startswith((".agent-harness/runs/", ".prguard/"))
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == binding["sha256"]
    assert len(receipt["mutations"]) == 15
    nonstrict = [row for row in receipt["mutations"] if row["mutation_id"] == "MU284-NONSTRICT-SUPPORT"]
    assert len(nonstrict) == 1
    assert nonstrict[0]["executed"] and nonstrict[0]["activated"] and nonstrict[0]["killed"]

    threshold = build_depth_path_threshold_contract(
        contract_id="PR284-R4-ORACLE-THRESHOLD",
        multiplier=Fraction(2),
        registration_id="sha256:r4-threshold-preregistered",
    )
    law, selection = _law_and_selection()
    shared = {
        "threshold_contract": threshold,
        "finite_target_law": law,
        "selection_contract": selection,
        "path_partitions": (("negative", "positive"), ("all", "all")),
        "sigma_field_ids": ("sha256:r4-fine", "sha256:r4-coarse"),
        "filtration_id": "sha256:r4-decreasing-filtration",
        "preprocessing_id": "sha256:r4-common-preprocessing",
        "estimator_id": "sha256:r4-common-estimator",
        "premise_evidence_id": "sha256:r4-finite-tower",
    }

    equal_path = _path("EQUAL", (0, 1))
    assert set(equal_path.strata[1].support_unit_ids) == set(equal_path.strata[0].support_unit_ids)
    try:
        build_depth_path_reverse_martingale_report(
            report_id="PR284-R4-EQUAL-SUPPORT-PROVED",
            path=equal_path,
            **shared,
        )
    except DepthPathError as exc:
        assert "strictly nested sky supports" in str(exc)
    else:
        raise AssertionError("equal-support path minted proved premise status")

    mock_plan = build_depth_path_matched_mock_plan(
        plan_id="PR284-R4-EQUAL-SUPPORT-MOCK-PLAN",
        path=equal_path,
        threshold_contract=threshold,
        preprocessing_id="sha256:r4-common-preprocessing",
        estimator_id="sha256:r4-common-estimator",
        registration_id="sha256:r4-mock-plan-preregistered",
        null_law_id="sha256:r4-null-law",
        mock_generator_id="sha256:r4-generator",
        ensemble_policy_id="sha256:r4-ensemble",
        seed_policy_id="sha256:r4-seeds",
        matching_variable_ids=("mask", "selection", "depth"),
        acceptance_rule_id="sha256:r4-acceptance",
        multiplicity_rule_id="sha256:r4-path-maximum",
    )
    unproved = build_unproved_depth_path_reverse_martingale_report(
        report_id="PR284-R4-EQUAL-SUPPORT-UNPROVED",
        path=equal_path,
        threshold_contract=threshold,
        filtration_id="sha256:r4-unproved-filtration",
        preprocessing_id="sha256:r4-common-preprocessing",
        estimator_id="sha256:r4-common-estimator",
        premise_evidence_id="sha256:r4-strict-reduction-unproved",
        unresolved_reasons=("strict support reduction remains unproved",),
        matched_mock_plan=mock_plan,
    )
    fallback = build_depth_path_doob_calibration(
        calibration_id="PR284-R4-EQUAL-SUPPORT-FALLBACK",
        report=unproved,
        threshold_contract=threshold,
    )
    assert fallback.status is DepthPathCalibrationStatus.MATCHED_MOCKS_REQUIRED
    assert fallback.probability_upper_bound is None
    assert fallback.path_exceeds_threshold is None
    assert unproved.matched_mock_plan.null_mock_status == "required_not_executed"

    strict_path = _path("STRICT", (0,))
    assert set(strict_path.strata[1].support_unit_ids) < set(strict_path.strata[0].support_unit_ids)
    proved = build_depth_path_reverse_martingale_report(
        report_id="PR284-R4-STRICT-SUPPORT-PROVED",
        path=strict_path,
        **shared,
    )
    calibration = build_depth_path_doob_calibration(
        calibration_id="PR284-R4-STRICT-SUPPORT-CALIBRATION",
        report=proved,
        threshold_contract=threshold,
    )
    assert calibration.status is DepthPathCalibrationStatus.BOUND_AVAILABLE_CONDITIONAL_PROVED_PREMISE
    assert calibration.probability_upper_bound == Fraction(1, 4)
    for artifact in (proved.as_payload(), calibration.as_payload(), unproved.as_payload(), fallback.as_payload()):
        assert artifact["owner"] == "HTT"
        for key, expected in expected_boundary.items():
            assert artifact[key] == expected
        forbidden = " ".join(artifact["forbidden_use"]).lower()
        assert "family identification" in forbidden
        assert "posterior" in forbidden

    required_for_bound = set(spec["reverse_martingale_premise"]["required_for_bound"])
    assert "exact DepthPath content identity with strictly nested sky supports" in required_for_bound
    assert "support nesting without explicit partitions" in spec["reverse_martingale_premise"]["forbidden_substitutes"]
    assert receipt["mathematical_boundary"]["relation_to_source"] == "FINITE_REGISTERED_PATH_ONLY"
    assert receipt["mathematical_boundary"]["source_proof_adjudication_status"] == "NOT_ADJUDICATED"

    print(json.dumps({
        "oracle": "A-PR284-R4-CLAIM",
        "status": "PASS",
        "checks": [
            "spec_policy_receipt_claim_boundary_consistent",
            "receipt_content_and_bound_source_hashes_recomputed",
            "fifteen_mutations_include_killed_nonstrict_support",
            "equal_support_rejected_for_proved_premise",
            "equal_support_allowed_only_on_unproved_no_bound_route",
            "strict_support_path_retains_conditional_finite_bound",
            "proper_subset_is_premise_not_proof_or_family_identification",
            "htt_common_obsstat_mio_ownership_boundary_preserved",
        ],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
