#!/usr/bin/env python3
"""Independent invariant oracle for the frozen PR-290 replay/claim review."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[4]
BASE = "45da1bf54149864fb9d87be3a828df202ee1df7f"
CANDIDATE = "8da5ea88ab98aa42c8538198ea2d625f7d0f0555"
TREE = "1dee7340e037c454d0516c43b9aef575c1a6a6f9"
COMMITS = (
    "206d9609f90cc34969b84c9d922ee60420386a7a",
    "757c32c09e8fa1ae6940fe51617a1b2e9faf6c6f",
    "ea1e9a92fe30ef22c5280e7d79007286731cfc5e",
    "27c83a1a12369b4b563667ff5145ae9a717b24f0",
    "73dc87c4a0e0cd752ab2d9fe10a7299f120f2f1d",
    "8da5ea88ab98aa42c8538198ea2d625f7d0f0555",
)


def git(*args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=ROOT, input=input_bytes, check=True, capture_output=True
    ).stdout


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_content_id(payload: dict[str, object], field: str) -> str:
    body = dict(payload)
    body.pop(field, None)
    encoded = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def tracked_manifest() -> str:
    paths = [
        item.decode("utf-8")
        for item in git("ls-files", "-z").split(b"\0")
        if item
    ]
    identities = {relative: sha(ROOT / relative) for relative in paths}
    encoded = json.dumps(
        identities, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    assert git("rev-parse", "HEAD").decode().strip() == CANDIDATE
    assert git("rev-parse", "HEAD^{tree}").decode().strip() == TREE
    assert git(
        "rev-parse",
        "refs/remotes/origin/changeset/pr289-native-data-identity-recovery-20260811",
    ).decode().strip() == BASE
    assert git("merge-base", BASE, CANDIDATE).decode().strip() == BASE
    observed_commits = tuple(
        git("rev-list", "--reverse", f"{BASE}..{CANDIDATE}").decode().splitlines()
    )
    assert observed_commits == COMMITS

    seal = json.loads((ROOT / ".prguard/runtime/PR290_R2_CANDIDATE_SEAL.json").read_text())
    patch_ids: list[str] = []
    for commit in COMMITS:
        patch = git("show", "--pretty=format:", commit)
        patch_ids.append(
            subprocess.run(
                ["git", "patch-id", "--stable"],
                cwd=ROOT,
                input=patch,
                check=True,
                capture_output=True,
            ).stdout.decode().split()[0]
        )
    assert len(set(patch_ids)) == 6
    assert patch_ids == [row["stable_patch_id"] for row in seal["stable_patch_ids"]]
    base_patch_rows = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=ROOT,
        input=git("log", "-p", "--format=format:%H", BASE),
        check=True,
        capture_output=True,
    ).stdout.decode().splitlines()
    base_patch_ids = {row.split()[0] for row in base_patch_rows if row.strip()}
    assert not (set(patch_ids) & base_patch_ids)

    spec = yaml.safe_load(
        (ROOT / "docs/research_program/post_pr275/pr290_spec.yaml").read_text()
    )
    boundary = spec["scientific_boundary"]
    assert boundary["claim_tier"] == "diagnostic_only"
    assert boundary["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
    assert boundary["transfer_source"] == "none"
    assert boundary["observed_data_executed"] is False
    assert boundary["public_use"] is False
    assert boundary["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert spec["artifact_ownership"] == {
        "delivery_orchestration": "HTT",
        "observable_features_morphology_axes_and_null_features": "OBSSTAT",
        "activation_manifests_provenance_and_semantic_guards": "COMMON",
        "model_dependent_likelihood_posterior_evidence": "HTT_NOT_EXECUTED_BY_PREACTIVATION",
        "mio_diagnostic_crosscheck": "NOT_AN_ACTIVE_PR290_ESTIMAND",
        "tsc_teff": "LEGACY_ONLY",
    }

    status = yaml.safe_load((ROOT / "docs/codex_handoff/pr_status.yaml").read_text())
    stack = status["stacked_pr_execution"]
    assert stack["merge_policy"] == "HUMAN_ONLY"
    assert stack["active_implementation_pr"] == "PR-290"
    pr287, pr290, pr291 = (stack["prs"][key] for key in ("PR-287", "PR-290", "PR-291"))
    assert pr287["gate_dispositions"]["fresh_execution"] == "INCONCLUSIVE"
    assert pr290["assurance_budget"] == {"maximum": 16, "consumed": 4}
    assert pr290["production_hash"] == seal["production_hash"]
    assert pr290["base_sha"] == BASE and pr290["predecessor_sealed_sha"] == BASE
    assert pr291["lifecycle"] == "PLANNED"
    assert pr291["gate_dispositions"] == {"eligibility": "INELIGIBLE"}
    assert pr291["assurance_budget"] == {"maximum": 16, "consumed": 0}

    receipt_path = ROOT / "docs/research_program/post_pr275/data_runs/planck/PR290_NONEXECUTION_RECEIPT.json"
    receipt = json.loads(receipt_path.read_text())
    assert receipt["receipt_content_sha256"] == canonical_content_id(
        receipt, "receipt_content_sha256"
    )
    assert receipt["terminal"] == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
    assert receipt["numeric_outputs_written"] == []
    assert receipt["observed_data_executed"] is False
    assert receipt["network_or_download_side_effect"] is False
    assert receipt["owner_scope_and_claim_boundary"]["claim_tier"] == "diagnostic_only"
    for relative, digest in receipt["source_bindings"].items():
        assert digest == "sha256:" + sha(ROOT / relative)

    identity = json.loads(
        (ROOT / "docs/generated/pr289_data_identity_v2_receipt.json").read_text()
    )
    assert identity["receipt_content_id"] == canonical_content_id(
        identity, "receipt_content_id"
    )
    for relative, digest in identity["source_bindings"].items():
        assert digest == "sha256:" + sha(ROOT / relative)
    planck = [row for row in identity["lane_decisions"] if row["lane_id"] == "PLANCK"]
    assert len(planck) == 1 and planck[0]["status"] == "REJECTED_NOT_PRESENT"

    delta = (ROOT / "docs/PR_DELTAS/pr-290.md").read_text()
    for token in ("G49", "G50", "G51", "G52", "G53", "obsolete G54", "duplicate aliases"):
        assert token in delta
    assert "human-readable delta" in delta
    assert "provenance rather than an exact candidate patch-id equivalence claim" in delta
    live_manifest = tracked_manifest()
    reported = re.search(r"`([0-9a-f]{64})`;\n  no observed input root", delta)
    assert reported is not None
    assert reported.group(1) != live_manifest

    print(
        json.dumps(
            {
                "status": "PASS",
                "safe_boundary": "verified",
                "candidate_patch_ids": patch_ids,
                "base_patch_collision_count": 0,
                "current_portable_manifest": live_manifest,
                "reported_portable_manifest": reported.group(1),
                "finding": "current-evidence portable manifest in pr-290.md is stale",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
