#!/usr/bin/env python3
"""Build the assignment-local coverage and reviewer envelope."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "pr291-bounded-repair-r4-review-20260813"
ASSIGNMENT_ID = "A-PR291-R4-PHYSSTAT"
RUN = ROOT / ".agent-harness" / "runs" / RUN_ID
ARTIFACT_DIR = RUN / "artifacts" / ASSIGNMENT_ID
RESULT_REL = f".agent-harness/runs/{RUN_ID}/results/{ASSIGNMENT_ID}.json"
COVERAGE_REL = f".agent-harness/runs/{RUN_ID}/artifacts/{ASSIGNMENT_ID}/REVIEW_COVERAGE.json"
ORACLE_REL = f".agent-harness/runs/{RUN_ID}/artifacts/{ASSIGNMENT_ID}/ORACLE_RESULT.json"
ORACLE_SCRIPT_REL = f".agent-harness/runs/{RUN_ID}/artifacts/{ASSIGNMENT_ID}/ORACLE.py"


def canonical_sha(value: object, *, omit: set[str] = set()) -> str:
    if isinstance(value, dict):
        value = {key: val for key, val in value.items() if key not in omit}
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_ref(relative: str) -> dict[str, object]:
    path = ROOT / relative
    data = path.read_bytes()
    return {
        "path": relative,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "producer": ASSIGNMENT_ID,
    }


def cell(name: str, status: str, evidence: list[str], rationale: str) -> dict[str, object]:
    return {
        "cell": name,
        "status": status,
        "evidence_refs": evidence,
        "rationale": rationale,
    }


def main() -> None:
    assignment = json.loads((RUN / "assignments" / f"{ASSIGNMENT_ID}.json").read_text())
    seal = json.loads((ROOT / assignment["candidate_binding"]["seal_path"]).read_text())
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    argv = [
        "python",
        "-B",
        ORACLE_SCRIPT_REL,
        "--output",
        ORACLE_REL,
    ]
    coverage = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "change_set_id": seal["change_set_id"],
        "publication_group_id": seal["publication_group_id"],
        "candidate_seal_sha256": seal["seal_sha256"],
        "candidate_sha": seal["candidate_sha"],
        "candidate_tree_sha": seal["candidate_tree_sha"],
        "diff_sha256": seal["diff_sha256"],
        "changed_files_sha256": seal["changed_files_sha256"],
        "first_verdict_read_only": True,
        "correlated_review": False,
        "completed_at": now,
        "coverage_cells": [
            cell("candidate_identity", "PASS", [assignment["candidate_binding"]["seal_path"], "git rev-parse HEAD; git rev-parse HEAD^{tree}"], "Frozen HEAD, tree, base, diff, changed-file, and production identities matched the assignment and seal."),
            cell("spec_before_execution", "PASS", ["docs/research_program/post_pr275/pr291_spec.yaml", "sha256:7b074bbb2f22ae62d2222e0bd8f62c0fd5253fe28ac5fca0ce45d956c0ac69ec"], "The registered spec was read and hash-verified before numerical execution."),
            cell("dependency_terminal_replay", "PASS", ["docs/research_program/post_pr275/data_runs/cf4/PR291_NONEXECUTION_RECEIPT.json", "python -B scripts/codex_harness/run_pr291_cf4_lane.py check"], "Replay stays typed BLOCKED_PREDECESSOR_FINAL_SUCCESS with no numerical output."),
            cell("data_identity_and_human_authorization_separation", "PASS", ["docs/research_program/post_pr275/pr291_spec.yaml", "docs/research_program/post_pr275/data_runs/cf4/PR291_NONEXECUTION_RECEIPT.json"], "Admission remains REJECTED_NOT_PRESENT and H-CF4 remains NOT_AUTHORIZED; neither substitutes for the other."),
            cell("preflight_before_first_write", "PASS", ["python -B scripts/codex_harness/run_pr291_cf4_lane.py focused", "tests/integration/test_cf4_post275_lane.py::test_runner_refuses_unsafe_destinations_before_payload_generation"], "Focused suite exercises output containment and passed 60 tests."),
            cell("synthetic_estimand_identity", "PASS", ["htt/obsstat/cf4_post275_lane.py:187", "tests/integration/test_cf4_post275_lane.py::test_operator_identity_is_exact_and_nonempty"], "The synthetic operator inventory is exact and does not present observed execution."),
            cell("group_row_selection_and_frame_conventions", "PASS", ["docs/research_program/post_pr275/pr291_spec.yaml", "python -B scripts/codex_harness/run_pr291_cf4_lane.py adjacent"], "Nine-role identity, frame, positive-receding sign, and units remain explicit; adjacent suite passed 189 tests."),
            cell("full_covariance_and_effective_rank", "PASS", [ORACLE_REL, "htt/obsstat/cf4_post275_lane.py:342", "htt/obsstat/cf4_post275_lane.py:1239"], "The oracle confirms fixed covariance-whitened column-normalized total-response rank, unit-column scale invariance, content binding, and a numerical null residual bound independent of the scientific rank floor."),
            cell("depth_zoa_nested_support_and_transport", "PASS", ["python -B scripts/codex_harness/run_pr291_cf4_lane.py focused", "tests/integration/test_cf4_post275_lane.py::test_depth_zoa_path_is_nested_and_identity_bound"], "Focused tests preserve nested support and bound row, covariance, ZoA, and transport identities."),
            cell("weak_identification_and_identified_set_abstention", "FAIL", [ORACLE_REL, "htt/obsstat/cf4_post275_lane.py:1380", "htt/obsstat/cf4_post275_lane.py:1401"], "The response/source gate equates a caller-declared LOCAL+GLOBAL joint rank to total response rank including NUISANCE. Identical LOCAL/GLOBAL columns with actual source joint rank one are accepted as declared joint rank two and emit a structural set."),
            cell("legacy_p0_and_curl_disposition", "PASS", ["htt/obsstat/cf4_post275_lane.py:1524", "tests/integration/test_cf4_post275_lane.py::test_gate_snapshot_and_legacy_curl_preserve_claim_ceiling"], "The 0.0089 value remains dimensionless legacy stencil self-consistency; vorticity and potential-flow claims are forbidden."),
            cell("blocked_no_numeric_output", "PASS", ["docs/research_program/post_pr275/data_runs/cf4/PR291_NONEXECUTION_RECEIPT.json", "python -B scripts/codex_harness/run_pr291_cf4_lane.py check"], "Receipt replay reports observed_data_executed false and an empty numeric_outputs_written list."),
            cell("portable_clean_integration", "PASS", [assignment["candidate_binding"]["seal_path"], "git status --short"], "Candidate seal records a clean frozen tree; assignment-local ignored evidence is the only review write."),
            cell("publication_policy_cross_binding", "PASS", ["docs/research_program/post_pr275/pr291_publication_policy.json", assignment["candidate_binding"]["seal_path"]], "The seal binds policy id PR291-PUBLICATION-POLICY and its registered hash."),
            cell("claim_and_family_ceiling", "PASS", ["docs/research_program/post_pr275/pr291_spec.yaml", "htt/obsstat/cf4_post275_lane.py:35", "docs/research_program/post_pr275/data_runs/cf4/PR291_NONEXECUTION_RECEIPT.json"], "OBSSTAT owns synthetic features only; no likelihood/prior/Q/F/G artifact is produced, transfer source is none, and family identification remains blocked pre-native-atlas."),
            cell("latest_target_integration", "PASS", [assignment["candidate_binding"]["seal_path"], "git merge-base 06ac20605ebc371b0f97ad6e91c802a51a9bf764 HEAD"], "The frozen candidate is based on the exact registered PR-290 sealed predecessor."),
        ],
        "independent_oracles": [
            {
                "kind": "invariant_checker",
                "status": "PASS",
                "oracle_id": "pr291-r4-physstat-hostile-oracle",
                "argv": argv,
                "command_fingerprint": canonical_sha({"argv": argv}),
                "returncode": 0,
                "timed_out": False,
                "started_at": "2026-08-13T06:44:44+00:00",
                "completed_at": "2026-08-13T06:44:44+00:00",
                "artifact_path": ORACLE_REL,
                "artifact_sha256": file_ref(ORACLE_REL)["sha256"],
                "artifact_bytes": file_ref(ORACLE_REL)["bytes"],
                "evidence_refs": [ORACLE_REL, ORACLE_SCRIPT_REL],
            }
        ],
    }
    coverage["coverage_sha256"] = canonical_sha(coverage)
    coverage_path = ROOT / COVERAGE_REL
    coverage_path.write_text(json.dumps(coverage, indent=2, sort_keys=True) + "\n")

    binding = assignment["candidate_binding"]
    finding_id = "F-PR291-R4-PHYSSTAT-SOURCE-RANK-PROVENANCE"
    result = {
        "schema_version": 3,
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "context_version": assignment["context_version"],
        "agent_type": assignment["agent_type"],
        "work_unit_id": assignment["work_unit_id"],
        "change_set_id": assignment["change_set_id"],
        "publication_group_id": assignment["publication_group_id"],
        "workflow_role": assignment["workflow_role"],
        "candidate_binding": binding,
        "independence_mode": assignment["independence_mode"],
        "status": "fail",
        "gate_disposition": "FAIL",
        "result_path": RESULT_REL,
        "assignment_sha256": assignment["assignment_sha256"],
        "launch_id": None,
        "launch_evidence": "unverified",
        "execution_evidence": "self_declared",
        "files_read": [
            assignment["candidate_binding"]["seal_path"],
            "docs/research_program/post_pr275/pr291_spec.yaml",
            "docs/PR_DELTAS/pr-291.md",
            "docs/codex_handoff/pr_status.yaml",
            "docs/research_program/post_pr275/data_runs/cf4/PR291_NONEXECUTION_RECEIPT.json",
            "docs/research_program/post_pr275/pr291_publication_policy.json",
            "docs/research_program/long_horizon_rescue/pr135_spec.yaml",
            "docs/research_program/long_horizon_rescue/pr136_spec.yaml",
            "htt/obsstat/cf4_post275_lane.py",
            "htt/src/common/cf4_observed_lane_activation.py",
            "htt/src/common/source_separation.py",
            "tests/integration/test_cf4_post275_lane.py",
            "scripts/codex_harness/run_pr291_cf4_lane.py",
            ".agent-harness/context/CONTEXT_INDEX.json",
            ".agent-harness/scripts/publication_integrity.py",
            ".agent-harness/scripts/strict_result_validation.py",
            ".agent-harness/scripts/review_coverage.py",
            ".agent-harness/templates/RESULT_ENVELOPE.json",
            ".agent-harness/README.md",
            ".agents/skills/htt-physmath-audit/SKILL.md",
            ".agents/skills/htt-physics-math-audit/SKILL.md",
            ".agents/skills/htt-statistical-hardening/SKILL.md",
            ".agents/skills/htt-scientific-code-validation/SKILL.md",
            ".agents/skills/htt-claim-firewall/SKILL.md",
            ".agents/skills/htt-claim-provenance-ledger/SKILL.md",
            ".agents/skills/htt-transfer-provenance/SKILL.md",
            ".agents/skills/htt-family-identification-gate/SKILL.md",
            ".agents/skills/htt-local-global-discrimination/SKILL.md",
            ".agents/skills/htt-xqpi-fg-formalism/SKILL.md",
        ],
        "files_read_evidence": "self_declared",
        "started_at": "2026-08-13T06:32:00+00:00",
        "completed_at": now,
        "tool_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pytest": pytest.__version__,
            "PyYAML": yaml.__version__,
        },
        "commands": [
            {"argv": argv, "returncode": 0, "result": "5 invariant checks pass; 1 expected hostile source-rank finding reproduced"},
            {"argv": ["python", "-B", "scripts/codex_harness/run_pr291_cf4_lane.py", "focused"], "returncode": 0, "result": "60 passed in 2.94s"},
            {"argv": ["python", "-B", "scripts/codex_harness/run_pr291_cf4_lane.py", "adjacent"], "returncode": 0, "result": "189 passed in 54.41s"},
            {"argv": ["python", "-B", "scripts/codex_harness/run_pr291_cf4_lane.py", "check"], "returncode": 0, "result": "BLOCKED_PREDECESSOR_FINAL_SUCCESS; no observed/numeric/network side effect"},
        ],
        "artifacts": [
            file_ref(COVERAGE_REL),
            file_ref(ORACLE_SCRIPT_REL),
            file_ref(ORACLE_REL),
        ],
        "review_coverage_path": COVERAGE_REL,
        "review_coverage_sha256": file_ref(COVERAGE_REL)["sha256"],
        "findings": [
            {
                "finding_id": finding_id,
                "claim_id": "C-PR136-IDENTIFIED-SET",
                "verdict": "fail",
                "severity": "high",
                "statement": "The typed response/source binding does not derive LOCAL/GLOBAL component ranks, their joint rank, principal angles, or joint singular values from the covariance-whitened response columns selected by parameter_roles. It only compares the caller-declared source joint_rank to total response rank, which includes NUISANCE. Consequently identical LOCAL and GLOBAL columns (actual source joint rank 1) plus an independent NUISANCE column (total response rank 2) accept a declared source joint rank 2, yield WEAKLY_IDENTIFIED, and permit a BOUNDED_BUT_NOT_POINT_IDENTIFIED structural set. The repaired total rank/nullity equality therefore does not establish the claimed typed local/global rank provenance.",
                "assumptions_used": [
                    "parameter_roles identify the response columns whose LOCAL/GLOBAL source ranks must be reconciled",
                    "the registered covariance is SPD and passes the declared condition ceiling",
                    "source separation is diagnostic-only and must fail closed when source geometry is not derived from bound response bytes",
                ],
                "evidence_refs": [
                    ORACLE_REL,
                    "htt/obsstat/cf4_post275_lane.py:1260",
                    "htt/obsstat/cf4_post275_lane.py:1390",
                    "htt/obsstat/cf4_post275_lane.py:1401",
                    "htt/src/common/source_separation.py:315",
                ],
                "evidence_fingerprint": "pr291-r4:typed-local-global-role-rank-vs-total-response-rank:nuisance-counterexample-v1",
                "counterevidence_refs": [
                    "tests/integration/test_cf4_post275_lane.py::test_gate_replays_null_basis_and_exact_source_rank",
                    "tests/integration/test_cf4_post275_lane.py::test_response_rank_is_whitened_column_scale_invariant_and_roles_are_typed",
                ],
                "reproduction": [
                    "Construct response [[1,1,0],[0,0,1]] with roles LOCAL,GLOBAL,NUISANCE and SPD covariance [[1,.2],[.2,1]].",
                    "Observe covariance-whitened column-normalized total response_rank=2 and nullity=1, while numpy matrix_rank(response[:, LOCAL+GLOBAL])=1.",
                    "Create SourceSeparationDecision with declared local_rank=1, global_rank=1, joint_rank=2 and the response normalizer_id.",
                    "Call build_structural_identified_set; it returns BOUNDED_BUT_NOT_POINT_IDENTIFIED instead of rejecting the source-rank mismatch.",
                    f"Run: PYTHONPATH=htt/src:htt:. {' '.join(argv)}",
                ],
                "confidence": 0.99,
                "unresolved": [
                    "A defensible repair must compute or content-bind source component design matrices and derive local/global/joint rank plus angle/singular geometry under the same whitening and normalization contract; merely adding another declared rank field is insufficient."
                ],
            }
        ],
        "claim_results": [
            {
                "claim_id": "C-PR135-FINITE-NULL-RANK",
                "outcome": "examined_no_findings",
                "finding_ids": [],
                "summary": "Within the assigned PR-291 numerical slice, fixed relative thresholds, covariance-whitened column-normalized total-response rank, scale invariance, content binding, and machine-epsilon null replay passed. This does not revalidate the broader historical finite-null p-value claim.",
                "evidence_refs": [ORACLE_REL, "python -B scripts/codex_harness/run_pr291_cf4_lane.py focused"],
                "evidence_fingerprint": "pr291-r4:fixed-threshold-total-rank-null-replay-oracle-v1",
            },
            {
                "claim_id": "C-PR136-IDENTIFIED-SET",
                "outcome": "findings_present",
                "finding_ids": [finding_id],
                "summary": "FAIL: a caller-declared source geometry inconsistent with typed response-role columns is accepted and can drive a structural identified set.",
            },
        ],
        "errors": [],
    }
    (ROOT / RESULT_REL).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
