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
RISK_TIERS = {"R0", "R1", "R2", "R3"}
CAS_AXES = {"wolfram_xact", "sympy", "sage_singular", "lean"}
RESULT_SIZE_CAP_BYTES = 64 * 1024


def historical_run_ids(repo: Path) -> set[str]:
    """Frozen pre-PR-124 runs that keep validating under schema v1."""

    path = repo / ".agent-harness" / "HISTORICAL_RUNS.json"
    if not path.is_file():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    runs = payload.get("runs", [])
    return {run for run in runs if isinstance(run, str)}


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


def _validate_hashed_input_list(
    repo: Path | None,
    values: object,
    *,
    field: str,
    errors: list[str],
) -> None:
    if not isinstance(values, list) or not values:
        errors.append(f"assignment {field} must be a non-empty list")
        return
    for index, item in enumerate(values):
        if not isinstance(item, Mapping):
            errors.append(f"assignment {field}[{index}] must be {{path, sha256}}")
            continue
        rel = item.get("path")
        sha = item.get("sha256")
        if not isinstance(rel, str) or not rel:
            errors.append(f"assignment {field}[{index}] lacks a path")
            continue
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha):
            errors.append(f"assignment {field}[{index}] lacks a sha256")
            continue
        if repo is not None:
            path = repo / rel
            if not path.is_file():
                errors.append(f"assignment {field}[{index}] path missing: {rel}")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != sha:
                errors.append(
                    f"assignment {field}[{index}] hash mismatch (stale input): {rel}"
                )


def validate_assignment_payload(
    assignment: object,
    *,
    run_id: str,
    context_version: str,
    assignment_id: str | None = None,
    registry: Mapping[str, Any] | None = None,
    historical_runs: set[str] | None = None,
    repo: Path | None = None,
) -> list[str]:
    """Fail-closed assignment validation (audit H3).

    Schema v2 is mandatory for new runs: unknown ``agent_type`` (not in the
    unique profile registry), empty ``claim_ids`` / ``required_inputs`` /
    ``allowed_tools`` / ``required_outputs``, a missing ``risk_tier``, an
    ``independent`` discovery mode without a rationale, or a CAS agent
    without an axis-bound contract are all registration errors. Runs listed
    in ``.agent-harness/HISTORICAL_RUNS.json`` keep validating under the
    frozen v1 rules so pre-PR-124 envelopes stay auditable.
    """

    errors: list[str] = []
    if not isinstance(assignment, Mapping):
        return ["assignment is not a JSON object"]
    if historical_runs is None:
        historical_runs = historical_run_ids(repo if repo is not None else root())
    historical = run_id in historical_runs

    actual_id = assignment.get("assignment_id")
    expected_schema = 1 if historical else 2
    if assignment.get("schema_version") != expected_schema:
        errors.append(f"assignment schema_version must equal {expected_schema}")
    if assignment.get("run_id") != run_id:
        errors.append("assignment run_id does not match ACTIVE_RUN")
    if not is_safe_identifier(actual_id):
        errors.append("assignment_id is missing or unsafe")
    if assignment_id is not None and actual_id != assignment_id:
        errors.append("assignment_id does not match the registered filename")
    if assignment.get("context_version") != context_version:
        errors.append("assignment context_version is stale")
    agent_type = assignment.get("agent_type")
    if not isinstance(agent_type, str) or not agent_type:
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
    if historical:
        return errors

    # --- v2 fail-closed additions -------------------------------------
    if isinstance(claim_ids, list) and not claim_ids:
        errors.append("assignment claim_ids must not be empty")
    if registry is None:
        try:
            from profile_registry import load_profile_registry

            registry = load_profile_registry(repo if repo is not None else root())
        except Exception as exc:  # fail closed: no registry, no registration
            errors.append(f"profile registry unavailable: {exc}")
            registry = {}
    if isinstance(agent_type, str) and agent_type and registry is not None:
        if agent_type not in registry:
            errors.append(
                f"assignment agent_type {agent_type!r} is not an installed profile"
            )
    if assignment.get("risk_tier") not in RISK_TIERS:
        errors.append(f"assignment risk_tier must be one of {sorted(RISK_TIERS)}")
    _validate_hashed_input_list(
        repo, assignment.get("required_inputs"), field="required_inputs", errors=errors
    )
    allowed_tools = assignment.get("allowed_tools")
    if (
        not isinstance(allowed_tools, list)
        or not allowed_tools
        or any(not isinstance(item, str) or not item for item in allowed_tools)
    ):
        errors.append("assignment allowed_tools must be a non-empty string list")
    required_outputs = assignment.get("required_outputs")
    if (
        not isinstance(required_outputs, list)
        or not required_outputs
        or any(not isinstance(item, str) or not item for item in required_outputs)
    ):
        errors.append("assignment required_outputs must be a non-empty string list")
    if assignment.get("discovery_mode") == "independent" and not str(
        assignment.get("independence_rationale") or ""
    ).strip():
        errors.append(
            "discovery_mode=independent requires a non-empty independence_rationale"
        )
    if isinstance(agent_type, str) and agent_type.startswith("cas_"):
        if assignment.get("cas_axis") not in CAS_AXES:
            errors.append(
                f"CAS assignment requires cas_axis in {sorted(CAS_AXES)}"
            )
        contract = assignment.get("cas_contract")
        if not isinstance(contract, Mapping):
            errors.append("CAS assignment requires cas_contract {path, sha256}")
        else:
            _validate_hashed_input_list(
                repo, [contract], field="cas_contract", errors=errors
            )
    return errors


