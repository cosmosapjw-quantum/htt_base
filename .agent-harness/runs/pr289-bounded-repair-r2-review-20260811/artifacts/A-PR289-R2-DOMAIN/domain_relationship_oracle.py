#!/usr/bin/env python3
"""Independent PR-289 domain oracle for native-role and semantic-status checks."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(ROOT / "htt/src"), str(ROOT / "htt"), str(ROOT)]

from common.data_identity import (  # noqa: E402
    AdmissionStatus,
    canonical_sha256,
    evaluate_lane_identity,
    load_lane_registry,
)


TEST_PATH = ROOT / "tests/contracts/test_data_identity_registry_v2.py"
OUTPUT_REL = Path(sys.argv[1]).as_posix()
COVERAGE_OUTPUT_REL = Path(sys.argv[2]).as_posix()
OUTPUT = (ROOT / OUTPUT_REL).resolve()
COVERAGE_OUTPUT = (ROOT / COVERAGE_OUTPUT_REL).resolve()
STAMP = "2026-08-09T00:00:00+00:00"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def raw_canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def main() -> int:
    started_at = utc_now()
    fixture = runpy.run_path(str(TEST_PATH))
    valid_descriptor = fixture["_valid_descriptor"]
    rewrite_evidence = fixture["_rewrite_evidence"]
    resign_nested = fixture["_resign_nested"]
    registry = load_lane_registry(fixture["REGISTRY_PATH"])
    checks: list[dict[str, object]] = []

    def evaluate(lane_id: str, descriptor: dict[str, object]):
        return evaluate_lane_identity(
            registry=registry,
            lane_id=lane_id,
            descriptor=descriptor,
            inspected_at_utc=STAMP,
        )

    def record(check_id: str, observed: str, expected: str, passed: bool) -> None:
        checks.append(
            {
                "check_id": check_id,
                "observed": observed,
                "expected": expected,
                "passed": passed,
            }
        )

    with tempfile.TemporaryDirectory(prefix="pr289-domain-oracle-") as temporary:
        scratch = Path(temporary)

        for lane_id in ("PLANCK", "CF4", "HSC_KIDS"):
            descriptor = valid_descriptor(scratch / f"baseline-{lane_id.lower()}", lane_id)
            decision = evaluate(lane_id, descriptor)
            record(
                f"baseline_{lane_id.lower()}_admits",
                decision.status.value,
                AdmissionStatus.ADMITTED_IDENTITY_ONLY.value,
                decision.status is AdmissionStatus.ADMITTED_IDENTITY_ONLY,
            )

        contradiction_results: dict[str, str] = {}
        for field in ("covariance_status", "sky_support_status"):
            descriptor = valid_descriptor(scratch / f"planck-{field}", "PLANCK")
            rewrite_evidence(
                descriptor,
                lambda evidence, field=field: evidence.__setitem__(
                    field, "NOT_APPLICABLE"
                ),
            )
            decision = evaluate("PLANCK", descriptor)
            contradiction_results[field] = decision.status.value
            record(
                f"planck_{field}_contradiction_reproduced",
                decision.status.value,
                AdmissionStatus.ADMITTED_IDENTITY_ONLY.value,
                decision.status is AdmissionStatus.ADMITTED_IDENTITY_ONLY,
            )

        control_mutations = (
            ("planck_commander_covariance_alias", "PLANCK", "planck_covariance"),
            ("cf4_sign_role_alias", "CF4", "cf4_sign"),
            ("cf4_depth_role_alias", "CF4", "cf4_depth"),
            ("hsc_kids_product_alias", "HSC_KIDS", "kids_product"),
            ("hsc_kids_covariance_alias", "HSC_KIDS", "kids_covariance"),
        )
        for check_id, lane_id, mutation in control_mutations:
            descriptor = valid_descriptor(scratch / check_id, lane_id)

            def mutate(evidence: dict[str, object], mutation=mutation) -> None:
                profile = evidence["native_identity_profile"]
                if mutation == "planck_covariance":
                    row = profile["pipelines"]["COMMANDER"]
                    row["covariance_component_id"] = "smica_covariance"
                    resign_nested(profile, row, "pipeline_identity")
                elif mutation == "cf4_sign":
                    row = profile["semantics"]
                    row["sign_component_id"] = "frame_definition"
                    resign_nested(profile, row, "semantics_identity")
                elif mutation == "cf4_depth":
                    row = profile["semantics"]
                    row["depth_component_id"] = "grouping_definition"
                    resign_nested(profile, row, "semantics_identity")
                else:
                    kids = profile["children"]["KIDS"]
                    if mutation == "kids_product":
                        kids["product_component_id"] = "hsc_product"
                    else:
                        kids["covariance_component_id"] = "hsc_covariance"
                    resign_nested(profile, kids, "child_identity_id")
                    cross = profile["cross_covariance"]
                    cross["kids_child_identity_id"] = kids["child_identity_id"]
                    resign_nested(profile, cross, "cross_covariance_identity")
                unsigned = dict(profile)
                unsigned.pop("profile_id")
                profile["profile_id"] = canonical_sha256(unsigned)

            rewrite_evidence(descriptor, mutate)
            decision = evaluate(lane_id, descriptor)
            record(
                check_id,
                decision.status.value,
                AdmissionStatus.REJECTED_MISSING_SEMANTIC_CONTRACT.value,
                decision.status
                is AdmissionStatus.REJECTED_MISSING_SEMANTIC_CONTRACT,
            )

    if not all(bool(row["passed"]) for row in checks):
        return 2
    payload = {
        "schema": "htt.pr289.domain_relationship_oracle.v1",
        "oracle_id": "PR289-DOMAIN-STATUS-RELATIONSHIP-ORACLE",
        "started_at": started_at,
        "completed_at": utc_now(),
        "candidate_sha": "e7affa4302f60cb02a664b315693b22e2372ef33",
        "status": "PASS",
        "verdict": "REPRODUCED_BLOCKING_SEMANTIC_STATUS_CONTRADICTION",
        "finding": {
            "lane_id": "PLANCK",
            "accepted_contradictions": contradiction_results,
            "bound_relationships": [
                "smica_covariance",
                "commander_covariance",
                "same_sky_pair",
            ],
        },
        "controls": checks,
    }
    encoded_oracle = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    OUTPUT.write_text(
        encoded_oracle, encoding="utf-8"
    )
    oracle_sha256 = hashlib.sha256(encoded_oracle.encode("utf-8")).hexdigest()
    oracle_argv = [
        "python3",
        "-B",
        ".agent-harness/runs/pr289-bounded-repair-r2-review-20260811/artifacts/"
        "A-PR289-R2-DOMAIN/domain_relationship_oracle.py",
        ".agent-harness/runs/pr289-bounded-repair-r2-review-20260811/artifacts/"
        "A-PR289-R2-DOMAIN/DOMAIN_ORACLE.json",
        ".agent-harness/runs/pr289-bounded-repair-r2-review-20260811/artifacts/"
        "A-PR289-R2-DOMAIN/REVIEW_COVERAGE.json",
    ]
    policy = json.loads(
        (ROOT / "docs/research_program/post_pr275/pr289_publication_policy.json")
        .read_text(encoding="utf-8")
    )
    pass_cells = {
        "candidate_identity",
        "machine_lane_cardinality_and_gate_identity",
        "units_frame_convention",
        "planck_first_candidate",
        "cf4_native_catalogue_selection_covariance_replay",
        "hsc_kids_separate_child_and_cross_covariance_replay",
        "admission_authorization_separation",
        "no_download_or_repository_copy",
        "receipt_recomputation_and_content_address",
        "publication_policy_cross_binding",
        "claim_and_family_ceiling",
    }
    fail_cells = {
        "typed_provenance_evidence",
        "mask_selection_covariance_null",
        "transfer_and_sky_support",
        "planck_native_profile_and_same_sky_replay",
    }
    source_evidence = [
        "docs/research_program/post_pr275/pr289_spec.yaml:105-110",
        "htt/src/common/data_identity.py:840-896",
        "htt/src/common/data_identity.py:1598-1623",
        "tests/contracts/test_data_identity_registry_v2.py:87-114",
        OUTPUT_REL,
    ]
    coverage_cells = []
    for cell in policy["required_review_cells"]:
        if cell in fail_cells:
            coverage_cells.append(
                {
                    "cell": cell,
                    "status": "FAIL",
                    "evidence_refs": source_evidence,
                    "rationale": (
                        "Planck admits covariance_status or sky_support_status "
                        "NOT_APPLICABLE while the corresponding covariance and "
                        "same-sky identities remain bound."
                    ),
                }
            )
        elif cell in pass_cells:
            coverage_cells.append(
                {
                    "cell": cell,
                    "status": "PASS",
                    "evidence_refs": source_evidence,
                    "rationale": (
                        "Targeted static review, focused suite, preflight/check, "
                        "and hostile relationship controls passed for this cell."
                    ),
                }
            )
        else:
            coverage_cells.append(
                {
                    "cell": cell,
                    "status": "NOT_APPLICABLE",
                    "evidence_refs": [],
                    "rationale": (
                        "Outside the registered scientific domain-consistency "
                        "slice for A-PR289-R2-DOMAIN."
                    ),
                }
            )
    coverage = {
        "schema_version": 1,
        "run_id": "pr289-bounded-repair-r2-review-20260811",
        "assignment_id": "A-PR289-R2-DOMAIN",
        "change_set_id": "CS-PR289-DATA-IDENTITY-V2",
        "publication_group_id": "PG-PR289-DATA-IDENTITY-V2",
        "candidate_seal_sha256": (
            "b87547b5c86fb27fb63c6ba2f62639733295efe0b7ddf91ed82685a6c6cbba90"
        ),
        "candidate_sha": "e7affa4302f60cb02a664b315693b22e2372ef33",
        "candidate_tree_sha": (
            "1d25895f229c87723797c73018fed8783466541f"
        ),
        "diff_sha256": (
            "124822f8c20278b307447150dcd0a8aa357048f6a9526e8feb976c14a2715ae1"
        ),
        "changed_files_sha256": (
            "621d99013dd65c44146ccb0f3d75a2365332deb43aeda60864bfa4f2d5bae15e"
        ),
        "completed_at": payload["completed_at"],
        "first_verdict_read_only": True,
        "correlated_review": False,
        "coverage_cells": coverage_cells,
        "independent_oracles": [
            {
                "oracle_id": payload["oracle_id"],
                "kind": "mutation_test",
                "status": "PASS",
                "argv": oracle_argv,
                "command_fingerprint": raw_canonical_sha256({"argv": oracle_argv}),
                "started_at": payload["started_at"],
                "completed_at": payload["completed_at"],
                "returncode": 0,
                "timed_out": False,
                "artifact_path": OUTPUT_REL,
                "artifact_sha256": oracle_sha256,
                "artifact_bytes": len(encoded_oracle.encode("utf-8")),
                "evidence_refs": source_evidence,
            }
        ],
    }
    coverage["coverage_sha256"] = raw_canonical_sha256(coverage)
    COVERAGE_OUTPUT.write_text(
        json.dumps(coverage, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
