#!/usr/bin/env python3
"""Portable focused, adjacent, and smoke runner for PR-272."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (REPO, REPO / "htt/src", REPO / "htt")
FOCUSED_TESTS = ("tests/contracts/test_pillar_s_inference.py",)
ADJACENT_TESTS = (
    "tests/contracts/test_pillar_s_core.py",
    "tests/contracts/test_conditional_exceedance.py",
    "tests/contracts/test_depth_path.py",
    "tests/contracts/test_anisotropy_type_report.py",
    "tests/pr_cards/test_pr_258_open_set_response_classes.py",
    "tests/contracts/test_pr137_weak_id_coverage.py",
    "tests/contracts/test_pr138_sbc_ppc.py",
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
    os.environ["PR272_PILLAR_S_INFERENCE_RUNNER_ACTIVE"] = "1"


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
