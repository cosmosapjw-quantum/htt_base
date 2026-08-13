#!/usr/bin/env python3
"""Independent PR-284 claim, ownership, and provenance invariant oracle."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import yaml


RUN_ID = "pr284-candidate-review-20260810"
ASSIGNMENT_ID = "A-PR284-CLAIM"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
ASSIGNMENT_PATH = (
    f".agent-harness/runs/{RUN_ID}/assignments/{ASSIGNMENT_ID}.json"
)


def canonical_sha256(value: object, *, omit: set[str] | None = None) -> str:
    if omit and isinstance(value, dict):
        value = {key: item for key, item in value.items() if key not in omit}
    data = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    output = (repo / args.output).resolve()
    output.relative_to(repo)
    started = utc_now()
    checks: list[dict[str, object]] = []

    def check(check_id: str, condition: bool, evidence: list[str], detail: str) -> None:
        checks.append(
            {
                "check_id": check_id,
                "status": "PASS" if condition else "FAIL",
                "detail": detail,
                "evidence_refs": evidence,
            }
        )

    assignment = json.loads((repo / ASSIGNMENT_PATH).read_text())
    seal_path = repo / ".prguard/runtime/PR284_CANDIDATE_SEAL.json"
    spec_path = repo / "docs/research_program/post_pr275/pr284_spec.yaml"
    policy_path = repo / "docs/research_program/post_pr275/pr284_publication_policy.json"
    delta_path = repo / "docs/PR_DELTAS/pr-284.md"
    receipt_path = repo / "docs/generated/pr284_depth_path_doob_receipt.json"
    common_path = repo / "htt/src/common/depth_path_calibration.py"
    htt_path = repo / "htt/htt/htt/infer/depth_path_calibration.py"
    seal = json.loads(seal_path.read_text())
    spec = yaml.safe_load(spec_path.read_text())
    policy = json.loads(policy_path.read_text())
    receipt = json.loads(receipt_path.read_text())
    delta = delta_path.read_text()
    common_source = common_path.read_text()
    htt_source = htt_path.read_text()

    check(
        "assignment-context-and-input-seals",
        assignment["context_version"] == CONTEXT_VERSION
        and assignment["assignment_id"] == ASSIGNMENT_ID
        and all(
            file_sha256(repo / row["path"]) == row["sha256"]
            for row in assignment["required_inputs"]
        ),
        [ASSIGNMENT_PATH, "required_inputs[*].sha256"],
        "Assignment identity, context version, and every required-input byte hash match.",
    )

    binding = assignment["candidate_binding"]
    binding_fields = (
        "seal_sha256",
        "base_sha",
        "candidate_sha",
        "merge_base_sha",
        "candidate_tree_sha",
        "diff_sha256",
        "changed_files_sha256",
        "production_hash",
    )
    check(
        "candidate-identity",
        file_sha256(seal_path) == binding["seal_file_sha256"]
        and seal["seal_sha256"] == canonical_sha256(seal, omit={"seal_sha256"})
        and all(binding[field] == seal[field] for field in binding_fields)
        and git(repo, "rev-parse", "HEAD") == seal["candidate_sha"]
        and git(repo, "rev-parse", "HEAD^{tree}") == seal["candidate_tree_sha"]
        and git(repo, "merge-base", seal["base_sha"], seal["candidate_sha"])
        == seal["merge_base_sha"],
        [str(seal_path.relative_to(repo)), ASSIGNMENT_PATH, "git rev-parse HEAD"],
        "The review is bound to the frozen candidate commit, tree, merge base, and seal.",
    )

    remote_target = git(repo, "rev-parse", seal["target_ref"])
    check(
        "exact-predecessor-and-policy",
        file_sha256(policy_path) == seal["integration_policy"]["sha256"]
        and seal["integration_policy"]["policy_id"] == policy["policy_id"]
        and policy["target_sha"] == seal["base_sha"] == remote_target
        and seal["target_ref"] == f"refs/remotes/{policy['target_ref']}"
        and seal["target_branch"]
        == "changeset/pr283-weak-identification-recovery-20260810"
        and seal["base_sha"] in delta
        and "the sealed head of open PR-283" in delta,
        [
            str(policy_path.relative_to(repo)),
            str(seal_path.relative_to(repo)),
            str(delta_path.relative_to(repo)) + ":21-34",
            f"git rev-parse {seal['target_ref']}",
        ],
        "Policy, seal, local target ref, and recovery delta bind the exact PR-283 predecessor SHA.",
    )

    expected_ownership = {
        "COMMON": "immutable path, filtration, report, and calibration contracts",
        "OBSSTAT": "estimator and mask-feature inputs only",
        "MIO": "diagnostic path-consistency consumers only",
        "HTT": "premise evaluation and calibration decision",
    }
    check(
        "owner-and-contributor-roles",
        spec["owner"] == "HTT"
        and spec["contributors"] == ["OBSSTAT", "MIO", "COMMON"]
        and spec["runtime_contract"]["ownership"] == expected_ownership
        and receipt["owner"] == "HTT"
        and receipt["contributors"] == ["OBSSTAT", "MIO", "COMMON"]
        and 'PR284_OWNER = "HTT"' in common_source
        and htt_source.startswith('"""HTT-owned PR-284'),
        [
            str(spec_path.relative_to(repo)) + ":4-8,162-166",
            str(receipt_path.relative_to(repo)) + ":20-29,198-200",
            str(common_path.relative_to(repo)) + ":1-5,38-41",
            str(htt_path.relative_to(repo)) + ":1",
        ],
        "HTT owns premise evaluation and calibration; contributors remain bounded to their declared roles.",
    )

    ceiling_ok = (
        spec["claim_tier"] == "diagnostic_only"
        and spec["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
        and spec["scientific_artifact_mode"] == "synthetic_diagnostic"
        and spec["transfer_source"] == "none"
        and spec["observed_data_executed"] is False
        and spec["public_use"] is False
        and spec["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
        and policy["claim_ceiling"] == "diagnostic_only"
        and policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
        and receipt["claim_tier"] == "diagnostic_only"
        and receipt["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
        and receipt["scientific_artifact_mode"] == "synthetic_diagnostic"
        and receipt["transfer_source"] == "none"
        and receipt["observed_data_executed"] is False
        and receipt["public_use"] is False
        and receipt["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    )
    payloads = [
        receipt["proved_fixture"]["report"],
        receipt["proved_fixture"]["calibration"],
        receipt["unproved_fixture"]["report"],
        receipt["unproved_fixture"]["calibration"],
    ]
    ceiling_ok = ceiling_ok and all(
        payload["owner"] == "HTT"
        and payload["claim_tier"] == "diagnostic_only"
        and payload["transfer_source"] == "none"
        and payload["observed_data_executed"] is False
        and payload["public_use"] is False
        and payload["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
        for payload in payloads
    )
    check(
        "c2-diagnostic-transfer-and-family-ceiling",
        ceiling_ok,
        [
            str(spec_path.relative_to(repo)) + ":16-24",
            str(policy_path.relative_to(repo)) + ":31-32",
            str(receipt_path.relative_to(repo)) + ":20-36,194-235,407-464",
            str(common_path.relative_to(repo)) + ":38-60,520-633,775-858",
        ],
        "Every layer preserves C2 diagnostic-only, transfer none, synthetic/non-observed/non-public status, and the blocked family gate.",
    )

    boundary = receipt["mathematical_boundary"]
    check(
        "finite-path-only-theorem-boundary",
        spec["mathematical_boundary"]["relation_to_source"]
        == boundary["relation_to_source"]
        == "FINITE_REGISTERED_PATH_ONLY"
        and spec["mathematical_boundary"]["source_registry_status"]
        == boundary["source_registry_status"]
        == "ORACLE_VERIFIED"
        and spec["mathematical_boundary"]["source_proof_adjudication_status"]
        == boundary["source_proof_adjudication_status"]
        == "NOT_ADJUDICATED"
        and spec["mathematical_boundary"]["pr284_effect"]
        == boundary["pr284_effect"]
        == "runtime_execution_without_general_theorem_promotion"
        and "not a convergence theorem" in spec["mathematical_boundary"]["boundary"]
        and "optional-stopping" in spec["forbidden_uses"][1].lower()
        and "does not promote it into a general theorem" in delta,
        [
            str(spec_path.relative_to(repo)) + ":39-52,304-314",
            str(receipt_path.relative_to(repo)) + ":54-74",
            str(delta_path.relative_to(repo)) + ":77-89",
        ],
        "The source is oracle-verified but not adjudicated; PR-284 is confined to an exact finite registered path.",
    )

    unproved = receipt["unproved_fixture"]
    plan = unproved["matched_mock_plan"]
    check(
        "matched-mocks-required-not-executed",
        unproved["matched_mocks_executed"] is False
        and unproved["probability_bound"] is None
        and unproved["calibration"]["status"] == "MATCHED_MOCKS_REQUIRED"
        and unproved["calibration"]["probability_upper_bound"] is None
        and unproved["report"]["premise_status"]
        == "UNPROVED_REQUIRES_MATCHED_MOCKS"
        and plan["null_mock_status"] == "required_not_executed"
        and unproved["report"]["matched_mock_plan"]["content_id"]
        == plan["content_id"]
        and "matched-mock plan is not execution evidence" in common_source
        and "matched mocks passed" in spec["assumptions"][3],
        [
            str(spec_path.relative_to(repo)) + ":117-138,286-298",
            str(receipt_path.relative_to(repo)) + ":465-609",
            str(common_path.relative_to(repo)) + ":393-436,597-622",
            str(htt_path.relative_to(repo)) + ":254-313,345-379",
        ],
        "The fallback is a preregistered design only: it emits no bound and contains no executed-mock claim.",
    )

    check(
        "receipt-content-address-and-source-bindings",
        receipt["receipt_content_sha256"]
        == canonical_sha256(receipt, omit={"receipt_content_sha256"})
        and all(
            file_sha256(repo / row["path"]) == row["sha256"]
            for row in receipt["source_bindings"]
        ),
        [str(receipt_path.relative_to(repo)) + ":408-464"],
        "The receipt content address and every declared source binding recompute exactly.",
    )

    forbidden_claim_fragments = (
        "MIO posterior",
        "model-independent truth certificate",
        "external transfer validated as native",
        "TSC full solver",
        "Teff full polarisation closure",
    )
    scanned = "\n".join((delta, common_source, htt_source))
    check(
        "forbidden-claim-drift",
        not any(fragment in scanned for fragment in forbidden_claim_fragments)
        and "This is not observed-data calibration" in delta
        and "geometry detection, or family" in delta
        and "No observed-sky data" in delta,
        [
            str(delta_path.relative_to(repo)) + ":3-17,77-89,131-135",
            str(common_path.relative_to(repo)) + ":42-60",
            str(htt_path.relative_to(repo)) + ":1-5",
        ],
        "Production prose and runtime sources contain the required denials and no MIO/TSC/native-transfer overclaim fragments.",
    )

    failures = [row["check_id"] for row in checks if row["status"] != "PASS"]
    payload = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "context_version": CONTEXT_VERSION,
        "oracle_id": "PR284-CLAIM-PROVENANCE-INVARIANTS-V1",
        "status": "PASS" if not failures else "FAIL",
        "started_at": started,
        "completed_at": utc_now(),
        "checks": checks,
        "failures": failures,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
