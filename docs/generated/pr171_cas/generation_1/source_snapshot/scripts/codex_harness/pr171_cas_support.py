"""Shared fail-closed helpers for the PR-171 CAS generation."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path("docs/generated/pr171_cas/CAS_CONTRACT_PR171_CLASS_CONDITIONAL_TILT.json")
AUTH_PATH = Path("docs/generated/pr171_cas/preaxis_authorization.json")
COLLECTION_PATH = Path("docs/generated/pr171_cas_collection_receipt.json")
AXES = ("wolfram_xact", "sympy", "sage_singular", "lean")
ASSIGNMENT_IDS = {
    "wolfram_xact": "A-PR171-CAS-WOLFRAM",
    "sympy": "A-PR171-CAS-SYMPY",
    "sage_singular": "A-PR171-CAS-SAGE",
    "lean": "A-PR171-CAS-LEAN",
}
BLOCKED_STATUSES = {
    "BLOCKED_PLATFORM_OR_LICENSE",
    "BLOCKED_PACKAGE_UNAVAILABLE",
    "BLOCKED_RESOURCE_LIMIT",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def render(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def assignment_self_hash(value: dict[str, Any]) -> str:
    material = dict(value)
    material.pop("assignment_sha256", None)
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def safe_rel(value: object) -> bool:
    if not isinstance(value, str):
        return False
    path = Path(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts


def valid_hash_row(row: object) -> bool:
    return (
        isinstance(row, dict)
        and safe_rel(row.get("path"))
        and isinstance(row.get("sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) is not None
    )


def validate_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if contract.get("schema_version") != 2:
        errors.append("contract schema_version must be 2")
    if set(contract.get("axes", {})) != set(AXES):
        errors.append("contract does not contain exactly four required axes")
    if contract.get("exceptions_adjudication", {}).get("preregistered_exceptions") != []:
        errors.append("PR-171 registers no CAS exception")
    identity = contract.get("identity", {})
    for field in ("contract_id", "statement", "pr_id"):
        if not isinstance(identity.get(field), str) or not identity[field].strip():
            errors.append(f"contract identity {field} is blank")
    rows = identity.get("source_input_hashes")
    if not isinstance(rows, list) or len(rows) < 10:
        errors.append("contract source inventory is vacuous")
        rows = []
    paths: list[str] = []
    for row in rows:
        if not valid_hash_row(row):
            errors.append("malformed source-input hash row")
            continue
        paths.append(row["path"])
        target = REPO / row["path"]
        if not target.is_file() or target.is_symlink() or sha(target) != row["sha256"]:
            errors.append(f"source-input mismatch: {row['path']}")
    if len(paths) != len(set(paths)):
        errors.append("duplicate source-input path")
    for axis, details in contract.get("axes", {}).items():
        if not isinstance(details, dict):
            errors.append(f"{axis}: details not an object")
            continue
        if not str(details.get("command", "")).strip() or not str(details.get("required_tool", "")).strip():
            errors.append(f"{axis}: command/tool missing")
        sources = details.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"{axis}: source inventory empty")
            continue
        for row in sources:
            if not valid_hash_row(row):
                errors.append(f"{axis}: malformed source row")
                continue
            target = REPO / row["path"]
            if not target.is_file() or target.is_symlink() or sha(target) != row["sha256"]:
                errors.append(f"{axis}: source mismatch {row['path']}")
    obligations = contract.get("target", {}).get("exact_test_obligations")
    expected = contract.get("target", {}).get("expected_exact_values")
    if not isinstance(obligations, list) or len(obligations) != 15 or len(set(obligations)) != 15:
        errors.append("contract must carry exactly fifteen unique obligations")
    if not isinstance(expected, dict) or len(expected) != 14:
        errors.append("contract must carry exactly fourteen canonical values")
    forbidden = contract.get("target", {}).get("forbidden_shortcuts", [])
    if not any("1e-6" in str(item) for item in forbidden):
        errors.append("numerical-precommitment guard missing")
    return errors
