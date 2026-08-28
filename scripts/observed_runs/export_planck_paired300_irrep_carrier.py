#!/usr/bin/env python3
"""Execute and replay the exact paired-300 Planck irrep carrier.

The public helpers in this module are deliberately data independent.  The
real-host CLI is added below them so the fixed leakage registry, resumable
private checkpoints, and terminal boundary can be tested without opening a
Planck map.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Callable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "htt", ROOT / "htt/src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import numpy as np

from obsstat.planck_irrep_carrier import EXPECTED_DIMENSION


_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_PORTABLE_OUTPUTS = frozenset(
    {
        "carrier.npz",
        "metadata.json",
        "scalar_closure.json",
        "input_identity_receipt.json",
        "leakage_receipt.json",
        "replay.json",
        "terminal.json",
    }
)
_TERMINAL_REQUIRED = {
    "work_unit": "PMG-WU-005",
    "state": "SUCCEEDED",
    "real_host_execution": True,
    "replay_status": "MATCH",
    "scalar_closure": "MATCH",
    "raw_data_mutation": False,
    "claim_promotion": False,
    "unresolved_blockers": [],
    "next_executable_action": "PMG-WU-006",
    "fresh_review": "PASS",
}


class CarrierExportError(RuntimeError):
    """Raised when PMG-WU-005 execution or portable output drifts."""


def _require_sha256(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise CarrierExportError(f"{label} must be one sha256 identity")
    return value


def _json_clone(value: object, *, label: str) -> object:
    try:
        return json.loads(
            json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
        )
    except (TypeError, ValueError) as exc:
        raise CarrierExportError(f"{label} is not canonical JSON") from exc


def _numeric_content_id(value: object, *, role: str) -> str:
    """Bind decoded numerical content rather than container serialization."""

    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(role.encode("ascii") + b"\0")
    digest.update(array.dtype.str.encode("ascii") + b"\0")
    digest.update(repr(array.shape).encode("ascii") + b"\0")
    digest.update(memoryview(array).cast("B"))
    return "sha256:" + digest.hexdigest()


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    encoded = (
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")
    try:
        with temporary.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_npz(path: Path, **values: np.ndarray) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as handle:
            np.savez(handle, **values)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def fixed_leakage_probe_layout() -> tuple[tuple[int, int, str], ...]:
    """Return the pre-observation complete real basis for ell=6 and ell=7."""

    return tuple(
        (ell, m, component)
        for ell in (6, 7)
        for m in range(ell + 1)
        for component in (("real",) if m == 0 else ("real", "imag"))
    )


def evaluate_fixed_leakage_probes(
    *,
    operator_identity_sha256: str,
    fit_probe: Callable[[int, int, str], np.ndarray],
) -> dict[str, object]:
    """Evaluate every fixed omitted-shell probe once with the supplied fit."""

    operator_id = _require_sha256(
        operator_identity_sha256,
        label="leakage operator identity",
    )
    probes = fixed_leakage_probe_layout()
    retained: list[np.ndarray] = []
    for ell, m, component in probes:
        value = np.asarray(fit_probe(ell, m, component), dtype=np.float64)
        if value.shape != (EXPECTED_DIMENSION,) or not np.all(np.isfinite(value)):
            raise CarrierExportError(
                "leakage fit must return one finite 32-real carrier"
            )
        retained.append(value.copy())
    matrix = np.asarray(retained, dtype=np.float64)
    return {
        "format": "PLANCK_PR3_PAIRED300_LEAKAGE_DIAGNOSTIC_V1",
        "probe_definition": "COMPLETE_REAL_BASIS_ELL6_ELL7_V1",
        "probe_count": len(probes),
        "input_amplitude": 1.0,
        "input_unit": "microK_CMB",
        "operator_identity_sha256": operator_id,
        "probes": [list(probe) for probe in probes],
        "retained_real_alm": matrix.tolist(),
        "retained_l2_l5_max_abs": float(np.max(np.abs(matrix))),
        "retained_l2_l5_max_l2_norm": float(
            np.max(np.linalg.norm(matrix, axis=1))
        ),
        "scope": "fixed ell>5 leakage probe diagnostic",
        "exhaustive_beyond_ell7": False,
        "correction_applied": False,
        "claim_promotion": False,
    }


def _checkpoint_metadata_path(path: Path) -> Path:
    return Path(path).with_suffix(".json")


def write_private_row_checkpoint(
    *,
    path: Path,
    ordinal: int,
    row_id: str,
    features: object,
    carrier: object,
    source_identities: Sequence[Mapping[str, object]],
    operator_identity_sha256: str,
) -> None:
    """Write one content-bound, private, resumable row checkpoint."""

    path = Path(path)
    if path.suffix != ".npz" or path.exists() or path.is_symlink():
        raise CarrierExportError("private checkpoint output must be a new NPZ")
    metadata_path = _checkpoint_metadata_path(path)
    if metadata_path.exists() or metadata_path.is_symlink():
        raise CarrierExportError("private checkpoint metadata already exists")
    if type(ordinal) is not int or ordinal < 0 or not isinstance(row_id, str) or not row_id:
        raise CarrierExportError("private checkpoint row identity is malformed")
    feature_row = np.asarray(features)
    carrier_row = np.asarray(carrier)
    if feature_row.dtype != np.dtype("float64") or feature_row.shape != (12,):
        raise CarrierExportError("private checkpoint feature row drifted")
    if carrier_row.dtype != np.dtype("float64") or carrier_row.shape != (
        EXPECTED_DIMENSION,
    ):
        raise CarrierExportError("private checkpoint carrier row drifted")
    if not np.all(np.isfinite(feature_row)) or not np.all(np.isfinite(carrier_row)):
        raise CarrierExportError("private checkpoint row became nonfinite")
    identities = _json_clone(list(source_identities), label="source identities")
    if not isinstance(identities, list) or not identities:
        raise CarrierExportError("private checkpoint source identity is missing")
    operator_id = _require_sha256(
        operator_identity_sha256,
        label="checkpoint operator identity",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise CarrierExportError("private checkpoint directory cannot be a symlink")
    _atomic_npz(path, features=feature_row, carrier=carrier_row)
    _atomic_json(
        metadata_path,
        {
            "format": "PLANCK_PR3_PAIRED300_PRIVATE_ROW_CHECKPOINT_V1",
            "state": "SUCCEEDED",
            "ordinal": ordinal,
            "row_id": row_id,
            "operator_identity_sha256": operator_id,
            "source_identities": identities,
            "features_content_id": _numeric_content_id(
                feature_row,
                role="private_checkpoint_features",
            ),
            "carrier_content_id": _numeric_content_id(
                carrier_row,
                role="private_checkpoint_carrier",
            ),
        },
    )


def load_private_row_checkpoint(
    *,
    path: Path,
    expected_ordinal: int,
    expected_row_id: str,
    expected_source_identities: Sequence[Mapping[str, object]],
    expected_operator_identity_sha256: str,
) -> dict[str, np.ndarray]:
    """Load one private checkpoint only under the exact current identities."""

    path = Path(path)
    metadata_path = _checkpoint_metadata_path(path)
    if (
        path.is_symlink()
        or metadata_path.is_symlink()
        or not path.is_file()
        or not metadata_path.is_file()
    ):
        raise CarrierExportError("private checkpoint files are missing or unsafe")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CarrierExportError("private checkpoint metadata is malformed") from exc
    if (
        not isinstance(metadata, dict)
        or metadata.get("format")
        != "PLANCK_PR3_PAIRED300_PRIVATE_ROW_CHECKPOINT_V1"
        or metadata.get("state") != "SUCCEEDED"
        or metadata.get("ordinal") != expected_ordinal
        or metadata.get("row_id") != expected_row_id
    ):
        raise CarrierExportError("private checkpoint row identity drifted")
    expected_operator = _require_sha256(
        expected_operator_identity_sha256,
        label="expected checkpoint operator identity",
    )
    if metadata.get("operator_identity_sha256") != expected_operator:
        raise CarrierExportError("private checkpoint operator identity drifted")
    identities = _json_clone(
        list(expected_source_identities),
        label="expected source identities",
    )
    if metadata.get("source_identities") != identities:
        raise CarrierExportError("private checkpoint source identity drifted")
    try:
        with np.load(path, allow_pickle=False) as bundle:
            if set(bundle.files) != {"features", "carrier"}:
                raise CarrierExportError("private checkpoint NPZ keys drifted")
            features = np.asarray(bundle["features"])
            carrier = np.asarray(bundle["carrier"])
    except (OSError, ValueError, KeyError) as exc:
        raise CarrierExportError("private checkpoint NPZ is malformed") from exc
    if (
        features.dtype != np.dtype("float64")
        or features.shape != (12,)
        or carrier.dtype != np.dtype("float64")
        or carrier.shape != (EXPECTED_DIMENSION,)
        or not np.all(np.isfinite(features))
        or not np.all(np.isfinite(carrier))
    ):
        raise CarrierExportError("private checkpoint numerical payload drifted")
    if (
        metadata.get("features_content_id")
        != _numeric_content_id(features, role="private_checkpoint_features")
        or metadata.get("carrier_content_id")
        != _numeric_content_id(carrier, role="private_checkpoint_carrier")
    ):
        raise CarrierExportError("private checkpoint content identity drifted")
    return {"features": features.copy(), "carrier": carrier.copy()}


def validate_portable_completion(output_dir: Path) -> dict[str, object]:
    """Accept only the seven exact portable outputs and terminal boundaries."""

    output_dir = Path(output_dir)
    if output_dir.is_symlink() or not output_dir.is_dir():
        raise CarrierExportError("portable output directory is missing or unsafe")
    present = {path.name for path in output_dir.iterdir()}
    if present != _PORTABLE_OUTPUTS or any(
        path.is_symlink() or not path.is_file() for path in output_dir.iterdir()
    ):
        raise CarrierExportError("portable package must contain exactly seven files")
    try:
        terminal = json.loads((output_dir / "terminal.json").read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CarrierExportError("portable terminal is malformed") from exc
    if not isinstance(terminal, dict) or terminal.get("fresh_review") != "PASS":
        raise CarrierExportError("portable terminal fresh review is not accepted")
    if not isinstance(terminal, dict) or any(
        terminal.get(key) != value for key, value in _TERMINAL_REQUIRED.items()
    ):
        raise CarrierExportError("portable terminal boundary is not PMG-WU-005 PASS")
    expected_names = _PORTABLE_OUTPUTS - {"terminal.json"}
    artifact_hashes = terminal.get("objective_artifact_sha256")
    if not isinstance(artifact_hashes, dict) or set(artifact_hashes) != expected_names:
        raise CarrierExportError("portable objective artifact identity set drifted")
    for name in sorted(expected_names):
        if artifact_hashes.get(name) != _file_sha256(output_dir / name):
            raise CarrierExportError(f"portable artifact identity drifted: {name}")
    return terminal


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _array_digest(value: object) -> str:
    return _numeric_content_id(value, role="array_identity")


def _canonical_hash(value: object, *, role: str) -> str:
    clone = _json_clone(value, label=role)
    encoded = json.dumps(
        clone,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    digest = hashlib.sha256()
    digest.update(role.encode("ascii") + b"\0")
    digest.update(encoded)
    return "sha256:" + digest.hexdigest()


def _load_json(path: Path, *, label: str) -> dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CarrierExportError(f"{label} is not readable JSON") from exc
    if not isinstance(value, dict):
        raise CarrierExportError(f"{label} must be a mapping")
    return value


def _require_post_stat_match(
    path: Path,
    before: Mapping[str, object],
) -> None:
    from obsstat.planck_paired300_carrier_execution import (
        capture_regular_file_identity,
    )

    after = capture_regular_file_identity(Path(path), hash_content=False)
    for key in ("path", "device", "inode", "size", "mtime_ns"):
        if after.get(key) != before.get(key):
            raise CarrierExportError(f"raw input mutated during execution: {path}")


def _identity_for_first_scientific_read(path: Path) -> dict[str, object]:
    from obsstat.planck_paired300_carrier_execution import (
        capture_regular_file_identity,
    )

    return capture_regular_file_identity(Path(path), hash_content=True)


def _checkpoint_or_process(
    *,
    checkpoint_path: Path,
    ordinal: int,
    row_id: str,
    source_identities: Sequence[Mapping[str, object]],
    operator_identity_sha256: str,
    make_map: Callable[[], np.ndarray],
    process_map: Callable[..., tuple[object, object, object]],
    context: Mapping[str, object],
) -> tuple[np.ndarray, np.ndarray, bool]:
    """Reuse an exact checkpoint or call the frozen estimator exactly once."""

    from obsstat.planck_paired300_carrier_execution import carrier_vector_from_alm

    metadata_path = _checkpoint_metadata_path(checkpoint_path)
    if checkpoint_path.exists() or metadata_path.exists():
        loaded = load_private_row_checkpoint(
            path=checkpoint_path,
            expected_ordinal=ordinal,
            expected_row_id=row_id,
            expected_source_identities=source_identities,
            expected_operator_identity_sha256=operator_identity_sha256,
        )
        return loaded["features"], loaded["carrier"], True
    pixel_map = np.asarray(make_map(), dtype=np.float64)
    payload = process_map(pixel_map, component="SMICA", context=context)
    if not isinstance(payload, tuple) or len(payload) != 3:
        raise CarrierExportError("frozen worker did not return features,timings,alm")
    features_raw, timings, retained_alm = payload
    features = np.asarray(features_raw, dtype=np.float64)
    if not isinstance(timings, Mapping) or features.shape != (12,):
        raise CarrierExportError("frozen worker feature/timing contract drifted")
    carrier = carrier_vector_from_alm(retained_alm)
    write_private_row_checkpoint(
        path=checkpoint_path,
        ordinal=ordinal,
        row_id=row_id,
        features=features,
        carrier=carrier,
        source_identities=source_identities,
        operator_identity_sha256=operator_identity_sha256,
    )
    return features, carrier, False


def _load_frozen_feature_rows(
    package_path: Path,
) -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    try:
        with np.load(package_path, allow_pickle=False) as bundle:
            if not {"observed_features", "null_features", "row_ids"}.issubset(
                bundle.files
            ):
                raise CarrierExportError("frozen scalar package keys drifted")
            observed = np.asarray(bundle["observed_features"], dtype=np.float64)
            nulls = np.asarray(bundle["null_features"], dtype=np.float64)
            row_ids = tuple(str(value) for value in bundle["row_ids"].tolist())
    except (OSError, ValueError, KeyError) as exc:
        raise CarrierExportError("frozen scalar package is unreadable") from exc
    if observed.shape != (12,) or nulls.shape != (300, 12) or len(row_ids) != 300:
        raise CarrierExportError("frozen scalar package shape drifted")
    return observed, nulls, row_ids


def _scalar_feature_content_id(
    observed: np.ndarray,
    nulls: np.ndarray,
    row_ids: Sequence[str],
) -> str:
    return _canonical_hash(
        {
            "observed_content_id": _numeric_content_id(
                observed,
                role="scalar_observed_features",
            ),
            "null_content_id": _numeric_content_id(
                nulls,
                role="scalar_null_features",
            ),
            "row_ids": list(row_ids),
        },
        role="planck_pr315_scalar_feature_content",
    )


def _intake_stat_index(
    intake_manifest: Mapping[str, object],
) -> dict[str, dict[str, int]]:
    if (
        intake_manifest.get("format")
        != "PLANCK_MES_IRREP_PRIVATE_INTAKE_MANIFEST_V1"
        or not isinstance(intake_manifest.get("entries"), list)
    ):
        raise CarrierExportError("accepted intake manifest is malformed")
    result: dict[str, dict[str, int]] = {}
    for entry in intake_manifest["entries"]:
        if not isinstance(entry, Mapping):
            raise CarrierExportError("accepted intake entry is malformed")
        path = entry.get("resolved_path")
        stat = entry.get("stat_identity")
        if not isinstance(path, str) or not isinstance(stat, Mapping):
            raise CarrierExportError("accepted intake stat identity is missing")
        normalized: dict[str, int] = {}
        for key in ("device", "inode", "size", "mtime_ns"):
            value = stat.get(key)
            if type(value) is not int:
                raise CarrierExportError("accepted intake stat identity is malformed")
            normalized[key] = value
        if path in result:
            raise CarrierExportError("accepted intake path is duplicated")
        result[path] = normalized
    return result


def _combined_intake_stat_index(
    *,
    intake_manifest: Mapping[str, object],
    selected_manifest: Mapping[str, object] | None,
) -> dict[str, dict[str, int]]:
    result = _intake_stat_index(intake_manifest)
    if selected_manifest is None:
        return result
    if (
        selected_manifest.get("format")
        != "PLANCK_MES_IRREP_SELECTED_INPUT_MANIFEST_V1"
        or not isinstance(selected_manifest.get("inputs"), list)
    ):
        raise CarrierExportError("selected input manifest is malformed")
    supplement = _intake_stat_index(
        {
            "format": "PLANCK_MES_IRREP_PRIVATE_INTAKE_MANIFEST_V1",
            "entries": selected_manifest["inputs"],
        }
    )
    for path, stat in supplement.items():
        prior = result.get(path)
        if prior is not None and prior != stat:
            raise CarrierExportError("accepted intake authorities disagree")
        result[path] = stat
    return result


def _require_intake_stat_identity(
    *,
    path: Path,
    execution_identity: Mapping[str, object],
    intake_index: Mapping[str, Mapping[str, int]],
) -> None:
    expected = intake_index.get(str(path))
    if expected is None:
        raise CarrierExportError(f"processed input is absent from accepted intake: {path}")
    current = {
        key: execution_identity.get(key)
        for key in ("device", "inode", "size", "mtime_ns")
    }
    if current != dict(expected):
        raise CarrierExportError(f"processed input intake stat identity drifted: {path}")


def validate_execution_input_provenance(
    *,
    intake_manifest: Mapping[str, object],
    execution_manifest: Mapping[str, object],
    selected_manifest: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Rebind the completed run to WU-004 without reopening any map."""

    if (
        execution_manifest.get("format")
        != "PLANCK_PR3_PAIRED300_PRIVATE_EXECUTION_MANIFEST_V1"
        or not isinstance(execution_manifest.get("selected_input_identities"), list)
    ):
        raise CarrierExportError("private execution manifest is malformed")
    intake_index = _combined_intake_stat_index(
        intake_manifest=intake_manifest,
        selected_manifest=selected_manifest,
    )
    selected = execution_manifest["selected_input_identities"]
    seen: set[str] = set()
    for entry in selected:
        if not isinstance(entry, Mapping) or not isinstance(entry.get("path"), str):
            raise CarrierExportError("private execution input identity is malformed")
        path = str(entry["path"])
        if path in seen:
            raise CarrierExportError("private execution input path is duplicated")
        seen.add(path)
        _require_sha256(entry.get("sha256"), label="execution input content identity")
        _require_intake_stat_identity(
            path=Path(path),
            execution_identity=entry,
            intake_index=intake_index,
        )
    return {
        "required_identity": "INTAKE_STAT_PLUS_EXECUTION_CONTENT",
        "result_validity": "PASS_UNCHANGED",
        "provenance_validity": "MATCH",
        "matched_file_count": len(selected),
    }


