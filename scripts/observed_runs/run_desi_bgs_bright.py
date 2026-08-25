#!/usr/bin/env python3
"""DESI BGS_BRIGHT-21.5 worker and observation-free synthetic profile."""

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
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import hashlib
import json
import multiprocessing
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
    canonical_sha256,
    DataIdentityError,
    _regular_beneath,
    load_lane_registry,
    replay_lane_admission_decision,
)
from obsstat.desi_successor_formalism import (  # noqa: E402
    DESIFitResult,
    DESIRealization,
    DESISelection,
    DESISuccessorError,
    EXPECTED_ABACUS_REALIZATIONS,
    EXPECTED_EZMOCK_REALIZATIONS,
    FEATURE_ORDER,
    SELECTION_DERIVATION_ID,
    SEMANTIC_IDENTITY_FIELDS,
    analyze_successor_formalism,
    fit_realization,
    validate_selection,
)


REGISTRY = ROOT / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
REQUIRED_COMPONENT_SEQUENCE = (
    "observed_catalogue",
    "selection",
    "covariance",
    *("ezmock_inventory" for _ in EXPECTED_EZMOCK_REALIZATIONS),
    *("abacus_inventory" for _ in EXPECTED_ABACUS_REALIZATIONS),
)
PROFILE_ROWS = {"1": 1, "8": 8, "32": 32, "128": 128, "full": 1025}
RAW_REQUIRED_COLUMNS = frozenset({"RA", "DEC", "Z", "WEIGHT"})
RAW_MAGNITUDE_COLUMNS = frozenset({"R_MAG_APP", "R_MAG_ABS"})
RAW_WINDOW_KEYS = frozenset({"NGC", "SGC", "nside", "zmin", "zmax"})
RAW_TOMOGRAPHY_KEY = "tomography_edges"
RAW_WINDOW_CAP_SHAPE = (3, 12 * 64 * 64)


class DESIWorkerError(RuntimeError):
    """Raised before a DESI result when the worker contract drifts."""


def classify_existing_raw_compatibility(
    *,
    observed_columns: set[str] | frozenset[str],
    ezmock_columns: set[str] | frozenset[str],
    abacus_columns: set[str] | frozenset[str],
    random_window_keys: set[str] | frozenset[str],
    random_window_cap_shape: tuple[int, ...],
) -> dict[str, object]:
    """Classify whether authenticated raw products can enter PR-311.

    This is a schema-only preflight.  It deliberately does not read galaxy
    rows, fit the observer statistic, or infer missing selection/window data.
    """

    families = {
        "OBSERVED": frozenset(observed_columns),
        "EZMOCK": frozenset(ezmock_columns),
        "ABACUS": frozenset(abacus_columns),
    }
    blockers: list[str] = []
    for family, columns in families.items():
        if not RAW_REQUIRED_COLUMNS <= columns:
            blockers.append(f"{family}_BASE_COLUMNS_UNAVAILABLE")
    if not RAW_MAGNITUDE_COLUMNS <= families["OBSERVED"]:
        blockers.append("OBSERVED_ROW_MAGNITUDE_EVIDENCE_UNAVAILABLE")
    if not RAW_MAGNITUDE_COLUMNS <= families["EZMOCK"]:
        blockers.append("EZMOCK_ROW_MAGNITUDE_EVIDENCE_UNAVAILABLE")
    if not RAW_MAGNITUDE_COLUMNS <= families["ABACUS"]:
        blockers.append("ABACUS_ROW_MAGNITUDE_EVIDENCE_UNAVAILABLE")
    window_keys = frozenset(random_window_keys)
    if (
        not RAW_WINDOW_KEYS <= window_keys
        or RAW_TOMOGRAPHY_KEY not in window_keys
        or tuple(random_window_cap_shape) != RAW_WINDOW_CAP_SHAPE
    ):
        blockers.append("TOMOGRAPHIC_RANDOM_WINDOW_UNAVAILABLE")
    return {
        "terminal_disposition": (
            "BLOCKED_EXISTING_RAW_INSUFFICIENT_FOR_PR311"
            if blockers
            else "RAW_SCHEMA_COMPATIBLE_WITH_PR311"
        ),
        "blockers": blockers,
        "observed_statistic_seen": False,
        "observed_science_executed": False,
        "p_value": None,
        "forced_source_label": None,
    }


