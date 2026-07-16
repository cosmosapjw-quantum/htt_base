from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
RESULT_STATUSES = {"pass", "fail", "inconclusive", "error"}


def root() -> Path:
    try:
        text = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if text:
            return Path(text).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    here = Path(__file__).resolve()
    return here.parents[2]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def hash_files(repo: Path, files: list[str]) -> tuple[str, list[tuple[str, str]]]:
    digest = hashlib.sha256()
    entries: list[tuple[str, str]] = []
    for rel in files:
        path = repo / rel
        data = path.read_bytes()
        file_hash = hashlib.sha256(data).hexdigest()
        entries.append((rel, file_hash))
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(data)
        digest.update(b"\0")
    return digest.hexdigest(), entries


def active_run_id(repo: Path) -> str:
    path = repo / ".agent-harness" / "ACTIVE_RUN"
    if not path.exists():
        raise SystemExit("No active run. Use init_run.py first.")
    run_id = path.read_text(encoding="utf-8").strip()
    if not run_id:
        raise SystemExit("ACTIVE_RUN is empty.")
    if not is_safe_identifier(run_id):
        raise SystemExit(f"ACTIVE_RUN contains an unsafe run identifier: {run_id!r}")
    return run_id


def is_safe_identifier(value: object) -> bool:
    return isinstance(value, str) and SAFE_IDENTIFIER_RE.fullmatch(value) is not None


def declared_result_path(run_id: str, assignment_id: str) -> str:
    return f".agent-harness/runs/{run_id}/results/{assignment_id}.json"


def validate_assignment_payload(
    assignment: object,
    *,
    run_id: str,
    context_version: str,
    assignment_id: str | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(assignment, Mapping):
        return ["assignment is not a JSON object"]
    actual_id = assignment.get("assignment_id")
    if assignment.get("schema_version") != 1:
        errors.append("assignment schema_version must equal 1")
    if assignment.get("run_id") != run_id:
        errors.append("assignment run_id does not match ACTIVE_RUN")
    if not is_safe_identifier(actual_id):
        errors.append("assignment_id is missing or unsafe")
    if assignment_id is not None and actual_id != assignment_id:
        errors.append("assignment_id does not match the registered filename")
    if assignment.get("context_version") != context_version:
        errors.append("assignment context_version is stale")
    if not isinstance(assignment.get("agent_type"), str) or not assignment.get(
        "agent_type"
    ):
        errors.append("assignment agent_type must be non-empty")
    claim_ids = assignment.get("claim_ids")
    if not isinstance(claim_ids, list) or any(
        not isinstance(item, str) or not item for item in claim_ids
    ):
        errors.append("assignment claim_ids must be a list of non-empty strings")
    if is_safe_identifier(actual_id):
        expected_path = declared_result_path(run_id, str(actual_id))
        if assignment.get("result_path") != expected_path:
            errors.append("assignment result_path is not the canonical unique path")
    return errors


def validate_result_payload(
    result: object,
    assignment: Mapping[str, Any],
    *,
    run_id: str,
    context_version: str,
) -> list[str]:
    """Validate the evidence-bearing minimum shared by all result roles."""

    errors: list[str] = []
    if not isinstance(result, Mapping):
        return ["result artifact is not a JSON object"]
    assignment_id = str(assignment.get("assignment_id", ""))
    if result.get("schema_version") != 1:
        errors.append("result schema_version must equal 1")
    if result.get("run_id") != run_id:
        errors.append("result run_id does not match ACTIVE_RUN")
    if result.get("assignment_id") != assignment_id:
        errors.append("result assignment_id does not match its registration")
    if result.get("context_version") != context_version:
        errors.append("result context_version is stale")
    status = result.get("status")
    if status not in RESULT_STATUSES:
        errors.append("result status is invalid")
    if "agent_type" in result and result.get("agent_type") != assignment.get(
        "agent_type"
    ):
        errors.append("result agent_type does not match its registration")
    if "independence_mode" in result and result.get(
        "independence_mode"
    ) != assignment.get("independence_mode"):
        errors.append("result independence_mode does not match its registration")
    expected_path = declared_result_path(run_id, assignment_id)
    if "result_path" in result and result.get("result_path") != expected_path:
        errors.append("result_path inside the result does not match its registration")

    findings = result.get("findings")
    claim_results = result.get("claim_results")
    reported_errors = result.get("errors")
    if not any(
        isinstance(value, list) for value in (findings, claim_results, reported_errors)
    ):
        errors.append("result has no findings, claim_results, or errors list")

    claim_ids = set(assignment.get("claim_ids", []))
    seen_finding_ids: set[str] = set()
    if isinstance(findings, list):
        for index, finding in enumerate(findings):
            if not isinstance(finding, Mapping):
                errors.append(f"finding {index} is not an object")
                continue
            finding_id = finding.get("finding_id")
            if not is_safe_identifier(finding_id):
                errors.append(f"finding {index} has a missing or unsafe finding_id")
            elif str(finding_id) in seen_finding_ids:
                errors.append(f"duplicate finding_id in result: {finding_id}")
            else:
                seen_finding_ids.add(str(finding_id))
            if assignment.get("independence_mode") != "adjudication":
                if finding.get("claim_id") not in claim_ids:
                    errors.append(f"finding {finding_id!r} has an undeclared claim_id")
                if not isinstance(finding.get("verdict"), str) or not finding.get(
                    "verdict"
                ):
                    errors.append(f"finding {finding_id!r} lacks a verdict")
                if not isinstance(
                    finding.get("evidence_fingerprint"), str
                ) or not finding.get("evidence_fingerprint"):
                    errors.append(f"finding {finding_id!r} lacks evidence_fingerprint")
    elif findings is not None:
        errors.append("result findings must be a list")

    if isinstance(claim_results, list):
        for index, claim_result in enumerate(claim_results):
            if not isinstance(claim_result, Mapping):
                errors.append(f"claim_result {index} is not an object")
                continue
            if claim_result.get("claim_id") not in claim_ids:
                errors.append(f"claim_result {index} has an undeclared claim_id")
            if not isinstance(claim_result.get("verdict"), str) or not claim_result.get(
                "verdict"
            ):
                errors.append(f"claim_result {index} lacks a verdict")
    elif claim_results is not None:
        errors.append("result claim_results must be a list")
    if reported_errors is not None and not isinstance(reported_errors, list):
        errors.append("result errors must be a list when present")
    return errors
