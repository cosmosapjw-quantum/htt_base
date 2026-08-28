"""Data-independent one-pass helpers for PMG-WU-005.

This module owns exact row ordering, same-pass feature/carrier assembly, and
selected-file immutability primitives. Raw FITS discovery and execution remain
in the observed-run layer.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

import numpy as np

from .planck_irrep_carrier import (
    EXPECTED_DIMENSION,
    EXPECTED_NULL_ROWS,
    OBSERVATION_ROW_ID,
)
from .planck_pr3_operator import alm_to_real_vector


class Paired300ExecutionError(RuntimeError):
    """Raised when one-pass carrier execution violates its frozen contract."""


@dataclass(frozen=True)
class Paired300ExecutionRows:
    observed_features: np.ndarray
    null_features: np.ndarray
    observed_real_alm: np.ndarray
    null_real_alm: np.ndarray
    row_ids: tuple[str, ...]
    row_count: int
    process_call_count: int


def expected_paired300_row_ids() -> tuple[str, ...]:
    """Return the exact frozen FFP10 paired-null row order."""

    return tuple(
        f"FFP10-SMICA-CMBNOISE-{index:05d}"
        for index in range(EXPECTED_NULL_ROWS)
    )


def carrier_vector_from_alm(alm: object) -> np.ndarray:
    """Convert one retained/full packed alm payload to the frozen 32-real layout."""

    try:
        carrier = np.asarray(
            alm_to_real_vector(alm, lmin=2, lmax=5),
            dtype=np.float64,
        )
    except Exception as exc:
        raise Paired300ExecutionError(
            "packed alm could not be converted to the frozen real carrier"
        ) from exc
    if carrier.shape != (EXPECTED_DIMENSION,) or not np.all(np.isfinite(carrier)):
        raise Paired300ExecutionError("carrier shape or finiteness drifted")
    return carrier


def _validate_processed_row(
    payload: object,
    *,
    row_id: str,
    carrier_from_alm: Callable[[object], np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    if not isinstance(payload, tuple) or len(payload) != 3:
        raise Paired300ExecutionError(
            f"process_map return for {row_id} must be features,timings,alm"
        )
    features_raw, timings, alm = payload
    features = np.asarray(features_raw, dtype=np.float64)
    if features.shape != (12,):
        raise Paired300ExecutionError(f"feature shape drifted for {row_id}")
    if not np.all(np.isfinite(features)):
        raise Paired300ExecutionError(f"feature row became nonfinite for {row_id}")
    if not isinstance(timings, Mapping):
        raise Paired300ExecutionError(f"timing payload drifted for {row_id}")
    carrier = np.asarray(carrier_from_alm(alm))
    if carrier.dtype != np.dtype("float64"):
        raise Paired300ExecutionError(f"carrier dtype drifted for {row_id}")
    if carrier.shape != (EXPECTED_DIMENSION,):
        raise Paired300ExecutionError(f"carrier shape drifted for {row_id}")
    if not np.all(np.isfinite(carrier)):
        raise Paired300ExecutionError(f"carrier became nonfinite for {row_id}")
    return features.copy(), carrier.copy()


def process_paired300_rows_one_pass(
    *,
    observed_map: object,
    null_rows: Iterable[tuple[str, object]],
    context: Mapping[str, object],
    process_map: Callable[..., tuple[object, object, object]],
    carrier_from_alm: Callable[[object], np.ndarray] = carrier_vector_from_alm,
) -> Paired300ExecutionRows:
    """Process observation and exact paired-300 rows once in frozen order."""

    if not isinstance(context, Mapping):
        raise Paired300ExecutionError("operator context must be a mapping")
    observed_features, observed_carrier = _validate_processed_row(
        process_map(observed_map, component="SMICA", context=context),
        row_id=OBSERVATION_ROW_ID,
        carrier_from_alm=carrier_from_alm,
    )

    expected = expected_paired300_row_ids()
    identifiers: list[str] = []
    feature_rows: list[np.ndarray] = []
    carrier_rows: list[np.ndarray] = []
    for ordinal, row in enumerate(null_rows):
        if not isinstance(row, tuple) or len(row) != 2:
            raise Paired300ExecutionError(
                "null row iterator must yield (row_id,map) pairs"
            )
        row_id, pixel_map = row
        if ordinal >= EXPECTED_NULL_ROWS or row_id != expected[ordinal]:
            raise Paired300ExecutionError(
                "paired null rows are not in the exact registered order"
            )
        features, carrier = _validate_processed_row(
            process_map(pixel_map, component="SMICA", context=context),
            row_id=row_id,
            carrier_from_alm=carrier_from_alm,
        )
        identifiers.append(row_id)
        feature_rows.append(features)
        carrier_rows.append(carrier)

    if tuple(identifiers) != expected:
        raise Paired300ExecutionError(
            "paired null rows are not in the exact registered order"
        )
    null_features = np.asarray(feature_rows, dtype=np.float64)
    null_carrier = np.asarray(carrier_rows, dtype=np.float64)
    if null_features.shape != (EXPECTED_NULL_ROWS, 12):
        raise Paired300ExecutionError("assembled null feature matrix shape drifted")
    if null_carrier.shape != (EXPECTED_NULL_ROWS, EXPECTED_DIMENSION):
        raise Paired300ExecutionError("assembled null carrier matrix shape drifted")
    return Paired300ExecutionRows(
        observed_features=observed_features,
        null_features=null_features,
        observed_real_alm=observed_carrier,
        null_real_alm=null_carrier,
        row_ids=(OBSERVATION_ROW_ID, *identifiers),
        row_count=EXPECTED_NULL_ROWS + 1,
        process_call_count=EXPECTED_NULL_ROWS + 1,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def capture_regular_file_identity(
    path: Path,
    *,
    hash_content: bool,
) -> dict[str, object]:
    """Capture a fail-closed regular-file identity for raw-input guards."""

    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.resolve() != path:
        raise Paired300ExecutionError(
            "input must be one absolute regular non-symlink file"
        )
    stat = path.stat(follow_symlinks=False)
    payload: dict[str, object] = {
        "path": str(path),
        "device": stat.st_dev,
        "inode": stat.st_ino,
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": None,
    }
    if hash_content:
        payload["sha256"] = _sha256(path)
    return payload


def require_regular_file_identity_unchanged(
    path: Path,
    expected: Mapping[str, object],
) -> dict[str, object]:
    """Re-read the same identity role and reject stat or content mutation."""

    if not isinstance(expected, Mapping):
        raise Paired300ExecutionError("expected file identity must be a mapping")
    current = capture_regular_file_identity(
        Path(path),
        hash_content=expected.get("sha256") is not None,
    )
    if dict(expected) != current:
        raise Paired300ExecutionError(f"raw input mutated: {path}")
    return current
