from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EVIDENCE_IDENTITY_RE = re.compile(r"[^\x00-\x1f\x7f]{1,512}")
RISK_TIERS = {"R0", "R1", "R2", "R3"}
CAS_AXES = {"wolfram_xact", "sympy", "sage_singular", "lean"}
ACTIVE_RUN_RELATIVE_PATH = Path(".agent-harness/runtime/ACTIVE_RUN")
LEGACY_ACTIVE_RUN_RELATIVE_PATH = Path(".agent-harness/ACTIVE_RUN")


class ActiveRunError(RuntimeError):
    """Structured failure while resolving local run state."""

    def __init__(
        self,
        error_code: str,
        message: str,
        **details: str,
    ) -> None:
        super().__init__(f"{error_code}: {message}")
        self.error_code = error_code
        self.message = message
        self.details = details

    def as_dict(self) -> dict[str, str]:
        return {"code": self.error_code, "message": self.message, **self.details}


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
    cwd = Path.cwd().resolve()
    if (cwd / ".agent-harness").is_dir():
        return cwd
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


def confined_repo_file(repo: Path, rel: str, *, label: str) -> Path:
    """Resolve a canonical repository-relative regular file without symlink escape."""

    if not isinstance(rel, str) or not rel:
        raise ValueError(f"{label} must be a non-empty repository-relative path.")
    rel_path = Path(rel)
    if (
        rel_path.is_absolute()
        or ".." in rel_path.parts
        or "\\" in rel
        or rel_path.as_posix() != rel
    ):
        raise ValueError(f"{label} must be canonical and repository-relative: {rel}")
    probe = repo
    for part in rel_path.parts:
        probe = probe / part
        if probe.is_symlink():
            raise ValueError(f"{label} traverses a symlink: {rel}")
    if not probe.is_file():
        raise ValueError(f"{label} is missing or not a regular file: {rel}")
    return probe


def hash_files(repo: Path, files: list[str]) -> tuple[str, list[tuple[str, str]]]:
    digest = hashlib.sha256()
    entries: list[tuple[str, str]] = []
    for rel in files:
        path = confined_repo_file(repo, rel, label="Shared context source")
        data = path.read_bytes()
        file_hash = hashlib.sha256(data).hexdigest()
        entries.append((rel, file_hash))
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(data)
        digest.update(b"\0")
    return digest.hexdigest(), entries


def context_entries(
    repo: Path,
    index: Mapping[str, Any],
) -> tuple[str, list[tuple[str, str]], list[tuple[str, str]]]:
    """Resolve the injected Tier-0 sources named by the context index."""

    files = index.get("shared_files")
    pack_files = index.get("pack_files")
    if (
        not isinstance(files, list)
        or not files
        or any(not isinstance(rel, str) for rel in files)
        or len(files) != len(set(files))
    ):
        raise ValueError("shared_files must be a non-empty list of unique paths.")
    if (
        not isinstance(pack_files, list)
        or not pack_files
        or any(not isinstance(rel, str) for rel in pack_files)
        or len(pack_files) != len(set(pack_files))
        or pack_files != files
    ):
        raise ValueError(
            "pack_files must exactly equal shared_files; non-injected references "
            "must not rotate the global context version."
        )
    reference_files = index.get("reference_only_files", [])
    if (
        not isinstance(reference_files, list)
        or any(not isinstance(rel, str) for rel in reference_files)
        or len(reference_files) != len(set(reference_files))
    ):
        raise ValueError("reference_only_files must be a list of unique paths.")
    overlap = sorted(set(files) & set(reference_files))
    if overlap:
        raise ValueError(
            "shared_files and reference_only_files must be disjoint: "
            + ", ".join(overlap)
        )
    version, entries = hash_files(repo, files)
    hashes = dict(entries)
    return version, entries, [(rel, hashes[rel]) for rel in pack_files]


def render_context_pack(
    version: str,
    built_at: str,
    entries: list[tuple[str, str]],
    repo: Path,
) -> str:
    chunks = [
        "# Generated Shared Context View",
        "",
        f"Context version: `{version}`",
        f"Built at: `{built_at}`",
        "",
        (
            "This compact view is generated from the machine context index. "
            "Live HEAD, DAG, status, and active-run context is computed by the "
            "hooks at use time. Reference-only files are read only when an "
            "assignment names them."
        ),
    ]
    for rel, sha in entries:
        text = confined_repo_file(
            repo, rel, label="Context pack source"
        ).read_text(encoding="utf-8")
        chunks.extend(
            [
                "",
                f"---\n\n## Source: `{rel}`\n\nSHA-256: `{sha}`\n",
                text.rstrip(),
            ]
        )
    return "\n".join(chunks).rstrip() + "\n"


