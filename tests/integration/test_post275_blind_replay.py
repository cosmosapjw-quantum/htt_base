"""PR-287 fresh-blind contract tests without fresh scientific execution."""

from __future__ import annotations

from copy import copy
import hashlib
import json
from pathlib import Path
import os
import subprocess
import sys
import types

import pytest
import yaml

from common.post275_blind_replay import (
    BlindReplayContractError,
    BlindReplayStage,
    BlindReplayPackKind,
    DependencyActivationStatus,
    HistoricalReplayReceipt,
    SubmissionFreezeReceipt,
    TruthVaultReference,
    build_dependency_activation_receipt,
    build_fresh_challenge,
    build_frozen_submission,
    build_historical_replay_receipt,
    build_pillar_row_projection,
    build_registered_case_analysis_results,
    build_common_pack_a,
    build_stage_trace,
    build_submission_freeze_receipt,
    build_typed_scenario_bank,
    build_truth_vault_reference,
    canonical_json_sha256,
    covariance_matrix_content_id,
    diagnostic_surface_content_id,
    require_dependency_activation,
    validate_fresh_challenge,
    validate_frozen_submission,
    validate_historical_replay_receipt,
    validate_pillar_row_projection,
    validate_registered_case_analysis_results,
    validate_diagnostic_pack,
    validate_stage_trace,
    validate_submission_freeze_receipt,
    validate_typed_scenario_bank,
    validate_truth_vault_reference,
)
from htt.infer.post275_blind_replay import analyze_fresh_challenge
from htt.infer.post275_blind_replay import build_htt_pack_b
from mio.reports.post275_blind_replay import build_mio_pack_c


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/post_pr275/pr287_spec.yaml"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"
CASE_IDS = (
    "D01",
    "D02",
    "D03",
    "D04",
    "H01",
    "H02",
    "H03",
    "H04",
    "H05",
    "H06",
    "H07",
    "H08",
)


def _id(label: str) -> str:
    return canonical_json_sha256({"label": label})


