#!/usr/bin/env python3
"""Verify R4A1V0 source identities before parent-owned CAS execution.

The contract remains the semantic authority.  This verifier checks that the
working-tree files named by that contract are the exact registered bytes before
``cas_gate.py run-adjudicate`` is allowed to launch either required axis.
It uses only the Python standard library and emits one JSON receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / ".agent-harness" / "scripts" / "cas_gate.py").is_file():
            return parent
    raise RuntimeError("could not locate repository root")


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_repo_file(root: Path, raw_path: object, label: str) -> tuple[Path | None, str | None]:
    if not isinstance(raw_path, str) or not raw_path:
        return None, f"{label}: path must be a non-empty string"
    relative = Path(raw_path)
    if relative.is_absolute():
        return None, f"{label}: path must be repository-relative"

    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return None, f"{label}: symlinked path component is forbidden: {raw_path}"

    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None, f"{label}: path escapes the repository: {raw_path}"
    if not resolved.is_file():
        return None, f"{label}: file does not exist: {raw_path}"
    return resolved, None


def _verify_row(root: Path, row: object, label: str) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(row, dict):
        return None, f"{label}: hash row must be an object"
    path, path_error = _safe_repo_file(root, row.get("path"), label)
    if path_error:
        return None, path_error
    assert path is not None

    algorithm = row.get("hash_algorithm")
    expected = row.get("digest")
    if algorithm not in {"git_blob_sha1", "sha256"}:
        return None, f"{label}: unsupported hash_algorithm {algorithm!r}"
    if not isinstance(expected, str) or not expected:
        return None, f"{label}: digest must be a non-empty string"

    data = path.read_bytes()
    actual = _git_blob_sha1(data) if algorithm == "git_blob_sha1" else _sha256(data)
    receipt = {
        "label": label,
        "path": path.relative_to(root).as_posix(),
        "hash_algorithm": algorithm,
        "expected": expected,
        "actual": actual,
        "bytes": len(data),
        "matched": actual == expected,
    }
    if actual != expected:
        return receipt, f"{label}: digest mismatch for {receipt['path']}"
    return receipt, None


def _single_identity_row(
    contract: dict[str, Any],
    key: str,
    expected_path: str,
) -> tuple[object, str | None]:
    identity = contract.get("identity")
    if not isinstance(identity, dict):
        return None, "contract.identity must be an object"
    row = identity.get(key)
    if not isinstance(row, dict):
        return row, f"contract.identity.{key} must be a hash row"
    if row.get("path") != expected_path:
        return row, (
            f"contract.identity.{key}.path must equal the invoked path "
            f"{expected_path!r}"
        )
    return row, None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--run-spec", required=True)
    parser.add_argument("--adjudicator", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    root = _repo_root()
    contract_rel = Path(args.contract).as_posix()
    run_spec_rel = Path(args.run_spec).as_posix()
    adjudicator_rel = Path(args.adjudicator).as_posix()
    out_path = root / args.out

    errors: list[str] = []
    verified: list[dict[str, Any]] = []

    contract_path, contract_path_error = _safe_repo_file(root, contract_rel, "contract")
    if contract_path_error:
        errors.append(contract_path_error)
        contract: dict[str, Any] = {}
        contract_sha256 = None
    else:
        assert contract_path is not None
        contract = _load_json(contract_path)
        contract_sha256 = _sha256(contract_path.read_bytes())

    rows: list[tuple[str, object]] = []
    identity = contract.get("identity") if isinstance(contract, dict) else None
    if not isinstance(identity, dict):
        errors.append("contract.identity must be an object")
    else:
        source_rows = identity.get("source_input_hashes")
        if not isinstance(source_rows, list) or not source_rows:
            errors.append("contract.identity.source_input_hashes must be a non-empty array")
        else:
            rows.extend(
                (f"identity.source_input_hashes[{index}]", row)
                for index, row in enumerate(source_rows)
            )

        for key, expected_path in (
            ("run_spec_hash", run_spec_rel),
            ("adjudicator_hash", adjudicator_rel),
            ("binding_validator_hash", Path(__file__).resolve().relative_to(root).as_posix()),
        ):
            row, error = _single_identity_row(contract, key, expected_path)
            if error:
                errors.append(error)
            else:
                rows.append((f"identity.{key}", row))

        support_rows = identity.get("adjudicator_support_hashes", [])
        if not isinstance(support_rows, list):
            errors.append("contract.identity.adjudicator_support_hashes must be an array")
        else:
            rows.extend(
                (f"identity.adjudicator_support_hashes[{index}]", row)
                for index, row in enumerate(support_rows)
            )

    axes = contract.get("axes") if isinstance(contract, dict) else None
    if not isinstance(axes, dict):
        errors.append("contract.axes must be an object")
    else:
        required_axes = contract.get("required_axes")
        if not isinstance(required_axes, list):
            errors.append("contract.required_axes must be an array")
            required_axes = []
        for axis in required_axes:
            details = axes.get(axis)
            if not isinstance(details, dict):
                errors.append(f"contract.axes.{axis} must be an object")
                continue
            source_hashes = details.get("source_hashes")
            if not isinstance(source_hashes, list) or not source_hashes:
                errors.append(f"contract.axes.{axis}.source_hashes must be a non-empty array")
                continue
            rows.extend(
                (f"axes.{axis}.source_hashes[{index}]", row)
                for index, row in enumerate(source_hashes)
            )

    seen_paths: set[str] = set()
    for label, row in rows:
        receipt, error = _verify_row(root, row, label)
        if receipt is not None:
            path_label = str(receipt["path"])
            if path_label in seen_paths:
                errors.append(f"{label}: duplicate registered path {path_label}")
            seen_paths.add(path_label)
            verified.append(receipt)
        if error:
            errors.append(error)

    receipt = {
        "schema_version": 1,
        "contract": contract_rel,
        "contract_sha256": contract_sha256,
        "run_spec": run_spec_rel,
        "adjudicator": adjudicator_rel,
        "verified_at": _utc_now(),
        "verified_rows": verified,
        "verified_row_count": len(verified),
        "ok": not errors,
        "errors": errors,
        "claim_scope": "supporting-domain source identity only",
        "observational_data_used": False,
        "finite_healpix_containment": "RANK_UNRESOLVED",
        "merge_or_publication_authority": False,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if receipt["ok"] else 2)


if __name__ == "__main__":
    main()
