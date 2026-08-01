#!/usr/bin/env python3
"""Portable focused, adjacent, and smoke runner for PR-268."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (REPO, REPO / "htt/src", REPO / "htt")
FOCUSED_TESTS = ("tests/contracts/test_theorem_signatures_v3.py",)
ADJACENT_TESTS = (
    "tests/contracts/test_vector_tensor_program_dag.py",
    (
        "tests/contracts/test_pr124_cas_lineage.py::"
        "test_theorem_inventory_honest_count_and_overstatement_kill"
    ),
    (
        "tests/contracts/test_pr124_cas_lineage.py::"
        "test_sanity_anchor_and_specification_never_count"
    ),
    (
        "tests/contracts/test_pr124_cas_lineage.py::"
        "test_successor_pointer_authorized_by_receipt_bytes_only"
    ),
    "tests/contracts/test_pr124_cas_lineage.py::test_frozen_modules_untouched",
    "tests/contracts/test_pr125_frame_contract.py",
    "tests/contracts/test_tensor_functionals.py",
    "tests/contracts/test_orbit_catalogue_v3.py",
    "tests/contracts/test_anisotropy_type_report.py",
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
    os.environ["PR268_THEOREM_REGISTRY_RUNNER_ACTIVE"] = "1"


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
