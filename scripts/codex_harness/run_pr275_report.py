#!/usr/bin/env python3
"""Portable focused/adjacent/smoke runner for PR-275."""

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
    parser.add_argument("mode", choices=("focused", "adjacent", "smoke"))
    args = parser.parse_args(argv)
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
        return _run(common + ["tests/contracts/test_vector_tensor_report.py"])
    if args.mode == "adjacent":
        return _run(
            common
            + [
                "tests/contracts/test_theorem_signatures_v3.py",
                "tests/contracts/test_pillar_t_core.py",
                "tests/contracts/test_pillar_t_cas.py",
                "tests/contracts/test_pillar_s_core.py",
                "tests/contracts/test_pillar_s_inference.py",
                "tests/integration/test_vector_tensor_blind_synthetic.py",
                "tests/contracts/test_vector_tensor_data_admission.py",
            ]
        )
    return _run(common + ["-m", "smoke"])


if __name__ == "__main__":
    raise SystemExit(main())