def load_validated_context_pack(repo: Path, index: Mapping[str, Any]) -> str:
    """Return the generated view only when index, sources, and rendered bytes agree."""

    actual, entries, pack_entries = context_entries(repo, index)
    if index.get("context_version") != actual:
        raise ValueError("Context sources changed after the generated view was built.")
    if index.get("file_hashes") != dict(entries):
        raise ValueError("CONTEXT_INDEX.json file_hashes do not match shared files.")
    expected = render_context_pack(
        actual,
        str(index.get("built_at", "")),
        pack_entries,
        repo,
    )
    pack_path = confined_repo_file(
        repo,
        ".agent-harness/generated/CONTEXT_PACK.md",
        label="Generated context view",
    )
    actual_text = pack_path.read_text(encoding="utf-8")
    if actual_text != expected:
        raise ValueError("Generated CONTEXT_PACK.md does not match the context index.")
    return actual_text


def active_run_pointer_paths(repo: Path) -> tuple[Path, Path]:
    """Return the local runtime pointer and the pre-MA-01 compatibility path."""

    return (
        repo / ACTIVE_RUN_RELATIVE_PATH,
        repo / LEGACY_ACTIVE_RUN_RELATIVE_PATH,
    )


def _relative_pointer(repo: Path, path: Path) -> str:
    return path.relative_to(repo).as_posix()


def _read_active_run_pointer(repo: Path, path: Path) -> str:
    pointer = _relative_pointer(repo, path)
    if path.is_symlink() or not path.is_file():
        raise ActiveRunError(
            "INVALID_ACTIVE_RUN_POINTER",
            "The active-run pointer must be a readable regular file containing a safe identifier.",
            pointer=pointer,
        )
    try:
        run_id = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise ActiveRunError(
            "INVALID_ACTIVE_RUN_POINTER",
            f"Cannot read the active-run pointer: {exc}",
            pointer=pointer,
        ) from exc
    if not is_safe_identifier(run_id):
        raise ActiveRunError(
            "INVALID_ACTIVE_RUN_POINTER",
            "The active-run pointer is empty or contains an unsafe identifier.",
            pointer=pointer,
        )
    return run_id


def active_run_id(
    repo: Path,
    *,
    required: bool = True,
) -> str | None:
    """Resolve active local run state without mistaking a dangling pointer for none.

    The runtime pointer is deliberately untracked.  The legacy root pointer is
    read only as an upgrade bridge; a clean clone contains neither.  Invalid or
    conflicting state is always an explicit error, including when ``required``
    is false.
    """

    candidates = [path for path in active_run_pointer_paths(repo) if path.exists()]
    if not candidates:
        if required:
            raise ActiveRunError(
                "NO_ACTIVE_RUN",
                "No active run. Use init_run.py first.",
            )
        return None

    values = [(path, _read_active_run_pointer(repo, path)) for path in candidates]

    distinct = {value for _, value in values}
    if len(distinct) != 1:
        detail = ", ".join(
            f"{_relative_pointer(repo, path)}={value!r}" for path, value in values
        )
        raise ActiveRunError(
            "CONFLICTING_ACTIVE_RUN_POINTERS",
            f"Runtime and legacy active-run pointers disagree: {detail}",
        )

    run_id = values[0][1]
    run_dir = repo / ".agent-harness" / "runs" / run_id
    plan_path = run_dir / "RUN_PLAN.json"
    pointer = _relative_pointer(repo, values[0][0])
    plan = None
    if (
        not run_dir.is_symlink()
        and run_dir.is_dir()
        and not plan_path.is_symlink()
        and plan_path.is_file()
    ):
        try:
            plan = load_json(plan_path)
        except (OSError, json.JSONDecodeError):
            pass
    if not isinstance(plan, Mapping) or plan.get("run_id") != run_id:
        raise ActiveRunError(
            "DANGLING_ACTIVE_RUN",
            "The active-run pointer has no valid matching RUN_PLAN.json target.",
            pointer=pointer,
            run_id=run_id,
        )
    return run_id