def upgrade_private_checkpoint_content_identities(private_dir: Path) -> int:
    """Bind existing zero-reuse checkpoints by decoded array content."""

    private_dir = Path(private_dir)
    paths = sorted(private_dir.glob("*.npz"))
    if len(paths) != 301:
        raise CarrierExportError("private checkpoint inventory is not exact 301 rows")
    upgraded = 0
    for path in paths:
        metadata_path = _checkpoint_metadata_path(path)
        metadata = _load_json(metadata_path, label="private checkpoint metadata")
        try:
            with np.load(path, allow_pickle=False) as bundle:
                if set(bundle.files) != {"features", "carrier"}:
                    raise CarrierExportError("private checkpoint NPZ keys drifted")
                features = np.asarray(bundle["features"])
                carrier = np.asarray(bundle["carrier"])
        except (OSError, ValueError, KeyError) as exc:
            raise CarrierExportError("private checkpoint NPZ is malformed") from exc
        if (
            features.dtype != np.dtype("float64")
            or features.shape != (12,)
            or carrier.dtype != np.dtype("float64")
            or carrier.shape != (EXPECTED_DIMENSION,)
            or not np.all(np.isfinite(features))
            or not np.all(np.isfinite(carrier))
        ):
            raise CarrierExportError("private checkpoint numerical payload drifted")
        feature_id = _numeric_content_id(
            features,
            role="private_checkpoint_features",
        )
        carrier_id = _numeric_content_id(
            carrier,
            role="private_checkpoint_carrier",
        )
        prior_feature = metadata.get("features_content_id")
        prior_carrier = metadata.get("carrier_content_id")
        if prior_feature is not None and prior_feature != feature_id:
            raise CarrierExportError("private checkpoint feature content identity drifted")
        if prior_carrier is not None and prior_carrier != carrier_id:
            raise CarrierExportError("private checkpoint carrier content identity drifted")
        if prior_feature is None or prior_carrier is None:
            metadata["features_content_id"] = feature_id
            metadata["carrier_content_id"] = carrier_id
            _atomic_json(metadata_path, metadata)
            upgraded += 1
    return upgraded


