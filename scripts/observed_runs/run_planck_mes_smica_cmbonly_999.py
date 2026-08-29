#!/usr/bin/env python3
"""Execute and replay the separate PMG-WU-007 SMICA CMB-only 999 lane.

The observation carrier is reused from the accepted paired-300 package.  Only
the official CMB-only FFP10 maps are opened, and each null map is fitted once.
This lane is a conditional null-ensemble sensitivity diagnostic; it neither
replaces the paired-300 primary nor promotes a physical claim.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[2]
for import_root in (ROOT, ROOT / "htt", ROOT / "htt/src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from obsstat.planck_paired300_carrier_execution import (  # noqa: E402
    carrier_vector_from_alm,
)
from scripts.observed_runs import run_planck_mes_irrep_analysis as wu006  # noqa: E402
from scripts.observed_runs import run_planck_pr3 as worker  # noqa: E402


EXPECTED_CMB_IDS = tuple(f"{index:05d}" for index in range(1000) if index != 970)
OBSERVATION_ROW_ID = "PLANCK-PR3-SMICA-OBSERVED"
ROW_PREFIX = "FFP10-SMICA-CMB-"
OUTPUT_FORMAT = "PLANCK_MES_SMICA_CMBONLY_999_IRREP_V1"
TERMINAL_FORMAT = "PLANCK_MES_SMICA_CMBONLY_999_REVIEWED_TERMINAL_V1"
REVIEW_FORMAT = "PLANCK_MES_SMICA_CMBONLY_999_FRESH_REVIEW_V1"
SUCCESS_NEXT_ACTION = "PMG-WU-008"
PRIMARY_CARRIER = ROOT / "docs/generated/planck_pr3_paired300_irrep_carrier"
PRIMARY_ANALYSIS = ROOT / "docs/generated/planck_mes_irrep_analysis"
DEFAULT_OUTPUT = ROOT / "docs/generated/planck_mes_smica_cmbonly_999_irrep"
REGISTRY_PATH = (
    ROOT / "docs/research_program/post_pr327/planck_mes_wu007_registry.yaml"
)
FIGURE_FILES = (
    "figure_observed_coordinate_ranks.pdf",
    "figure_family_reducer_comparison.pdf",
    "figure_null_score_distributions.pdf",
    "figure_dependence_spectrum.pdf",
)
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
GIT_RE = re.compile(r"^[0-9a-f]{40}$")


class Wu007Error(RuntimeError):
    """Typed fail-closed PMG-WU-007 execution error."""


@dataclass(frozen=True)
class CmbOnlyRow:
    row_id: str
    source_id: str
    path: Path
    source_identity: Mapping[str, object]


@dataclass(frozen=True)
class ExecutionRows:
    row_ids: tuple[str, ...]
    scalar_features: np.ndarray
    carrier_rows: np.ndarray
    checkpoint_reused_count: int


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _canonical_content_id(value: object, *, role: str) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    digest = hashlib.sha256()
    digest.update(role.encode("ascii") + b"\0" + encoded)
    return "sha256:" + digest.hexdigest()


def _array_content_id(arrays: Mapping[str, np.ndarray], *, role: str) -> str:
    digest = hashlib.sha256()
    digest.update(role.encode("ascii") + b"\0")
    for name in sorted(arrays):
        value = np.ascontiguousarray(arrays[name])
        digest.update(name.encode("ascii") + b"\0")
        digest.update(value.dtype.str.encode("ascii") + b"\0")
        digest.update(repr(value.shape).encode("ascii") + b"\0")
        digest.update(memoryview(value).cast("B"))
    return "sha256:" + digest.hexdigest()


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _atomic_npz(path: Path, arrays: Mapping[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("wb") as handle:
        np.savez(handle, **arrays)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        raise Wu007Error(f"cannot write empty table: {path.name}")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def stat_identity(path: Path) -> dict[str, object]:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise Wu007Error(f"source is not a regular non-symlink file: {path}")
    value = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(value.st_mode):
        raise Wu007Error(f"source is not a regular file: {path}")
    return {
        "resolved_path": str(path.resolve(strict=True)),
        "device": int(value.st_dev),
        "inode": int(value.st_ino),
        "mode": int(value.st_mode),
        "size": int(value.st_size),
        "mtime_ns": int(value.st_mtime_ns),
    }


def require_stat_identity(path: Path, expected: Mapping[str, object]) -> None:
    current = stat_identity(path)
    selected = {key: current[key] for key in current if key in expected}
    expected_selected = {key: expected[key] for key in selected}
    if selected != expected_selected:
        raise Wu007Error(f"source identity mutated: {path}")


def snapshot_primary_artifacts(*roots: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for root in roots:
        root = Path(root)
        if root.is_symlink() or not root.is_dir():
            raise Wu007Error(f"accepted primary is missing or unsafe: {root}")
        for path in sorted(root.rglob("*")):
            if path.is_symlink() or (path.exists() and not path.is_file() and not path.is_dir()):
                raise Wu007Error(f"accepted primary contains an unsafe path: {path}")
            if path.is_file():
                result[str(path.resolve())] = _sha256(path)
    return result


def require_separate_output_boundary(
    output: Path, *, primary_paths: Sequence[Path] = (PRIMARY_CARRIER, PRIMARY_ANALYSIS)
) -> None:
    resolved = Path(output).resolve(strict=False)
    for primary in primary_paths:
        primary_resolved = Path(primary).resolve(strict=True)
        if resolved == primary_resolved or resolved.is_relative_to(primary_resolved):
            raise Wu007Error("robustness output must be separate from the accepted primary")


def validate_cmbonly_rows(rows: Sequence[CmbOnlyRow]) -> None:
    if len(rows) != 999:
        raise Wu007Error("CMB-only route must contain exactly 999 rows")
    expected = tuple((f"{ROW_PREFIX}{value}", value) for value in EXPECTED_CMB_IDS)
    actual = tuple((row.row_id, row.source_id) for row in rows)
    if actual != expected:
        raise Wu007Error("CMB-only row identity/order differs from the exact registry")
    for row in rows:
        if "noise" in row.path.name.lower() or not re.fullmatch(
            rf"dx12_v3_smica_cmb_mc_{row.source_id}_raw\.fits", row.path.name
        ):
            raise Wu007Error("noise or non-CMB product entered the CMB-only route")


def process_null_rows_one_pass(
    *,
    observed_features: object,
    observed_carrier: object,
    rows: Sequence[CmbOnlyRow],
    context: Mapping[str, object],
    operator_identity_sha256: str,
    read_cmb: Callable[[Path], object],
    process_map: Callable[..., tuple[object, object, object]],
    carrier_from_alm: Callable[[object], object],
    checkpoint_dir: Path | None,
    verify_source_unchanged: Callable[[CmbOnlyRow], None],
) -> ExecutionRows:
    """Fit each registered null once and retain scalar/carrier rows together."""

    validate_cmbonly_rows(rows)
    if not SHA256_RE.fullmatch(operator_identity_sha256):
        raise Wu007Error("operator identity is malformed")
    observation_scalar = np.asarray(observed_features, dtype=np.float64)
    observation_carrier = np.asarray(observed_carrier, dtype=np.float64)
    if observation_scalar.shape != (12,) or observation_carrier.shape != (32,):
        raise Wu007Error("accepted observation scalar/carrier shape drifted")
    scalar_rows = [observation_scalar.copy()]
    carrier_rows = [observation_carrier.copy()]
    reused = 0
    if checkpoint_dir is not None:
        checkpoint_dir = Path(checkpoint_dir)
        if checkpoint_dir.is_symlink():
            raise Wu007Error("checkpoint directory cannot be a symlink")
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
    for ordinal, row in enumerate(rows, start=1):
        verify_source_unchanged(row)
        checkpoint = None if checkpoint_dir is None else checkpoint_dir / f"null-{row.source_id}.npz"
        loaded = _load_checkpoint(
            checkpoint, ordinal=ordinal, row=row,
            operator_identity_sha256=operator_identity_sha256,
        ) if checkpoint is not None and checkpoint.exists() else None
        if loaded is None:
            pixel_map = np.asarray(read_cmb(row.path), dtype=np.float64)
            payload = process_map(pixel_map, component="SMICA", context=context)
            if not isinstance(payload, tuple) or len(payload) != 3:
                raise Wu007Error("frozen worker did not return features,timings,alm")
            features_raw, timings, retained_alm = payload
            features = np.asarray(features_raw, dtype=np.float64)
            carrier = np.asarray(carrier_from_alm(retained_alm), dtype=np.float64)
            if not isinstance(timings, Mapping):
                raise Wu007Error("frozen worker timing contract drifted")
            if features.shape != (12,) or carrier.shape != (32,):
                raise Wu007Error("same-pass scalar/carrier shape drifted")
            if not np.all(np.isfinite(features)) or not np.all(np.isfinite(carrier)):
                raise Wu007Error("same-pass scalar/carrier became nonfinite")
            if checkpoint is not None:
                _write_checkpoint(
                    checkpoint, ordinal=ordinal, row=row, features=features,
                    carrier=carrier, operator_identity_sha256=operator_identity_sha256,
                )
        else:
            features, carrier = loaded
            reused += 1
        verify_source_unchanged(row)
        scalar_rows.append(features)
        carrier_rows.append(carrier)
        if checkpoint_dir is not None and (
            ordinal == 1 or ordinal % 10 == 0 or row.source_id == "00818"
            or ordinal == len(rows)
        ):
            print(json.dumps({
                "completed": ordinal, "expected": len(rows), "row": row.row_id,
                "checkpoint_reused": loaded is not None,
            }, sort_keys=True), flush=True)
    scalar_matrix = np.asarray(scalar_rows, dtype=np.float64)
    carrier_matrix = np.asarray(carrier_rows, dtype=np.float64)
    if scalar_matrix.shape != (1000, 12) or carrier_matrix.shape != (1000, 32):
        raise Wu007Error("complete CMB-only matrices were not produced")
    return ExecutionRows(
        row_ids=(OBSERVATION_ROW_ID, *(row.row_id for row in rows)),
        scalar_features=scalar_matrix,
        carrier_rows=carrier_matrix,
        checkpoint_reused_count=reused,
    )


def _checkpoint_metadata_path(path: Path) -> Path:
    return path.with_suffix(".json")


def _checkpoint_numeric_id(value: np.ndarray, *, role: str) -> str:
    return _array_content_id({role: np.asarray(value)}, role=f"wu007_{role}")


def _write_checkpoint(
    path: Path, *, ordinal: int, row: CmbOnlyRow, features: np.ndarray,
    carrier: np.ndarray, operator_identity_sha256: str,
) -> None:
    metadata_path = _checkpoint_metadata_path(path)
    if path.exists() or path.is_symlink() or metadata_path.exists() or metadata_path.is_symlink():
        raise Wu007Error("checkpoint output collision")
    _atomic_npz(path, {"features": features, "carrier": carrier})
    _atomic_json(metadata_path, {
        "format": "PLANCK_MES_SMICA999_PRIVATE_ROW_CHECKPOINT_V1",
        "state": "SUCCEEDED",
        "ordinal": ordinal,
        "row_id": row.row_id,
        "source_id": row.source_id,
        "source_identity": dict(row.source_identity),
        "operator_identity_sha256": operator_identity_sha256,
        "features_content_id": _checkpoint_numeric_id(features, role="features"),
        "carrier_content_id": _checkpoint_numeric_id(carrier, role="carrier"),
    })


def _load_checkpoint(
    path: Path, *, ordinal: int, row: CmbOnlyRow,
    operator_identity_sha256: str,
) -> tuple[np.ndarray, np.ndarray]:
    metadata_path = _checkpoint_metadata_path(path)
    if path.is_symlink() or metadata_path.is_symlink() or not metadata_path.is_file():
        raise Wu007Error("checkpoint pair is missing or unsafe")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    required = {
        "format": "PLANCK_MES_SMICA999_PRIVATE_ROW_CHECKPOINT_V1",
        "state": "SUCCEEDED", "ordinal": ordinal, "row_id": row.row_id,
        "source_id": row.source_id, "source_identity": dict(row.source_identity),
        "operator_identity_sha256": operator_identity_sha256,
    }
    if any(metadata.get(key) != value for key, value in required.items()):
        raise Wu007Error("checkpoint row/source/operator identity drifted")
    with np.load(path, allow_pickle=False) as bundle:
        if set(bundle.files) != {"features", "carrier"}:
            raise Wu007Error("checkpoint numerical schema drifted")
        features = np.asarray(bundle["features"])
        carrier = np.asarray(bundle["carrier"])
    if (
        features.dtype != np.dtype("float64") or features.shape != (12,)
        or carrier.dtype != np.dtype("float64") or carrier.shape != (32,)
        or metadata.get("features_content_id") != _checkpoint_numeric_id(features, role="features")
        or metadata.get("carrier_content_id") != _checkpoint_numeric_id(carrier, role="carrier")
    ):
        raise Wu007Error("checkpoint decoded content identity drifted")
    return features.copy(), carrier.copy()


def require_scalar_carrier_closure(
    scalar_features: object, carrier_rows: object,
) -> dict[str, object]:
    scalar = np.asarray(scalar_features, dtype=np.float64)
    carriers = np.asarray(carrier_rows, dtype=np.float64)
    if scalar.ndim != 2 or scalar.shape[1] != 12 or carriers.shape != (scalar.shape[0], 32):
        raise Wu007Error("scalar/carrier closure matrices are malformed")
    projected = np.asarray(
        [worker._component_features_from_real_carrier(row) for row in carriers],
        dtype=np.float64,
    )
    residual = np.abs(projected - scalar)
    scale = np.maximum(1.0, np.abs(scalar))
    criterion = wu006.NUMERICAL_ATOL + wu006.NUMERICAL_RTOL * scale
    if np.any(residual > criterion):
        raise Wu007Error("same-row scalar/carrier closure differs")
    return {
        "state": "MATCH",
        "max_absolute_residual": float(np.max(residual)),
        "atol": wu006.NUMERICAL_ATOL,
        "rtol": wu006.NUMERICAL_RTOL,
        "tolerance_changed_after_execution": False,
    }


def require_accepted_operator_and_representation(
    *, operator_identity: Mapping[str, object], operator_identity_sha256: str,
    metadata: Mapping[str, object],
) -> None:
    accepted_operator = metadata.get("operator_identity")
    accepted_hash = metadata.get("operator_identity_sha256")
    computed = worker.require_observation_null_operator_identity(
        operator_identity, operator_identity
    )
    accepted_computed = worker.require_observation_null_operator_identity(
        accepted_operator, accepted_operator
    ) if isinstance(accepted_operator, Mapping) else None
    if (
        dict(operator_identity) != accepted_operator
        or operator_identity_sha256 != accepted_hash
        or computed != accepted_computed
        or metadata.get("coordinate_frame") != "GALACTIC"
        or metadata.get("map_unit") != "microK_CMB"
        or metadata.get("real_alm_layout_sha256")
        != "sha256:bddf7d6e0cae21e9c8885fe21d623c7c5a38279e6ea25889955e91ae25fdb117"
    ):
        raise Wu007Error("operator or carrier representation differs from accepted primary")


def load_frozen_registry(path: Path = REGISTRY_PATH) -> dict[str, object]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Wu007Error("WU-007 registry is malformed")
    required = {
        "reducers": list(wu006.REDUCERS),
        "families": wu006.family_registry_payload(),
        "source_reducer_registry_sha256": wu006.EXPECTED_COORDINATE_REGISTRY_SHA256,
        "primary_replacement": False,
        "rank_based_promotion_forbidden": True,
    }
    if any(payload.get(key) != value for key, value in required.items()):
        raise Wu007Error("WU-007 registry differs from accepted WU-006")
    return payload


def claim_envelope() -> dict[str, object]:
    return {
        "allowed_claim": (
            "The same observation and frozen feature families were compared against "
            "a separate official 999-row CMB-only FFP10 pool under the same operator; "
            "rank differences are null-ensemble sensitivity only."
        ),
        "artifact_mode": "SEPARATE_CONDITIONAL_NULL_SENSITIVITY_DIAGNOSTIC",
        "bianchi_family_status": "NOT_IDENTIFIED",
        "claim_promotion": False,
        "forbidden_use": [
            "foreground or component-separation validation",
            "local boost versus global tilt identification",
            "physical shear or vorticity inference",
            "Bianchi family identification",
            "unconditional p-value or detection claim",
        ],
        "physical_source_status": "NOT_IDENTIFIED",
        "primary_replacement": False,
        "rank_based_promotion_forbidden": True,
    }


def final_terminal_payload(
    *, pending: Mapping[str, object], review: Mapping[str, object],
    candidate_head: str, candidate_tree: str,
) -> dict[str, object]:
    required_pending = {
        "format": TERMINAL_FORMAT, "work_unit": "PMG-WU-007",
        "state": "EXECUTED_PENDING_REVIEW", "real_host_execution": True,
        "row_count": 1000, "null_row_count": 999, "noise_read_count": 0,
        "replay_status": "MATCH", "raw_data_mutation": False,
        "primary_replacement": False, "claim_promotion": False,
        "fresh_review": "PENDING",
        "unresolved_blockers": ["FRESH_REVIEW_PENDING"],
        "next_executable_action": "FRESH_READ_ONLY_REVIEW",
    }
    if any(pending.get(key) != value for key, value in required_pending.items()):
        raise Wu007Error("pending terminal is not complete")
    figures = review.get("figures")
    if (
        review.get("format") != REVIEW_FORMAT or review.get("state") != "PASS"
        or review.get("P0_remaining") != 0 or review.get("P1_remaining") != 0
        or review.get("candidate_git_head") != candidate_head
        or review.get("candidate_git_tree") != candidate_tree
        or not GIT_RE.fullmatch(candidate_head) or not GIT_RE.fullmatch(candidate_tree)
        or not isinstance(figures, Mapping) or set(figures) != set(FIGURE_FILES)
        or any(
            record != {
                "single_column_3.3in": "PASS",
                "double_column_6.8in": "PASS",
            }
            for record in figures.values()
        )
    ):
        raise Wu007Error("fresh review is not an exact zero-P0/P1 PASS")
    result = dict(pending)
    result.update({
        "state": "SUCCEEDED", "fresh_review": "PASS",
        "P0_remaining": 0, "P1_remaining": 0,
        "candidate_git_head": candidate_head, "candidate_git_tree": candidate_tree,
        "review_repair_count": review.get("repair_rounds_used"),
        "unresolved_blockers": [], "next_executable_action": SUCCESS_NEXT_ACTION,
    })
    return result


def _load_json(path: Path, *, label: str) -> dict[str, object]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Wu007Error(f"{label} is unreadable") from exc
    if not isinstance(payload, dict):
        raise Wu007Error(f"{label} must be a JSON object")
    return payload


def _preflight_content_id(payload: Mapping[str, object]) -> str:
    clone = dict(payload)
    content_id = clone.pop("content_id", None)
    raw = json.dumps(
        clone, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    expected = "sha256:" + hashlib.sha256(raw).hexdigest()
    if content_id != expected:
        raise Wu007Error("preflight content identity drifted")
    return expected


def load_preflight(output: Path, workdir: Path) -> tuple[list[CmbOnlyRow], dict[str, object]]:
    output = Path(output)
    summary = _load_json(output / "preflight_summary.json", label="preflight summary")
    terminal = _load_json(output / "preflight_terminal.json", label="preflight terminal")
    route = _load_json(output / "route_receipt.json", label="preflight route receipt")
    selected = _load_json(
        output / "selected_input_manifest.json", label="selected input manifest"
    )
    for payload in (summary, route, selected):
        _preflight_content_id(payload)
    if (
        summary.get("state") != "PREFLIGHT_SUCCEEDED"
        or summary.get("cmb_complete_count") != 999
        or summary.get("noise_selected_count") != 0
        or summary.get("raw_data_mutation") is not False
        or terminal.get("state") != "PRECONDITION_SUCCEEDED"
        or terminal.get("scientific_execution_state") != "NOT_STARTED"
        or route.get("null_count") != 999
        or route.get("paired_noise_selected") != 0
        or route.get("downloads_performed") != 0
        or route.get("row_00818", {}).get("fits", {}).get("state")
        != "ADMITTED_SEMANTICALLY"
        or selected.get("format") != "PLANCK_MES_SMICA999_SELECTED_INPUTS_V1"
        or selected.get("noise_files_selected") != 0
    ):
        raise Wu007Error("accepted real-host preflight contract is incomplete")
    expected_order = [OBSERVATION_ROW_ID] + [
        f"{ROW_PREFIX}{value}" for value in EXPECTED_CMB_IDS
    ]
    if selected.get("row_order") != expected_order:
        raise Wu007Error("preflight row order differs from the exact 1000-row registry")
    entries = selected.get("null_rows")
    if not isinstance(entries, list) or len(entries) != 999:
        raise Wu007Error("preflight null-row manifest is incomplete")
    raw_root = (Path(workdir) / "raw").resolve(strict=True)
    rows: list[CmbOnlyRow] = []
    for source_id, entry in zip(EXPECTED_CMB_IDS, entries, strict=True):
        if not isinstance(entry, Mapping) or entry.get("row_id") != source_id:
            raise Wu007Error("preflight null-row identity/order drifted")
        path = Path(str(entry.get("resolved_path"))).resolve(strict=True)
        if not path.is_relative_to(raw_root):
            raise Wu007Error("preflight null row escapes the admitted raw root")
        rows.append(CmbOnlyRow(
            row_id=f"{ROW_PREFIX}{source_id}", source_id=source_id,
            path=path, source_identity=dict(entry),
        ))
    validate_cmbonly_rows(rows)
    return rows, {
        "summary_content_id": summary["content_id"],
        "route_content_id": route["content_id"],
        "selected_input_manifest_content_id": selected["content_id"],
        "row_00818_sha256": route["row_00818"]["sha256"],
    }


def _array_digest(value: object) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(array.dtype.str.encode("ascii") + b"\0")
    digest.update(repr(array.shape).encode("ascii") + b"\0")
    digest.update(memoryview(array).cast("B"))
    return "sha256:" + digest.hexdigest()


def load_accepted_observation() -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    rows, row_ids, metadata = wu006._load_accepted_carrier(PRIMARY_CARRIER)
    if row_ids[0] != OBSERVATION_ROW_ID or rows.shape != (301, 32):
        raise Wu007Error("accepted observation carrier row drifted")
    carrier = np.asarray(rows[0], dtype=np.float64)
    scalar = np.asarray(
        worker._component_features_from_real_carrier(carrier), dtype=np.float64
    )
    require_scalar_carrier_closure(scalar.reshape(1, 12), carrier.reshape(1, 32))
    accepted_terminal = _load_json(
        PRIMARY_CARRIER / "terminal.json", label="accepted carrier terminal"
    )
    analysis_terminal = _load_json(
        PRIMARY_ANALYSIS / "terminal.json", label="accepted WU-006 terminal"
    )
    if (
        accepted_terminal.get("state") != "SUCCEEDED"
        or analysis_terminal.get("state") != "SUCCEEDED"
        or analysis_terminal.get("next_executable_action") != "PMG-WU-007"
    ):
        raise Wu007Error("accepted observation/WU-006 authority is not complete")
    return scalar, carrier, metadata


def load_accepted_operator_context(
    workdir: Path, metadata: Mapping[str, object]
) -> tuple[dict[str, object], dict[str, object]]:
    component_dir = (
        Path(workdir)
        / "compact_products/planck_pr3_smica_pr314/components"
    )
    if component_dir.is_symlink() or not component_dir.is_dir():
        raise Wu007Error("accepted compact operator inputs are missing or unsafe")
    mask = np.load(component_dir / "smica_mask.npy", allow_pickle=False)
    beam = np.load(component_dir / "smica_beam.npy", allow_pickle=False)
    with np.load(component_dir / "smica_window_operator.npz", allow_pickle=False) as bundle:
        if set(bundle.files) != {
            "source_pixel_window", "target_beam", "target_pixel_window"
        }:
            raise Wu007Error("accepted compact transfer schema drifted")
        window = {name: np.asarray(bundle[name]) for name in bundle.files}
    transfer = {
        "source_beam_sha256": _array_digest(beam),
        "source_pixel_window_sha256": _array_digest(window["source_pixel_window"]),
        "target_beam_sha256": _array_digest(window["target_beam"]),
        "target_pixel_window_sha256": _array_digest(window["target_pixel_window"]),
    }
    if transfer != metadata.get("transfer_identity"):
        raise Wu007Error("compact beam/pixel transfer differs from accepted primary")
    context = worker.build_smica_joint_cutsky_context(
        smica_map=np.zeros(mask.shape, dtype=np.float64),
        mask=mask,
        beam=beam,
        window=window,
        declared_nside=16,
    )
    operator = worker.joint_cutsky_operator_identity(context)
    carrier_operator_id = str(metadata.get("operator_identity_sha256"))
    require_accepted_operator_and_representation(
        operator_identity=operator,
        operator_identity_sha256=carrier_operator_id,
        metadata=metadata,
    )
    receipt = {
        "format": "PLANCK_MES_SMICA999_OPERATOR_RECEIPT_V1",
        "state": "MATCH_ACCEPTED_PRIMARY",
        "operator_identity": operator,
        "carrier_operator_identity_sha256": carrier_operator_id,
        "fit_operator_identity_sha256": worker.require_observation_null_operator_identity(
            operator, operator
        ),
        "transfer_identity": transfer,
        "coordinate_frame": metadata["coordinate_frame"],
        "map_unit": metadata["map_unit"],
        "real_alm_layout_sha256": metadata["real_alm_layout_sha256"],
        "observation_map_reopened": False,
    }
    receipt["content_id"] = _canonical_content_id(
        receipt, role="planck_mes_smica999_operator_receipt"
    )
    return context, receipt


def read_reduce_cmb(path: Path) -> np.ndarray:
    from scripts.observed_runs import prepare_planck_pr3_admission as preparation

    payload = preparation.read_temperature_fits(
        Path(path), allowed_column_names=("INTENSITY",),
        declared_coordinate_frame="GALACTIC",
    )
    return preparation.reduce_temperature_map(
        payload.values, source_unit=payload.unit,
        source_ordering=payload.ordering, output_nside=16,
    )


def compute_irrep_arrays(
    *, carrier_rows: np.ndarray, scalar_features: np.ndarray,
    row_ids: Sequence[str], metadata: Mapping[str, object],
) -> tuple[dict[str, np.ndarray], list[dict[str, object]], list[object], float]:
    carriers = np.asarray(carrier_rows, dtype=np.float64)
    scalars = np.asarray(scalar_features, dtype=np.float64)
    count = len(row_ids)
    if carriers.shape != (count, 32) or scalars.shape != (count, 12):
        raise Wu007Error("portable scalar/carrier row matrices are incomplete")
    source_identity = _array_content_id(
        {"carrier_rows": carriers, "row_ids": np.asarray(row_ids, dtype="U64")},
        role="planck_mes_smica999_carrier",
    )
    q_components = np.empty((count, 5), dtype=np.float64)
    o_components = np.empty((count, 7), dtype=np.float64)
    coordinate_values = np.full(
        (count, len(wu006.ALL_COORDINATE_IDS)), np.nan, dtype=np.float64
    )
    availability = np.zeros(coordinate_values.shape, dtype=np.bool_)
    frame_free = np.empty(
        (count, len(wu006.FRAME_FREE_FEATURE_IDS)), dtype=np.float64
    )
    orientation = np.empty(
        (count, len(wu006.GALACTIC_ORIENTATION_FEATURE_IDS)), dtype=np.float64
    )
    state_ids: list[str] = []
    degeneracy_rows: list[dict[str, object]] = []
    reports: list[object] = []
    max_roundtrip = 0.0
    for row_index, (components, row_id) in enumerate(
        zip(carriers, row_ids, strict=True)
    ):
        carrier = wu006.ObservableIrrepCarrier(
            components=tuple(float(value) for value in components),
            frame=str(metadata["coordinate_frame"]),
            basis="ORTHONORMAL_CONDON_SHORTLEY_REAL_L2_L5_V1",
            units=str(metadata["map_unit"]),
            source_identity=source_identity,
            operator_identity=str(metadata["operator_identity_sha256"]),
            row_identity=str(row_id),
        )
        state = wu006.project_planck_carrier_to_observable_irreps(carrier)
        q = np.asarray(state.blocks[0].components, dtype=np.float64)
        o = np.asarray(state.blocks[1].components, dtype=np.float64)
        q_components[row_index] = q
        o_components[row_index] = o
        q_residual = float(np.max(np.abs(
            wu006.stf2_to_real_harmonic(wu006.stf2_components_to_tensor(q))
            - components[:5]
        )))
        o_residual = float(np.max(np.abs(
            wu006.stf3_to_real_harmonic(wu006.stf3_components_to_tensor(o))
            - components[5:12]
        )))
        residual = max(q_residual, o_residual)
        max_roundtrip = max(max_roundtrip, residual)
        scale = max(1.0, float(np.max(np.abs(components[:12]))))
        if residual > wu006.NUMERICAL_ATOL + wu006.NUMERICAL_RTOL * scale:
            raise Wu007Error(f"harmonic-STF roundtrip failed for row {row_id}")
        report = wu006.observable_irrep_orbit_report(state)
        reports.append(report)
        state_ids.append(state.content_id)
        absent: list[str] = []
        for column, feature_id in enumerate(wu006.ALL_COORDINATE_IDS):
            coordinate = report.coordinate(feature_id)
            if coordinate.status == "AVAILABLE":
                coordinate_values[row_index, column] = float(coordinate.value)
                availability[row_index, column] = True
            else:
                absent.append(feature_id)
        try:
            frame_free[row_index] = wu006.orbit_family_vector(
                report, wu006.FRAME_FREE_FAMILY_ID
            )
            orientation[row_index] = wu006.orbit_family_vector(
                report, wu006.GALACTIC_ORIENTATION_FAMILY_ID
            )
            disposition = "COMPLETE"
        except ValueError:
            disposition = "TYPED_ABSENCE"
        degeneracy_rows.append({
            "absent_feature_ids": json.dumps(absent, separators=(",", ":")),
            "krylov_plane_status": report.krylov_plane_status,
            "krylov_rank": report.krylov_rank,
            "mixed_vector_status": report.mixed_vector_status,
            "primary_family_disposition": disposition,
            "q_spectrum_status": report.q_spectrum_status,
            "row_id": row_id,
            "row_index": row_index,
        })
    unavailable = [
        str(row["row_id"]) for row in degeneracy_rows
        if row["primary_family_disposition"] != "COMPLETE"
    ]
    if unavailable:
        raise Wu007Error(
            "typed-absent primary-family rows cannot be zero-filled or dropped: "
            + ",".join(unavailable)
        )
    arrays = {
        "all_coordinate_values": coordinate_values,
        "carrier_rows": carriers,
        "coordinate_availability": availability,
        "coordinate_ids": np.asarray(wu006.ALL_COORDINATE_IDS, dtype="U32"),
        "frame_free_features": frame_free,
        "o_components": o_components,
        "orientation_features": orientation,
        "q_components": q_components,
        "row_ids": np.asarray(row_ids, dtype="U64"),
        "scalar_features": scalars,
        "state_content_ids": np.asarray(state_ids, dtype="U71"),
    }
    return arrays, degeneracy_rows, reports, max_roundtrip


def _make_plots(
    output: Path, *, family_results: Mapping[str, Mapping[str, Mapping[str, object]]],
    distributions: Mapping[str, np.ndarray], dependence: Mapping[str, object],
    denominator: int,
) -> None:
    plt = wu006.plt
    labels = {
        "LEGACY_ABSOLUTE_MEDIAN_V1": "Legacy abs-median",
        "LOO_ECDF_MIDRANK_V1": "LOO-ECDF midrank",
    }
    coordinate_labels = (
        r"$q_2$", r"$o_2$", r"$J_Q$", r"$\widehat R_{v0}$",
        r"$\widehat R_{v1}$", r"$\widehat R_{v2}$", r"$\widehat R_{QS}$",
        r"$\widehat K_v$",
    )
    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    x = np.arange(len(wu006.FRAME_FREE_FEATURE_IDS))
    for reducer_id, marker in zip(wu006.REDUCERS, ("o", "s"), strict=True):
        numerators = family_results[wu006.FRAME_FREE_FAMILY_ID][reducer_id][
            "local_rank_numerators"
        ]
        ax.plot(x, np.asarray(numerators) / denominator, marker=marker,
                label=labels[reducer_id])
    ax.set_xticks(x, coordinate_labels, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("Observation-inclusive local rank")
    ax.set_title("SMICA observation in the CMB-only 999 pool")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(output / FIGURE_FILES[0])
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    family_ids = (
        wu006.FRAME_FREE_FAMILY_ID, wu006.GALACTIC_ORIENTATION_FAMILY_ID
    )
    x = np.arange(2)
    width = 0.34
    for offset, reducer_id in zip((-width / 2, width / 2), wu006.REDUCERS, strict=True):
        values = [
            family_results[family_id][reducer_id]["global_rank_numerator"]
            / denominator for family_id in family_ids
        ]
        ax.bar(x + offset, values, width=width, label=labels[reducer_id])
    ax.set_xticks(x, ("Frame-free", "+ Galactic orientation"))
    ax.set_ylabel("Observation-inclusive family rank")
    ax.set_title("Frozen families under a separate CMB-only null")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(output / FIGURE_FILES[1])
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.2), sharex=False)
    panel_labels = (
        "Frame-free / Legacy", "Frame-free / LOO-ECDF",
        "Galactic companion / Legacy", "Galactic companion / LOO-ECDF",
    )
    score_distributions = tuple(
        value for key, value in distributions.items()
        if key.endswith("__row_max_scores")
    )
    for axis, values, label in zip(
        axes.flat, score_distributions, panel_labels, strict=True
    ):
        axis.hist(values[1:], bins=30, color="#4c72b0", alpha=0.75)
        axis.axvline(values[0], color="#c44e52", linewidth=1.2, label="observed")
        axis.set_title(label, fontsize=8)
        axis.legend(fontsize=6)
    fig.suptitle("CMB-only complete-pool row-score distributions", fontsize=10)
    fig.tight_layout()
    fig.savefig(output / FIGURE_FILES[2])
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for family_id, marker in zip(family_ids, ("o", "s"), strict=True):
        eigenvalues = dependence[family_id]["spearman_eigenvalues_descending"]
        label = "Frame-free" if family_id == family_ids[0] else "+ Galactic orientation"
        ax.plot(np.arange(1, len(eigenvalues) + 1), eigenvalues,
                marker=marker, label=label)
    ax.set_xlabel("Spearman correlation eigenvalue index")
    ax.set_ylabel("Eigenvalue")
    ax.set_title("CMB-only coordinate dependence spectrum")
    ax.legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(output / FIGURE_FILES[3])
    plt.close(fig)


def build_portable_analysis(
    *, output: Path, execution: ExecutionRows, metadata: Mapping[str, object],
    preflight_binding: Mapping[str, object], operator_receipt: Mapping[str, object],
    scalar_closure: Mapping[str, object], primary_before: Mapping[str, str],
    primary_after: Mapping[str, str], checkpoint_reused_count: int,
) -> dict[str, object]:
    output = Path(output)
    load_frozen_registry()
    if primary_before != primary_after:
        raise Wu007Error("accepted paired-300 primary changed during WU-007")
    arrays, degeneracy_rows, reports, max_roundtrip = compute_irrep_arrays(
        carrier_rows=execution.carrier_rows,
        scalar_features=execution.scalar_features,
        row_ids=execution.row_ids,
        metadata=metadata,
    )
    family_results, distributions = wu006._run_scans(
        arrays["frame_free_features"], arrays["orientation_features"],
        observation_index=0,
    )
    dependence, dependence_rows = wu006._dependence_diagnostics({
        wu006.FRAME_FREE_FAMILY_ID: arrays["frame_free_features"],
        wu006.GALACTIC_ORIENTATION_FAMILY_ID: arrays["orientation_features"],
    })
    _, family_rows = wu006._make_tables(
        reports=reports, family_results=family_results,
        degeneracy_rows=degeneracy_rows, dependence_rows=dependence_rows,
    )
    _atomic_npz(output / "observable_irreps.npz", arrays)
    _atomic_npz(output / "null_distributions.npz", distributions)
    _write_csv(output / "family_table.csv", family_rows)
    _write_csv(output / "degeneracy_ledger.csv", degeneracy_rows)
    _write_csv(output / "dependence_spectrum.csv", dependence_rows)
    registry = load_frozen_registry()
    observable_metadata: dict[str, object] = {
        "format": "PLANCK_MES_SMICA_CMBONLY_999_OBSERVABLE_IRREPS_V1",
        "row_count": 1000,
        "null_row_count": 999,
        "row_ids_content_id": _canonical_content_id(
            list(execution.row_ids), role="planck_mes_smica999_row_ids"
        ),
        "numerical_content_id": _array_content_id(
            arrays, role="planck_mes_smica999_observable_irreps"
        ),
        "scalar_carrier_closure": dict(scalar_closure),
        "projection_identity": wu006.PROJECTION_IDENTITY,
        "coordinate_frame": metadata["coordinate_frame"],
        "map_unit": metadata["map_unit"],
        "real_alm_layout_sha256": metadata["real_alm_layout_sha256"],
        "operator_receipt_content_id": operator_receipt["content_id"],
        "registry_source_sha256": registry["source_reducer_registry_sha256"],
        "observation_source": "REUSED_ACCEPTED_ONE_PASS_CARRIER_NO_MAP_REOPEN",
        "null_source": "OFFICIAL_FFP10_SMICA_CMB_ONLY_999",
        "noise_read_count": 0,
        "same_pass_scalar_and_carrier": True,
    }
    observable_metadata["content_id"] = _canonical_content_id(
        observable_metadata, role="planck_mes_smica999_observable_metadata"
    )
    _atomic_json(output / "observable_irreps.json", observable_metadata)
    primary_result = _load_json(
        PRIMARY_ANALYSIS / "result.json", label="accepted WU-006 result"
    )
    sensitivity: dict[str, object] = {}
    for family_id, reducers in family_results.items():
        sensitivity[family_id] = {}
        for reducer_id, record in reducers.items():
            primary_record = primary_result["family_results"][family_id][reducer_id]
            sensitivity[family_id][reducer_id] = {
                "paired300_rank": primary_record["global_rank"],
                "cmbonly999_rank": record["global_rank"],
                "paired300_fraction": primary_record["global_rank_numerator"] / 301.0,
                "cmbonly999_fraction": record["global_rank_numerator"] / 1000.0,
                "descriptive_fraction_difference_cmbonly_minus_paired": (
                    record["global_rank_numerator"] / 1000.0
                    - primary_record["global_rank_numerator"] / 301.0
                ),
                "interpretation": "DESCRIPTIVE_NULL_ENSEMBLE_SENSITIVITY_NOT_AN_INDEPENDENT_TEST",
            }
    result: dict[str, object] = {
        "format": OUTPUT_FORMAT,
        "work_unit": "PMG-WU-007",
        "state": "EXECUTED_PENDING_REVIEW",
        "owner": "OBSSTAT",
        "scope": (
            "same-observation frozen-irrep calibration against the separate official "
            "999-row SMICA CMB-only FFP10 pool"
        ),
        "artifact_mode": "SEPARATE_CONDITIONAL_NULL_SENSITIVITY_DIAGNOSTIC",
        "row_count": 1000,
        "null_row_count": 999,
        "observation_row_count": 1,
        "null_status": "EXACT_ORDERED_FFP10_SMICA_CMB_ONLY_999_CONDITIONAL",
        "known_missing_ids": ["00970"],
        "included_special_ids": ["00818"],
        "noise_read_count": 0,
        "family_results": family_results,
        "paired300_sensitivity_comparison": sensitivity,
        "dependence_diagnostics": dependence,
        "harmonic_stf_roundtrip": {
            "status": "PASS", "max_absolute_residual": max_roundtrip,
            "atol": wu006.NUMERICAL_ATOL, "rtol": wu006.NUMERICAL_RTOL,
        },
        "numerical_outputs": {
            "observable_irreps_content_id": observable_metadata["numerical_content_id"],
            "null_distributions_content_id": _array_content_id(
                distributions, role="planck_mes_smica999_null_distributions"
            ),
        },
        "preflight_binding": dict(preflight_binding),
        "operator_receipt_content_id": operator_receipt["content_id"],
        "checkpoint_reused_count": checkpoint_reused_count,
        "selection_policy": registry["selection_policy"],
        "reducers": list(wu006.REDUCERS),
        "families": wu006.family_registry_payload(),
        "raw_maps_reopened_by_replay": False,
        "observation_map_reopened": False,
        "raw_data_mutation": False,
        **claim_envelope(),
    }
    result["content_id"] = _canonical_content_id(
        result, role="planck_mes_smica999_result"
    )
    _atomic_json(output / "result.json", result)
    _atomic_json(output / "operator_identity_receipt.json", dict(operator_receipt))
    _atomic_json(output / "scalar_closure.json", dict(scalar_closure))
    primary_receipt = {
        "format": "PLANCK_MES_SMICA999_PRIMARY_SEPARATION_V1",
        "state": "MATCH_UNCHANGED",
        "primary_role": "PAIRED300_PRIMARY",
        "wu007_role": "SEPARATE_CMBONLY999_ROBUSTNESS",
        "primary_artifact_sha256": dict(primary_after),
        "primary_replacement": False,
    }
    primary_receipt["content_id"] = _canonical_content_id(
        primary_receipt, role="planck_mes_smica999_primary_separation"
    )
    _atomic_json(output / "primary_separation_receipt.json", primary_receipt)
    _make_plots(
        output, family_results=family_results, distributions=distributions,
        dependence=dependence, denominator=1000,
    )
    plot_audit = {
        "format": "PLANCK_MES_SMICA999_PLOT_AUDIT_V1",
        "state": "PENDING_EXTERNAL_DIRECT_INSPECTION",
        "result_content_id": result["content_id"],
        "figures": {
            name: {
                "sha256": _sha256(output / name),
                "single_column_3.3in": "PENDING",
                "double_column_6.8in": "PENDING",
            } for name in FIGURE_FILES
        },
        "generator_self_attestation": False,
    }
    _atomic_json(output / "plot_audit.json", plot_audit)
    replay = replay_directory(output, write_receipt=False)
    _atomic_json(output / "replay.json", replay)
    objective_names = sorted(
        path.name for path in output.iterdir()
        if path.is_file() and path.name not in {
            "terminal.json", "preflight_terminal.json"
        }
    )
    terminal = {
        "format": TERMINAL_FORMAT,
        "work_unit": "PMG-WU-007",
        "state": "EXECUTED_PENDING_REVIEW",
        "real_host_execution": True,
        "row_count": 1000,
        "null_row_count": 999,
        "noise_read_count": 0,
        "replay_status": "MATCH",
        "scalar_closure": "MATCH",
        "raw_data_mutation": False,
        "primary_replacement": False,
        "claim_promotion": False,
        "fresh_review": "PENDING",
        "P0_remaining": None,
        "P1_remaining": None,
        "objective_artifact_sha256": {
            name: _sha256(output / name) for name in objective_names
        },
        "unresolved_blockers": ["FRESH_REVIEW_PENDING"],
        "next_executable_action": "FRESH_READ_ONLY_REVIEW",
    }
    _atomic_json(output / "terminal.json", terminal)
    return result


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    try:
        with np.load(path, allow_pickle=False) as bundle:
            return {name: np.asarray(bundle[name]) for name in bundle.files}
    except (OSError, ValueError, KeyError) as exc:
        raise Wu007Error(f"numerical artifact is unreadable: {path.name}") from exc


def replay_directory(output: Path = DEFAULT_OUTPUT, *, write_receipt: bool = False) -> dict[str, object]:
    """Replay the WU-007 package from portable rows without opening maps."""

    output = Path(output)
    arrays = _load_npz(output / "observable_irreps.npz")
    metadata = _load_json(
        output / "observable_irreps.json", label="observable-irrep metadata"
    )
    result = _load_json(output / "result.json", label="WU-007 result")
    operator = _load_json(
        output / "operator_identity_receipt.json", label="operator receipt"
    )
    metadata_without_id = dict(metadata)
    metadata_id = metadata_without_id.pop("content_id", None)
    if metadata_id != _canonical_content_id(
        metadata_without_id, role="planck_mes_smica999_observable_metadata"
    ):
        raise Wu007Error("observable metadata content identity differs")
    result_without_id = dict(result)
    result_id = result_without_id.pop("content_id", None)
    if result_id != _canonical_content_id(
        result_without_id, role="planck_mes_smica999_result"
    ):
        raise Wu007Error("result content identity differs")
    if metadata.get("numerical_content_id") != _array_content_id(
        arrays, role="planck_mes_smica999_observable_irreps"
    ):
        raise Wu007Error("observable numerical content identity differs")
    expected_keys = {
        "all_coordinate_values", "carrier_rows", "coordinate_availability",
        "coordinate_ids", "frame_free_features", "o_components",
        "orientation_features", "q_components", "row_ids", "scalar_features",
        "state_content_ids",
    }
    if set(arrays) != expected_keys:
        raise Wu007Error("observable numerical schema differs")
    row_ids = tuple(str(value) for value in arrays["row_ids"].tolist())
    expected_ids = (
        OBSERVATION_ROW_ID,
        *(f"{ROW_PREFIX}{value}" for value in EXPECTED_CMB_IDS),
    )
    if row_ids != expected_ids:
        raise Wu007Error("portable row order differs from exact CMB-only registry")
    closure = require_scalar_carrier_closure(
        arrays["scalar_features"], arrays["carrier_rows"]
    )
    projection_metadata = {
        "coordinate_frame": metadata["coordinate_frame"],
        "map_unit": metadata["map_unit"],
        "operator_identity_sha256": operator["carrier_operator_identity_sha256"],
    }
    recomputed, _, _, _ = compute_irrep_arrays(
        carrier_rows=arrays["carrier_rows"],
        scalar_features=arrays["scalar_features"],
        row_ids=row_ids,
        metadata=projection_metadata,
    )
    for name in expected_keys:
        left, right = arrays[name], recomputed[name]
        if left.shape != right.shape or left.dtype.kind != right.dtype.kind:
            raise Wu007Error(f"map-free replay structure differs: {name}")
        if left.dtype.kind in "fc":
            if not np.allclose(
                left, right, rtol=wu006.NUMERICAL_RTOL,
                atol=wu006.NUMERICAL_ATOL, equal_nan=True,
            ):
                raise Wu007Error(f"map-free replay numerics differ: {name}")
        elif not np.array_equal(left, right):
            raise Wu007Error(f"map-free replay decoded content differs: {name}")
    family_results, _ = wu006._run_scans(
        recomputed["frame_free_features"], recomputed["orientation_features"],
        observation_index=0,
    )
    if family_results != result.get("family_results"):
        raise Wu007Error("map-free family ranks differ")
    primary_receipt = _load_json(
        output / "primary_separation_receipt.json", label="primary separation receipt"
    )
    if (
        primary_receipt.get("state") != "MATCH_UNCHANGED"
        or primary_receipt.get("primary_replacement") is not False
        or primary_receipt.get("primary_artifact_sha256")
        != snapshot_primary_artifacts(PRIMARY_CARRIER, PRIMARY_ANALYSIS)
    ):
        raise Wu007Error("paired-300 primary separation no longer matches")
    replay: dict[str, object] = {
        "format": "PLANCK_MES_SMICA_CMBONLY_999_REPLAY_V1",
        "status": "MATCH",
        "identity_policy": "TYPED_IDENTITY_V1",
        "input_inventory_identity": "MATCH_PREFLIGHT_CONTENT",
        "numerical_output_identity": "NUMERICALLY_EQUIVALENT",
        "result_content_id": result_id,
        "scalar_closure": closure,
        "raw_maps_reopened": False,
        "noise_maps_read": 0,
        "primary_replacement": False,
        "claim_promotion": False,
    }
    if write_receipt:
        _atomic_json(output / "replay.json", replay)
    return replay


def execute_real_host(*, repo_root: Path, workdir: Path, output: Path) -> dict[str, object]:
    repo_root = Path(repo_root).resolve(strict=True)
    workdir = Path(workdir)
    output = Path(output)
    if (
        not workdir.is_absolute() or workdir.is_symlink() or not workdir.is_dir()
        or workdir.resolve(strict=True) != workdir
    ):
        raise Wu007Error("workdir must be an absolute non-symlink directory")
    raw_root = workdir / "raw"
    if raw_root.is_symlink() or not raw_root.is_dir():
        raise Wu007Error("raw root is missing or unsafe")
    require_separate_output_boundary(output)
    if not output.is_dir() or output.is_symlink():
        raise Wu007Error("successful preflight output directory is required")
    allowed_initial = {
        "preflight_summary.json", "preflight_terminal.json",
        "route_receipt.json", "selected_input_manifest.json",
    }
    if {path.name for path in output.iterdir()} != allowed_initial:
        raise Wu007Error("WU-007 output contains non-preflight artifacts; use replay")
    rows, preflight_binding = load_preflight(output, workdir)
    primary_before = snapshot_primary_artifacts(PRIMARY_CARRIER, PRIMARY_ANALYSIS)
    observed_features, observed_carrier, carrier_metadata = load_accepted_observation()
    context, operator_receipt = load_accepted_operator_context(
        workdir, carrier_metadata
    )
    operator_id = str(operator_receipt["carrier_operator_identity_sha256"])

    def verify_row(row: CmbOnlyRow) -> None:
        require_stat_identity(row.path, row.source_identity)

    def read_row(path: Path) -> np.ndarray:
        row = next(value for value in rows if value.path == path)
        verify_row(row)
        return read_reduce_cmb(path)

    checkpoint_dir = workdir / "analysis/planck_mes_irrep/smica999/carrier_rows"
    started = time.monotonic()
    execution = process_null_rows_one_pass(
        observed_features=observed_features,
        observed_carrier=observed_carrier,
        rows=rows,
        context=context,
        operator_identity_sha256=operator_id,
        read_cmb=read_row,
        process_map=worker._process_map,
        carrier_from_alm=carrier_vector_from_alm,
        checkpoint_dir=checkpoint_dir,
        verify_source_unchanged=verify_row,
    )
    elapsed = time.monotonic() - started
    for row in rows:
        verify_row(row)
    closure = require_scalar_carrier_closure(
        execution.scalar_features, execution.carrier_rows
    )
    primary_after = snapshot_primary_artifacts(PRIMARY_CARRIER, PRIMARY_ANALYSIS)
    if primary_after != primary_before:
        raise Wu007Error("accepted paired-300 primary changed during execution")
    private_manifest = {
        "format": "PLANCK_MES_SMICA999_PRIVATE_EXECUTION_MANIFEST_V1",
        "state": "SUCCEEDED",
        "row_count": 1000,
        "null_row_count": 999,
        "noise_read_count": 0,
        "row_ids": list(execution.row_ids),
        "operator_identity_sha256": operator_id,
        "preflight_binding": preflight_binding,
        "source_identities": [dict(row.source_identity) for row in rows],
        "checkpoint_reused_count": execution.checkpoint_reused_count,
        "elapsed_seconds": elapsed,
        "raw_data_mutation": False,
        "observation_map_reopened": False,
    }
    _atomic_json(
        workdir / "analysis/planck_mes_irrep/smica999/execution_manifest.json",
        private_manifest,
    )
    result = build_portable_analysis(
        output=output, execution=execution, metadata=carrier_metadata,
        preflight_binding=preflight_binding, operator_receipt=operator_receipt,
        scalar_closure=closure, primary_before=primary_before,
        primary_after=primary_after,
        checkpoint_reused_count=execution.checkpoint_reused_count,
    )
    return result


def _git_identity(repo_root: Path) -> tuple[str, str]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, check=True,
        text=True, capture_output=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"], cwd=repo_root, check=True,
        text=True, capture_output=True,
    ).stdout.strip()
    if not GIT_RE.fullmatch(head) or not GIT_RE.fullmatch(tree):
        raise Wu007Error("candidate Git identity is malformed")
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo_root, check=True,
        text=True, capture_output=True,
    ).stdout
    if status:
        raise Wu007Error("fresh-review finalization requires a clean candidate")
    return head, tree


def finalize_reviewed(*, output: Path, review_path: Path) -> dict[str, object]:
    output = Path(output)
    head, tree = _git_identity(ROOT)
    pending = _load_json(output / "terminal.json", label="pending WU-007 terminal")
    review = _load_json(review_path, label="external fresh review")
    result = _load_json(output / "result.json", label="WU-007 result")
    if (
        review.get("result_content_id") != result.get("content_id")
        or review.get("artifact_sha256") != pending.get("objective_artifact_sha256")
        or review.get("repair_rounds_used") not in {0, 1}
    ):
        raise Wu007Error("fresh review artifact/result binding differs")
    final = final_terminal_payload(
        pending=pending, review=review, candidate_head=head, candidate_tree=tree
    )
    replay = replay_directory(output, write_receipt=False)
    review_bytes = Path(review_path).read_bytes()
    fresh_path = output / "fresh_review.json"
    if fresh_path.exists() or fresh_path.is_symlink():
        raise Wu007Error("fresh-review destination already exists")
    fresh_path.write_bytes(review_bytes)
    plot = _load_json(output / "plot_audit.json", label="plot audit")
    plot["state"] = "PASS_EXTERNAL_DIRECT_INSPECTION"
    plot["review_candidate_git_head"] = head
    plot["review_candidate_git_tree"] = tree
    for name in FIGURE_FILES:
        plot["figures"][name]["single_column_3.3in"] = "PASS"
        plot["figures"][name]["double_column_6.8in"] = "PASS"
    _atomic_json(output / "plot_audit.json", plot)
    final.update({
        "fresh_review_receipt_sha256": _sha256(fresh_path),
        "result_content_id": result["content_id"],
        "map_free_replay": replay,
        "objective_artifact_sha256": {
            path.name: _sha256(path) for path in sorted(output.iterdir())
            if path.is_file() and path.name != "terminal.json"
        },
    })
    _atomic_json(output / "terminal.json", final)
    return final


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute-real-host", action="store_true")
    mode.add_argument("--replay-committed", action="store_true")
    mode.add_argument("--finalize-reviewed", action="store_true")
    parser.add_argument("--workdir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fresh-review", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.execute_real_host:
            if args.workdir is None or args.fresh_review is not None:
                parser.error("--execute-real-host requires --workdir only")
            payload = execute_real_host(
                repo_root=ROOT, workdir=args.workdir, output=args.output_dir
            )
        elif args.replay_committed:
            if args.workdir is not None or args.fresh_review is not None:
                parser.error("--replay-committed accepts no workdir/review")
            payload = replay_directory(args.output_dir, write_receipt=False)
        else:
            if args.workdir is not None or args.fresh_review is None:
                parser.error("--finalize-reviewed requires --fresh-review only")
            payload = finalize_reviewed(
                output=args.output_dir, review_path=args.fresh_review
            )
    except Wu007Error as exc:
        print(json.dumps({"state": "BLOCKED", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