def _git_head_state(repo: Path) -> tuple[str, str]:
    """Distinguish a genuine unborn branch from an unreadable Git state."""

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                ["git", *args],
                cwd=repo,
                text=True,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ValueError("Git is unavailable; live HEAD cannot be resolved.") from exc

    head_result = run("rev-parse", "--verify", "HEAD^{commit}")
    head = head_result.stdout.strip()
    if head_result.returncode == 0:
        if re.fullmatch(r"[0-9a-f]{40,64}", head) is None:
            raise ValueError("Git returned a malformed HEAD identity.")
        branch_result = run("symbolic-ref", "--quiet", "--short", "HEAD")
        if branch_result.returncode == 0 and branch_result.stdout.strip():
            return head, branch_result.stdout.strip()
        if branch_result.returncode == 1:
            return head, "detached"
        detail = branch_result.stderr.strip() or "symbolic-ref failed"
        raise ValueError(f"Git branch state cannot be resolved: {detail}")

    symbolic = run("symbolic-ref", "--quiet", "HEAD")
    full_ref = symbolic.stdout.strip()
    if (
        symbolic.returncode == 0
        and full_ref.startswith("refs/heads/")
        and full_ref != "refs/heads/"
    ):
        shown = run("show-ref", "--verify", "--quiet", full_ref)
        if shown.returncode == 1:
            return "UNBORN", full_ref.removeprefix("refs/heads/")
        detail = (
            head_result.stderr.strip()
            or shown.stderr.strip()
            or "symbolic HEAD does not resolve to a commit"
        )
        raise ValueError(f"Git HEAD cannot be resolved: {detail}")
    detail = head_result.stderr.strip() or symbolic.stderr.strip() or "rev-parse failed"
    raise ValueError(f"Git HEAD cannot be resolved: {detail}")


def _yaml_scalar(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", text)
    if match is None:
        return None
    value = match.group(1).strip().strip("'\"")
    return None if value in {"", "null", "~"} else value


def _yaml_top_level_list_count(text: str, key: str) -> int:
    lines = text.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line.startswith(f"{key}:")),
        None,
    )
    if start is None:
        return 0
    inline = lines[start].split(":", 1)[1].strip()
    if inline in {"[]", "null", "~"}:
        return 0
    count = 0
    for line in lines[start + 1 :]:
        if line and not line[0].isspace() and not line.startswith("- "):
            break
        if line.startswith("- "):
            count += 1
    return count


def _yaml_pr_mapping_count(text: str) -> int:
    lines = text.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line == "prs:"),
        None,
    )
    if start is None:
        return 0
    count = 0
    for line in lines[start + 1 :]:
        if re.match(r"^  PR-[^:]+:", line) or re.match(r"^- id:\s*PR-", line):
            count += 1
            continue
        if line and not line[0].isspace():
            break
    return count


