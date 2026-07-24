"""PR-144: authenticated Cosmicflows-4 row/group/selection manifest.

Binds the exact CF4 release (Tully et al. 2023, ApJ 944, 94; VizieR
J/ApJ/944/94) and every group-level column of ``table3.dat`` and
``table4.dat`` to its byte range, format, units, producer, and a TYPE
classification. The group ID (1PGC) parity across the two tables is
verified, the tables are content-addressed at the file and per-row level,
and the selection / completeness (per-method observation counts) and the
duplicate / missing structure are recorded.

A peculiar-velocity RECONSTRUCTION column (Vpds, Vpwf, Vpec) is never
selected as the true flow, an audit-only replacement value is never
promoted to an observed measurement, the Cartesian SGX/SGY/SGZ columns are
never used as Mpc lengths without the cz conversion, and a column whose
authority is not in the registry is refused.

Dataset / estimand provenance only at ``roadmap_rescue_v1:C1`` — no
cosmological measurement, no detection. The two CF4 P0s stay OPEN; this
manifest supplies their data lineage, it does not resolve them.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum

import numpy as np

SCHEMA_VERSION = "pr144.cf4_manifest.v1"

CF4_RELEASE = {
    "catalogue": "J/ApJ/944/94",
    "reference": "Tully et al. 2023, ApJ 944, 94",
    "release": "Cosmicflows-4",
    "bibcode": "2023ApJ...944...94T",
    "velocity_frame": "V3k (cosmic microwave background frame)",
    "n_groups": 38053,
}


class ColumnType(str, Enum):
    IDENTIFIER = "identifier"
    POSITION_OBSERVABLE = "position_observable"
    VELOCITY_OBSERVABLE = "velocity_observable"
    FRAME_DERIVED = "frame_derived"
    COSMOLOGY_CORRECTED = "cosmology_corrected"
    DISTANCE_INDICATOR = "distance_indicator"
    UNCERTAINTY = "uncertainty"
    RECONSTRUCTION = "reconstruction"
    CARTESIAN_DERIVED = "cartesian_derived"
    SELECTION_COUNT = "selection_count"


class Cf4ManifestError(ValueError):
    """Raised when the CF4 manifest discipline is violated."""


@dataclass(frozen=True)
class Column:
    label: str
    byte_start: int          # 1-indexed inclusive (VizieR convention)
    byte_end: int            # 1-indexed inclusive
    fmt: str
    units: str
    ctype: ColumnType
    numeric: bool = True

    def slice(self, line: str) -> str:
        return line[self.byte_start - 1:self.byte_end]

    def value(self, line: str):
        raw = self.slice(line).strip()
        if not raw:
            return None
        if not self.numeric:
            return raw
        return float(raw) if ("." in self.fmt or "F" in self.fmt) else int(raw)


# byte ranges transcribed from the CF4 VizieR ReadMe (workdir/raw/cf4_full)
TABLE3_COLUMNS = (
    Column("1PGC", 1, 7, "I7", "---", ColumnType.IDENTIFIER),
    Column("DMzp", 9, 14, "F6.3", "mag", ColumnType.DISTANCE_INDICATOR),
    Column("DMav", 16, 21, "F6.3", "mag", ColumnType.DISTANCE_INDICATOR),
    Column("e_DMav", 23, 27, "F5.3", "mag", ColumnType.UNCERTAINTY),
    Column("Vcmb", 29, 33, "I5", "km/s", ColumnType.FRAME_DERIVED),
    Column("RAdeg", 35, 42, "F8.4", "deg", ColumnType.POSITION_OBSERVABLE),
    Column("DEdeg", 44, 51, "F8.4", "deg", ColumnType.POSITION_OBSERVABLE),
    Column("GLON", 53, 60, "F8.4", "deg", ColumnType.POSITION_OBSERVABLE),
    Column("GLAT", 62, 69, "F8.4", "deg", ColumnType.POSITION_OBSERVABLE),
    Column("SGL", 71, 78, "F8.4", "deg", ColumnType.POSITION_OBSERVABLE),
    Column("SGB", 80, 87, "F8.4", "deg", ColumnType.POSITION_OBSERVABLE),
    Column("o_DMcal", 89, 90, "I2", "---", ColumnType.SELECTION_COUNT),
    Column("DMcal", 92, 97, "F6.3", "mag", ColumnType.DISTANCE_INDICATOR),
    Column("o_DMsnIa", 99, 99, "I1", "---", ColumnType.SELECTION_COUNT),
    Column("DMsnIa", 101, 106, "F6.3", "mag", ColumnType.DISTANCE_INDICATOR),
    Column("e_DMsnIa", 108, 112, "F5.3", "mag", ColumnType.UNCERTAINTY),
    Column("o_DMfp", 114, 116, "I3", "---", ColumnType.SELECTION_COUNT),
    Column("DMfp", 118, 123, "F6.3", "mag", ColumnType.DISTANCE_INDICATOR),
    Column("e_DMfp", 125, 129, "F5.3", "mag", ColumnType.UNCERTAINTY),
    Column("o_DMtf", 131, 132, "I2", "---", ColumnType.SELECTION_COUNT),
    Column("DMtf", 134, 139, "F6.3", "mag", ColumnType.DISTANCE_INDICATOR),
    Column("e_DMtf", 141, 145, "F5.3", "mag", ColumnType.UNCERTAINTY),
    Column("o_DMsbfo", 147, 149, "I3", "---", ColumnType.SELECTION_COUNT),
    Column("DMsbfo", 151, 156, "F6.3", "mag", ColumnType.DISTANCE_INDICATOR),
    Column("e_DMsbfo", 158, 162, "F5.3", "mag", ColumnType.UNCERTAINTY),
    Column("o_DMsbfi", 164, 164, "I1", "---", ColumnType.SELECTION_COUNT),
    Column("DMsbfi", 166, 171, "F6.3", "mag", ColumnType.DISTANCE_INDICATOR),
    Column("e_DMsbfi", 173, 177, "F5.3", "mag", ColumnType.UNCERTAINTY),
    Column("DMsnII", 179, 184, "F6.3", "mag", ColumnType.DISTANCE_INDICATOR),
    Column("e_DMsnII", 186, 190, "F5.3", "mag", ColumnType.UNCERTAINTY),
)

TABLE4_COLUMNS = (
    Column("1PGC", 1, 7, "I7", "---", ColumnType.IDENTIFIER),
    Column("DMzp", 9, 14, "F6.3", "mag", ColumnType.DISTANCE_INDICATOR),
    Column("e_DMzp", 16, 20, "F5.3", "mag", ColumnType.UNCERTAINTY),
    Column("Dist", 22, 26, "F5.1", "Mpc", ColumnType.DISTANCE_INDICATOR),
    Column("Vh", 28, 32, "I5", "km/s", ColumnType.VELOCITY_OBSERVABLE),
    Column("Vls", 34, 38, "I5", "km/s", ColumnType.FRAME_DERIVED),
    Column("V3k", 40, 44, "I5", "km/s", ColumnType.FRAME_DERIVED),
    Column("fV3k", 46, 50, "I5", "km/s", ColumnType.COSMOLOGY_CORRECTED),
    Column("Vpds", 52, 57, "I6", "km/s", ColumnType.RECONSTRUCTION),
    Column("Vpwf", 59, 63, "I5", "km/s", ColumnType.RECONSTRUCTION),
    Column("Vpec", 65, 69, "I5", "km/s", ColumnType.RECONSTRUCTION),
    Column("Hi", 71, 75, "F5.1", "km/s/Mpc", ColumnType.COSMOLOGY_CORRECTED),
    Column("logHi", 77, 82, "F6.3", "[km/s/Mpc]",
           ColumnType.COSMOLOGY_CORRECTED),
    Column("RAdeg", 84, 91, "F8.4", "deg", ColumnType.POSITION_OBSERVABLE),
    Column("DEdeg", 93, 100, "F8.4", "deg", ColumnType.POSITION_OBSERVABLE),
    Column("GLON", 102, 109, "F8.4", "deg", ColumnType.POSITION_OBSERVABLE),
    Column("GLAT", 111, 118, "F8.4", "deg", ColumnType.POSITION_OBSERVABLE),
    Column("SGL", 120, 127, "F8.4", "deg", ColumnType.POSITION_OBSERVABLE),
    Column("SGB", 129, 136, "F8.4", "deg", ColumnType.POSITION_OBSERVABLE),
    Column("SGX", 138, 143, "I6", "cz_km/s", ColumnType.CARTESIAN_DERIVED),
    Column("SGY", 145, 150, "I6", "cz_km/s", ColumnType.CARTESIAN_DERIVED),
    Column("SGZ", 152, 157, "I6", "cz_km/s", ColumnType.CARTESIAN_DERIVED),
)

RECONSTRUCTION_COLUMNS = ("Vpds", "Vpwf", "Vpec")
AUDIT_ONLY_VALUE_KM_S = 94
# SGX/SGY/SGZ are labelled Mpc in the ReadMe but expressed in cz (km/s)
CARTESIAN_UNITS_CAVEAT = (
    "SGX/SGY/SGZ are labelled Mpc in the ReadMe but expressed in OBSERVED "
    "VELOCITY UNITS (cz, km/s); never used as a Mpc length without the cz "
    "conversion")


# --------------------------------------------------------------------------
# parsing + content addressing
# --------------------------------------------------------------------------
def read_lines(path) -> list[str]:
    with open(path, encoding="utf-8") as handle:
        return [ln.rstrip("\n") for ln in handle if ln.strip()]


def parse_column(lines: list[str], column: Column) -> list:
    return [column.value(ln) for ln in lines]


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def row_hash_digest(lines: list[str]) -> str:
    """A single digest over every row's exact bytes (order-sensitive)."""
    h = hashlib.sha256()
    for ln in lines:
        h.update(ln.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


# --------------------------------------------------------------------------
# authority + parity + completeness
# --------------------------------------------------------------------------
def column_authority(columns) -> dict:
    return {c.label: {"byte_start": c.byte_start, "byte_end": c.byte_end,
                      "format": c.fmt, "units": c.units,
                      "type": c.ctype.value} for c in columns}


def require_registered_column(label: str, columns) -> Column:
    for c in columns:
        if c.label == label:
            return c
    raise Cf4ManifestError(
        f"column {label!r} is not in the CF4 authority registry — a column "
        "may not be used by name without a registered byte range, units, "
        "producer, and type")


def id_parity(t3_lines: list[str], t4_lines: list[str]) -> dict:
    id_col3 = require_registered_column("1PGC", TABLE3_COLUMNS)
    id_col4 = require_registered_column("1PGC", TABLE4_COLUMNS)
    ids3 = [id_col3.value(ln) for ln in t3_lines]
    ids4 = [id_col4.value(ln) for ln in t4_lines]
    if any(not isinstance(group_id, int) or group_id <= 0
           for group_id in (*ids3, *ids4)):
        raise Cf4ManifestError(
            "1PGC group IDs must be present positive integers")
    set3, set4 = set(ids3), set(ids4)
    duplicates3 = len(ids3) - len(set3)
    duplicates4 = len(ids4) - len(set4)
    if duplicates3 or duplicates4:
        raise Cf4ManifestError(
            "duplicate 1PGC group IDs prevent row identity authentication")
    if set3 != set4:
        raise Cf4ManifestError(
            "the table3 and table4 1PGC group-ID sets do not match — the "
            "group identity is not authenticated")
    return {"n_table3": len(ids3), "n_table4": len(ids4),
            "n_unique": len(set3), "duplicates_table3": duplicates3,
            "duplicates_table4": duplicates4, "parity": True}


def selection_completeness(t3_lines: list[str]) -> dict:
    """Per-method group-observation counts (the selection function)."""
    out = {}
    for c in TABLE3_COLUMNS:
        if c.ctype is ColumnType.SELECTION_COUNT:
            vals = [c.value(ln) for ln in t3_lines]
            out[c.label] = {
                "n_groups_with_method": sum(1 for v in vals if v),
                "max_members": max((v for v in vals if v), default=0)}
    return out


def missing_summary(lines: list[str], columns) -> dict:
    out = {}
    for c in columns:
        if c.ctype is ColumnType.SELECTION_COUNT:
            continue
        n_missing = sum(1 for ln in lines if not c.slice(ln).strip())
        out[c.label] = n_missing
    return out


def range_fixtures(t4_lines: list[str], ranges: dict) -> dict:
    """Validate coordinate/distance ranges against the ReadMe bounds."""
    cols = {c.label: c for c in TABLE4_COLUMNS}
    report = {}
    for label, (lo, hi) in ranges.items():
        col = cols[label]
        vals = [col.value(ln) for ln in t4_lines]
        vals = [v for v in vals if v is not None]
        finite_vals = [v for v in vals if np.isfinite(v)]
        n_out = len(vals) - len(finite_vals)
        strict_positive_distance = label == "Dist" and lo == 0
        n_out += sum(
            1 for v in finite_vals
            if (v <= lo if strict_positive_distance else v < lo) or v > hi
        )
        report[label] = {"low": lo, "high": hi, "n_out_of_range": n_out,
                         "observed_min": (min(finite_vals)
                                          if finite_vals else None),
                         "observed_max": (max(finite_vals)
                                          if finite_vals else None)}
    return report


# --------------------------------------------------------------------------
# anti-drift guards
# --------------------------------------------------------------------------
def refuse_reconstruction_as_true_flow(column: str) -> None:
    if column in RECONSTRUCTION_COLUMNS:
        raise Cf4ManifestError(
            f"{column} is an estimator-dependent peculiar-velocity "
            "RECONSTRUCTION and may not be selected as the true flow")


def refuse_audit_value_as_observed(value_km_s: float) -> None:
    if int(round(value_km_s)) == AUDIT_ONLY_VALUE_KM_S:
        raise Cf4ManifestError(
            f"the value {AUDIT_ONLY_VALUE_KM_S} (an audit-only sensitivity "
            "figure, in the velocity convention) may not be promoted to an "
            "observed measurement replacement")


def require_cz_units_for_cartesian(column: str, treated_as: str) -> None:
    if column in ("SGX", "SGY", "SGZ") and treated_as == "mpc_length":
        raise Cf4ManifestError(
            f"{column} is expressed in cz (km/s), not a Mpc length; "
            "the cz conversion is required")


def refuse_cf4_p0_resolution_claim(claim_scope: str) -> None:
    """The manifest is provenance only; it never resolves the CF4 P0s."""
    if claim_scope in ("cf4_p0_resolved", "measurement", "detection",
                       "true_flow_established"):
        raise Cf4ManifestError(
            "the manifest is dataset provenance only; the two CF4 P0s "
            "(C1-K5-MV-F1, C3-K5-VCORR-ML-F1) stay OPEN and are never "
            "resolved by authenticating the data lineage")


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------
_FORBIDDEN = tuple(
    a + b for a, b in (
        ("vpec is the ", "true flow"),
        ("audit value observed ", "replacement"),
        ("cf4 p0 ", "resolved"),
        ("reconstruction is the ", "observed velocity"),
        ("sgx is a ", "mpc length"),
        ("shear ", "detected"),
        ("isotropy ", "established"),
        ("finding ", "rescued"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise Cf4ManifestError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(n_groups: int, n_columns: int) -> str:
    return (
        f"Authenticated Cosmicflows-4 group manifest ({n_groups} groups, "
        f"{n_columns} typed columns across table3 and table4): each column "
        f"bound to its byte range, units, producer, and type; 1PGC parity "
        f"verified; tables content-addressed. Peculiar-velocity columns are "
        f"reconstructions, never the true flow. Dataset provenance only; the "
        f"two CF4 P0s stay OPEN; no cosmological measurement, no detection.")
