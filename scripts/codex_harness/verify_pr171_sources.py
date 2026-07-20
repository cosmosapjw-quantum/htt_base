#!/usr/bin/env python3
"""Verify PR-171 raw primary-source archives and normalized records."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml


REPO = Path(__file__).resolve().parents[2]
PROVENANCE = Path("docs/research_program/long_horizon_rescue/pr171_primary_source_provenance.yaml")
OUTPUT = Path("docs/generated/pr171_source_verification.json")
REQUIRED_IDS = {
    "CEMBRANOS_2019_NONCOMOVING",
    "COLEY_HERVIK_LIM_2006_REVIEW",
    "HERVIK_LIM_2006_VIII",
    "BELTRAN_JIMENEZ_2021_VELOCITY_INTERACTION",
    "BLANCHET_SKORDIS_2024_KHRONON",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(*, require_raw: bool = True) -> dict[str, Any]:
    provenance = yaml.safe_load((REPO / PROVENANCE).read_text(encoding="utf-8"))
    rows = provenance.get("sources", []) if isinstance(provenance, dict) else []
    errors: list[str] = []
    verified: list[dict[str, Any]] = []
    ids = [row.get("source_id") for row in rows if isinstance(row, dict)]
    if set(ids) != REQUIRED_IDS or len(ids) != len(set(ids)):
        errors.append("source inventory is not the exact five-source registry")
    for row in rows:
        if not isinstance(row, dict):
            errors.append("source row is not a mapping")
            continue
        raw = REPO / str(row.get("raw_archive", ""))
        record = REPO / str(row.get("record", ""))
        row_errors: list[str] = []
        if require_raw and (
            not raw.is_file()
            or raw.is_symlink()
            or _sha(raw) != row.get("raw_sha256")
            or raw.stat().st_size != row.get("raw_bytes")
        ):
            row_errors.append("raw archive absent or hash/size mismatch")
        if (
            not record.is_file()
            or record.is_symlink()
            or _sha(record) != row.get("record_sha256")
        ):
            row_errors.append("normalized record absent or hash mismatch")
        if not str(row.get("url", "")).startswith("https://arxiv.org/abs/"):
            row_errors.append("source URL is not an arXiv abstract locator")
        errors.extend(f"{row.get('source_id')}: {item}" for item in row_errors)
        verified.append(
            {
                "source_id": row.get("source_id"),
                "raw_path": row.get("raw_archive"),
                "raw_sha256": row.get("raw_sha256"),
                "raw_bytes": row.get("raw_bytes"),
                "record_path": row.get("record"),
                "record_sha256": row.get("record_sha256"),
                "ok": not row_errors,
            }
        )
    return {
        "schema": "htt.pr171.source_verification.v1",
        "provenance_path": str(PROVENANCE),
        "provenance_sha256": _sha(REPO / PROVENANCE),
        "require_raw": require_raw,
        "source_count": len(rows),
        "verified_sources": verified,
        "errors": errors,
        "ok": not errors,
        "scope": "source-byte and normalized-record authentication; not validation of a universal no-go",
    }


def _render(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--records-only", action="store_true")
    args = parser.parse_args()
    payload = verify(require_raw=not args.records_only)
    rendered = _render(payload)
    if args.write:
        _write(REPO / OUTPUT, rendered)
    if args.check:
        if not (REPO / OUTPUT).is_file() or (REPO / OUTPUT).read_bytes() != rendered:
            payload["errors"] = [*payload["errors"], "stored verification receipt differs"]
            payload["ok"] = False
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
