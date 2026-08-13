#!/usr/bin/env python3
"""Independent narrow claim/identity oracle for A-PR284-R3-CLAIM."""

from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

from common import depth_path_calibration as contracts
from common.depth_path import DepthPathError, build_depth_path, build_mask_stratum, build_transport_kernel
from common.depth_path_calibration import (
    DepthPathCalibrationStatus,
    ReverseMartingalePremiseStatus,
    build_depth_path_finite_target_law,
    build_depth_path_selection_contract,
    build_depth_path_threshold_contract,
    revalidate_depth_path_reverse_martingale_report,
)
from common.sky_support import build_sky_support_from_mask
from htt.infer.depth_path_calibration import (
    build_depth_path_doob_calibration,
    build_depth_path_matched_mock_plan,
    build_depth_path_reverse_martingale_report,
    build_unproved_depth_path_reverse_martingale_report,
)


ROOT = Path(__file__).resolve().parents[5]
SPEC = ROOT / "docs/research_program/post_pr275/pr284_spec.yaml"
POLICY = ROOT / "docs/research_program/post_pr275/pr284_publication_policy.json"
RECEIPT = ROOT / "docs/generated/pr284_depth_path_doob_receipt.json"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_digest(payload: dict[str, object]) -> str:
    stripped = dict(payload)
    stripped.pop("receipt_content_sha256", None)
    encoded = json.dumps(
        stripped,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _stratum(suffix: str, depth: int, kept: tuple[int, ...]):
    mask = np.zeros(2, dtype=bool)
    mask[list(kept)] = True
    support = build_sky_support_from_mask(
        mask,
        coordinate_frame="GALACTIC",
        completeness_status="synthetic_fixture_complete",
        selection_mode=f"oracle-selection-{suffix}",
        mock_coverage_status="synthetic_fixture_only",
        pixelization="PR284_ORACLE_PIXELS",
    )
    return build_mask_stratum(
        stratum_id=f"ORACLE-{suffix}",
        depth_coordinate=depth,
        depth_unit="synthetic_depth",
        support_unit_ids=tuple(f"pixel-{index}" for index in kept),
        support_universe_size=2,
        sky_support=support,
        selection_id=f"sha256:oracle-selection-{suffix}",
        covariance_id=f"sha256:oracle-covariance-{suffix}",
        source_artifact_id=f"sha256:oracle-source-{suffix}",
        feature_names=("centered_scalar",),
        feature_unit="dimensionless_diagnostic",
        assumptions=("independent synthetic nested-support oracle",),
    )


def _path(tag: str, second_kept: tuple[int, ...] = (0,)):
    first = _stratum(f"{tag}-D1", 1, (0, 1))
    second = _stratum(f"{tag}-D2", 2, second_kept)
    kernel = build_transport_kernel(
        transport_id=f"ORACLE-{tag}-K12",
        source=first,
        target=second,
        matrix=((1.0,),),
        mask_transport_id=f"sha256:oracle-mask-{tag}",
        selection_transport_id=f"sha256:oracle-selection-{tag}",
        covariance_transport_id=f"sha256:oracle-covariance-{tag}",
        method_id="PR284-ORACLE-IDENTITY-TRANSPORT-V1",
        assumptions=("independent synthetic identity transport",),
    )
    return build_depth_path(
        path_id=f"PR284-ORACLE-{tag}",
        strata=(first, second),
        kernels=(kernel,),
    )


def main() -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    ceiling = {
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "observed_data_executed": False,
        "public_use": False,
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
    }
    for key, expected in ceiling.items():
        assert spec[key] == expected
        assert receipt[key] == expected
    assert policy["claim_ceiling"] == ceiling["claim_tier"]
    assert policy["family_identification_gate"] == ceiling["family_identification_gate"]
    assert spec["owner"] == receipt["owner"] == "HTT"
    assert set(spec["contributors"]) == set(receipt["contributors"]) == {
        "COMMON",
        "OBSSTAT",
        "MIO",
    }
    assert spec["runtime_contract"]["ownership"] == {
        "COMMON": "immutable path, filtration, report, and calibration contracts",
        "OBSSTAT": "estimator and mask-feature inputs only",
        "MIO": "diagnostic path-consistency consumers only",
        "HTT": "premise evaluation and calibration decision",
    }

    assert receipt["receipt_content_sha256"] == _canonical_digest(receipt)
    for binding in receipt["source_bindings"]:
        path = binding["path"]
        assert not path.startswith((".agent-harness/runs/", ".prguard/"))
        assert _digest(ROOT / path) == binding["sha256"]
    assert receipt["generation_identity"]["git_or_worktree_identity"] == (
        "EXTERNAL_CANDIDATE_SEAL_REQUIRED"
    )
    assert receipt["mathematical_boundary"]["relation_to_source"] == (
        "FINITE_REGISTERED_PATH_ONLY"
    )
    assert receipt["mathematical_boundary"]["source_proof_adjudication_status"] == (
        "NOT_ADJUDICATED"
    )

    path = _path("PRIMARY")
    law = build_depth_path_finite_target_law(
        law_id="ORACLE-LAW",
        common_target_id="ORACLE-TARGET",
        atom_ids=("minus", "plus"),
        weights=(Fraction(1, 2), Fraction(1, 2)),
        common_target=(Fraction(-1), Fraction(1)),
        registration_id="sha256:oracle-law-preregistered",
    )
    selection = build_depth_path_selection_contract(
        selection_id="ORACLE-SELECTION",
        finite_target_law=law,
        selected_atom_id="minus",
        selected_atom_index=0,
        selection_rule_id="sha256:oracle-first-atom",
        registration_id="sha256:oracle-selection-preregistered",
    )
    threshold = build_depth_path_threshold_contract(
        contract_id="ORACLE-THRESHOLD",
        multiplier=Fraction(2),
        registration_id="sha256:oracle-threshold-preregistered",
    )
    report = build_depth_path_reverse_martingale_report(
        report_id="ORACLE-PROVED-REPORT",
        path=path,
        threshold_contract=threshold,
        finite_target_law=law,
        selection_contract=selection,
        path_partitions=(("minus", "plus"), ("all", "all")),
        sigma_field_ids=("sha256:oracle-fine", "sha256:oracle-coarse"),
        filtration_id="sha256:oracle-decreasing-filtration",
        preprocessing_id="sha256:oracle-common-preprocessing",
        estimator_id="sha256:oracle-common-estimator",
        premise_evidence_id="sha256:oracle-finite-tower",
    )
    assert report.path.content_id == report.path_content_id == path.content_id
    assert report.premise_status is ReverseMartingalePremiseStatus.PROVED_FINITE_REGISTERED_PATH
    assert report.path_values == (Fraction(-1), Fraction(0))

    calibration = build_depth_path_doob_calibration(
        calibration_id="ORACLE-PROVED-CALIBRATION",
        report=report,
        threshold_contract=threshold,
    )
    assert calibration.status is DepthPathCalibrationStatus.BOUND_AVAILABLE_CONDITIONAL_PROVED_PREMISE
    assert calibration.probability_upper_bound == Fraction(1, 4)
    for value in (report, calibration):
        payload = value.as_payload()
        for key, expected in ceiling.items():
            assert payload[key] == expected
        assert payload["owner"] == "HTT"

    forged = copy.copy(report)
    object.__setattr__(forged, "path", _path("ALTERNATE"))
    try:
        revalidate_depth_path_reverse_martingale_report(forged)
    except DepthPathError as exc:
        assert "path content identity" in str(exc)
    else:
        raise AssertionError("stale report accepted an alternate embedded DepthPath")

    try:
        contracts._build_depth_path_reverse_martingale_report_contract(
            path=None,
            report_id="ORACLE-NO-PATH-FORGERY",
        )
    except DepthPathError as exc:
        assert "exact DepthPath" in str(exc)
    else:
        raise AssertionError("report builder accepted a missing exact DepthPath")

    try:
        build_depth_path_reverse_martingale_report(
            report_id="ORACLE-SUPPORT-AS-PROOF",
            path=path,
            threshold_contract=threshold,
            finite_target_law=law,
            selection_contract=selection,
            path_partitions=(),
            sigma_field_ids=(),
            filtration_id="sha256:oracle-no-filtration",
            preprocessing_id="sha256:oracle-common-preprocessing",
            estimator_id="sha256:oracle-common-estimator",
            premise_evidence_id="sha256:oracle-support-only",
        )
    except DepthPathError:
        pass
    else:
        raise AssertionError("support nesting alone minted a proved report")

    mock_plan = build_depth_path_matched_mock_plan(
        plan_id="ORACLE-MATCHED-MOCK-PLAN",
        path=path,
        threshold_contract=threshold,
        preprocessing_id="sha256:oracle-common-preprocessing",
        estimator_id="sha256:oracle-common-estimator",
        registration_id="sha256:oracle-mock-plan-preregistered",
        null_law_id="sha256:oracle-null-law",
        mock_generator_id="sha256:oracle-generator",
        ensemble_policy_id="sha256:oracle-ensemble",
        seed_policy_id="sha256:oracle-seeds",
        matching_variable_ids=("mask", "selection", "depth"),
        acceptance_rule_id="sha256:oracle-acceptance",
        multiplicity_rule_id="sha256:oracle-path-maximum",
    )
    unproved = build_unproved_depth_path_reverse_martingale_report(
        report_id="ORACLE-UNPROVED-REPORT",
        path=path,
        threshold_contract=threshold,
        filtration_id="sha256:oracle-unproved-filtration",
        preprocessing_id="sha256:oracle-common-preprocessing",
        estimator_id="sha256:oracle-common-estimator",
        premise_evidence_id="sha256:oracle-support-only",
        unresolved_reasons=("explicit partitions and tower are not proved",),
        matched_mock_plan=mock_plan,
    )
    fallback = build_depth_path_doob_calibration(
        calibration_id="ORACLE-FALLBACK",
        report=unproved,
        threshold_contract=threshold,
    )
    assert fallback.status is DepthPathCalibrationStatus.MATCHED_MOCKS_REQUIRED
    assert fallback.probability_upper_bound is None
    assert fallback.path_exceeds_threshold is None
    assert unproved.matched_mock_plan.null_mock_status == "required_not_executed"

    proved_payload = receipt["proved_fixture"]["report"]
    assert proved_payload["path"]["content_id"] == proved_payload["path_content_id"]
    assert tuple(s["content_id"] for s in proved_payload["path"]["strata"]) == tuple(
        proved_payload["stratum_content_ids"]
    )
    unproved_calibration = receipt["unproved_fixture"]["calibration"]
    assert unproved_calibration["status"] == "MATCHED_MOCKS_REQUIRED"
    assert unproved_calibration["probability_upper_bound"] is None

    print(
        json.dumps(
            {
                "oracle": "A-PR284-R3-CLAIM",
                "status": "PASS",
                "checks": [
                    "spec_policy_receipt_claim_ceiling_consistent",
                    "receipt_content_address_and_source_bindings_recomputed",
                    "historical_run_and_seal_artifacts_not_receipt_sources",
                    "exact_depth_path_embedded_and_revalidated",
                    "alternate_path_identity_forgery_rejected",
                    "missing_exact_path_rejected",
                    "support_nesting_alone_cannot_mint_proved_status",
                    "unproved_path_has_no_bound_and_requires_unexecuted_matched_mocks",
                    "htt_owner_and_c2_diagnostic_boundary_locked",
                ],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
