#!/usr/bin/env python3
"""Fail-closed byte-determinism check for the committed PR-315 projection."""

from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import sys
from typing import Mapping, Sequence


FROZEN_SCIENTIFIC_PROJECTION_SHA256 = (
    "sha256:8b0aadf1897703f32c0904ad6cc6f5db41766c896382f21e709a6cd212d81750"
)
FROZEN_FEATURE_PACKAGE_SHA256 = (
    "sha256:b262425eb4f3a879513c02644bcbdd3ab313e487d101f6a29cb85284c30f845b"
)
CANONICAL_PYTHON = "3.12.14"
CANONICAL_PACKAGES = {
    "numpy": "2.5.2",
    "scipy": "1.18.1",
    "healpy": "1.19.0",
    "threadpoolctl": "3.6.0",
}
CANONICAL_ENV = {
    "LANG": "C",
    "LC_ALL": "C",
    "PYTHONHASHSEED": "0",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
    "OPENBLAS_CORETYPE": "Haswell",
}


def _startup_environment_failures() -> list[str]:
    mismatches = {
        key: {"expected": expected, "actual": os.environ.get(key)}
        for key, expected in CANONICAL_ENV.items()
        if os.environ.get(key) != expected
    }
    failures = []
    if mismatches:
        failures.append(f"canonical startup environment drifted: {mismatches}")
    if platform.machine().lower() not in {"x86_64", "amd64"}:
        failures.append("PR-315 V1 byte replay is defined only for x86-64")
    return failures


STARTUP_FAILURES = _startup_environment_failures()

# NumPy is imported after the environment snapshot so a drifted run can still
# emit its complete projection preimage while remaining a fail-closed result.
import numpy as np  # noqa: E402
from threadpoolctl import threadpool_info  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "htt", ROOT / "htt/src", ROOT / "htt/htt"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))
from scripts.observed_runs import run_planck_pr3 as worker  # noqa: E402


def _canonical_bytes(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _openblas_state() -> tuple[list[dict[str, object]], str | None]:
    rows = [
        {
            "prefix": str(item.get("prefix")),
            "version": str(item.get("version")),
            "architecture": str(item.get("architecture")),
            "num_threads": int(item.get("num_threads", -1)),
        }
        for item in threadpool_info()
        if item.get("internal_api") == "openblas"
    ]
    rows.sort(
        key=lambda row: (
            str(row["prefix"]),
            str(row["version"]),
            str(row["architecture"]),
            int(row["num_threads"]),
        )
    )
    if not rows or any(
        row["architecture"].casefold() != "haswell" or row["num_threads"] != 1
        for row in rows
    ):
        return rows, f"OpenBLAS dispatch contract drifted: {rows}"
    return rows, None


def _projection(package: Path) -> dict[str, object]:
    with np.load(package, allow_pickle=False) as bundle:
        observed = np.asarray(bundle["observed_features"], dtype=float)
        nulls = np.asarray(bundle["null_features"], dtype=float)
        row_ids = tuple(str(value) for value in bundle["row_ids"].tolist())
    diagnostic = worker.analyze_smica_feature_rows(
        observed_features=observed,
        null_features=nulls,
        row_ids=row_ids,
    )
    return worker._pr315_feature_scientific_projection(diagnostic)


def run(package: Path, metadata: Path, output: Path) -> int:
    expected = json.loads(metadata.read_text(encoding="ascii"))[
        "scientific_projection_sha256"
    ]
    projection = _projection(package)
    preimage = _canonical_bytes(projection)
    actual = "sha256:" + hashlib.sha256(preimage).hexdigest()

    failures = list(STARTUP_FAILURES)
    if expected != FROZEN_SCIENTIFIC_PROJECTION_SHA256:
        failures.append(
            "frozen scientific projection receipt changed: "
            f"expected {FROZEN_SCIENTIFIC_PROJECTION_SHA256}, metadata {expected}"
        )
    if actual != expected:
        failures.append(
            f"scientific projection hash drifted: expected {expected}, actual {actual}"
        )

    package_sha256 = _sha256_file(package)
    if package_sha256 != FROZEN_FEATURE_PACKAGE_SHA256:
        failures.append(
            "frozen feature package changed: "
            f"expected {FROZEN_FEATURE_PACKAGE_SHA256}, actual {package_sha256}"
        )

    try:
        replay = worker.replay_pr315_feature_package(
            package_path=package,
            metadata_path=metadata,
        )
    except worker.PlanckWorkerError as exc:
        replay = None
        failures.append(f"exact replay rejected the package: {exc}")

    openblas, openblas_failure = _openblas_state()
    if openblas_failure is not None:
        failures.append(openblas_failure)
    if replay is not None and replay["raw_maps_reopened"] is not False:
        failures.append("portable replay reopened raw maps")

    python_version = platform.python_version()
    package_versions = {name: version(name) for name in CANONICAL_PACKAGES}
    if python_version != CANONICAL_PYTHON:
        failures.append(
            f"Python version drifted: expected {CANONICAL_PYTHON}, "
            f"actual {python_version}"
        )
    for name, expected_version in CANONICAL_PACKAGES.items():
        actual_version = package_versions[name]
        if actual_version != expected_version:
            failures.append(
                f"{name} version drifted: expected {expected_version}, "
                f"actual {actual_version}"
            )

    payload: dict[str, object] = {
        "format": "PLANCK_PR315_PORTABLE_DETERMINISM_CHECK_V1",
        "status": "PASS" if not failures else "FAIL",
        "frozen_scientific_projection_sha256": (
            FROZEN_SCIENTIFIC_PROJECTION_SHA256
        ),
        "expected_scientific_projection_sha256": expected,
        "actual_scientific_projection_sha256": actual,
        "scientific_projection_preimage_ascii": preimage.decode("ascii"),
        "scientific_projection_preimage_byte_size": len(preimage),
        "scientific_projection": projection,
        "frozen_feature_package_sha256": FROZEN_FEATURE_PACKAGE_SHA256,
        "feature_package_sha256": package_sha256,
        "feature_metadata_file_sha256": _sha256_file(metadata),
        "raw_maps_reopened": False if replay is None else replay["raw_maps_reopened"],
        "runtime": {
            "machine": platform.machine().lower(),
            "python": python_version,
            "packages": package_versions,
            "environment": dict(CANONICAL_ENV),
            "openblas": openblas,
        },
    }
    if failures:
        payload["failures"] = failures

    raw = _canonical_bytes(payload) + b"\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    sys.stdout.buffer.write(raw)
    return 0 if payload["status"] == "PASS" else 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    return run(args.package, args.metadata, args.output)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, ValueError, RuntimeError, worker.PlanckWorkerError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(2)
