#!/usr/bin/env python3
"""Archive PR-176 independent reviews byte-for-byte into tracked evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SPEC = Path("docs/research_program/long_horizon_rescue/pr176_spec.yaml")
ERRATUM = Path("docs/research_program/long_horizon_rescue/pr176_spec_erratum.yaml")
OUTPUT_DIR = Path("docs/generated/pr176_reviews")
SOURCES = {
    "intake_mapper": Path(
        ".agent-harness/runs/pr176-intake-20260720/results/A-PR176-MAP.json"
    ),
    "intake_harness": Path(
        ".agent-harness/runs/pr176-intake-20260720/results/A-PR176-HARNESS.json"
    ),
    "intake_statistics": Path(
        ".agent-harness/runs/pr176-intake-20260720/results/A-PR176-STAT.json"
    ),
    "intake_claim": Path(
        ".agent-harness/runs/pr176-intake-20260720/results/A-PR176-CLAIM2.json"
    ),
    "first_final_code_fail": Path(
        ".agent-harness/runs/pr176-final-review-20260720/results/A-PR176-FINAL-CODE.json"
    ),
    "first_final_statistics_fail": Path(
        ".agent-harness/runs/pr176-final-review-20260720/results/A-PR176-FINAL-STAT.json"
    ),
    "first_final_claim_fail": Path(
        ".agent-harness/runs/pr176-final-review-20260720/results/A-PR176-FINAL-CLAIM.json"
    ),
    "remediation_code_pass": Path(
        ".agent-harness/runs/pr176-final-review-20260720/results/A-PR176-REVIEW2-CODE.json"
    ),
    "remediation_statistics_pass": Path(
        ".agent-harness/runs/pr176-final-review-20260720/results/A-PR176-REVIEW2-STAT.json"
    ),
    "remediation_claim_pass": Path(
        ".agent-harness/runs/pr176-final-review-20260720/results/A-PR176-REVIEW2-CLAIM.json"
    ),
    "final_adjudication": Path(
        ".agent-harness/runs/pr176-final-review-20260720/results/A-PR176-FINAL-ADJ.json"
    ),
    "superseded_adjudication_error": Path(
        ".agent-harness/runs/pr176-final-review-20260720/results/A-PR176-FINAL-ADJ2.json"
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
                "verdict": envelope.get("verdict"),
            }
        )
    config_hash = _sha((REPO / SPEC).read_bytes() + (REPO / ERRATUM).read_bytes())
    manifest = {
        "schema": "htt.pr176.review_archive.v1",
        "pr_id": "PR-176",
        "claim_id": "C-PR176-AFFINE-DIVERGENCE-Q",
        "owner": "OBSSTAT",
        "contributors": ["BASS", "HTT"],
        "implementation_scope": "obsstat",
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C3"},
        "scientific_artifact_mode": "standard_internal",
        "scientific_status": "NON_INFORMATIVE_Q_RESPONSE_UNAVAILABLE",
        "validation_axis": "FROZEN_COVARIANCE_SELF_CONSISTENCY_GATE_FAILED",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": config_hash,
        "input_hashes": {row["source_path"]: row["sha256"] for row in rows},
        "sky_support_status": "not_applicable_review_evidence",
        "mask_status": "not_applicable_review_evidence",
        "covariance_status": "not_applicable_review_evidence",
        "null_mock_status": "not_applicable_review_evidence",
        "copy_mode": "byte_for_byte",
        "review_count": len(rows),
        "review_statuses": {row["role"]: row["status"] for row in rows},
        "reviews": rows,
        "authorized_generation_root": (
            "b917b933229c8786550c69d1466f8d57ccf87990c4fcf243740374efe3c9860d"
        ),
        "generating_command": (
            "venv/bin/python -B scripts/codex_harness/archive_pr176_reviews.py --write"
        ),
        "git_commit": "06083de0b575e19aada5d56ef10fb043f654faf2",
        "worktree_state": "06083de0b575e19aada5d56ef10fb043f654faf2+PR-176-worktree",
        "caveats": [
            "The three first final-review FAIL envelopes are preserved without relabeling.",
            "The three remediation reviews close the concrete code, statistics, and claim findings only for the pinned candidate bytes.",
            "The final adjudication authorizes only the exact recorded generation root and internal C3 conditional claim ceiling.",
            "A replacement adjudication was registered while the first envelope was delayed; it was stopped without verdict and its ERROR envelope is preserved as superseded, not counted as authorization.",
            "The affine coefficients remain candidate diagnostics, not an accepted covariance-validated measurement.",
            "The q-response non-identification terminal is separate from the failed frozen covariance self-consistency validation axis.",
            "No q estimate, significance, acceleration, anisotropy, geometry, family, transfer-validation, or public-use claim is authorized.",
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
