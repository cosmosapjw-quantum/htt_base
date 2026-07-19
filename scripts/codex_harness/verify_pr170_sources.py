#!/usr/bin/env python3
"""Verify PR-170's content-addressed arXiv source and equation records."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


REPO = Path(__file__).resolve().parents[2]
PROVENANCE = Path(
    "docs/research_program/long_horizon_rescue/pr170_primary_source_provenance.yaml"
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(*, require_raw: bool = True) -> dict[str, Any]:
    document = yaml.safe_load((REPO / PROVENANCE).read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for source in document["sources"]:
        source_id = str(source["source_id"])
        record_path = REPO / str(source["equation_record"])
        raw_path = REPO / str(source["raw_path"])
        record_ok = record_path.is_file() and _sha(record_path) == source["equation_record_sha256"]
        raw_present = raw_path.is_file()
        raw_ok = (
            raw_present
            and raw_path.stat().st_size == int(source["byte_count"])
            and _sha(raw_path) == source["raw_sha256"]
        )
        if not record_ok:
            errors.append(f"{source_id}: equation record hash mismatch")
        if require_raw and not raw_ok:
            errors.append(f"{source_id}: raw source archive missing or mismatched")
        rows.append(
            {
                "source_id": source_id,
                "equation_record_ok": record_ok,
                "raw_present": raw_present,
                "raw_ok": raw_ok,
                "raw_sha256": source["raw_sha256"],
                "retrieval_url": source["retrieval_url"],
            }
        )
    return {
        "schema": "htt.pr170.source_verification.v1",
        "provenance_path": str(PROVENANCE),
        "require_raw": require_raw,
        "sources": rows,
        "errors": errors,
        "ok": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--allow-raw-absent", action="store_true")
    args = parser.parse_args()
    payload = verify(require_raw=not args.allow_raw_absent)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
