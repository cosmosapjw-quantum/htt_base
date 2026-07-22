"""Single strict validator for registered harness result files."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from _harness import (
    EVIDENCE_FINGERPRINT_RE,
    SHA256_RE,
    compute_effective_context_sha256,
    declared_result_path,
    historical_run_ids,
    is_safe_identifier,
    load_json,
    role_file_hashes,
    validate_assignment_payload,
)


RESULT_STATUSES = {"pass", "fail", "inconclusive", "error"}
CLAIM_OUTCOMES = {"findings_present", "examined_no_findings", "not_examined"}
FINDING_SEVERITIES = {"low", "medium", "high", "critical"}
RESULT_SIZE_CAP_BYTES = 64 * 1024


def _string_list(
    value: object,
    *,
    field: str,
    errors: list[str],
    allow_empty: bool = True,
) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        errors.append(f"{field} must be a list of non-empty strings")
        return []
    if not allow_empty and not value:
        errors.append(f"{field} must not be empty")
    return list(value)


def _regular_repo_file(
    repo: Path,
    relative: object,
    *,
    field: str,
    errors: list[str],
) -> Path | None:
    if not isinstance(relative, str) or not relative:
        errors.append(f"{field} must be a non-empty repository-relative path")
        return None
    rel = Path(relative)
    if (
        rel.is_absolute()
        or ".." in rel.parts
        or "\\" in relative
        or rel.as_posix() != relative
    ):
        errors.append(
            f"{field} must stay inside the repository and use a canonical "
            "repository-relative path"
        )
        return None
    probe = repo
    for part in rel.parts:
        probe = probe / part
        if probe.is_symlink():
            errors.append(f"{field} traverses a symlink: {relative}")
            return None
    resolved = (repo / rel).resolve()
    try:
        resolved.relative_to(repo)
    except ValueError:
        errors.append(f"{field} escapes the repository")
        return None
    if not resolved.is_file():
        errors.append(f"{field} is missing or not a regular file: {relative}")
        return None
    return resolved


def _is_forbidden_sibling_result(
    relative: object,
    assignment: Mapping[str, Any],
    *,
    run_id: str,
    expected_result_path: str,
) -> bool:
    if not isinstance(relative, str):
        return False
    results_prefix = f".agent-harness/runs/{run_id}/results/"
    allowed = set(assignment.get("allowed_sibling_results", []) or [])
    return (
        relative.startswith(results_prefix)
        and relative != expected_result_path
        and relative not in allowed
        and assignment.get("independence_mode") != "adjudication"
    )


def _validate_artifacts(
    repo: Path,
    artifacts: object,
    *,
    assignment: Mapping[str, Any],
    run_id: str,
    expected_result_path: str,
    errors: list[str],
) -> None:
    if not isinstance(artifacts, list):
        errors.append("result artifacts must be a list")
        return
    seen_paths: set[str] = set()
    for index, row in enumerate(artifacts):
        field = f"artifact {index}"
        if not isinstance(row, Mapping):
            errors.append(f"{field} must be a typed reference object")
            continue
        required = {
            "path",
            "sha256",
            "bytes",
            "producer",
            "command_fingerprint",
        }
        if not required <= set(row):
            errors.append(
                f"{field} must contain path, sha256, bytes, producer, "
                "and command_fingerprint"
            )
            continue
        rel = row.get("path")
        if isinstance(rel, str) and rel in seen_paths:
            errors.append(f"duplicate artifact path: {rel}")
        elif isinstance(rel, str):
            seen_paths.add(rel)
        if _is_forbidden_sibling_result(
            rel,
            assignment,
            run_id=run_id,
            expected_result_path=expected_result_path,
        ):
            errors.append(
                f"{field} blind-results violation: unallowed sibling result {rel!r}"
            )
            continue
        path = _regular_repo_file(
            repo, rel, field=f"{field} path", errors=errors
        )
        digest = row.get("sha256")
        if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
            errors.append(f"{field} sha256 must be a lowercase SHA-256")
        byte_count = row.get("bytes")
        if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count < 0:
            errors.append(f"{field} bytes must be a non-negative integer")
        if not isinstance(row.get("producer"), str) or not row.get("producer"):
            errors.append(f"{field} producer must be non-empty")
        fingerprint = row.get("command_fingerprint")
        if (
            not isinstance(fingerprint, str)
            or EVIDENCE_FINGERPRINT_RE.fullmatch(fingerprint) is None
        ):
            errors.append(
                f"{field} command_fingerprint must be sha256:<64 lowercase hex>"
            )
        if path is not None:
            data = path.read_bytes()
            if isinstance(digest, str) and hashlib.sha256(data).hexdigest() != digest:
                errors.append(f"{field} sha256 does not match artifact bytes")
            if isinstance(byte_count, int) and not isinstance(byte_count, bool):
                if len(data) != byte_count:
                    errors.append(f"{field} bytes does not match artifact size")


def validate_launch_payload(
    launch: object,
    assignment: Mapping[str, Any],
    *,
    repo: Path,
    assignment_path: Path,
    index: Mapping[str, Any],
) -> tuple[list[str], str]:
    """Validate local launch binding and return its honest evidence origin.

    The repository can integrity-check its own receipt, but its public CLI
    cannot authenticate a platform event.  Therefore current receipts are
    explicitly ``self_declared``; a JSON claim of ``platform_authenticated``
    is rejected until a platform-owned verifier exists.
    """

    errors: list[str] = []
    if not isinstance(launch, Mapping):
        return ["launch receipt is not a JSON object"], "unverified"
    if launch.get("schema_version") != 1:
        errors.append("launch receipt schema_version must equal 1")
    if launch.get("run_id") != assignment.get("run_id"):
        errors.append("launch run_id does not match the assignment")
    if launch.get("assignment_id") != assignment.get("assignment_id"):
        errors.append("launch assignment_id does not match the assignment")
    launch_id = launch.get("launch_id")
    if not isinstance(launch_id, str) or SHA256_RE.fullmatch(launch_id) is None:
        errors.append("launch_id must be a lowercase SHA-256")
    origin = launch.get("evidence_origin")
    if origin == "platform_authenticated":
        errors.append(
            "platform_authenticated launch evidence has no platform-owned verifier"
        )
    elif origin != "self_declared":
        errors.append("launch evidence_origin must be self_declared")

    if not isinstance(launch.get("attested"), bool):
        errors.append("launch attested must be boolean")
    attested = launch.get("attested") is True
    expected_origin = "self_declared" if attested else "unverified"
    requested = launch.get("requested_profile")
    actual = launch.get("actual_profile")
    assigned_profile = assignment.get("agent_type")
    if requested != assigned_profile:
        errors.append(
            f"requested profile {requested!r} does not match assigned "
            f"agent_type {assigned_profile!r}"
        )
    if requested != actual:
        errors.append(f"requested profile {requested!r} != actual {actual!r}")
    if launch.get("fork_mode") != assignment.get("fork_mode"):
        errors.append("launch fork_mode does not match the sealed assignment")
    if launch.get("context_delivery_mode") not in {
        "hook_injected",
        "file_fallback",
    }:
        errors.append("launch context_delivery_mode is invalid")

    try:
        from profile_registry import ProfileRegistryError, load_profile_registry

        registry = load_profile_registry(repo)
    except (ImportError, ProfileRegistryError) as exc:
        errors.append(f"profile registry unavailable: {exc}")
        registry = {}
    profile = registry.get(str(actual)) if attested else None
    if attested:
        if profile is None:
            errors.append(f"profile not installed: {actual!r}")
        elif profile["config_sha256"] != launch.get("config_sha256"):
            errors.append(f"profile config drifted since launch: {actual!r}")
        elif profile["sandbox_mode"] != launch.get("sandbox"):
            errors.append(f"profile sandbox does not match installed profile: {actual!r}")

    if not assignment_path.is_file() or assignment_path.is_symlink():
        errors.append("sealed assignment file is unavailable for launch validation")
    else:
        role_files = role_file_hashes(repo, index, str(actual))
        expected_context = compute_effective_context_sha256(
            index, assignment_path.read_bytes(), role_files, launch
        )
        if launch.get("effective_context_sha256") != expected_context:
            errors.append("launch effective context is stale")
    return errors, expected_origin


def _validate_declared_reads(
    repo: Path,
    result: Mapping[str, Any],
    assignment: Mapping[str, Any],
    *,
    run_id: str,
    expected_result_path: str,
    errors: list[str],
) -> None:
    files_read = _string_list(
        result.get("files_read"), field="result files_read", errors=errors
    )
    if result.get("files_read_evidence") == "platform_authenticated":
        errors.append(
            "platform_authenticated files_read evidence has no platform-owned verifier"
        )
    elif result.get("files_read_evidence") != "self_declared":
        errors.append("result files_read_evidence must be self_declared")
    for rel in files_read:
        path = Path(rel)
        if (
            path.is_absolute()
            or ".." in path.parts
            or "\\" in rel
            or path.as_posix() != rel
        ):
            errors.append(
                f"self-declared files_read path is not canonical "
                f"repository-relative: {rel!r}"
            )
            continue
        if _is_forbidden_sibling_result(
            rel,
            assignment,
            run_id=run_id,
            expected_result_path=expected_result_path,
        ):
            errors.append(
                f"self-declared blind-results violation: sibling result read {rel!r}"
            )

    if any(rel.endswith("CONTEXT_PACK.md") for rel in files_read):
        deliveries = (
            repo
            / ".agent-harness"
            / "runs"
            / run_id
            / "launches"
            / "deliveries.jsonl"
        )
        agent_type = str(result.get("agent_type") or "")
        if deliveries.is_file() and not deliveries.is_symlink():
            for line in deliveries.read_text(encoding="utf-8").splitlines():
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if (
                    (record.get("agent_type") in (agent_type, None) or not agent_type)
                    and record.get("truncated") is False
                ):
                    errors.append(
                        "self-declared duplicate-delivery violation: full context "
                        "was hook-injected but CONTEXT_PACK.md was re-read"
                    )
                    break


def validate_result_payload(
    result: object,
    assignment: Mapping[str, Any],
    *,
    repo: Path,
    run_id: str,
    context_version: str,
    expected_result_path: str,
    launch: Mapping[str, Any] | None,
    launch_evidence: str,
    result_bytes: int,
    historical_runs: set[str] | None = None,
) -> list[str]:
    """Validate one result payload after its registered files are resolved."""

    errors: list[str] = []
    if not isinstance(result, Mapping):
        return ["result artifact is not a JSON object"]
    if historical_runs is None:
        historical_runs = historical_run_ids(repo)
    historical = run_id in historical_runs
    assignment_id = str(assignment.get("assignment_id", ""))
    expected_schema = 1 if historical else 2
    if result.get("schema_version") != expected_schema:
        errors.append(f"result schema_version must equal {expected_schema}")
    if result.get("run_id") != run_id:
        errors.append("result run_id does not match the registered run")
    if result.get("assignment_id") != assignment_id:
        errors.append("result assignment_id does not match its registration")
    if result.get("context_version") != context_version:
        errors.append("result context_version is stale")
    status = result.get("status")
    if status not in RESULT_STATUSES:
        errors.append("result status is invalid")

    if historical:
        findings = result.get("findings")
        claim_results = result.get("claim_results")
        reported_errors = result.get("errors")
        if not any(
            isinstance(value, list)
            for value in (findings, claim_results, reported_errors)
        ):
            errors.append("result has no findings, claim_results, or errors list")
        return errors

    if result_bytes > RESULT_SIZE_CAP_BYTES:
        errors.append(
            f"result artifact is {result_bytes} bytes; routine results are capped "
            f"at {RESULT_SIZE_CAP_BYTES} — reference content-addressed raw evidence"
        )
    if result.get("assignment_sha256") != assignment.get("assignment_sha256"):
        errors.append("result assignment_sha256 does not match the registration seal")
    if result.get("agent_type") != assignment.get("agent_type"):
        errors.append("result agent_type does not match its registration")
    if result.get("independence_mode") != assignment.get("independence_mode"):
        errors.append("result independence_mode does not match its registration")
    if result.get("result_path") != expected_result_path:
        errors.append("result_path inside the result does not match its registration")
    if launch is None:
        if result.get("launch_id") not in (None, ""):
            errors.append("result names a launch_id but no launch receipt exists")
    elif result.get("launch_id") != launch.get("launch_id"):
        errors.append("result launch_id does not match the launch receipt")
    if result.get("launch_evidence") != launch_evidence:
        errors.append(
            f"result launch_evidence must equal the verified class {launch_evidence!r}"
        )
    if result.get("execution_evidence") == "platform_authenticated":
        errors.append(
            "platform_authenticated execution evidence has no platform-owned verifier"
        )
    elif result.get("execution_evidence") != "self_declared":
        errors.append("result execution_evidence must be self_declared")

    for field in ("started_at", "completed_at"):
        if not isinstance(result.get(field), str) or not result.get(field):
            errors.append(f"result {field} must be a non-empty string")
    if not isinstance(result.get("tool_versions"), Mapping):
        errors.append("result tool_versions must be an object")
    if not isinstance(result.get("commands"), list):
        errors.append("result commands must be a list")
    _validate_artifacts(
        repo,
        result.get("artifacts"),
        assignment=assignment,
        run_id=run_id,
        expected_result_path=expected_result_path,
        errors=errors,
    )
    _validate_declared_reads(
        repo,
        result,
        assignment,
        run_id=run_id,
        expected_result_path=expected_result_path,
        errors=errors,
    )

    findings = result.get("findings")
    claim_results = result.get("claim_results")
    reported_errors = result.get("errors")
    if not isinstance(findings, list):
        errors.append("result findings must be a list")
        findings = []
    if not isinstance(claim_results, list):
        errors.append("result claim_results must be a list")
        claim_results = []
    if not isinstance(reported_errors, list):
        errors.append("result errors must be a list")
        reported_errors = []
    else:
        reported_errors = _string_list(
            reported_errors, field="result errors", errors=errors
        )

    claim_ids = set(assignment.get("claim_ids", []))
    finding_by_id: dict[str, Mapping[str, Any]] = {}
    for index, finding in enumerate(findings):
        if not isinstance(finding, Mapping):
            errors.append(f"finding {index} is not an object")
            continue
        finding_id = finding.get("finding_id")
        if not is_safe_identifier(finding_id):
            errors.append(f"finding {index} has a missing or unsafe finding_id")
            continue
        finding_text = str(finding_id)
        if finding_text in finding_by_id:
            errors.append(f"duplicate finding_id in result: {finding_text}")
            continue
        finding_by_id[finding_text] = finding
        claim_id = finding.get("claim_id")
        if claim_id not in claim_ids:
            errors.append(f"finding {finding_text!r} has an undeclared claim_id")
        if finding.get("verdict") not in RESULT_STATUSES:
            errors.append(f"finding {finding_text!r} has an invalid verdict")
        if finding.get("severity") not in FINDING_SEVERITIES:
            errors.append(
                f"finding {finding_text!r} severity must be one of "
                f"{sorted(FINDING_SEVERITIES)}"
            )
        fingerprint = finding.get("evidence_fingerprint")
        if (
            not isinstance(fingerprint, str)
            or EVIDENCE_FINGERPRINT_RE.fullmatch(fingerprint) is None
        ):
            errors.append(
                f"finding {finding_text!r} evidence_fingerprint must be "
                "sha256:<64 lowercase hex>"
            )
        if not isinstance(finding.get("statement"), str) or not finding.get(
            "statement"
        ):
            errors.append(f"finding {finding_text!r} lacks a statement")
        for list_field in (
            "assumptions_used",
            "evidence_refs",
            "counterevidence_refs",
            "reproduction",
            "unresolved",
        ):
            _string_list(
                finding.get(list_field),
                field=f"finding {finding_text!r} {list_field}",
                errors=errors,
                allow_empty=list_field != "evidence_refs",
            )
        confidence = finding.get("confidence")
        if (
            not isinstance(confidence, (int, float))
            or isinstance(confidence, bool)
            or not 0.0 <= float(confidence) <= 1.0
        ):
            errors.append(f"finding {finding_text!r} confidence must be in [0, 1]")

    seen_claims: set[str] = set()
    referenced_findings: set[str] = set()
    for index, claim_result in enumerate(claim_results):
        if not isinstance(claim_result, Mapping):
            errors.append(f"claim_result {index} is not an object")
            continue
        claim_id = claim_result.get("claim_id")
        if claim_id not in claim_ids:
            errors.append(f"claim_result {index} has an undeclared claim_id")
            continue
        claim_text = str(claim_id)
        if claim_text in seen_claims:
            errors.append(f"duplicate claim_result for claim_id: {claim_text}")
        seen_claims.add(claim_text)
        outcome = claim_result.get("outcome")
        if outcome not in CLAIM_OUTCOMES:
            errors.append(
                f"claim_result {claim_text!r} outcome must be one of "
                f"{sorted(CLAIM_OUTCOMES)}"
            )
        finding_ids = _string_list(
            claim_result.get("finding_ids"),
            field=f"claim_result {claim_text!r} finding_ids",
            errors=errors,
        )
        if len(set(finding_ids)) != len(finding_ids):
            errors.append(f"claim_result {claim_text!r} finding_ids must be unique")
        if outcome == "findings_present" and not finding_ids:
            errors.append(
                f"claim_result {claim_text!r} findings_present requires finding_ids"
            )
        if outcome in {"examined_no_findings", "not_examined"} and finding_ids:
            errors.append(
                f"claim_result {claim_text!r} {outcome} requires empty finding_ids"
            )
        if outcome == "examined_no_findings":
            _string_list(
                claim_result.get("evidence_refs"),
                field=f"claim_result {claim_text!r} evidence_refs",
                errors=errors,
                allow_empty=False,
            )
            fingerprint = claim_result.get("evidence_fingerprint")
            if (
                not isinstance(fingerprint, str)
                or EVIDENCE_FINGERPRINT_RE.fullmatch(fingerprint) is None
            ):
                errors.append(
                    f"claim_result {claim_text!r} examined_no_findings requires "
                    "evidence_fingerprint sha256:<64 lowercase hex>"
                )
        if outcome == "not_examined" and status not in {"inconclusive", "error"}:
            errors.append(
                f"claim_result {claim_text!r} not_examined requires "
                "inconclusive or error status"
            )
        if not isinstance(claim_result.get("summary"), str) or not claim_result.get(
            "summary"
        ):
            errors.append(f"claim_result {claim_text!r} requires a summary")
        for finding_id in finding_ids:
            finding = finding_by_id.get(finding_id)
            if finding is None:
                errors.append(
                    f"claim_result {claim_text!r} references unknown finding {finding_id!r}"
                )
            elif finding.get("claim_id") != claim_text:
                errors.append(
                    f"claim_result {claim_text!r} references finding for another claim"
                )
            if finding_id in referenced_findings:
                errors.append(f"finding is referenced by multiple claim_results: {finding_id}")
            referenced_findings.add(finding_id)

    if seen_claims != claim_ids:
        missing = sorted(claim_ids - seen_claims)
        extra = sorted(seen_claims - claim_ids)
        errors.append(
            f"claim_results must cover every assigned claim exactly once "
            f"(missing={missing}, extra={extra})"
        )
    unreferenced = sorted(set(finding_by_id) - referenced_findings)
    if unreferenced:
        errors.append(f"findings are not linked from claim_results: {unreferenced}")
    if status == "pass" and reported_errors:
        errors.append("pass result must not contain reported errors")
    if status == "error" and not reported_errors:
        errors.append("error result must contain at least one reported error")
    if status == "pass" and any(
        finding.get("verdict") == "fail" for finding in finding_by_id.values()
    ):
        errors.append("pass result must not contain a fail finding")
    if status == "pass" and any(
        finding.get("verdict") in {"inconclusive", "error"}
        for finding in finding_by_id.values()
    ):
        errors.append("pass result must contain only pass findings")
    if status == "fail" and not any(
        finding.get("verdict") == "fail" for finding in finding_by_id.values()
    ):
        errors.append("fail result must contain at least one fail finding")
    return errors


@dataclass
class RegisteredResultValidation:
    result_path: Path | None
    assignment: Mapping[str, Any] | None
    result: Mapping[str, Any] | None
    launch: Mapping[str, Any] | None
    launch_evidence: str
    errors: list[str]


def load_and_validate_registered_result_file(
    repo: Path,
    result_path: Path,
    *,
    run_id: str,
    context_version: str,
    envelope: Mapping[str, Any] | None = None,
) -> RegisteredResultValidation:
    """Load and strictly validate one registered result through one kernel."""

    repo = repo.resolve()
    errors: list[str] = []
    raw_path = result_path if result_path.is_absolute() else repo / result_path
    try:
        relative = raw_path.relative_to(repo)
    except ValueError:
        return RegisteredResultValidation(
            None, None, None, None, "unverified", ["result path escapes repository"]
        )
    if ".." in relative.parts:
        errors.append("result path escapes repository")
    expected_parent = Path(".agent-harness") / "runs" / run_id / "results"
    if relative.parent != expected_parent:
        errors.append("result file is outside the registered run results directory")
    assignment_id = relative.stem
    if not is_safe_identifier(run_id) or not is_safe_identifier(assignment_id):
        errors.append("run_id or result filename has an unsafe identifier")
    expected_result = declared_result_path(run_id, assignment_id)
    if relative.as_posix() != expected_result:
        errors.append("result filename is not the canonical registered path")
    resolved_result = _regular_repo_file(
        repo, relative.as_posix(), field="result path", errors=errors
    )

    assignment: Mapping[str, Any] | None = None
    assignment_path = (
        repo
        / ".agent-harness"
        / "runs"
        / run_id
        / "assignments"
        / f"{assignment_id}.json"
    )
    assignment_rel = assignment_path.relative_to(repo).as_posix()
    resolved_assignment = _regular_repo_file(
        repo, assignment_rel, field="registered assignment path", errors=errors
    )
    if resolved_assignment is not None:
        try:
            loaded_assignment = load_json(resolved_assignment)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid assignment JSON: {exc}")
        else:
            if isinstance(loaded_assignment, Mapping):
                assignment = loaded_assignment
                errors.extend(
                    validate_assignment_payload(
                        assignment,
                        run_id=run_id,
                        context_version=context_version,
                        assignment_id=assignment_id,
                        repo=repo,
                    )
                )
            else:
                errors.append("assignment is not a JSON object")

    result: Mapping[str, Any] | None = None
    result_bytes = 0
    if resolved_result is not None:
        try:
            data = resolved_result.read_bytes()
            loaded_result = json.loads(data)
            result_bytes = len(data)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid result JSON: {exc}")
        else:
            if isinstance(loaded_result, Mapping):
                result = loaded_result
            else:
                errors.append("result artifact is not a JSON object")

    launch: Mapping[str, Any] | None = None
    launch_evidence = "unverified"
    historical = run_id in historical_run_ids(repo)
    launch_path = (
        repo
        / ".agent-harness"
        / "runs"
        / run_id
        / "launches"
        / f"{assignment_id}.json"
    )
    if launch_path.exists() or launch_path.is_symlink():
        launch_rel = launch_path.relative_to(repo).as_posix()
        resolved_launch = _regular_repo_file(
            repo, launch_rel, field="launch path", errors=errors
        )
        if resolved_launch is not None:
            try:
                loaded_launch = load_json(resolved_launch)
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"invalid launch JSON: {exc}")
            else:
                if isinstance(loaded_launch, Mapping):
                    launch = loaded_launch
                    if assignment is not None and not historical:
                        index_path = (
                            repo / ".agent-harness" / "context" / "CONTEXT_INDEX.json"
                        )
                        try:
                            index = load_json(index_path)
                        except (OSError, json.JSONDecodeError) as exc:
                            errors.append(f"invalid context index: {exc}")
                        else:
                            launch_errors, launch_evidence = validate_launch_payload(
                                launch,
                                assignment,
                                repo=repo,
                                assignment_path=assignment_path,
                                index=index,
                            )
                            errors.extend(launch_errors)
                else:
                    errors.append("launch receipt is not a JSON object")

    if assignment is not None and result is not None:
        errors.extend(
            validate_result_payload(
                result,
                assignment,
                repo=repo,
                run_id=run_id,
                context_version=context_version,
                expected_result_path=expected_result,
                launch=launch,
                launch_evidence=launch_evidence,
                result_bytes=result_bytes,
            )
        )

    if envelope is not None:
        required = {"assignment_id", "context_version", "status", "result_path"}
        missing = sorted(required - set(envelope))
        if missing:
            errors.append(
                "HARNESS_RESULT is missing required fields: " + ", ".join(missing)
            )
        if not is_safe_identifier(envelope.get("assignment_id")):
            errors.append("HARNESS_RESULT assignment_id is unsafe")
        if envelope.get("status") not in RESULT_STATUSES:
            errors.append("HARNESS_RESULT status is invalid")
        if envelope.get("assignment_id") != assignment_id:
            errors.append("HARNESS_RESULT assignment_id does not match result filename")
        if envelope.get("context_version") != context_version:
            errors.append("HARNESS_RESULT context_version is stale")
        if envelope.get("result_path") != expected_result:
            errors.append("HARNESS_RESULT result_path is not canonical")
        if result is not None and envelope.get("status") != result.get("status"):
            errors.append("HARNESS_RESULT status does not match the result artifact")
        if launch is not None:
            if envelope.get("launch_id") != launch.get("launch_id"):
                errors.append("HARNESS_RESULT launch_id does not match launch receipt")
        elif envelope.get("launch_id") not in (None, ""):
            errors.append("HARNESS_RESULT names a launch_id without a receipt")

    return RegisteredResultValidation(
        resolved_result,
        assignment,
        result,
        launch,
        launch_evidence,
        errors,
    )
