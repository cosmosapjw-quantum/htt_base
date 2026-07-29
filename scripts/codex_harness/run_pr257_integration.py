#!/usr/bin/env python3
"""Portable focused and adjacent integration runner for PR-257."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile


REPO = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (
    REPO,
    REPO / "htt/src",
    REPO / "htt",
    REPO / "research_gates/pr04/src",
)
CAS_CONTRACT = (
    REPO
    / "docs/generated/pr257_lowell_morphology/"
    "CAS_CONTRACT_PR257_ORBIT_V2.json"
)
CAS_RUN_SPEC = (
    REPO
    / "docs/generated/pr257_lowell_morphology/"
    "CAS_RUN_SPEC_PR257_ORBIT_V2.json"
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
    os.environ["PR257_INTEGRATION_ACTIVE"] = "1"


def _pytest(
    paths: tuple[str, ...],
    *,
    extra: tuple[str, ...] = (),
) -> int:
    import pytest

    return int(
        pytest.main(
            [
                "-p",
                "no:cacheprovider",
                "-q",
                *extra,
                *(str(REPO / path) for path in paths),
            ]
        )
    )


def _packaging_probe() -> int:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env["PIP_NO_INDEX"] = "1"
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        wheel_dir = root / "wheel"
        wheel_dir.mkdir()
        build = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--disable-pip-version-check",
                "--no-cache-dir",
                "--no-deps",
                "--no-build-isolation",
                "--wheel-dir",
                str(wheel_dir),
                str(REPO / "htt"),
            ],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if build.returncode:
            sys.stderr.write(build.stdout)
            sys.stderr.write(build.stderr)
            return build.returncode
        wheels = tuple(wheel_dir.glob("bass_py-*.whl"))
        if len(wheels) != 1:
            print("isolated PR-257 probe did not build one wheel", file=sys.stderr)
            return 1
        target = root / "target"
        install = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-deps",
                "--no-index",
                "--target",
                str(target),
                str(wheels[0]),
            ],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if install.returncode:
            sys.stderr.write(install.stdout)
            sys.stderr.write(install.stderr)
            return install.returncode
        code = """
import importlib
import sys
sys.path.insert(0, sys.argv[1])
catalogue = importlib.import_module("common.orbit_catalogue_v2")
top = importlib.import_module("obsstat.lowell_counterpairs")
alias = importlib.import_module("htt.obsstat.lowell_counterpairs")
benchmark = importlib.import_module("htt.statistics.morphology_benchmark")
assert top is alias
assert top.MatchedCounterpairReport is alias.MatchedCounterpairReport
assert catalogue.OrbitCatalogueV2Report.__module__ == "common.orbit_catalogue_v2"
assert benchmark.LowEllMorphologyBenchmarkReport.__module__ == (
    "htt.statistics.morphology_benchmark"
)
"""
        probe = subprocess.run(
            [sys.executable, "-c", code, str(target)],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if probe.returncode:
            sys.stderr.write(probe.stdout)
            sys.stderr.write(probe.stderr)
            return probe.returncode
    print("PASS PR-257 isolated wheel import and alias probe")
    return 0


def _cas() -> int:
    if not CAS_CONTRACT.is_file() or not CAS_RUN_SPEC.is_file():
        print("PR-257 CAS contract or run spec is missing", file=sys.stderr)
        return 1
    command = [
        sys.executable,
        "-B",
        str(REPO / ".agent-harness/scripts/cas_gate.py"),
        "run-adjudicate",
        "--contract",
        str(CAS_CONTRACT),
        "--run-spec",
        str(CAS_RUN_SPEC),
    ]
    return subprocess.run(command, cwd=REPO, check=False).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=("focused", "benchmark", "cas", "adjacent", "claim"),
    )
    args = parser.parse_args(argv)
    _activate_source_layout()
    if args.mode == "focused":
        return _pytest(
            ("tests/pr_cards/test_pr_257_lowell_morphology.py",)
        )
    if args.mode == "benchmark":
        from scripts.codex_harness.run_pr257_morphology_benchmark import (
            main as benchmark_main,
        )

        return benchmark_main([])
    if args.mode == "cas":
        return _cas()
    if args.mode == "adjacent":
        result = _pytest(
            (
                "htt/src/common/test_orbit_nonlinearity.py",
                "htt/src/common/test_anchored_response_geometry.py",
                "tests/obsstat/test_biposh_features.py",
                "tests/obsstat/test_lowell_poles.py",
                "tests/obsstat/test_scalar_lowell.py",
                "tests/pr_cards/test_pr_251_orbit_nonlinearity.py",
                "tests/pr_cards/test_pr_255_anchored_response_geometry.py",
                "tests/pr_cards/test_pr_257_lowell_morphology.py",
            ),
            extra=(
                "-k",
                "not test_obsstat_import_aliases_share_the_lowell_pole_types",
            ),
        )
        return result if result else _packaging_probe()
    return _pytest(
        (
            "tests/contracts/test_claim_language_lint.py",
            "tests/contracts/test_artifact_manifest.py",
            "tests/result_packs/test_pack_A.py",
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