def resolve_live_context(repo: Path, index: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve transient operational context without creating another state file.

    The byte identities below are internal spawn-context drift seals only.
    They are not scientific provenance and must not be copied into claim,
    novelty, or research-artifact gates.
    """

    sources = index.get("live_sources")
    if not isinstance(sources, Mapping):
        raise ValueError("CONTEXT_INDEX.json must define live_sources.")
    dag_rel = sources.get("dag")
    status_rel = sources.get("status")
    if not isinstance(dag_rel, str) or not isinstance(status_rel, str):
        raise ValueError("live_sources must name string dag and status paths.")

    source_bytes: dict[str, bytes] = {}
    for label, rel in (("dag", dag_rel), ("status", status_rel)):
        path = confined_repo_file(repo, rel, label=f"Live {label} source")
        source_bytes[label] = path.read_bytes()

    dag_text = source_bytes["dag"].decode("utf-8")
    status_text = source_bytes["status"].decode("utf-8")
    head, branch = _git_head_state(repo)

    run_id = active_run_id(repo, required=False)
    run_summary = None
    if run_id is not None:
        plan = load_json(
            repo / ".agent-harness" / "runs" / run_id / "RUN_PLAN.json"
        )
        run_summary = {
            key: plan.get(key)
            for key in (
                "run_id",
                "work_unit_id",
                "spec_ref",
                "base_ref",
                "head_ref",
                "context_version",
                "status",
            )
        }

    identity_payload = {
        "context_version": index.get("context_version"),
        "head": head,
        "dag_sha256": hashlib.sha256(source_bytes["dag"]).hexdigest(),
        "status_sha256": hashlib.sha256(source_bytes["status"]).hexdigest(),
        "run": run_summary,
    }
    live_context_id = hashlib.sha256(
        json.dumps(
            identity_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    return {
        **identity_payload,
        "live_context_id": live_context_id,
        "branch": branch,
        "dag": {
            "path": dag_rel,
            "generated_on": _yaml_scalar(dag_text, "generated_on"),
            "scope": _yaml_scalar(dag_text, "scope"),
            "pr_count": _yaml_pr_mapping_count(dag_text),
        },
        "status": {
            "path": status_rel,
            "generated_on": _yaml_scalar(status_text, "generated_on"),
            "completed": _yaml_top_level_list_count(status_text, "completed"),
            "blocked": _yaml_top_level_list_count(status_text, "blocked"),
            "pending": _yaml_top_level_list_count(status_text, "pending"),
            "in_progress": _yaml_scalar(status_text, "in_progress"),
        },
    }


def format_live_context(state: Mapping[str, Any]) -> str:
    dag = state["dag"]
    status = state["status"]
    run = state.get("run")
    run_text = "none"
    if isinstance(run, Mapping):
        run_text = (
            f"{run.get('run_id')} (status={run.get('status') or 'unspecified'}, "
            f"work_unit={run.get('work_unit_id')}, spec={run.get('spec_ref')})"
        )
    return "\n".join(
        [
            f"Live context ID: {str(state['live_context_id'])[:12]}",
            f"HEAD: {str(state['head'])[:12]} ({state['branch']})",
            (
                f"DAG: {dag['path']} (generated={dag.get('generated_on')}, "
                f"prs={dag.get('pr_count')})"
            ),
            (
                f"Status: {status['path']} (generated={status.get('generated_on')}, "
                f"completed={status.get('completed')}, blocked={status.get('blocked')}, "
                f"pending={status.get('pending')}, "
                f"in_progress={status.get('in_progress') or 'none'})"
            ),
            f"Active run summary: {run_text}",
        ]
    )


def cli_active_run_id(
    repo: Path,
    *,
    required: bool = True,
) -> str | None:
    """Resolve active state for a CLI without leaking a Python traceback."""

    try:
        return active_run_id(repo, required=required)
    except ActiveRunError as exc:
        raise SystemExit(str(exc)) from None


def write_active_run_id(repo: Path, run_id: str) -> Path:
    """Atomically publish a local-only active-run pointer."""

    if not is_safe_identifier(run_id):
        raise ActiveRunError(
            "INVALID_ACTIVE_RUN_POINTER",
            f"Refusing to write an unsafe active-run identifier: {run_id!r}",
            run_id=run_id,
        )
    path = repo / ACTIVE_RUN_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(run_id + "\n", encoding="utf-8")
    temporary.replace(path)
    return path


def clear_active_run_pointers(
    repo: Path,
    *,
    expected_run_id: str | None = None,
) -> list[str]:
    """Remove only local pointer files; run directories and evidence remain."""

    targets: list[tuple[Path, str]] = []
    for path in active_run_pointer_paths(repo):
        if not path.exists():
            continue
        pointer = _relative_pointer(repo, path)
        if expected_run_id is not None:
            actual = _read_active_run_pointer(repo, path)
            if actual != expected_run_id:
                raise ActiveRunError(
                    "CONFLICTING_ACTIVE_RUN_POINTERS",
                    "The active-run pointer changed while the run was closing.",
                    pointer=pointer,
                    run_id=actual,
                )
        elif path.is_symlink() or not path.is_file():
            raise ActiveRunError(
                "INVALID_ACTIVE_RUN_POINTER",
                "Refusing to remove a non-regular active-run pointer.",
                pointer=pointer,
            )
        targets.append((path, pointer))

    cleared: list[str] = []
    for path, pointer in targets:
        path.unlink()
        cleared.append(pointer)
    return cleared


def is_safe_identifier(value: object) -> bool:
    return isinstance(value, str) and SAFE_IDENTIFIER_RE.fullmatch(value) is not None


def is_evidence_identity(value: object) -> bool:
    """Accept a bounded stable identity without pretending it is authenticated.

    A cryptographic digest is one valid identity when exact bytes matter, but a
    DOI, dataset release, source path/revision, or review-scope label is also a
    legitimate research identity.  This field is self-declared unless another
    validator explicitly binds it to bytes.
    """

    return (
        isinstance(value, str)
        and value == value.strip()
        and EVIDENCE_IDENTITY_RE.fullmatch(value) is not None
    )


def is_run_local_claim_id(value: object, run_id: str) -> bool:
    """Return whether a non-persistent process question is bound to this run."""

    return is_safe_identifier(value) and str(value).startswith(f"RUN-{run_id}-")


def declared_result_path(run_id: str, assignment_id: str) -> str:
    return f".agent-harness/runs/{run_id}/results/{assignment_id}.json"


def assignment_sha256(assignment: Mapping[str, Any]) -> str:
    """Return the canonical registration seal, excluding the seal field itself."""

    payload = dict(assignment)
    payload.pop("assignment_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_claim_references(
    repo: Path,
    row: Mapping[str, Any],
    *,
    line_number: int,
    errors: list[str],
) -> None:
    """Validate live spec/evidence links without evaluating a stored status."""

    spec_refs = row.get("spec_refs")
    evidence_refs = row.get("evidence_refs")
    if spec_refs is None and evidence_refs is None and "evidence_ids" not in row:
        return

    if "evidence_ids" in row:
        errors.append(
            f"claim registry line {line_number} uses duplicate evidence_ids; "
            "evidence_refs is the canonical base field"
        )

    spec_prs: set[str] = set()
    if (
        not isinstance(spec_refs, list)
        or not spec_refs
        or any(not isinstance(ref, str) or not ref for ref in spec_refs)
        or len(spec_refs) != len(set(spec_refs))
    ):
        errors.append(
            f"claim registry line {line_number} spec_refs must be a non-empty "
            "list of unique strings"
        )
    else:
        for index, ref in enumerate(spec_refs):
            rel = ref.split("#", 1)[0]
            try:
                confined_repo_file(
                    repo,
                    rel,
                    label=f"claim registry line {line_number} spec_refs[{index}]",
                )
            except ValueError as exc:
                errors.append(str(exc))
            match = re.fullmatch(
                r"docs/research_program/long_horizon_rescue/pr([0-9]+)_spec[.]yaml",
                rel,
            )
            if match is not None:
                spec_prs.add(match.group(1))

    evidence_prs: set[str] = set()
    if (
        not isinstance(evidence_refs, list)
        or not evidence_refs
        or any(not is_evidence_identity(ref) for ref in evidence_refs)
        or len(evidence_refs) != len(set(evidence_refs))
    ):
        errors.append(
            f"claim registry line {line_number} evidence_refs must be a non-empty "
            "list of unique evidence identities"
        )
    else:
        for ref in evidence_refs:
            match = re.fullmatch(r"E-PR([0-9]+)(?:-.+)", ref)
            if match is not None:
                evidence_prs.add(match.group(1))

    if spec_prs and evidence_prs and spec_prs.isdisjoint(evidence_prs):
        expected = ", ".join(f"E-PR{number}-*" for number in sorted(spec_prs))
        errors.append(
            f"claim registry line {line_number} has no evidence reference "
            f"matching its PR-scoped spec; expected one of {expected}"
        )


def _registered_claim_ids(repo: Path) -> tuple[set[str], list[str]]:
    """Load claim identities only; stored scientific/gate status is not authority."""

    path = repo / ".agent-harness" / "context" / "CLAIM_REGISTRY.jsonl"
    if not path.is_file() or path.is_symlink():
        return set(), ["canonical claim registry is missing or not a regular file"]
    claims: set[str] = set()
    errors: list[str] = []
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"claim registry line {line_number} is invalid JSON: {exc}")
            continue
        claim_id = row.get("claim_id") if isinstance(row, Mapping) else None
        if not is_safe_identifier(claim_id):
            errors.append(
                f"claim registry line {line_number} has a missing or unsafe claim_id"
            )
            continue
        claim_text = str(claim_id)
        if claim_text in claims:
            errors.append(f"claim registry has duplicate claim_id: {claim_text}")
        claims.add(claim_text)
    if not claims:
        errors.append("canonical claim registry contains no claim identities")
    return claims, errors


def validate_claim_registry(repo: Path) -> list[str]:
    """Return current referential errors; stored claim/gate status is ignored."""

    _, errors = _registered_claim_ids(repo)
    path = repo / ".agent-harness" / "context" / "CLAIM_REGISTRY.jsonl"
    if not path.is_file() or path.is_symlink():
        return errors
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(row, Mapping) and is_safe_identifier(row.get("claim_id")):
            _validate_claim_references(
                repo,
                row,
                line_number=line_number,
                errors=errors,
            )
    return errors


def _validate_input_list(
    repo: Path | None,
    values: object,
    *,
    field: str,
    errors: list[str],
    require_hash: bool = False,
) -> None:
    if not isinstance(values, list) or not values:
        errors.append(f"assignment {field} must be a non-empty list")
        return
    for index, item in enumerate(values):
        if not isinstance(item, Mapping):
            errors.append(
                f"assignment {field}[{index}] must contain a path and may "
                "contain sha256"
            )
            continue
        rel = item.get("path")
        has_sha = "sha256" in item
        sha = item.get("sha256")
        if not isinstance(rel, str) or not rel:
            errors.append(f"assignment {field}[{index}] lacks a path")
            continue
        rel_path = Path(rel)
        if (
            rel_path.is_absolute()
            or ".." in rel_path.parts
            or "\\" in rel
            or rel_path.as_posix() != rel
        ):
            errors.append(
                f"assignment {field}[{index}] path must be canonical and "
                f"repository-relative: {rel}"
            )
            continue
        if require_hash and not has_sha:
            errors.append(f"assignment {field}[{index}] requires a sha256")
            continue
        if has_sha and (
            not isinstance(sha, str) or SHA256_RE.fullmatch(sha) is None
        ):
            errors.append(f"assignment {field}[{index}] has an invalid sha256")
            continue
        if repo is not None:
            path = repo / rel_path
            probe = repo
            traverses_symlink = False
            for part in rel_path.parts:
                probe = probe / part
                if probe.is_symlink():
                    traverses_symlink = True
                    break
            if traverses_symlink:
                errors.append(
                    f"assignment {field}[{index}] path traverses a symlink: {rel}"
                )
            elif not path.is_file():
                errors.append(f"assignment {field}[{index}] path missing: {rel}")
            elif has_sha and hashlib.sha256(path.read_bytes()).hexdigest() != sha:
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
        not is_safe_identifier(item) for item in claim_ids
    ):
        errors.append("assignment claim_ids must be a list of safe identifiers")
    elif len(set(claim_ids)) != len(claim_ids):
        errors.append("assignment claim_ids must be unique")
    if is_safe_identifier(actual_id):
        expected_path = declared_result_path(run_id, str(actual_id))
        if assignment.get("result_path") != expected_path:
            errors.append("assignment result_path is not the canonical unique path")
    if historical:
        return errors

    # --- v2 fail-closed additions -------------------------------------
    if isinstance(claim_ids, list) and not claim_ids:
        errors.append("assignment claim_ids must not be empty")
    seal = assignment.get("assignment_sha256")
    if not isinstance(seal, str) or SHA256_RE.fullmatch(seal) is None:
        errors.append("assignment assignment_sha256 must be a lowercase SHA-256")
    elif seal != assignment_sha256(assignment):
        errors.append("assignment_sha256 does not match the sealed assignment payload")
    if repo is None:
        errors.append("strict assignment validation requires the repository root")
    else:
        registered_claims, claim_registry_errors = _registered_claim_ids(repo)
        errors.extend(claim_registry_errors)
        if isinstance(claim_ids, list):
            for claim_id in claim_ids:
                if (
                    isinstance(claim_id, str)
                    and claim_id not in registered_claims
                    and not is_run_local_claim_id(claim_id, run_id)
                ):
                    errors.append(f"assignment claim_id is not registered: {claim_id}")
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
    _validate_input_list(
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
            _validate_input_list(
                repo,
                [contract],
                field="cas_contract",
                errors=errors,
                require_hash=True,
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
        "pack_files": index.get("pack_files"),
        "live_sources": index.get("live_sources"),
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
        "actual_profile": receipt_fields.get("actual_profile"),
        "config_sha256": receipt_fields.get("config_sha256"),
        "model": receipt_fields.get("model"),
        "sandbox": receipt_fields.get("sandbox"),
        "fork_mode": receipt_fields.get("fork_mode"),
        "attested": receipt_fields.get("attested"),
        "evidence_origin": receipt_fields.get("evidence_origin"),
    }
    digest.update(json.dumps(receipt_semantic, sort_keys=True).encode("utf-8"))
    return digest.hexdigest()


def role_file_hashes(
    repo: Path, index: Mapping[str, Any], agent_type: str
) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    role_files = index.get("role_files", {})
    if not isinstance(role_files, Mapping):
        return rows
    for rel in role_files.get(agent_type, []):
        path = repo / str(rel)
        digest = (
            hashlib.sha256(path.read_bytes()).hexdigest()
            if path.is_file() and not path.is_symlink()
            else "MISSING"
        )
        rows.append((str(rel), digest))
    return rows
