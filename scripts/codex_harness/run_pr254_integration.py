#!/usr/bin/env python3
"""Portable latest-target integration entry point for PR-254."""

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (
    REPO,
    REPO / "htt/src",
    REPO / "htt",
    REPO / "research_gates/pr04/src",
)


def _activate_source_layout() -> None:
    resolved = [str(path) for path in SOURCE_PATHS]
    sys.path[:] = resolved + [
        entry for entry in sys.path if entry not in resolved
    ]


def _run_focused() -> int:
    import pytest

    return int(
        pytest.main(
            [
                "-p",
                "no:cacheprovider",
                "-q",
                str(REPO / "htt/src/common/test_anchor_geometry.py"),
                str(
                    REPO
                    / "tests/pr_cards/"
                    "test_pr_254_normalizer_anchor_geometry.py"
                ),
            ]
        )
    )


def _run_unittest_suite(directory: str, pattern: str) -> int:
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(REPO / directory),
        pattern=pattern,
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=("focused", "counterexample", "benchmark", "pr04", "pr07"),
    )
    args = parser.parse_args(argv)
    _activate_source_layout()

    if args.mode == "focused":
        return _run_focused()
    if args.mode == "counterexample":
        from scripts.codex_harness.run_pr254_counterexamples import (
            main as counterexample_main,
        )

        return counterexample_main(["--check"])
    if args.mode == "benchmark":
        from scripts.codex_harness.run_pr254_normalizer_benchmark import (
            main as benchmark_main,
        )

        return benchmark_main(["--check"])
    if args.mode == "pr04":
        return _run_unittest_suite(
            "research_gates/pr04/tests",
            "test_pr04_*.py",
        )
    return _run_unittest_suite(
        "research_gates/pr07/tests",
        "test_pr07_*.py",
    )


if __name__ == "__main__":
    raise SystemExit(main())
