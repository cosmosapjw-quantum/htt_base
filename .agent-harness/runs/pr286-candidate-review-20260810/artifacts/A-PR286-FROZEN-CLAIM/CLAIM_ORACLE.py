#!/usr/bin/env python3
"""Independent frozen-candidate claim and lifecycle oracle for PR-286."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[5]
RUN_ID = "pr286-candidate-review-20260810"
ASSIGNMENT_ID = "A-PR286-FROZEN-CLAIM"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
CANDIDATE_SHA = "f2fb069d4ac5bdcd18564839ffa236bd242ca115"
CANDIDATE_TREE = "1d6ca231d3137b95372da18087741531f9cc0b0b"
BASE_SHA = "16bc6db511b8b7228e5c4dcb95c65074fe519f24"
RECEIPT_REL = (
    "docs/research_program/post_pr275/pillar_s_adjudication/"
    "PILLAR_S_COMPLETE_ADJUDICATION_V1.json"
)


def load_json(relative: str) -> dict:
    return json.loads((REPO / relative).read_text(encoding="utf-8"))


def load_yaml(relative: str) -> dict:
    return yaml.safe_load((REPO / relative).read_text(encoding="utf-8"))


def sha256(relative: str) -> str:
    return hashlib.sha256((REPO / relative).read_bytes()).hexdigest()


def canonical_sha256(value: dict, *, omit: set[str] | None = None) -> str:
    payload = {key: item for key, item in value.items() if key not in (omit or set())}
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, text=True, capture_output=True
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    checks: list[dict[str, object]] = []

    def check(check_id: str, condition: bool, evidence: object) -> None:
        checks.append(
            {
                "check_id": check_id,
                "status": "PASS" if condition else "FAIL",
                "evidence": evidence,
            }
        )

    assignment = load_json(
        f".agent-harness/runs/{RUN_ID}/assignments/{ASSIGNMENT_ID}.json"
    )
    index = load_json(".agent-harness/context/CONTEXT_INDEX.json")
    seal = load_json(".prguard/runtime/PR286_CANDIDATE_SEAL.json")
    rehearsal = load_json(
        ".prguard/runtime/PR286_CANDIDATE_INTEGRATION_REHEARSAL.json"
    )
    spec = load_yaml("docs/research_program/post_pr275/pr286_spec.yaml")
    policy = load_json("docs/research_program/post_pr275/pr286_publication_policy.json")
    receipt = load_json(RECEIPT_REL)
    status = load_yaml("docs/codex_handoff/pr_status.yaml")
    backlog = load_yaml("docs/codex_handoff/pr_backlog.yaml")
    delta = (REPO / "docs/PR_DELTAS/pr-286.md").read_text(encoding="utf-8")

    required_hashes = {
        row["path"]: row["sha256"] for row in assignment["required_inputs"]
    }
    actual_hashes = {path: sha256(path) for path in required_hashes}
    check("required_input_hashes", actual_hashes == required_hashes, actual_hashes)
    check(
        "context_version",
        assignment["context_version"] == index["context_version"] == CONTEXT_VERSION,
        index["context_version"],
    )
    current_head = git("rev-parse", "HEAD")
    current_tree = git("rev-parse", "HEAD^{tree}")
    merge_base = git("merge-base", BASE_SHA, CANDIDATE_SHA)
    check(
        "candidate_identity",
        current_head == seal["candidate_sha"] == CANDIDATE_SHA
        and current_tree == seal["candidate_tree_sha"] == CANDIDATE_TREE
        and merge_base == seal["merge_base_sha"] == BASE_SHA,
        {"head": current_head, "tree": current_tree, "merge_base": merge_base},
    )
    check(
        "integration_rehearsal_identity",
        rehearsal["status"] == "PASS"
        and rehearsal["candidate_sha"] == CANDIDATE_SHA
        and rehearsal["candidate_tree_sha"] == CANDIDATE_TREE
        and rehearsal["latest_target_sha"] == BASE_SHA
        and rehearsal["merged_tree_sha"] == CANDIDATE_TREE,
        {
            "status": rehearsal["status"],
            "latest_target_sha": rehearsal["latest_target_sha"],
            "merged_tree_sha": rehearsal["merged_tree_sha"],
        },
    )

    metadata = receipt["metadata"]
    check(
        "claim_ceiling_and_provenance",
        spec["claim_tier"] == policy["claim_ceiling"] == metadata["claim_tier"] == "diagnostic_only"
        and spec["claim_level"] == metadata["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
        and spec["transfer_source"] == metadata["transfer_source"] == "none"
        and spec["observed_data_executed"] is metadata["observed_data_executed"] is False
        and spec["public_use"] is metadata["public_use"] is False
        and spec["family_identification_gate"]
        == policy["family_identification_gate"]
        == metadata["family_identification_gate"]
        == "BLOCKED_PRE_NATIVE_ATLAS",
        metadata,
    )
    check(
        "ownership_firewall",
        receipt["ownership"]
        == {
            "COMMON": "exact contracts and proof identities",
            "HTT": "model-dependent calibration coverage and inference diagnostics",
            "MIO": "diagnostic residual and coherence consumers only",
            "OBSSTAT": "observable estimands features nulls and covariance inputs",
        }
        and set(receipt["mio_forbidden_outputs"])
        == {"likelihood", "posterior", "Bayes_factor", "evidence"},
        {
            "ownership": receipt["ownership"],
            "mio_forbidden_outputs": receipt["mio_forbidden_outputs"],
        },
    )

    rows = receipt["rows"]
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    terminal_vocab = {"PASS", "FAIL", "INCONCLUSIVE_WITH_RECEIPT", "BLOCKED_WITH_RECEIPT"}
    vts14 = next(row for row in rows if row["row_id"] == "VT-S14")
    check(
        "row_terminal_contract",
        len(rows) == 72
        and counts == {"PASS": 21, "INCONCLUSIVE_WITH_RECEIPT": 50, "BLOCKED_WITH_RECEIPT": 1}
        and {row["verdict"] for row in rows} <= terminal_vocab
        and all(row["claim_ceiling"] == "diagnostic_only" for row in rows)
        and vts14["verdict"] == "BLOCKED_WITH_RECEIPT",
        {"row_count": len(rows), "terminal_counts": counts, "vts14": vts14["verdict"]},
    )
    check(
        "complete_is_not_universal_proof",
        receipt["terminal"] == "PASS_COMPLETE_PILLAR_S_ADJUDICATION"
        and receipt["success_semantics"] == "PROCESS_COMPLETION_ONLY"
        and receipt["scientific_status_effect"] == "ROW_LEVEL_EVIDENCE_SPECIFIC_DISPOSITION_ONLY"
        and any("not universal proof" in item for item in metadata["assumptions"])
        and "does not mean that all 72 propositions passed" in delta,
        {
            "terminal": receipt["terminal"],
            "success_semantics": receipt["success_semantics"],
            "scientific_status_effect": receipt["scientific_status_effect"],
        },
    )
    consumer = receipt["future_consumer_contract"]
    check(
        "downstream_nonpromotion",
        consumer["consumer"] == "PR-287"
        and consumer["preserve_row_verdicts"] is True
        and consumer["preserve_inconclusive_and_blocked"] is True
        and consumer["synthetic_validation_effect"] == "NO_OBSERVED_OR_SOURCE_PROOF_PROMOTION",
        consumer,
    )
    mutations = receipt["mutation_results"]
    check(
        "forbidden_input_mutations",
        len(mutations) == 18
        and all(
            item["activated"] is True
            and item["executed"] is True
            and item["killed"] is True
            and item["survivor"] is False
            for item in mutations
        )
        and {item["mutation_id"] for item in mutations}
        >= {"MU286-MIO-POSTERIOR", "MU286-CLAIM-PROMOTION", "MU286-VTS14-DATA-PROMOTION"},
        {"count": len(mutations), "survivors": [item["mutation_id"] for item in mutations if item["survivor"]]},
    )
    source_paths = {row["path"] for row in receipt["source_bindings"]}
    forbidden_source_tokens = ("PR-151", "native low-ell", "morphology atlas", "observed-sky")
    check(
        "forbidden_sources_absent",
        not any(token.lower() in path.lower() for path in source_paths for token in forbidden_source_tokens),
        sorted(source_paths),
    )
    check(
        "receipt_content_address",
        receipt["receipt_content_sha256"]
        == canonical_sha256(receipt, omit={"receipt_content_sha256"}),
        receipt["receipt_content_sha256"],
    )

    stack = status["stacked_pr_execution"]
    pr286 = stack["prs"]["PR-286"]
    pr287 = stack["prs"]["PR-287"]
    check(
        "status_mirrors_and_lifecycle",
        (REPO / "docs/codex_handoff/pr_status.yaml").read_bytes()
        == (REPO / "machine_readable/pr_status.yaml").read_bytes()
        and pr286["lifecycle"] == "VALIDATED"
        and pr286["lifecycle_history"] == ["PLANNED", "ACTIVE", "IMPLEMENTED", "VALIDATED"]
        and pr286["gate_dispositions"]["review"] == "DEFERRED"
        and pr286["gate_dispositions"]["seal"] == "INELIGIBLE"
        and pr287["lifecycle"] == "PLANNED"
        and pr287["gate_dispositions"]["eligibility"] == "INELIGIBLE"
        and pr287["assurance_budget"] == {"maximum": 16, "consumed": 0},
        {"PR-286": pr286["lifecycle"], "PR-287": pr287},
    )
    check(
        "predecessor_exactness_and_human_merge",
        pr286["base_sha"] == BASE_SHA
        and pr286["predecessor_pr"] == "PR-285"
        and pr286["predecessor_sealed_sha"] == BASE_SHA
        and stack["prs"]["PR-285"]["sealed_head"] == BASE_SHA
        and stack["merge_policy"] == "HUMAN_ONLY",
        {
            "base_sha": pr286["base_sha"],
            "predecessor_sealed_sha": pr286["predecessor_sealed_sha"],
            "merge_policy": stack["merge_policy"],
        },
    )
    backlog_pr287 = next(row for row in backlog["prs"] if row["id"] == "PR-287")
    edge = next(
        row for row in backlog_pr287["dependency_contracts"] if row["upstream_id"] == "PR-286"
    )
    check(
        "backlog_consumer_edge",
        edge["required_terminal"] == "PASS_COMPLETE_PILLAR_S_ADJUDICATION"
        and edge["success_semantics"] == "PROCESS_COMPLETION_ONLY"
        and edge["downstream_row_contract"]
        == {
            "preserve_row_verdicts": True,
            "preserve_inconclusive_and_blocked": True,
            "synthetic_validation_effect": "NO_OBSERVED_OR_SOURCE_PROOF_PROMOTION",
        },
        edge,
    )

    completed = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload = {
        "schema_version": 1,
        "oracle_id": "PR286-FROZEN-CLAIM-ORACLE",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "candidate_sha": CANDIDATE_SHA,
        "candidate_tree_sha": CANDIDATE_TREE,
        "started_at": started,
        "completed_at": completed,
        "status": "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL",
        "checks": checks,
    }
    out = (REPO / args.out).resolve()
    out.relative_to(REPO)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "checks": len(checks), "out": args.out}, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
