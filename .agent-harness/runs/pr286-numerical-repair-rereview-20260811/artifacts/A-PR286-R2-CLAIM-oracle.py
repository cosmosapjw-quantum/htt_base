#!/usr/bin/env python3
"""Independent bounded claim/lifecycle oracle for PR-286 repaired candidate."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[4]
RUN_ID = "pr286-numerical-repair-rereview-20260811"
ASSIGNMENT_ID = "A-PR286-R2-CLAIM"
OUT = (
    ROOT
    / ".agent-harness/runs"
    / RUN_ID
    / "artifacts"
    / f"{ASSIGNMENT_ID}-oracle-output.json"
)
BASE = "16bc6db511b8b7228e5c4dcb95c65074fe519f24"
CANDIDATE = "7ad8176282554670909c28306b3e14e83662a42b"
TREE = "d14eedaa79f902f5b47b507fa3951e5a22cbe9b7"

INPUT_HASHES = {
    ".prguard/runtime/PR286_R2_CANDIDATE_SEAL.json": "217f4c0cd8da2c6b40c15257ea1954352704fbb01757ccf9d7ff9addd6165509",
    "docs/research_program/post_pr275/pr286_spec.yaml": "7b359af0818766860b4bfecc4eae36fa2b31580636d3dfea99a6ed280c4e4989",
    "docs/research_program/post_pr275/pr286_publication_policy.json": "768b5263096154770e48762704e363d127ea1c1ef89a8c973f94a14173ec086d",
    "scripts/codex_harness/run_pr286_pillar_s_adjudication.py": "7da531e70160a751e45348db7eeb4d2ee3fe129a31cbca01315c242a38f5557e",
    "docs/research_program/post_pr275/pillar_s_adjudication/PILLAR_S_COMPLETE_ADJUDICATION_V1.json": "ff2fe5f92cc3a6470500905f742dd788d63fd17a53ac00ffb7560cf3c1c503c2",
    "docs/PR_DELTAS/pr-286.md": "3553f2994a77172b83b553c034f9cc44e1736924878c2b3f425d2f734209b441",
    "docs/codex_handoff/pr_status.yaml": "9d9a7d2f2f6a7362ef81314c816f3338d76ca66f0bcf2e19efaf472d61c4ed6d",
    "machine_readable/pr_status.yaml": "9d9a7d2f2f6a7362ef81314c816f3338d76ca66f0bcf2e19efaf472d61c4ed6d",
    "docs/codex_handoff/pr_backlog.yaml": "73553b6056e5111c1047b80f79c35cdb8e898e0a7b8a7e7e28f97731b5cc699e",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(value: object) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    )


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def load_yaml(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, check=False)


def require(condition: bool, check_id: str, checks: list[str]) -> None:
    if not condition:
        raise AssertionError(check_id)
    checks.append(check_id)


def main() -> int:
    started = utc_now()
    checks: list[str] = []
    commands: list[dict[str, object]] = []
    try:
        for path, expected in INPUT_HASHES.items():
            require(sha256((ROOT / path).read_bytes()) == expected, f"input-hash:{path}", checks)
        require(
            (ROOT / "docs/codex_handoff/pr_status.yaml").read_bytes()
            == (ROOT / "machine_readable/pr_status.yaml").read_bytes(),
            "status-mirror-byte-equality",
            checks,
        )

        seal = load_json(".prguard/runtime/PR286_R2_CANDIDATE_SEAL.json")
        assignment = load_json(f".agent-harness/runs/{RUN_ID}/assignments/{ASSIGNMENT_ID}.json")
        binding = assignment["candidate_binding"]
        seal_body = dict(seal)
        seal_digest = seal_body.pop("seal_sha256")
        require(canonical_sha256(seal_body) == seal_digest == binding["seal_sha256"], "candidate-seal-canonical-hash", checks)
        require(
            all(
                seal[key] == binding[key]
                for key in (
                    "base_sha", "candidate_sha", "merge_base_sha", "candidate_tree_sha",
                    "diff_sha256", "changed_files_sha256", "production_hash",
                )
            ),
            "assignment-candidate-binding",
            checks,
        )
        require(run(["git", "status", "--porcelain=v1"]).stdout == "", "candidate-clean", checks)
        require(run(["git", "rev-parse", "HEAD"]).stdout.strip() == CANDIDATE, "candidate-head", checks)
        require(run(["git", "rev-parse", "HEAD^{tree}"]).stdout.strip() == TREE, "candidate-tree", checks)
        require(run(["git", "merge-base", BASE, CANDIDATE]).stdout.strip() == BASE, "candidate-merge-base", checks)
        diff = subprocess.run(
            [
                "git", "diff", "--binary", "--full-index", "--no-color", "--no-ext-diff",
                "--no-textconv", "--no-renames", "--submodule=short", f"{BASE}..{CANDIDATE}",
            ],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        require(diff.returncode == 0 and sha256(diff.stdout) == seal["diff_sha256"], "candidate-diff-digest", checks)

        spec = load_yaml("docs/research_program/post_pr275/pr286_spec.yaml")
        policy = load_json("docs/research_program/post_pr275/pr286_publication_policy.json")
        receipt = load_json(
            "docs/research_program/post_pr275/pillar_s_adjudication/PILLAR_S_COMPLETE_ADJUDICATION_V1.json"
        )
        expected_claim = {
            "claim_tier": "diagnostic_only",
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
            "transfer_source": "none",
            "observed_data_executed": False,
            "public_use": False,
            "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
        }
        require(all(spec[key] == value for key, value in expected_claim.items()), "spec-claim-ceiling", checks)
        require(all(receipt["metadata"][key] == value for key, value in expected_claim.items()), "receipt-claim-ceiling", checks)
        require(policy["claim_ceiling"] == "diagnostic_only", "policy-claim-ceiling", checks)
        require(policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS", "policy-family-gate", checks)
        require(policy["target_sha"] == BASE and seal["base_sha"] == BASE, "policy-exact-predecessor-sha", checks)
        require(
            seal["target_branch"] == "changeset/pr285-pillar-t-adjudication-recovery-20260810"
            and policy["target_ref"] == f"origin/{seal['target_branch']}",
            "policy-exact-predecessor-ref",
            checks,
        )

        expected_ownership = {
            "COMMON": "exact contracts and proof identities",
            "OBSSTAT": "observable estimands features nulls and covariance inputs",
            "HTT": "model-dependent calibration coverage and inference diagnostics",
            "MIO": "diagnostic residual and coherence consumers only",
        }
        require(receipt["ownership"] == expected_ownership, "receipt-owner-separation", checks)
        require(
            receipt["mio_forbidden_outputs"] == ["likelihood", "posterior", "Bayes_factor", "evidence"],
            "mio-diagnostic-only-firewall",
            checks,
        )

        rows = receipt["rows"]
        counts = Counter(row["verdict"] for row in rows)
        expected_counts = {
            "PASS": 21,
            "FAIL": 0,
            "INCONCLUSIVE_WITH_RECEIPT": 50,
            "BLOCKED_WITH_RECEIPT": 1,
        }
        require(len(rows) == 72 and dict(receipt["summary"]["terminal_counts"]) == expected_counts, "receipt-declared-21-0-50-1", checks)
        require(all(counts.get(key, 0) == value for key, value in expected_counts.items()), "receipt-recounted-21-0-50-1", checks)
        require(receipt["summary"]["source_rows"] == 58 and receipt["summary"]["vector_tensor_rows"] == 14, "receipt-58-plus-14", checks)
        vts14 = next(row for row in rows if row["row_id"] == "VT-S14")
        require(vts14["verdict"] == "BLOCKED_WITH_RECEIPT", "vts14-blocked", checks)
        require(vts14["negative_controls"]["admitted_data_executed"] is False, "vts14-no-admitted-data", checks)
        require(vts14["source_status_effect"] == "RETAIN_PROGRAM_OBLIGATION", "vts14-program-obligation-retained", checks)
        require(vts14["claim_ceiling"] == "diagnostic_only", "vts14-no-claim-promotion", checks)
        require(
            vts14["coverage_evidence"]["MIO_local_diagnostic_cross_check"]["posterior_present"] is False
            and vts14["coverage_evidence"]["MIO_global_diagnostic_cross_check"]["likelihood_present"] is False,
            "vts14-mio-no-inference-output",
            checks,
        )

        require(
            receipt["terminal"] == "PASS_COMPLETE_PILLAR_S_ADJUDICATION"
            and receipt["success_semantics"] == "PROCESS_COMPLETION_ONLY"
            and receipt["scientific_status_effect"] == "ROW_LEVEL_EVIDENCE_SPECIFIC_DISPOSITION_ONLY",
            "process-pass-not-proposition-promotion",
            checks,
        )
        consumer = receipt["future_consumer_contract"]
        require(
            consumer["consumer"] == "PR-287"
            and consumer["preserve_inconclusive_and_blocked"] is True
            and consumer["synthetic_validation_effect"] == "NO_OBSERVED_OR_SOURCE_PROOF_PROMOTION",
            "pr287-nonpromotion-consumer-contract",
            checks,
        )
        mutation_map = {row["mutation_id"]: row for row in receipt["mutation_results"]}
        require(
            len(mutation_map) == 19 and all(row["executed"] and row["activated"] and row["killed"] and not row["survivor"] for row in mutation_map.values()),
            "all-19-mutations-killed",
            checks,
        )
        require(mutation_map["MU286-CLAIM-PROMOTION"]["kill_marker"] == "CLAIM_FIREWALL_DRIFT", "claim-promotion-mutation-killed", checks)
        require(mutation_map["MU286-MIO-POSTERIOR"]["kill_marker"] == "OWNERSHIP_FIREWALL_DRIFT", "mio-posterior-mutation-killed", checks)
        require(mutation_map["MU286-VTS14-DATA-PROMOTION"]["kill_marker"] == "VTS14_ADMITTED_DATA_PROMOTION", "data-promotion-mutation-killed", checks)

        status = load_yaml("docs/codex_handoff/pr_status.yaml")
        stack = status["stacked_pr_execution"]
        pr286 = stack["prs"]["PR-286"]
        pr287 = stack["prs"]["PR-287"]
        require(stack["merge_policy"] == "HUMAN_ONLY", "human-only-merge", checks)
        require(
            pr286["lifecycle"] == "VALIDATED"
            and pr286["lifecycle_history"] == ["PLANNED", "ACTIVE", "IMPLEMENTED", "VALIDATED"],
            "pr286-lifecycle-validated",
            checks,
        )
        require(
            pr286["predecessor_pr"] == "PR-285"
            and pr286["base_sha"] == BASE
            and pr286["predecessor_sealed_sha"] == BASE,
            "pr286-exact-predecessor-binding",
            checks,
        )
        deferred = {"code", "physics", "statistics", "claim", "harness", "portability_replay", "review"}
        require(all(pr286["gate_dispositions"][key] == "DEFERRED" for key in deferred), "pr286-rereview-deferred", checks)
        require(pr286["assurance_budget"] == {"maximum": 16, "consumed": 4}, "pr286-assurance-4-of-16", checks)
        require(
            pr287["lifecycle"] == "PLANNED"
            and pr287["gate_dispositions"] == {"eligibility": "INELIGIBLE"}
            and pr287["assurance_budget"] == {"maximum": 16, "consumed": 0},
            "pr287-ineligible-zero-budget",
            checks,
        )
        resolutions = status["execution_resolutions"]
        require(
            resolutions["PR-273"]["scientific_status_effect"] == "registered_blind_synthetic_integration_only"
            and resolutions["PR-273"]["public_use"] is False,
            "pr273-synthetic-only",
            checks,
        )
        require(
            resolutions["PR-274"]["data_admission_status"] == "NO_ADMITTED_DATA_PILOT"
            and resolutions["PR-274"]["admitted_input_count"] == 0
            and resolutions["PR-274"]["observed_data_executed"] is False
            and resolutions["PR-274"]["public_use"] is False,
            "pr274-no-admitted-data",
            checks,
        )

        backlog = load_yaml("docs/codex_handoff/pr_backlog.yaml")
        cards = {row["id"]: row for row in backlog["prs"]}
        require(cards["PR-273"]["claim_tier_ceiling"] == "diagnostic_only" and cards["PR-273"]["public_use"] is False, "pr273-backlog-ceiling", checks)
        require(cards["PR-274"]["owner"] == "OBSSTAT" and cards["PR-274"]["public_use"] is False, "pr274-obsstat-admission-owner", checks)
        dependency = next(row for row in cards["PR-287"]["dependency_contracts"] if row["upstream_id"] == "PR-286")
        require(
            dependency["required_terminal"] == "PASS_COMPLETE_PILLAR_S_ADJUDICATION"
            and dependency["success_semantics"] == "PROCESS_COMPLETION_ONLY"
            and dependency["downstream_row_contract"]["preserve_inconclusive_and_blocked"] is True,
            "backlog-pr287-edge-nonpromotion",
            checks,
        )

        delta = (ROOT / "docs/PR_DELTAS/pr-286.md").read_text(encoding="utf-8")
        for fragment, check_id in (
            ("`VALIDATED_PENDING_BOUNDED_REREVIEW`", "delta-resolution"),
            ("Lifecycle remains `VALIDATED`.", "delta-lifecycle"),
            ("now `DEFERRED`, not silently regraded PASS", "delta-no-silent-regrade"),
            ("Assurance consumption remains 4 of\n16", "delta-assurance"),
            ("PR-287 activation remain INELIGIBLE", "delta-pr287-ineligible"),
            ("merge remains human-only", "delta-human-only"),
            ("historical validation evidence only; they are not an\nacceptance seal", "delta-historical-not-acceptance"),
            ("current-candidate\nresults, not reused historical outputs", "delta-current-not-historical"),
            ("the repair does not promote any scientific row", "delta-repair-no-promotion"),
        ):
            require(fragment in delta, check_id, checks)

        runner_path = ROOT / "scripts/codex_harness/run_pr286_pillar_s_adjudication.py"
        module_spec = importlib.util.spec_from_file_location("pr286_claim_oracle_target", runner_path)
        if module_spec is None or module_spec.loader is None:
            raise AssertionError("runner-import-spec")
        runner = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(runner)
        runner.validate_complete_adjudication_receipt(receipt)
        checks.append("runner-validates-tracked-receipt")
        for mutation_id, marker in (
            ("MU286-CLAIM-PROMOTION", "CLAIM_FIREWALL_DRIFT"),
            ("MU286-MIO-POSTERIOR", "OWNERSHIP_FIREWALL_DRIFT"),
            ("MU286-VTS14-DATA-PROMOTION", "VTS14_ADMITTED_DATA_PROMOTION"),
        ):
            try:
                runner._validate_core(runner.apply_registered_mutation(json.loads(json.dumps(receipt)), mutation_id))
            except runner.PillarSAdjudicationError as exc:
                require(str(exc) == marker, f"live-mutation:{mutation_id}", checks)
            else:
                raise AssertionError(f"live-mutation-survived:{mutation_id}")

        commands_to_run = [
            [sys.executable, "-B", "scripts/codex_harness/run_pr286_pillar_s_adjudication.py", "check"],
            [
                sys.executable, "-B", "scripts/check_claim_language.py", "--strict-missing", "--include-archives",
                "scripts/codex_harness/run_pr286_pillar_s_adjudication.py",
                "tests/contracts/test_pillar_s_complete_adjudication.py",
                "docs/research_program/post_pr275/pr286_spec.yaml",
                "docs/research_program/post_pr275/pillar_s_adjudication/PILLAR_S_COMPLETE_ADJUDICATION_V1.json",
                "docs/PR_DELTAS/pr-286.md",
            ],
        ]
        for argv in commands_to_run:
            completed = run(argv)
            commands.append(
                {
                    "argv": argv,
                    "returncode": completed.returncode,
                    "stdout_sha256": sha256(completed.stdout.encode()),
                    "stderr_sha256": sha256(completed.stderr.encode()),
                }
            )
            require(completed.returncode == 0, f"subprocess:{Path(argv[1]).name if len(argv) > 1 else argv[0]}", checks)

        payload = {
            "schema_version": 1,
            "run_id": RUN_ID,
            "assignment_id": ASSIGNMENT_ID,
            "started_at": started,
            "completed_at": utc_now(),
            "status": "PASS",
            "check_count": len(checks),
            "checks": checks,
            "commands": commands,
            "claim_audit": {
                "upgraded_claims": [],
                "downgraded_claims": [],
                "forbidden_drift_detected": [],
                "ledger_updates_needed": [],
                "proposed_changes": [],
                "risks_and_kill_switches": [
                    "Any candidate, seal, spec, receipt, lifecycle, or predecessor identity change invalidates this review.",
                    "Any observed/native/public/family promotion, MIO inference output, admitted-data relabeling, or historical-envelope reuse fails closed.",
                ],
                "status_updates_needed": [
                    "This result may satisfy only its registered fresh bounded claim rereview cell; aggregate review and sealing remain separate gates."
                ],
            },
        }
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "run_id": RUN_ID,
            "assignment_id": ASSIGNMENT_ID,
            "started_at": started,
            "completed_at": utc_now(),
            "status": "FAIL",
            "check_count": len(checks),
            "checks": checks,
            "commands": commands,
            "error": f"{type(exc).__name__}:{exc}",
        }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "check_count": payload["check_count"], "output": str(OUT.relative_to(ROOT))}, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
