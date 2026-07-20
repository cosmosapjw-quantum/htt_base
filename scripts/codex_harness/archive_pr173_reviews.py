#!/usr/bin/env python3
"""Archive PR-173 independent reviews byte-for-byte into tracked evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SPEC = Path("docs/research_program/long_horizon_rescue/pr173_spec.yaml")
OUTPUT_DIR = Path("docs/generated/pr173_reviews")
SOURCES = {
    "intake_claim": Path(
        ".agent-harness/runs/pr173-intake-20260720/results/A-PR173-CLAIM.json"
    ),
    "intake_harness": Path(
        ".agent-harness/runs/pr173-intake-20260720/results/A-PR173-HARNESS.json"
    ),
    "intake_statistics": Path(
        ".agent-harness/runs/pr173-intake-20260720/results/A-PR173-STAT.json"
    ),
    "stale_final_code": Path(
        ".agent-harness/runs/pr173-final-review-20260720/results/A-PR173-FINAL-CODE.json"
    ),
    "stale_final_statistics": Path(
        ".agent-harness/runs/pr173-final-review-20260720/results/A-PR173-FINAL-STAT.json"
    ),
    "stale_final_claim": Path(
        ".agent-harness/runs/pr173-final-review-20260720/results/A-PR173-FINAL-CLAIM.json"
    ),
    "final_code": Path(
        ".agent-harness/runs/pr173-final-review-20260720/results/A-PR173-FINAL2-CODE.json"
    ),
    "final_statistics": Path(
        ".agent-harness/runs/pr173-final-review-20260720/results/A-PR173-FINAL2-STAT.json"
    ),
    "final_claim": Path(
        ".agent-harness/runs/pr173-final-review-20260720/results/A-PR173-FINAL2-CLAIM.json"
    ),
    "remediation_code": Path(
        ".agent-harness/runs/pr173-final-review-20260720/results/A-PR173-REMED-CODE.json"
    ),
    "remediation_claim": Path(
        ".agent-harness/runs/pr173-final-review-20260720/results/A-PR173-REMED-CLAIM.json"
    ),
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
    rows: list[dict[str, object]] = []
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
    statuses = {row["role"]: row["status"] for row in rows}
    manifest = {
        "schema": "htt.pr173.review_archive.v1",
        "pr_id": "PR-173",
        "claim_id": "C-PR173-MC-CERTIFIER",
        "owner": "OBSSTAT",
        "contributors": ["COMMON"],
        "implementation_scope": "obsstat",
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
        "review_statuses": statuses,
        "reviews": rows,
        "generating_command": (
            "venv/bin/python -B scripts/codex_harness/archive_pr173_reviews.py --write"
        ),
        "git_commit": "9ce5c878ef785def0a684f9addcc764b5cedd3e2",
        "worktree_state": "9ce5c878ef785def0a684f9addcc764b5cedd3e2+PR-173-worktree",
        "caveats": [
            "The intake claim FAIL is preserved and supplied the orthogonal availability, lineage, and numerical-state remediation.",
            "Three first final-review attempts are preserved as ERROR because a required input changed after assignment registration; they issued no substantive verdict.",
            "The fresh final code FAIL is preserved; it exposed coordinated uncertainty and provenance false-green paths.",
            "Fresh code and claim remediation reviews pass after authoritative frozen-source reconstruction kills all six reported survivors.",
            "No archived verdict is relabeled by the main writer.",
            "Copying a review does not create independent scientific evidence.",
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
        if envelope.get("assignment_id") != row.get("assignment_id"):
            errors.append(f"{role}: assignment metadata mismatch")
        if envelope.get("status") != row.get("status"):
            errors.append(f"{role}: status metadata mismatch")
        source = REPO / SOURCES[role]
        if source.is_file() and source.read_bytes() != data:
            errors.append(f"{role}: live source differs from tracked review")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write:
        for relative, data in build().items():
            _write(REPO / relative, data)
    errors = check_archive()
    print(
        json.dumps(
            {"ok": not errors, "review_count": len(SOURCES), "errors": errors},
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
