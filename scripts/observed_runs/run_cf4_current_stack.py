#!/usr/bin/env python3
"""CF4 current-stack worker plus observation-free synthetic profiling.

The admitted mode is reachable only through the attended primary-lane
executor after ``start.json`` exists.  Synthetic profiling uses generated
catalogues and never accepts a data root or admission.
"""

from __future__ import annotations

import os

for _name in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ[_name] = "1"

import argparse
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import json
from pathlib import Path
import resource
import sys
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
from obsstat.cf4_current_stack import (  # noqa: E402
    Cf4CurrentStackError,
    Cf4NuisanceProfile,
    Cf4OperatorConfig,
    Cf4OperatorInputs,
    analyze_cf4_current_stack,
    build_cf4_affine_design,
    galactic_unit_vectors,
)


REGISTRY = (
    ROOT / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
)
REQUIRED_COMPONENTS = frozenset(
    {
        "catalogue",
        "row_selection",
        "covariance",
        "frame_definition",
        "sign_convention",
        "units_contract",
        "grouping_definition",
        "depth_definition",
        "zoa_definition",
    }
)
ROW_LABELS = ("1", "8", "32", "128", "full")
PROFILE_MODES = ("serial", "thread", "process")
PROFILE_ROWS = {"1": 1, "8": 8, "32": 32, "128": 128, "full": 256}


class Cf4WorkerError(RuntimeError):
    """Raised when worker input or execution semantics drift."""