def _fits_column_names(path: Path) -> frozenset[str]:
    """Read only a FITS table header and return its column-name contract."""

    try:
        from astropy.io import fits

        with fits.open(path, memmap=True, lazy_load_hdus=True) as hdus:
            if len(hdus) < 2 or hdus[1].columns is None:
                raise DESIWorkerError(f"DESI FITS table is missing: {path}")
            return frozenset(str(name) for name in hdus[1].columns.names)
    except (OSError, ValueError, IndexError) as exc:
        raise DESIWorkerError(f"DESI FITS header could not be inspected: {path}") from exc


def _window_contract(path: Path) -> tuple[frozenset[str], tuple[int, ...]]:
    try:
        with np.load(path, allow_pickle=False) as data:
            keys = frozenset(data.files)
            if "NGC" not in data or "SGC" not in data:
                raise DESIWorkerError(f"DESI random window lacks cap arrays: {path}")
            ngc_shape = tuple(np.asarray(data["NGC"]).shape)
            sgc_shape = tuple(np.asarray(data["SGC"]).shape)
    except (OSError, ValueError) as exc:
        raise DESIWorkerError(f"DESI random window could not be inspected: {path}") from exc
    if ngc_shape != sgc_shape:
        raise DESIWorkerError(f"DESI random-window cap shapes disagree: {path}")
    return keys, ngc_shape


def _manifest_paths(rows: object, *, label: str) -> tuple[Path, Path]:
    if not isinstance(rows, list) or len(rows) != 2:
        raise DESIWorkerError(f"{label} must contain one NGC and one SGC file")
    paths: list[Path] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise DESIWorkerError(f"{label} file identity is malformed")
        raw_path, size = row.get("path"), row.get("size_bytes")
        path = Path(raw_path) if isinstance(raw_path, str) else Path()
        if (
            type(size) is not int
            or not path.is_absolute()
            or not path.is_file()
            or path.stat().st_size != size
        ):
            raise DESIWorkerError(f"{label} file is absent or size-drifted")
        paths.append(path)
    return tuple(sorted(paths, key=lambda item: ("SGC" in item.name, item.name)))


def _manifest_window(row: Mapping[str, object], *, label: str) -> Path:
    windows = row.get("random_windows")
    window = windows.get("0") if isinstance(windows, Mapping) else None
    raw_path = window.get("path") if isinstance(window, Mapping) else None
    path = Path(raw_path) if isinstance(raw_path, str) else Path()
    if not path.is_absolute() or not path.is_file():
        raise DESIWorkerError(f"{label} random window is absent")
    return path


