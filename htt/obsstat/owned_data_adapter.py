"""Typed, read-only bindings for the owner-provided observational inventory.

This module discovers bytes and lightweight schemas.  It never downloads,
copies, or upgrades a diagnostic binding into an inference law.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np


MATRIX_MEMBER = "HTT_OWNED_DATA_UPGRADE_HANDOFF_20260929/DATASET_ANALYSIS_MATRIX.json"


@dataclass(frozen=True)
class OwnedDataBinding:
    dataset_id: str
    work_packet: str
    role_for_analysis: str
    ownership: str
    path_hint: str
    resolved_path: str
    path_status: str
    sha256: str | None
    byte_count: int | None
    units: str | None
    overlap_family: str | None
    duplicate_relation_status: str
    covariance_status: str
    window_status: str
    schema: Mapping[str, Any]
    claim_ceiling: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_matrix(path: str | Path) -> dict[str, Any]:
    """Load the handoff matrix from JSON, a directory, or the original ZIP."""
    source = Path(path)
    if source.is_dir():
        source = source / "DATASET_ANALYSIS_MATRIX.json"
    if source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as archive:
            payload = json.loads(archive.read(MATRIX_MEMBER))
    else:
        payload = json.loads(source.read_text(encoding="utf-8"))
    rows = payload.get("datasets")
    if payload.get("user_dataset_count") != 52 or not isinstance(rows, list) or len(rows) != 52:
        raise ValueError("owned-data matrix must contain exactly 52 datasets")
    ids = [row.get("dataset_id") for row in rows]
    if any(not isinstance(item, str) or not item for item in ids) or len(set(ids)) != 52:
        raise ValueError("owned-data matrix requires 52 unique non-empty dataset IDs")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolved_hint(repo_root: Path, hint: str, external_workdir: Path | None) -> Path:
    relative = Path(hint)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe inventory path hint: {hint!r}")
    if relative.parts and relative.parts[0] == "workdir" and external_workdir is not None:
        return external_workdir.joinpath(*relative.parts[1:])
    return repo_root / relative


def _path_status(path: Path) -> str:
    if path.is_file():
        return "PRESENT_FILE"
    if path.is_dir():
        return "PRESENT_DIRECTORY"
    if path.is_symlink():
        return "BROKEN_SYMLINK"
    for parent in path.parents:
        if parent.is_symlink() and not parent.exists():
            return "BROKEN_SYMLINK_ANCESTOR"
    return "MISSING"


def _scalar(value: np.ndarray) -> Any:
    if value.shape == ():
        item = value.item()
        if isinstance(item, (str, int, float, bool)) or item is None:
            return item
    return None


def inspect_schema(path: Path) -> dict[str, Any]:
    """Inspect bounded metadata without loading large arrays into the result."""
    suffix = path.suffix.lower()
    if suffix == ".npz":
        fields = {}
        with zipfile.ZipFile(path) as archive:
            for member in sorted(name for name in archive.namelist() if name.endswith(".npy")):
                key = Path(member).stem
                with archive.open(member) as handle:
                    version = np.lib.format.read_magic(handle)
                    if version == (1, 0):
                        shape, fortran, dtype = np.lib.format.read_array_header_1_0(handle)
                    elif version == (2, 0):
                        shape, fortran, dtype = np.lib.format.read_array_header_2_0(handle)
                    else:
                        shape, fortran, dtype = np.lib.format._read_array_header(handle, version)  # type: ignore[attr-defined]
                fields[key] = {"shape": list(shape), "dtype": str(dtype), "fortran_order": bool(fortran), "scalar": None}
        with np.load(path, allow_pickle=False) as arrays:
            for key, field in fields.items():
                if field["shape"] == [] and not np.dtype(field["dtype"]).hasobject:
                    field["scalar"] = _scalar(arrays[key])
        return {"format": "npz", "fields": fields}
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return {"format": "json", "top_level_keys": sorted(map(str, payload))}
        return {"format": "json", "top_level_type": type(payload).__name__}
    if suffix in {".csv", ".txt", ".dat"}:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            first = next((line for line in handle if line.strip() and not line.lstrip().startswith("#")), "")
        dialect = "comma" if "," in first else "whitespace"
        columns = next(csv.reader([first])) if dialect == "comma" and first else first.split()
        return {"format": suffix.lstrip("."), "header_or_first_row": columns[:64]}
    return {"format": suffix.lstrip(".") or "unknown", "inspection": "metadata_only"}


def _availability(row: Mapping[str, Any], schema: Mapping[str, Any]) -> tuple[str, str]:
    metadata = row.get("index_metadata") if isinstance(row.get("index_metadata"), Mapping) else {}
    keys = set(schema.get("fields", {}))
    covariance = "AVAILABLE" if any("cov" in key.lower() for key in keys) else "UNAVAILABLE_NOT_ZERO"
    windows = "AVAILABLE" if any("window" in key.lower() or "binning" in key.lower() for key in keys) else "UNAVAILABLE"
    if row.get("role_for_analysis") == "likelihood_asset_or_release_container":
        covariance = "CONTAINER_REQUIRES_RELEASE_SPECIFIC_ALIGNMENT"
        windows = "CONTAINER_REQUIRES_RELEASE_SPECIFIC_ALIGNMENT"
    if not schema and row.get("role_for_analysis") == "likelihood_asset_or_release_container":
        covariance = "DIRECTORY_CONTAINER_UNINSPECTED"
        windows = "DIRECTORY_CONTAINER_UNINSPECTED"
    elif not schema:
        covariance = "NOT_INSPECTED_INPUT_MISSING"
        windows = "NOT_INSPECTED_INPUT_MISSING"
    return covariance, windows


def bind_owned_products(
    matrix: Mapping[str, Any],
    *,
    repo_root: str | Path,
    external_workdir: str | Path | None = None,
) -> list[OwnedDataBinding]:
    """Resolve all 52 rows, using one resolved path for both schema and hash."""
    rows = matrix.get("datasets")
    if not isinstance(rows, list) or len(rows) != 52:
        raise ValueError("matrix must expose exactly 52 dataset rows")
    root = Path(repo_root).resolve()
    if external_workdir is None:
        configured = os.environ.get("HTT_EXTERNAL_DATA_ROOT")
        external = Path(configured).expanduser() if configured else None
    else:
        external = Path(external_workdir).expanduser()
    bindings: list[OwnedDataBinding] = []
    for row in rows:
        hint = str(row.get("historical_inventory_path_hint", ""))
        path = _resolved_hint(root, hint, external)
        status = _path_status(path)
        schema = inspect_schema(path) if status == "PRESENT_FILE" else {}
        covariance, windows = _availability(row, schema)
        metadata = row.get("index_metadata") if isinstance(row.get("index_metadata"), Mapping) else {}
        bindings.append(OwnedDataBinding(
            dataset_id=str(row["dataset_id"]),
            work_packet=str(row.get("work_packet", "UNASSIGNED")),
            role_for_analysis=str(row.get("role_for_analysis", "unknown")),
            ownership=str(row.get("ownership", "UNKNOWN")),
            path_hint=hint,
            resolved_path=str(path),
            path_status=status,
            sha256=_sha256(path) if status == "PRESENT_FILE" else None,
            byte_count=path.stat().st_size if status == "PRESENT_FILE" else None,
            units=str(metadata["unit"]) if metadata.get("unit") not in (None, "") else None,
            overlap_family=str(row["overlap_family_candidate"]) if row.get("overlap_family_candidate") else None,
            duplicate_relation_status=str(row.get("duplicate_relation_status", "UNKNOWN")),
            covariance_status=covariance,
            window_status=windows,
            schema=schema,
            claim_ceiling=str(row.get("claim_ceiling", "diagnostic_only")),
        ))
    if len({item.dataset_id for item in bindings}) != 52:
        raise ValueError("resolved bindings lost or duplicated dataset IDs")
    return bindings


def binding_report(bindings: Iterable[OwnedDataBinding]) -> dict[str, Any]:
    rows = list(bindings)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.path_status] = counts.get(row.path_status, 0) + 1
    return {
        "schema": "htt.owned_data_bindings/v1",
        "dataset_count": len(rows),
        "status_counts": counts,
        "claim_tier": "diagnostic_only",
        "cross_dataset_independence": "NOT_ASSUMED",
        "bindings": [row.to_dict() for row in rows],
    }
