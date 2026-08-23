#!/usr/bin/env python3
"""JWST-SN row/covariance worker and observation-free synthetic closure.

The admitted mode is reachable only through the attended single-lane executor
after ``start.json`` exists.  Synthetic profiling creates its own typed rows;
it accepts no admission or data root and never opens an observed payload.
"""

from __future__ import annotations

import os


THREAD_CONTROLS = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
}
for _name, _value in THREAD_CONTROLS.items():
    os.environ[_name] = _value

import argparse
import json
from pathlib import Path
import resource
import sys
import tempfile
import time
from typing import Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT / "htt", ROOT / "htt/src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from common.data_identity import (  # noqa: E402
    AdmissionStatus,
    DataIdentityError,
    _regular_beneath,
    _stream_sha256,
    load_lane_registry,
    replay_lane_admission_decision,
)
from obsstat.jwst_distance_consistency import (  # noqa: E402
    JWSTSNCurrentStackError,
    PR309_COMPETITOR_SEMANTIC_CONTRACTS,
    PR309_OBSERVABLE_CONTRACT,
    PR309_SEMANTIC_CONTRACT,
    analyze_pr309_current_stack,
    build_pr309_inputs,
)


REGISTRY = (
    ROOT / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
)
REQUIRED_COMPONENTS = frozenset(
    {
        "source_rows",
        "host_rows",
        "individual_errors",
        "covariance",
        "competitor_model",
    }
)


class JWSTSNWorkerError(RuntimeError):
    """Raised before a result when JWST-SN worker semantics drift."""


