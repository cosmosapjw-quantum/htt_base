#!/usr/bin/env python3
"""Content-address the immutable inputs of a completed PR-171 CAS generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def build(contract_path: Path, authorization_path: Path, output_root: Path) -> tuple[dict[str, bytes], dict[str, Any]]:
    contract = _load(REPO / contract_path)
    authorization = _load(REPO / authorization_path)
    paths: set[Path] = {contract_path, authorization_path}
    for row in contract.get("identity", {}).get("source_input_hashes", []):
        paths.add(Path(row["path"]))
    for details in contract.get("axes", {}).values():
        for row in details.get("sources", []):
            paths.add(Path(row["path"]))
    for key in ("runner_path", "collector_path", "result_router_path", "support_path", "source_verifier_path"):
        if authorization.get(key):
            paths.add(Path(authorization[key]))
    run_dir = Path(authorization["run_dir"])
    for assignment_id in authorization.get("assignments", {}):
        paths.add(run_dir / "assignments" / f"{assignment_id}.json")
        result = run_dir / "results" / f"{assignment_id}.json"
        if (REPO / result).is_file():
            paths.add(result)
    files: dict[str, bytes] = {}
    rows: list[dict[str, Any]] = []
    for path in sorted(paths, key=str):
        target = REPO / path
        if not target.is_file() or target.is_symlink():
            raise ValueError(f"snapshot input absent or symlinked: {path}")
        data = target.read_bytes()
        relative = Path("source_snapshot") / path
        files[str(relative)] = data
        rows.append({"path": str(path), "snapshot_path": str(output_root / relative), "sha256": _sha(data), "bytes": len(data)})
    manifest = {
        "schema": "htt.pr171.cas_generation_snapshot.v1",
        "contract_path": str(contract_path),
        "contract_sha256": _sha((REPO / contract_path).read_bytes()),
        "authorization_path": str(authorization_path),
        "authorization_sha256": _sha((REPO / authorization_path).read_bytes()),
        "file_count": len(rows),
        "files": rows,
    }
    files["source_snapshot_manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    return files, manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, manifest = build(args.contract, args.authorization, args.output_root)
    mismatches: list[str] = []
    for relative, data in files.items():
        path = REPO / args.output_root / relative
        if args.write:
            _write(path, data)
        if args.check and (not path.is_file() or path.read_bytes() != data):
            mismatches.append(str(path.relative_to(REPO)))
    print(json.dumps({"ok": not mismatches, "manifest": manifest, "mismatches": mismatches}, indent=2, sort_keys=True))
    return 0 if not mismatches else 2


if __name__ == "__main__":
    raise SystemExit(main())
