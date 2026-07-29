#!/usr/bin/env python3
"""Portable focused and adjacent integration runner for PR-256."""

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
    os.environ["PR256_INTEGRATION_ACTIVE"] = "1"


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
        choices=("focused", "benchmark", "adjacent", "claim"),
    )
    args = parser.parse_args(argv)
    _activate_source_layout()
    if args.mode == "focused":
        return _pytest(
            (
                "htt/htt/tests/test_velocity_frame_decomposition.py",
                "tests/pr_cards/test_pr_256_velocity_frame_decomposition.py",
            )
        )
    if args.mode == "benchmark":
        from scripts.codex_harness.run_pr256_velocity_frame_benchmark import (
            main as benchmark_main,
        )

        return benchmark_main([])
    if args.mode == "adjacent":
        return _pytest(
            (
                "tests/htt/test_response_overlap.py",
                "tests/htt/test_local_global_mixture.py",
                "htt/htt/tests/test_ver2_local_global_discrimination.py",
                "tests/pr_cards/test_pr_222_revival.py",
                "tests/pr_cards/test_pr_251_orbit_nonlinearity.py",
                "tests/pr_cards/test_pr_255_anchored_response_geometry.py",
                "tests/pr_cards/test_pr_256_velocity_frame_decomposition.py",
            )
        )
    return _pytest(
        (
            "tests/contracts/test_claim_language_lint.py",
            "tests/contracts/test_artifact_manifest.py",
            "tests/result_packs/test_pack_A.py",
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
