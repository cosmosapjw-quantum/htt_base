"""Fail-closed change-set and publication-integrity primitives.

This module never publishes.  Repository hooks use it to deny ordinary-agent
publication attempts; a credential-isolated external publisher may use the
validation functions immediately before a serialized publication transaction.
Repo-local hooks are guardrails, not an authentication boundary.
"""
from __future__ import annotations

import fcntl
import hashlib
import hmac
import json
import math
import os
import re
import shlex
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlsplit


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_OID_RE = re.compile(r"^[0-9a-f]{40,64}$")
CANONICAL_CHANGE_SET_RE = re.compile(r"^CS-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
CANONICAL_PUBLICATION_GROUP_RE = re.compile(r"^PG-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
CHANGE_SET_METADATA_LINE_RE = re.compile(
    r"(?m)^Change-Set-ID:[ \t]*(CS-[A-Z0-9]+(?:-[A-Z0-9]+)*)[ \t]*$"
)
PUBLICATION_GROUP_METADATA_LINE_RE = re.compile(
    r"(?m)^Publication-Group-ID:[ \t]*"
    r"(PG-[A-Z0-9]+(?:-[A-Z0-9]+)*)[ \t]*$"
)
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SHELL_SEPARATORS = {";", "&&", "||", "|", "&", "\n"}
REVIEW_STATUSES = {"PASS", "FAIL", "NOT_APPLICABLE", "WAIVED"}
EXECUTABLE_ORACLE_KINDS = {
    "property_test",
    "metamorphic_test",
    "mutation_test",
    "differential_implementation",
    "static_analyzer",
    "type_checker",
    "security_analyzer",
    "hidden_human_test",
    "independent_dataset",
    "invariant_checker",
    "independent_numerical_backend",
}
PYTHON_EXECUTABLE_TOKEN = "{python}"
NON_PUBLISHING_GIT_SUBCOMMANDS = {
    "add",
    "am",
    "apply",
    "archive",
    "bisect",
    "blame",
    "branch",
    "bundle",
    "cat-file",
    "check-ignore",
    "check-ref-format",
    "checkout",
    "cherry-pick",
    "clean",
    "clone",
    "commit",
    "config",
    "count-objects",
    "describe",
    "diff",
    "diff-index",
    "diff-tree",
    "difftool",
    "fetch",
    "for-each-ref",
    "format-patch",
    "fsck",
    "gc",
    "grep",
    "hash-object",
    "help",
    "init",
    "log",
    "ls-files",
    "ls-remote",
    "ls-tree",
    "maintenance",
    "merge",
    "merge-base",
    "merge-file",
    "merge-tree",
    "mergetool",
    "mktree",
    "mv",
    "name-rev",
    "notes",
    "pack-objects",
    "prune",
    "pull",
    "range-diff",
    "read-tree",
    "rebase",
    "reflog",
    "remote",
    "repack",
    "replace",
    "request-pull",
    "reset",
    "restore",
    "revert",
    "rev-list",
    "rev-parse",
    "rm",
    "show",
    "show-branch",
    "show-ref",
    "sparse-checkout",
    "stash",
    "status",
    "submodule",
    "switch",
    "symbolic-ref",
    "tag",
    "update-index",
    "update-ref",
    "verify-commit",
    "verify-pack",
    "verify-tag",
    "version",
    "whatchanged",
    "worktree",
    "write-tree",
}


class PublicationIntegrityError(RuntimeError):
    """A fail-closed publication-integrity validation error."""


def canonical_json_bytes(
    value: Mapping[str, Any], *, omit: Iterable[str] = ()
) -> bytes:
    def reject_nonfinite(item: object) -> None:
        if isinstance(item, float) and not math.isfinite(item):
            raise PublicationIntegrityError(
                "publication artifact contains NaN or infinity"
            )
        if isinstance(item, Mapping):
            if any(not isinstance(key, str) for key in item):
                raise PublicationIntegrityError(
                    "publication artifact object keys must be strings"
                )
            for nested in item.values():
                reject_nonfinite(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                reject_nonfinite(nested)

    payload = dict(value)
    for field in omit:
        payload.pop(field, None)
    reject_nonfinite(payload)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def canonical_sha256(
    value: Mapping[str, Any], *, omit: Iterable[str] = ()
) -> str:
    return hashlib.sha256(canonical_json_bytes(value, omit=omit)).hexdigest()


def bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise PublicationIntegrityError(f"{field} must be a non-empty UTC timestamp")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise PublicationIntegrityError(f"{field} is not an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise PublicationIntegrityError(f"{field} must be timezone-aware UTC")
    return parsed


def require_plain_int(
    value: object,
    *,
    field: str,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    if type(value) is not int:
        raise PublicationIntegrityError(f"{field} must be an integer (bool is invalid)")
    result = int(value)
    if minimum is not None and result < minimum:
        raise PublicationIntegrityError(f"{field} must be >= {minimum}")
    if maximum is not None and result > maximum:
        raise PublicationIntegrityError(f"{field} must be <= {maximum}")
    return result


def require_safe_id(value: object, *, field: str) -> str:
    if not isinstance(value, str) or SAFE_ID_RE.fullmatch(value) is None:
        raise PublicationIntegrityError(f"{field} is missing or not a safe identifier")
    return value


def require_change_set_id(value: object) -> str:
    if not isinstance(value, str) or CANONICAL_CHANGE_SET_RE.fullmatch(value) is None:
        raise PublicationIntegrityError(
            "change_set_id must use canonical uppercase CS-... form; aliases are forbidden"
        )
    return value


def require_publication_group_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or CANONICAL_PUBLICATION_GROUP_RE.fullmatch(value) is None
    ):
        raise PublicationIntegrityError(
            "publication_group_id must use canonical uppercase PG-... form"
        )
    return value


def single_pr_metadata(
    pattern: re.Pattern[str], body: object, *, field: str
) -> str:
    if not isinstance(body, str) or not body:
        raise PublicationIntegrityError(f"{field} is missing")
    matches = pattern.findall(body)
    if len(matches) != 1:
        raise PublicationIntegrityError(
            f"{field} must occur exactly once in the PR body"
        )
    return matches[0]


def require_branch_name(value: object, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value.startswith("refs/")
        or value.startswith(("/", "."))
        or value.endswith(("/", ".", ".lock"))
        or ".." in value
        or "@{" in value
        or any(
            char.isspace() or ord(char) < 32 or char in "~^:?*[\\"
            for char in value
        )
    ):
        raise PublicationIntegrityError(f"{field} is not a canonical branch name")
    return value


def require_repo_relative_name(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise PublicationIntegrityError(f"{field} must be non-empty")
    path = Path(value)
    if (
        path.is_absolute()
        or ".." in path.parts
        or "\\" in value
        or path.as_posix() != value
        or "\n" in value
        or "\r" in value
    ):
        raise PublicationIntegrityError(
            f"{field} must be a canonical repository-relative path"
        )
    return value


def git(
    repo: Path,
    *args: str,
    binary: bool = False,
    env: Mapping[str, str] | None = None,
    timeout_seconds: int | None = None,
) -> bytes | str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo,
            text=not binary,
            capture_output=True,
            check=False,
            env=dict(env) if env is not None else None,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as exc:
        raise PublicationIntegrityError("git is unavailable") from exc
    except subprocess.TimeoutExpired as exc:
        raise PublicationIntegrityError(
            f"git {' '.join(args)} timed out"
        ) from exc
    if completed.returncode != 0:
        stderr = completed.stderr
        if isinstance(stderr, bytes):
            detail = stderr.decode("utf-8", errors="replace").strip()
        else:
            detail = stderr.strip()
        raise PublicationIntegrityError(
            f"git {' '.join(args)} failed ({completed.returncode}): {detail}"
        )
    return completed.stdout


def resolve_repo_root(repo: str | Path) -> Path:
    candidate = Path(repo).resolve()
    value = str(git(candidate, "rev-parse", "--show-toplevel")).strip()
    resolved = Path(value).resolve()
    if resolved != candidate:
        raise PublicationIntegrityError(
            f"repository root mismatch: requested {candidate}, git resolved {resolved}"
        )
    return resolved


def _walk_without_symlinks(path: Path, *, stop: Path | None = None) -> None:
    absolute = path.absolute()
    stop_abs = stop.absolute() if stop is not None else Path(absolute.anchor)
    try:
        relative = absolute.relative_to(stop_abs)
    except ValueError as exc:
        raise PublicationIntegrityError(f"path escapes allowed root: {path}") from exc
    current = stop_abs
    for part in relative.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            if current == absolute:
                return
            raise PublicationIntegrityError(f"path parent is missing: {current}") from None
        if stat.S_ISLNK(mode):
            raise PublicationIntegrityError(f"path traverses a symlink: {path}")


def canonical_repo_path(repo: Path, relative: object, *, field: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise PublicationIntegrityError(f"{field} must be repository-relative")
    rel = Path(relative)
    if (
        rel.is_absolute()
        or ".." in rel.parts
        or "\\" in relative
        or rel.as_posix() != relative
    ):
        raise PublicationIntegrityError(
            f"{field} must be a canonical repository-relative path"
        )
    path = repo / rel
    _walk_without_symlinks(path, stop=repo)
    try:
        path.resolve().relative_to(repo)
    except ValueError as exc:
        raise PublicationIntegrityError(f"{field} escapes the repository") from exc
    return path


def runtime_output_path(repo: Path, relative: object, *, field: str) -> Path:
    name = require_repo_relative_name(relative, field=field)
    parts = Path(name).parts
    if len(parts) < 3 or parts[:2] != (".prguard", "runtime"):
        raise PublicationIntegrityError(
            f"{field} must be below .prguard/runtime/"
        )
    guard = repo / ".prguard"
    _walk_without_symlinks(guard, stop=repo)
    if not guard.is_dir():
        raise PublicationIntegrityError(".prguard must be a real directory")
    runtime = guard / "runtime"
    if not runtime.exists():
        runtime.mkdir(mode=0o700)
    _walk_without_symlinks(runtime, stop=repo)
    if not runtime.is_dir():
        raise PublicationIntegrityError(".prguard/runtime must be a real directory")
    return canonical_repo_path(repo, name, field=field)


def read_regular_bytes(
    path: Path,
    *,
    allowed_root: Path | None = None,
    field: str,
) -> bytes:
    if allowed_root is not None:
        _walk_without_symlinks(path, stop=allowed_root)
    elif path.is_symlink():
        raise PublicationIntegrityError(f"{field} must not be a symlink")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise PublicationIntegrityError(f"cannot open {field}: {exc}") from exc
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise PublicationIntegrityError(f"{field} is not a regular file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def read_json_bytes(data: bytes, *, field: str) -> Mapping[str, Any]:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate object key: {key}")
            value[key] = item
        return value

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite number: {value}")

    try:
        value = json.loads(
            data,
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise PublicationIntegrityError(f"{field} is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, Mapping):
        raise PublicationIntegrityError(f"{field} must contain a JSON object")
    return value


def read_repo_json(
    repo: Path, relative: object, *, field: str
) -> tuple[Path, bytes, Mapping[str, Any]]:
    path = canonical_repo_path(repo, relative, field=field)
    data = read_regular_bytes(path, allowed_root=repo, field=field)
    return path, data, read_json_bytes(data, field=field)


def read_external_json(
    repo: Path, path_value: str | Path, *, field: str
) -> tuple[Path, bytes, Mapping[str, Any]]:
    path, data = read_external_bytes(repo, path_value, field=field)
    return path, data, read_json_bytes(data, field=field)


def read_external_bytes(
    repo: Path, path_value: str | Path, *, field: str
) -> tuple[Path, bytes]:
    path = Path(path_value).expanduser().absolute()
    if _path_is_inside(path, repo):
        raise PublicationIntegrityError(f"{field} must be outside the repository")
    _walk_without_symlinks(path)
    data = read_regular_bytes(path, field=field)
    return path, data


def write_json_exclusive(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _walk_without_symlinks(path.parent)
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    data = json.dumps(value, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise PublicationIntegrityError(f"refusing to overwrite immutable file: {path}") from exc
    try:
        offset = 0
        while offset < len(data):
            offset += os.write(fd, data[offset:])
        os.fsync(fd)
    finally:
        os.close(fd)


def _remote_names(repo: Path) -> list[str]:
    names = [line for line in str(git(repo, "remote")).splitlines() if line]
    return sorted(names, key=len, reverse=True)


def canonical_target_ref(
    repo: Path, target_ref: str | None, *, default_remote: str = "origin"
) -> tuple[str, str, str]:
    """Return ``(remote, branch, refs/remotes/<remote>/<branch>)``.

    Missing target input is resolved only from an existing remote HEAD.  No
    branch name, including ``main``, is guessed.
    """

    if target_ref is None:
        symbolic = f"refs/remotes/{default_remote}/HEAD"
        try:
            raw = str(git(repo, "symbolic-ref", "--quiet", symbolic)).strip()
        except PublicationIntegrityError as exc:
            raise PublicationIntegrityError(
                f"{symbolic} is unavailable; pass an explicit remote target ref"
            ) from exc
    else:
        raw = target_ref.strip()
    if raw.startswith("refs/remotes/"):
        short = raw.removeprefix("refs/remotes/")
    else:
        short = raw
    for remote in _remote_names(repo):
        prefix = remote + "/"
        if short.startswith(prefix) and len(short) > len(prefix):
            branch = short[len(prefix) :]
            if branch == "HEAD":
                break
            require_branch_name(branch, field="target branch")
            canonical = f"refs/remotes/{remote}/{branch}"
            commit = str(git(repo, "rev-parse", "--verify", f"{canonical}^{{commit}}")).strip()
            if GIT_OID_RE.fullmatch(commit) is None:
                raise PublicationIntegrityError("target ref did not resolve to a commit")
            return remote, branch, canonical
    raise PublicationIntegrityError(
        "target_ref must name a resolvable remote-tracking branch, not a local branch"
    )


def remote_urls(repo: Path, remote: str, *, push: bool) -> list[str]:
    args = ["remote", "get-url", "--all"]
    if push:
        args.append("--push")
    args.append(remote)
    values = [line for line in str(git(repo, *args)).splitlines() if line]
    if not values:
        kind = "push" if push else "fetch"
        raise PublicationIntegrityError(f"remote {remote!r} has no {kind} URL")
    return values


def publication_repository_identity(
    urls: Iterable[object],
) -> tuple[str, str]:
    """Return the one network GitHub host and ``owner/repository`` identity.

    Both GitHub.com and GitHub Enterprise URL shapes are accepted. Local/file
    remotes are ignored so hermetic tests may fetch from a local bare remote
    while sealing a distinct GitHub publication destination.
    """

    identities: set[tuple[str, str]] = set()
    for value in urls:
        if not isinstance(value, str) or not value:
            raise PublicationIntegrityError(
                "publication remote URLs must be non-empty strings"
            )
        host: str | None = None
        path: str | None = None
        parsed = urlsplit(value)
        if parsed.scheme.lower() in {"https", "http", "ssh", "git"}:
            scheme = parsed.scheme.lower()
            if parsed.query or parsed.fragment:
                raise PublicationIntegrityError(
                    "publication remote URL must not contain query or fragment data"
                )
            if scheme in {"https", "http"} and (
                parsed.username is not None or parsed.password is not None
            ):
                raise PublicationIntegrityError(
                    "publication remote URL must not embed credentials"
                )
            if scheme in {"ssh", "git"} and (
                parsed.password is not None
                or parsed.username not in {None, "git"}
            ):
                raise PublicationIntegrityError(
                    "SSH publication remotes may use only the git user"
                )
            host = parsed.hostname
            path = parsed.path
        else:
            scp = re.fullmatch(
                r"(?:(?P<user>[^@/:]+)@)?(?P<host>[A-Za-z0-9.-]+):"
                r"(?P<path>[^?#]+)",
                value,
            )
            if scp is not None:
                if scp.group("user") not in {None, "git"}:
                    raise PublicationIntegrityError(
                        "SSH publication remotes may use only the git user"
                    )
                host = scp.group("host")
                path = scp.group("path")
        if host is None or path is None:
            continue
        canonical_host = host.lower().rstrip(".")
        if (
            not canonical_host
            or any(
                not label
                or label.startswith("-")
                or label.endswith("-")
                or re.fullmatch(r"[a-z0-9-]+", label) is None
                for label in canonical_host.split(".")
            )
        ):
            raise PublicationIntegrityError(
                f"publication remote has an invalid network host: {value}"
            )
        repository_path = path.strip("/")
        if repository_path.endswith(".git"):
            repository_path = repository_path[:-4]
        parts = repository_path.split("/")
        if (
            len(parts) != 2
            or any(
                not part
                or re.fullmatch(r"[A-Za-z0-9_.-]+", part) is None
                for part in parts
            )
        ):
            raise PublicationIntegrityError(
                "publication remote must identify exactly OWNER/REPOSITORY"
            )
        identities.add(
            (canonical_host, f"{parts[0]}/{parts[1]}".lower())
        )
    if len(identities) != 1:
        raise PublicationIntegrityError(
            "sealed remotes must resolve to exactly one GitHub publication "
            "host and repository"
        )
    return next(iter(identities))


def remote_target_sha(repo: Path, remote: str, branch: str) -> str:
    environment = dict(os.environ)
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    output = str(
        git(
            repo,
            "ls-remote",
            "--exit-code",
            remote,
            f"refs/heads/{branch}",
            env=environment,
            timeout_seconds=30,
        )
    )
    rows = [line.split() for line in output.splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) != 2:
        raise PublicationIntegrityError(
            "live remote target did not resolve to exactly one branch"
        )
    sha, ref = rows[0]
    if GIT_OID_RE.fullmatch(sha) is None or ref != f"refs/heads/{branch}":
        raise PublicationIntegrityError("live remote target identity is malformed")
    return sha


def load_publication_policy(
    repo: Path,
    relative: object,
    *,
    expected_sha256: str | None = None,
) -> tuple[bytes, Mapping[str, Any]]:
    _, data, value = read_repo_json(repo, relative, field="integration policy")
    digest = bytes_sha256(data)
    if expected_sha256 is not None and digest != expected_sha256:
        raise PublicationIntegrityError("integration policy bytes drifted")
    if value.get("schema_version") != 1:
        raise PublicationIntegrityError("publication policy schema_version must equal 1")
    require_safe_id(value.get("policy_id"), field="policy_id")
    for field, minimum, maximum in (
        ("max_open_prs", 1, 1000),
        ("max_direct_to_target_prs", 0, 1000),
        ("max_prs_per_change_set", 1, 1),
        ("max_stack_depth", 1, 100),
        ("max_file_overlap_prs", 0, 1000),
        ("max_inventory_age_seconds", 1, 3600),
        ("max_receipt_age_seconds", 1, 86400),
        ("max_authorization_ttl_seconds", 1, 3600),
    ):
        require_plain_int(
            value.get(field), field=field, minimum=minimum, maximum=maximum
        )
    cells = value.get("required_review_cells")
    if (
        not isinstance(cells, list)
        or not cells
        or any(not isinstance(cell, str) or not cell for cell in cells)
        or len(cells) != len(set(cells))
    ):
        raise PublicationIntegrityError(
            "required_review_cells must be a non-empty unique string list"
        )
    commands = value.get("required_commands")
    if not isinstance(commands, list) or not commands:
        raise PublicationIntegrityError("required_commands must be non-empty")
    command_ids: set[str] = set()
    for index, row in enumerate(commands):
        if not isinstance(row, Mapping):
            raise PublicationIntegrityError(f"required_commands[{index}] must be an object")
        command_id = require_safe_id(
            row.get("id"), field=f"required_commands[{index}].id"
        )
        if command_id in command_ids:
            raise PublicationIntegrityError(f"duplicate required command id: {command_id}")
        command_ids.add(command_id)
        argv = row.get("argv")
        if (
            not isinstance(argv, list)
            or not argv
            or any(not isinstance(item, str) or not item for item in argv)
        ):
            raise PublicationIntegrityError(
                f"required_commands[{index}].argv must be a non-empty string list"
            )
        if PYTHON_EXECUTABLE_TOKEN in argv and (
            argv[0] != PYTHON_EXECUTABLE_TOKEN
            or argv.count(PYTHON_EXECUTABLE_TOKEN) != 1
        ):
            raise PublicationIntegrityError(
                f"required_commands[{index}] may use {PYTHON_EXECUTABLE_TOKEN} "
                "exactly once as argv[0]"
            )
        classified_argv = [
            "python3" if item == PYTHON_EXECUTABLE_TOKEN else item
            for item in argv
        ]
        denied, reason = classify_publication_command(
            shlex.join(classified_argv)
        )
        if denied:
            raise PublicationIntegrityError(
                f"required_commands[{index}] is publication-capable: {reason}"
            )
        require_plain_int(
            row.get("timeout_seconds"),
            field=f"required_commands[{index}].timeout_seconds",
            minimum=1,
            maximum=3600,
        )
    return data, value


def _candidate_branch(repo: Path, candidate_ref: str) -> tuple[str, str, str]:
    candidate_sha = str(
        git(repo, "rev-parse", "--verify", f"{candidate_ref}^{{commit}}")
    ).strip()
    if GIT_OID_RE.fullmatch(candidate_sha) is None:
        raise PublicationIntegrityError("candidate ref did not resolve to a commit")
    if candidate_ref == "HEAD":
        try:
            full_ref = str(git(repo, "symbolic-ref", "--quiet", "HEAD")).strip()
        except PublicationIntegrityError as exc:
            raise PublicationIntegrityError(
                "candidate must be on a named integration branch"
            ) from exc
    elif candidate_ref.startswith("refs/heads/"):
        full_ref = candidate_ref
    else:
        try:
            full_ref = str(
                git(repo, "rev-parse", "--symbolic-full-name", candidate_ref)
            ).strip()
        except PublicationIntegrityError as exc:
            raise PublicationIntegrityError(
                "candidate_ref must resolve to a local branch"
            ) from exc
    if not full_ref.startswith("refs/heads/"):
        raise PublicationIntegrityError("candidate_ref must resolve to a local branch")
    branch = full_ref.removeprefix("refs/heads/")
    require_branch_name(branch, field="candidate branch")
    if not branch.startswith("changeset/"):
        raise PublicationIntegrityError("candidate branch must use the changeset/ prefix")
    ref_sha = str(git(repo, "rev-parse", "--verify", f"{full_ref}^{{commit}}")).strip()
    if ref_sha != candidate_sha:
        raise PublicationIntegrityError("candidate branch and candidate commit disagree")
    return branch, full_ref, candidate_sha


def _git_status_bytes(repo: Path) -> bytes:
    value = git(
        repo,
        "-c",
        "status.showUntrackedFiles=all",
        "-c",
        "diff.ignoreSubmodules=none",
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignore-submodules=none",
        binary=True,
    )
    assert isinstance(value, bytes)
    return value


def _changed_files(repo: Path, start: str, end: str) -> list[dict[str, str]]:
    raw = git(
        repo,
        "diff",
        "--name-status",
        "--no-renames",
        "-z",
        f"{start}..{end}",
        binary=True,
    )
    assert isinstance(raw, bytes)
    parts = [part for part in raw.split(b"\0") if part]
    if len(parts) % 2:
        raise PublicationIntegrityError("git returned malformed changed-file output")
    rows: list[dict[str, str]] = []
    for index in range(0, len(parts), 2):
        try:
            status_code = parts[index].decode("ascii")
            path = parts[index + 1].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PublicationIntegrityError(
                "changed paths must be valid UTF-8 for the publication contract"
            ) from exc
        if status_code not in {"A", "M", "D", "T", "U", "X", "B"}:
            raise PublicationIntegrityError(
                f"unexpected changed-file status: {status_code!r}"
            )
        require_repo_relative_name(path, field="changed-file path")
        rows.append({"status": status_code, "path": path})
    return rows


def build_candidate_seal(
    repo: str | Path,
    *,
    change_set_id: str,
    publication_group_id: str,
    target_ref: str | None,
    candidate_ref: str = "HEAD",
    integration_policy_path: str,
) -> dict[str, Any]:
    root = resolve_repo_root(repo)
    change_set = require_change_set_id(change_set_id)
    publication_group = require_publication_group_id(publication_group_id)
    remote, target_branch, canonical_target = canonical_target_ref(root, target_ref)
    base_sha = str(
        git(root, "rev-parse", "--verify", f"{canonical_target}^{{commit}}")
    ).strip()
    live_base_sha = remote_target_sha(root, remote, target_branch)
    if live_base_sha != base_sha:
        raise PublicationIntegrityError(
            "remote target differs from the local tracking ref; fetch, rebase, "
            "and freeze again"
        )
    branch, canonical_candidate_ref, candidate_sha = _candidate_branch(
        root, candidate_ref
    )
    if branch == target_branch:
        raise PublicationIntegrityError("candidate branch must differ from target branch")
    if _git_status_bytes(root):
        raise PublicationIntegrityError(
            "candidate worktree is dirty; commit or remove non-ignored changes first"
        )
    merge_base = str(git(root, "merge-base", base_sha, candidate_sha)).strip()
    if GIT_OID_RE.fullmatch(merge_base) is None:
        raise PublicationIntegrityError("merge-base did not resolve to a commit")
    tree_sha = str(
        git(root, "rev-parse", "--verify", f"{candidate_sha}^{{tree}}")
    ).strip()
    if GIT_OID_RE.fullmatch(tree_sha) is None:
        raise PublicationIntegrityError("candidate tree identity is malformed")
    diff = git(
        root,
        "diff",
        "--binary",
        "--full-index",
        "--no-color",
        "--no-ext-diff",
        "--no-textconv",
        "--no-renames",
        "--submodule=short",
        f"{merge_base}..{candidate_sha}",
        binary=True,
    )
    assert isinstance(diff, bytes)
    changed_files = _changed_files(root, merge_base, candidate_sha)
    if not diff or not changed_files:
        raise PublicationIntegrityError("candidate has no reviewable diff")
    commits = [
        line
        for line in str(
            git(root, "rev-list", "--reverse", f"{merge_base}..{candidate_sha}")
        ).splitlines()
        if line
    ]
    if not commits or any(GIT_OID_RE.fullmatch(item) is None for item in commits):
        raise PublicationIntegrityError("candidate commit set is empty or malformed")
    policy_data, policy = load_publication_policy(root, integration_policy_path)
    fetch_urls = remote_urls(root, remote, push=False)
    push_urls = remote_urls(root, remote, push=True)
    publication_host, publication_slug = publication_repository_identity(
        push_urls
    )
    combined_host, combined_slug = publication_repository_identity(
        [*fetch_urls, *push_urls]
    )
    if (combined_host, combined_slug) != (
        publication_host,
        publication_slug,
    ):
        raise PublicationIntegrityError(
            "fetch and push remotes identify different publication repositories"
        )
    payload: dict[str, Any] = {
        "schema_version": 1,
        "change_set_id": change_set,
        "publication_group_id": publication_group,
        "target_remote": remote,
        "target_branch": target_branch,
        "target_ref": canonical_target,
        "remote_fetch_urls": fetch_urls,
        "remote_push_urls": push_urls,
        "publication_repository_host": publication_host,
        "publication_repository_slug": publication_slug,
        "base_sha": base_sha,
        "candidate_branch": branch,
        "candidate_ref": canonical_candidate_ref,
        "candidate_sha": candidate_sha,
        "merge_base_sha": merge_base,
        "candidate_tree_sha": tree_sha,
        "candidate_commits": commits,
        "candidate_commits_sha256": bytes_sha256(
            canonical_json_bytes({"commits": commits})
        ),
        "diff_sha256": bytes_sha256(diff),
        "changed_files": changed_files,
        "changed_files_sha256": bytes_sha256(
            canonical_json_bytes({"changed_files": changed_files})
        ),
        "integration_policy": {
            "path": integration_policy_path,
            "sha256": bytes_sha256(policy_data),
            "policy_id": policy["policy_id"],
        },
        "dirty": False,
    }
    payload["seal_sha256"] = canonical_sha256(payload, omit={"seal_sha256"})
    return payload


def validate_candidate_seal_payload(
    seal: Mapping[str, Any], *, repo: str | Path
) -> list[str]:
    errors: list[str] = []
    try:
        if seal.get("schema_version") != 1:
            raise PublicationIntegrityError("candidate seal schema_version must equal 1")
        require_change_set_id(seal.get("change_set_id"))
        require_publication_group_id(seal.get("publication_group_id"))
        internal = seal.get("seal_sha256")
        if not isinstance(internal, str) or SHA256_RE.fullmatch(internal) is None:
            raise PublicationIntegrityError("seal_sha256 must be a lowercase SHA-256")
        if internal != canonical_sha256(seal, omit={"seal_sha256"}):
            raise PublicationIntegrityError("candidate seal checksum mismatch")
        policy_ref = seal.get("integration_policy")
        if not isinstance(policy_ref, Mapping):
            raise PublicationIntegrityError("candidate seal lacks integration_policy")
        current = build_candidate_seal(
            repo,
            change_set_id=str(seal.get("change_set_id") or ""),
            publication_group_id=str(seal.get("publication_group_id") or ""),
            target_ref=str(seal.get("target_ref") or ""),
            candidate_ref=str(seal.get("candidate_ref") or ""),
            integration_policy_path=str(policy_ref.get("path") or ""),
        )
        if current != dict(seal):
            for key in sorted(set(current) | set(seal)):
                if current.get(key) != seal.get(key):
                    errors.append(f"candidate seal field drifted: {key}")
    except (OSError, PublicationIntegrityError) as exc:
        errors.append(str(exc))
    return errors


def candidate_binding_from_payload(
    seal: Mapping[str, Any], *, seal_path: str, seal_file_sha256: str
) -> dict[str, Any]:
    if SHA256_RE.fullmatch(seal_file_sha256) is None:
        raise PublicationIntegrityError("candidate seal file hash is invalid")
    fields = (
        "base_sha",
        "candidate_sha",
        "merge_base_sha",
        "candidate_tree_sha",
        "diff_sha256",
        "changed_files_sha256",
    )
    binding = {
        "state": "frozen",
        "seal_path": seal_path,
        "seal_file_sha256": seal_file_sha256,
        "seal_sha256": seal.get("seal_sha256"),
    }
    binding.update({field: seal.get(field) for field in fields})
    for field in fields:
        value = binding[field]
        pattern = GIT_OID_RE if field.endswith("_sha") else SHA256_RE
        if not isinstance(value, str) or pattern.fullmatch(value) is None:
            raise PublicationIntegrityError(f"candidate seal field is invalid: {field}")
    return binding


def mutable_candidate_binding() -> dict[str, Any]:
    return {
        "state": "mutable",
        "seal_path": None,
        "seal_file_sha256": None,
        "seal_sha256": None,
        "base_sha": None,
        "candidate_sha": None,
        "merge_base_sha": None,
        "candidate_tree_sha": None,
        "diff_sha256": None,
        "changed_files_sha256": None,
    }


def validate_candidate_binding(
    binding: object,
    *,
    repo: Path,
    require_frozen: bool,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(binding, Mapping):
        return ["candidate_binding must be an object"]
    state = binding.get("state")
    if state == "mutable":
        if require_frozen:
            return ["workflow role requires a frozen candidate seal"]
        if dict(binding) != mutable_candidate_binding():
            return ["mutable candidate_binding must not carry frozen identities"]
        return []
    if state != "frozen":
        return ["candidate_binding state must be mutable or frozen"]
    try:
        seal_path = binding.get("seal_path")
        _, data, seal = read_repo_json(repo, seal_path, field="candidate seal")
        if bytes_sha256(data) != binding.get("seal_file_sha256"):
            raise PublicationIntegrityError("candidate seal file hash drifted")
        expected = candidate_binding_from_payload(
            seal,
            seal_path=str(seal_path),
            seal_file_sha256=bytes_sha256(data),
        )
        if dict(binding) != expected:
            raise PublicationIntegrityError(
                "candidate_binding does not match the referenced candidate seal"
            )
        errors.extend(validate_candidate_seal_payload(seal, repo=repo))
    except PublicationIntegrityError as exc:
        errors.append(str(exc))
    return errors


def _validate_string_list(
    value: object, *, field: str, allow_empty: bool = False
) -> list[str]:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or not item for item in value)
        or len(value) != len(set(value))
        or (not allow_empty and not value)
    ):
        qualifier = "a unique string list"
        if not allow_empty:
            qualifier = "a non-empty unique string list"
        raise PublicationIntegrityError(f"{field} must be {qualifier}")
    return list(value)


def validate_review_coverage_payload(
    coverage: Mapping[str, Any],
    *,
    seal: Mapping[str, Any],
    policy: Mapping[str, Any],
    run_id: str,
    assignment_id: str,
    risk_tier: str,
    require_ready: bool = True,
    repo: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    try:
        if coverage.get("schema_version") != 1:
            raise PublicationIntegrityError("review coverage schema_version must equal 1")
        if coverage.get("coverage_sha256") != canonical_sha256(
            coverage, omit={"coverage_sha256"}
        ):
            raise PublicationIntegrityError("review coverage checksum mismatch")
        bindings = {
            "run_id": run_id,
            "assignment_id": assignment_id,
            "change_set_id": seal.get("change_set_id"),
            "publication_group_id": seal.get("publication_group_id"),
            "candidate_seal_sha256": seal.get("seal_sha256"),
            "candidate_sha": seal.get("candidate_sha"),
            "candidate_tree_sha": seal.get("candidate_tree_sha"),
            "diff_sha256": seal.get("diff_sha256"),
            "changed_files_sha256": seal.get("changed_files_sha256"),
        }
        for field, expected in bindings.items():
            if coverage.get(field) != expected:
                raise PublicationIntegrityError(
                    f"review coverage targets a different {field}"
                )
        parse_utc(coverage.get("completed_at"), field="review completed_at")
        if coverage.get("first_verdict_read_only") is not True:
            raise PublicationIntegrityError(
                "first reviewer verdict must be recorded read-only"
            )
        if type(coverage.get("correlated_review")) is not bool:
            raise PublicationIntegrityError("correlated_review must be boolean")
        cells = coverage.get("coverage_cells")
        if not isinstance(cells, list):
            raise PublicationIntegrityError("coverage_cells must be a list")
        by_name: dict[str, Mapping[str, Any]] = {}
        for index, row in enumerate(cells):
            if not isinstance(row, Mapping):
                raise PublicationIntegrityError(
                    f"coverage_cells[{index}] must be an object"
                )
            name = row.get("cell")
            if not isinstance(name, str) or not name:
                raise PublicationIntegrityError(
                    f"coverage_cells[{index}].cell must be non-empty"
                )
            if name in by_name:
                raise PublicationIntegrityError(f"duplicate review coverage cell: {name}")
            by_name[name] = row
            status_value = row.get("status")
            if status_value not in REVIEW_STATUSES:
                raise PublicationIntegrityError(
                    f"coverage cell {name} has invalid status"
                )
            evidence = _validate_string_list(
                row.get("evidence_refs"),
                field=f"coverage cell {name} evidence_refs",
                allow_empty=True,
            )
            rationale = row.get("rationale")
            if not isinstance(rationale, str):
                raise PublicationIntegrityError(
                    f"coverage cell {name} rationale must be a string"
                )
            if status_value in {"PASS", "FAIL"} and not evidence:
                raise PublicationIntegrityError(
                    f"{status_value} coverage cell {name} requires evidence"
                )
            if status_value in {"NOT_APPLICABLE", "WAIVED"} and not rationale.strip():
                raise PublicationIntegrityError(
                    f"{status_value} coverage cell {name} requires a rationale"
                )
            if require_ready and status_value in {"FAIL", "WAIVED"}:
                raise PublicationIntegrityError(
                    f"coverage cell {name} blocks readiness with {status_value}"
                )
        required = set(policy["required_review_cells"])
        actual = set(by_name)
        if actual != required:
            raise PublicationIntegrityError(
                "review coverage cells do not exactly match policy "
                f"(missing={sorted(required - actual)}, extra={sorted(actual - required)})"
            )
        oracles = coverage.get("independent_oracles")
        if not isinstance(oracles, list):
            raise PublicationIntegrityError("independent_oracles must be a list")
        passing_executable = 0
        for index, oracle in enumerate(oracles):
            if not isinstance(oracle, Mapping):
                raise PublicationIntegrityError(
                    f"independent_oracles[{index}] must be an object"
                )
            kind = oracle.get("kind")
            if kind not in EXECUTABLE_ORACLE_KINDS:
                raise PublicationIntegrityError(
                    f"independent_oracles[{index}] has unsupported kind"
                )
            if oracle.get("status") != "PASS":
                raise PublicationIntegrityError(
                    f"independent_oracles[{index}] did not pass"
                )
            require_safe_id(
                oracle.get("oracle_id"),
                field=f"independent_oracles[{index}].oracle_id",
            )
            argv = oracle.get("argv")
            if (
                not isinstance(argv, list)
                or not argv
                or any(not isinstance(item, str) or not item for item in argv)
            ):
                raise PublicationIntegrityError(
                    f"independent_oracles[{index}].argv must be a non-empty "
                    "string list"
                )
            fingerprint = oracle.get("command_fingerprint")
            if fingerprint != canonical_sha256({"argv": argv}):
                raise PublicationIntegrityError(
                    f"independent_oracles[{index}] command fingerprint drifted"
                )
            if type(oracle.get("returncode")) is not int or oracle.get(
                "returncode"
            ) != 0:
                raise PublicationIntegrityError(
                    f"independent_oracles[{index}] did not exit zero"
                )
            if oracle.get("timed_out") is not False:
                raise PublicationIntegrityError(
                    f"independent_oracles[{index}] timed_out must be false"
                )
            started = parse_utc(
                oracle.get("started_at"),
                field=f"independent_oracles[{index}] started_at",
            )
            completed = parse_utc(
                oracle.get("completed_at"),
                field=f"independent_oracles[{index}] completed_at",
            )
            if completed < started:
                raise PublicationIntegrityError(
                    f"independent_oracles[{index}] completion precedes start"
                )
            artifact_path = oracle.get("artifact_path")
            artifact_sha = oracle.get("artifact_sha256")
            artifact_bytes = require_plain_int(
                oracle.get("artifact_bytes"),
                field=f"independent_oracles[{index}].artifact_bytes",
                minimum=0,
            )
            if not isinstance(artifact_sha, str) or SHA256_RE.fullmatch(
                artifact_sha
            ) is None:
                raise PublicationIntegrityError(
                    f"independent_oracles[{index}] artifact_sha256 is malformed"
                )
            if repo is not None:
                path = canonical_repo_path(
                    repo,
                    artifact_path,
                    field=f"independent_oracles[{index}].artifact_path",
                )
                data = read_regular_bytes(
                    path,
                    allowed_root=repo,
                    field=f"independent_oracles[{index}] artifact",
                )
                if len(data) != artifact_bytes:
                    raise PublicationIntegrityError(
                        f"independent_oracles[{index}] artifact byte count drifted"
                    )
                if bytes_sha256(data) != artifact_sha:
                    raise PublicationIntegrityError(
                        f"independent_oracles[{index}] artifact hash drifted"
                    )
            _validate_string_list(
                oracle.get("evidence_refs"),
                field=f"independent_oracles[{index}].evidence_refs",
            )
            passing_executable += 1
        if risk_tier in {"R2", "R3"} and passing_executable < 1:
            raise PublicationIntegrityError(
                f"{risk_tier} review requires at least one executable independent oracle"
            )
    except PublicationIntegrityError as exc:
        errors.append(str(exc))
    return errors


def validate_integration_receipt_payload(
    receipt: Mapping[str, Any],
    *,
    seal: Mapping[str, Any],
    policy: Mapping[str, Any],
    now: datetime | None = None,
    repo: Path | None = None,
    log_dir: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    clock = now or datetime.now(timezone.utc)
    try:
        if receipt.get("schema_version") != 1:
            raise PublicationIntegrityError(
                "integration receipt schema_version must equal 1"
            )
        if receipt.get("receipt_sha256") != canonical_sha256(
            receipt, omit={"receipt_sha256"}
        ):
            raise PublicationIntegrityError("integration receipt checksum mismatch")
        bindings = {
            "change_set_id": seal.get("change_set_id"),
            "publication_group_id": seal.get("publication_group_id"),
            "candidate_seal_sha256": seal.get("seal_sha256"),
            "candidate_sha": seal.get("candidate_sha"),
            "candidate_tree_sha": seal.get("candidate_tree_sha"),
            "diff_sha256": seal.get("diff_sha256"),
            "changed_files_sha256": seal.get("changed_files_sha256"),
            "target_remote": seal.get("target_remote"),
            "target_branch": seal.get("target_branch"),
            "latest_target_sha": seal.get("base_sha"),
            "integration_policy_sha256": seal.get("integration_policy", {}).get(
                "sha256"
            ),
        }
        for field, expected in bindings.items():
            if receipt.get(field) != expected:
                raise PublicationIntegrityError(
                    f"integration receipt targets a different {field}"
                )
        if receipt.get("status") != "PASS":
            raise PublicationIntegrityError("integration receipt status is not PASS")
        merged_tree = receipt.get("merged_tree_sha")
        if not isinstance(merged_tree, str) or GIT_OID_RE.fullmatch(merged_tree) is None:
            raise PublicationIntegrityError("merged_tree_sha is missing or malformed")
        if repo is not None:
            expected_tree = str(
                git(
                    repo,
                    "-c",
                    f"core.hooksPath={os.devnull}",
                    "merge-tree",
                    "--write-tree",
                    "--no-messages",
                    str(seal.get("base_sha") or ""),
                    str(seal.get("candidate_sha") or ""),
                    env={
                        **os.environ,
                        "GIT_CONFIG_GLOBAL": os.devnull,
                        "GIT_CONFIG_SYSTEM": os.devnull,
                        "GIT_CONFIG_NOSYSTEM": "1",
                        "GIT_ATTR_NOSYSTEM": "1",
                        "GIT_TERMINAL_PROMPT": "0",
                    },
                )
            ).strip()
            if GIT_OID_RE.fullmatch(expected_tree) is None:
                raise PublicationIntegrityError(
                    "latest-target merge did not resolve to one tree"
                )
            if merged_tree != expected_tree:
                raise PublicationIntegrityError(
                    "integration merged_tree_sha does not match the exact "
                    "target/candidate merge"
                )
        started = parse_utc(receipt.get("started_at"), field="integration started_at")
        completed = parse_utc(
            receipt.get("completed_at"), field="integration completed_at"
        )
        if completed < started:
            raise PublicationIntegrityError("integration completion precedes start")
        max_age = require_plain_int(
            policy.get("max_receipt_age_seconds"),
            field="max_receipt_age_seconds",
            minimum=1,
        )
        age = (clock - completed).total_seconds()
        if age < -30:
            raise PublicationIntegrityError("integration receipt is future-dated")
        if age > max_age:
            raise PublicationIntegrityError("integration receipt is stale")
        commands = receipt.get("commands")
        expected_commands = policy.get("required_commands")
        if not isinstance(commands, list) or len(commands) != len(expected_commands):
            raise PublicationIntegrityError(
                "integration receipt does not cover every required command exactly once"
            )
        for index, (actual, expected) in enumerate(zip(commands, expected_commands)):
            if not isinstance(actual, Mapping):
                raise PublicationIntegrityError(
                    f"integration commands[{index}] must be an object"
                )
            for field in ("id", "timeout_seconds"):
                if actual.get(field) != expected.get(field):
                    raise PublicationIntegrityError(
                        f"integration command {index} {field} drifted from policy"
                    )
            policy_argv = actual.get("policy_argv")
            if policy_argv != expected.get("argv"):
                raise PublicationIntegrityError(
                    f"integration command {index} policy_argv drifted from policy"
                )
            executed_argv = actual.get("argv")
            if (
                not isinstance(executed_argv, list)
                or not executed_argv
                or any(
                    not isinstance(item, str) or not item
                    for item in executed_argv
                )
            ):
                raise PublicationIntegrityError(
                    f"integration command {index} executed argv is malformed"
                )
            expected_argv = expected.get("argv")
            assert isinstance(expected_argv, list)
            if expected_argv[0] == PYTHON_EXECUTABLE_TOKEN:
                if (
                    executed_argv[1:] != expected_argv[1:]
                    or not Path(executed_argv[0]).is_absolute()
                ):
                    raise PublicationIntegrityError(
                        f"integration command {index} Python resolution drifted"
                    )
            elif executed_argv != expected_argv:
                raise PublicationIntegrityError(
                    f"integration command {index} argv drifted from policy"
                )
            executable_path = actual.get("executable_path")
            executable_realpath = actual.get("executable_realpath")
            executable_sha = actual.get("executable_sha256")
            if (
                executable_path != executed_argv[0]
                or not isinstance(executable_path, str)
                or not Path(executable_path).is_absolute()
                or not isinstance(executable_realpath, str)
                or not Path(executable_realpath).is_absolute()
                or not isinstance(executable_sha, str)
                or SHA256_RE.fullmatch(executable_sha) is None
            ):
                raise PublicationIntegrityError(
                    f"integration command {index} executable identity is malformed"
                )
            if repo is not None:
                try:
                    current_realpath = Path(executable_path).resolve(strict=True)
                except OSError as exc:
                    raise PublicationIntegrityError(
                        f"integration command {expected['id']} executable "
                        f"cannot be resolved: {exc}"
                    ) from exc
                if current_realpath != Path(executable_realpath):
                    raise PublicationIntegrityError(
                        f"integration command {expected['id']} executable "
                        "realpath drifted"
                    )
                executable_bytes = read_regular_bytes(
                    current_realpath,
                    field=f"integration command {expected['id']} executable",
                )
                if bytes_sha256(executable_bytes) != executable_sha:
                    raise PublicationIntegrityError(
                        f"integration command {expected['id']} executable hash drifted"
                    )
            if type(actual.get("returncode")) is not int or actual.get("returncode") != 0:
                raise PublicationIntegrityError(
                    f"integration command {expected['id']} did not exit zero"
                )
            if actual.get("timed_out") is not False:
                raise PublicationIntegrityError(
                    f"integration command {expected['id']} timed_out must be false"
                )
            for field in ("stdout_sha256", "stderr_sha256"):
                value = actual.get(field)
                if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
                    raise PublicationIntegrityError(
                        f"integration command {expected['id']} lacks {field}"
                    )
            for field in ("stdout_bytes", "stderr_bytes"):
                require_plain_int(
                    actual.get(field),
                    field=f"integration command {expected['id']} {field}",
                    minimum=0,
                )
            cmd_started = parse_utc(
                actual.get("started_at"),
                field=f"integration command {expected['id']} started_at",
            )
            cmd_completed = parse_utc(
                actual.get("completed_at"),
                field=f"integration command {expected['id']} completed_at",
            )
            if cmd_started < started or cmd_completed > completed or cmd_completed < cmd_started:
                raise PublicationIntegrityError(
                    f"integration command {expected['id']} timestamps are inconsistent"
                )
            if log_dir is not None:
                for stream in ("stdout", "stderr"):
                    log_path = log_dir / f"{expected['id']}.{stream}"
                    data = read_regular_bytes(
                        log_path,
                        allowed_root=repo,
                        field=f"integration {expected['id']} {stream} log",
                    )
                    if len(data) != actual.get(f"{stream}_bytes"):
                        raise PublicationIntegrityError(
                            f"integration command {expected['id']} "
                            f"{stream} byte count drifted"
                        )
                    if bytes_sha256(data) != actual.get(f"{stream}_sha256"):
                        raise PublicationIntegrityError(
                            f"integration command {expected['id']} "
                            f"{stream} log hash drifted"
                        )
    except PublicationIntegrityError as exc:
        errors.append(str(exc))
    return errors


def validate_pr_inventory_payload(
    inventory: Mapping[str, Any],
    *,
    seal: Mapping[str, Any],
    policy: Mapping[str, Any],
    now: datetime | None = None,
) -> list[str]:
    errors: list[str] = []
    clock = now or datetime.now(timezone.utc)
    try:
        if inventory.get("schema_version") != 1:
            raise PublicationIntegrityError("PR inventory schema_version must equal 1")
        if inventory.get("inventory_sha256") != canonical_sha256(
            inventory, omit={"inventory_sha256"}
        ):
            raise PublicationIntegrityError("PR inventory checksum mismatch")
        if inventory.get("target_remote") != seal.get("target_remote"):
            raise PublicationIntegrityError("PR inventory targets a different remote")
        if inventory.get("target_branch") != seal.get("target_branch"):
            raise PublicationIntegrityError("PR inventory targets a different branch")
        if inventory.get("repository_fetch_url") not in seal.get(
            "remote_fetch_urls", []
        ):
            raise PublicationIntegrityError("PR inventory targets a different repository")
        if inventory.get("repository_host") != seal.get(
            "publication_repository_host"
        ):
            raise PublicationIntegrityError(
                "PR inventory targets a different repository host"
            )
        if inventory.get("repository_slug") != seal.get(
            "publication_repository_slug"
        ):
            raise PublicationIntegrityError(
                "PR inventory targets a different repository slug"
            )
        observed = parse_utc(inventory.get("observed_at"), field="inventory observed_at")
        max_age = require_plain_int(
            policy.get("max_inventory_age_seconds"),
            field="max_inventory_age_seconds",
            minimum=1,
        )
        age = (clock - observed).total_seconds()
        if age < -30:
            raise PublicationIntegrityError("PR inventory is future-dated")
        if age > max_age:
            raise PublicationIntegrityError("PR inventory is stale")
        rows = inventory.get("open_prs")
        if not isinstance(rows, list):
            raise PublicationIntegrityError("open_prs must be a list")
        if len(rows) >= require_plain_int(
            policy.get("max_open_prs"), field="max_open_prs", minimum=1
        ):
            raise PublicationIntegrityError("repository open-PR budget is exhausted")
        candidate_paths = {
            require_repo_relative_name(
                row.get("path"), field="candidate changed-file path"
            )
            for row in seal.get("changed_files", [])
            if isinstance(row, Mapping)
        }
        duplicate_change_sets: list[int] = []
        duplicate_publication_groups: list[int] = []
        duplicate_heads: list[int] = []
        overlap_prs: list[int] = []
        direct_count = 0
        max_stack = 0
        seen_numbers: set[int] = set()
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                raise PublicationIntegrityError(f"open_prs[{index}] must be an object")
            number = require_plain_int(
                row.get("number"), field=f"open_prs[{index}].number", minimum=1
            )
            if number in seen_numbers:
                raise PublicationIntegrityError(f"duplicate open PR number: {number}")
            seen_numbers.add(number)
            head = require_branch_name(
                row.get("head_branch"),
                field=f"open_prs[{index}].head_branch",
            )
            base = require_branch_name(
                row.get("base_branch"),
                field=f"open_prs[{index}].base_branch",
            )
            head_sha = row.get("head_sha")
            if not isinstance(head_sha, str) or GIT_OID_RE.fullmatch(head_sha) is None:
                raise PublicationIntegrityError(f"open_prs[{index}] lacks head_sha")
            change_set = row.get("change_set_id")
            require_change_set_id(change_set)
            if change_set == seal.get("change_set_id"):
                duplicate_change_sets.append(number)
            publication_group = row.get("publication_group_id")
            require_publication_group_id(publication_group)
            if publication_group == seal.get("publication_group_id"):
                duplicate_publication_groups.append(number)
            if head == seal.get("candidate_branch"):
                duplicate_heads.append(number)
            paths = _validate_string_list(
                row.get("changed_files"),
                field=f"open_prs[{index}].changed_files",
            )
            paths = [
                require_repo_relative_name(
                    path,
                    field=f"open_prs[{index}].changed_files",
                )
                for path in paths
            ]
            if candidate_paths & set(paths):
                overlap_prs.append(number)
            depth = require_plain_int(
                row.get("stack_depth"),
                field=f"open_prs[{index}].stack_depth",
                minimum=1,
            )
            max_stack = max(max_stack, depth)
            if type(row.get("is_draft")) is not bool:
                raise PublicationIntegrityError(
                    f"open_prs[{index}].is_draft must be boolean"
                )
            if base == seal.get("target_branch"):
                direct_count += 1
        if duplicate_change_sets:
            raise PublicationIntegrityError(
                "change-set already has open PR(s): "
                + ", ".join(f"#{number}" for number in duplicate_change_sets)
            )
        if duplicate_publication_groups:
            raise PublicationIntegrityError(
                "publication group already has open PR(s): "
                + ", ".join(
                    f"#{number}" for number in duplicate_publication_groups
                )
            )
        if duplicate_heads:
            raise PublicationIntegrityError(
                "candidate branch already has open PR(s): "
                + ", ".join(f"#{number}" for number in duplicate_heads)
            )
        allowed_overlap = require_plain_int(
            policy.get("max_file_overlap_prs"),
            field="max_file_overlap_prs",
            minimum=0,
        )
        if len(overlap_prs) > allowed_overlap:
            raise PublicationIntegrityError(
                "candidate overlaps open PR(s): "
                + ", ".join(f"#{number}" for number in overlap_prs)
            )
        if direct_count >= require_plain_int(
            policy.get("max_direct_to_target_prs"),
            field="max_direct_to_target_prs",
            minimum=0,
        ):
            raise PublicationIntegrityError("direct-to-target PR budget is exhausted")
        if max_stack >= require_plain_int(
            policy.get("max_stack_depth"), field="max_stack_depth", minimum=1
        ):
            raise PublicationIntegrityError("open PR stack-depth budget is exhausted")
    except PublicationIntegrityError as exc:
        errors.append(str(exc))
    return errors


def _path_is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def load_publisher_key(key_path: str | Path, *, repo: Path) -> bytes:
    path = Path(key_path).expanduser().absolute()
    if _path_is_inside(path, repo):
        raise PublicationIntegrityError("publisher key must be outside the repository")
    _walk_without_symlinks(path)
    data = read_regular_bytes(path, field="publisher key")
    metadata = path.stat(follow_symlinks=False)
    if metadata.st_uid != os.getuid():
        raise PublicationIntegrityError("publisher key must be owned by the publisher user")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise PublicationIntegrityError("publisher key permissions must be 0600 or stricter")
    if metadata.st_nlink != 1:
        raise PublicationIntegrityError("publisher key must not have hard links")
    try:
        key = bytes.fromhex(data.decode("ascii").strip())
    except (UnicodeDecodeError, ValueError) as exc:
        raise PublicationIntegrityError(
            "publisher key must contain a hexadecimal secret"
        ) from exc
    if len(key) < 32:
        raise PublicationIntegrityError("publisher key must contain at least 256 bits")
    return key


def authorization_hmac(
    authorization: Mapping[str, Any], *, key: bytes
) -> str:
    return hmac.new(
        key,
        canonical_json_bytes(authorization, omit={"hmac_sha256"}),
        hashlib.sha256,
    ).hexdigest()


def validate_authorization_payload(
    authorization: Mapping[str, Any],
    *,
    key: bytes,
    seal: Mapping[str, Any],
    policy: Mapping[str, Any],
    artifact_hashes: Mapping[str, str],
    now: datetime | None = None,
) -> list[str]:
    errors: list[str] = []
    clock = now or datetime.now(timezone.utc)
    try:
        if authorization.get("schema_version") != 1:
            raise PublicationIntegrityError(
                "publish authorization schema_version must equal 1"
            )
        supplied_hmac = authorization.get("hmac_sha256")
        if not isinstance(supplied_hmac, str) or SHA256_RE.fullmatch(supplied_hmac) is None:
            raise PublicationIntegrityError("publish authorization HMAC is malformed")
        expected_hmac = authorization_hmac(authorization, key=key)
        if not hmac.compare_digest(supplied_hmac, expected_hmac):
            raise PublicationIntegrityError("publish authorization HMAC is invalid")
        bindings = {
            "change_set_id": seal.get("change_set_id"),
            "publication_group_id": seal.get("publication_group_id"),
            "target_remote": seal.get("target_remote"),
            "target_branch": seal.get("target_branch"),
            "publication_repository_host": seal.get(
                "publication_repository_host"
            ),
            "publication_repository_slug": seal.get(
                "publication_repository_slug"
            ),
            "candidate_branch": seal.get("candidate_branch"),
            "candidate_sha": seal.get("candidate_sha"),
            "candidate_seal_sha256": seal.get("seal_sha256"),
            "head_refspec": (
                f"{seal.get('candidate_sha')}:"
                f"refs/heads/{seal.get('candidate_branch')}"
            ),
            "pr_base_branch": seal.get("target_branch"),
            "pr_head_branch": seal.get("candidate_branch"),
        }
        for field, expected in bindings.items():
            if authorization.get(field) != expected:
                raise PublicationIntegrityError(
                    f"publish authorization targets a different {field}"
                )
        if authorization.get("remote_push_url") not in seal.get(
            "remote_push_urls", []
        ):
            raise PublicationIntegrityError(
                "publish authorization targets an unsealed push URL"
            )
        title = authorization.get("pr_title")
        if (
            not isinstance(title, str)
            or not title.strip()
            or "\n" in title
            or "\r" in title
            or len(title) > 256
        ):
            raise PublicationIntegrityError(
                "publish authorization pr_title is missing or malformed"
            )
        body = authorization.get("pr_body")
        if not isinstance(body, str) or not body.strip() or len(body) > 65536:
            raise PublicationIntegrityError(
                "publish authorization pr_body is missing or oversized"
            )
        if single_pr_metadata(
            CHANGE_SET_METADATA_LINE_RE,
            body,
            field="Change-Set-ID",
        ) != seal.get("change_set_id"):
            raise PublicationIntegrityError(
                "publish authorization PR body targets a different change-set"
            )
        if single_pr_metadata(
            PUBLICATION_GROUP_METADATA_LINE_RE,
            body,
            field="Publication-Group-ID",
        ) != seal.get("publication_group_id"):
            raise PublicationIntegrityError(
                "publish authorization PR body targets a different publication group"
            )
        if type(authorization.get("pr_draft")) is not bool:
            raise PublicationIntegrityError(
                "publish authorization pr_draft must be boolean"
            )
        auth_hashes = authorization.get("artifact_hashes")
        if not isinstance(auth_hashes, Mapping) or dict(auth_hashes) != dict(
            artifact_hashes
        ):
            raise PublicationIntegrityError(
                "publish authorization artifact hashes do not match current evidence"
            )
        if set(auth_hashes) != {
            "candidate_seal_file_sha256",
            "review_result_file_sha256",
            "integration_receipt_file_sha256",
            "pr_inventory_file_sha256",
        } or any(
            not isinstance(value, str) or SHA256_RE.fullmatch(value) is None
            for value in auth_hashes.values()
        ):
            raise PublicationIntegrityError(
                "publish authorization artifact hash set is malformed"
            )
        approved_by = authorization.get("approved_by")
        if not isinstance(approved_by, str) or not approved_by.strip():
            raise PublicationIntegrityError("publish authorization lacks approved_by")
        nonce = authorization.get("nonce")
        if (
            not isinstance(nonce, str)
            or re.fullmatch(r"[0-9a-f]{32,128}", nonce) is None
        ):
            raise PublicationIntegrityError("publish authorization nonce is malformed")
        issued = parse_utc(authorization.get("issued_at"), field="authorization issued_at")
        expires = parse_utc(
            authorization.get("expires_at"), field="authorization expires_at"
        )
        if expires <= issued:
            raise PublicationIntegrityError("authorization expiry must follow issuance")
        ttl = (expires - issued).total_seconds()
        maximum = require_plain_int(
            policy.get("max_authorization_ttl_seconds"),
            field="max_authorization_ttl_seconds",
            minimum=1,
        )
        if ttl > maximum:
            raise PublicationIntegrityError("publish authorization TTL exceeds policy")
        if issued > clock.replace(microsecond=0) and (issued - clock).total_seconds() > 30:
            raise PublicationIntegrityError("publish authorization is future-issued")
        if expires <= clock:
            raise PublicationIntegrityError("publish authorization has expired")
    except PublicationIntegrityError as exc:
        errors.append(str(exc))
    return errors


def consume_authorization_nonce(
    nonce: str,
    *,
    ledger_path: str | Path,
    repo: Path,
) -> None:
    require_safe_id(nonce, field="authorization nonce")
    path = Path(ledger_path).expanduser().absolute()
    if _path_is_inside(path, repo):
        raise PublicationIntegrityError("nonce ledger must be outside the repository")
    _walk_without_symlinks(path.parent)
    if path.exists() or path.is_symlink():
        _walk_without_symlinks(path)
    flags = (
        os.O_RDWR
        | os.O_CREAT
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        raise PublicationIntegrityError(f"cannot open nonce ledger: {exc}") from exc
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise PublicationIntegrityError("nonce ledger is not a regular file")
        if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
            raise PublicationIntegrityError(
                "nonce ledger must be publisher-owned with 0600 permissions"
            )
        if metadata.st_nlink != 1:
            raise PublicationIntegrityError(
                "nonce ledger must not have hard links"
            )
        fcntl.flock(fd, fcntl.LOCK_EX)
        os.lseek(fd, 0, os.SEEK_SET)
        existing = os.read(fd, max(metadata.st_size, 1) + 1_000_000).decode(
            "ascii", errors="strict"
        )
        consumed = {line.strip() for line in existing.splitlines() if line.strip()}
        if nonce in consumed:
            raise PublicationIntegrityError("publish authorization nonce was already used")
        os.lseek(fd, 0, os.SEEK_END)
        os.write(fd, (nonce + "\n").encode("ascii"))
        os.fsync(fd)
    finally:
        os.close(fd)


def _shell_tokens(command: str) -> list[str]:
    if not isinstance(command, str) or not command.strip():
        raise PublicationIntegrityError("tool command is missing")
    if "\x00" in command:
        raise PublicationIntegrityError("tool command contains NUL")
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError as exc:
        raise PublicationIntegrityError(
            f"tool command cannot be parsed safely: {exc}"
        ) from exc


def _segments(tokens: Sequence[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in SHELL_SEPARATORS or set(token) <= {";", "&", "|"}:
            if current:
                rows.append(current)
                current = []
        elif token not in {"(", ")"}:
            current.append(token)
    if current:
        rows.append(current)
    return rows


def _basename(token: str) -> str:
    return Path(token).name.lower()


def _git_subcommand(tokens: Sequence[str], start: int) -> tuple[str | None, dict[str, str]]:
    aliases: dict[str, str] = {}
    index = start + 1
    options_with_values = {
        "-C",
        "-c",
        "--git-dir",
        "--work-tree",
        "--namespace",
        "--config-env",
    }
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            index += 1
            break
        if token in options_with_values:
            if index + 1 >= len(tokens):
                return None, aliases
            value = tokens[index + 1]
            if token == "-c" and value.lower().startswith("alias.") and "=" in value:
                name, expansion = value.split("=", 1)
                aliases[name[6:].lower()] = expansion
            index += 2
            continue
        if token.startswith("-c") and len(token) > 2:
            value = token[2:]
            if value.lower().startswith("alias.") and "=" in value:
                name, expansion = value.split("=", 1)
                aliases[name[6:].lower()] = expansion
            index += 1
            continue
        if token.startswith(("-C", "--git-dir=", "--work-tree=", "--namespace=")):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token.lower(), aliases
    if index < len(tokens):
        return tokens[index].lower(), aliases
    return None, aliases


def _gh_subcommands(tokens: Sequence[str], start: int) -> tuple[str | None, str | None]:
    index = start + 1
    options_with_values = {"--repo", "-R", "--hostname"}
    while index < len(tokens):
        token = tokens[index]
        if token in options_with_values:
            index += 2
            continue
        if token.startswith(("--repo=", "--hostname=")):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        group = token.lower()
        action = tokens[index + 1].lower() if index + 1 < len(tokens) else None
        return group, action
    return None, None


def _inline_program_candidates(
    segment: Sequence[str],
    *,
    start: int,
    executable: str,
) -> tuple[list[str], bool]:
    """Return statically visible code strings accepted by common runtimes.

    Short options may be bundled (for example ``bash -lc`` or ``python -Bc``)
    and some runtimes accept long inline-code options.  The boolean is true
    when an inline-code marker is present but no following code can be
    identified, which is denied fail-closed by the caller.
    """

    marker_chars = {
        "bash": {"c"},
        "sh": {"c"},
        "zsh": {"c"},
        "dash": {"c"},
        "python": {"c"},
        "python3": {"c"},
        "node": {"e", "p"},
        "ruby": {"e"},
        "perl": {"e", "E"},
    }[executable]
    long_markers = {
        "node": {"--eval", "--print"},
    }.get(executable, set())
    candidates: list[str] = []
    malformed = False
    arguments = list(segment[start + 1 :])
    for offset, token in enumerate(arguments):
        next_token = arguments[offset + 1] if offset + 1 < len(arguments) else None
        if token == "--":
            break
        if token in long_markers:
            if next_token is None:
                malformed = True
            else:
                candidates.append(next_token)
            continue
        matched_long = False
        for marker in long_markers:
            prefix = marker + "="
            if token.startswith(prefix):
                value = token[len(prefix) :]
                if value:
                    candidates.append(value)
                else:
                    malformed = True
                matched_long = True
                break
        if matched_long or token.startswith("--") or not token.startswith("-"):
            continue
        bundle = token[1:]
        positions = [
            bundle.index(marker)
            for marker in marker_chars
            if marker in bundle
        ]
        if not positions:
            continue
        marker_position = min(positions)
        suffix = bundle[marker_position + 1 :]
        if suffix:
            candidates.append(suffix)
        if next_token is not None:
            candidates.append(next_token)
        elif not suffix:
            malformed = True
    return list(dict.fromkeys(candidates)), malformed


def classify_publication_command(command: str) -> tuple[bool, str]:
    """Return ``(deny, reason)`` for direct publication-capable shell forms.

    This is deliberately an over-approximation.  Credential isolation and a
    managed hook/network boundary remain mandatory because arbitrary programs
    can synthesize network requests that no shell-text parser can prove safe.
    """

    tokens = _shell_tokens(command)
    lowered = [token.lower() for token in tokens]
    if any(
        "git-receive-pack" in token
        or "git-send-pack" in token
        or _basename(token) == "git-push"
        or _basename(token) == "git-http-push"
        or _basename(token).startswith("git-remote-")
        for token in lowered
    ):
        return True, "direct Git transport publication is reserved for the external publisher"
    for segment in _segments(tokens):
        for index, token in enumerate(segment):
            executable = _basename(token)
            if executable == "git":
                subcommand, aliases = _git_subcommand(segment, index)
                if subcommand is None:
                    return True, "ambiguous Git command is denied fail-closed"
                if subcommand in {"push", "send-pack"}:
                    return True, "Git publication is reserved for the external publisher"
                if subcommand in aliases:
                    nested = f"git {aliases[subcommand]}"
                    denied, reason = classify_publication_command(nested)
                    if denied:
                        return True, reason
                if subcommand == "submodule":
                    try:
                        foreach_index = segment.index("foreach", index + 1)
                    except ValueError:
                        foreach_index = -1
                    if foreach_index >= 0 and foreach_index + 1 < len(segment):
                        denied, reason = classify_publication_command(
                            segment[foreach_index + 1]
                        )
                        if denied:
                            return True, reason
                if subcommand == "bisect" and "run" in segment[index + 1 :]:
                    run_index = segment.index("run", index + 1)
                    if run_index + 1 < len(segment):
                        denied, reason = classify_publication_command(
                            " ".join(segment[run_index + 1 :])
                        )
                        if denied:
                            return True, reason
                if "$" in subcommand or "`" in subcommand:
                    return True, "dynamic Git subcommand is denied fail-closed"
                if subcommand not in NON_PUBLISHING_GIT_SUBCOMMANDS:
                    return (
                        True,
                        "unknown or external Git subcommand is denied fail-closed",
                    )
            elif executable == "gh":
                group, action = _gh_subcommands(segment, index)
                read_only = {
                    ("auth", "status"),
                    ("pr", "view"),
                    ("pr", "list"),
                    ("pr", "status"),
                    ("pr", "checks"),
                    ("pr", "diff"),
                    ("repo", "view"),
                    ("repo", "list"),
                    ("run", "view"),
                    ("run", "list"),
                    ("run", "watch"),
                    ("workflow", "view"),
                    ("workflow", "list"),
                }
                if group == "api":
                    payload_flags = {
                        "-f",
                        "-F",
                        "--field",
                        "--raw-field",
                        "--input",
                    }
                    method_tokens: set[str] = set()
                    for position, value in enumerate(segment[index + 1 :], start=index + 1):
                        if position > index and segment[position - 1] in {
                            "-X",
                            "--method",
                        }:
                            method_tokens.add(value.upper())
                        elif value.startswith("--method="):
                            method_tokens.add(value.split("=", 1)[1].upper())
                        elif value.startswith("-X") and len(value) > 2:
                            method_tokens.add(value[2:].upper())
                    if (
                        any(
                            item in payload_flags
                            or (
                                item.startswith(("-f", "-F"))
                                and len(item) > 2
                            )
                            or item.startswith(
                                (
                                    "--field=",
                                    "--raw-field=",
                                    "--input=",
                                )
                            )
                            for item in segment[index + 1 :]
                        )
                        or method_tokens - {"GET"}
                    ):
                        return True, "mutating gh api is reserved for the external publisher"
                    continue
                if (group, action) not in read_only:
                    return True, "non-read-only gh command is denied fail-closed"
            elif executable in {"hub"}:
                return True, "hub mutation is reserved for the external publisher"
            elif executable in {"curl", "wget"}:
                if any(
                    "api.github.com" in value.lower()
                    or re.search(r"github\\.com/.+/(pulls|issues|releases)", value.lower())
                    for value in segment[index + 1 :]
                ):
                    return True, "direct GitHub API command is denied fail-closed"
            elif executable in {
                "bash",
                "sh",
                "zsh",
                "dash",
                "python",
                "python3",
                "node",
                "ruby",
                "perl",
            }:
                nested_candidates, malformed = _inline_program_candidates(
                    segment,
                    start=index,
                    executable=executable,
                )
                if malformed:
                    return True, "ambiguous inline program is denied fail-closed"
                for nested in nested_candidates:
                    if nested == command:
                        return True, "recursive inline program is denied fail-closed"
                    denied, reason = classify_publication_command(nested)
                    if denied:
                        return True, reason
            elif executable == "eval" and index + 1 < len(segment):
                denied, reason = classify_publication_command(segment[index + 1])
                if denied:
                    return True, reason
    return False, ""


def classify_github_tool(tool_name: object, tool_input: object) -> tuple[bool, str]:
    if not isinstance(tool_name, str):
        return False, ""
    lowered = tool_name.lower()
    if "github" not in lowered and "pull_request" not in lowered and "pullrequest" not in lowered:
        return False, ""
    read_markers = ("get", "list", "search", "view", "read", "status", "diff", "checks")
    mutation_markers = (
        "create",
        "update",
        "edit",
        "merge",
        "close",
        "reopen",
        "ready",
        "review",
        "comment",
        "delete",
        "publish",
    )
    if any(marker in lowered for marker in mutation_markers):
        return True, "GitHub mutation tool is reserved for the external publisher"
    if any(marker in lowered for marker in read_markers):
        return False, ""
    if isinstance(tool_input, Mapping):
        action = str(tool_input.get("action") or tool_input.get("method") or "").lower()
        if action in {"get", "list", "search", "view", "read", "status"}:
            return False, ""
    return True, "unknown GitHub tool is denied fail-closed"


def extract_provider_tool(
    payload: Mapping[str, Any], *, provider: str
) -> tuple[str | None, str | None, object]:
    if provider in {"codex", "claude"}:
        tool_name = payload.get("tool_name")
        tool_input = payload.get("tool_input")
        if not isinstance(tool_name, str) or not tool_name:
            raise PublicationIntegrityError(
                f"{provider} hook payload is missing its documented tool_name"
            )
        if not isinstance(tool_input, Mapping):
            raise PublicationIntegrityError(
                f"{provider} hook payload is missing its documented tool_input object"
            )
        command = tool_input.get("command") if isinstance(tool_input, Mapping) else None
        return (
            tool_name,
            str(command) if isinstance(command, str) else None,
            tool_input,
        )
    if provider == "antigravity":
        has_current_envelope = "toolCall" in payload
        has_legacy_envelope = "tool_args" in payload or "tool_name" in payload
        if has_current_envelope and has_legacy_envelope:
            raise PublicationIntegrityError(
                "Antigravity hook payload mixes current and legacy envelopes"
            )
        if has_current_envelope:
            tool_call = payload.get("toolCall")
            if not isinstance(tool_call, Mapping):
                raise PublicationIntegrityError(
                    "Antigravity hook payload toolCall is not an object"
                )
            tool_name = tool_call.get("name")
            arguments = tool_call.get("args")
        elif has_legacy_envelope:
            # Google's secure-agentic-coding codelab documents the older
            # top-level tool_args.CommandLine envelope. The PreToolUse matcher
            # already scopes this adapter to run_command, so a missing legacy
            # tool_name is normalized to that matched tool.
            tool_name = payload.get("tool_name", "run_command")
            arguments = payload.get("tool_args")
        else:
            raise PublicationIntegrityError(
                "Antigravity hook payload has no recognized tool-call envelope"
            )
        if not isinstance(tool_name, str) or not tool_name:
            raise PublicationIntegrityError(
                "Antigravity hook payload is missing its documented tool name"
            )
        if not isinstance(arguments, Mapping):
            raise PublicationIntegrityError(
                "Antigravity hook payload is missing its documented arguments object"
            )
        command = arguments.get("CommandLine")
        return (
            tool_name,
            str(command) if isinstance(command, str) else None,
            arguments,
        )
    raise PublicationIntegrityError(f"unknown provider adapter: {provider}")


def classify_provider_payload(
    payload: Mapping[str, Any], *, provider: str
) -> tuple[bool, str]:
    try:
        tool_name, command, tool_input = extract_provider_tool(
            payload, provider=provider
        )
    except PublicationIntegrityError as exc:
        return True, str(exc)
    is_github_tool = isinstance(tool_name, str) and (
        "github" in tool_name.lower()
        or "pull_request" in tool_name.lower()
        or "pullrequest" in tool_name.lower()
    )
    if is_github_tool:
        return classify_github_tool(tool_name, tool_input)
    shell_tool = (
        tool_name in {"Bash", "bash", "run_command"}
        or (isinstance(tool_name, str) and tool_name.lower().endswith("exec_command"))
    )
    if shell_tool:
        if command is None:
            return True, "shell tool input is missing its documented command field"
        try:
            return classify_publication_command(command)
        except PublicationIntegrityError as exc:
            return True, str(exc)
    return True, "unsupported provider tool is denied fail-closed"
