"""Strict portable carrier for the paired-300 Planck PR3 low-ell pass.

The carrier is an observer-space numerical artifact. It preserves the
retained real harmonic coefficients produced by the frozen joint cut-sky
operator and does not identify physical shear, vorticity, tilt, geometry, or
a Bianchi family.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Mapping, Sequence

import numpy as np

from .planck_pr3_operator import (
    JOINT_CUTSKY_ESTIMATOR_ID,
    JOINT_CUTSKY_RETAINED_DIMENSION,
    LMAX,
    LMIN,
    ordered_row_id_hash,
    real_alm_layout,
)


FORMAT = "PLANCK_PR3_PAIRED300_IRREP_CARRIER_V1"
CLAIM_TIER = "OBSERVER_SPACE_CARRIER_ONLY"
ARTIFACT_MODE = "ENABLING_REPLAYABLE_HARMONIC_CARRIER"
EXPECTED_NULL_ROWS = 300
EXPECTED_TOTAL_ROWS = 301
EXPECTED_DIMENSION = JOINT_CUTSKY_RETAINED_DIMENSION
OBSERVATION_ROW_ID = "PLANCK-PR3-SMICA-OBSERVED"
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class PlanckIrrepCarrierError(RuntimeError):
    """Raised when carrier content, metadata, or replay semantics drift."""


@dataclass(frozen=True)
class PlanckIrrepCarrierPool:
    observed_real_alm: np.ndarray
    null_real_alm: np.ndarray
    row_ids: tuple[str, ...]
    layout: tuple[tuple[int, int, str], ...]
    content_id: str


def _strict_sha256(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise PlanckIrrepCarrierError(f"{label} must be one sha256 identity")
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
        raise PlanckIrrepCarrierError(f"{label} is not canonical JSON") from exc


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


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _array_digest(value: np.ndarray, *, role: str) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(role.encode("ascii") + b"\0")
    digest.update(array.dtype.str.encode("ascii") + b"\0")
    digest.update(repr(array.shape).encode("ascii") + b"\0")
    digest.update(memoryview(array).cast("B"))
    return "sha256:" + digest.hexdigest()


def _expected_layout() -> tuple[tuple[int, int, str], ...]:
    layout = real_alm_layout(lmin=LMIN, lmax=LMAX)
    if len(layout) != EXPECTED_DIMENSION:
        raise PlanckIrrepCarrierError("frozen real-alm layout dimension drifted")
    return layout


def _validate_rows(
    *,
    observed_real_alm: object,
    null_real_alm: object,
    row_ids: Sequence[str],
    null_ordered_row_ids_sha256: str,
) -> PlanckIrrepCarrierPool:
    observed = np.asarray(observed_real_alm)
    nulls = np.asarray(null_real_alm)
    if observed.dtype != np.dtype("float64") or nulls.dtype != np.dtype("float64"):
        raise PlanckIrrepCarrierError("carrier arrays must be native float64")
    if observed.shape != (EXPECTED_DIMENSION,):
        raise PlanckIrrepCarrierError("observed carrier must have shape (32,)")
    if nulls.shape != (EXPECTED_NULL_ROWS, EXPECTED_DIMENSION):
        raise PlanckIrrepCarrierError("null carrier must have shape (300,32)")
    if not np.all(np.isfinite(observed)) or not np.all(np.isfinite(nulls)):
        raise PlanckIrrepCarrierError("carrier arrays must be finite")

    identifiers = tuple(row_ids)
    if (
        len(identifiers) != EXPECTED_TOTAL_ROWS
        or identifiers[0] != OBSERVATION_ROW_ID
        or any(not isinstance(value, str) or not value for value in identifiers)
        or len(set(identifiers)) != len(identifiers)
    ):
        raise PlanckIrrepCarrierError("carrier row identity or order is malformed")
    expected_null_hash = _strict_sha256(
        null_ordered_row_ids_sha256,
        label="null ordered row identity",
    )
    if ordered_row_id_hash(identifiers[1:]) != expected_null_hash:
        raise PlanckIrrepCarrierError("null row order differs from its registered identity")

    layout = _expected_layout()
    projection = {
        "format": FORMAT,
        "observed_sha256": _array_digest(observed, role="observed_real_alm"),
        "null_sha256": _array_digest(nulls, role="null_real_alm"),
        "row_ids": list(identifiers),
        "layout": [list(row) for row in layout],
    }
    return PlanckIrrepCarrierPool(
        observed_real_alm=observed.copy(),
        null_real_alm=nulls.copy(),
        row_ids=identifiers,
        layout=layout,
        content_id=_canonical_hash(projection, role="planck_irrep_carrier_content"),
    )


def _validate_operator_identity(value: Mapping[str, object]) -> dict[str, object]:
    clone = _json_clone(value, label="operator identity")
    if not isinstance(clone, dict):
        raise PlanckIrrepCarrierError("operator identity must be a mapping")
    if (
        clone.get("estimator_id") != JOINT_CUTSKY_ESTIMATOR_ID
        or clone.get("retained_dimension") != EXPECTED_DIMENSION
        or clone.get("basis_dimension") != 36
        or clone.get("transfer_order")
        != "JOINT_MASKED_FIT_THEN_BEAM_PIXEL_COMMONIZATION"
    ):
        raise PlanckIrrepCarrierError("operator identity is not the frozen joint cut-sky fit")
    for key in ("mask_sha256", "normal_matrix_sha256", "operator_sha256"):
        _strict_sha256(clone.get(key), label=f"operator identity {key}")
    return clone


def _validate_transfer_identity(value: Mapping[str, object]) -> dict[str, object]:
    clone = _json_clone(value, label="beam/pixel transfer identity")
    if not isinstance(clone, dict):
        raise PlanckIrrepCarrierError("beam/pixel transfer identity must be a mapping")
    required = {
        "source_beam_sha256",
        "source_pixel_window_sha256",
        "target_beam_sha256",
        "target_pixel_window_sha256",
    }
    if set(clone) != required:
        raise PlanckIrrepCarrierError("beam/pixel transfer identity keys drifted")
    for key in sorted(required):
        _strict_sha256(clone[key], label=f"beam/pixel transfer {key}")
    return clone


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


def write_planck_irrep_carrier(
    *,
    package_path: Path,
    metadata_path: Path,
    observed_real_alm: object,
    null_real_alm: object,
    row_ids: Sequence[str],
    null_ordered_row_ids_sha256: str,
    operator_identity: Mapping[str, object],
    transfer_identity: Mapping[str, object],
    source_manifest_sha256: str,
    scalar_feature_package_sha256: str,
) -> dict[str, object]:
    """Write a strict no-pickle 301x32 carrier and metadata."""

    package_path = Path(package_path)
    metadata_path = Path(metadata_path)
    if package_path.suffix != ".npz" or metadata_path.suffix != ".json":
        raise PlanckIrrepCarrierError("carrier outputs must be NPZ plus JSON")
    if package_path.exists() or package_path.is_symlink():
        raise PlanckIrrepCarrierError("carrier package output already exists")
    if metadata_path.exists() or metadata_path.is_symlink():
        raise PlanckIrrepCarrierError("carrier metadata output already exists")
    if package_path.parent != metadata_path.parent:
        raise PlanckIrrepCarrierError("carrier package and metadata must share one directory")
    package_path.parent.mkdir(parents=True, exist_ok=True)
    if package_path.parent.is_symlink():
        raise PlanckIrrepCarrierError("carrier output directory cannot be a symlink")

    pool = _validate_rows(
        observed_real_alm=observed_real_alm,
        null_real_alm=null_real_alm,
        row_ids=row_ids,
        null_ordered_row_ids_sha256=null_ordered_row_ids_sha256,
    )
    operator = _validate_operator_identity(operator_identity)
    transfer = _validate_transfer_identity(transfer_identity)
    source_identity = _strict_sha256(
        source_manifest_sha256,
        label="source manifest identity",
    )
    scalar_identity = _strict_sha256(
        scalar_feature_package_sha256,
        label="scalar feature package identity",
    )
    layout_array = np.asarray(pool.layout, dtype="U8")
    row_array = np.asarray(pool.row_ids, dtype="U64")
    _atomic_npz(
        package_path,
        observed_real_alm=pool.observed_real_alm,
        null_real_alm=pool.null_real_alm,
        row_ids=row_array,
        real_alm_layout=layout_array,
    )
    metadata: dict[str, object] = {
        "format": FORMAT,
        "artifact_mode": ARTIFACT_MODE,
        "claim_tier": CLAIM_TIER,
        "allowed_use": [
            "map-free harmonic replay",
            "scalar feature closure",
            "observer-space irrep projection in PMG-WU-006",
        ],
        "forbidden_use": [
            "physical shear or vorticity measurement",
            "local boost versus global tilt identification",
            "Bianchi family identification",
            "likelihood or posterior",
        ],
        "package_filename": package_path.name,
        "package_byte_size": package_path.stat().st_size,
        "package_sha256": _file_sha256(package_path),
        "carrier_content_id": pool.content_id,
        "dtype": "float64",
        "observed_shape": [EXPECTED_DIMENSION],
        "null_shape": [EXPECTED_NULL_ROWS, EXPECTED_DIMENSION],
        "row_count": EXPECTED_TOTAL_ROWS,
        "observation_row_id": OBSERVATION_ROW_ID,
        "null_ordered_row_ids_sha256": null_ordered_row_ids_sha256,
        "real_alm_layout": [list(row) for row in pool.layout],
        "real_alm_layout_sha256": _canonical_hash(
            [list(row) for row in pool.layout],
            role="real_alm_layout",
        ),
        "lmin": LMIN,
        "lmax": LMAX,
        "map_unit": "microK_CMB",
        "coordinate_frame": "GALACTIC",
        "harmonic_convention": "ORTHONORMAL_CONDON_SHORTLEY_REAL_MAP",
        "operator_identity": operator,
        "operator_identity_sha256": _canonical_hash(
            operator,
            role="joint_cutsky_operator_identity",
        ),
        "transfer_identity": transfer,
        "transfer_identity_sha256": _canonical_hash(
            transfer,
            role="beam_pixel_transfer_identity",
        ),
        "source_manifest_sha256": source_identity,
        "scalar_feature_package_sha256": scalar_identity,
        "raw_maps_reopened_by_replay": False,
    }
    _atomic_json(metadata_path, metadata)
    return {
        **metadata,
        "metadata_sha256": _file_sha256(metadata_path),
    }


def replay_planck_irrep_carrier(
    *,
    package_path: Path,
    metadata_path: Path,
) -> dict[str, object]:
    """Replay and verify a committed carrier without reopening maps."""

    package_path = Path(package_path)
    metadata_path = Path(metadata_path)
    try:
        metadata = json.loads(metadata_path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PlanckIrrepCarrierError("carrier metadata is not strict JSON") from exc
    if not isinstance(metadata, dict) or metadata.get("format") != FORMAT:
        raise PlanckIrrepCarrierError("carrier metadata format drifted")
    if (
        metadata.get("package_filename") != package_path.name
        or metadata.get("package_byte_size") != package_path.stat().st_size
        or metadata.get("package_sha256") != _file_sha256(package_path)
        or metadata.get("claim_tier") != CLAIM_TIER
        or metadata.get("artifact_mode") != ARTIFACT_MODE
        or metadata.get("raw_maps_reopened_by_replay") is not False
    ):
        raise PlanckIrrepCarrierError("carrier package or claim metadata drifted")

    operator = metadata.get("operator_identity")
    transfer = metadata.get("transfer_identity")
    if not isinstance(operator, Mapping) or not isinstance(transfer, Mapping):
        raise PlanckIrrepCarrierError("carrier operator/transfer identity is missing")
    validated_operator = _validate_operator_identity(operator)
    validated_transfer = _validate_transfer_identity(transfer)
    if metadata.get("operator_identity_sha256") != _canonical_hash(
        validated_operator,
        role="joint_cutsky_operator_identity",
    ):
        raise PlanckIrrepCarrierError("carrier operator identity hash drifted")
    if metadata.get("transfer_identity_sha256") != _canonical_hash(
        validated_transfer,
        role="beam_pixel_transfer_identity",
    ):
        raise PlanckIrrepCarrierError("carrier transfer identity hash drifted")
    _strict_sha256(metadata.get("source_manifest_sha256"), label="source manifest")
    _strict_sha256(
        metadata.get("scalar_feature_package_sha256"),
        label="scalar feature package",
    )

    try:
        with np.load(package_path, allow_pickle=False) as bundle:
            if set(bundle.files) != {
                "observed_real_alm",
                "null_real_alm",
                "row_ids",
                "real_alm_layout",
            }:
                raise PlanckIrrepCarrierError("carrier NPZ keys drifted")
            observed = np.asarray(bundle["observed_real_alm"])
            nulls = np.asarray(bundle["null_real_alm"])
            row_ids = tuple(str(value) for value in bundle["row_ids"].tolist())
            layout = tuple(
                (int(row[0]), int(row[1]), str(row[2]))
                for row in bundle["real_alm_layout"].tolist()
            )
    except (KeyError, OSError, ValueError) as exc:
        raise PlanckIrrepCarrierError("carrier is not a safe numeric NPZ") from exc

    pool = _validate_rows(
        observed_real_alm=observed,
        null_real_alm=nulls,
        row_ids=row_ids,
        null_ordered_row_ids_sha256=str(
            metadata.get("null_ordered_row_ids_sha256")
        ),
    )
    if layout != pool.layout:
        raise PlanckIrrepCarrierError("carrier real-alm layout payload drifted")
    if metadata.get("real_alm_layout") != [list(row) for row in pool.layout]:
        raise PlanckIrrepCarrierError("carrier real-alm layout metadata drifted")
    if metadata.get("real_alm_layout_sha256") != _canonical_hash(
        [list(row) for row in pool.layout],
        role="real_alm_layout",
    ):
        raise PlanckIrrepCarrierError("carrier real-alm layout hash drifted")
    if metadata.get("carrier_content_id") != pool.content_id:
        raise PlanckIrrepCarrierError("carrier scientific content identity drifted")
    if (
        metadata.get("dtype") != "float64"
        or metadata.get("observed_shape") != [EXPECTED_DIMENSION]
        or metadata.get("null_shape")
        != [EXPECTED_NULL_ROWS, EXPECTED_DIMENSION]
        or metadata.get("row_count") != EXPECTED_TOTAL_ROWS
        or metadata.get("observation_row_id") != OBSERVATION_ROW_ID
        or metadata.get("map_unit") != "microK_CMB"
        or metadata.get("coordinate_frame") != "GALACTIC"
        or metadata.get("lmin") != LMIN
        or metadata.get("lmax") != LMAX
    ):
        raise PlanckIrrepCarrierError("carrier schema metadata drifted")
    return {
        "state": "REPLAY_MATCH",
        "format": FORMAT,
        "carrier_content_id": pool.content_id,
        "package_sha256": metadata["package_sha256"],
        "metadata_sha256": _file_sha256(metadata_path),
        "operator_identity_sha256": metadata["operator_identity_sha256"],
        "transfer_identity_sha256": metadata["transfer_identity_sha256"],
        "row_count": EXPECTED_TOTAL_ROWS,
        "carrier_dimension": EXPECTED_DIMENSION,
        "raw_maps_reopened": False,
        "claim_tier": CLAIM_TIER,
    }


def scalar_feature_closure_report(
    *,
    observed_expected: object,
    observed_projected: object,
    null_expected: object,
    null_projected: object,
) -> dict[str, object]:
    """Require carrier-derived scalar rows to close against the frozen package."""

    observed_a = np.asarray(observed_expected, dtype=np.float64)
    observed_b = np.asarray(observed_projected, dtype=np.float64)
    null_a = np.asarray(null_expected, dtype=np.float64)
    null_b = np.asarray(null_projected, dtype=np.float64)
    if observed_a.shape != (12,) or observed_b.shape != (12,):
        raise PlanckIrrepCarrierError("observed scalar closure shape drifted")
    if null_a.shape != (EXPECTED_NULL_ROWS, 12) or null_b.shape != null_a.shape:
        raise PlanckIrrepCarrierError("null scalar closure shape drifted")
    if any(
        not np.all(np.isfinite(value))
        for value in (observed_a, observed_b, null_a, null_b)
    ):
        raise PlanckIrrepCarrierError("scalar closure inputs must be finite")

    atol = np.asarray([1.0e-9] * 4 + [1.0e-12] * 8, dtype=np.float64)
    rtol = np.asarray([1.0e-12] * 12, dtype=np.float64)
    observed_delta = np.abs(observed_a - observed_b)
    null_delta = np.abs(null_a - null_b)
    observed_limit = atol + rtol * np.abs(observed_a)
    null_limit = atol[None, :] + rtol[None, :] * np.abs(null_a)
    passed = bool(
        np.all(observed_delta <= observed_limit)
        and np.all(null_delta <= null_limit)
    )
    report = {
        "state": "MATCH" if passed else "MISMATCH",
        "feature_count": 12,
        "null_rows": EXPECTED_NULL_ROWS,
        "absolute_tolerance": atol.tolist(),
        "relative_tolerance": rtol.tolist(),
        "observed_max_abs_delta": float(observed_delta.max()),
        "null_max_abs_delta": float(null_delta.max()),
        "observed_max_bound_ratio": float(
            np.max(observed_delta / np.maximum(observed_limit, np.finfo(float).tiny))
        ),
        "null_max_bound_ratio": float(
            np.max(null_delta / np.maximum(null_limit, np.finfo(float).tiny))
        ),
    }
    if not passed:
        raise PlanckIrrepCarrierError(
            "carrier-derived scalar features differ from the frozen rows"
        )
    return report
