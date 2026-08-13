#!/usr/bin/env python3
"""Independent invariant oracle for the frozen PR-285 claim/lifecycle review."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml


ROOT = Path.cwd().resolve()
ASSIGNMENT_PATH = Path(
    ".agent-harness/runs/pr285-candidate-review-20260810/assignments/"
    "A-PR285-FROZEN-CLAIM.json"
)
CAS_LOG_PATH = Path(
    ".prguard/runtime/PR285_FINAL_INTEGRATION_REHEARSAL.logs/"
    "pr285-cas-four-axis-terminal-evidence.stdout"
)


def read_json(path: Path) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def read_yaml(path: Path) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def canonical_digest(value: dict, omit: str) -> str:
    payload = {key: val for key, val in value.items() if key != omit}
    data = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def main() -> None:
    checks: list[str] = []
    assignment = read_json(ASSIGNMENT_PATH)
    require(
        assignment["assignment_sha256"]
        == "5f6f0e2ef1d0438e3401f949d8ccf3c994f60b4c7b1886387c344bec23397c38",
        "assignment identity drift",
    )
    require(assignment["independence_mode"] == "blind-results", "wrong mode")

    for required in assignment["required_inputs"]:
        path = Path(required["path"])
        require(digest(path) == required["sha256"], f"input hash drift: {path}")
    checks.append("required_input_hashes")

    seal = read_json(Path(assignment["candidate_binding"]["seal_path"]))
    rehearsal = read_json(Path(".prguard/runtime/PR285_FINAL_INTEGRATION_REHEARSAL.json"))
    spec = read_yaml(Path("docs/research_program/post_pr275/pr285_spec.yaml"))
    policy = read_json(Path("docs/research_program/post_pr275/pr285_publication_policy.json"))
    receipt = read_json(
        Path(
            "docs/research_program/post_pr275/pillar_t_adjudication/"
            "PILLAR_T_COMPLETE_ADJUDICATION_V1.json"
        )
    )
    status = read_yaml(Path("docs/codex_handoff/pr_status.yaml"))
    status_mirror = read_yaml(Path("machine_readable/pr_status.yaml"))

    binding = assignment["candidate_binding"]
    require(digest(Path(binding["seal_path"])) == binding["seal_file_sha256"], "seal bytes")
    for key in (
        "seal_sha256",
        "base_sha",
        "candidate_sha",
        "merge_base_sha",
        "candidate_tree_sha",
        "diff_sha256",
        "changed_files_sha256",
        "production_hash",
    ):
        require(seal[key] == binding[key], f"candidate seal binding drift: {key}")
    require(git("rev-parse", "HEAD") == binding["candidate_sha"], "HEAD drift")
    require(git("rev-parse", "HEAD^{tree}") == binding["candidate_tree_sha"], "tree drift")
    require(git("status", "--short") == "", "worktree is not clean")
    checks.append("candidate_identity")

    require(
        canonical_digest(receipt, "receipt_content_sha256")
        == receipt["receipt_content_sha256"],
        "adjudication content address drift",
    )
    require(
        canonical_digest(rehearsal, "receipt_sha256") == rehearsal["receipt_sha256"],
        "integration rehearsal content address drift",
    )
    for source in receipt["source_bindings"]:
        require(digest(Path(source["path"])) == source["sha256"], f"source drift: {source['path']}")
    checks.append("receipt_content_and_source_bindings")

    meta = receipt["metadata"]
    require(spec["owner"] == meta["owner"] == "COMMON", "owner is not COMMON")
    require(spec["contributors"] == [], "unexpected contributor ownership")
    require(spec["claim_tier"] == meta["claim_tier"] == "diagnostic_only", "claim tier")
    require(spec["claim_level"] == meta["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}, "claim level")
    require(spec["transfer_source"] == meta["transfer_source"] == "none", "transfer source")
    require(spec["observed_data_executed"] is meta["observed_data_executed"] is False, "observed flag")
    require(spec["public_use"] is meta["public_use"] is False, "public flag")
    require(
        spec["family_identification_gate"]
        == meta["family_identification_gate"]
        == policy["family_identification_gate"]
        == "BLOCKED_PRE_NATIVE_ATLAS",
        "family-identification gate",
    )
    require(policy["claim_ceiling"] == "diagnostic_only", "policy claim ceiling")
    checks.append("common_c2_claim_firewall")

    rows = receipt["rows"]
    legacy = [r for r in rows if r["source_group"] == "legacy_signature_inventory"]
    vt = [r for r in rows if r["source_group"] == "vector_tensor_successor"]
    failed = [r for r in rows if r["source_group"] == "failed_candidate"]
    require(len(rows) == 80 and len(legacy) == 65 and len(vt) == 14 and len(failed) == 1, "inventory cardinality")
    require(Counter(r["source_partition"] for r in legacy) == {"T": 31, "S": 34}, "legacy partitions")
    require(Counter(r["verdict"] for r in rows) == {"PASS": 11, "INCONCLUSIVE_WITH_RECEIPT": 67, "BLOCKED_WITH_RECEIPT": 1, "FAIL": 1}, "terminal counts")
    allowed = set(spec["gate"]["terminal_verdicts"])
    require(all(r["verdict"] in allowed for r in rows), "non-terminal row vocabulary")
    require(receipt["summary"]["bare_not_adjudicated_count"] == 0, "bare status count")
    require(all(r["verdict"] == "INCONCLUSIVE_WITH_RECEIPT" for r in legacy), "legacy title-only boundary")
    expected_vt = {}
    for verdict, ids in spec["expected_vector_tensor_dispositions"].items():
        if verdict != "rationale":
            expected_vt.update({row_id: verdict for row_id in ids})
    require({r["row_id"]: r["verdict"] for r in vt} == expected_vt, "VT dispositions")
    require(failed[0]["row_id"] == "C-PR190-FULL-COMPARATOR-ATTAINABILITY", "PR-190 row identity")
    require(failed[0]["verdict"] == "FAIL", "PR-190 counterexample laundering")
    require(receipt["terminal"] == spec["gate"]["pass_token"], "terminal token")
    require(receipt["success_dependency_satisfied"] is True, "dependency coverage")
    require(any(r["verdict"] != "PASS" for r in rows), "terminal coverage incorrectly means universal PASS")
    checks.append("complete_disposition_not_universal_proof")

    registry_ids = [r["mutation_id"] for r in receipt["mutation_registry"]]
    result_ids = [r["mutation_id"] for r in receipt["mutation_results"]]
    require(receipt["mutation_registry"] == spec["mutation_registry"], "mutation registry drift")
    require(registry_ids == result_ids and len(registry_ids) == 12, "mutation mapping/order")
    require(
        all(r["executed"] and r["activated"] and r["killed"] and not r["survivor"] for r in receipt["mutation_results"]),
        "mutation survivor or unexecuted mutation",
    )
    checks.append("mutation_kills")

    historical_cas = receipt["cas_evidence"]
    require(historical_cas["aggregate_status"] == "CAS_4AXIS_PASS", "historical CAS identity")
    require(historical_cas["claim_promotion_effect"] == "CAS_COMPONENT_ONLY_NO_SCIENTIFIC_PROMOTION", "historical CAS promotion drift")
    require(historical_cas["majority_vote_forbidden"] is True, "CAS majority vote enabled")
    sealed_cas = json.loads((ROOT / CAS_LOG_PATH).read_text(encoding="utf-8"))
    rehearsal_cas = next(c for c in rehearsal["commands"] if c["id"] == "pr285-cas-four-axis-terminal-evidence")
    require(digest(CAS_LOG_PATH) == rehearsal_cas["stdout_sha256"], "sealed current CAS log drift")
    require(sealed_cas["current_aggregate_status"] == "CAS_BLOCKED", "current CAS promoted")
    require(sealed_cas["claim_promotion_cas_eligible_from_current_run"] is False, "current CAS eligibility")
    require(sealed_cas["axis_statuses"] == {"lean": "PASS", "sage_singular": "PASS", "sympy": "PASS", "wolfram_xact": "BLOCKED_PLATFORM_OR_LICENSE"}, "current CAS axes")
    fresh = subprocess.run(
        [sys.executable, "-B", "scripts/codex_harness/run_pr285_pillar_t_adjudication.py", "cas"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    fresh_cas = json.loads(fresh.stdout)
    require(fresh_cas["current_aggregate_status"] == "CAS_BLOCKED", "fresh current CAS promoted")
    require(fresh_cas["claim_promotion_cas_eligible_from_current_run"] is False, "fresh current CAS eligibility")
    require(fresh_cas["historical_aggregate_status"] == "CAS_4AXIS_PASS", "historical/current CAS separation")
    checks.append("current_cas_blocked_historical_only")

    required_command_ids = [row["id"] for row in policy["required_commands"]]
    rehearsal_ids = [row["id"] for row in rehearsal["commands"]]
    require(rehearsal["status"] == "PASS", "integration rehearsal status")
    require(rehearsal_ids == required_command_ids and len(rehearsal_ids) == 8, "integration command coverage")
    require(all(c["returncode"] == 0 and c["timed_out"] is False for c in rehearsal["commands"]), "integration command failure")
    require(rehearsal["candidate_seal_sha256"] == seal["seal_sha256"], "rehearsal seal binding")
    require(rehearsal["candidate_sha"] == seal["candidate_sha"], "rehearsal candidate binding")
    require(rehearsal["candidate_tree_sha"] == rehearsal["merged_tree_sha"] == seal["candidate_tree_sha"], "rehearsal tree binding")
    require(rehearsal["latest_target_sha"] == seal["base_sha"], "latest target binding")
    require(rehearsal["integration_policy_sha256"] == seal["integration_policy"]["sha256"], "policy binding")
    checks.append("sealed_integration_rehearsal")

    require((ROOT / "docs/codex_handoff/pr_status.yaml").read_bytes() == (ROOT / "machine_readable/pr_status.yaml").read_bytes(), "status mirrors differ")
    require(status == status_mirror, "status semantic mirror differs")
    stack = status["stacked_pr_execution"]
    pr285 = stack["prs"]["PR-285"]
    pr286 = stack["prs"]["PR-286"]
    require(stack["merge_policy"] == "HUMAN_ONLY", "merge policy promotion")
    require(pr285["lifecycle"] == "VALIDATED" and pr285["lifecycle_history"] == ["PLANNED", "ACTIVE", "IMPLEMENTED", "VALIDATED"], "PR-285 lifecycle")
    require(pr285["gate_dispositions"]["cas"] == "INCONCLUSIVE", "PR-285 CAS status")
    require(pr285["gate_dispositions"]["review"] == "DEFERRED", "PR-285 review status")
    require(all(pr285["gate_dispositions"][k] == "INELIGIBLE" for k in ("seal", "push", "publication")), "PR-285 premature release eligibility")
    require(pr285["sealed_head"] is pr285["pushed_ref"] is pr285["pr_url"] is None, "PR-285 publication identity exists")
    require(pr285["assurance_budget"]["consumed"] == 0, "PR-285 budget consumption")
    require(pr286["lifecycle"] == "PLANNED", "PR-286 lifecycle")
    require(pr286["gate_dispositions"] == {"eligibility": "INELIGIBLE"}, "PR-286 eligibility")
    require(pr286["assurance_budget"]["consumed"] == 0, "PR-286 budget consumption")
    checks.append("validated_status_and_human_only_boundary")

    require(receipt["scientific_status_effect"] == "ROW_LEVEL_TERMINAL_DISPOSITION_ONLY", "scientific effect promotion")
    require(set(spec["forbidden_uses"]) == {"Native solver validation.", "Observed-data inference.", "Bianchi family identification.", "Claim that all source rows are proved.", "Majority-vote CAS adjudication."}, "forbidden use contract drift")
    checks.append("no_scientific_or_publication_promotion")

    print(json.dumps({"status": "PASS", "checks": checks, "check_count": len(checks)}, sort_keys=True))


if __name__ == "__main__":
    main()
