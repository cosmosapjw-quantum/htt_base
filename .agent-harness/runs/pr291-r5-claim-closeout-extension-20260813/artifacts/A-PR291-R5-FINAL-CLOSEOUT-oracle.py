#!/usr/bin/env python3
"""Deterministic metadata-only FAIL closeout oracle for PR-291 R5."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
RUN = ".agent-harness/runs/pr291-r5-claim-closeout-extension-20260813"
ORDINARY = ".agent-harness/runs/pr291-authorized-r5-review-20260813"


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def git(*args: str, input_bytes: bytes | None = None) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, input=input_bytes, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.decode().strip()


assignment = read_json(f"{RUN}/assignments/A-PR291-R5-FINAL-CLOSEOUT.json")
assert assignment["context_version"] == read_json(
    ".agent-harness/context/CONTEXT_INDEX.json"
)["context_version"]
for row in assignment["required_inputs"]:
    assert sha(row["path"]) == row["sha256"]

binding = assignment["candidate_binding"]
assert git("rev-parse", "HEAD") == binding["candidate_sha"]
assert git("rev-parse", "HEAD^{tree}") == binding["candidate_tree_sha"]
assert git("merge-base", binding["base_sha"], binding["candidate_sha"]) == binding["merge_base_sha"]
assert git("status", "--porcelain=v2", "--untracked-files=no") == ""

commits = git("rev-list", "--reverse", f'{binding["base_sha"]}..{binding["candidate_sha"]}').splitlines()
patch_ids = []
for commit in commits:
    shown = subprocess.run(
        ["git", "show", "--pretty=format:", "--no-ext-diff", "--binary", commit],
        cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout
    patch_id = git("patch-id", "--stable", input_bytes=shown).split()[0]
    patch_ids.append(patch_id)
assert len(commits) == 13 and len(patch_ids) == len(set(patch_ids))

code = read_json(f"{ORDINARY}/results/A-PR291-R5-CODE-REPLAY.json")
phys = read_json(f"{ORDINARY}/results/A-PR291-R5-PHYSSTAT.json")
claim = read_json(f"{RUN}/results/A-PR291-R5-CLAIM.json")
assert (code["status"], code["gate_disposition"]) == ("pass", "PASS")
assert (phys["status"], phys["gate_disposition"]) == ("pass", "PASS")
assert (claim["status"], claim["gate_disposition"]) == ("fail", "FAIL")
assert claim["findings"][0]["finding_id"] == "F-PR291-R5-CLAIM-001"
assert claim["findings"][0]["severity"] == "high"
assert "eight" in claim["findings"][0]["statement"]

summary = read_json(f"{ORDINARY}/RUN_SUMMARY.json")
merged = read_json(f"{ORDINARY}/MERGED_RESULTS.json")
assert summary["assurance_budget"] == {"maximum": 16, "consumed": 14}
assert summary["assignment_count"] == 2
assert merged["process_status"] == "STRUCTURALLY_VALID"
assert merged["claim_gate_status"] == "NOT_EVALUATED"

status = yaml.safe_load((ROOT / "docs/codex_handoff/pr_status.yaml").read_text())
stack = status["stacked_pr_execution"]
pr291, pr292 = stack["prs"]["PR-291"], stack["prs"]["PR-292"]
assert stack["merge_policy"] == "HUMAN_ONLY"
assert pr291["lifecycle"] == "VALIDATED"
assert pr291["base_sha"] == pr291["predecessor_sealed_sha"] == binding["base_sha"]
assert pr291["sealed_head"] is None and pr291["pushed_ref"] is None and pr291["pr_url"] is None
assert pr291["production_hash"] == binding["production_hash"]
assert pr291["assurance_budget"] == {"maximum": 16, "consumed": 14}
assert pr291["authorized_assurance_extension_maximum"] == 2
assert pr292["lifecycle"] == "PLANNED"
assert pr292["gate_dispositions"] == {"eligibility": "INELIGIBLE"}
assert pr292["assurance_budget"] == {"maximum": 16, "consumed": 0}

# Two ordinary R5 lanes consume the remaining 2/16. Claim plus this closeout
# consume the authorized single-use 2/2 extension; the claim FAIL prevents any
# lifecycle mutation or downstream eligibility.
assert pr291["assurance_budget"]["consumed"] + 2 == 16
assert len([claim, assignment]) == pr291["authorized_assurance_extension_maximum"]

receipt = read_json("docs/research_program/post_pr275/data_runs/cf4/PR291_NONEXECUTION_RECEIPT.json")
assert receipt["terminal"] == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
assert receipt["observed_data_executed"] is False
assert receipt["numeric_outputs_written"] == []
assert receipt["network_or_download_side_effect"] is False
assert receipt["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"

print(json.dumps({
    "status": "PASS",
    "closeout_disposition": "FAIL",
    "ordinary_assurance": "16/16",
    "authorized_extension": "2/2",
    "r5_lanes": {"code_replay": "PASS", "physstat": "PASS", "claim": "FAIL"},
    "lifecycle_advance": False,
    "pr292": "PLANNED/INELIGIBLE",
    "publication": "NONE_HUMAN_ONLY",
    "stable_patch_ids": len(patch_ids),
}, sort_keys=True))
