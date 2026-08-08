#!/usr/bin/env python3
"""Portable focused and historical-replay runner for PR-281."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (REPO, REPO / "htt/src", REPO / "htt")
TESTS = {
    "focused": ("tests/contracts/test_orbit_type_acceptance.py",),
    "adjacent": (
        "tests/contracts/test_joint_anisotropy_state.py",
        "tests/contracts/test_orbit_catalogue_v3.py",
        "tests/contracts/test_anisotropy_type_report.py",
        "tests/pr_cards/test_pr_255_anchored_response_geometry.py",
    ),
    "pr269-replay": ("tests/contracts/test_pillar_t_core.py",),
    "pr273-replay": (
        "tests/integration/test_vector_tensor_blind_synthetic.py",
    ),
}


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
    os.environ["PR281_ORBIT_TYPE_ACCEPTANCE_RUNNER_ACTIVE"] = "1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=tuple(TESTS))
    args = parser.parse_args(argv)
    _activate_source_layout()
    import pytest

    return int(
        pytest.main(
            [
                "-p",
                "no:cacheprovider",
                "-q",
                *(str(REPO / path) for path in TESTS[args.mode]),
            ]
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
