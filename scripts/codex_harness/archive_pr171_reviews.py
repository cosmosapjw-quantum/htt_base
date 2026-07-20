#!/usr/bin/env python3
"""Archive PR-171 review envelopes from ignored run state into tracked evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path("docs/generated/pr171_reviews")
SOURCES = {
    "claim_gate": Path(".agent-harness/runs/pr171-intake-20260719/results/A-PR171-CLAIM.json"),
    "harness": Path(".agent-harness/runs/pr171-intake-20260719/results/A-PR171-HARNESS.json"),
    "physics_statistics": Path(".agent-harness/runs/pr171-intake-20260719/results/A-PR171-PHYSICS.json"),
    "adjudicator": Path(".agent-harness/runs/pr171-cas-g3-20260720/results/A-PR171-ADJUDICATOR.json"),
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def build() -> tuple[dict[str, bytes], dict[str, object]]:
    outputs: dict[str, bytes] = {}
    rows: list[dict[str, object]] = []
    for role, source in SOURCES.items():
        source_path = REPO / source
        data = source_path.read_bytes()
        # Parsing is part of the archive gate; bytes are otherwise preserved exactly.
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
        "schema": "htt.pr171.review_archive.v1",
        "pr_id": "PR-171",
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "scientific_artifact_mode": "hypothesis_only",
        "transfer_source": "none",
        "config_hash": _sha(
            (REPO / "docs/research_program/long_horizon_rescue/pr171_spec.yaml").read_bytes()
        ),
        "input_hashes": {row["source_path"]: row["sha256"] for row in rows},
        "sky_support_status": "not_applicable_review_evidence",
        "mask_status": "not_applicable_review_evidence",
        "covariance_status": "not_applicable_review_evidence",
        "null_mock_status": "not_applicable_review_evidence",
        "copy_mode": "byte_for_byte",
        "review_count": len(rows),
        "reviews": rows,
        "generating_command": "venv/bin/python -B scripts/codex_harness/archive_pr171_reviews.py --write",
        "git_commit": "c936fabd1527bb8c38cb13b98fc1ee608d0c5738",
        "worktree_state": "c936fabd1527bb8c38cb13b98fc1ee608d0c5738+PR-171-worktree",
        "public_use": False,
        "caveats": [
            "Archived verdicts retain their original status; copying does not relabel them as passes.",
            "Tracked destination hashes are sufficient for clean-checkout replay; ignored source paths are checked additionally when present.",
        ],
    }
    outputs[str(OUTPUT_DIR / "manifest.json")] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    return outputs, manifest


def check_archive() -> list[str]:
    manifest_path = REPO / OUTPUT_DIR / "manifest.json"
    if not manifest_path.is_file():
        return [str(manifest_path.relative_to(REPO))]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest.get("reviews", [])
    errors: list[str] = []
    if manifest.get("copy_mode") != "byte_for_byte" or manifest.get("review_count") != len(SOURCES):
        errors.append("manifest inventory mismatch")
    if {row.get("role") for row in rows} != set(SOURCES):
        errors.append("manifest role inventory mismatch")
    for row in rows:
        role = row.get("role")
        if role not in SOURCES:
            continue
        destination = REPO / OUTPUT_DIR / f"{role}.json"
        if row.get("destination_path") != str(destination.relative_to(REPO)) or not destination.is_file():
            errors.append(f"{role}: tracked destination missing or misrouted")
            continue
        data = destination.read_bytes()
        try:
            envelope = json.loads(data)
        except json.JSONDecodeError:
            errors.append(f"{role}: tracked destination is not JSON")
            continue
        if _sha(data) != row.get("sha256") or len(data) != row.get("bytes"):
            errors.append(f"{role}: tracked destination hash/size mismatch")
        if envelope.get("assignment_id") != row.get("assignment_id") or envelope.get("status") != row.get("status"):
            errors.append(f"{role}: tracked envelope metadata mismatch")
        source = REPO / SOURCES[role]
        if source.is_file() and source.read_bytes() != data:
            errors.append(f"{role}: live ignored source differs from tracked copy")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs: dict[str, bytes] = {}
    manifest: dict[str, object] = {}
    if args.write or not args.check:
        outputs, manifest = build()
    mismatches: list[str] = []
    if args.write:
        for relative, data in outputs.items():
            path = REPO / relative
            _write(path, data)
    if args.check:
        mismatches.extend(check_archive())
    print(
        json.dumps(
            {
                "ok": not mismatches,
                "review_count": manifest.get("review_count", len(SOURCES)),
                "mismatches": mismatches,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not mismatches else 2


if __name__ == "__main__":
    raise SystemExit(main())
