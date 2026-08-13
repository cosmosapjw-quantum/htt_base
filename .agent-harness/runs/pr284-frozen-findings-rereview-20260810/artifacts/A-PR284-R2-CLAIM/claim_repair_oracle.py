#!/usr/bin/env python3
"""Independent affected-cell claim oracle for the PR-284 R2 repair."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import yaml


RUN_ID = "pr284-frozen-findings-rereview-20260810"
ASSIGNMENT_ID = "A-PR284-R2-CLAIM"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
ASSIGNMENT_PATH = f".agent-harness/runs/{RUN_ID}/assignments/{ASSIGNMENT_ID}.json"
PRE_REPAIR_SHA = "029f8cedd044cc5967bc12dc695230ca69cf3308"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: object, *, omit: set[str] | None = None) -> str:
    if omit and isinstance(value, dict):
        value = {key: item for key, item in value.items() if key not in omit}
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


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
    started = now()
    checks: list[dict[str, object]] = []

    def check(check_id: str, condition: bool, detail: str, refs: list[str]) -> None:
        checks.append(
            {
                "check_id": check_id,
                "status": "PASS" if condition else "FAIL",
                "detail": detail,
                "evidence_refs": refs,
            }
        )

    assignment = json.loads((repo / ASSIGNMENT_PATH).read_text())
    seal_path = repo / ".prguard/runtime/PR284_R2_CANDIDATE_SEAL.json"
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
    delta_words = " ".join(delta.split())
    common = common_path.read_text()
    htt = htt_path.read_text()

    check(
        "registered-inputs-and-context",
        assignment["context_version"] == CONTEXT_VERSION
        and assignment["assignment_id"] == ASSIGNMENT_ID
        and all(
            file_sha(repo / row["path"]) == row["sha256"]
            for row in assignment["required_inputs"]
        ),
        "The R2 assignment context and all six registered input byte identities match.",
        [ASSIGNMENT_PATH, "required_inputs[*].sha256"],
    )

    binding = assignment["candidate_binding"]
    fields = (
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
        "r2-candidate-and-policy-binding",
        file_sha(seal_path) == binding["seal_file_sha256"]
        and seal["seal_sha256"] == canonical_sha(seal, omit={"seal_sha256"})
        and all(binding[field] == seal[field] for field in fields)
        and git(repo, "rev-parse", "HEAD") == seal["candidate_sha"]
        and git(repo, "rev-parse", "HEAD^{tree}") == seal["candidate_tree_sha"]
        and git(repo, "merge-base", seal["base_sha"], seal["candidate_sha"])
        == seal["merge_base_sha"]
        and file_sha(policy_path) == seal["integration_policy"]["sha256"]
        and policy["policy_id"] == seal["integration_policy"]["policy_id"]
        and policy["target_sha"] == seal["base_sha"]
        and git(repo, "rev-parse", seal["target_ref"]) == seal["base_sha"],
        "The affected-cell rereview is bound to the repaired candidate and unchanged predecessor policy.",
        [str(seal_path.relative_to(repo)), str(policy_path.relative_to(repo))],
    )

    expected_roles = {
        "COMMON": "immutable path, filtration, report, and calibration contracts",
        "OBSSTAT": "estimator and mask-feature inputs only",
        "MIO": "diagnostic path-consistency consumers only",
        "HTT": "premise evaluation and calibration decision",
    }
    common_exports = common.split("__all__ = [", 1)[1]
    check(
        "htt-owner-common-contract-replay",
        spec["owner"] == "HTT"
        and spec["contributors"] == ["OBSSTAT", "MIO", "COMMON"]
        and spec["runtime_contract"]["ownership"] == expected_roles
        and receipt["owner"] == "HTT"
        and receipt["contributors"] == ["OBSSTAT", "MIO", "COMMON"]
        and 'PR284_OWNER = "HTT"' in common
        and "def _assert_proved_premise_replay" in common
        and common.count("self._assert_proved_premise_replay()") == 2
        and '"_build_depth_path_reverse_martingale_report_contract"'
        not in common_exports
        and htt.startswith('"""HTT-owned PR-284 premise evaluation')
        and "def build_depth_path_reverse_martingale_report" in htt
        and "def build_depth_path_doob_calibration" in htt,
        "COMMON performs fail-closed contract replay while HTT retains public premise-evaluation and calibration ownership.",
        [
            str(spec_path.relative_to(repo)) + ":4-8,140-166",
            str(common_path.relative_to(repo)) + ":42-64,660-864,1087-1102",
            str(htt_path.relative_to(repo)) + ":1,126-380",
            str(receipt_path.relative_to(repo)) + ":20-29,207-230",
        ],
    )

    payloads = [
        receipt["proved_fixture"]["report"],
        receipt["proved_fixture"]["calibration"],
        receipt["unproved_fixture"]["report"],
        receipt["unproved_fixture"]["calibration"],
    ]
    check(
        "c2-diagnostic-transfer-and-family-firewall",
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
        and all(
            payload["owner"] == "HTT"
            and payload["claim_tier"] == "diagnostic_only"
            and payload["transfer_source"] == "none"
            and payload["observed_data_executed"] is False
            and payload["public_use"] is False
            and payload["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
            for payload in payloads
        ),
        "The repair preserves HTT ownership, C2 diagnostic-only scope, transfer none, non-observed/non-public status, and the blocked family gate at every artifact layer.",
        [
            str(spec_path.relative_to(repo)) + ":16-24",
            str(policy_path.relative_to(repo)) + ":31-32",
            str(receipt_path.relative_to(repo)) + ":20-37,207-230,416-473,474-619",
            str(common_path.relative_to(repo)) + ":42-64,541-654,898-985",
        ],
    )

    boundary = receipt["mathematical_boundary"]
    check(
        "finite-path-only-no-theorem-promotion",
        spec["mathematical_boundary"]["relation_to_source"]
        == boundary["relation_to_source"]
        == "FINITE_REGISTERED_PATH_ONLY"
        and spec["mathematical_boundary"]["source_proof_adjudication_status"]
        == boundary["source_proof_adjudication_status"]
        == "NOT_ADJUDICATED"
        and spec["mathematical_boundary"]["pr284_effect"]
        == boundary["pr284_effect"]
        == "runtime_execution_without_general_theorem_promotion"
        and "not a convergence theorem" in spec["mathematical_boundary"]["boundary"]
        and "does not promote it into a general theorem" in delta,
        "The new replay is a finite registered contract check, not an adjudicated, convergence, optional-stopping, or general theorem promotion.",
        [
            str(spec_path.relative_to(repo)) + ":39-52",
            str(receipt_path.relative_to(repo)) + ":54-74",
            str(delta_path.relative_to(repo)) + ":77-89,100-119",
        ],
    )

    mutation_spec = next(
        row
        for row in spec["mutation_registry"]
        if row["mutation_id"] == "MU284-REPORT-BUILDER-BYPASS"
    )
    mutation_rows = [
        row
        for row in receipt["mutations"]
        if row["mutation_id"] == "MU284-REPORT-BUILDER-BYPASS"
    ]
    check(
        "bounded-builder-bypass-mutation-language",
        len(mutation_rows) == 1
        and mutation_spec["mutation_kind"]
        == mutation_rows[0]["mutation_kind"]
        == "caller_supplied_proved_report_bypasses_replay"
        and all(mutation_rows[0][field] is True for field in ("activated", "executed", "killed"))
        and mutation_rows[0]["observed_outcome"]
        == "BLOCKED_DEPTH_PATH_CALIBRATION_CONTRACT"
        and mutation_rows[0]["observed_reason"]
        == "CALLER_SUPPLIED_PROVED_REPORT_REJECTED"
        and "The repair is confined to the existing report contract" in delta
        and "before any calibration can be built" in delta,
        "The new mutation records rejection of a forged constructor path; it does not promote the repaired replay into scientific validation.",
        [
            str(spec_path.relative_to(repo)) + ":186-242",
            str(receipt_path.relative_to(repo)) + ":75-201",
            str(delta_path.relative_to(repo)) + ":100-119",
        ],
    )

    fallback = receipt["unproved_fixture"]
    check(
        "matched-mocks-remain-unexecuted",
        fallback["matched_mocks_executed"] is False
        and fallback["probability_bound"] is None
        and fallback["calibration"]["status"] == "MATCHED_MOCKS_REQUIRED"
        and fallback["calibration"]["probability_upper_bound"] is None
        and fallback["report"]["premise_status"]
        == "UNPROVED_REQUIRES_MATCHED_MOCKS"
        and fallback["matched_mock_plan"]["null_mock_status"]
        == "required_not_executed"
        and "Process success does not imply that a bound is available" in delta_words
        and "separate executed and independently reviewed matched-mock receipt"
        in delta_words,
        "Neither the repair nor its mutation kill claims mock execution, an unproved bound, or observed significance.",
        [
            str(spec_path.relative_to(repo)) + ":117-138,290-316",
            str(receipt_path.relative_to(repo)) + ":474-619",
            str(delta_path.relative_to(repo)) + ":86-89",
        ],
    )

    added_delta = git(
        repo,
        "diff",
        "--unified=0",
        PRE_REPAIR_SHA,
        seal["candidate_sha"],
        "--",
        "docs/PR_DELTAS/pr-284.md",
    )
    added_delta_words = " ".join(
        line[1:].strip()
        for line in added_delta.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    unsafe_promotions = (
        "Bianchi geometry detected",
        "Bianchi family identified",
        "family identified",
        "native solver result",
        "matched mocks executed",
        "observed-data significance established",
        "general theorem proved",
        "MIO posterior",
        "model-independent truth certificate",
        "TSC full solver",
        "Teff full polarisation closure",
        "external transfer validated as native",
    )
    check(
        "repair-prose-no-forbidden-promotion",
        not any(fragment in added_delta_words for fragment in unsafe_promotions)
        and "substantive FAIL" in added_delta_words
        and "not regraded or used as acceptance evidence" in added_delta_words
        and "remain lifecycle-gated and are not claimed" in delta_words
        and "bootstrap-only failure is preserved" in added_delta_words,
        "Added repair prose preserves the failed historical verdict and lifecycle limits without positive theorem, native, observed, geometry, family, or mock-execution claims.",
        [str(delta_path.relative_to(repo)) + ":100-162", f"git diff {PRE_REPAIR_SHA}..{seal['candidate_sha']}"],
    )

    check(
        "receipt-content-address-and-bindings",
        receipt["receipt_content_sha256"]
        == canonical_sha(receipt, omit={"receipt_content_sha256"})
        and all(
            file_sha(repo / row["path"]) == row["sha256"]
            for row in receipt["source_bindings"]
        ),
        "The repaired receipt content identity and every declared source binding recompute exactly.",
        [str(receipt_path.relative_to(repo)) + ":416-473"],
    )

    failures = [row["check_id"] for row in checks if row["status"] != "PASS"]
    payload = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "context_version": CONTEXT_VERSION,
        "oracle_id": "PR284-R2-CLAIM-REPAIR-INVARIANTS-V1",
        "status": "PASS" if not failures else "FAIL",
        "started_at": started,
        "completed_at": now(),
        "checks": checks,
        "failures": failures,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
