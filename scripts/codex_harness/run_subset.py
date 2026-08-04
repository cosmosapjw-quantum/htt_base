#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_VENV_PYTHON = REPO_ROOT / "venv" / "bin" / "python"
PROFILE_MANIFEST = (
    REPO_ROOT / "docs/research_program/post_pr275/harness_profiles_v4.yaml"
)
for _source_root in (REPO_ROOT / "htt/src", REPO_ROOT / "htt"):
    if str(_source_root) not in sys.path:
        sys.path.insert(0, str(_source_root))

from common.harness_profiles_v4 import load_profile_manifest  # noqa: E402


SUBSETS = frozenset({"collect", "fast", "package", "smoke"})


def default_python() -> str:
    if REPO_VENV_PYTHON.exists():
        return str(REPO_VENV_PYTHON)
    return sys.executable


def command_for(subset: str, *, python: str | None = None) -> list[str]:
    if subset not in SUBSETS:
        raise KeyError(subset)
    manifest = load_profile_manifest(PROFILE_MANIFEST, repo_root=REPO_ROOT)
    return manifest.profile(subset).pytest_command(python or default_python())


def print_subset_list(*, python: str | None = None) -> None:
    for name in sorted(SUBSETS):
        print(f"{name} {shlex.join(command_for(name, python=python))}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run deterministic htt_base pytest subsets from the repository root."
    )
    parser.add_argument("subset", nargs="?", help="subset name to run")
    parser.add_argument("--list", action="store_true", help="list available subsets")
    parser.add_argument("--dry-run", action="store_true", help="print command without running it")
    parser.add_argument(
        "--python",
        dest="python_executable",
        help="Python executable used for the pytest child process",
    )
    args = parser.parse_args(argv)

    if args.list or not args.subset:
        print_subset_list(python=args.python_executable)
        return 0

    try:
        command = command_for(args.subset, python=args.python_executable)
    except KeyError:
        print(f"unknown subset: {args.subset}", file=sys.stderr)
        return 2

    print(shlex.join(command), flush=True)
    if args.dry_run:
        return 0

    environment = dict(os.environ)
    for name in tuple(environment):
        if name.startswith("PYTEST_"):
            environment.pop(name, None)
    environment["PYTHONPATH"] = os.pathsep.join(
        str(path) for path in (REPO_ROOT / "htt/src", REPO_ROOT / "htt", REPO_ROOT / "htt/htt")
    )
    completed = subprocess.run(
        command, cwd=REPO_ROOT, env=environment, check=False
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
