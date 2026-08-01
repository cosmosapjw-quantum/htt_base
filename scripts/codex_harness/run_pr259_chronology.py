#!/usr/bin/env python3
"""Portable focused and smoke runner for PR-259 chronology repair."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (
    REPO,
    REPO / "htt/src",
    REPO / "htt",
)
FOCUSED_TESTS = (
    "tests/contracts/test_pr124_cas_lineage.py",
    "tests/contracts/test_mes_successor_registry.py",
    "tests/contracts/test_pr259_review_policy.py",
)


def _activate_source_layout() -> None:
    resolved = [str(path) for path in SOURCE_PATHS]
    sys.path[:] = resolved + [
        entry for entry in sys.path if entry not in resolved
    ]
    existing = [
        entry
        for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep)
        if entry and entry not in resolved
    ]
    os.environ["PYTHONPATH"] = os.pathsep.join((*resolved, *existing))
    os.environ["PR259_CHRONOLOGY_RUNNER_ACTIVE"] = "1"


def _pytest(mode: str) -> int:
    import pytest

    arguments = ["-p", "no:cacheprovider", "-q"]
    if mode == "focused":
        arguments.extend(str(REPO / path) for path in FOCUSED_TESTS)
    else:
        arguments.extend(("-m", "smoke"))
    return int(pytest.main(arguments))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("focused", "smoke"))
    args = parser.parse_args(argv)
    _activate_source_layout()
    return _pytest(args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