def _write_activated_contract(tmp_path: Path) -> tuple[Path, Path]:
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=tmp_path,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout.strip()

    remote = tmp_path.parent / f"{tmp_path.name}-remote.git"
    subprocess.run(
        ["git", "init", "--bare", str(remote)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    git("init", "-b", "research/pr04-multicomponent")
    git("config", "user.name", "PR-287 Scratch")
    git("config", "user.email", "pr287-scratch@example.invalid")
    (tmp_path / ".gitignore").write_text(
        "\n".join(
            (
                ".agent-harness/context/",
                ".agent-harness/runs/",
                ".codex/",
                ".prguard/",
                "docs/",
                "historical/",
                "",
            )
        ),
        encoding="utf-8",
    )
    git("add", ".gitignore")
    git("commit", "-m", "scratch target")
    git("remote", "add", "origin", str(remote))
    git("push", "-u", "origin", "research/pr04-multicomponent")
    git("fetch", "origin")
    git("switch", "-c", "changeset/pr287-scratch")
    (tmp_path / "candidate.txt").write_text("candidate\n", encoding="utf-8")
    git("add", "candidate.txt")
    git("commit", "-m", "scratch candidate")
    git(
        "remote",
        "set-url",
        "--push",
        "origin",
        "https://github.com/example/pr287-scratch.git",
    )
    candidate_sha = git("rev-parse", "HEAD")
    scratch_context_version = hashlib.sha256(
        b"pr287-activated-contract-context"
    ).hexdigest()
    context_index = tmp_path / ".agent-harness/context/CONTEXT_INDEX.json"
    context_index.parent.mkdir(parents=True, exist_ok=True)
    context_index.write_text(
        json.dumps({"context_version": scratch_context_version}) + "\n",
        encoding="utf-8",
    )
    claim_registry = tmp_path / ".agent-harness/context/CLAIM_REGISTRY.jsonl"
    claim_registry.write_text(
        json.dumps({"claim_id": "SCRATCH-REGISTERED-CLAIM"}) + "\n",
        encoding="utf-8",
    )
    profile = tmp_path / ".codex/agents/default.toml"
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_text(
        'name = "default"\nsandbox_mode = "read-only"\n',
        encoding="utf-8",
    )
    harness_scripts = ROOT / ".agent-harness/scripts"
    inserted_harness_path = False
    if str(harness_scripts) not in sys.path:
        sys.path.insert(0, str(harness_scripts))
        inserted_harness_path = True
    try:
        import publication_integrity
    finally:
        if inserted_harness_path:
            sys.path.remove(str(harness_scripts))
    terminal_contracts = {
        "PR-281": ("docs/PR_DELTAS/pr-281.md", None),
        "PR-282": (
            "docs/generated/pr282_exact_parity_readiness_receipt.json",
            "PASS_EXECUTABLE_P_EQUIVARIANCE",
        ),
        "PR-283": (
            "docs/generated/pr283_weak_identification_receipt.json",
            "PASS_WEAK_IDENTIFICATION_ABSTENTION",
        ),
        "PR-284": (
            "docs/generated/pr284_depth_path_doob_receipt.json",
            "PASS_PREMISE_BOUND_DEPTH_PATH_CALIBRATION",
        ),
        "PR-285": (
            "docs/research_program/post_pr275/pillar_t_adjudication/"
            "PILLAR_T_COMPLETE_ADJUDICATION_V1.json",
            "PASS_COMPLETE_PILLAR_T_ADJUDICATION",
        ),
        "PR-286": (
            "docs/research_program/post_pr275/pillar_s_adjudication/"
            "PILLAR_S_COMPLETE_ADJUDICATION_V1.json",
            "PASS_COMPLETE_PILLAR_S_ADJUDICATION",
        ),
    }
    contracts = []
    resolutions = {}
    completed = []
    for index, pr_id in enumerate(
        ("PR-281", "PR-282", "PR-283", "PR-284", "PR-285", "PR-286"),
        start=1,
    ):
        terminal_path, terminal = terminal_contracts[pr_id]
        receipt = tmp_path / terminal_path
        receipt.parent.mkdir(parents=True, exist_ok=True)
        if pr_id == "PR-281":
            receipt.write_text("# PR-281\n\nCloseout receipt.\n", encoding="utf-8")
        else:
            terminal_payload = {
                "PR-282": {
                    "readiness_receipt": {
                        "terminal": {"g3_outcome": terminal}
                    }
                },
                "PR-283": {"terminal": {"g4_outcome": terminal}},
                "PR-284": {"terminal_status": terminal},
                "PR-285": {"terminal": terminal},
                "PR-286": {"terminal": terminal},
            }[pr_id]
            receipt.write_text(
                json.dumps(terminal_payload, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        status_receipt = tmp_path / "docs/PR_DELTAS" / f"{pr_id.lower()}.md"
        if pr_id == "PR-281":
            status_receipt = receipt
        else:
            status_receipt.parent.mkdir(parents=True, exist_ok=True)
            status_receipt.write_text(f"# {pr_id}\n", encoding="utf-8")
        run_id = f"{pr_id.lower()}-candidate-review"
        assignment_id = f"{pr_id.lower()}_candidate_review"
        context_version = scratch_context_version
        run_dir = tmp_path / ".agent-harness/runs" / run_id
        review_receipt = run_dir / "RUN_SUMMARY.json"
        assignment_path = run_dir / "assignments" / f"{assignment_id}.json"
        result_path = run_dir / "results" / f"{assignment_id}.json"
        coverage_path = (
            run_dir / "artifacts" / assignment_id / "REVIEW_COVERAGE.json"
        )
        review_receipt.parent.mkdir(parents=True, exist_ok=True)
        assignment_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.parent.mkdir(parents=True, exist_ok=True)
        coverage_path.parent.mkdir(parents=True, exist_ok=True)
        result_relative = str(result_path.relative_to(tmp_path))
        coverage_relative = str(coverage_path.relative_to(tmp_path))
        seal_path = run_dir / "CANDIDATE_SEAL.json"
        policy_path = run_dir / "PUBLICATION_POLICY.json"
        run_plan_path = run_dir / "RUN_PLAN.json"
        seal_relative = str(seal_path.relative_to(tmp_path))
        policy_relative = str(policy_path.relative_to(tmp_path))
        policy_payload = {
            "schema_version": 1,
            "policy_id": f"{pr_id.lower()}-scratch-review-policy",
            "max_open_prs": 1,
            "max_direct_to_target_prs": 0,
            "max_prs_per_change_set": 1,
            "max_stack_depth": 1,
            "max_file_overlap_prs": 0,
            "max_inventory_age_seconds": 300,
            "max_receipt_age_seconds": 300,
            "max_authorization_ttl_seconds": 300,
            "required_review_cells": ["candidate_identity"],
            "required_commands": [
                {
                    "id": "scratch-review-evidence",
                    "argv": ["python3", "-B", "-m", "pytest", "--version"],
                    "timeout_seconds": 30,
                }
            ],
        }
        policy_path.write_text(
            json.dumps(policy_payload, sort_keys=True) + "\n", encoding="utf-8"
        )
        seal_payload = publication_integrity.build_candidate_seal(
            tmp_path,
            change_set_id=f"CS-{pr_id}",
            publication_group_id=f"PG-{pr_id}",
            target_ref="origin/research/pr04-multicomponent",
            candidate_ref="HEAD",
            integration_policy_path=policy_relative,
        )
        seal_path.write_text(
            json.dumps(seal_payload, sort_keys=True) + "\n", encoding="utf-8"
        )
        seal_file_sha = hashlib.sha256(seal_path.read_bytes()).hexdigest()
        candidate_binding = publication_integrity.candidate_binding_from_payload(
            seal_payload,
            seal_path=seal_relative,
            seal_file_sha256=seal_file_sha,
        )
        candidate_tree_sha = str(seal_payload["candidate_tree_sha"])
        seal_sha = str(seal_payload["seal_sha256"])
        diff_sha = str(seal_payload["diff_sha256"])
        changed_files_sha = str(seal_payload["changed_files_sha256"])
        policy_sha = hashlib.sha256(policy_path.read_bytes()).hexdigest()
        run_plan_path.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "run_id": run_id,
                    "context_version": context_version,
                    "work_unit_id": pr_id,
                    "change_set_id": f"CS-{pr_id}",
                    "publication_group_id": f"PG-{pr_id}",
                    "target_remote": "origin",
                    "target_branch": "research/pr04-multicomponent",
                    "target_ref": (
                        "refs/remotes/origin/research/pr04-multicomponent"
                    ),
                    "base_sha": seal_payload["base_sha"],
                    "candidate_ref": "refs/heads/changeset/pr287-scratch",
                    "spec_ref": terminal_path,
                    "budget": {
                        "max_concurrent": 4,
                        "max_total": 8,
                        "max_total_per_work_unit": 8,
                        "max_depth": 2,
                    },
                    "candidate_binding": candidate_binding,
                    "integration_policy": {
                        "path": policy_relative,
                        "sha256": policy_sha,
                        "policy_id": policy_payload["policy_id"],
                    },
                    "publication_budget": {
                        field: policy_payload[field]
                        for field in (
                            "max_open_prs",
                            "max_direct_to_target_prs",
                            "max_prs_per_change_set",
                            "max_stack_depth",
                            "max_file_overlap_prs",
                        )
                    },
                    "publication_mode": "external_publisher_only",
                    "github_pr_created_by_harness": False,
                    "status": "candidate_frozen",
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        claim_id = f"RUN-{run_id}-REVIEW"
        assignment = {
            "schema_version": 3,
            "run_id": run_id,
            "assignment_id": assignment_id,
            "agent_type": "default",
            "context_version": context_version,
            "work_unit_id": pr_id,
            "change_set_id": f"CS-{pr_id}",
            "publication_group_id": f"PG-{pr_id}",
            "workflow_role": "reviewer",
            "candidate_binding": candidate_binding,
            "independence_mode": "blind-results",
            "risk_tier": "R3",
            "claim_ids": [claim_id],
            "task": f"Review the sealed {pr_id} predecessor candidate.",
            "required_inputs": [
                {
                    "path": terminal_path,
                    "sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
                }
            ],
            "allowed_tools": ["read-only shell", "pytest"],
            "required_outputs": [
                "schema-v3 reviewer result envelope",
                "exact policy-cell REVIEW_COVERAGE artifact",
            ],
            "result_path": result_relative,
            "status": "registered",
        }
        assignment["assignment_sha256"] = hashlib.sha256(
            json.dumps(
                assignment, sort_keys=True, ensure_ascii=False
            ).encode("utf-8")
        ).hexdigest()
        assignment_path.write_text(
            json.dumps(assignment, sort_keys=True) + "\n", encoding="utf-8"
        )
        coverage = {
            "schema_version": 1,
            "run_id": run_id,
            "assignment_id": assignment_id,
            "change_set_id": f"CS-{pr_id}",
            "publication_group_id": f"PG-{pr_id}",
            "candidate_seal_sha256": seal_sha,
            "candidate_sha": candidate_sha,
            "candidate_tree_sha": candidate_tree_sha,
            "diff_sha256": diff_sha,
            "changed_files_sha256": changed_files_sha,
            "first_verdict_read_only": True,
            "correlated_review": False,
            "completed_at": "2026-08-09T00:00:00+00:00",
            "coverage_cells": [
                {
                    "cell": "candidate_identity",
                    "status": "PASS",
                    "evidence_refs": ["sealed predecessor candidate matched"],
                    "rationale": "Exact registered candidate binding matched.",
                }
            ],
            "independent_oracles": [],
        }
        oracle_path = run_dir / "artifacts" / assignment_id / "ORACLE.json"
        oracle_path.write_text("{}\n", encoding="utf-8")
        oracle_relative = str(oracle_path.relative_to(tmp_path))
        oracle_argv = ["python3", "-B", "-m", "pytest", "--version"]
        coverage["independent_oracles"] = [
            {
                "kind": "invariant_checker",
                "status": "PASS",
                "oracle_id": f"{pr_id.lower()}-scratch-review-oracle",
                "argv": oracle_argv,
                "command_fingerprint": hashlib.sha256(
                    json.dumps(
                        {"argv": oracle_argv},
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ).encode("utf-8")
                ).hexdigest(),
                "returncode": 0,
                "timed_out": False,
                "started_at": "2026-08-09T00:00:00+00:00",
                "completed_at": "2026-08-09T00:00:01+00:00",
                "artifact_path": oracle_relative,
                "artifact_sha256": hashlib.sha256(
                    oracle_path.read_bytes()
                ).hexdigest(),
                "artifact_bytes": oracle_path.stat().st_size,
                "evidence_refs": [oracle_relative],
            }
        ]
        coverage["coverage_sha256"] = hashlib.sha256(
            json.dumps(
                coverage,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        coverage_path.write_text(
            json.dumps(coverage, sort_keys=True) + "\n", encoding="utf-8"
        )
        coverage_sha = hashlib.sha256(coverage_path.read_bytes()).hexdigest()
        result_path.write_text(
            json.dumps(
                {
                    "schema_version": 3,
                    "run_id": run_id,
                    "assignment_id": assignment_id,
                    "agent_type": "default",
                    "context_version": context_version,
                    "status": "pass",
                    "work_unit_id": pr_id,
                    "change_set_id": f"CS-{pr_id}",
                    "publication_group_id": f"PG-{pr_id}",
                    "workflow_role": "reviewer",
                    "candidate_binding": candidate_binding,
                    "independence_mode": "blind-results",
                    "result_path": result_relative,
                    "assignment_sha256": assignment["assignment_sha256"],
                    "launch_id": None,
                    "launch_evidence": "unverified",
                    "execution_evidence": "self_declared",
                    "files_read": [],
                    "files_read_evidence": "self_declared",
                    "started_at": "2026-08-09T00:00:00+00:00",
                    "completed_at": "2026-08-09T00:01:00+00:00",
                    "tool_versions": {"python": sys.version.split()[0]},
                    "commands": [],
                    "artifacts": [
                        {
                            "path": coverage_relative,
                            "sha256": coverage_sha,
                            "bytes": coverage_path.stat().st_size,
                            "producer": assignment_id,
                        },
                        {
                            "path": oracle_relative,
                            "sha256": hashlib.sha256(
                                oracle_path.read_bytes()
                            ).hexdigest(),
                            "bytes": oracle_path.stat().st_size,
                            "producer": assignment_id,
                        },
                    ],
                    "review_coverage_path": coverage_relative,
                    "review_coverage_sha256": coverage_sha,
                    "findings": [],
                    "claim_results": [
                        {
                            "claim_id": claim_id,
                            "outcome": "examined_no_findings",
                            "finding_ids": [],
                            "summary": "The sealed predecessor review passed.",
                            "evidence_refs": [coverage_relative],
                            "evidence_fingerprint": f"{pr_id.lower()}-sealed-review-pass",
                        }
                    ],
                    "errors": [],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        review_receipt.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "run_id": run_id,
                    "context_version": context_version,
                    "work_unit_id": pr_id,
                    "candidate_binding": candidate_binding,
                    "results": [
                        {
                            "assignment_id": assignment_id,
                            "status": "pass",
                            "path": result_relative,
                            "sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        contract = {
            "upstream_id": pr_id,
            "mode": "requires_success",
            "required_resolution": "COMPLETED_SUCCESS",
            "required_receipt": terminal_path,
        }
        if pr_id != "PR-281":
            contract["required_terminal"] = terminal
        contracts.append(contract)
        completed.append(pr_id)
        resolutions[pr_id] = {
            "resolution": "COMPLETED_SUCCESS",
            "success_dependency_satisfied": True,
            "candidate_sha": candidate_sha,
            "receipt": str(receipt.relative_to(tmp_path)),
            "review_receipt": str(review_receipt.relative_to(tmp_path)),
            "observed_data_executed": False,
            "public_use": False,
        }
        resolutions[pr_id]["receipt"] = str(status_receipt.relative_to(tmp_path))
    spec = tmp_path / "docs/research_program/post_pr275/pr287_spec.yaml"
    status = tmp_path / "docs/codex_handoff/pr_status.yaml"
    spec.parent.mkdir(parents=True, exist_ok=True)
    status.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(
        yaml.safe_dump(
            {
                "pr_id": "PR-287",
                "dependencies": list(terminal_contracts),
                "dependency_contracts": contracts,
                "activation_contract": {
                    "required_predecessor_state": "COMPLETED_SUCCESS"
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    status.write_text(
        yaml.safe_dump(
            {
                "completed": completed,
                "pending": ["PR-287"],
                "execution_resolutions": resolutions,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return spec, status


def _promote_to_stacked_pr_open_authority(
    spec: Path, status: Path
) -> tuple[Path, Path]:
    """Add the Phase-2 exact-sealed stacked authority to a scratch contract."""

    spec_payload = yaml.safe_load(spec.read_text(encoding="utf-8"))
    status_payload = yaml.safe_load(status.read_text(encoding="utf-8"))
    resolutions = status_payload["execution_resolutions"]
    sealed = {
        pr_id: resolutions[pr_id]["candidate_sha"]
        for pr_id in ("PR-283", "PR-284", "PR-285", "PR-286")
    }
    canonical_target = "0" * 40
    spec_payload["activation_contract"] = {
        "authority_mode": "STACKED_PR_OPEN_EXACT_SEALED_HEAD",
        "canonical_target_sha": canonical_target,
        "required_predecessor_state": "PR_OPEN",
        "required_predecessor_sealed_sha": sealed["PR-286"],
        "review_evidence_role": "HISTORICAL_PROVENANCE_ONLY",
    }
    lifecycle = [
        "PLANNED",
        "ACTIVE",
        "IMPLEMENTED",
        "VALIDATED",
        "REVIEWED",
        "SEALED",
        "PUSHED",
        "PR_OPEN",
    ]
    rows = {}
    previous_id = None
    previous_sha = canonical_target
    for pr_id in ("PR-283", "PR-284", "PR-285", "PR-286"):
        rows[pr_id] = {
            "lifecycle": "PR_OPEN",
            "lifecycle_history": lifecycle,
            "base_sha": previous_sha,
            "predecessor_pr": previous_id,
            "predecessor_sealed_sha": None if previous_id is None else previous_sha,
            "sealed_head": sealed[pr_id],
            "pushed_ref": f"refs/heads/changeset/{pr_id.lower()}-scratch",
            "pr_url": f"https://github.com/example/repo/pull/{pr_id[3:]}",
            "gate_dispositions": {
                key: "PASS"
                for key in (
                    "eligibility",
                    "implementation",
                    "validation",
                    "review",
                    "seal",
                    "push",
                    "publication",
                )
            },
            "assurance_budget": {"maximum": 16, "consumed": 1},
        }
        resolutions[pr_id].update(
            {
                "sealed_head": sealed[pr_id],
                "pushed_ref": rows[pr_id]["pushed_ref"],
                "pr_url": rows[pr_id]["pr_url"],
            }
        )
        previous_id = pr_id
        previous_sha = sealed[pr_id]
    rows["PR-287"] = {
        "lifecycle": "ACTIVE",
        "lifecycle_history": ["PLANNED", "ACTIVE"],
        "base_sha": sealed["PR-286"],
        "predecessor_pr": "PR-286",
        "predecessor_sealed_sha": sealed["PR-286"],
        "assurance_budget": {"maximum": 16, "consumed": 0},
    }
    status_payload["stacked_pr_execution"] = {
        "execution_mode": "AUTO_STACKED_PR",
        "merge_policy": "HUMAN_ONLY",
        "target_sha": canonical_target,
        "active_implementation_pr": "PR-287",
        "active_implementation_prs": ["PR-287"],
        "pr_order": [
            "PR-283",
            "PR-284",
            "PR-285",
            "PR-286",
            "PR-287",
        ],
        "prs": rows,
    }
    spec.write_text(
        yaml.safe_dump(spec_payload, sort_keys=False), encoding="utf-8"
    )
    status.write_text(
        yaml.safe_dump(status_payload, sort_keys=False), encoding="utf-8"
    )
    return spec, status


def _activated_receipt(tmp_path: Path):
    spec, status = _write_activated_contract(tmp_path)
    receipt = build_dependency_activation_receipt(
        spec_path=spec,
        status_path=status,
        repository_root=tmp_path,
    )
    assert receipt.status is DependencyActivationStatus.ACTIVATED
    return receipt


def _case_payloads() -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "case_id": case_id,
            "observable_vector": [float(index), -float(index)],
            "covariance_id": _id(f"covariance:{case_id}"),
            "mask_id": _id(f"mask:{case_id}"),
        }
        for index, case_id in enumerate(CASE_IDS, start=1)
    )


def _scenario_bank():
    scenario_contracts = (
        ("SCALAR_LIMIT", "scalar_limit_crosswalk", "NOT_APPLICABLE"),
        ("TENSOR_ONLY", "tensor_channel_response", "NOT_APPLICABLE"),
        ("MISSING_CHANNEL", "typed_missingness", "REQUIRED_ABSTENTION"),
        ("COVARIANCE_CORRECT", "covariance_calibrated_coverage", "CALIBRATED_CONTROL"),
        (
            "COVARIANCE_MISSPECIFIED_PAIRED",
            "paired_covariance_failure_visibility",
            "MISSPECIFIED_NEGATIVE_CONTROL",
        ),
        ("MULTIPLICITY_STRESS", "familywise_error_control", "SIMULTANEOUS_FAILURE_VISIBLE"),
        ("COVERAGE_FAILURE", "registered_interval_coverage", "COVERAGE_FAILURE_VISIBLE"),
        ("WEAK_LOCAL_GLOBAL_OVERLAP", "source_separation_abstention", "TYPE_UNIDENTIFIED"),
        ("SEPARATED_LOCAL_GLOBAL", "source_separation_candidate_eligibility", "NOT_APPLICABLE"),
        ("OPEN_SET_UNKNOWN", "open_set_unknown_abstention", "UNKNOWN_CLASS"),
        ("PROVED_DEPTH_PATH", "premise_bound_depth_calibration", "NOT_APPLICABLE"),
        ("PREMISE_MISSING_DEPTH_PATH", "depth_bound_unavailability", "MATCHED_MOCKS_REQUIRED"),
    )
    shared_law = _id("paired-covariance-law")
    shared_covariance_matrix = [[1.0, 0.2], [0.2, 1.5]]
    misspecified_covariance_matrix = [[1.0, 0.0], [0.0, 1.5]]
    shared_latent = _id("paired-latent-draws")
    scenarios = []
    for index, (scenario_id, estimand, terminal) in enumerate(scenario_contracts):
        paired = scenario_id in {
            "COVARIANCE_CORRECT",
            "COVARIANCE_MISSPECIFIED_PAIRED",
        }
        generator_matrix = (
            shared_covariance_matrix
            if paired
            else [[1.0 + 0.01 * index, 0.05], [0.05, 1.2 + 0.01 * index]]
        )
        analysis_matrix = generator_matrix
        if scenario_id == "COVARIANCE_MISSPECIFIED_PAIRED":
            analysis_matrix = misspecified_covariance_matrix
        generator = covariance_matrix_content_id(generator_matrix)
        analysis = covariance_matrix_content_id(analysis_matrix)
        scenarios.append(
            {
                "scenario_id": scenario_id,
                "partition": "development" if index < 4 else "held_out",
                "data_generating_law_id": shared_law if paired else _id(f"law:{scenario_id}"),
                "estimand_id": estimand,
                "analysis_unit": "one_complete_synthetic_challenge_case",
                "covariance_generator_id": generator,
                "covariance_analysis_id": analysis,
                "covariance_generator_matrix": generator_matrix,
                "covariance_analysis_matrix": analysis_matrix,
                "latent_draw_inventory_id": shared_latent if paired else _id(f"latent:{scenario_id}"),
                "replicate_or_exact_enumeration_rule": "512_independent_replicates",
                "exact_enumeration_cell_ids": [],
                "seed_policy_id": "PR287-CRYPTO-SEED-DERIVATION-V1",
                "hypothesis_family_id": "PR287-HELDOUT-FAMILY-V1",
                "alpha": 0.05,
                "simultaneous_method": "Holm-Bonferroni_FWER",
                "acceptance_rule_id": _id(f"accept:{scenario_id}"),
                "expected_negative_control_terminal": terminal,
                "mc_precision_rule_id": "PR287-EXACT-BINOMIAL-HALFWIDTH-004-V1",
            }
        )
    bank = build_typed_scenario_bank(
        scenarios=scenarios,
        case_to_scenario=dict(
            zip(CASE_IDS, (row[0] for row in scenario_contracts), strict=True)
        ),
    )
    assert validate_typed_scenario_bank(bank) is bank
    return bank


def _analysis_inputs(bank=None) -> tuple[dict[str, object], ...]:
    if bank is None:
        bank = _scenario_bank()
    scenario_by_case = {
        row["case_id"]: next(
            scenario
            for scenario in bank.scenarios
            if scenario["scenario_id"] == row["scenario_id"]
        )
        for row in bank.case_assignments
    }
    return tuple(
        {
            "case_id": case_id,
            "supported_quotient": True,
            "response_provider_available": True,
            "local_response_rank": 1,
            "global_response_rank": 1,
            "joint_response_rank": 2,
            "response_class_cardinality": 1,
            "minimum_principal_angle": 0.5,
            "weak_angle_threshold": 0.2,
            "weak_identification": False,
            "unknown_distance": 0.1,
            "unknown_distance_threshold": 1.0,
            "response_equivalence": False,
            "margin_abstention": False,
            "depth_premise_status": "PROVED",
            "finite_depth_bound": 0.5,
            "matched_mock_status": "NOT_REQUIRED",
            "covariance_status": (
                "MISSPECIFIED_NEGATIVE_CONTROL"
                if scenario_by_case[case_id]["scenario_id"]
                == "COVARIANCE_MISSPECIFIED_PAIRED"
                else "REGISTERED_VALID"
            ),
            "raw_p_value": min(0.99, 0.01 * (index + 1)),
            "coverage_evidence_mode": scenario_by_case[case_id][
                "replicate_or_exact_enumeration_rule"
            ],
            "coverage_cell_results": [1] * 512,
        }
        for index, case_id in enumerate(CASE_IDS)
    )


def _case_results():
    bank = _scenario_bank()
    rows = build_registered_case_analysis_results(
        _analysis_inputs(bank), scenario_bank=bank
    )
    assert validate_registered_case_analysis_results(
        rows, scenario_bank=bank
    ) == rows
    return rows


def test_live_activation_uses_exact_pr_open_sealed_chain() -> None:
    receipt = build_dependency_activation_receipt(
        spec_path=SPEC,
        status_path=STATUS,
        repository_root=ROOT,
    )
    assert receipt.status is DependencyActivationStatus.ACTIVATED
    assert receipt.terminal == "ACTIVATED_PREDECESSOR_FINAL_SUCCESS"
    assert all(row.satisfied for row in receipt.predecessor_rows)
    mutant = copy(receipt)
    object.__setattr__(mutant, "status", DependencyActivationStatus.BLOCKED)
    object.__setattr__(mutant, "terminal", "BLOCKED_PREDECESSOR_FINAL_SUCCESS")
    with pytest.raises(BlindReplayContractError, match="identity drifted"):
        require_dependency_activation(mutant)


@pytest.mark.parametrize(
    ("mutation", "reason"),
    (
        ("lifecycle", "exact PR_OPEN lifecycle"),
        ("sealed_head", "sealed head"),
        ("base", "exact predecessor sealed head"),
        ("publication", "publication gate"),
        ("active", "only active implementation"),
    ),
)
def test_stacked_activation_rejects_lifecycle_chain_drift(
    tmp_path: Path, mutation: str, reason: str
) -> None:
    spec, status = _promote_to_stacked_pr_open_authority(
        *_write_activated_contract(tmp_path)
    )
    payload = yaml.safe_load(status.read_text(encoding="utf-8"))
    stack = payload["stacked_pr_execution"]
    if mutation == "lifecycle":
        stack["prs"]["PR-285"]["lifecycle"] = "SEALED"
    elif mutation == "sealed_head":
        stack["prs"]["PR-285"]["sealed_head"] = "f" * 40
    elif mutation == "base":
        stack["prs"]["PR-286"]["base_sha"] = "e" * 40
    elif mutation == "publication":
        stack["prs"]["PR-284"]["gate_dispositions"]["publication"] = "FAIL"
    else:
        stack["active_implementation_prs"] = ["PR-287", "PR-288"]
    status.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    receipt = build_dependency_activation_receipt(
        spec_path=spec,
        status_path=status,
        repository_root=tmp_path,
    )
    assert receipt.status is DependencyActivationStatus.BLOCKED
    assert any(reason in item for item in receipt.reasons)


def test_activation_requires_exact_regular_receipt_and_terminal(tmp_path: Path) -> None:
    spec, status = _write_activated_contract(tmp_path)
    activated = build_dependency_activation_receipt(
        spec_path=spec,
        status_path=status,
        repository_root=tmp_path,
    )
    assert activated.status is DependencyActivationStatus.ACTIVATED
    missing = tmp_path / "docs/generated/pr284_depth_path_doob_receipt.json"
    missing.unlink()
    blocked = build_dependency_activation_receipt(
        spec_path=spec,
        status_path=status,
        repository_root=tmp_path,
    )
    assert blocked.status is DependencyActivationStatus.BLOCKED
    assert any("PR-284" in reason and "receipt" in reason for reason in blocked.reasons)


def test_activation_rejects_pass_summary_over_failing_result_envelope(
    tmp_path: Path,
) -> None:
    spec, status = _write_activated_contract(tmp_path)
    status_payload = yaml.safe_load(status.read_text(encoding="utf-8"))
    summary_path = tmp_path / status_payload["execution_resolutions"]["PR-282"][
        "review_receipt"
    ]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    result_path = tmp_path / summary["results"][0]["path"]
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["status"] = "fail"
    result_path.write_text(json.dumps(result) + "\n", encoding="utf-8")
    summary["results"][0]["sha256"] = hashlib.sha256(
        result_path.read_bytes()
    ).hexdigest()
    summary_path.write_text(json.dumps(summary) + "\n", encoding="utf-8")

    receipt = build_dependency_activation_receipt(
        spec_path=spec,
        status_path=status,
        repository_root=tmp_path,
    )
    assert receipt.status is DependencyActivationStatus.BLOCKED
    assert any(
        "review result envelope contradicts" in reason
        for reason in receipt.reasons
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "result_schema",
        "stale_assignment_context",
        "wrong_internal_result_path",
        "duplicate_result_path",
        "missing_result_field",
        "failing_review_coverage",
        "invented_review_coverage",
        "malformed_extra_artifact",
        "blind_sibling_artifact",
    ),
)
def test_activation_rejects_unregistered_review_result_evidence(
    tmp_path: Path, mutation: str
) -> None:
    spec, status = _write_activated_contract(tmp_path)
    status_payload = yaml.safe_load(status.read_text(encoding="utf-8"))
    summary_path = tmp_path / status_payload["execution_resolutions"]["PR-282"][
        "review_receipt"
    ]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    row = summary["results"][0]
    result_path = tmp_path / row["path"]
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assignment_path = (
        tmp_path
        / ".agent-harness/runs"
        / summary["run_id"]
        / "assignments"
        / f"{row['assignment_id']}.json"
    )
    assignment = json.loads(assignment_path.read_text(encoding="utf-8"))

    if mutation == "result_schema":
        result["schema_version"] = 999
    elif mutation == "stale_assignment_context":
        assignment["context_version"] = "f" * 64
        unsigned = dict(assignment)
        unsigned.pop("assignment_sha256")
        assignment["assignment_sha256"] = hashlib.sha256(
            json.dumps(
                unsigned, sort_keys=True, ensure_ascii=False
            ).encode("utf-8")
        ).hexdigest()
        assignment_path.write_text(
            json.dumps(assignment, sort_keys=True) + "\n", encoding="utf-8"
        )
        result["context_version"] = assignment["context_version"]
        result["assignment_sha256"] = assignment["assignment_sha256"]
    elif mutation == "wrong_internal_result_path":
        result["result_path"] = ".agent-harness/runs/wrong/results/wrong.json"
    elif mutation == "missing_result_field":
        result.pop("agent_type")
    elif mutation == "failing_review_coverage":
        coverage_path = tmp_path / result["review_coverage_path"]
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        coverage["coverage_cells"][0]["status"] = "FAIL"
        coverage.pop("coverage_sha256")
        coverage["coverage_sha256"] = hashlib.sha256(
            json.dumps(
                coverage,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        coverage_path.write_text(
            json.dumps(coverage, sort_keys=True) + "\n", encoding="utf-8"
        )
        coverage_sha = hashlib.sha256(coverage_path.read_bytes()).hexdigest()
        result["review_coverage_sha256"] = coverage_sha
        result["artifacts"][0]["sha256"] = coverage_sha
        result["artifacts"][0]["bytes"] = coverage_path.stat().st_size
    elif mutation == "invented_review_coverage":
        coverage_path = tmp_path / result["review_coverage_path"]
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        coverage["coverage_cells"] = [
            {
                "cell": "attacker_invented_cell",
                "status": "PASS",
                "evidence_refs": ["self-authored evidence"],
                "rationale": "This cell is absent from the registered policy.",
            }
        ]
        coverage["independent_oracles"] = [{"status": "PASS"}]
        coverage.pop("coverage_sha256")
        coverage["coverage_sha256"] = hashlib.sha256(
            json.dumps(
                coverage,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        coverage_path.write_text(
            json.dumps(coverage, sort_keys=True) + "\n", encoding="utf-8"
        )
        coverage_sha = hashlib.sha256(coverage_path.read_bytes()).hexdigest()
        result["review_coverage_sha256"] = coverage_sha
        result["artifacts"][0]["sha256"] = coverage_sha
        result["artifacts"][0]["bytes"] = coverage_path.stat().st_size
    elif mutation == "malformed_extra_artifact":
        result["artifacts"].append(
            {
                "path": "../../outside",
                "sha256": "not-a-sha256",
                "bytes": -1,
                "producer": "attacker",
            }
        )
    elif mutation == "blind_sibling_artifact":
        sibling_path = (
            tmp_path
            / ".agent-harness/runs"
            / summary["run_id"]
            / "results"
            / "unallowed_sibling.json"
        )
        sibling_path.write_text("{}\n", encoding="utf-8")
        result["artifacts"].append(
            {
                "path": str(sibling_path.relative_to(tmp_path)),
                "sha256": hashlib.sha256(sibling_path.read_bytes()).hexdigest(),
                "bytes": sibling_path.stat().st_size,
                "producer": row["assignment_id"],
            }
        )
    else:
        summary["results"].append(dict(row))

    if mutation != "duplicate_result_path":
        result_path.write_text(
            json.dumps(result, sort_keys=True) + "\n", encoding="utf-8"
        )
        row["sha256"] = hashlib.sha256(result_path.read_bytes()).hexdigest()
    summary_path.write_text(
        json.dumps(summary, sort_keys=True) + "\n", encoding="utf-8"
    )
    receipt = build_dependency_activation_receipt(
        spec_path=spec,
        status_path=status,
        repository_root=tmp_path,
    )
    assert receipt.status is DependencyActivationStatus.BLOCKED
    assert any("review" in reason for reason in receipt.reasons)


@pytest.mark.parametrize(
    "mutation",
    (
        "policy_substitution",
        "blind_sibling_registration",
        "independence_mode_substitution",
        "stale_context",
    ),
)
def test_activation_rejects_self_consistent_registration_substitution(
    tmp_path: Path, mutation: str
) -> None:
    spec, status = _write_activated_contract(tmp_path)
    status_payload = yaml.safe_load(status.read_text(encoding="utf-8"))
    summary_path = tmp_path / status_payload["execution_resolutions"]["PR-282"][
        "review_receipt"
    ]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    row = summary["results"][0]
    run_dir = summary_path.parent
    result_path = tmp_path / row["path"]
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assignment_path = run_dir / "assignments" / f"{row['assignment_id']}.json"
    assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
    plan_path = run_dir / "RUN_PLAN.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))

    if mutation == "policy_substitution":
        policy_path = tmp_path / plan["integration_policy"]["path"]
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["required_review_cells"] = ["attacker_invented_cell"]
        policy_path.write_text(
            json.dumps(policy, sort_keys=True) + "\n", encoding="utf-8"
        )
        plan["integration_policy"]["sha256"] = hashlib.sha256(
            policy_path.read_bytes()
        ).hexdigest()
        plan_path.write_text(
            json.dumps(plan, sort_keys=True) + "\n", encoding="utf-8"
        )
        coverage_path = tmp_path / result["review_coverage_path"]
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        coverage["coverage_cells"] = [
            {
                "cell": "attacker_invented_cell",
                "status": "PASS",
                "evidence_refs": ["self-authored evidence"],
                "rationale": "Invented after candidate freeze.",
            }
        ]
        coverage.pop("coverage_sha256")
        coverage["coverage_sha256"] = hashlib.sha256(
            json.dumps(
                coverage,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        coverage_path.write_text(
            json.dumps(coverage, sort_keys=True) + "\n", encoding="utf-8"
        )
        coverage_sha = hashlib.sha256(coverage_path.read_bytes()).hexdigest()
        result["review_coverage_sha256"] = coverage_sha
        result["artifacts"][0]["sha256"] = coverage_sha
        result["artifacts"][0]["bytes"] = coverage_path.stat().st_size
    elif mutation in {
        "blind_sibling_registration",
        "independence_mode_substitution",
    }:
        sibling = run_dir / "results" / "attacker_sibling.json"
        sibling.write_text("{}\n", encoding="utf-8")
        sibling_relative = sibling.relative_to(tmp_path).as_posix()
        assignment["allowed_sibling_results"] = [sibling_relative]
        if mutation == "independence_mode_substitution":
            assignment["independence_mode"] = "adjudication"
            result["independence_mode"] = "adjudication"
        unsigned = dict(assignment)
        unsigned.pop("assignment_sha256")
        assignment["assignment_sha256"] = hashlib.sha256(
            json.dumps(
                unsigned, sort_keys=True, ensure_ascii=False
            ).encode("utf-8")
        ).hexdigest()
        assignment_path.write_text(
            json.dumps(assignment, sort_keys=True) + "\n", encoding="utf-8"
        )
        result["assignment_sha256"] = assignment["assignment_sha256"]
    else:
        stale = "f" * 64
        summary["context_version"] = stale
        assignment["context_version"] = stale
        unsigned = dict(assignment)
        unsigned.pop("assignment_sha256")
        assignment["assignment_sha256"] = hashlib.sha256(
            json.dumps(
                unsigned, sort_keys=True, ensure_ascii=False
            ).encode("utf-8")
        ).hexdigest()
        assignment_path.write_text(
            json.dumps(assignment, sort_keys=True) + "\n", encoding="utf-8"
        )
        result["context_version"] = stale
        result["assignment_sha256"] = assignment["assignment_sha256"]

    result_path.write_text(
        json.dumps(result, sort_keys=True) + "\n", encoding="utf-8"
    )
    row["sha256"] = hashlib.sha256(result_path.read_bytes()).hexdigest()
    summary_path.write_text(
        json.dumps(summary, sort_keys=True) + "\n", encoding="utf-8"
    )
    receipt = build_dependency_activation_receipt(
        spec_path=spec,
        status_path=status,
        repository_root=tmp_path,
    )
    assert receipt.status is DependencyActivationStatus.BLOCKED
    assert any("review" in reason for reason in receipt.reasons)


def test_activation_rejects_parent_escape_and_symlink_aliases(tmp_path: Path) -> None:
    spec, status = _write_activated_contract(tmp_path)
    payload = yaml.safe_load(status.read_text(encoding="utf-8"))
    payload["execution_resolutions"]["PR-281"]["receipt"] = "../outside.json"
    status.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    blocked = build_dependency_activation_receipt(
        spec_path=spec,
        status_path=status,
        repository_root=tmp_path,
    )
    assert blocked.status is DependencyActivationStatus.BLOCKED
    assert any("escapes repository root" in reason for reason in blocked.reasons)

    alias = tmp_path.parent / f"{tmp_path.name}-alias"
    alias.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(BlindReplayContractError, match="root must not be a symlink"):
        build_dependency_activation_receipt(
            spec_path=alias / spec.name,
            status_path=alias / status.name,
            repository_root=alias,
        )


def test_activation_binds_review_results_and_schema_defined_terminal(
    tmp_path: Path,
) -> None:
    spec, status = _write_activated_contract(tmp_path)
    status_payload = yaml.safe_load(status.read_text(encoding="utf-8"))
    review = tmp_path / status_payload["execution_resolutions"]["PR-282"][
        "review_receipt"
    ]
    review.unlink()
    blocked = build_dependency_activation_receipt(
        spec_path=spec, status_path=status, repository_root=tmp_path
    )
    assert blocked.status is DependencyActivationStatus.BLOCKED
    assert any("PR-282" in reason and "review receipt" in reason for reason in blocked.reasons)

    second_root = tmp_path / "second"
    second_root.mkdir()
    spec, status = _write_activated_contract(second_root)
    terminal = second_root / "docs/generated/pr282_exact_parity_readiness_receipt.json"
    payload = json.loads(terminal.read_text(encoding="utf-8"))
    payload["readiness_receipt"]["terminal"]["g3_outcome"] = "FAIL_HOSTILE"
    payload["nonterminal_decoy"] = "PASS_EXECUTABLE_P_EQUIVARIANCE"
    terminal.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    blocked = build_dependency_activation_receipt(
        spec_path=spec, status_path=status, repository_root=second_root
    )
    assert blocked.status is DependencyActivationStatus.BLOCKED
    assert any("schema-defined terminal" in reason for reason in blocked.reasons)


def test_activation_rejects_alternate_in_root_spec_or_status(tmp_path: Path) -> None:
    spec, status = _write_activated_contract(tmp_path)
    alternate = tmp_path / "alternate-spec.yaml"
    alternate.write_bytes(spec.read_bytes())
    with pytest.raises(BlindReplayContractError, match="canonical PR-287 path"):
        build_dependency_activation_receipt(
            spec_path=alternate,
            status_path=status,
            repository_root=tmp_path,
        )


def test_fresh_challenge_is_content_addressed_and_recursively_truth_free(
    tmp_path: Path,
) -> None:
    activation = _activated_receipt(tmp_path)
    challenge = build_fresh_challenge(
        activation_receipt=activation,
        challenge_config_content_id=_id("config"),
        threshold_contract_content_id=_id("thresholds"),
        scenario_bank=_scenario_bank(),
        seed_commitment_content_id=_id("seed-commitment"),
        cases=_case_payloads(),
    )
    assert validate_fresh_challenge(challenge) is challenge
    assert challenge.challenge_content_id.startswith("sha256:")
    with pytest.raises(BlindReplayContractError, match="schema|forbidden"):
        build_fresh_challenge(
            activation_receipt=activation,
            challenge_config_content_id=_id("config"),
            threshold_contract_content_id=_id("thresholds"),
            scenario_bank=_scenario_bank(),
            seed_commitment_content_id=_id("seed-commitment"),
            cases=tuple(
                {**row, "nested": {"expected_label": "forbidden"}}
                if row["case_id"] == "H04"
                else row
                for row in _case_payloads()
            ),
        )
    with pytest.raises(BlindReplayContractError, match="schema|forbidden"):
        build_fresh_challenge(
            activation_receipt=activation,
            challenge_config_content_id=_id("config"),
            threshold_contract_content_id=_id("thresholds"),
            scenario_bank=_scenario_bank(),
            seed_commitment_content_id=_id("seed-commitment"),
            cases=tuple(
                {**row, "secret": {"seed": 7}}
                if row["case_id"] == "H01"
                else row
                for row in _case_payloads()
            ),
        )


def test_analyst_receives_only_public_case_payloads(tmp_path: Path) -> None:
    activation = _activated_receipt(tmp_path)
    challenge = build_fresh_challenge(
        activation_receipt=activation,
        challenge_config_content_id=_id("config"),
        threshold_contract_content_id=_id("thresholds"),
        scenario_bank=_scenario_bank(),
        seed_commitment_content_id=_id("seed-commitment"),
        cases=_case_payloads(),
    )
    called = False

    def analyzer(case):
        nonlocal called
        called = True
        return case

    with pytest.raises(BlindReplayContractError, match="in-process analyzer"):
        analyze_fresh_challenge(challenge, analyzer=analyzer)
    assert called is False


def test_submission_rejects_truth_and_challenge_identity_drift(tmp_path: Path) -> None:
    activation = _activated_receipt(tmp_path)
    challenge = build_fresh_challenge(
        activation_receipt=activation,
        challenge_config_content_id=_id("config"),
        threshold_contract_content_id=_id("thresholds"),
        scenario_bank=_scenario_bank(),
        seed_commitment_content_id=_id("seed-commitment"),
        cases=_case_payloads(),
    )
    results = _case_results()
    submission = build_frozen_submission(challenge=challenge, case_results=results)
    hostile = [dict(row) for row in _analysis_inputs()]
    hostile[-1]["oracle_truth"] = "forbidden"
    with pytest.raises(BlindReplayContractError, match="input schema"):
        build_registered_case_analysis_results(
            hostile,
            scenario_bank=_scenario_bank(),
        )
    mutant = copy(submission)
    object.__setattr__(
        mutant,
        "challenge_content_id",
        _id("other-challenge"),
    )
    with pytest.raises(BlindReplayContractError, match="content identity"):
        validate_frozen_submission(mutant, challenge=challenge)


def test_scenario_bank_enforces_bijection_and_paired_covariance_contract() -> None:
    bank = _scenario_bank()
    missing = [dict(row) for row in bank.scenarios]
    missing[0].pop("alpha")
    with pytest.raises(BlindReplayContractError, match="field inventory"):
        build_typed_scenario_bank(
            scenarios=missing,
            case_to_scenario={
                row["case_id"]: row["scenario_id"] for row in bank.case_assignments
            },
        )
    duplicate = {
        row["case_id"]: row["scenario_id"] for row in bank.case_assignments
    }
    duplicate["H08"] = duplicate["H07"]
    with pytest.raises(BlindReplayContractError, match="bijection"):
        build_typed_scenario_bank(scenarios=bank.scenarios, case_to_scenario=duplicate)
    covariance_drift = [dict(row) for row in bank.scenarios]
    covariance_drift[4]["latent_draw_inventory_id"] = _id("independent-draws")
    with pytest.raises(BlindReplayContractError, match="paired covariance"):
        build_typed_scenario_bank(
            scenarios=covariance_drift,
            case_to_scenario={
                row["case_id"]: row["scenario_id"] for row in bank.case_assignments
            },
        )
    non_spd = [dict(row) for row in bank.scenarios]
    non_spd[4]["covariance_analysis_matrix"] = [[1.0, 2.0], [2.0, 1.0]]
    with pytest.raises(BlindReplayContractError, match="positive definite"):
        build_typed_scenario_bank(
            scenarios=non_spd,
            case_to_scenario={
                row["case_id"]: row["scenario_id"]
                for row in bank.case_assignments
            },
        )


def test_case_results_derive_precedence_holm_coverage_and_depth_fail_closed() -> None:
    bank = _scenario_bank()
    inputs = [dict(row) for row in _analysis_inputs(bank)]
    inputs[4]["local_response_rank"] = 0
    inputs[4]["joint_response_rank"] = 1
    inputs[4]["minimum_principal_angle"] = None
    inputs[4]["weak_identification"] = True
    inputs[4]["unknown_distance"] = 9.0
    inputs[4]["unknown_distance_threshold"] = 1.0
    inputs[4]["response_equivalence"] = True
    inputs[5]["weak_identification"] = True
    inputs[5]["minimum_principal_angle"] = 0.1
    inputs[5]["unknown_distance"] = 9.0
    inputs[5]["unknown_distance_threshold"] = 1.0
    results = build_registered_case_analysis_results(inputs, scenario_bank=bank)
    assert results[4].classifier_terminal == "TYPE_UNIDENTIFIED"
    assert results[5].classifier_terminal == "TYPE_UNIDENTIFIED"
    assert tuple(row.holm_adjusted_p_value for row in results[4:]) == pytest.approx(
        (0.4, 0.42, 0.42, 0.42, 0.42, 0.42, 0.42, 0.42)
    )
    assert all(row.coverage_status == "TARGET_NOT_CONTAINED" for row in results)

    missing_premise = [dict(row) for row in _analysis_inputs(bank)]
    missing_premise[-1]["depth_premise_status"] = "MISSING"
    missing_premise[-1]["matched_mock_status"] = "REQUIRED"
    with pytest.raises(BlindReplayContractError, match="missing depth premise"):
        build_registered_case_analysis_results(
            missing_premise, scenario_bank=bank
        )


def test_case_results_bind_covariance_rank_angle_and_raw_coverage_cells() -> None:
    bank = _scenario_bank()
    wrong_covariance = [dict(row) for row in _analysis_inputs(bank)]
    wrong_covariance[4]["covariance_status"] = "REGISTERED_VALID"
    with pytest.raises(BlindReplayContractError, match="registered scenario"):
        build_registered_case_analysis_results(
            wrong_covariance, scenario_bank=bank
        )

    impossible_rank = [dict(row) for row in _analysis_inputs(bank)]
    impossible_rank[8]["joint_response_rank"] = 3
    with pytest.raises(BlindReplayContractError, match="direct-sum"):
        build_registered_case_analysis_results(
            impossible_rank, scenario_bank=bank
        )

    below_component_rank = [dict(row) for row in _analysis_inputs(bank)]
    below_component_rank[8]["local_response_rank"] = 2
    below_component_rank[8]["joint_response_rank"] = 1
    with pytest.raises(BlindReplayContractError, match="component rank"):
        build_registered_case_analysis_results(
            below_component_rank, scenario_bank=bank
        )

    intersection_angle = [dict(row) for row in _analysis_inputs(bank)]
    intersection_angle[8]["joint_response_rank"] = 1
    with pytest.raises(BlindReplayContractError, match="zero principal angle"):
        build_registered_case_analysis_results(
            intersection_angle, scenario_bank=bank
        )

    weak_drift = [dict(row) for row in _analysis_inputs(bank)]
    weak_drift[7]["minimum_principal_angle"] = 0.0
    with pytest.raises(BlindReplayContractError, match="principal angle"):
        build_registered_case_analysis_results(weak_drift, scenario_bank=bank)

    exact_rows = [dict(row) for row in bank.scenarios]
    exact_rows[-1]["replicate_or_exact_enumeration_rule"] = (
        "exact_finite_enumeration"
    )
    exact_rows[-1]["exact_enumeration_cell_ids"] = [
        _id(f"exact-cell:{index}") for index in range(10)
    ]
    exact_bank = build_typed_scenario_bank(
        scenarios=exact_rows,
        case_to_scenario={
            row["case_id"]: row["scenario_id"] for row in bank.case_assignments
        },
    )
    inputs = [dict(row) for row in _analysis_inputs(exact_bank)]
    inputs[-1]["coverage_cell_results"] = [1] * 9 + [0]
    results = build_registered_case_analysis_results(
        inputs, scenario_bank=exact_bank
    )
    exact = results[-1]
    assert exact.coverage_successes == 9
    assert exact.coverage_trials == 10
    assert exact.coverage_interval == pytest.approx((0.9, 0.9))
    assert exact.mc_precision_status == "EXACT_FINITE_ENUMERATION"
    assert exact.coverage_status == "TARGET_CONTAINED"
    assert exact.coverage_cell_results_content_id.startswith("sha256:")

    raw_drift = copy(exact)
    object.__setattr__(raw_drift, "coverage_cell_results", (1,) * 10)
    with pytest.raises(BlindReplayContractError, match="identity drifted"):
        validate_registered_case_analysis_results(
            (*results[:-1], raw_drift), scenario_bank=exact_bank
        )


def test_challenge_validation_rechecks_activation_authority(tmp_path: Path) -> None:
    activation = _activated_receipt(tmp_path)
    challenge = build_fresh_challenge(
        activation_receipt=activation,
        challenge_config_content_id=_id("config"),
        threshold_contract_content_id=_id("thresholds"),
        scenario_bank=_scenario_bank(),
        seed_commitment_content_id=_id("seed-commitment"),
        cases=_case_payloads(),
    )
    mutant = copy(challenge)
    object.__setattr__(mutant, "activation_receipt_content_id", _id("fabricated"))
    object.__setattr__(
        mutant,
        "challenge_content_id",
        canonical_json_sha256(mutant.unsigned_payload()),
    )
    with pytest.raises(BlindReplayContractError, match="activation authority"):
        validate_fresh_challenge(mutant)


def _valid_stage_rows(activation, challenge, submission):
    truth_id = _id("truth-vault")
    adjudication_id = _id("adjudication")
    pack_ids = {name: _id(name) for name in ("pack-A", "pack-B", "pack-C")}
    return [
        {
            "stage_id": "SPEC_AND_DEPENDENCY_FREEZE",
            "input_content_ids": {
                "spec_content_id": activation.spec_content_id,
                "status_content_id": activation.status_content_id,
            },
            "output_content_ids": {
                "dependency_activation_receipt_content_id": activation.receipt_content_id
            },
            "status": "COMPLETED",
            "started_at_utc": "2026-08-09T00:00:00Z",
            "completed_at_utc": "2026-08-09T00:00:01Z",
        },
        {
            "stage_id": "CHALLENGE_DESIGN",
            "input_content_ids": {
                "dependency_activation_receipt_content_id": activation.receipt_content_id,
                "challenge_config_content_id": challenge.challenge_config_content_id,
                "threshold_contract_content_id": challenge.threshold_contract_content_id,
            },
            "output_content_ids": {
                "challenge_content_id": challenge.challenge_content_id,
                "truth_vault_content_id": truth_id,
                "seed_commitment_content_id": challenge.seed_commitment_content_id,
                "case_inventory_content_id": challenge.case_inventory_content_id,
            },
            "status": "COMPLETED",
            "started_at_utc": "2026-08-09T00:00:02Z",
            "completed_at_utc": "2026-08-09T00:00:03Z",
        },
        {
            "stage_id": "BLIND_ANALYSIS",
            "input_content_ids": {
                "challenge_content_id": challenge.challenge_content_id,
                "challenge_config_content_id": challenge.challenge_config_content_id,
                "threshold_contract_content_id": challenge.threshold_contract_content_id,
            },
            "output_content_ids": {
                "submission_content_id": submission.submission_content_id
            },
            "status": "COMPLETED",
            "started_at_utc": "2026-08-09T00:00:04Z",
            "completed_at_utc": "2026-08-09T00:00:05Z",
        },
        {
            "stage_id": "REGISTERED_ADJUDICATION",
            "input_content_ids": {
                "truth_vault_content_id": truth_id,
                "submission_content_id": submission.submission_content_id,
                "challenge_content_id": challenge.challenge_content_id,
                "threshold_contract_content_id": challenge.threshold_contract_content_id,
            },
            "output_content_ids": {
                "adjudication_content_id": adjudication_id,
                "pack_A_content_id": pack_ids["pack-A"],
                "pack_B_content_id": pack_ids["pack-B"],
                "pack_C_content_id": pack_ids["pack-C"],
                "terminal_receipt_content_id": _id("terminal"),
            },
            "status": "COMPLETED",
            "started_at_utc": "2026-08-09T00:00:06Z",
            "completed_at_utc": "2026-08-09T00:00:07Z",
        },
        {
            "stage_id": "HISTORICAL_REPLAY",
            "input_content_ids": {
                "submission_content_id": submission.submission_content_id,
                "historical_pr273_pack_content_id": _id("historical-pr273"),
            },
            "output_content_ids": {
                "historical_replay_receipt_content_id": _id("historical-replay")
            },
            "status": "COMPLETED",
            "started_at_utc": "2026-08-09T00:00:08Z",
            "completed_at_utc": "2026-08-09T00:00:09Z",
        },
    ]


def test_stage_trace_is_exact_ordered_and_identity_linked(tmp_path: Path) -> None:
    activation = _activated_receipt(tmp_path)
    challenge = build_fresh_challenge(
        activation_receipt=activation,
        challenge_config_content_id=_id("config"),
        threshold_contract_content_id=_id("thresholds"),
        scenario_bank=_scenario_bank(),
        seed_commitment_content_id=_id("seed-commitment"),
        cases=_case_payloads(),
    )
    submission = build_frozen_submission(
        challenge=challenge,
        case_results=_case_results(),
    )
    rows = _valid_stage_rows(activation, challenge, submission)
    trace = build_stage_trace(rows)
    assert tuple(row.stage_id for row in trace.rows) == tuple(BlindReplayStage)
    assert validate_stage_trace(trace) is trace

    swapped = list(rows)
    swapped[2], swapped[3] = swapped[3], swapped[2]
    with pytest.raises(BlindReplayContractError, match="exact stage order"):
        build_stage_trace(swapped)

    drifted = [dict(row) for row in rows]
    drifted[3] = {
        **drifted[3],
        "input_content_ids": {
            **drifted[3]["input_content_ids"],
            "submission_content_id": _id("mutated-submission"),
        },
    }
    with pytest.raises(BlindReplayContractError, match="identity linkage"):
        build_stage_trace(drifted)
    with pytest.raises(BlindReplayContractError, match="every exact stage"):
        build_stage_trace(None)


def test_truth_reference_and_submission_freeze_are_factory_bound(tmp_path: Path) -> None:
    activation = _activated_receipt(tmp_path)
    challenge = build_fresh_challenge(
        activation_receipt=activation,
        challenge_config_content_id=_id("config"),
        threshold_contract_content_id=_id("thresholds"),
        scenario_bank=_scenario_bank(),
        seed_commitment_content_id=_id("seed-commitment"),
        cases=_case_payloads(),
    )
    submission = build_frozen_submission(
        challenge=challenge,
        case_results=_case_results(),
    )
    truth = build_truth_vault_reference(
        challenge=challenge,
        truth_vault_content_id=_id("truth-vault"),
    )
    freeze = build_submission_freeze_receipt(
        challenge=challenge,
        submission=submission,
        submission_frozen_at_utc="2026-08-09T00:00:05Z",
        source_commit_or_external_candidate_seal_id="a" * 40,
    )
    assert validate_truth_vault_reference(truth, challenge=challenge) is truth
    assert (
        validate_submission_freeze_receipt(
            freeze,
            challenge=challenge,
            submission=submission,
        )
        is freeze
    )
    with pytest.raises(BlindReplayContractError, match="factory-derived"):
        TruthVaultReference(
            challenge_content_id=challenge.challenge_content_id,
            seed_commitment_content_id=challenge.seed_commitment_content_id,
            case_inventory_content_id=challenge.case_inventory_content_id,
            truth_vault_content_id=_id("truth-vault"),
            reference_content_id=_id("reference"),
        )
    with pytest.raises(BlindReplayContractError, match="factory-derived"):
        SubmissionFreezeReceipt(
            challenge_content_id=challenge.challenge_content_id,
            challenge_config_content_id=challenge.challenge_config_content_id,
            threshold_contract_content_id=challenge.threshold_contract_content_id,
            case_inventory_content_id=challenge.case_inventory_content_id,
            submission_content_id=submission.submission_content_id,
            submission_frozen_at_utc="2026-08-09T00:00:05Z",
            source_commit_or_external_candidate_seal_id="a" * 40,
            freeze_receipt_content_id=_id("freeze"),
        )

    mutant = copy(submission)
    object.__setattr__(mutant, "submission_content_id", _id("mutated-submission"))
    with pytest.raises(
        BlindReplayContractError, match="content identity drifted|freeze binding"
    ):
        validate_submission_freeze_receipt(
            freeze,
            challenge=challenge,
            submission=mutant,
        )


def test_historical_replay_receipt_requires_a_frozen_fresh_submission(
    tmp_path: Path,
) -> None:
    activation = _activated_receipt(tmp_path)
    challenge = build_fresh_challenge(
        activation_receipt=activation,
        challenge_config_content_id=_id("config"),
        threshold_contract_content_id=_id("thresholds"),
        scenario_bank=_scenario_bank(),
        seed_commitment_content_id=_id("seed-commitment"),
        cases=_case_payloads(),
    )
    submission = build_frozen_submission(
        challenge=challenge,
        case_results=_case_results(),
    )
    freeze = build_submission_freeze_receipt(
        challenge=challenge,
        submission=submission,
        submission_frozen_at_utc="2026-08-09T00:00:05Z",
        source_commit_or_external_candidate_seal_id="c" * 40,
    )
    historical = tmp_path / "historical" / "PR273_DIAGNOSTIC_PACK.json"
    historical.parent.mkdir()
    historical.write_text(
        json.dumps(
            {
                "schema": "htt.pr273.blind_synthetic_diagnostic_pack.v1",
                "content_id": _id("historical-pack"),
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    receipt = build_historical_replay_receipt(
        freeze_receipt=freeze,
        challenge=challenge,
        submission=submission,
        historical_source_path=str(historical.relative_to(tmp_path)),
        repository_root=tmp_path,
        replay_command=(
            "python3 -B scripts/codex_harness/build_pr273_blind_synthetic.py --check"
        ),
        replay_exit_code=0,
    )
    assert receipt.terminal == "PASS_EXACT_HISTORICAL_PR273_REPLAY"
    assert validate_historical_replay_receipt(
        receipt,
        freeze_receipt=freeze,
        challenge=challenge,
        submission=submission,
        repository_root=tmp_path,
    ) is receipt
    with pytest.raises(BlindReplayContractError, match="factory-derived"):
        HistoricalReplayReceipt(
            freeze_receipt_content_id=freeze.freeze_receipt_content_id,
            submission_content_id=submission.submission_content_id,
            historical_source_path=str(historical.relative_to(tmp_path)),
            historical_source_sha256=_id("file"),
            historical_pack_content_id=_id("historical-pack"),
            replay_command=(
                "python3 -B scripts/codex_harness/build_pr273_blind_synthetic.py --check"
            ),
            replay_exit_code=0,
            legacy_reproduction_only=True,
            terminal="PASS_EXACT_HISTORICAL_PR273_REPLAY",
            receipt_content_id=_id("historical-receipt"),
        )


def test_spec_freezes_identity_stage_pack_and_claim_boundaries() -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    assert spec["activation_contract"]["current_state"] == (
        "ACTIVE_PREDECESSOR_PR_OPEN"
    )
    assert spec["fresh_artifact_contracts"]["content_id_algorithm"] == (
        "sha256_of_canonical_json_excluding_own_content_id"
    )
    assert spec["analysis_protocol"]["stage_trace_contract"]["exact_stage_order"] == [
        "SPEC_AND_DEPENDENCY_FREEZE",
        "CHALLENGE_DESIGN",
        "BLIND_ANALYSIS",
        "REGISTERED_ADJUDICATION",
        "HISTORICAL_REPLAY",
    ]
    packs = spec["result_pack_contract"]
    assert packs["pack_C"]["required_surfaces"][:5] == [
        "x_phi",
        "Q_phi",
        "Pi_phi_of_q",
        "F_phi_certified",
        "G_F",
    ]
    assert spec["claim_tier"] == "diagnostic_only"
    assert spec["observed_data_executed"] is spec["public_use"] is False
    assert spec["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"


def test_runner_verifies_activated_typed_blocker_without_fresh_writes() -> None:
    runner = ROOT / "scripts/codex_harness/run_pr287_post275_blind_replay.py"
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    outputs = tuple(
        ROOT / relative
        for relative in spec["fresh_artifact_contracts"]["artifact_paths"].values()
    )
    before = tuple(path.exists() for path in outputs)
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT / "htt/src"), str(ROOT / "htt")))
    for mode, expected in (("check", 0), ("historical", 0), ("build", 2)):
        completed = subprocess.run(
            [sys.executable, "-B", str(runner), mode],
            cwd=ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == expected, completed.stderr
        if mode != "build":
            assert "ACTIVATED_PREDECESSOR_FINAL_SUCCESS" in completed.stdout
            assert (
                "BLOCKED_CAPABILITY_ISOLATED_EXECUTOR_NOT_INSTALLED"
                in completed.stdout
            )
        else:
            assert (
                "BLOCKED_CAPABILITY_ISOLATED_EXECUTOR_NOT_INSTALLED"
                in completed.stderr
            )
    assert tuple(path.exists() for path in outputs) == before
    assert not any(before)


def test_pillar_row_projection_preserves_exact_inventory_and_negative_rows() -> None:
    pillar_t = build_pillar_row_projection(
        pillar="T",
        source_path=(
            "docs/research_program/post_pr275/pillar_t_adjudication/"
            "PILLAR_T_COMPLETE_ADJUDICATION_V1.json"
        ),
        repository_root=ROOT,
    )
    pillar_s = build_pillar_row_projection(
        pillar="S",
        source_path=(
            "docs/research_program/post_pr275/pillar_s_adjudication/"
            "PILLAR_S_COMPLETE_ADJUDICATION_V1.json"
        ),
        repository_root=ROOT,
    )
    assert len(pillar_t.rows) == 80
    assert len(pillar_s.rows) == 72
    assert pillar_t.terminal_counts == {
        "BLOCKED_WITH_RECEIPT": 1,
        "FAIL": 1,
        "INCONCLUSIVE_WITH_RECEIPT": 67,
        "PASS": 11,
    }
    assert pillar_s.terminal_counts == {
        "BLOCKED_WITH_RECEIPT": 1,
        "FAIL": 0,
        "INCONCLUSIVE_WITH_RECEIPT": 50,
        "PASS": 21,
    }
    assert next(
        row for row in pillar_t.rows if row["row_id"] == "C-PR190-FULL-COMPARATOR-ATTAINABILITY"
    )["verdict"] == "FAIL"
    assert next(row for row in pillar_s.rows if row["row_id"] == "VT-S14")[
        "verdict"
    ] == "BLOCKED_WITH_RECEIPT"
    assert validate_pillar_row_projection(
        pillar_t, repository_root=ROOT
    ) is pillar_t

    mutant = copy(pillar_t)
    mutated_rows = [dict(row) for row in pillar_t.rows]
    mutated_rows[-1]["verdict"] = "PASS"
    object.__setattr__(mutant, "rows", tuple(mutated_rows))
    with pytest.raises(BlindReplayContractError, match="projection identity drifted"):
        validate_pillar_row_projection(mutant, repository_root=ROOT)


def _surface(name: str, owner: str) -> dict[str, object]:
    payload = {
        "subject_owner": owner,
        "schema_id": f"PR287-{name}-V1",
        "status": "AVAILABLE_SYNTHETIC_DIAGNOSTIC",
        "allowed_use": ["registered synthetic diagnostic integration"],
        "forbidden_use": ["observed or family inference"],
    }
    extras = {
        "x_phi": {
            "units_normalization_and_frame": "registered dimensionless frame",
            "sign_orientation_convention": "positive registered orientation",
            "value": 0.25,
        },
        "Q_phi": {
            "policy_id": "PR287-Q-POLICY-V1",
            "denominator_identity": _id("q-denominator"),
            "zero_denominator_status": "NONZERO",
            "value": 0.5,
        },
        "Pi_phi_of_q": {
            "q_threshold": 0.4,
            "comparison_rule": "greater_than_or_equal",
            "denominator_identity": _id("pi-denominator"),
            "value": 0.5,
        },
        "F_phi_certified": {
            "ceiling_identity": _id("f-ceiling"),
            "sign_clean_status": "PASS",
            "admissibility_status": "ADMISSIBLE",
            "value": 0.2,
        },
        "G_F": {
            "ordered_depth_bin_identity": _id("depth-bins"),
            "path_identity": _id("depth-path"),
            "covariance_id": _id("g-covariance"),
            "null_status": "REGISTERED_SYNTHETIC_NULL",
            "value": 0.1,
        },
        "rank": {
            "local_response_rank": 1,
            "global_response_rank": 1,
            "joint_response_rank": 2,
            "identification_status": "RANK_SEPARABLE_CANDIDATE",
        },
        "principal_angles": {
            "minimum_principal_angle": 0.5,
            "weak_threshold": 0.2,
            "weak_identification_status": "SEPARABLE_CANDIDATE",
        },
        "covariance_status": {
            "generator_covariance_id": _id("cov-generator"),
            "analysis_covariance_id": _id("cov-generator"),
            "covariance_status": "REGISTERED_VALID",
        },
        "weak_identification": {
            "classifier_terminal": "UNIQUE_RESPONSE_CLASS_CANDIDATE",
            "precedence_rule_id": _id("classifier-precedence"),
            "response_equivalence": False,
            "margin_abstention": False,
        },
        "abstention": {
            "unknown_distance": 0.1,
            "unknown_threshold": 1.0,
            "abstention_status": "WITHIN_REGISTERED_SUPPORT",
        },
        "depth_calibration": {
            "premise_status": "PROVED",
            "finite_bound": 0.5,
            "matched_mock_status": "NOT_REQUIRED",
        },
        "coverage": {
            "hypothesis_family_id": "PR287-HELDOUT-FAMILY-V1",
            "simultaneous_method": "Holm-Bonferroni_FWER",
            "coverage_status": "TARGET_NOT_CONTAINED",
            "mc_precision_status": "SUFFICIENT",
        },
        "direction_coherence": {
            "direction_frame": "registered synthetic frame",
            "covariance_id": _id("direction-covariance"),
            "null_status": "REGISTERED_SYNTHETIC_NULL",
        },
        "depth_coherence": {
            "ordered_depth_bin_identity": _id("coherence-depth-bins"),
            "path_identity": _id("coherence-path"),
            "covariance_id": _id("coherence-covariance"),
            "null_status": "REGISTERED_SYNTHETIC_NULL",
        },
    }
    payload.update(extras.get(name, {}))
    payload["content_id"] = diagnostic_surface_content_id(name, payload)
    return payload


def _pack_metadata(
    owner: str, surfaces: dict[str, dict[str, object]]
) -> dict[str, object]:
    identities = {
        key: _id(key)
        for key in (
            "challenge_content_id",
            "submission_content_id",
            "freeze_receipt_content_id",
            "adjudication_content_id",
            "pillar_t_projection_content_id",
            "pillar_s_projection_content_id",
        )
    }
    return {
        "owner": owner,
        "scope": "synthetic current-spine diagnostic integration",
        "claim_tier": "diagnostic_only",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "scientific_artifact_mode": "synthetic_diagnostic",
        "transfer_source": "none",
        "config_and_input_identities": identities,
        "synthetic_sky_mask_status": "synthetic_registered",
        "covariance_and_null_status": "scenario_specific_registered",
        "observed_data_executed": False,
        "public_use": False,
        "scientific_status_effect": "OPEN_UNCHANGED",
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
        "evidence_lane_identity": _id(f"lane:{owner}"),
        "pr151_partial_data_excluded": True,
        "likelihood_semantics": "NOT_APPLICABLE_DIAGNOSTIC_ONLY",
        "prior_applicability_and_identity": "NOT_APPLICABLE_DIAGNOSTIC_ONLY",
        "units_normalization_and_frame": "surface_specific_registered",
        "sign_orientation_convention": "surface_specific_registered",
        "surface_semantic_content_ids": {
            name: surface["content_id"] for name, surface in surfaces.items()
        },
        "seed_commitment_and_disclosure_status": {
            "seed_commitment_content_id": _id("seed-commitment"),
            "disclosure_status": "DISCLOSED_AFTER_SUBMISSION_FREEZE",
        },
        "assumptions": ["registered synthetic challenge only"],
        "caveats": ["no observed, source, geometry, or family promotion"],
        "generating_procedure": "owner-specific PR-287 factory",
        "git_commit_or_worktree_state": "b" * 40,
    }


def test_owner_specific_packs_enforce_claim_firewall_and_surface_identity() -> None:
    a_names = (
        "x_phi",
        "Q_phi",
        "Pi_phi_of_q",
        "F_phi_certified",
        "G_F",
        "SectorStress",
        "support_utilization",
        "partial_identification",
    )
    b_names = (
        "rank",
        "principal_angles",
        "covariance_status",
        "weak_identification",
        "abstention",
        "depth_calibration",
        "coverage",
    )
    c_names = (
        "x_phi",
        "Q_phi",
        "Pi_phi_of_q",
        "F_phi_certified",
        "G_F",
        "direction_coherence",
        "depth_coherence",
    )
    a_owners = {
        **{name: "MIO" for name in a_names[:5]},
        "SectorStress": "OBSSTAT",
        "support_utilization": "OBSSTAT",
        "partial_identification": "COMMON",
    }
    a_surfaces = {name: _surface(name, a_owners[name]) for name in a_names}
    b_surfaces = {name: _surface(name, "HTT") for name in b_names}
    c_surfaces = {name: _surface(name, "MIO") for name in c_names}
    pack_a = build_common_pack_a(
        metadata=_pack_metadata("COMMON", a_surfaces),
        surfaces=a_surfaces,
    )
    pack_b = build_htt_pack_b(
        metadata=_pack_metadata("HTT", b_surfaces),
        surfaces=b_surfaces,
    )
    pack_c = build_mio_pack_c(
        metadata=_pack_metadata("MIO", c_surfaces),
        surfaces=c_surfaces,
    )
    assert pack_a.kind is BlindReplayPackKind.PACK_A
    assert pack_b.kind is BlindReplayPackKind.PACK_B
    assert pack_c.kind is BlindReplayPackKind.PACK_C
    assert all(validate_diagnostic_pack(pack) is pack for pack in (pack_a, pack_b, pack_c))
    for pack in (pack_a, pack_b, pack_c):
        provenance = pack.factory_provenance
        assert provenance["module"] == pack.factory_module
        assert provenance["factory_name"]
        assert provenance["source_path"].endswith("post275_blind_replay.py")
        assert len(provenance["source_sha256"]) == 64

    bad_surface = {name: _surface(name, "HTT") for name in b_names}
    bad_surface["coverage"]["nested"] = {"posterior": [0.2, 0.8]}
    with pytest.raises(BlindReplayContractError, match="forbidden .*field"):
        build_htt_pack_b(
            metadata=_pack_metadata("HTT", bad_surface),
            surfaces=bad_surface,
        )

    bad_metadata = _pack_metadata("MIO", c_surfaces)
    bad_metadata["transfer_source"] = "external_transfer"
    with pytest.raises(BlindReplayContractError, match="claim boundary"):
        build_mio_pack_c(
            metadata=bad_metadata,
            surfaces=c_surfaces,
        )

    for alias in (
        "posterior_odds",
        "log_evidence",
        "family_candidate",
        "detected_geometry",
    ):
        hostile = {name: dict(surface) for name, surface in c_surfaces.items()}
        hostile["depth_coherence"][alias] = "forbidden"
        hostile["depth_coherence"]["content_id"] = diagnostic_surface_content_id(
            "depth_coherence", hostile["depth_coherence"]
        )
        with pytest.raises(BlindReplayContractError, match="forbidden diagnostic"):
            build_mio_pack_c(
                metadata=_pack_metadata("MIO", hostile),
                surfaces=hostile,
            )

    rank_drift = {name: dict(surface) for name, surface in b_surfaces.items()}
    rank_drift["rank"]["joint_response_rank"] = 0
    rank_drift["rank"]["content_id"] = diagnostic_surface_content_id(
        "rank", rank_drift["rank"]
    )
    with pytest.raises(
        BlindReplayContractError, match="rank identification|component rank"
    ):
        build_htt_pack_b(
            metadata=_pack_metadata("HTT", rank_drift),
            surfaces=rank_drift,
        )

    weak_contradiction = {
        name: dict(surface) for name, surface in b_surfaces.items()
    }
    weak_contradiction["principal_angles"]["minimum_principal_angle"] = 0.1
    weak_contradiction["principal_angles"]["weak_identification_status"] = (
        "WEAKLY_IDENTIFIED"
    )
    weak_contradiction["principal_angles"]["content_id"] = (
        diagnostic_surface_content_id(
            "principal_angles", weak_contradiction["principal_angles"]
        )
    )
    with pytest.raises(BlindReplayContractError, match="precedence contradiction"):
        build_htt_pack_b(
            metadata=_pack_metadata("HTT", weak_contradiction),
            surfaces=weak_contradiction,
        )

    covariance_contradiction = {
        name: dict(surface) for name, surface in b_surfaces.items()
    }
    covariance_contradiction["covariance_status"]["analysis_covariance_id"] = _id(
        "different-analysis-covariance"
    )
    covariance_contradiction["covariance_status"]["content_id"] = (
        diagnostic_surface_content_id(
            "covariance_status", covariance_contradiction["covariance_status"]
        )
    )
    with pytest.raises(BlindReplayContractError, match="contradicts"):
        build_htt_pack_b(
            metadata=_pack_metadata("HTT", covariance_contradiction),
            surfaces=covariance_contradiction,
        )

    negative_f = {name: dict(surface) for name, surface in c_surfaces.items()}
    negative_f["F_phi_certified"]["value"] = -0.25
    negative_f["F_phi_certified"]["content_id"] = diagnostic_surface_content_id(
        "F_phi_certified", negative_f["F_phi_certified"]
    )
    with pytest.raises(BlindReplayContractError, match="finite probability"):
        build_mio_pack_c(
            metadata=_pack_metadata("MIO", negative_f),
            surfaces=negative_f,
        )

    null_f_drift = {name: dict(surface) for name, surface in c_surfaces.items()}
    null_f_drift["F_phi_certified"].update(
        {
            "sign_clean_status": "UNKNOWN",
            "admissibility_status": "UNREGISTERED",
            "value": None,
        }
    )
    null_f_drift["F_phi_certified"]["content_id"] = diagnostic_surface_content_id(
        "F_phi_certified", null_f_drift["F_phi_certified"]
    )
    with pytest.raises(BlindReplayContractError, match="unregistered"):
        build_mio_pack_c(
            metadata=_pack_metadata("MIO", null_f_drift),
            surfaces=null_f_drift,
        )

    impossible_pack_rank = {
        name: dict(surface) for name, surface in b_surfaces.items()
    }
    impossible_pack_rank["rank"].update(
        {
            "local_response_rank": 2,
            "global_response_rank": 1,
            "joint_response_rank": 1,
            "identification_status": "TYPE_UNIDENTIFIED",
        }
    )
    impossible_pack_rank["rank"]["content_id"] = diagnostic_surface_content_id(
        "rank", impossible_pack_rank["rank"]
    )
    with pytest.raises(BlindReplayContractError, match="component rank"):
        build_htt_pack_b(
            metadata=_pack_metadata("HTT", impossible_pack_rank),
            surfaces=impossible_pack_rank,
        )

    negative_angle = {name: dict(surface) for name, surface in b_surfaces.items()}
    negative_angle["principal_angles"].update(
        {"minimum_principal_angle": -0.1, "weak_threshold": -0.2}
    )
    negative_angle["principal_angles"]["content_id"] = (
        diagnostic_surface_content_id(
            "principal_angles", negative_angle["principal_angles"]
        )
    )
    with pytest.raises(BlindReplayContractError, match="threshold|angle"):
        build_htt_pack_b(
            metadata=_pack_metadata("HTT", negative_angle),
            surfaces=negative_angle,
        )

    equivalence = {name: dict(surface) for name, surface in b_surfaces.items()}
    equivalence["weak_identification"].update(
        {
            "classifier_terminal": "RESPONSE_EQUIVALENCE_ABSTENTION",
            "response_equivalence": True,
        }
    )
    equivalence["weak_identification"]["content_id"] = (
        diagnostic_surface_content_id(
            "weak_identification", equivalence["weak_identification"]
        )
    )
    equivalence_pack = build_htt_pack_b(
        metadata=_pack_metadata("HTT", equivalence),
        surfaces=equivalence,
    )
    assert validate_diagnostic_pack(equivalence_pack) is equivalence_pack

    for claim_text in (
        " ".join(("Bianchi", "family", "identified")),
        " ".join(("Bianchi", "family", "was", "identified")),
        " ".join(("we", "identified", "a", "Bianchi", "family")),
        " ".join(("we", "identified", "the", "Bianchi", "family")),
        " ".join(("we", "detected", "a", "Bianchi", "geometry")),
        " ".join(("the", "Bianchi", "family", "was", "identified")),
        " ".join(("Bianchi", "families", "were", "identified")),
        " ".join(("we", "detected", "Bianchi", "geometries")),
        " ".join(("identified", "the", "family", "as", "Bianchi")),
        " ".join(("native", "solver", "result")),
        " ".join(("native", "solver", "results")),
        " ".join(("MIO", "model", "posterior")),
        " ".join(("posterior", "from", "MIO")),
    ):
        forbidden_claim = {
            name: dict(surface) for name, surface in c_surfaces.items()
        }
        forbidden_claim["depth_coherence"]["status"] = claim_text
        forbidden_claim["depth_coherence"]["content_id"] = (
            diagnostic_surface_content_id(
                "depth_coherence", forbidden_claim["depth_coherence"]
            )
        )
        with pytest.raises(BlindReplayContractError, match="claim language"):
            build_mio_pack_c(
                metadata=_pack_metadata("MIO", forbidden_claim),
                surfaces=forbidden_claim,
            )

    for caveat_text in (
        "native solver result was not evaluated",
        "MIO model posterior remains blocked",
        "no Bianchi family identified by this diagnostic",
    ):
        safe_caveat = {
            name: dict(surface) for name, surface in c_surfaces.items()
        }
        safe_caveat["depth_coherence"]["status"] = caveat_text
        safe_caveat["depth_coherence"]["content_id"] = (
            diagnostic_surface_content_id(
                "depth_coherence", safe_caveat["depth_coherence"]
            )
        )
        safe_pack = build_mio_pack_c(
            metadata=_pack_metadata("MIO", safe_caveat),
            surfaces=safe_caveat,
        )
        assert validate_diagnostic_pack(safe_pack) is safe_pack

    factory_drift = copy(pack_c)
    object.__setattr__(factory_drift, "factory_module", "common.post275_blind_replay")
    with pytest.raises(BlindReplayContractError, match="factory module"):
        validate_diagnostic_pack(factory_drift)

    from common import post275_blind_replay as contracts

    with pytest.raises(BlindReplayContractError, match="call-site substitution"):
        contracts._issue_diagnostic_pack(
            kind=BlindReplayPackKind.PACK_A,
            factory_module="common.post275_blind_replay",
            metadata=_pack_metadata("COMMON", a_surfaces),
            surfaces=a_surfaces,
        )

    spoof_globals = {
        "__name__": "mio.reports.post275_blind_replay",
        "_issue": contracts._issue_diagnostic_pack,
        "BlindReplayPackKind": BlindReplayPackKind,
        "metadata": _pack_metadata("MIO", c_surfaces),
        "surfaces": c_surfaces,
    }
    with pytest.raises(BlindReplayContractError, match="call-site substitution"):
        exec(
            "_issue(kind=BlindReplayPackKind.PACK_C, "
            "factory_module=__name__, metadata=metadata, surfaces=surfaces)",
            spoof_globals,
        )

    cloned_factory = types.FunctionType(
        build_mio_pack_c.__code__,
        {
            "__name__": "mio.reports.post275_blind_replay",
            "BlindReplayPackKind": BlindReplayPackKind,
            "_issue_diagnostic_pack": contracts._issue_diagnostic_pack,
        },
        name="build_mio_pack_c",
    )
    with pytest.raises(BlindReplayContractError, match="call-site substitution"):
        cloned_factory(
            metadata=_pack_metadata("MIO", c_surfaces),
            surfaces=c_surfaces,
        )

    replacement_globals = {
        "__name__": "mio.reports.post275_blind_replay",
        "BlindReplayPackKind": BlindReplayPackKind,
        "_issue_diagnostic_pack": contracts._issue_diagnostic_pack,
    }
    replacement_factory = types.FunctionType(
        build_mio_pack_c.__code__,
        replacement_globals,
        name="build_mio_pack_c",
    )
    replacement_module = types.ModuleType("mio.reports.post275_blind_replay")
    replacement_module.build_mio_pack_c = replacement_factory
    original_module = sys.modules["mio.reports.post275_blind_replay"]
    sys.modules["mio.reports.post275_blind_replay"] = replacement_module
    try:
        with pytest.raises(BlindReplayContractError, match="factory provenance"):
            replacement_factory(
                metadata=_pack_metadata("MIO", c_surfaces),
                surfaces=c_surfaces,
            )
    finally:
        sys.modules["mio.reports.post275_blind_replay"] = original_module


@pytest.mark.parametrize(
    "module_name", ("publication_integrity", "profile_registry")
)
def test_canonical_validator_rejects_transitive_module_substitution(
    monkeypatch: pytest.MonkeyPatch, module_name: str
) -> None:
    from common import post275_blind_replay as contracts

    monkeypatch.setitem(sys.modules, module_name, types.ModuleType(module_name))
    with pytest.raises(BlindReplayContractError, match="module provenance"):
        contracts._canonical_harness_validation_module()
