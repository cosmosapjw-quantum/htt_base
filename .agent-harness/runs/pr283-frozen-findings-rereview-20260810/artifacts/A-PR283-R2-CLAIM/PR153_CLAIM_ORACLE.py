#!/usr/bin/env python3
"""Assignment-local invariant oracle for the PR-283 claim/provenance rereview."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[5]
SPEC_PATH = ROOT / "docs/research_program/post_pr275/pr283_spec.yaml"
POLICY_PATH = ROOT / "docs/research_program/post_pr275/pr283_publication_policy.json"
RECEIPT_PATH = ROOT / "docs/generated/pr283_weak_identification_receipt.json"
RUNNER_PATH = ROOT / "scripts/codex_harness/run_pr283_weak_identification.py"
DELTA_PATH = ROOT / "docs/PR_DELTAS/pr-283.md"
TEST_PATH = ROOT / "tests/contracts/test_weak_identification.py"
PRIOR_PATH = ROOT / (
    ".agent-harness/runs/pr283-candidate-review-20260810/results/"
    "A-PR283-FROZEN-CLAIM.json"
)
CANONICAL = "PR-153 artifacts are forbidden input."
CURRENT_CANDIDATE = "6fa98399dfe8b0a0735f9938063420457cda7688"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assignment_constant(module: ast.Module, name: str):
    for node in module.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                return ast.literal_eval(node.value)
    raise AssertionError(f"missing runner constant {name}")


spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
runner_text = RUNNER_PATH.read_text(encoding="utf-8")
runner_ast = ast.parse(runner_text)
delta = DELTA_PATH.read_text(encoding="utf-8")
tests = TEST_PATH.read_text(encoding="utf-8")
prior = json.loads(PRIOR_PATH.read_text(encoding="utf-8"))

checks: dict[str, bool] = {
    "spec_forbidden_use": CANONICAL in spec["forbidden_uses"],
    "spec_caveat": CANONICAL in spec["caveats"],
    "policy_forbidden_input": CANONICAL in policy["forbidden_inputs"],
    "generator_forbidden_use": CANONICAL in assignment_constant(runner_ast, "_FORBIDDEN_USES"),
    "generator_caveat": CANONICAL in assignment_constant(runner_ast, "_CAVEATS"),
    "receipt_forbidden_use": CANONICAL in receipt["forbidden_uses"],
    "receipt_caveat": CANONICAL in receipt["caveats"],
    "delta_prohibition": (
        "PR-151 partial/background acquisition and PR-153 artifacts are forbidden\n"
        "  inputs" in delta
    ),
    "delta_repair_chronology": (
        "PR-153 is now bound in the spec forbidden uses and\n"
        "caveats, policy forbidden inputs, generator constants, and fresh receipt." in delta
    ),
    "test_canonical_value": 'forbidden_pr153 = "PR-153 artifacts are forbidden input."' in tests,
    "test_spec_forbidden_use": 'assert forbidden_pr153 in spec["forbidden_uses"]' in tests,
    "test_spec_caveat": 'assert forbidden_pr153 in spec["caveats"]' in tests,
    "test_policy_forbidden_input": '"forbidden_inputs"' in tests,
    "test_receipt_forbidden_use": 'assert forbidden_pr153 in payload["forbidden_uses"]' in tests,
    "test_receipt_caveat": 'assert forbidden_pr153 in payload["caveats"]' in tests,
    "spec_owner": spec["owner"] == "HTT",
    "spec_contributors": spec["contributors"] == ["COMMON", "MIO"],
    "receipt_owner": receipt["owner"] == "HTT",
    "receipt_contributors": receipt["contributors"] == ["COMMON", "MIO"],
    "c2_diagnostic_only": (
        spec["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
        and spec["claim_tier"] == receipt["claim_tier"] == "diagnostic_only"
        and receipt["claim_level"] == spec["claim_level"]
        and policy["claim_ceiling"] == "diagnostic_only"
    ),
    "transfer_none": spec["transfer_source"] == receipt["transfer_source"] == "none",
    "observed_false": spec["observed_data_executed"] is receipt["observed_data_executed"] is False,
    "public_false": spec["public_use"] is receipt["public_use"] is False,
    "family_gate_blocked": (
        spec["family_identification_gate"]
        == receipt["family_identification_gate"]
        == policy["family_identification_gate"]
        == "BLOCKED_PRE_NATIVE_ATLAS"
    ),
    "no_mio_posterior_or_truth": (
        "HTT posterior/evidence production or MIO truth certification."
        in spec["forbidden_uses"]
        and "does not create a MIO posterior or a\n  truth certificate" in delta
    ),
    "no_family_or_native_promotion": (
        "Native solver validation, geometry detection, or Bianchi family identification."
        in receipt["forbidden_uses"]
        and "not promote morphology compatibility to family identification" in delta
    ),
    "prior_fail_is_older_candidate": (
        prior["status"] == "fail"
        and prior["candidate_binding"]["candidate_sha"] != CURRENT_CANDIDATE
        and prior["candidate_binding"]["candidate_sha"]
        == "6ee9048ffd80f25337f405d8c6a39fd3b7f489eb"
    ),
}

source_bindings = {row["path"]: row["sha256"] for row in receipt["source_bindings"]}
for path in (SPEC_PATH, POLICY_PATH, RUNNER_PATH, TEST_PATH):
    relative = str(path.relative_to(ROOT))
    checks[f"receipt_source_hash:{relative}"] = source_bindings.get(relative) == sha256(path)

unsigned = dict(receipt)
recorded_content_hash = unsigned.pop("artifact_content_sha256")
canonical = json.dumps(
    unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True
).encode("utf-8")
checks["receipt_content_address"] = recorded_content_hash == hashlib.sha256(canonical).hexdigest()

failed = sorted(name for name, passed in checks.items() if not passed)
payload = {
    "schema": "htt.pr283.claim_rereview_oracle.v1",
    "status": "PASS" if not failed else "FAIL",
    "candidate_sha": CURRENT_CANDIDATE,
    "canonical_pr153_semantics": CANONICAL,
    "checks": checks,
    "failed_checks": failed,
}
print(json.dumps(payload, sort_keys=True, indent=2))
raise SystemExit(0 if not failed else 1)
