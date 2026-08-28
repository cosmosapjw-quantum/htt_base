#!/usr/bin/env python3
"""Portable focused, benchmark, adjacent and claim runner for PR-258."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


REPO = Path(__file__).resolve().parents[2]
CLEANUP_BASE = "0864b00948143d9b19d4983e50fcd2d905f4a5d3"
SOURCE_PATHS = (
    REPO,
    REPO / "htt/src",
    REPO / "htt",
    REPO / "research_gates/pr04/src",
)
ARTIFACT = (
    REPO
    / "docs/generated/pr258_open_set_response_classes/"
    "open_set_benchmark.json"
)
HISTORICAL_HASHES = {
    "htt/src/common/revival_response_quotient.py": (
        "cc9802426d7af2eb29d77eef89f63e7eb3a220d935243c87fdf34ac757899d22"
    ),
    "docs/generated/pr219_result_card.json": (
        "a1615e4df9f59712d482b30be374874d66a480c97ba18a453838858aa45bc222"
    ),
    "docs/research_program/revival/pr219_spec.yaml": (
        "56a860c315e9c134b2d545c0fd0af6876f3c6b031d96c2fe5f50c32ede43650e"
    ),
    "docs/research_program/STAT_FOUNDATIONS_REVIEW_20260727.md": (
        "61a3ded47a9925cbddd620635c32c075d02eec2ca038824d440acc5f49e4c87a"
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
    os.environ["PR258_INTEGRATION_ACTIVE"] = "1"


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
            print("isolated PR-258 probe did not build one wheel", file=sys.stderr)
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
common = importlib.import_module("common.open_set_response_classes")
facade = importlib.import_module("htt.statistics.open_set_response_classes")
statistics = importlib.import_module("htt.statistics")
assert facade.ResponseClassManifoldSpec is common.ResponseClassManifoldSpec
assert statistics.ResponseEquivalenceClassReport is common.ResponseEquivalenceClassReport
assert facade.classify_open_set_response_batch is common.classify_open_set_response_batch
assert callable(facade.source_separation_gate_from_pr256)
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
    print("PASS PR-258 isolated wheel import and facade identity probe")
    return 0


def _historical_bytes() -> None:
    def source_bytes(path: str) -> bytes:
        live = REPO / path
        if live.is_file():
            return live.read_bytes()
        return subprocess.run(
            ["git", "show", f"{CLEANUP_BASE}:{path}"],
            cwd=REPO,
            capture_output=True,
            check=True,
        ).stdout

    observed = {
        path: hashlib.sha256(source_bytes(path)).hexdigest()
        for path in HISTORICAL_HASHES
    }
    if observed != HISTORICAL_HASHES:
        raise AssertionError(
            f"PR-258 changed historical PR-219/x_C authority: {observed}"
        )


def _claim_checks() -> int:
    if not ARTIFACT.is_file():
        print("PR-258 frozen benchmark is missing", file=sys.stderr)
        return 1
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    provenance = payload["provenance"]
    artifact_metadata = {
        "owner": "common",
        "scope": (
            "pre_native_finite_synthetic_response_library_software_validation"
        ),
        "artifact_mode": "internal_exploratory",
        "sky_support_status": "not_applicable_synthetic_feature_space",
        "null_mock_status": (
            "synthetic_generator_cells_only_not_observational_null_calibration"
        ),
        "covariance_status": (
            "fixed_registered_synthetic_covariance_exact_bytes"
        ),
    }
    if payload.get("schema") != "PR258_OPEN_SET_SYNTHETIC_BENCHMARK_V2":
        print("PR-258 artifact schema drifted", file=sys.stderr)
        return 1
    for key, expected in artifact_metadata.items():
        if payload.get(key) != expected or provenance.get(key) != expected:
            print(
                f"PR-258 artifact metadata {key} drifted",
                file=sys.stderr,
            )
            return 1
    for key in (
        "pr151_data_used",
        "observed_data_used",
        "old_rust_output_used",
        "native_solver_output_used",
    ):
        if provenance[key] is not False:
            print(f"PR-258 provenance flag {key} drifted", file=sys.stderr)
            return 1
    if provenance["transfer_source"] != "none":
        print("PR-258 imported a transfer provider", file=sys.stderr)
        return 1
    if payload["claim_tier_ceiling"] != "diagnostic_only":
        print("PR-258 machine claim tier drifted", file=sys.stderr)
        return 1
    benchmark_report = payload["benchmark_report"]
    protocol = payload["protocol"]
    if (
        benchmark_report.get("schema")
        != "PR258_OPEN_SET_BENCHMARK_REPORT_V3"
        or benchmark_report.get("maximum_mcse") != 0.0025
        or benchmark_report.get("minimum_replicates_per_cell") != 20_000
        or benchmark_report.get("maximum_replicates_per_cell") != 400_000
        or protocol.get("maximum_mcse") != 0.0025
        or protocol.get("minimum_replicates_per_cell") != 20_000
        or protocol.get("maximum_replicates_per_cell") != 400_000
    ):
        print(
            "PR-258 benchmark MC precision/cap contract drifted",
            file=sys.stderr,
        )
        return 1
    for key, expected in artifact_metadata.items():
        if benchmark_report.get(key) != expected:
            print(
                f"PR-258 benchmark report metadata {key} drifted",
                file=sys.stderr,
            )
            return 1
    required_perturbations = {
        "EXACT_DUPLICATE",
        "REFINEMENT",
        "EXPANSION",
        "CONTRACTION",
        "BOUNDARY_RESTRICTION",
    }
    rates = benchmark_report[
        "finite_support_perturbation_sensitivity_rates"
    ]
    bindings = payload["cell_equivalence_bindings"]
    perturbation_bindings = bindings["finite_support_perturbations"]
    if set(rates) != required_perturbations or set(
        perturbation_bindings
    ) != required_perturbations:
        print(
            "PR-258 benchmark omitted a registered support perturbation",
            file=sys.stderr,
        )
        return 1
    if (
        perturbation_bindings["EXACT_DUPLICATE"]
        != bindings["baseline_known_and_unknown"]
    ):
        print(
            "PR-258 exact duplicate changed baseline equivalence identity",
            file=sys.stderr,
        )
        return 1
    perturbation_receipts = payload["finite_support_perturbations"]
    if set(perturbation_receipts) != required_perturbations or any(
        not receipt.get("class_contract_ids")
        for receipt in perturbation_receipts.values()
    ):
        print(
            "PR-258 perturbations lack typed class-contract bindings",
            file=sys.stderr,
        )
        return 1
    nonduplicate_ids = {
        perturbation_bindings[kind]
        for kind in required_perturbations - {"EXACT_DUPLICATE"}
    }
    if (
        bindings["baseline_known_and_unknown"] in nonduplicate_ids
        or len(nonduplicate_ids) != len(required_perturbations) - 1
    ):
        print(
            "PR-258 non-duplicate perturbations reused baseline or each other",
            file=sys.stderr,
        )
        return 1
    banned_keys = {
        "family_probability",
        "family_posterior",
        "bayes_factor",
        "p_value",
        "e_value",
        "likelihood",
        "log_likelihood",
        "Q",
        "Pi",
        "F",
        "G_F",
        "native_geometry",
        "detected_family",
        "identified_family",
    }

    def keys(value: object):
        if isinstance(value, dict):
            for key, item in value.items():
                yield key
                yield from keys(item)
        elif isinstance(value, list):
            for item in value:
                yield from keys(item)

    found = banned_keys.intersection(keys(payload))
    if found:
        print(f"PR-258 emitted banned inference keys: {sorted(found)}", file=sys.stderr)
        return 1
    _historical_bytes()
    lint = subprocess.run(
        [
            sys.executable,
            "-B",
            str(REPO / "scripts/check_claim_language.py"),
            "--dry-run",
            str(REPO / "papers/planck_mes_first_observation"),
            "--format",
            "json",
        ],
        cwd=REPO,
        check=False,
    )
    return lint.returncode


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
            ("tests/pr_cards/test_pr_258_open_set_response_classes.py",)
        )
    if args.mode == "benchmark":
        from scripts.codex_harness.run_pr258_open_set_benchmark import (
            main as benchmark_main,
        )

        return benchmark_main([])
    if args.mode == "adjacent":
        result = _pytest(
            (
                "tests/pr_cards/test_pr_219_revival.py",
                "htt/src/common/test_anchored_response_geometry.py",
                "tests/pr_cards/test_pr_255_anchored_response_geometry.py",
                "tests/pr_cards/test_pr_256_velocity_frame_decomposition.py",
                "tests/pr_cards/test_pr_257_lowell_morphology.py",
                "tests/pr_cards/test_pr_258_open_set_response_classes.py",
            )
        )
        return result if result else _packaging_probe()
    return _claim_checks()


if __name__ == "__main__":
    raise SystemExit(main())
