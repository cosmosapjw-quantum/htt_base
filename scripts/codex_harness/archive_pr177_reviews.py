#!/usr/bin/env python3
"""Archive PR-177 independent reviews byte-for-byte into tracked evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SPEC = Path("docs/research_program/long_horizon_rescue/pr177_spec.yaml")
OUTPUT_DIR = Path("docs/generated/pr177_reviews")
SOURCES = {
    "intake_claim": Path(
        ".agent-harness/runs/pr177-intake-20260720/results/A-PR177-CLAIM.json"
    ),
    "intake_harness": Path(
        ".agent-harness/runs/pr177-intake-20260720/results/A-PR177-HARNESS.json"
    ),
    "intake_statistics": Path(
        ".agent-harness/runs/pr177-intake-20260720/results/A-PR177-STAT.json"
    ),
    "final_code": Path(
        ".agent-harness/runs/pr177-intake-20260720/results/A-PR177-FINAL-CODE.json"
    ),
    "final_science": Path(
        ".agent-harness/runs/pr177-intake-20260720/results/A-PR177-FINAL-SCIENCE.json"
    ),
    "final_claim": Path(
        ".agent-harness/runs/pr177-intake-20260720/results/A-PR177-FINAL-CLAIM.json"
    ),
    "first_remediation_code_fail": Path(
        ".agent-harness/runs/pr177-intake-20260720/results/A-PR177-REMED-CODE.json"
    ),
    "first_remediation_claim_pass": Path(
        ".agent-harness/runs/pr177-intake-20260720/results/A-PR177-REMED-CLAIM.json"
    ),
    "second_final_code_fail": Path(
        ".agent-harness/runs/pr177-final-remediation2-20260720/results/A-PR177-FINAL2-CODE.json"
    ),
    "second_final_claim_fail": Path(
        ".agent-harness/runs/pr177-final-remediation2-20260720/results/A-PR177-FINAL2-CLAIM.json"
    ),
    "final_code_pass": Path(
        ".agent-harness/runs/pr177-final-remediation2-20260720/results/A-PR177-FINAL3-CODE.json"
    ),
    "final_claim_pass": Path(
        ".agent-harness/runs/pr177-final-remediation2-20260720/results/A-PR177-FINAL3-CLAIM.json"
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
    manifest = {
        "schema": "htt.pr177.review_archive.v1",
        "pr_id": "PR-177",
        "claim_id": "C-PR177-INBAND-MODULATION",
        "owner": "OBSSTAT",
        "contributors": [],
        "implementation_scope": "obsstat",
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C3"},
        "scientific_artifact_mode": "standard_internal",
        "scientific_status": "CLOSED",
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
        "review_statuses": {row["role"]: row["status"] for row in rows},
        "reviews": rows,
        "generating_command": (
            "venv/bin/python -B scripts/codex_harness/archive_pr177_reviews.py --write"
        ),
        "git_commit": "76675be04bafdd79b3487e9be81a03557de42ea5",
        "worktree_state": "76675be04bafdd79b3487e9be81a03557de42ea5+PR-177-worktree",
        "caveats": [
            "The intake claim FAIL is preserved and supplied the exact-support and product-scope preregistration requirements.",
            "The first final code FAIL is preserved; it exposed cache-identity, resource-receipt, and runtime-provenance false-green paths.",
            "The first final claim FAIL is preserved; it exposed omitted strict support on result-bearing artifacts.",
            "The final science PASS applies only to the ACT release-simulation-conditional estimand and does not validate a physical interpretation.",
            "The first remediation code FAIL is preserved; it exposed mutable PR-152 authority reconstruction, incomplete replay-status checks, and an incomplete recorded command.",
            "The second code and claim FAILs are preserved; they exposed contradictory resealed PR-152 entries in feature/deep input-hash metadata and stale delta counts.",
            "The final independent code and claim reviews pass only after exact complete authority-map reconstruction kills those residual consistency cases.",
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
    if (
        manifest.get("copy_mode") != "byte_for_byte"
        or manifest.get("review_count") != len(SOURCES)
    ):
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
