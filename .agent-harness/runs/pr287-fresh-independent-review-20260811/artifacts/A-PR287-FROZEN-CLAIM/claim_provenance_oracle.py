#!/usr/bin/env python3
"""Independent, read-only PR-287 claim-boundary invariant checker."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[5]
EXPECTED = {
    "candidate_sha": "06ee728054fd62423fa90bc6a5d714b9be8631e3",
    "candidate_tree_sha": "dd909b5d35a385b251547f6224b657346d7688f6",
    "diff_sha256": "83ef2581a3a1afdf5459ad64730783f6f7e905a3cda155236ec44971b160912f",
}


def load_yaml(relative: str) -> dict:
    return yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))


def main() -> int:
    spec = load_yaml("docs/research_program/post_pr275/pr287_spec.yaml")
    status = load_yaml("docs/codex_handoff/pr_status.yaml")
    policy = json.loads(
        (ROOT / "docs/research_program/post_pr275/pr287_publication_policy.json").read_text()
    )
    seal_path = ROOT / ".prguard/runtime/PR287_VALIDATED_CANDIDATE_SEAL.json"
    seal = json.loads(seal_path.read_text())
    readme = (ROOT / "docs/research_program/post_pr275/blind_replay/README.md").read_text()
    module = (ROOT / "htt/src/common/post275_blind_replay.py").read_text()
    claim_tests = (ROOT / "tests/integration/test_post275_blind_replay.py").read_text()
    checks = {
        "candidate_identity": all(seal.get(key) == value for key, value in EXPECTED.items()),
        "seal_file_hash": hashlib.sha256(seal_path.read_bytes()).hexdigest()
        == "fbe4787a82f650ec050fab020ae2c9545e9f7fe778ec2d6f5d4550470537712b",
        "c2_diagnostic_metadata": (
            spec["claim_tier"] == "diagnostic_only"
            and spec["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
            and spec["scientific_artifact_mode"] == "synthetic_diagnostic"
            and spec["transfer_source"] == "none"
            and spec["observed_data_executed"] is False
            and spec["public_use"] is False
            and spec["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
        ),
        "owner_separation": (
            spec["owner"] == "HTT"
            and spec["result_pack_contract"]["pack_A"]["owner"] == "COMMON"
            and spec["result_pack_contract"]["pack_B"]["owner"] == "HTT"
            and spec["result_pack_contract"]["pack_C"]["owner"] == "MIO"
            and "posterior" in spec["result_pack_contract"]["pack_C"]["forbidden_surfaces"]
        ),
        "history_fresh_separation": (
            spec["lane_separation"]["historical_replay"]["mode"] == "EXACT_HISTORICAL_REPLAY_ONLY"
            and spec["lane_separation"]["fresh_challenge"]["mode"] == "NEW_CHALLENGE_AND_NEW_TRUTH_VAULT"
            and "proof, observed, native, geometry, or family promotion"
            in spec["lane_separation"]["historical_replay"]["forbidden_use"]
        ),
        "pr151_exclusion": (
            "PR-151 partial acquisition is\nnot an allowed input." in readme
            and "pr151_partial_data_excluded" in spec["result_pack_contract"]["shared_metadata"]
        ),
        "typed_executor_block": (
            spec["fresh_artifact_contracts"]["analyst_executor_status"]
            == "BLOCKED_CAPABILITY_ISOLATED_EXECUTOR_NOT_INSTALLED"
            and spec["fresh_artifact_contracts"]["execution_disposition"] == "INCONCLUSIVE"
            and "BLOCKED_CAPABILITY_ISOLATED_EXECUTOR_NOT_INSTALLED" in readme
        ),
        "lifecycle": (
            status["stacked_pr_execution"]["prs"]["PR-287"]["lifecycle"] == "VALIDATED"
            and status["stacked_pr_execution"]["prs"]["PR-287"]["gate_dispositions"]["fresh_execution"] == "INCONCLUSIVE"
            and status["stacked_pr_execution"]["prs"]["PR-287"]["execution_blocker"]
            == "BLOCKED_CAPABILITY_ISOLATED_EXECUTOR_NOT_INSTALLED"
        ),
        "claim_variant_rejection": (
            all(alias in spec["result_pack_contract"]["recursive_forbidden_aliases"]
                for alias in ("posterior_odds", "log_evidence", "family_candidate", "detected_geometry"))
            and all(variant in claim_tests for variant in (
                '"we", "identified", "a", "Bianchi", "family"',
                '"Bianchi", "families", "were", "identified"',
                '"identified", "the", "family", "as", "Bianchi"',
            ))
            and "family_candidate" in module
        ),
        "policy_ceiling": (
            policy["claim_ceiling"] == "diagnostic_only"
            and policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
            and len(policy["required_review_cells"]) == 30
        ),
    }
    payload = {"schema_version": 1, "kind": "pr287_claim_provenance_oracle", "checks": checks}
    print(json.dumps(payload, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