def _pending_terminal_payload(
    *,
    operator_identity_sha256: str,
    artifact_hashes: Mapping[str, str],
) -> dict[str, object]:
    return {
        "work_unit": "PMG-WU-005",
        "state": "PENDING_REVIEW",
        "real_host_execution": True,
        "replay_status": "MATCH",
        "scalar_closure": "MATCH",
        "raw_data_mutation": False,
        "claim_promotion": False,
        "unresolved_blockers": ["FRESH_REVIEW_PENDING"],
        "next_executable_action": "FRESH_REVIEW",
        "fresh_review": "PENDING",
        "row_count": 301,
        "operator_identity_sha256": operator_identity_sha256,
        "objective_artifact_sha256": dict(artifact_hashes),
        "P0_remaining": None,
        "P1_remaining": None,
    }


def _project_carrier_rows(
    observed_carrier: np.ndarray,
    null_carrier: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    from scripts.observed_runs import run_planck_pr3 as worker

    observed = worker._component_features_from_real_carrier(observed_carrier)
    nulls = np.asarray(
        [worker._component_features_from_real_carrier(row) for row in null_carrier],
        dtype=np.float64,
    )
    return observed, nulls


def _rank_regression(
    *,
    observed_features: np.ndarray,
    null_features: np.ndarray,
    row_ids: tuple[str, ...],
    frozen_result_path: Path,
) -> dict[str, object]:
    from scripts.observed_runs import run_planck_pr3 as worker

    current = worker.analyze_smica_feature_rows(
        observed_features=observed_features,
        null_features=null_features,
        row_ids=row_ids,
    )
    frozen = _load_json(frozen_result_path, label="frozen PR315 result")
    for key in (
        "finite_feature_family_p",
        "local_feature_p",
        "null_ordered_row_ids_sha256",
    ):
        if current.get(key) != frozen.get(key):
            raise CarrierExportError(f"frozen scalar rank regression drifted: {key}")
    return {
        "state": "MATCH",
        "finite_feature_family_p": current["finite_feature_family_p"],
        "local_feature_p": current["local_feature_p"],
        "null_ordered_row_ids_sha256": current[
            "null_ordered_row_ids_sha256"
        ],
    }


def _validate_leakage_receipt(
    receipt: Mapping[str, object],
    *,
    operator_identity_sha256: str,
) -> None:
    if (
        receipt.get("format")
        != "PLANCK_PR3_PAIRED300_LEAKAGE_DIAGNOSTIC_V1"
        or receipt.get("probe_definition") != "COMPLETE_REAL_BASIS_ELL6_ELL7_V1"
        or receipt.get("probe_count") != 28
        or receipt.get("probes")
        != [list(probe) for probe in fixed_leakage_probe_layout()]
        or receipt.get("operator_identity_sha256") != operator_identity_sha256
        or receipt.get("correction_applied") is not False
        or receipt.get("claim_promotion") is not False
    ):
        raise CarrierExportError("leakage receipt schema or fixed registry drifted")
    values = np.asarray(receipt.get("retained_real_alm"), dtype=np.float64)
    if values.shape != (28, EXPECTED_DIMENSION) or not np.all(np.isfinite(values)):
        raise CarrierExportError("leakage receipt numerical payload drifted")


def _leakage_operator_identity_from_metadata(
    metadata: Mapping[str, object],
) -> str:
    """Recover the existing PR315 hash role from strict carrier metadata."""

    from scripts.observed_runs import run_planck_pr3 as worker

    operator = metadata.get("operator_identity")
    if not isinstance(operator, Mapping):
        raise CarrierExportError("carrier metadata operator identity is missing")
    return worker.require_observation_null_operator_identity(operator, operator)


def _compute_map_free_replay(*, repo_root: Path) -> dict[str, object]:
    """Compute scientific replay semantics without trusting the terminal."""

    from obsstat.planck_irrep_carrier import (
        PlanckIrrepCarrierError,
        replay_planck_irrep_carrier,
        scalar_feature_closure_report,
    )

    output_dir = repo_root / "docs/generated/planck_pr3_paired300_irrep_carrier"
    replay = replay_planck_irrep_carrier(
        package_path=output_dir / "carrier.npz",
        metadata_path=output_dir / "metadata.json",
    )
    with np.load(output_dir / "carrier.npz", allow_pickle=False) as carrier_bundle:
        observed_carrier = np.asarray(
            carrier_bundle["observed_real_alm"], dtype=np.float64
        )
        null_carrier = np.asarray(carrier_bundle["null_real_alm"], dtype=np.float64)
        row_ids = tuple(str(value) for value in carrier_bundle["row_ids"].tolist())
    frozen_package = repo_root / "docs/generated/pr315_planck_smica_feature_replay.npz"
    frozen_observed, frozen_nulls, frozen_row_ids = _load_frozen_feature_rows(
        frozen_package
    )
    metadata = _load_json(output_dir / "metadata.json", label="carrier metadata")
    scalar_content_id = _scalar_feature_content_id(
        frozen_observed,
        frozen_nulls,
        frozen_row_ids,
    )
    if metadata.get("scalar_feature_content_id") != scalar_content_id:
        raise CarrierExportError("scalar feature scientific content identity drifted")
    scalar_byte_identical = (
        metadata.get("scalar_feature_package_sha256")
        == _file_sha256(frozen_package)
    )
    if row_ids[1:] != frozen_row_ids:
        raise CarrierExportError("map-free replay row order drifted")
    projected_observed, projected_nulls = _project_carrier_rows(
        observed_carrier, null_carrier
    )
    try:
        closure = scalar_feature_closure_report(
            observed_expected=frozen_observed,
            observed_projected=projected_observed,
            null_expected=frozen_nulls,
            null_projected=projected_nulls,
        )
    except PlanckIrrepCarrierError as exc:
        raise CarrierExportError(
            "scalar feature scientific content differs from the carrier"
        ) from exc
    rank = _rank_regression(
        observed_features=projected_observed,
        null_features=projected_nulls,
        row_ids=frozen_row_ids,
        frozen_result_path=repo_root / "docs/generated/pr315_planck_smica_result.json",
    )
    leakage = _load_json(
        output_dir / "leakage_receipt.json",
        label="leakage receipt",
    )
    _validate_leakage_receipt(
        leakage,
        operator_identity_sha256=_leakage_operator_identity_from_metadata(metadata),
    )
    if (
        replay.get("state") != "REPLAY_MATCH"
        or closure.get("state") != "MATCH"
        or rank.get("state") != "MATCH"
    ):
        raise CarrierExportError("map-free committed replay did not match")
    return {
        "state": "MATCH",
        "carrier_replay": replay,
        "scalar_closure": closure,
        "rank_regression": rank,
        "leakage_receipt_sha256": _file_sha256(
            output_dir / "leakage_receipt.json"
        ),
        "raw_maps_reopened": False,
        "scalar_feature_required_identity": "NUMERICAL_CONTENT_IDENTITY",
        "scalar_feature_content_id": scalar_content_id,
        "scalar_feature_identity_disposition": (
            "BYTE_IDENTICAL"
            if scalar_byte_identical
            else "NUMERICALLY_EQUIVALENT"
        ),
    }


def _replay_receipt_from_result(result: Mapping[str, object]) -> dict[str, object]:
    return {
        "format": "PLANCK_PR3_PAIRED300_IRREP_REPLAY_V1",
        "state": "MATCH",
        "carrier_replay": result["carrier_replay"],
        "scalar_closure": "MATCH",
        "rank_regression": result["rank_regression"],
        "leakage_receipt_sha256": result["leakage_receipt_sha256"],
        "raw_maps_reopened": False,
        "scalar_feature_required_identity": "NUMERICAL_CONTENT_IDENTITY",
        "scalar_feature_content_id": result["scalar_feature_content_id"],
    }


def replay_committed(*, repo_root: Path) -> dict[str, object]:
    """Replay the seven-file package without opening any map."""

    output_dir = repo_root / "docs/generated/planck_pr3_paired300_irrep_carrier"
    terminal = validate_portable_completion(output_dir)
    result = _compute_map_free_replay(repo_root=repo_root)
    committed = _load_json(output_dir / "replay.json", label="committed replay")
    if committed != _replay_receipt_from_result(result):
        raise CarrierExportError("committed replay receipt semantic content drifted")
    if terminal.get("replay_status") != "MATCH" or terminal.get(
        "scalar_closure"
    ) != "MATCH":
        raise CarrierExportError("map-free committed replay terminal drifted")
    return result


def _execute_leakage_probes(
    *,
    context: Mapping[str, object],
    operator_identity_sha256: str,
) -> dict[str, object]:
    import healpy as hp

    from obsstat.planck_pr3_operator import fit_joint_cutsky_alm, real_vector_to_alm

    probes = fixed_leakage_probe_layout()

    def fit_probe(ell: int, m: int, component: str) -> np.ndarray:
        index = probes.index((ell, m, component))
        vector = np.zeros(len(probes), dtype=np.float64)
        vector[index] = 1.0
        alm = real_vector_to_alm(vector, lmin=6, lmax=7)
        pixel_map = hp.alm2map(
            alm,
            nside=int(context["nside"]),
            lmax=7,
            pol=False,
        )
        fit = fit_joint_cutsky_alm(
            np.asarray(pixel_map, dtype=np.float64),
            mask=np.asarray(context["common_mask"], dtype=np.float64),
            operator=context["joint_cutsky_operator"],
            source_beam=np.asarray(context["source_beams"]["SMICA"]),
            source_pixel_window=np.asarray(context["source_pixels"]["SMICA"]),
            target_beam=np.asarray(context["target_beam"]),
            target_pixel_window=np.asarray(context["target_pixel"]),
        )
        return np.asarray(fit.retained_coefficients, dtype=np.float64)

    return evaluate_fixed_leakage_probes(
        operator_identity_sha256=operator_identity_sha256,
        fit_probe=fit_probe,
    )


def _execution_git_state(repo_root: Path) -> dict[str, object]:
    def run(*args: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            text=True,
            capture_output=True,
            check=True,
        )
        return completed.stdout.strip()

    try:
        head = run("rev-parse", "HEAD")
        dirty = bool(run("status", "--porcelain=v1"))
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CarrierExportError("git execution provenance is unavailable") from exc
    return {
        "git_head": head,
        "worktree_state": "DIRTY_IMPLEMENTATION_CANDIDATE" if dirty else "CLEAN",
        "exact_execution_source_bytes_captured": False,
        "provenance_level": "R2_SCIENTIFIC_NUMERICAL_REPLAY",
    }


def _augment_carrier_metadata(
    *,
    metadata_path: Path,
    repo_root: Path,
    scalar_feature_content_id: str,
) -> dict[str, object]:
    metadata = _load_json(metadata_path, label="carrier metadata")
    metadata.update(
        {
            "owner": "obsstat",
            "scope": (
                "Planck PR3 SMICA observer-space l=2..5 harmonic carrier "
                "with exact ordered paired-300 FFP10 conditional null rows"
            ),
            "transfer_source": "PLANCK_PR3_SMICA_FFP10_FROZEN_JOINT_CUTSKY",
            "sky_support_status": "GALACTIC_COMMON_TEMPERATURE_MASK",
            "null_mock_status": "EXACT_ORDERED_FFP10_CMB_PLUS_NOISE_300_CONDITIONAL",
            "caveats": [
                "observer-space carrier only",
                "no physical shear, vorticity, local/global, or family identification",
                "finite-pool and Planck/FFP10 null fidelity remain conditional",
                "execution source was an uncommitted implementation candidate; "
                "post-execution repairs affect validation and transition boundaries only",
            ],
            "generating_procedure": {
                "command": (
                    "python scripts/observed_runs/"
                    "export_planck_paired300_irrep_carrier.py "
                    "--execute-real-host --workdir "
                    "/mnt/sn850x2t/htt_base_e2e/workdir"
                ),
                "carrier_capture": (
                    "alm returned by the same frozen _process_map call as each scalar row"
                ),
                "second_estimator_run": False,
            },
            "execution_git_state": _execution_git_state(repo_root),
            "scalar_feature_content_id": scalar_feature_content_id,
            "scalar_feature_required_identity": "NUMERICAL_CONTENT_IDENTITY",
            "identity_validity": {
                "result_validity": "PASS_UNCHANGED",
                "provenance_validity": "MATCH_AFTER_REBIND",
                "packaging_validity": "BYTE_IDENTITY_NOT_A_SCIENCE_GATE",
            },
        }
    )
    _atomic_json(metadata_path, metadata)
    return metadata


def execute_real_host(
    *,
    repo_root: Path,
    workdir: Path,
) -> dict[str, object]:
    """Execute observation and exact 300 raw pairs with private checkpoints."""

    import healpy as hp

    from obsstat.planck_irrep_carrier import (
        OBSERVATION_ROW_ID,
        replay_planck_irrep_carrier,
        scalar_feature_closure_report,
        write_planck_irrep_carrier,
    )
    from obsstat.planck_paired300_carrier_execution import (
        expected_paired300_row_ids,
    )
    from scripts.observed_runs import prepare_planck_pr3_admission as preparation
    from scripts.observed_runs import run_planck_pr3 as worker

    repo_root = Path(repo_root).resolve()
    workdir = Path(workdir)
    if (
        not workdir.is_absolute()
        or workdir.is_symlink()
        or not workdir.is_dir()
        or workdir.resolve() != workdir
    ):
        raise CarrierExportError("workdir must be one absolute non-symlink directory")
    raw_root = workdir / "raw"
    if raw_root.is_symlink() or not raw_root.is_dir():
        raise CarrierExportError("raw root is missing or is a symlink")
    output_dir = repo_root / "docs/generated/planck_pr3_paired300_irrep_carrier"
    if output_dir.exists() or output_dir.is_symlink():
        raise CarrierExportError("portable output already exists; use replay mode")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    if output_dir.parent.is_symlink():
        raise CarrierExportError("portable output parent cannot be a symlink")
    staging_dir = output_dir.with_name(f".{output_dir.name}.{os.getpid()}.staging")
    if staging_dir.exists() or staging_dir.is_symlink():
        raise CarrierExportError("portable staging path already exists")

    private_dir = workdir / "analysis/planck_mes_irrep/paired300_carrier"
    if private_dir.is_symlink():
        raise CarrierExportError("private checkpoint directory cannot be a symlink")
    private_dir.mkdir(parents=True, exist_ok=True)
    private_manifest_path = workdir / "analysis/planck_mes_irrep/intake_manifest.json"
    selected_manifest_path = (
        repo_root
        / "docs/generated/planck_mes_irrep_inventory/selected_input_manifest.json"
    )
    selected_manifest = _load_json(
        selected_manifest_path,
        label="selected input manifest",
    )
    private_intake_manifest = _load_json(
        private_manifest_path,
        label="accepted private intake manifest",
    )
    intake_stat_index = _combined_intake_stat_index(
        intake_manifest=private_intake_manifest,
        selected_manifest=selected_manifest,
    )
    source_manifest_sha256 = _file_sha256(private_manifest_path)
    if selected_manifest.get("private_manifest_sha256") != source_manifest_sha256:
        raise CarrierExportError("accepted private intake manifest identity drifted")

    selected_inputs = selected_manifest.get("inputs")
    if not isinstance(selected_inputs, list):
        raise CarrierExportError("selected input manifest inputs are malformed")
    by_product = {
        value.get("product_identity"): Path(str(value.get("resolved_path")))
        for value in selected_inputs
        if isinstance(value, Mapping)
    }
    observed_path = by_product.get("COM_CMB_IQU-smica_2048_R3.00_full.fits")
    mask_path = by_product.get("COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits")
    if observed_path is None or mask_path is None:
        raise CarrierExportError("selected observed SMICA or mask path is missing")
    cmb_root = raw_root / "planck_ffp10/smica/cmb_mc"
    noise_root = raw_root / "planck_ffp10/smica/noise_mc"
    pairs = preparation.inspect_smica_cmb_noise_inventory(
        cmb_root=cmb_root,
        noise_root=noise_root,
    )
    if tuple(pairs) != tuple(range(300)):
        raise CarrierExportError("raw paired-300 inventory order drifted")
    expected_row_ids = expected_paired300_row_ids()
    frozen_package = repo_root / "docs/generated/pr315_planck_smica_feature_replay.npz"
    frozen_observed, frozen_nulls, frozen_row_ids = _load_frozen_feature_rows(
        frozen_package
    )
    scalar_feature_content_id = _scalar_feature_content_id(
        frozen_observed,
        frozen_nulls,
        frozen_row_ids,
    )
    if expected_row_ids != frozen_row_ids:
        raise CarrierExportError("frozen scalar and raw row registries differ")

    observed_identity = _identity_for_first_scientific_read(observed_path)
    mask_identity = _identity_for_first_scientific_read(mask_path)
    _require_intake_stat_identity(
        path=observed_path,
        execution_identity=observed_identity,
        intake_index=intake_stat_index,
    )
    _require_intake_stat_identity(
        path=mask_path,
        execution_identity=mask_identity,
        intake_index=intake_stat_index,
    )
    observed_payload = preparation.read_temperature_fits(
        observed_path,
        allowed_column_names=("I_STOKES",),
        declared_coordinate_frame="GALACTIC",
    )
    observed_map = preparation.reduce_temperature_map(
        observed_payload.values,
        source_unit=observed_payload.unit,
        source_ordering=observed_payload.ordering,
        output_nside=16,
    )
    beam = preparation.read_temperature_beam(observed_path)
    mask = preparation.reduce_mask(
        preparation.read_mask_fits(mask_path),
        output_nside=16,
    )
    pixel = np.asarray(hp.pixwin(16, lmax=worker.LMAX), dtype=np.float64)
    context = worker.build_smica_joint_cutsky_context(
        smica_map=observed_map,
        mask=mask,
        beam=beam,
        window={
            "source_pixel_window": pixel,
            "target_beam": beam,
            "target_pixel_window": pixel,
        },
        declared_nside=16,
    )
    operator_identity = worker.joint_cutsky_operator_identity(context)
    operator_identity_sha256 = worker.require_observation_null_operator_identity(
        operator_identity,
        worker.joint_cutsky_operator_identity(context),
    )
    frozen_metadata = _load_json(
        repo_root / "docs/generated/pr315_planck_smica_feature_replay.json",
        label="frozen scalar metadata",
    )
    if (
        frozen_metadata.get("operator_identity") != operator_identity
        or frozen_metadata.get("operator_identity_sha256")
        != operator_identity_sha256
    ):
        raise CarrierExportError("real-host operator differs from frozen PR315")

    observed_features, observed_carrier, observed_reused = _checkpoint_or_process(
        checkpoint_path=private_dir / "observed.npz",
        ordinal=0,
        row_id=OBSERVATION_ROW_ID,
        source_identities=(observed_identity,),
        operator_identity_sha256=operator_identity_sha256,
        make_map=lambda: observed_map,
        process_map=worker._process_map,
        context=context,
    )
    _require_post_stat_match(observed_path, observed_identity)
    _require_post_stat_match(mask_path, mask_identity)
    print(
        json.dumps(
            {"row": OBSERVATION_ROW_ID, "checkpoint_reused": observed_reused},
            sort_keys=True,
        ),
        flush=True,
    )

    null_features: list[np.ndarray] = []
    null_carriers: list[np.ndarray] = []
    private_identities: list[dict[str, object]] = [
        {"role": "observed_smica", **observed_identity},
        {"role": "temperature_mask", **mask_identity},
    ]
    reused_count = int(observed_reused)
    for index, row_id in enumerate(expected_row_ids):
        cmb_path, noise_path = pairs[index]
        cmb_identity = _identity_for_first_scientific_read(cmb_path)
        noise_identity = _identity_for_first_scientific_read(noise_path)
        _require_intake_stat_identity(
            path=cmb_path,
            execution_identity=cmb_identity,
            intake_index=intake_stat_index,
        )
        _require_intake_stat_identity(
            path=noise_path,
            execution_identity=noise_identity,
            intake_index=intake_stat_index,
        )
        features, carrier, reused = _checkpoint_or_process(
            checkpoint_path=private_dir / f"null-{index:05d}.npz",
            ordinal=index + 1,
            row_id=row_id,
            source_identities=(cmb_identity, noise_identity),
            operator_identity_sha256=operator_identity_sha256,
            make_map=lambda cmb_path=cmb_path, noise_path=noise_path: (
                preparation.reduce_smica_cmb_plus_noise(
                    cmb_path=cmb_path,
                    noise_path=noise_path,
                    output_nside=16,
                )
            ),
            process_map=worker._process_map,
            context=context,
        )
        _require_post_stat_match(cmb_path, cmb_identity)
        _require_post_stat_match(noise_path, noise_identity)
        null_features.append(features)
        null_carriers.append(carrier)
        reused_count += int(reused)
        private_identities.extend(
            (
                {"role": "cmb", "row_id": row_id, **cmb_identity},
                {"role": "noise", "row_id": row_id, **noise_identity},
            )
        )
        print(
            json.dumps(
                {
                    "completed": index + 1,
                    "expected": 300,
                    "row": row_id,
                    "checkpoint_reused": reused,
                },
                sort_keys=True,
            ),
            flush=True,
        )

    null_feature_matrix = np.asarray(null_features, dtype=np.float64)
    null_carrier_matrix = np.asarray(null_carriers, dtype=np.float64)
    if null_feature_matrix.shape != (300, 12) or null_carrier_matrix.shape != (
        300,
        EXPECTED_DIMENSION,
    ):
        raise CarrierExportError("real-host paired-300 matrix is incomplete")

    raw_to_frozen = scalar_feature_closure_report(
        observed_expected=frozen_observed,
        observed_projected=observed_features,
        null_expected=frozen_nulls,
        null_projected=null_feature_matrix,
    )
    projected_observed, projected_nulls = _project_carrier_rows(
        observed_carrier,
        null_carrier_matrix,
    )
    carrier_to_raw = scalar_feature_closure_report(
        observed_expected=observed_features,
        observed_projected=projected_observed,
        null_expected=null_feature_matrix,
        null_projected=projected_nulls,
    )
    rank = _rank_regression(
        observed_features=observed_features,
        null_features=null_feature_matrix,
        row_ids=expected_row_ids,
        frozen_result_path=repo_root / "docs/generated/pr315_planck_smica_result.json",
    )
    leakage = _execute_leakage_probes(
        context=context,
        operator_identity_sha256=operator_identity_sha256,
    )
    _validate_leakage_receipt(
        leakage,
        operator_identity_sha256=operator_identity_sha256,
    )
    _require_post_stat_match(observed_path, observed_identity)
    _require_post_stat_match(mask_path, mask_identity)
    for entry in private_identities[2:]:
        _require_post_stat_match(Path(str(entry["path"])), entry)

    private_execution_manifest = {
        "format": "PLANCK_PR3_PAIRED300_PRIVATE_EXECUTION_MANIFEST_V1",
        "state": "SUCCEEDED",
        "row_count": 301,
        "row_ids": [OBSERVATION_ROW_ID, *expected_row_ids],
        "operator_identity_sha256": operator_identity_sha256,
        "source_manifest_sha256": source_manifest_sha256,
        "selected_input_identities": private_identities,
        "raw_data_mutation": False,
        "checkpoint_reused_count": reused_count,
    }
    _atomic_json(private_dir / "execution_manifest.json", private_execution_manifest)
    provenance_rebind = validate_execution_input_provenance(
        intake_manifest=private_intake_manifest,
        execution_manifest=private_execution_manifest,
        selected_manifest=selected_manifest,
    )
    private_execution_manifest_sha256 = _file_sha256(
        private_dir / "execution_manifest.json"
    )
    identity_set_sha256 = _canonical_hash(
        private_identities,
        role="paired300_selected_input_identities",
    )

    staging_dir.mkdir()
    transfer_identity = {
        "source_beam_sha256": _array_digest(context["source_beams"]["SMICA"]),
        "source_pixel_window_sha256": _array_digest(
            context["source_pixels"]["SMICA"]
        ),
        "target_beam_sha256": _array_digest(context["target_beam"]),
        "target_pixel_window_sha256": _array_digest(context["target_pixel"]),
    }
    write_planck_irrep_carrier(
        package_path=staging_dir / "carrier.npz",
        metadata_path=staging_dir / "metadata.json",
        observed_real_alm=observed_carrier,
        null_real_alm=null_carrier_matrix,
        row_ids=(OBSERVATION_ROW_ID, *expected_row_ids),
        null_ordered_row_ids_sha256=worker.SMICA_EXISTING_INVENTORY_ID,
        operator_identity=operator_identity,
        transfer_identity=transfer_identity,
        source_manifest_sha256=source_manifest_sha256,
        scalar_feature_package_sha256=_file_sha256(frozen_package),
    )
    _augment_carrier_metadata(
        metadata_path=staging_dir / "metadata.json",
        repo_root=repo_root,
        scalar_feature_content_id=scalar_feature_content_id,
    )
    scalar_closure = {
        "format": "PLANCK_PR3_PAIRED300_SCALAR_CLOSURE_V1",
        "state": "MATCH",
        "raw_to_frozen": raw_to_frozen,
        "carrier_to_same_pass_raw": carrier_to_raw,
        "rank_regression": rank,
        "tolerance_source": "htt.obsstat.planck_irrep_carrier.scalar_feature_closure_report",
        "tolerance_changed_after_execution": False,
    }
    _atomic_json(staging_dir / "scalar_closure.json", scalar_closure)
    input_receipt = {
        "format": "PLANCK_PR3_PAIRED300_INPUT_IDENTITY_RECEIPT_V1",
        "state": "MATCH",
        "source_manifest_sha256": source_manifest_sha256,
        "private_execution_manifest_sha256": private_execution_manifest_sha256,
        "selected_input_identity_set_sha256": identity_set_sha256,
        "selected_regular_file_count": 602,
        "observed_file_count": 1,
        "temperature_mask_file_count": 1,
        "cmb_file_count": 300,
        "noise_file_count": 300,
        "content_identity_policy": "STREAMING_SHA256_BEFORE_FIRST_SCIENTIFIC_READ",
        "post_read_identity_policy": "DEVICE_INODE_SIZE_MTIME_MATCH",
        "raw_data_mutation": False,
        "raw_paths_embedded_in_portable_receipt": False,
        "accepted_intake_provenance": provenance_rebind,
        "checkpoint_content_identity": "DECODED_NUMERICAL_CONTENT_BOUND",
    }
    _atomic_json(staging_dir / "input_identity_receipt.json", input_receipt)
    _atomic_json(staging_dir / "leakage_receipt.json", leakage)
    carrier_replay = replay_planck_irrep_carrier(
        package_path=staging_dir / "carrier.npz",
        metadata_path=staging_dir / "metadata.json",
    )
    replay_result = {
        "state": "MATCH",
        "carrier_replay": carrier_replay,
        "rank_regression": rank,
        "leakage_receipt_sha256": _file_sha256(
            staging_dir / "leakage_receipt.json"
        ),
        "raw_maps_reopened": False,
        "scalar_feature_required_identity": "NUMERICAL_CONTENT_IDENTITY",
        "scalar_feature_content_id": scalar_feature_content_id,
        "scalar_feature_identity_disposition": "BYTE_IDENTICAL",
    }
    replay = _replay_receipt_from_result(replay_result)
    _atomic_json(staging_dir / "replay.json", replay)
    artifact_hashes = {
        name: _file_sha256(staging_dir / name)
        for name in sorted(_PORTABLE_OUTPUTS - {"terminal.json"})
    }
    terminal = _pending_terminal_payload(
        operator_identity_sha256=operator_identity_sha256,
        artifact_hashes=artifact_hashes,
    )
    _atomic_json(staging_dir / "terminal.json", terminal)
    os.replace(staging_dir, output_dir)
    return {
        "state": "PENDING_REVIEW",
        "output_dir": str(output_dir),
        "row_count": 301,
        "checkpoint_reused_count": reused_count,
        "operator_identity_sha256": operator_identity_sha256,
        "scalar_closure": "MATCH",
        "rank_regression": rank,
        "raw_data_mutation": False,
        "next_executable_action": "FRESH_REVIEW",
    }


def finalize_reviewed_package(*args, **kwargs):
    """Fail closed: reviewed finalization moved to the external-receipt CLI."""

    raise CarrierExportError(
        "self-attested finalization is disabled; use "
        "replay_planck_paired300_irrep_carrier.py with an external fresh-review receipt"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute-real-host", action="store_true")
    mode.add_argument("--replay-committed", action="store_true")
    parser.add_argument("--workdir", type=Path)
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    started = time.monotonic()
    try:
        if args.execute_real_host:
            if args.workdir is None:
                parser.error("--execute-real-host requires --workdir")
            result = execute_real_host(repo_root=repo_root, workdir=args.workdir)
        else:
            if args.workdir is not None:
                parser.error("--replay-committed does not accept --workdir")
            from obsstat.planck_paired300_evidence import (
                FINAL_TERMINAL_FORMAT,
                verify_portable_artifact_manifest,
            )
            output_dir = repo_root / "docs/generated/planck_pr3_paired300_irrep_carrier"
            terminal = _load_json(output_dir / "terminal.json", label="reviewed terminal")
            if terminal.get("format") != FINAL_TERMINAL_FORMAT:
                raise CarrierExportError(
                    "committed replay requires the externally reviewed terminal"
                )
            review_path = output_dir / "fresh_review.json"
            if terminal.get("fresh_review_receipt_sha256") != _file_sha256(review_path):
                raise CarrierExportError("fresh-review receipt identity drifted")
            frozen = repo_root / "docs/generated/pr315_planck_smica_feature_replay.npz"
            verify_portable_artifact_manifest(
                manifest_path=output_dir / "artifact_manifest.json",
                output_root=output_dir,
                frozen_scalar_package_path=frozen,
            )
            result = _compute_map_free_replay(repo_root=repo_root)
    except Exception as exc:
        print(json.dumps({
            "state": "BLOCKED_PMG_WU005",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }, sort_keys=True), file=sys.stderr, flush=True)
        return 3
    print(json.dumps({**result, "wall_seconds": time.monotonic() - started}, sort_keys=True, allow_nan=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
