#!/usr/bin/env python3
"""Archive PR-172 intake reviews from ignored run state into tracked evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SPEC = Path("docs/research_program/long_horizon_rescue/pr172_spec.yaml")
OUTPUT_DIR = Path("docs/generated/pr172_reviews")
SOURCES = {
    "claim_gate": Path(".agent-harness/runs/pr172-intake-20260720/results/A-PR172-CLAIM.json"),
    "harness": Path(".agent-harness/runs/pr172-intake-20260720/results/A-PR172-HARNESS.json"),
    "physics_statistics": Path(".agent-harness/runs/pr172-intake-20260720/results/A-PR172-PHYSSTAT.json"),
    "final_code": Path(".agent-harness/runs/pr172-final-review-20260720/results/A-PR172-FINAL-CODE.json"),
    "final_science": Path(".agent-harness/runs/pr172-final-review-20260720/results/A-PR172-FINAL-SCIENCE.json"),
    "final_claim": Path(".agent-harness/runs/pr172-final-review-20260720/results/A-PR172-FINAL-CLAIM.json"),
    "remediation_code": Path(".agent-harness/runs/pr172-remediation-review2-20260720/results/A-PR172-REMED2-CODE3.json"),
    "remediation_claim": Path(".agent-harness/runs/pr172-remediation-review2-20260720/results/A-PR172-REMED2-CLAIM.json"),
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def build() -> dict[str, bytes]:
    outputs: dict[str, bytes] = {}
    rows = []
    for role, source in SOURCES.items():
        data = (REPO / source).read_bytes()
        envelope = json.loads(data)
        destination = OUTPUT_DIR / f"{role}.json"
        outputs[str(destination)] = data
        rows.append(
            {
                "role": role,
                "source_path": str(source),
                "destination_path": str(destination),
                "sha256": _sha(data),
                "bytes": len(data),
                "assignment_id": envelope.get("assignment_id"),
                "status": envelope.get("status"),
            }
        )
    manifest = {
        "schema": "htt.pr172.review_archive.v1",
        "pr_id": "PR-172",
        "claim_id": "C-PR172-METAMORPHIC-CONSISTENCY",
        "owner": "COMMON",
        "contributors": ["OBSSTAT"],
        "implementation_scope": "common",
        "claim_tier": "exploratory",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
        "scientific_artifact_mode": "standard_internal",
        "scientific_status": "OPEN",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": _sha((REPO / SPEC).read_bytes()),
        "input_hashes": {row["source_path"]: row["sha256"] for row in rows},
        "sky_support_status": "not_applicable_review_evidence",
        "mask_status": "not_applicable_review_evidence",
        "covariance_status": "not_applicable_review_evidence",
        "null_mock_status": "not_applicable_review_evidence",
        "copy_mode": "byte_for_byte",
        "review_count": len(rows),
        "reviews": rows,
        "generating_command": "venv/bin/python -B scripts/codex_harness/archive_pr172_reviews.py --write",
        "git_commit": "b8a857742bd6c2d727ea2009f6e8a341a031b120",
        "worktree_state": "b8a857742bd6c2d727ea2009f6e8a341a031b120+PR-172-worktree",
        "caveats": [
            "The physics/statistics FAIL verdict is preserved and supplies the formal B-projector falsifier.",
            "The first final code and claim FAIL verdicts are preserved; their concrete false-green and provenance findings require a separate remediation replay.",
            "Fresh remediation code and claim PASS envelopes close those concrete findings without relabeling earlier reviews or changing the blocked scientific terminal.",
            "Copying an envelope does not relabel its status or create independent scientific evidence.",
        ],
    }
    outputs[str(OUTPUT_DIR / "manifest.json")] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return outputs


def check_archive() -> list[str]:
    manifest_path = REPO / OUTPUT_DIR / "manifest.json"
    if not manifest_path.is_file():
        return [str(manifest_path.relative_to(REPO))]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    rows = manifest.get("reviews", [])
    if manifest.get("copy_mode") != "byte_for_byte" or manifest.get("review_count") != len(SOURCES):
        errors.append("manifest inventory mismatch")
    if {row.get("role") for row in rows} != set(SOURCES):
        errors.append("manifest role inventory mismatch")
    for row in rows:
        role = row.get("role")
        if role not in SOURCES:
            continue
        destination = REPO / OUTPUT_DIR / f"{role}.json"
        if not destination.is_file():
            errors.append(f"{role}: tracked review missing")
            continue
        data = destination.read_bytes()
        if _sha(data) != row.get("sha256") or len(data) != row.get("bytes"):
            errors.append(f"{role}: tracked review hash/size mismatch")
        envelope = json.loads(data)
        if envelope.get("assignment_id") != row.get("assignment_id") or envelope.get("status") != row.get("status"):
            errors.append(f"{role}: envelope metadata mismatch")
        source = REPO / SOURCES[role]
        if source.is_file() and source.read_bytes() != data:
            errors.append(f"{role}: live source differs from tracked review")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build() if args.write or not args.check else {}
    if args.write:
        for relative, data in outputs.items():
            _write(REPO / relative, data)
    errors = check_archive() if args.check else []
    print(json.dumps({"ok": not errors, "review_count": len(SOURCES), "errors": errors}, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