def _strict_json(path: Path, *, label: str) -> Mapping[str, object]:
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise Cf4WorkerError(f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    try:
        payload = json.loads(path.read_bytes(), object_pairs_hook=unique)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Cf4WorkerError(f"{label} is not strict JSON") from exc
    if not isinstance(payload, Mapping):
        raise Cf4WorkerError(f"{label} must be a JSON object")
    return payload


def _load_admission(path: Path):
    try:
        decision = replay_lane_admission_decision(
            _strict_json(path, label="CF4 admission"),
            registry=load_lane_registry(REGISTRY),
        )
    except (DataIdentityError, Cf4WorkerError) as exc:
        raise Cf4WorkerError(f"CF4 admission replay failed: {exc}") from exc
    if (
        decision.status is not AdmissionStatus.ADMITTED_IDENTITY_ONLY
        or decision.lane_id != "CF4"
        or len(decision.records) != len(REQUIRED_COMPONENTS)
        or decision.lane_admission_bundle_id is None
    ):
        raise Cf4WorkerError("CF4 admission is not complete identity admission")
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
        raise Cf4WorkerError("attended output/start/data-open binding is invalid")
    _write_json(marker, {"state": "OBSERVED_DATA_OPEN_ATTEMPTED"})


def _admitted_paths(decision, *, data_root: Path) -> dict[str, Path]:
    if (
        not data_root.is_absolute()
        or data_root.is_symlink()
        or not data_root.is_dir()
        or data_root.resolve() != data_root
    ):
        raise Cf4WorkerError("data root must be an absolute regular directory")
    profile = decision.records[0].native_identity_profile
    bindings = profile.get("component_bindings")
    if not isinstance(bindings, Sequence) or len(bindings) != len(decision.records):
        raise Cf4WorkerError("CF4 native component bindings drifted")
    records = {record.component_id: record for record in decision.records}
    if set(records) != REQUIRED_COMPONENTS:
        raise Cf4WorkerError("CF4 admitted component inventory is incomplete")
    result: dict[str, Path] = {}
    for row in bindings:
        if not isinstance(row, Mapping):
            raise Cf4WorkerError("CF4 component binding is not a mapping")
        component = row.get("component_id")
        relative = row.get("relative_path")
        if (
            not isinstance(component, str)
            or component not in records
            or not isinstance(relative, str)
        ):
            raise Cf4WorkerError("CF4 component binding identity drifted")
        try:
            candidate, info = _regular_beneath(
                data_root, Path(relative), f"CF4 component {component}"
            )
            digest = "sha256:" + _stream_sha256(
                candidate,
                field_name=f"CF4 component {component}",
                expected_info=info,
            )
        except DataIdentityError as exc:
            raise Cf4WorkerError(
                f"{component} is not an exact admitted file: {exc}"
            ) from exc
        record = records[component]
        if info.st_size != record.byte_size or digest != record.content_sha256:
            raise Cf4WorkerError(f"{component} no longer matches the admission")
        result[component] = candidate
    return result


def _exact_json(path: Path, expected: Mapping[str, object], label: str) -> None:
    if dict(_strict_json(path, label=label)) != dict(expected):
        raise Cf4WorkerError(f"{label} contract drifted")


def _load_inputs(
    paths: Mapping[str, Path], *, expected_selection_id: str | None = None
) -> tuple[Cf4OperatorInputs, Cf4OperatorConfig]:
    try:
        with np.load(paths["catalogue"], allow_pickle=False) as payload:
            if set(payload.files) != {
                "group_id",
                "galactic_l_deg",
                "galactic_b_deg",
                "distance_mpc",
                "cmb_velocity_km_s",
            }:
                raise Cf4WorkerError("CF4 catalogue columns drifted")
            catalogue = {name: np.asarray(payload[name]) for name in payload.files}
        with np.load(paths["covariance"], allow_pickle=False) as payload:
            if set(payload.files) != {"group_id", "covariance_km2_s2"}:
                raise Cf4WorkerError("CF4 covariance columns drifted")
            covariance_ids = np.asarray(payload["group_id"])
            covariance = np.asarray(payload["covariance_km2_s2"], dtype=float)
    except (OSError, ValueError, KeyError) as exc:
        raise Cf4WorkerError("CF4 numeric component is not a safe NPZ") from exc
    selection = _strict_json(paths["row_selection"], label="row selection")
    if set(selection) != {"selection_id", "ordered_group_ids"}:
        raise Cf4WorkerError("row-selection fields drifted")
    selected_ids = selection["ordered_group_ids"]
    if (
        not isinstance(selection["selection_id"], str)
        or (
            expected_selection_id is not None
            and selection["selection_id"] != expected_selection_id
        )
        or not isinstance(selected_ids, list)
        or not all(type(value) is int for value in selected_ids)
    ):
        raise Cf4WorkerError("row-selection values drifted")
    _exact_json(
        paths["frame_definition"],
        {"basis": "IAU_1958", "coordinate_frame": "GALACTIC"},
        "frame definition",
    )
    _exact_json(
        paths["sign_convention"],
        {
            "peculiar_velocity_definition": "VCMB_MINUS_H0_DISTANCE",
            "positive_velocity": "RECEDING",
        },
        "sign convention",
    )
    _exact_json(
        paths["units_contract"],
        {
            "angle": "deg",
            "covariance": "(km s-1)^2",
            "distance": "Mpc",
            "radial_velocity": "km s-1",
        },
        "units contract",
    )
    _exact_json(
        paths["grouping_definition"],
        {
            "group_id_field": "group_id",
            "row_unit": "CF4_GROUP",
            "unique_group_ids": True,
        },
        "grouping definition",
    )
    depth = _strict_json(paths["depth_definition"], label="depth definition")
    zoa = _strict_json(paths["zoa_definition"], label="ZoA definition")
    if set(depth) != {
        "depth_thresholds_mpc",
        "maximum_standardized_condition_number",
        "minimum_singular_value_ratio",
        "nuisance_profiles",
        "rank_relative_tolerance",
    } or set(zoa) != {"zoa_half_widths_deg"}:
        raise Cf4WorkerError("depth/ZoA definition fields drifted")
    nuisance_rows = depth["nuisance_profiles"]
    if not isinstance(nuisance_rows, list):
        raise Cf4WorkerError("nuisance profiles must be a finite list")
    try:
        profiles = tuple(
            Cf4NuisanceProfile(
                profile_id=row["profile_id"],
                h0_km_s_mpc=float(row["h0_km_s_mpc"]),
                distance_scale=float(row["distance_scale"]),
                covariance_scale=float(row["covariance_scale"]),
            )
            for row in nuisance_rows
            if isinstance(row, Mapping) and set(row) == {
                "profile_id",
                "h0_km_s_mpc",
                "distance_scale",
                "covariance_scale",
            }
        )
        if len(profiles) != len(nuisance_rows):
            raise Cf4WorkerError("nuisance profile fields drifted")
        config = Cf4OperatorConfig(
            depth_thresholds_mpc=tuple(float(x) for x in depth["depth_thresholds_mpc"]),
            zoa_half_widths_deg=tuple(float(x) for x in zoa["zoa_half_widths_deg"]),
            nuisance_profiles=profiles,
            rank_relative_tolerance=float(depth["rank_relative_tolerance"]),
            minimum_singular_value_ratio=float(depth["minimum_singular_value_ratio"]),
            maximum_standardized_condition_number=float(
                depth["maximum_standardized_condition_number"]
            ),
        )
    except (Cf4CurrentStackError, KeyError, TypeError, ValueError) as exc:
        raise Cf4WorkerError(f"CF4 operator configuration rejected: {exc}") from exc
    inputs = Cf4OperatorInputs(
        group_ids=np.asarray(catalogue["group_id"]),
        galactic_longitude_deg=np.asarray(catalogue["galactic_l_deg"], dtype=float),
        galactic_latitude_deg=np.asarray(catalogue["galactic_b_deg"], dtype=float),
        distance_mpc=np.asarray(catalogue["distance_mpc"], dtype=float),
        cmb_velocity_km_s=np.asarray(catalogue["cmb_velocity_km_s"], dtype=float),
        covariance_km2_s2=covariance,
        covariance_group_ids=covariance_ids,
        selected_group_ids=np.asarray(selected_ids),
    )
    return inputs, config


def run_admitted(*, admission_path: Path, data_root: Path) -> dict[str, object]:
    decision = _load_admission(admission_path)
    _mark_observed_data_open_attempt()
    paths = _admitted_paths(decision, data_root=data_root)
    profile = decision.records[0].native_identity_profile
    catalogue_binding = profile.get("catalogue")
    if not isinstance(catalogue_binding, Mapping) or not isinstance(
        catalogue_binding.get("row_selection_id"), str
    ):
        raise Cf4WorkerError("CF4 admitted row-selection identity is missing")
    inputs, config = _load_inputs(
        paths,
        expected_selection_id=str(catalogue_binding["row_selection_id"]),
    )
    report = analyze_cf4_current_stack(inputs, config, observed=True)
    return {
        **report,
        "lane_admission_bundle_id": decision.lane_admission_bundle_id,
        "artifact_metadata": {
            "owner": "OBSSTAT",
            "scope": "CF4 current-stack affine-flow diagnostic",
            "claim_tier": "C3_DEPTH_DIRECTION_DIAGNOSTIC",
            "covariance_status": "FULL_ADMITTED_OFF_DIAGONAL",
            "null_mock_status": "NOT_ADMITTED_NO_P_VALUE",
            "family_identification": "FORBIDDEN",
            "candidate_commit": os.environ.get("HTT_ATTENDED_CANDIDATE_COMMIT"),
            "candidate_tree": os.environ.get("HTT_ATTENDED_CANDIDATE_TREE"),
        },
    }


def _synthetic_inputs(seed: int) -> tuple[Cf4OperatorInputs, Cf4OperatorConfig]:
    rng = np.random.default_rng(seed)
    rows = 48
    direction = rng.normal(size=(rows, 3))
    direction /= np.linalg.norm(direction, axis=1)[:, None]
    distance = np.linspace(30.0, 160.0, rows)
    design = build_cf4_affine_design(direction, distance)
    coefficient = np.asarray((4.0, 30.0, -12.0, 8.0, 0.10, -0.08, 0.04, 0.02, -0.03))
    h0 = 70.0
    vcmb = h0 * distance + design @ coefficient
    sigma = np.linspace(80.0, 120.0, rows)
    covariance = 0.03 * np.outer(sigma, sigma)
    covariance.flat[:: rows + 1] = np.square(sigma)
    ids = np.arange(rows, dtype=np.int64)
    inputs = Cf4OperatorInputs(
        group_ids=ids,
        galactic_longitude_deg=np.degrees(np.arctan2(direction[:, 1], direction[:, 0]))
        % 360.0,
        galactic_latitude_deg=np.degrees(np.arcsin(direction[:, 2])),
        distance_mpc=distance,
        cmb_velocity_km_s=vcmb,
        covariance_km2_s2=covariance,
        covariance_group_ids=ids.copy(),
        selected_group_ids=ids.copy(),
    )
    config = Cf4OperatorConfig(
        depth_thresholds_mpc=(160.0,),
        zoa_half_widths_deg=(0.0,),
        nuisance_profiles=(Cf4NuisanceProfile("synthetic", h0, 1.0, 1.0),),
    )
    return inputs, config


def _synthetic_once(seed: int) -> str:
    inputs, config = _synthetic_inputs(seed)
    return str(analyze_cf4_current_stack(inputs, config)["terminal_disposition"])


def _max_rss_bytes() -> int:
    maximum = max(
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
    )
    return int(maximum if sys.platform == "darwin" else maximum * 1024)


def synthetic_profile(*, rows: str, mode: str, workers: int) -> dict[str, object]:
    count = PROFILE_ROWS[rows]
    if mode not in PROFILE_MODES or type(workers) is not int or not 1 <= workers <= 4:
        raise Cf4WorkerError("synthetic profile mode/workers drifted")
    if mode == "serial" and workers != 1:
        raise Cf4WorkerError("serial profile requires one worker")
    started = time.perf_counter()
    seeds = list(range(307000, 307000 + count))
    if mode == "serial":
        states = [_synthetic_once(seed) for seed in seeds]
    else:
        executor = ThreadPoolExecutor if mode == "thread" else ProcessPoolExecutor
        with executor(max_workers=workers) as pool:
            states = list(pool.map(_synthetic_once, seeds))
    return {
        "format": "CF4_SYNTHETIC_PROFILE",
        "lane": "CF4",
        "row_label": rows,
        "synthetic_realizations": count,
        "mode": mode,
        "workers": workers,
        "wall_seconds": time.perf_counter() - started,
        "max_rss_bytes": _max_rss_bytes(),
        "terminal_dispositions": sorted(set(states)),
        "thread_controls": {
            name: os.environ[name]
            for name in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
            )
        },
        "observed_statistic_seen": False,
        "observed_science_executed": False,
    }


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n",
        encoding="ascii",
    )
    os.replace(temporary, path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run-admitted", action="store_true")
    mode.add_argument("--synthetic-profile", action="store_true")
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rows", choices=ROW_LABELS)
    parser.add_argument("--mode", choices=PROFILE_MODES, default="serial")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args(argv)
    try:
        if args.run_admitted:
            if args.admission is None or args.data_root is None or args.rows is not None:
                raise Cf4WorkerError("admitted run requires admission/data root only")
            payload = run_admitted(
                admission_path=args.admission, data_root=args.data_root
            )
        else:
            if args.admission is not None or args.data_root is not None or args.rows is None:
                raise Cf4WorkerError("synthetic profile forbids admitted inputs")
            payload = synthetic_profile(
                rows=args.rows, mode=args.mode, workers=args.workers
            )
        _write_json(args.output, payload)
        print(json.dumps(payload, sort_keys=True, allow_nan=False))
        return 0
    except (Cf4WorkerError, Cf4CurrentStackError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
