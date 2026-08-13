#!/usr/bin/env python3
"""Independent claim/provenance oracle for frozen PR-289 R2 review."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[4]
RUN_ID = "pr289-bounded-repair-r2-review-20260811"
ASSIGNMENT_ID = "A-PR289-R2-CLAIM"
SEAL = ROOT / ".prguard/runtime/PR289_R2_CANDIDATE_SEAL.json"
SPEC = ROOT / "docs/research_program/post_pr275/pr289_spec.yaml"
POLICY = ROOT / "docs/research_program/post_pr275/pr289_publication_policy.json"
REGISTRY = ROOT / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
RECEIPT = ROOT / "docs/generated/pr289_data_identity_v2_receipt.json"
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"
DELTA = ROOT / "docs/PR_DELTAS/pr-289.md"
LEDGER = ROOT / "docs/harness/CLAIM_LEDGER.md"


def canonical_sha256(value: object, *, omit: set[str] | None = None) -> str:
    payload = value
    if omit:
        assert isinstance(value, dict)
        payload = {key: item for key, item in value.items() if key not in omit}
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*argv: str) -> str:
    return subprocess.run(
        ["git", *argv],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def card(backlog: dict[str, object], pr_id: str) -> dict[str, object]:
    rows = backlog["prs"]
    assert isinstance(rows, list)
    matches = [row for row in rows if row.get("id") == pr_id]
    assert len(matches) == 1
    return matches[0]


def main() -> int:
    seal = json.loads(SEAL.read_text(encoding="utf-8"))
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    backlog = yaml.safe_load(BACKLOG.read_text(encoding="utf-8"))
    status = yaml.safe_load(STATUS.read_text(encoding="utf-8"))
    delta = DELTA.read_text(encoding="utf-8")
    ledger = LEDGER.read_text(encoding="utf-8")

    assert git("rev-parse", "HEAD") == seal["candidate_sha"]
    assert git("rev-parse", "HEAD^{tree}") == seal["candidate_tree_sha"]
    assert seal["candidate_sha"] == "e7affa4302f60cb02a664b315693b22e2372ef33"
    assert seal["candidate_tree_sha"] == "1d25895f229c87723797c73018fed8783466541f"

    expected_claim = {
        "owner": "COMMON",
        "scope": "external-data identity admission without acquisition or analysis",
        "claim_tier": "diagnostic_only",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "transfer_source": "none",
        "observed_data_executed": False,
        "public_use": False,
        "scientific_status_effect": "OPEN_UNCHANGED",
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
    }
    assert {key: spec[key] for key in expected_claim} == expected_claim
    assert {key: receipt[key] for key in expected_claim} == expected_claim
    assert policy["claim_ceiling"] == "diagnostic_only"
    assert policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert all(row["allowed_transfer_sources"] == ["none"] for row in registry["lanes"])
    assert receipt["aggregate_status"] == "NO_ADMITTED_IDENTITIES"
    assert [row["status"] for row in receipt["lane_decisions"]] == [
        "REJECTED_NOT_PRESENT"
    ] * 6

    for auth in receipt["authorization_receipts"]:
        assert auth["status"] == "NOT_AUTHORIZED"
        assert auth["authorization_domain"] == "lane_data_execution"
        assert auth["exact_admission_record_ids"] == []
        assert auth["lane_admission_bundle_id"] is None
        for field in (
            "human_gate_receipt_id",
            "human_authority_identity",
            "authorized_scope",
            "issued_at_utc",
            "expires_at_utc",
        ):
            assert auth[field] is None
        assert auth["authorization_id"] == canonical_sha256(
            auth, omit={"authorization_id"}
        )

    for relative, digest in receipt["source_bindings"].items():
        assert digest == "sha256:" + sha256(ROOT / relative)
    generation = receipt["generation_identity"]
    assert generation["schema"] == "common.source_bound_generation_identity.v1"
    assert generation["generating_procedure"] == [
        "python3",
        "-B",
        "scripts/codex_harness/run_pr289_data_identity_v2.py",
        "build",
    ]
    assert generation["git_commit_or_worktree_state"] == (
        "BOUND_SOURCE_WORKTREE:" + canonical_sha256(receipt["source_bindings"])
    )
    assert receipt["git_commit_or_worktree_state"] == generation[
        "git_commit_or_worktree_state"
    ]
    assert receipt["generating_procedure"] == generation["generating_procedure"]
    assert receipt["receipt_content_id"] == canonical_sha256(
        receipt, omit={"receipt_content_id"}
    )

    pr289 = card(backlog, "PR-289")
    pr290 = card(backlog, "PR-290")
    assert pr289["owner"] == "COMMON"
    assert pr289["claim_tier_ceiling"] == "diagnostic_only"
    assert pr289["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
    assert pr289["execution_authorization"] == "EXPLICIT_USER_AUTHORIZED"
    assert pr289["authorization_domain"] == "workflow_only"
    assert pr289["public_use"] is False
    assert pr290["execution_authorization"] == "HUMAN_GATE_REQUIRED"
    assert pr290["external_execution_gates"] == [
        {
            "gate_id": "H-PLANCK",
            "mode": "requires_human_execution_authorization",
            "scope": "admitted_planck_observed_execution",
        }
    ]

    execution = status["stacked_pr_execution"]["prs"]
    r1 = execution["PR-289"]
    assert r1["lifecycle"] == "VALIDATED"
    assert r1["gate_dispositions"] == {
        "eligibility": "PASS",
        "implementation": "PASS",
        "validation": "PASS",
        "code": "FAIL",
        "physics": "INCONCLUSIVE",
        "statistics": "INCONCLUSIVE",
        "claim": "INCONCLUSIVE",
        "harness": "FAIL",
        "portability_replay": "PASS",
        "review": "FAIL",
    }
    r2 = execution["PR-290"]
    assert r2["lifecycle"] == "PLANNED"
    assert r2["predecessor_sealed_sha"] is None
    assert r2["gate_dispositions"] == {"eligibility": "INELIGIBLE"}
    assert r2["assurance_budget"] == {"maximum": 16, "consumed": 0}

    normalized_delta = " ".join(delta.split())
    for phrase in (
        "frozen R1 review FAIL preserved",
        "authorization_domain: workflow_only",
        "not any lane-specific data execution",
        "No data was acquired or executed",
        "no R1 acceptance envelope is reused",
        "no force push, approval, or merge",
    ):
        assert phrase in normalized_delta
    for phrase in (
        "| COMMON | IMPLEMENTED_DIAGNOSTIC_CONTRACT |",
        "| COMMON | FORBIDDEN / NOT_GRANTED |",
        "| COMMON | FORBIDDEN / NOT_EVALUATED |",
    ):
        assert phrase in ledger

    sys.path[:0] = [str(ROOT), str(ROOT / "htt/src"), str(ROOT / "htt")]
    from common import data_identity as identity

    mutation_ids = (
        "MU289-ADMISSION-AUTH-COLLAPSE",
        "MU289-WORKFLOW-AUTH-LAUNDERING",
        "MU289-CLAIM-PROMOTION",
    )
    mutation_results = identity._run_registered_mutations(
        mutation_ids,
        registry=identity.load_lane_registry(REGISTRY),
        spec_path=SPEC,
        source_bindings={
            relative: digest.removeprefix("sha256:")
            for relative, digest in receipt["source_bindings"].items()
        },
    )
    identity.validate_mutation_results(mutation_ids, mutation_results)
    assert all(row.executed and row.activated and row.killed for row in mutation_results)

    result = {
        "schema": "htt.pr289.r2.claim_oracle.v1",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "candidate_sha": seal["candidate_sha"],
        "candidate_tree_sha": seal["candidate_tree_sha"],
        "status": "PASS",
        "checks": {
            "claim_projection_exact": True,
            "source_bound_generation_identity_exact": True,
            "receipt_content_address_exact": True,
            "admission_authorization_separated": True,
            "workflow_authority_not_lane_authority": True,
            "r1_fail_chronology_preserved": True,
            "pr290_ineligible_zero_consumed_budget": True,
            "claim_mutations_executed_activated_killed": [
                row.mutation_id for row in mutation_results
            ],
        },
        "evidence": {
            "receipt_sha256": sha256(RECEIPT),
            "receipt_content_id": receipt["receipt_content_id"],
            "source_binding_count": len(receipt["source_bindings"]),
            "authorization_receipt_count": len(receipt["authorization_receipts"]),
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