def _strict_json(path: Path, *, label: str) -> Mapping[str, object]:
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise JWSTSNWorkerError(f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str) -> object:
        raise JWSTSNWorkerError(f"{label} contains non-finite constant {value}")

    try:
        payload = json.loads(
            path.read_bytes(), object_pairs_hook=unique, parse_constant=reject_constant
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise JWSTSNWorkerError(f"{label} is not strict JSON") from exc
    if not isinstance(payload, Mapping):
        raise JWSTSNWorkerError(f"{label} must be a JSON object")
    return payload


def _load_admission(path: Path):
    try:
        registry = load_lane_registry(REGISTRY)
        decision = replay_lane_admission_decision(
            _strict_json(path, label="JWST-SN admission"), registry=registry
        )
    except (DataIdentityError, JWSTSNWorkerError) as exc:
        raise JWSTSNWorkerError(f"JWST-SN admission replay failed: {exc}") from exc
    if (
        decision.status is not AdmissionStatus.ADMITTED_IDENTITY_ONLY
        or decision.lane_id != "JWST_SN"
        or tuple(record.component_id for record in decision.records)
        != tuple(registry.lane("JWST_SN").expected_component_sequence)
        or decision.lane_admission_bundle_id is None
    ):
        raise JWSTSNWorkerError("JWST-SN admission is not complete identity admission")
    return decision


def _mark_observed_data_open_attempt() -> None:
    output_text = os.environ.get("HTT_ATTENDED_OUTPUT_DIR", "")
    output = Path(output_text)
    marker = output / "observed_data_opened.json"
    if (
        os.environ.get("HTT_ATTENDED_START_WRITTEN") != "1"
        or not output_text
        or not output.is_absolute()
        or output.is_symlink()
        or not output.is_dir()
        or not (output / "start.json").is_file()
        or os.environ.get("HTT_ATTENDED_DATA_OPEN_MARKER") != str(marker)
        or marker.exists()
        or marker.is_symlink()
    ):
        raise JWSTSNWorkerError("attended output/start/data-open binding is invalid")
    _write_json(marker, {"state": "OBSERVED_DATA_OPEN_ATTEMPTED"})


def _admitted_paths(decision, *, data_root: Path) -> dict[str, Path]:
    if (
        not data_root.is_absolute()
        or data_root.is_symlink()
        or not data_root.is_dir()
        or data_root.resolve() != data_root
    ):
        raise JWSTSNWorkerError("data root must be an absolute regular directory")
    bindings = decision.records[0].native_identity_profile.get("component_bindings")
    if not isinstance(bindings, Sequence) or len(bindings) != len(REQUIRED_COMPONENTS):
        raise JWSTSNWorkerError("JWST-SN native component bindings drifted")
    records = {record.component_id: record for record in decision.records}
    if set(records) != REQUIRED_COMPONENTS:
        raise JWSTSNWorkerError("JWST-SN admitted component inventory is incomplete")
    binding_rows = [
        binding
        for binding in bindings
        if isinstance(binding, Mapping)
    ]
    if (
        len(binding_rows) != len(bindings)
        or tuple(binding.get("component_id") for binding in binding_rows)
        != tuple(record.component_id for record in decision.records)
    ):
        raise JWSTSNWorkerError("JWST-SN component binding order drifted")
    result: dict[str, Path] = {}
    for binding in binding_rows:
        component = binding.get("component_id")
        relative = binding.get("relative_path")
        if component not in records or not isinstance(relative, str):
            raise JWSTSNWorkerError("JWST-SN component binding identity drifted")
        try:
            path, info = _regular_beneath(
                data_root, Path(relative), f"JWST-SN {component}"
            )
            digest = "sha256:" + _stream_sha256(
                path, field_name=f"JWST-SN {component}", expected_info=info
            )
        except DataIdentityError as exc:
            raise JWSTSNWorkerError(
                f"JWST-SN {component} is not an exact admitted file"
            ) from exc
        record = records[str(component)]
        if info.st_size != record.byte_size or digest != record.content_sha256:
            raise JWSTSNWorkerError(f"JWST-SN {component} no longer matches admission")
        result[str(component)] = path
    return result


def _load_inputs(paths: Mapping[str, Path]):
    if set(paths) != REQUIRED_COMPONENTS:
        raise JWSTSNWorkerError("JWST-SN five-component bundle is incomplete")
    try:
        return build_pr309_inputs(
            source_rows=_strict_json(paths["source_rows"], label="source rows"),
            host_rows=_strict_json(paths["host_rows"], label="host rows"),
            individual_errors=_strict_json(
                paths["individual_errors"], label="individual errors"
            ),
            covariance=_strict_json(paths["covariance"], label="covariance"),
            competitor_model=_strict_json(
                paths["competitor_model"], label="competitor model"
            ),
        )
    except JWSTSNCurrentStackError as exc:
        raise JWSTSNWorkerError(f"JWST-SN input contract failed: {exc}") from exc


def run_admitted(*, admission_path: Path, data_root: Path) -> dict[str, object]:
    decision = _load_admission(admission_path)
    _mark_observed_data_open_attempt()
    paths = _admitted_paths(decision, data_root=data_root)
    inputs = _load_inputs(paths)
    try:
        report = analyze_pr309_current_stack(inputs, observed=True)
    except JWSTSNCurrentStackError as exc:
        raise JWSTSNWorkerError(f"JWST-SN operator failed: {exc}") from exc
    return {
        **report,
        "lane_admission_bundle_id": decision.lane_admission_bundle_id,
        "ordered_record_ids": [record.record_id for record in decision.records],
        "artifact_metadata": {
            "owner": "HTT",
            "scope": "JWST-SN row-provenance and shared-covariance diagnostic",
            "claim_tier": "diagnostic_only",
            "transfer_source": "none",
            "covariance_status": "FULL_ADMITTED_SHARED_COVARIANCE",
            "null_mock_status": "NOT_APPLICABLE_DESCRIPTIVE_OPERATOR",
            "public_use": False,
            "candidate_commit": os.environ.get("HTT_ATTENDED_CANDIDATE_COMMIT"),
            "candidate_tree": os.environ.get("HTT_ATTENDED_CANDIDATE_TREE"),
        },
    }


def _synthetic_payloads(rows: int = 24) -> tuple[dict, dict, dict, dict, dict]:
    row_ids = [f"SYNTH-JWST-{index:03d}" for index in range(rows)]
    angles = np.linspace(0.1, 5.9, rows)
    latitude = np.linspace(-52.0, 57.0, rows)
    depth = np.linspace(18.0, 118.0, rows)
    redshift = 0.0015 + depth / 31_000.0 + 3.0e-5 * np.sin(angles)
    source_rows = {
        "row_order": row_ids,
        "rows": [
            {
                "row_id": row_id,
                "source_id": f"synthetic:source:{index // 6}",
                "source_release": "synthetic-pr309",
                "source_locator": f"generated-row:{index}",
                **PR309_OBSERVABLE_CONTRACT,
                "observable_delta_mag": float(
                    0.015 * np.sin(angles[index])
                    + 0.006 * np.cos(2.0 * angles[index])
                ),
            }
            for index, row_id in enumerate(row_ids)
        ],
    }
    host_rows = {
        "row_order": row_ids,
        "rows": [
            {
                "row_id": row_id,
                "host_id": f"SYNTH-HOST-{index:03d}",
                "host_linkage_basis": "SOURCE_REPORTED_HOST_IDENTITY",
                "host_linkage_probability": 0.96,
                "host_linkage_sigma_mag": 0.008 + 0.0002 * (index % 3),
                "redshift": float(redshift[index]),
                "depth_mpc": float(depth[index]),
                "galactic_l_deg": float(np.degrees(angles[index]) % 360.0),
                "galactic_b_deg": float(latitude[index]),
                **PR309_SEMANTIC_CONTRACT,
            }
            for index, row_id in enumerate(row_ids)
        ],
    }
    groups = [f"CAL-{index % 4}" for index in range(rows)]
    individual_errors = {
        "row_order": row_ids,
        "rows": [
            {
                "row_id": row_id,
                "sigma_individual_mag": 0.035 + 0.001 * (index % 5),
                "calibration_group": groups[index],
            }
            for index, row_id in enumerate(row_ids)
        ],
    }
    group_covariance = np.full((4, 4), 1.0e-5)
    np.fill_diagonal(group_covariance, 1.6e-4)
    separation = np.abs(np.subtract.outer(np.arange(rows), np.arange(rows)))
    peculiar = 5.0e-5 * np.exp(-separation / 5.0)
    covariance = {
        "row_order": row_ids,
        "calibration_group_order": ["CAL-0", "CAL-1", "CAL-2", "CAL-3"],
        "shared_zero_point_covariance_mag2": group_covariance.tolist(),
        "peculiar_velocity_covariance_mag2": peculiar.tolist(),
        "maximum_condition_number": 1.0e10,
    }
    competitor_model = {
        "row_order": row_ids,
        "competitors": [
            {
                "competitor_id": "CF4",
                "model_identity": "synthetic-cf4-forward-v1",
                "source_release": "synthetic-only",
                "model_role": "SEPARATE_DIRECTION_DEPTH_COMPETITOR",
                **PR309_COMPETITOR_SEMANTIC_CONTRACTS["CF4"],
                "frame_transformation_identity": "synthetic:cf4:cmb-frame:v1",
                "predicted_delta_mag": (
                    0.02 * np.sin(2.0 * angles)
                    + 0.004 * np.square(depth / depth.max())
                ).tolist(),
            },
            {
                "competitor_id": "2MRS",
                "model_identity": "synthetic-2mrs-forward-v1",
                "source_release": "synthetic-only",
                "model_role": "SEPARATE_DIRECTION_DEPTH_COMPETITOR",
                **PR309_COMPETITOR_SEMANTIC_CONTRACTS["2MRS"],
                "frame_transformation_identity": (
                    "synthetic:2mrs:barycentric-to-cmb:v1"
                ),
                "predicted_delta_mag": (
                    0.017 * np.cos(angles)
                    - 0.003 * redshift / redshift.max()
                ).tolist(),
            },
        ],
    }
    return source_rows, host_rows, individual_errors, covariance, competitor_model


def _max_rss_bytes() -> int:
    maximum = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(maximum if sys.platform == "darwin" else maximum * 1024)


def synthetic_profile() -> dict[str, object]:
    started = time.perf_counter()
    source_rows, host_rows, errors, covariance, competitors = _synthetic_payloads()
    inputs = build_pr309_inputs(
        source_rows=source_rows,
        host_rows=host_rows,
        individual_errors=errors,
        covariance=covariance,
        competitor_model=competitors,
    )
    report = analyze_pr309_current_stack(inputs, observed=False)
    return {
        "format": "JWST_SN_SYNTHETIC_PROFILE",
        "lane": "JWST_SN",
        "synthetic_rows": len(inputs.row_ids),
        "wall_seconds": time.perf_counter() - started,
        "max_rss_bytes": _max_rss_bytes(),
        "thread_controls": dict(THREAD_CONTROLS),
        "report": report,
        "observed_statistic_seen": False,
        "observed_science_executed": False,
    }


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii") as handle:
            json.dump(
                payload,
                handle,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--synthetic-profile", action="store_true")
    mode.add_argument("--run-admitted", action="store_true")
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.synthetic_profile:
            if args.admission is not None or args.data_root is not None:
                raise JWSTSNWorkerError(
                    "synthetic profile forbids admission and data root"
                )
            payload = synthetic_profile()
        else:
            if args.admission is None or args.data_root is None:
                raise JWSTSNWorkerError(
                    "admitted run requires admission and data root"
                )
            payload = run_admitted(
                admission_path=args.admission, data_root=args.data_root
            )
        _write_json(args.output, payload)
        print(json.dumps(payload, sort_keys=True, allow_nan=False))
        return 0
    except (JWSTSNWorkerError, JWSTSNCurrentStackError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
