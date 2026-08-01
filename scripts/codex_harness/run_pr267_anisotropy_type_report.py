#!/usr/bin/env python3
"""Portable focused, adjacent, and smoke runner for PR-267."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (REPO, REPO / "htt/src", REPO / "htt")
FOCUSED_TESTS = ("tests/contracts/test_anisotropy_type_report.py",)
ADJACENT_TESTS = (
    "htt/src/common/test_anchored_response_geometry.py",
    "tests/pr_cards/test_pr_256_velocity_frame_decomposition.py",
    "tests/pr_cards/test_pr_258_open_set_response_classes.py",
    "tests/contracts/test_orbit_catalogue_v3.py",
    "tests/contracts/test_conditional_exceedance.py",
    "tests/contracts/test_depth_path.py",
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
    os.environ["PR267_ANISOTROPY_TYPE_REPORT_RUNNER_ACTIVE"] = "1"


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
    parser.add_argument("mode", choices=("focused", "adjacent", "smoke"))
    args = parser.parse_args(argv)
    _activate_source_layout()
    if args.mode == "focused":
        return _pytest(FOCUSED_TESTS)
    if args.mode == "adjacent":
        return _pytest(ADJACENT_TESTS)
    import pytest

    return int(pytest.main(["-p", "no:cacheprovider", "-q", "-m", "smoke"]))


if __name__ == "__main__":
    raise SystemExit(main())