def preflight_existing_acquisition(path: Path) -> dict[str, object]:
    """Inspect the complete local acquisition without evaluating a statistic."""

    payload = _strict_json_file(path, label="DESI acquisition manifest")
    records = payload.get("records")
    observed = payload.get("observed")
    if (
        payload.get("schema") != "htt.desi_dr1_mock_acquisition.v2"
        or payload.get("status") != "complete"
        or payload.get("authenticated_counts") != {"abacus": 25, "ezmock": 1000}
        or payload.get("final_full_data_rehash") is not True
        or not isinstance(payload.get("aggregate_input_hash"), str)
        or not isinstance(records, list)
        or len(records) != 1025
        or not isinstance(observed, Mapping)
        or observed.get("sample") != "DESI_DR1_BGS_BRIGHT-21.5"
    ):
        raise DESIWorkerError("DESI acquisition is not the exact completed DR1 slice")

    observed_window = observed.get("random_window")
    if (
        not isinstance(observed_window, Mapping)
        or not isinstance(observed_window.get("path"), str)
    ):
        raise DESIWorkerError("DESI observed acquisition identity is malformed")
    observed_paths = _manifest_paths(observed.get("data_files"), label="observed data")
    observed_window_path = Path(str(observed_window["path"]))
    if not observed_window_path.is_absolute() or not observed_window_path.is_file():
        raise DESIWorkerError("DESI observed random window is absent")

    typed_records = [row for row in records if isinstance(row, Mapping)]
    if len(typed_records) != len(records):
        raise DESIWorkerError("DESI acquisition contains a non-object record")
    ez_rows = [row for row in typed_records if row.get("family") == "ezmock"]
    ab_rows = [row for row in typed_records if row.get("family") == "abacus"]
    ez = sorted(row.get("realization") for row in ez_rows)
    ab = sorted(row.get("realization") for row in ab_rows)
    if ez != list(EXPECTED_EZMOCK_REALIZATIONS) or ab != list(
        EXPECTED_ABACUS_REALIZATIONS
    ):
        raise DESIWorkerError("DESI realization inventory is incomplete or reordered")

    representatives = {
        "OBSERVED": observed_paths,
        "EZMOCK": _manifest_paths(ez_rows[0].get("data_files"), label="EZmock[1]"),
        "ABACUS": _manifest_paths(ab_rows[0].get("data_files"), label="Abacus[0]"),
    }
    common_columns = {
        family: frozenset.intersection(*(_fits_column_names(item) for item in paths))
        for family, paths in representatives.items()
    }
    windows = [
        observed_window_path,
        _manifest_window(ez_rows[0], label="EZmock[1]"),
        _manifest_window(ab_rows[0], label="Abacus[0]"),
    ]
    contracts = [_window_contract(item) for item in windows]
    window_keys = frozenset.intersection(*(row[0] for row in contracts))
    window_shapes = {row[1] for row in contracts}
    if len(window_shapes) != 1:
        raise DESIWorkerError("DESI random-window shapes drift across the inventory")
    window_shape = next(iter(window_shapes))

    report = classify_existing_raw_compatibility(
        observed_columns=set(common_columns["OBSERVED"]),
        ezmock_columns=set(common_columns["EZMOCK"]),
        abacus_columns=set(common_columns["ABACUS"]),
        random_window_keys=set(window_keys),
        random_window_cap_shape=window_shape,
    )
    return {
        "report_type": "DESI_EXISTING_RAW_PR311_COMPATIBILITY_PREFLIGHT",
        **report,
        "acquisition": {
            "manifest": str(path.resolve()),
            "aggregate_input_hash": payload["aggregate_input_hash"],
            "final_full_data_rehash": True,
            "observed_catalogues": 2,
            "ezmock_realizations": len(ez),
            "abacus_realizations": len(ab),
        },
        "schema_evidence": {
            "common_columns": {
                family: sorted(columns)
                for family, columns in common_columns.items()
            },
            "random_window_keys": sorted(window_keys),
            "random_window_cap_shape": list(window_shape),
            "representative_fits_headers_inspected": 6,
            "representative_random_windows_inspected": len(windows),
        },
        "observed_file_headers_inspected": True,
        "observed_payload_rows_read": False,
        "required_next_action": (
            "materialize exact per-tomographic-bin mock random windows and "
            "bind official-product selection evidence before PR-311 execution"
        ),
        "artifact_metadata": {
            "owner": "OBSSTAT",
            "artifact_mode": "input_compatibility_blocker",
            "claim_tier": "diagnostic_only",
            "public_use": False,
        },
    }


def _strict_json_bytes(raw: bytes, *, label: str) -> Mapping[str, object]:
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise DESIWorkerError(f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str) -> object:
        raise DESIWorkerError(f"{label} contains non-finite constant {value}")

    try:
        payload = json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DESIWorkerError(f"{label} is not strict JSON") from exc
    if not isinstance(payload, Mapping):
        raise DESIWorkerError(f"{label} must be a JSON object")
    return payload


