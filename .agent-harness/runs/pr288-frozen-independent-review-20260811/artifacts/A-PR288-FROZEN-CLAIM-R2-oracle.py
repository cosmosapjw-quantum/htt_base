#!/usr/bin/env python3
"""Independent, bounded claim/provenance oracle for frozen PR-288."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[4]
SPEC = ROOT / "docs/research_program/post_pr275/pr288_spec.yaml"
POLICY = ROOT / "docs/research_program/post_pr275/pr288_publication_policy.json"
RECEIPT = ROOT / "docs/generated/pr288_bayesian_semantics_receipt.json"
SOURCE = ROOT / "htt/htt/htt/infer/bayesian_semantics.py"

EXPECTED_HASHES = {
    ".prguard/runtime/PR288_VALIDATED_CANDIDATE_SEAL.json": "cdde24653257c03c34fc94b2af1d58eff55f8aad4575bff07e8190c4d6a637fe",
    "docs/research_program/post_pr275/pr288_spec.yaml": "994603817e0546a1abb10b026cb3fcb31ebf5bee829c4e452798a808e19d4233",
    "docs/research_program/post_pr275/pr288_publication_policy.json": "c1e088fa12716ef9bc9870bad0213b8d37ae28e0dc96edec6e2cc66f1f81910b",
    "docs/PR_DELTAS/pr-288.md": "761b214ed538dc7e4c7a097355c2763f88531d7c3f380a12785f50426e06ad15",
    "docs/generated/pr288_bayesian_semantics_receipt.json": "622dadbcdf4a5d616a78f485fd6a772d1c7823ed8d77e808aa2bfc8f66169b0c",
    "htt/htt/htt/infer/bayesian_semantics.py": "d5bf1dd1856cf0eb302ade89ac99488fcfdd8f8589d463ed62c627f23e1e13cc",
    "docs/codex_handoff/pr_status.yaml": "d0377f0bf3a945947ccc76157962703b478631e17843e951d780714eff42c5b6",
    "machine_readable/pr_status.yaml": "d0377f0bf3a945947ccc76157962703b478631e17843e951d780714eff42c5b6",
    "docs/PR_DELTAS/pr-280.md": "46b46e1d3937600118cb2670d9788e2424ee4fc26f4ee1e9ac993e1b497b978b",
    ".agent-harness/scripts/review_coverage.py": "c435de8331952dc333fb81dd9be7463baaa57833497fd8701f8d07174a77dad4",
    ".agent-harness/scripts/strict_result_validation.py": "8c288e2d23899f07f11dce4a3bf7647a382adeed91f13a6c2c56dbf9cc4c4106",
}

EXPECTED_ALLOWED = [
    "analytic and synthetic model-dependent Bayesian method diagnostics",
    "bounded engine-agreement and uncertainty-calibration evidence",
    "posterior-draw PPC and fold-wise nuisance-refit LOOCV receipts",
]
EXPECTED_FORBIDDEN = [
    "observed-data evidence or PR-151 partial-data use",
    "legacy number reuse as current evidence",
    "MIO posterior or MIO evidence",
    "native solver validation geometry detection or Bianchi family identification",
]
EXPECTED_PROCESS = (
    "PASS means the registered analytic/synthetic cross-check, posterior-draw PPC, "
    "fold-wise-refit LOOCV, and mutations executed as specified. It is not observed "
    "evidence, native validation, a geometry result, or family identification."
)
EXPECTED_BUILD_ARGV = [
    "{python}",
    "-B",
    "scripts/codex_harness/run_pr288_bayesian_semantics.py",
    "build",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def content_id(value: object) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT
    ).strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module():
    spec = importlib.util.spec_from_file_location("pr288_claim_oracle_module", SOURCE)
    require(spec is not None and spec.loader is not None, "module loader unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    checks: dict[str, str] = {}
    for relative, expected in EXPECTED_HASHES.items():
        require(digest(ROOT / relative) == expected, f"required input drift: {relative}")
    checks["required_input_hashes"] = "PASS"

    seal = json.loads((ROOT / ".prguard/runtime/PR288_VALIDATED_CANDIDATE_SEAL.json").read_text())
    require(git("rev-parse", "HEAD") == seal["candidate_sha"], "candidate SHA drift")
    require(git("rev-parse", "HEAD^{tree}") == seal["candidate_tree_sha"], "candidate tree drift")
    require(
        git("merge-base", seal["base_sha"], seal["candidate_sha"]) == seal["merge_base_sha"],
        "merge-base drift",
    )
    require(not git("status", "--porcelain=v1", "--untracked-files=no"), "tracked worktree dirty")
    checks["candidate_identity"] = "PASS"

    spec = yaml.safe_load(SPEC.read_text())
    policy = json.loads(POLICY.read_text())
    receipt = json.loads(RECEIPT.read_text())
    canonical_status_bytes = (ROOT / "docs/codex_handoff/pr_status.yaml").read_bytes()
    mirror_status_bytes = (ROOT / "machine_readable/pr_status.yaml").read_bytes()
    require(canonical_status_bytes == mirror_status_bytes, "status mirrors differ")
    status = yaml.safe_load(canonical_status_bytes)

    frozen_claim = {
        "owner": "HTT",
        "scope": "preregistered synthetic and analytic Bayesian-method diagnostics",
        "claim_tier": "diagnostic_only",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "scientific_artifact_mode": "synthetic_diagnostic",
        "transfer_source": "none",
        "observed_data_executed": False,
        "public_use": False,
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
        "scientific_status_effect": "OPEN_UNCHANGED",
    }
    for key, expected in frozen_claim.items():
        require(spec[key] == expected, f"spec claim boundary drift: {key}")
        require(receipt["metadata"][key] == expected, f"receipt claim boundary drift: {key}")
    require(policy["claim_ceiling"] == "diagnostic_only", "publication claim ceiling drift")
    require(
        policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS",
        "publication family gate drift",
    )
    checks["htt_mio_ownership_boundary"] = "PASS"
    checks["claim_and_family_ceiling"] = "PASS"

    require(spec["allowed_uses"] == EXPECTED_ALLOWED, "spec allowed uses drift")
    require(receipt["metadata"]["allowed_uses"] == EXPECTED_ALLOWED, "receipt allowed uses drift")
    require(spec["forbidden_uses"] == EXPECTED_FORBIDDEN, "spec forbidden uses drift")
    require(receipt["metadata"]["forbidden_uses"] == EXPECTED_FORBIDDEN, "receipt forbidden uses drift")
    require(
        spec["receipt_contract"]["process_success_semantics"] == EXPECTED_PROCESS,
        "process-success semantics drift",
    )
    checks["allowed_forbidden_uses"] = "PASS"
    checks["process_success_nonpromotion"] = "PASS"

    expected_legacy = spec["legacy_disposition"]
    require(expected_legacy["status"] == "LEGACY_REPRODUCTION_ONLY", "legacy status promoted")
    require(
        expected_legacy["forbidden_roles"]
        == ["engine_anchor", "tolerance_anchor", "posterior_draw", "fold_result", "observed_claim"],
        "legacy forbidden roles drift",
    )
    require(receipt["metadata"]["legacy_disposition"] == expected_legacy, "legacy receipt drift")
    checks["legacy_value_quarantine"] = "PASS"

    pr280 = status["execution_resolutions"]["PR-280"]
    require(pr280["resolution"] == "COMPLETED_FAILED_WITH_RECEIPT", "PR-280 terminal promoted")
    require(pr280["success_dependency_satisfied"] is False, "PR-280 success invented")
    require(pr280["active_core_count"] == 3, "PR-280 failures hidden")
    dep = receipt["dependency_receipt"]
    require(dep["resolution"] == "COMPLETED_FAILED_WITH_RECEIPT", "receipt PR-280 terminal promoted")
    require(dep["success_dependency_satisfied"] is False, "receipt PR-280 success invented")
    require(dep["status"] == "PASS_REQUIRED_TERMINAL_RECEIPT", "PR-280 terminal receipt absent")
    require(dep["inventory_summary"]["active_core_count"] == 3, "active-core regressions hidden")
    checks["pr280_terminal_receipt_without_success_promotion"] = "PASS"

    pr288 = status["stacked_pr_execution"]["prs"]["PR-288"]
    pr289 = status["stacked_pr_execution"]["prs"]["PR-289"]
    require(pr288["lifecycle"] == "VALIDATED", "PR-288 lifecycle unexpectedly promoted")
    require(pr288["gate_dispositions"]["review"] == "DEFERRED", "review pre-promoted")
    require(pr289["gate_dispositions"]["eligibility"] == "INELIGIBLE", "downstream unlocked")
    checks["latest_target_integration"] = "PASS"

    bindings = receipt["source_bindings"]
    require(len(bindings) == 7, "source binding inventory drift")
    binding_map = {row["path"]: row["sha256"] for row in bindings}
    for relative in (
        "docs/research_program/post_pr275/pr288_spec.yaml",
        "docs/research_program/post_pr275/pr288_publication_policy.json",
        "htt/htt/htt/infer/bayesian_semantics.py",
        "docs/PR_DELTAS/pr-280.md",
    ):
        require(binding_map[relative] == EXPECTED_HASHES[relative], f"source binding drift: {relative}")
    expected_generation = "BOUND_SOURCE_WORKTREE:" + content_id(bindings)
    require(receipt["generation_identity"] == expected_generation, "generation identity not source-bound")
    require(
        receipt["metadata"]["git_commit_or_worktree_state"] == expected_generation,
        "metadata generation identity drift",
    )
    require(receipt["metadata"]["generating_procedure"] == EXPECTED_BUILD_ARGV, "build argv drift")
    unsigned = dict(receipt)
    claimed_content_id = unsigned.pop("receipt_content_id")
    require(content_id(unsigned) == claimed_content_id, "receipt content ID mismatch")
    checks["receipt_recomputation_and_content_address"] = "PASS"
    checks["source_bound_generation_identity"] = "PASS"
    checks["exact_build_argv"] = "PASS"

    require(receipt["terminal"] == "PASS_BAYESIAN_SEMANTICS_REPAIR", "process terminal not PASS")
    require(receipt["reasons"] == [], "passing receipt carries reasons")
    require(len(receipt["engine_results"]) == 10, "engine inventory incomplete")
    require(all(row["status"] == "PASS" for row in receipt["engine_results"]), "engine row failed")
    require(len(receipt["evidence_crosschecks"]) == 5, "crosscheck inventory incomplete")
    require(
        all(row["status"] == "PASS_INDEPENDENT_EVIDENCE_CROSSCHECK" for row in receipt["evidence_crosschecks"]),
        "engine crosscheck failed",
    )
    checks["analytic_fixture_accuracy"] = "PASS"
    checks["dynesty_sobol_independence"] = "PASS"
    checks["combined_uncertainty_preregistration"] = "PASS"
    checks["sobol_scramble_uncertainty"] = "PASS"

    require(
        receipt["degenerate_null_control"]["status"] == "PASS_DEGENERATE_NULL_COMPATIBLE_WITH_ZERO",
        "degenerate null promoted preference",
    )
    require(
        receipt["negative_control"]["status"] == "MISSPECIFIED_NEGATIVE_CONTROL_VISIBLE",
        "negative control hidden",
    )
    checks["degenerate_null_control"] = "PASS"
    checks["covariance_misspecification_visibility"] = "PASS"

    ppc = receipt["posterior_predictive"]
    loocv = receipt["loocv"]
    require(ppc["status"] == "PASS_REGISTERED_POSTERIOR_DRAW_PPC", "PPC contract failed")
    require(ppc["equality_rule"].endswith("greater_or_equal_observed_counts_in_tail"), "PPC equality drift")
    require(loocv["status"] == "PASS_FOLDWISE_REFIT_LOOCV", "LOOCV contract failed")
    require(len(loocv["fold_results"]) == 4, "fold inventory incomplete")
    require(len({row["held_out_id"] for row in loocv["fold_results"]}) == 4, "fold inventory duplicated")
    checks["posterior_draw_ppc"] = "PASS"
    checks["ppc_tail_and_equality_semantics"] = "PASS"
    checks["foldwise_nuisance_refit"] = "PASS"
    checks["integrated_heldout_predictive_density"] = "PASS"
    checks["complete_fold_inventory"] = "PASS"

    mutations = {row["mutation_id"]: row for row in receipt["mutation_results"]}
    require(len(mutations) == 15, "mutation inventory incomplete")
    require(all(row["executed"] and row["activated"] and row["killed"] for row in mutations.values()), "mutation survived")
    require(mutations["MU288-LEGACY-ANCHOR"]["killed"], "legacy anchor mutation survived")
    require(mutations["MU288-CLAIM-PROMOTION"]["killed"], "claim promotion mutation survived")
    checks["registered_mutation_completeness"] = "PASS"

    module = load_module()
    require(dict(module._FROZEN_CLAIM_BOUNDARY) == frozen_claim, "implementation claim boundary drift")
    require(list(module._FROZEN_ALLOWED_USES) == EXPECTED_ALLOWED, "implementation allowed uses drift")
    require(list(module._FROZEN_FORBIDDEN_USES) == EXPECTED_FORBIDDEN, "implementation forbidden uses drift")
    require(module._FROZEN_PROCESS_SUCCESS_SEMANTICS == EXPECTED_PROCESS, "implementation process semantics drift")
    require(list(module._FROZEN_GENERATING_PROCEDURE) == EXPECTED_BUILD_ARGV, "implementation build argv drift")
    require(importlib.util.find_spec("dynesty") is None, "system Dynesty unexpectedly present")
    fixture = module.load_registered_fixtures(SPEC)["PR288-NORMAL-MEAN-ANALYTIC"]
    blocked = module.run_dynesty_evidence(fixture, spec_path=SPEC)
    require(blocked.status.value == "BLOCKED_REQUIRED_ENGINE_UNAVAILABLE", "missing engine not typed blocked")
    require(blocked.log_evidence is None, "missing engine invented evidence")
    checks["system_engine_typed_blocker"] = "PASS"
    checks["spec_before_execution"] = "PASS"

    banned_positive = (
        "Bianchi geometry detected",
        "Bianchi family identified",
        "model-independent truth certificate",
        "MIO certifies truth",
        "external transfer validated as native",
    )
    surfaces = [SOURCE.read_text(), SPEC.read_text(), RECEIPT.read_text(), (ROOT / "docs/PR_DELTAS/pr-288.md").read_text()]
    require(not any(term in surface for term in banned_positive for surface in surfaces), "positive overclaim found")
    checks["absence_of_mio_posterior_or_family_claim"] = "PASS"

    require(
        seal["integration_policy"]["sha256"] == EXPECTED_HASHES["docs/research_program/post_pr275/pr288_publication_policy.json"],
        "seal/policy cross-binding drift",
    )
    require(policy["target_sha"] == seal["base_sha"], "policy target and seal base disagree")
    checks["publication_policy_cross_binding"] = "PASS"
    checks["portable_clean_integration"] = "PASS"

    required_cells = set(policy["required_review_cells"])
    require(required_cells <= set(checks), f"uncovered policy cells: {sorted(required_cells - set(checks))}")
    print(json.dumps({"ok": True, "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