def compute_effective_context_sha256(
    index: Mapping[str, Any],
    assignment_bytes: bytes,
    role_files: list[tuple[str, str]],
    receipt_fields: Mapping[str, Any],
) -> str:
    """Bind every effective launch input into one hash (audit H2).

    Covers the Tier-0 pack semantic fields (never ``built_at``), the sealed
    assignment bytes (which embed required-input hashes), per-role context
    file hashes, and the launcher/profile/delivery receipt fields. Any drift
    in any component blocks launch.
    """

    digest = hashlib.sha256()
    semantic = {
        "context_version": index.get("context_version"),
        "shared_files": index.get("shared_files"),
        "file_hashes": index.get("file_hashes"),
        "max_injected_chars": index.get("max_injected_chars"),
    }
    digest.update(json.dumps(semantic, sort_keys=True).encode("utf-8"))
    digest.update(b"\0")
    digest.update(assignment_bytes)
    digest.update(b"\0")
    for rel, sha in sorted(role_files):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha.encode("utf-8"))
        digest.update(b"\0")
    receipt_semantic = {
        "context_delivery_mode": receipt_fields.get("context_delivery_mode"),
        "requested_profile": receipt_fields.get("requested_profile"),
        "config_sha256": receipt_fields.get("config_sha256"),
        "fork_mode": receipt_fields.get("fork_mode"),
    }
    digest.update(json.dumps(receipt_semantic, sort_keys=True).encode("utf-8"))
    return digest.hexdigest()


def validate_result_payload(
    result: object,
    assignment: Mapping[str, Any],
    *,
    run_id: str,
    context_version: str,
    launch: Mapping[str, Any] | None = None,
    historical_runs: set[str] | None = None,
    result_bytes: int | None = None,
) -> list[str]:
    """Validate the evidence-bearing minimum shared by all result roles.

    v2 additions (non-historical runs): the envelope must carry the
    ``launch_id`` from the launcher-owned receipt when one exists, artifact
    rows must be typed ``{path, sha256, bytes, producer,
    command_fingerprint}`` references instead of inlined logs, and routine
    results above 64 KiB are rejected (audit §7 retention).
    """

    errors: list[str] = []
    if not isinstance(result, Mapping):
        return ["result artifact is not a JSON object"]
    if historical_runs is None:
        historical_runs = historical_run_ids(root())
    historical = run_id in historical_runs
    assignment_id = str(assignment.get("assignment_id", ""))
    if result.get("schema_version") != 1:
        errors.append("result schema_version must equal 1")
    if not historical:
        if launch is not None and result.get("launch_id") != launch.get("launch_id"):
            errors.append("result launch_id does not match the launch receipt")
        artifacts = result.get("artifacts")
        if isinstance(artifacts, list):
            for index, row in enumerate(artifacts):
                if not isinstance(row, Mapping) or not {
                    "path",
                    "sha256",
                    "bytes",
                    "producer",
                    "command_fingerprint",
                } <= set(row):
                    errors.append(
                        f"artifact {index} must be a typed reference "
                        "{path, sha256, bytes, producer, command_fingerprint}"
                    )
        if result_bytes is not None and result_bytes > RESULT_SIZE_CAP_BYTES:
            errors.append(
                f"result artifact is {result_bytes} bytes; routine results are "
                f"capped at {RESULT_SIZE_CAP_BYTES} — store raw output in the "
                "content-addressed evidence store and reference it"
            )
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