def _raw_hash(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _validate_attended_admission_binding(raw: bytes, decision) -> None:
    record_ids = [record.record_id for record in decision.records]
    if (
        os.environ.get("HTT_ATTENDED_ADMISSION_SHA256") != _raw_hash(raw)
        or os.environ.get("HTT_ATTENDED_ADMISSION_BUNDLE_ID")
        != decision.lane_admission_bundle_id
        or os.environ.get("HTT_ATTENDED_ORDERED_RECORD_IDS_SHA256")
        != canonical_sha256(record_ids)
    ):
        raise DESIWorkerError("attended admission acceptance binding drifted")


def _load_admission(path: Path):
    try:
        raw = path.read_bytes()
        decision = replay_lane_admission_decision(
            _strict_json_bytes(raw, label="DESI admission"),
            registry=load_lane_registry(REGISTRY),
        )
    except (OSError, DataIdentityError, DESIWorkerError) as exc:
        raise DESIWorkerError(f"DESI admission replay failed: {exc}") from exc
    if (
        decision.status is not AdmissionStatus.ADMITTED_IDENTITY_ONLY
        or decision.lane_id != "DESI"
        or tuple(record.component_id for record in decision.records)
        != REQUIRED_COMPONENT_SEQUENCE
        or decision.lane_admission_bundle_id is None
    ):
        raise DESIWorkerError("DESI admission is not the complete 1028-record identity")
    _validate_attended_admission_binding(raw, decision)
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
        raise DESIWorkerError("attended output/start/data-open binding is invalid")
    _write_json(marker, {"state": "OBSERVED_DATA_OPEN_ATTEMPTED"})


def _admitted_paths(decision, *, data_root: Path) -> dict[str, list[Path]]:
    if (
        not data_root.is_absolute()
        or data_root.is_symlink()
        or not data_root.is_dir()
        or data_root.resolve() != data_root
    ):
        raise DESIWorkerError("data root must be an absolute regular directory")
    profile = decision.records[0].native_identity_profile
    bindings = profile.get("component_bindings")
    if isinstance(bindings, (str, bytes)) or not isinstance(bindings, Sequence):
        raise DESIWorkerError("DESI native component bindings are malformed")
    rows = tuple(row for row in bindings if isinstance(row, Mapping))
    if len(rows) != len(decision.records) or len(rows) != len(bindings):
        raise DESIWorkerError("DESI native component binding cardinality drifted")
    result = {component: [] for component in dict.fromkeys(REQUIRED_COMPONENT_SEQUENCE)}
    for record, binding in zip(decision.records, rows, strict=True):
        relative = binding.get("relative_path")
        if (
            binding.get("component_id") != record.component_id
            or binding.get("ordinal") != record.component_ordinal
            or binding.get("byte_size") != record.byte_size
            or binding.get("content_sha256") != record.content_sha256
            or not isinstance(relative, str)
        ):
            raise DESIWorkerError("DESI component binding identity drifted")
        try:
            path, info = _regular_beneath(
                data_root, Path(relative), f"{record.component_id}[{record.component_ordinal}]"
            )
            digest = _file_hash(path)
        except (DataIdentityError, OSError) as exc:
            raise DESIWorkerError("DESI admitted component could not be verified") from exc
        if info.st_size != record.byte_size or digest != record.content_sha256:
            raise DESIWorkerError("DESI admitted component no longer matches admission")
        result[record.component_id].append(path)
    expected_counts = {
        "observed_catalogue": 1,
        "selection": 1,
        "covariance": 1,
        "ezmock_inventory": 1000,
        "abacus_inventory": 25,
    }
    if {key: len(value) for key, value in result.items()} != expected_counts:
        raise DESIWorkerError("DESI admitted inventory is incomplete")
    return result


def _strict_json_file(path: Path, *, label: str) -> Mapping[str, object]:
    try:
        return _strict_json_bytes(path.read_bytes(), label=label)
    except OSError as exc:
        raise DESIWorkerError(f"{label} could not be read") from exc


def _selection(payload: Mapping[str, object]) -> DESISelection:
    expected = {
        "release_id",
        "tracer",
        "base_apparent_r_limit",
        "absolute_magnitude_max",
        "z_min",
        "z_max",
        "caps",
        "selection_id",
        "selection_derivation_id",
        "window_ids",
        "operator_id",
        *SEMANTIC_IDENTITY_FIELDS,
        "transfer_source",
    }
    if set(payload) != expected:
        raise DESIWorkerError("DESI selection document fields drifted")
    try:
        selection = DESISelection(
            release_id=str(payload["release_id"]),
            tracer=str(payload["tracer"]),
            base_apparent_r_limit=float(payload["base_apparent_r_limit"]),
            absolute_magnitude_max=float(payload["absolute_magnitude_max"]),
            z_min=float(payload["z_min"]),
            z_max=float(payload["z_max"]),
            caps=tuple(str(value) for value in payload["caps"]),
            selection_id=str(payload["selection_id"]),
            selection_derivation_id=str(payload["selection_derivation_id"]),
            window_ids=tuple(str(value) for value in payload["window_ids"]),
            operator_id=str(payload["operator_id"]),
            units_contract_id=str(payload["units_contract_id"]),
            coordinate_frame_id=str(payload["coordinate_frame_id"]),
            sign_orientation_convention_id=str(
                payload["sign_orientation_convention_id"]
            ),
            directional_convention_id=str(payload["directional_convention_id"]),
            harmonic_convention_id=str(payload["harmonic_convention_id"]),
            mask_id=str(payload["mask_id"]),
            sky_support_id=str(payload["sky_support_id"]),
            covariance_id=str(payload["covariance_id"]),
            null_ensemble_id=str(payload["null_ensemble_id"]),
            transfer_source=str(payload["transfer_source"]),
            transfer_function_spec_id=str(payload["transfer_function_spec_id"]),
        )
        validate_selection(selection)
    except (TypeError, ValueError, DESISuccessorError) as exc:
        raise DESIWorkerError(f"DESI selection document is invalid: {exc}") from exc
    return selection


def _npz_text(value: np.ndarray, *, label: str) -> str:
    if value.shape != ():
        raise DESIWorkerError(f"{label} must be one scalar string")
    item = value.item()
    if not isinstance(item, str) or not item:
        raise DESIWorkerError(f"{label} must be one scalar string")
    return item


def _fit_npz(
    path: Path,
    *,
    family: str,
    realization: int,
    selection: DESISelection,
) -> tuple[DESIFitResult, DESIRealization | None]:
    expected = {
        "cap",
        "redshift",
        "official_sample_member",
        "apparent_r_mag",
        "absolute_magnitude_r",
        "direction",
        "weighted_counts",
        "random_window_weight",
        "nuisance_template",
        "tracer",
        "base_apparent_r_limit",
        "absolute_magnitude_max",
        "selection_id",
        "window_ids",
        "operator_id",
    }
    try:
        with np.load(path, allow_pickle=False) as data:
            if set(data.files) != expected:
                raise DESIWorkerError("DESI compact realization fields drifted")
            row = DESIRealization(
                family=family,
                realization=realization,
                tracer=_npz_text(data["tracer"], label="tracer"),
                base_apparent_r_limit=float(np.asarray(data["base_apparent_r_limit"]).item()),
                absolute_magnitude_max=float(np.asarray(data["absolute_magnitude_max"]).item()),
                cap=np.asarray(data["cap"]),
                redshift=np.asarray(data["redshift"]),
                official_sample_member=np.asarray(data["official_sample_member"]),
                apparent_r_mag=np.asarray(data["apparent_r_mag"]),
                absolute_magnitude_r=np.asarray(data["absolute_magnitude_r"]),
                direction=np.asarray(data["direction"]),
                weighted_counts=np.asarray(data["weighted_counts"]),
                random_window_weight=np.asarray(data["random_window_weight"]),
                nuisance_template=np.asarray(data["nuisance_template"]),
                selection_id=_npz_text(data["selection_id"], label="selection_id"),
                window_ids=tuple(str(value) for value in np.asarray(data["window_ids"])),
                operator_id=_npz_text(data["operator_id"], label="operator_id"),
            )
    except (OSError, ValueError, DESISuccessorError) as exc:
        raise DESIWorkerError(f"DESI compact realization is invalid: {path.name}") from exc
    fitted = fit_realization(row, selection)
    return fitted, row if family == "OBSERVED" else None


def _responses(payload: Mapping[str, object], selection: DESISelection):
    expected = {
        "operator_id",
        "feature_order",
        "nuisance_response",
        "candidate_response",
        "confusion_templates",
    }
    if set(payload) != expected or payload.get("operator_id") != selection.operator_id:
        raise DESIWorkerError("DESI response/covariance contract drifted")
    if tuple(payload.get("feature_order", ())) != FEATURE_ORDER:
        raise DESIWorkerError("DESI response feature order drifted")
    return (
        np.asarray(payload["nuisance_response"], dtype=float),
        np.asarray(payload["candidate_response"], dtype=float),
        np.asarray(payload["confusion_templates"], dtype=float),
    )


def _synthetic_selection() -> DESISelection:
    return DESISelection(
        release_id="DESI_DR1_LSS_IRON_V1_5",
        tracer="BGS_BRIGHT-21.5",
        base_apparent_r_limit=19.5,
        absolute_magnitude_max=-21.5,
        z_min=0.1,
        z_max=0.4,
        caps=("NGC", "SGC"),
        selection_id="desi:dr1:bgs_bright-21.5:z0.1-0.4",
        selection_derivation_id=SELECTION_DERIVATION_ID,
        window_ids=("desi:dr1:ngc:random0", "desi:dr1:sgc:random0"),
        operator_id="desi-pr311-identical-data-null-operator-v1",
        units_contract_id="units:DESI:number-counts-direction-redshift:v1",
        coordinate_frame_id="frame:DESI:galactic-direction-cmb-redshift:v1",
        sign_orientation_convention_id="sign:DESI:overdensity-positive:v1",
        directional_convention_id="direction:DESI:galactic-unit-vector:v1",
        harmonic_convention_id="harmonic:DESI:not-applicable:v1",
        mask_id="mask:DESI:dr1-v1.5-ngc-sgc-random-window:v1",
        sky_support_id="sky:DESI:dr1-v1.5-ngc-sgc:v1",
        covariance_id="covariance:DESI:ezmock-1000:v1",
        null_ensemble_id="null:DESI:ezmock-1000-abacus-25:v1",
        transfer_source="none",
        transfer_function_spec_id="none",
    )


def _synthetic_realization(family: str, realization: int, *, phase: float = 0.0):
    selection = _synthetic_selection()
    rows_per_cell = 8
    caps = np.repeat(np.asarray(["NGC", "SGC"]), 3 * rows_per_cell)
    bins = np.tile(np.repeat(np.arange(3), rows_per_cell), 2)
    row = np.arange(caps.size, dtype=float)
    redshift = 0.15 + 0.10 * bins + 0.002 * ((row % rows_per_cell) - 3.5)
    apparent_r = 18.2 + 0.02 * (row % rows_per_cell)
    absolute_r = -22.2 + 0.03 * (row % rows_per_cell)
    longitude = 0.19 * row + phase
    latitude = 0.25 * np.sin(0.23 * row + 0.01 * realization)
    direction = np.column_stack(
        [
            np.cos(latitude) * np.cos(longitude),
            np.cos(latitude) * np.sin(longitude),
            np.sin(latitude),
        ]
    )
    randoms = 75.0 + 4.0 * np.cos(0.17 * row + phase)
    nuisance = np.sin(0.31 * row + 0.07 * realization)
    nuisance -= np.mean(nuisance)
    alpha = np.where(caps == "NGC", 0.78, 0.84) * (1.0 + 2.0e-4 * realization)
    clustering = 0.006 * (direction @ np.asarray([0.4, -0.2, 0.7]))
    offset = 0 if family == "EZMOCK" else 100_000
    stochastic = np.random.default_rng(offset + realization).normal(
        0.0, 0.002, row.size
    )
    counts = alpha * randoms * (1.0 + clustering + 0.004 * nuisance + stochastic)
    return DESIRealization(
        family=family,
        realization=realization,
        tracer=selection.tracer,
        base_apparent_r_limit=selection.base_apparent_r_limit,
        absolute_magnitude_max=selection.absolute_magnitude_max,
        cap=caps,
        redshift=redshift,
        official_sample_member=np.ones(row.size, dtype=bool),
        apparent_r_mag=apparent_r,
        absolute_magnitude_r=absolute_r,
        direction=direction,
        weighted_counts=counts,
        random_window_weight=randoms,
        nuisance_template=nuisance,
        selection_id=selection.selection_id,
        window_ids=selection.window_ids,
        operator_id=selection.operator_id,
    )


def _synthetic_responses():
    x = np.linspace(-1.0, 1.0, len(FEATURE_ORDER))
    return (
        np.column_stack([np.ones(x.size), x]),
        np.column_stack(
            [np.sin(1.3 * x), np.cos(1.9 * x), x * x - np.mean(x * x)]
        ),
        np.column_stack(
            [np.sin(0.8 * x), np.cos(1.1 * x), np.sin(1.7 * x + 0.2)]
        ),
    )


def _bind_selection_to_admission(selection: DESISelection, decision) -> None:
    """Require the operator document to replay PR-289 scientific identities."""

    for record in decision.records:
        if (
            record.selection_id != selection.selection_id
            or record.transfer_source != selection.transfer_source
            or any(
                getattr(record, field) != getattr(selection, field)
                for field in SEMANTIC_IDENTITY_FIELDS
            )
        ):
            raise DESIWorkerError(
                "DESI admission units/frame/mask/covariance/null identity drifted"
            )


def _base_profile(rows: str, started: float) -> dict[str, object]:
    return {
        "profile_rows": rows,
        "profile_realization_count": PROFILE_ROWS[rows],
        "p_value": None,
        "forced_source_label": None,
        "observed_statistic_seen": False,
        "observed_science_executed": False,
        "elapsed_seconds": time.perf_counter() - started,
        "max_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024),
        "artifact_metadata": {
            "owner": "OBSSTAT",
            "artifact_mode": "synthetic_operator_diagnostic",
            "claim_tier": "diagnostic_only",
            "public_use": False,
            "allowed_use": "internal_operator_validation",
        },
    }


def _profile_fit(task: tuple[str, int, float]) -> DESIFitResult:
    family, realization, phase = task
    selection = _synthetic_selection()
    return fit_realization(
        _synthetic_realization(family, realization, phase=phase), selection
    )


def synthetic_profile(
    *, rows: str, mode: str = "serial", workers: int = 2
) -> dict[str, object]:
    if (
        rows not in PROFILE_ROWS
        or mode not in {"serial", "thread", "process"}
        or type(workers) is not int
        or not 1 <= workers <= 4
    ):
        raise DESIWorkerError("synthetic profile row label is unsupported")
    started = time.perf_counter()
    full_tasks = [
        ("EZMOCK", index, 0.0) for index in EXPECTED_EZMOCK_REALIZATIONS
    ] + [("ABACUS", index, 0.09) for index in EXPECTED_ABACUS_REALIZATIONS]
    tasks = full_tasks if rows == "full" else full_tasks[: PROFILE_ROWS[rows]]
    fit_started = time.perf_counter()
    if mode == "serial":
        fitted = [_profile_fit(task) for task in tasks]
    elif mode == "thread":
        with ThreadPoolExecutor(max_workers=workers) as pool:
            fitted = list(pool.map(_profile_fit, tasks))
    else:
        context = multiprocessing.get_context("fork")
        with ProcessPoolExecutor(max_workers=workers, mp_context=context) as pool:
            fitted = list(pool.map(_profile_fit, tasks))
    fit_seconds = time.perf_counter() - fit_started
    if rows != "full":
        return {
            **_base_profile(rows, started),
            "mode": mode,
            "workers": workers,
            "thread_controls": dict(THREAD_CONTROLS),
            "stage_seconds": {"per_realization_refit": fit_seconds},
            "terminal_disposition": "PROFILE_ONLY_INCOMPLETE_INVENTORY",
            "mock_support": {
                "ezmock_count": min(PROFILE_ROWS[rows], 1000),
                "abacus_count": 0,
                "covariance_owner": None,
                "pooled_with_ezmock": False,
            },
            "covariance": None,
            "response_rank": None,
            "component_confusion": None,
        }
    selection = _synthetic_selection()
    nuisance, candidate, confusion = _synthetic_responses()
    ezmock = tuple(fitted[:1000])
    abacus = tuple(fitted[1000:])
    closure_started = time.perf_counter()
    report = analyze_successor_formalism(
        ezmock,
        abacus,
        selection=selection,
        nuisance_response=nuisance,
        candidate_response=candidate,
        confusion_templates=confusion,
        observed=False,
    )
    profile = _base_profile(rows, started)
    profile_metadata = profile.pop("artifact_metadata")
    return {
        **report,
        **profile,
        "artifact_metadata": {
            **report["artifact_metadata"],
            **profile_metadata,
        },
        "mode": mode,
        "workers": workers,
        "thread_controls": dict(THREAD_CONTROLS),
        "stage_seconds": {
            "per_realization_refit": fit_seconds,
            "covariance_validation_rank": time.perf_counter() - closure_started,
        },
    }


def run_admitted(*, admission_path: Path, data_root: Path) -> dict[str, object]:
    decision = _load_admission(admission_path)
    _mark_observed_data_open_attempt()
    paths = _admitted_paths(decision, data_root=data_root)
    selection = _selection(
        _strict_json_file(paths["selection"][0], label="DESI selection")
    )
    _bind_selection_to_admission(selection, decision)
    nuisance, candidate, confusion = _responses(
        _strict_json_file(paths["covariance"][0], label="DESI response contract"),
        selection,
    )
    observed_fit, observed_row = _fit_npz(
        paths["observed_catalogue"][0],
        family="OBSERVED",
        realization=0,
        selection=selection,
    )
    assert observed_row is not None and observed_fit.family == "OBSERVED"
    ezmock = tuple(
        _fit_npz(path, family="EZMOCK", realization=index, selection=selection)[0]
        for path, index in zip(
            paths["ezmock_inventory"], EXPECTED_EZMOCK_REALIZATIONS, strict=True
        )
    )
    abacus = tuple(
        _fit_npz(path, family="ABACUS", realization=index, selection=selection)[0]
        for path, index in zip(
            paths["abacus_inventory"], EXPECTED_ABACUS_REALIZATIONS, strict=True
        )
    )
    report = analyze_successor_formalism(
        ezmock,
        abacus,
        selection=selection,
        nuisance_response=nuisance,
        candidate_response=candidate,
        confusion_templates=confusion,
        observed=True,
        observed_realization=observed_row,
    )
    record_ids = [record.record_id for record in decision.records]
    report["artifact_metadata"].update(
        {
            "candidate_commit": os.environ.get("HTT_ATTENDED_CANDIDATE_COMMIT"),
            "candidate_tree": os.environ.get("HTT_ATTENDED_CANDIDATE_TREE"),
            "input_identity": {
                "lane_admission_bundle_id": decision.lane_admission_bundle_id,
                "ordered_record_ids": record_ids,
            },
        }
    )
    return {
        **report,
        "lane_admission_bundle_id": decision.lane_admission_bundle_id,
        "ordered_record_ids": record_ids,
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
    mode.add_argument("--preflight-existing-raw", action="store_true")
    parser.add_argument("--rows", choices=tuple(PROFILE_ROWS), default="full")
    parser.add_argument("--mode", choices=("serial", "thread", "process"), default="serial")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--acquisition-manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.preflight_existing_raw:
            if (
                args.acquisition_manifest is None
                or args.admission is not None
                or args.data_root is not None
            ):
                raise DESIWorkerError(
                    "existing-raw preflight requires only the acquisition manifest"
                )
            payload = preflight_existing_acquisition(args.acquisition_manifest)
        elif args.synthetic_profile:
            if (
                args.admission is not None
                or args.data_root is not None
                or args.acquisition_manifest is not None
            ):
                raise DESIWorkerError("synthetic profile forbids admission and data root")
            payload = synthetic_profile(rows=args.rows, mode=args.mode, workers=args.workers)
        else:
            if (
                args.admission is None
                or args.data_root is None
                or args.acquisition_manifest is not None
            ):
                raise DESIWorkerError("admitted run requires admission and data root")
            payload = run_admitted(admission_path=args.admission, data_root=args.data_root)
        _write_json(args.output, payload)
        print(json.dumps(payload, sort_keys=True, allow_nan=False))
        return 0
    except (DESIWorkerError, DESISuccessorError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
