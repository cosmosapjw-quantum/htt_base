#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HTT_SRC = REPO_ROOT / "htt" / "src"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "generated" / "optional_dependency_status.md"

if str(HTT_SRC) not in sys.path:
    sys.path.insert(0, str(HTT_SRC))

from common.optional_dependencies import (  # noqa: E402
    OPTIONAL_DEPENDENCIES,
    dependency_statuses,
)


def _repo_relative(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip()


def _worktree_state() -> str:
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return "unknown"
    return "dirty" if completed.stdout.strip() else "clean"


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _config_hash() -> str:
    hasher = hashlib.sha256()
    for path in (
        REPO_ROOT / "scripts" / "codex_harness" / "optional_dep_report.py",
        REPO_ROOT / "htt" / "src" / "common" / "optional_dependencies.py",
        REPO_ROOT / "htt" / "conftest.py",
        REPO_ROOT / "pytest.ini",
        REPO_ROOT / "htt" / "pytest.ini",
        REPO_ROOT / "htt" / "pyproject.toml",
    ):
        hasher.update(_repo_relative(path).encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(path.read_bytes())
        hasher.update(b"\0")
    return hasher.hexdigest()


def _input_hash_rows() -> list[str]:
    paths = (
        REPO_ROOT / "scripts" / "codex_harness" / "optional_dep_report.py",
        REPO_ROOT / "htt" / "src" / "common" / "optional_dependencies.py",
        REPO_ROOT / "htt" / "conftest.py",
        REPO_ROOT / "pytest.ini",
        REPO_ROOT / "htt" / "pytest.ini",
        REPO_ROOT / "htt" / "pyproject.toml",
    )
    return [f"- {_repo_relative(path)}: `{_file_sha256(path)}`" for path in paths]


def render_report(*, command: str) -> str:
    statuses = dependency_statuses()
    status_by_key = {status.key: status for status in statuses}
    lines = [
        "# Optional Dependency Status",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        "transfer_source: none",
        "sky_support_status: not_directional",
        "null_mock_status: not_statistical",
        f"config_hash: `{_config_hash()}`",
        "input_hashes:",
        *_input_hash_rows(),
        "caveats:",
        "- Machine-local availability records harness provenance only.",
        "- Missing optional dependencies are skip causes or documented blockers, not passes.",
        "- This report is not scientific readiness evidence.",
        f"generating_command: {command}",
        f"python_executable: {sys.executable}",
        f"git_commit: {_git_commit()}",
        f"worktree_state: {_worktree_state()}",
        "",
        "## Dependency Registry",
        "",
        "| key | import | status | policy | pytest marker | owner | attribution | explanation |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for dependency in OPTIONAL_DEPENDENCIES:
        status = status_by_key[dependency.key]
        marker = status.pytest_marker or "none"
        attribution = "<br>".join(status.attribution_paths) or "none"
        lines.append(
            "| "
            f"{status.key} | "
            f"{status.import_name} | "
            f"{status.status} | "
            f"{status.missing_policy} | "
            f"{marker} | "
            f"{status.owner} | "
            f"{attribution} | "
            f"{status.explanation} |"
        )
    lines.extend(
        [
            "",
            "## Skip Attribution",
            "",
            "- `requires_healpy` maps to `healpy` through the COMMON optional dependency registry.",
            "- `requires_dynesty` maps to `dynesty` through the COMMON optional dependency registry.",
            "- Registered skip markers use dependency-named reasons during pytest collection.",
            "- Existing `pytest.importorskip` gates remain the local test-level attribution for optional modules.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate the COMMON optional dependency status report."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Markdown report path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the target path and report without writing it",
    )
    args = parser.parse_args(argv)

    command = "python scripts/codex_harness/optional_dep_report.py"
    rendered = render_report(command=command)
    target = args.output if args.output.is_absolute() else REPO_ROOT / args.output

    if args.dry_run:
        print(f"COMMON optional dependency registry -> {_repo_relative(target)}")
        print(rendered)
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    print(f"wrote {_repo_relative(target)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
