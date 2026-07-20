"""Authenticated raw Cosmicflows-4 group adapter for PR-179.

Only the prospectively frozen catalogue columns are exposed.  In particular,
the adapter never parses the cosmology-corrected ``fV3k/Hi/logHi`` values, the
peculiar-velocity reconstructions, or the velocity-unit Cartesian columns into
the scientific object.  It joins the two release tables by the unique 1PGC
group identifier and keeps method metadata in a selection/nuisance sidecar.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np

from common.cf4_manifest import (
    TABLE3_COLUMNS,
    TABLE4_COLUMNS,
    file_sha256,
    id_parity,
    read_lines,
    require_registered_column,
)

__all__ = [
    "CF4_PR179_DENYLIST",
    "CF4_PR179_PRIMARY_COLUMNS",
    "Cf4RawGroupCatalog",
    "Cf4RawInputError",
    "load_authenticated_cf4_raw_groups",
    "require_pr179_columns",
    "require_pr179_value_access",
]


CF4_PR179_PRIMARY_COLUMNS = {
    "table3": ("1PGC", "Vcmb", "RAdeg", "DEdeg"),
    "table4": ("1PGC", "DMzp", "e_DMzp"),
}
CF4_PR179_SELECTION_COLUMNS = (
    "o_DMcal",
    "o_DMsnIa",
    "o_DMfp",
    "o_DMtf",
    "o_DMsbfo",
    "o_DMsbfi",
    "DMcal",
    "DMsnIa",
    "e_DMsnIa",
    "DMfp",
    "e_DMfp",
    "DMtf",
    "e_DMtf",
    "DMsbfo",
    "e_DMsbfo",
    "DMsbfi",
    "e_DMsbfi",
    "DMsnII",
    "e_DMsnII",
)
CF4_PR179_DENYLIST = (
    "fV3k",
    "Hi",
    "logHi",
    "Vpds",
    "Vpwf",
    "Vpec",
    "Dist",
    "SGX",
    "SGY",
    "SGZ",
)
_PR179_VALUE_ACCESS = {
    "table3": frozenset(CF4_PR179_PRIMARY_COLUMNS["table3"] + CF4_PR179_SELECTION_COLUMNS),
    "table4": frozenset(CF4_PR179_PRIMARY_COLUMNS["table4"]),
}
_METHOD_LABELS = np.asarray(("CAL", "SN", "FP", "TF", "SBF", "MIXED_OTHER"))


class Cf4RawInputError(ValueError):
    """Raised when PR-179 raw-input or column authority fails closed."""


def require_pr179_columns(columns: Mapping[str, tuple[str, ...] | list[str]]) -> None:
    """Require the literal frozen allowlist and reject every denied field."""

    normalized = {str(table): tuple(str(x) for x in values)
                  for table, values in columns.items()}
    if normalized != CF4_PR179_PRIMARY_COLUMNS:
        flattened = {value for values in normalized.values() for value in values}
        denied = sorted(flattened.intersection(CF4_PR179_DENYLIST))
        if denied:
            raise Cf4RawInputError(
                "forbidden PR-179 input column(s): " + ", ".join(denied)
            )
        raise Cf4RawInputError("PR-179 primary column allowlist drift")


def require_pr179_value_access(table: str, label: str) -> None:
    """Capability gate used by every production fixed-width value access."""

    if table not in _PR179_VALUE_ACCESS:
        raise Cf4RawInputError(f"unknown PR-179 table capability: {table!r}")
    if label not in _PR179_VALUE_ACCESS[table]:
        if label in CF4_PR179_DENYLIST:
            raise Cf4RawInputError(f"forbidden PR-179 value access: {table}.{label}")
        raise Cf4RawInputError(f"unregistered PR-179 value access: {table}.{label}")


def _column_map(columns) -> dict[str, object]:
    return {column.label: column for column in columns}


def _values(lines: list[str], columns, label: str, *, dtype=float) -> np.ndarray:
    column = require_registered_column(label, columns)
    values = [column.value(line) for line in lines]
    if dtype is int:
        if any(value is None for value in values):
            raise Cf4RawInputError(f"required integer column {label} contains blanks")
        return np.asarray(values, dtype=np.int64)
    return np.asarray([np.nan if value is None else float(value) for value in values],
                      dtype=float)


def _stable_hash_records(ids: np.ndarray, selected: np.ndarray | None = None) -> str:
    import hashlib

    payload = ids if selected is None else ids[np.asarray(selected, dtype=bool)]
    return hashlib.sha256(np.asarray(payload, dtype="<i8").tobytes()).hexdigest()


@dataclass(frozen=True)
class Cf4RawGroupCatalog:
    """One-row-per-group PR-179 catalogue surface.

    Arrays are sorted by 1PGC.  ``selection`` contains only the frozen
    method-availability/count/error sidecar and cannot become the target.
    """

    group_id: np.ndarray
    dmzp: np.ndarray
    e_dmzp: np.ndarray
    vcmb_km_s: np.ndarray
    ra_deg: np.ndarray
    dec_deg: np.ndarray
    method_family: np.ndarray
    selection: Mapping[str, np.ndarray]
    source_hashes: Mapping[str, str]
    accessed_columns: Mapping[str, tuple[str, ...]]
    row_id_sha256: str

    def __post_init__(self) -> None:
        n = int(self.group_id.size)
        if n <= 0:
            raise Cf4RawInputError("CF4 raw group catalogue is empty")
        arrays = (
            self.dmzp,
            self.e_dmzp,
            self.vcmb_km_s,
            self.ra_deg,
            self.dec_deg,
            self.method_family,
        )
        if any(np.asarray(value).ndim != 1 or len(value) != n for value in arrays):
            raise Cf4RawInputError("CF4 raw group arrays have inconsistent shapes")
        if len(np.unique(self.group_id)) != n:
            raise Cf4RawInputError("CF4 1PGC identities are not unique")
        if np.any(np.diff(self.group_id) <= 0):
            raise Cf4RawInputError("CF4 1PGC identities are not in stable sorted order")
        if any(np.asarray(value).shape != (n,) for value in self.selection.values()):
            raise Cf4RawInputError("CF4 selection sidecar shape mismatch")
        if not set(np.unique(self.method_family)).issubset(set(_METHOD_LABELS)):
            raise Cf4RawInputError("unregistered CF4 method family")
        expected_access = {
            table: tuple(sorted(values)) for table, values in _PR179_VALUE_ACCESS.items()
        }
        if dict(self.accessed_columns) != expected_access:
            raise Cf4RawInputError("runtime PR-179 column-access receipt is incomplete")

    @property
    def row_count(self) -> int:
        return int(self.group_id.size)

    def primary_domain_mask(
        self,
        *,
        c_km_s: float = 299792.458,
        z_min: float = 0.01,
        z_max: float = 0.10,
    ) -> np.ndarray:
        z = self.vcmb_km_s / float(c_km_s)
        return (
            np.isfinite(self.dmzp)
            & np.isfinite(self.e_dmzp)
            & (self.e_dmzp > 0.0)
            & np.isfinite(z)
            & (z >= float(z_min))
            & (z <= float(z_max))
            & np.isfinite(self.ra_deg)
            & np.isfinite(self.dec_deg)
            & (self.ra_deg >= 0.0)
            & (self.ra_deg < 360.0)
            & (self.dec_deg >= -90.0)
            & (self.dec_deg <= 90.0)
        )

    def selected_row_sha256(self, mask: np.ndarray) -> str:
        return _stable_hash_records(self.group_id, mask)


def _method_families(selection: Mapping[str, np.ndarray]) -> np.ndarray:
    n = len(selection["o_DMcal"])
    precision = np.zeros((n, 4), dtype=float)

    def contribution(count_name: str | None, error_name: str) -> np.ndarray:
        error = np.asarray(selection[error_name], dtype=float)
        valid = np.isfinite(error) & (error > 0.0)
        count = np.ones(n, dtype=float)
        if count_name is not None:
            raw = np.asarray(selection[count_name], dtype=float)
            count = np.where(np.isfinite(raw) & (raw > 0.0), raw, 0.0)
        out = np.zeros(n, dtype=float)
        out[valid] = count[valid] / np.square(error[valid])
        return out

    # SN, FP, TF, SBF.  SNII has no registered count, so its available group
    # distance contributes one precision unit rather than an invented count.
    precision[:, 0] = (
        contribution("o_DMsnIa", "e_DMsnIa")
        + contribution(None, "e_DMsnII")
    )
    precision[:, 1] = contribution("o_DMfp", "e_DMfp")
    precision[:, 2] = contribution("o_DMtf", "e_DMtf")
    precision[:, 3] = (
        contribution("o_DMsbfo", "e_DMsbfo")
        + contribution("o_DMsbfi", "e_DMsbfi")
    )
    total = precision.sum(axis=1)
    top = np.argmax(precision, axis=1)
    share = np.divide(
        precision[np.arange(n), top],
        total,
        out=np.zeros(n, dtype=float),
        where=total > 0.0,
    )
    labels = np.full(n, "MIXED_OTHER", dtype="U16")
    precision_labels = np.asarray(("SN", "FP", "TF", "SBF"))
    dominant = (total > 0.0) & (share >= 0.8)
    labels[dominant] = precision_labels[top[dominant]]
    calibrator_only = (
        (total == 0.0)
        & np.isfinite(selection["o_DMcal"])
        & (selection["o_DMcal"] > 0.0)
    )
    labels[calibrator_only] = "CAL"
    return labels


def load_authenticated_cf4_raw_groups(
    table3_path: str | Path,
    table4_path: str | Path,
    *,
    expected_table3_sha256: str,
    expected_table4_sha256: str,
    expected_rows: int = 38053,
    primary_columns: Mapping[str, tuple[str, ...] | list[str]] = CF4_PR179_PRIMARY_COLUMNS,
) -> Cf4RawGroupCatalog:
    """Authenticate, join, and expose the frozen PR-179 raw group surface."""

    require_pr179_columns(primary_columns)
    path3, path4 = Path(table3_path), Path(table4_path)
    hash3, hash4 = file_sha256(path3), file_sha256(path4)
    if hash3 != expected_table3_sha256 or hash4 != expected_table4_sha256:
        raise Cf4RawInputError("CF4 raw source hash mismatch")
    lines3, lines4 = read_lines(path3), read_lines(path4)
    if len(lines3) != expected_rows or len(lines4) != expected_rows:
        raise Cf4RawInputError("CF4 raw source row-count mismatch")
    parity = id_parity(lines3, lines4)
    if not parity["parity"] or parity["n_unique"] != expected_rows:
        raise Cf4RawInputError("CF4 raw source 1PGC parity failure")

    require_pr179_value_access("table3", "1PGC")
    require_pr179_value_access("table4", "1PGC")
    ids3 = _values(lines3, TABLE3_COLUMNS, "1PGC", dtype=int)
    ids4 = _values(lines4, TABLE4_COLUMNS, "1PGC", dtype=int)
    if len(np.unique(ids3)) != expected_rows or len(np.unique(ids4)) != expected_rows:
        raise Cf4RawInputError("CF4 raw source duplicate 1PGC")
    row3 = {int(value): index for index, value in enumerate(ids3)}
    row4 = {int(value): index for index, value in enumerate(ids4)}
    ordered_ids = np.asarray(sorted(row3), dtype=np.int64)
    order3 = np.asarray([row3[int(value)] for value in ordered_ids], dtype=np.int64)
    order4 = np.asarray([row4[int(value)] for value in ordered_ids], dtype=np.int64)

    accessed: dict[str, set[str]] = {"table3": {"1PGC"}, "table4": {"1PGC"}}

    def t3(label: str) -> np.ndarray:
        require_pr179_value_access("table3", label)
        accessed["table3"].add(label)
        return _values(lines3, TABLE3_COLUMNS, label)[order3]

    def t4(label: str) -> np.ndarray:
        require_pr179_value_access("table4", label)
        accessed["table4"].add(label)
        return _values(lines4, TABLE4_COLUMNS, label)[order4]

    selection = {label: t3(label) for label in CF4_PR179_SELECTION_COLUMNS}
    families = _method_families(selection)
    return Cf4RawGroupCatalog(
        group_id=ordered_ids,
        dmzp=t4("DMzp"),
        e_dmzp=t4("e_DMzp"),
        vcmb_km_s=t3("Vcmb"),
        ra_deg=t3("RAdeg"),
        dec_deg=t3("DEdeg"),
        method_family=families,
        selection=selection,
        source_hashes={"table3": hash3, "table4": hash4},
        accessed_columns={
            table: tuple(sorted(values)) for table, values in accessed.items()
        },
        row_id_sha256=_stable_hash_records(ordered_ids),
    )
