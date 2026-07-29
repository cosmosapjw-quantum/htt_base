#!/usr/bin/env python3
"""Portable focused and adjacent integration runner for PR-255."""

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
    REPO / "research_gates/pr04/src",
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
    os.environ["PR255_INTEGRATION_ACTIVE"] = "1"


def _pytest(paths: tuple[str, ...]) -> int:
    import pytest

    return int(
        pytest.main(
            [
                "-p",
                "no:cacheprovider",
                "-q",
                *(str(REPO / path) for path in paths),
            ]
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=("focused", "benchmark", "adjacent", "claim", "common"),
    )
    args = parser.parse_args(argv)
    _activate_source_layout()
    if args.mode == "focused":
        return _pytest(
            (
                "htt/src/common/test_anchored_response_geometry.py",
                "tests/pr_cards/test_pr_255_anchored_response_geometry.py",
            )
        )
    if args.mode == "benchmark":
        from scripts.codex_harness.run_pr255_response_geometry_benchmark import (
            main as benchmark_main,
        )

        return benchmark_main([])
    if args.mode == "adjacent":
        return _pytest(
            (
                "tests/htt/test_mes_information_gain.py",
                "tests/pr_cards/test_pr_251_orbit_nonlinearity.py",
                "tests/pr_cards/test_pr_254_normalizer_anchor_geometry.py",
                "tests/pr_cards/test_pr_255_anchored_response_geometry.py",
            )
        )
    if args.mode == "claim":
        return _pytest(
            (
                "tests/contracts/test_claim_language_lint.py",
                "tests/contracts/test_artifact_manifest.py",
                "tests/result_packs/test_pack_A.py",
            )
        )
    return _pytest(
        tuple(
            path.relative_to(REPO).as_posix()
            for path in sorted((REPO / "htt/src/common").glob("test_*.py"))
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
