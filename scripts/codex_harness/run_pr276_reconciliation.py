#!/usr/bin/env python3
"""Portable focused, collection, and smoke runner for PR-276."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    source_paths = [str(ROOT / "htt/src"), str(ROOT / "htt")]
    existing = environment.get("PYTHONPATH")
    if existing:
        source_paths.append(existing)
    environment["PYTHONPATH"] = os.pathsep.join(source_paths)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["MPLBACKEND"] = "Agg"
    return environment


def _run(arguments: list[str]) -> int:
    completed = subprocess.run(
        arguments,
        cwd=ROOT,
        env=_environment(),
        check=False,
    )
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("probe", "focused", "collect", "smoke"))
    args = parser.parse_args(argv)
    if args.mode == "probe":
        return _run(
            [
                sys.executable,
                "-B",
                "-c",
                (
                    "from pathlib import Path; import common, bass, htt; "
                    "root=Path.cwd().resolve(); "
                    "paths=[Path(module.__file__).resolve() for module in "
                    "(common, bass, htt)]; "
                    "assert all(path.is_relative_to(root) for path in paths); "
                    "print('source-layout-ok')"
                ),
            ]
        )
    common = [
        sys.executable,
        "-B",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "-q",
    ]
    if args.mode == "focused":
        return _run(
            common
            + [
                "tests/pr_cards/test_pr_276_post275_reconciliation.py",
                "tests/pr_cards/test_pr_276_attended_publication.py",
                "tests/contracts/test_status_snapshot.py",
                "tests/contracts/test_vector_tensor_program_dag.py",
                "tests/contracts/test_pr119_long_horizon_intake.py",
            ]
        )
    if args.mode == "collect":
        return _run(common + ["--collect-only"])
    return _run(common + ["-m", "smoke"])


if __name__ == "__main__":
    raise SystemExit(main())
