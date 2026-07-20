#!/usr/bin/env python3
"""Archive PR-182 independent reviews byte-for-byte into tracked evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path("docs/generated/pr182_reviews")
SOURCES = {
    "review_physics": Path(
        ".agent-harness/runs/pr182-final-review-20260720/results/A-PR182-REVIEW-PHYS.json"
    ),
    "review_code": Path(
        ".agent-harness/runs/pr182-final-review-20260720/results/A-PR182-REVIEW-CODE.json"
    ),
    "review_claim": Path(
        ".agent-harness/runs/pr182-final-review-20260720/results/A-PR182-REVIEW-CLAIM.json"
    ),
    "finding_verdicts": Path(
        ".agent-harness/runs/pr182-final-review-20260720/results/A-PR182-VERDICTS.json"
    ),
    "final_adjudication": Path(
        ".agent-harness/runs/pr182-final-review-20260720/results/A-PR182-FINAL-ADJ.json"
    ),
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build() -> dict[Path, bytes]:
    out: dict[Path, bytes] = {}
    manifest_rows = {}
    for key, source in sorted(SOURCES.items()):
        data = (REPO / source).read_bytes()
        target = OUTPUT_DIR / f"{key}.json"
        out[target] = data
        manifest_rows[key] = {
            "source": source.as_posix(),
            "archived": target.as_posix(),
            "sha256": _sha(data),
        }
    manifest = {
        "schema": "htt.pr182.review_archive_manifest.v1",
        "pr_id": "PR-182",
        "rows": manifest_rows,
    }
    out[OUTPUT_DIR / "manifest.json"] = (
        json.dumps(manifest, sort_keys=True, indent=1) + "\n"
    ).encode()
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payloads = build()
    if args.write:
        for path, data in payloads.items():
            full = REPO / path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_bytes(data)
            print(f"wrote {path}")
        return 0
    failures = []
    for path, data in payloads.items():
        full = REPO / path
        if not full.exists() or full.read_bytes() != data:
            failures.append(str(path))
    if failures:
        print("archive differs:", failures)
        return 1
    print(json.dumps({"mode": "check", "ok": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
