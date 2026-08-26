#!/usr/bin/env python3
"""Prepare the locally complete Planck PR3 SMICA-only diagnostic inputs.

Preflight reads directory entries and file metadata only. Numerical preparation
forms exactly 300 released ``CMB_i + noise_i`` rows in ``K_CMB`` before one
frozen low-ell reduction to ``microK_CMB``. It never opens the observed
temperature column.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import sys
from typing import Mapping, NamedTuple, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "htt", ROOT / "htt/src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from obsstat.planck_pr3_operator import ordered_row_id_hash  # noqa: E402

LMIN = 2
LMAX = 5
MISSING_OFFICIAL_FFP10_CMB_REALIZATION = 970
SMICA_EXISTING_NULL_ROWS = 300
SMICA_EXISTING_ROW_IDS = tuple(
    f"FFP10-SMICA-CMBNOISE-{index:05d}"
    for index in range(SMICA_EXISTING_NULL_ROWS)
)
SMICA_EXISTING_INVENTORY_ID = ordered_row_id_hash(SMICA_EXISTING_ROW_IDS)


class PlanckPreparationError(RuntimeError):
    """Raised when Planck source identity or reduction semantics drift."""


class TemperatureMap(NamedTuple):
    values: np.ndarray
    unit: str
    ordering: str
    coordinate_frame: str
    nside: int


class MaskMap(NamedTuple):
    values: np.ndarray
    ordering: str
    coordinate_frame: str
    nside: int


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def raw_input_manifest_identity(payload: Mapping[str, object]) -> str:
    """Return the exact identity of a raw-input manifest excluding its seal."""

    if not isinstance(payload, Mapping):
        raise PlanckPreparationError("raw input manifest must be a mapping")
    projection = dict(payload)
    projection.pop("manifest_sha256", None)
    return "sha256:" + hashlib.sha256(_canonical_bytes(projection)).hexdigest()


def _raw_file_record(path: Path, *, label: str) -> dict[str, object]:
    if (
        not path.is_absolute()
        or path.is_symlink()
        or not path.is_file()
        or path.resolve() != path
        or path.stat().st_size <= 0
    ):
        raise PlanckPreparationError(f"{label} is not an absolute regular file")
    return {
        "path": str(path),
        "filename": path.name,
        "byte_size": path.stat().st_size,
        "sha256": "sha256:" + _file_sha256(path),
    }


def build_raw_input_manifest(
    *,
    cmb_root: Path,
    noise_root: Path,
    observed_smica: Path,
    temperature_mask: Path,
) -> dict[str, object]:
    """Hash-bind the exact raw SMICA observation, mask, and 300 pair slice."""

    pairs = inspect_smica_cmb_noise_inventory(
        cmb_root=cmb_root, noise_root=noise_root
    )
    rows: list[dict[str, object]] = []
    for ordinal, realization_id in enumerate(pairs):
        cmb_path, noise_path = pairs[realization_id]
        rows.append(
            {
                "ordinal": ordinal,
                "realization_id": realization_id,
                "row_id": SMICA_EXISTING_ROW_IDS[ordinal],
                "cmb": _raw_file_record(
                    cmb_path, label=f"SMICA CMB {realization_id:05d}"
                ),
                "noise": _raw_file_record(
                    noise_path, label=f"SMICA noise {realization_id:05d}"
                ),
            }
        )
    payload: dict[str, object] = {
        "schema": "htt.planck_pr3.smica_raw_input_manifest.v1",
        "pipeline_scope": "SMICA_ONLY_EXACT_300_PAIR",
        "release_identity": "Planck PR3 R3.00 plus FFP10 v3",
        "null_semantics": "FFP10_CMB_PLUS_NOISE_PAIRED_BY_ID",
        "observed_smica": _raw_file_record(
            observed_smica, label="observed_smica"
        ),
        "temperature_mask": _raw_file_record(
            temperature_mask, label="temperature_mask"
        ),
        "ordered_row_ids_sha256": SMICA_EXISTING_INVENTORY_ID,
        "pairs": rows,
        "temperature_arrays_decoded": False,
    }
    payload["manifest_sha256"] = raw_input_manifest_identity(payload)
    return payload


def _validate_raw_record(
    row: object, *, label: str, verify_files: bool
) -> None:
    if not isinstance(row, Mapping) or set(row) != {
        "path",
        "filename",
        "byte_size",
        "sha256",
    }:
        raise PlanckPreparationError(f"{label} identity fields drifted")
    path_text = row.get("path")
    filename = row.get("filename")
    byte_size = row.get("byte_size")
    sha256 = row.get("sha256")
    if (
        not isinstance(path_text, str)
        or not isinstance(filename, str)
        or type(byte_size) is not int
        or byte_size <= 0
        or not isinstance(sha256, str)
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", sha256)
    ):
        raise PlanckPreparationError(f"{label} hash or metadata is malformed")
    path = Path(path_text)
    if not path.is_absolute() or path.name != filename:
        raise PlanckPreparationError(f"{label} path identity drifted")
    if verify_files:
        if (
            path.is_symlink()
            or not path.is_file()
            or path.resolve() != path
            or path.stat().st_size != byte_size
            or "sha256:" + _file_sha256(path) != sha256
        ):
            raise PlanckPreparationError(f"{label} hash no longer matches")


def validate_raw_input_manifest(
    payload: Mapping[str, object], *, verify_files: bool
) -> dict[str, object]:
    """Validate exact order/identity and optionally replay every raw digest."""

    if not isinstance(payload, Mapping):
        raise PlanckPreparationError("raw input manifest must be a mapping")
    if (
        payload.get("schema")
        != "htt.planck_pr3.smica_raw_input_manifest.v1"
        or payload.get("pipeline_scope") != "SMICA_ONLY_EXACT_300_PAIR"
        or payload.get("null_semantics")
        != "FFP10_CMB_PLUS_NOISE_PAIRED_BY_ID"
        or payload.get("ordered_row_ids_sha256")
        != SMICA_EXISTING_INVENTORY_ID
        or payload.get("temperature_arrays_decoded") is not False
    ):
        raise PlanckPreparationError("raw input manifest contract drifted")
    stored_identity = payload.get("manifest_sha256")
    if stored_identity != raw_input_manifest_identity(payload):
        raise PlanckPreparationError(
            "observed_smica hash binding or raw manifest identity drifted"
        )
    _validate_raw_record(
        payload.get("observed_smica"),
        label="observed_smica",
        verify_files=verify_files,
    )
    _validate_raw_record(
        payload.get("temperature_mask"),
        label="temperature_mask",
        verify_files=verify_files,
    )
    pairs = payload.get("pairs")
    if not isinstance(pairs, list) or len(pairs) != SMICA_EXISTING_NULL_ROWS:
        raise PlanckPreparationError("raw pair manifest is not exact 300")
    for ordinal, row in enumerate(pairs):
        if (
            not isinstance(row, Mapping)
            or set(row) != {"ordinal", "realization_id", "row_id", "cmb", "noise"}
            or row.get("ordinal") != ordinal
            or row.get("realization_id") != ordinal
            or row.get("row_id") != SMICA_EXISTING_ROW_IDS[ordinal]
        ):
            raise PlanckPreparationError("raw pair identity or order drifted")
        _validate_raw_record(
            row.get("cmb"),
            label=f"SMICA CMB {ordinal:05d}",
            verify_files=verify_files,
        )
        _validate_raw_record(
            row.get("noise"),
            label=f"SMICA noise {ordinal:05d}",
            verify_files=verify_files,
        )
    return dict(payload)


def write_raw_input_manifest(
    *,
    output: Path,
    cmb_root: Path,
    noise_root: Path,
    observed_smica: Path,
    temperature_mask: Path,
) -> dict[str, object]:
    payload = build_raw_input_manifest(
        cmb_root=cmb_root,
        noise_root=noise_root,
        observed_smica=observed_smica,
        temperature_mask=temperature_mask,
    )
    _atomic_json(output, payload)
    return payload


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_bytes(_canonical_bytes(payload) + b"\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_npy(path: Path, value: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("wb") as handle:
            np.save(handle, np.asarray(value), allow_pickle=False)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_npz(path: Path, **values: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("wb") as handle:
            np.savez(handle, **values)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def official_ffp10_cmb_indices() -> tuple[int, ...]:
    """Return official PR3 CMB-MC IDs; row 00970 was not released."""

    return tuple(
        index
        for index in range(1000)
        if index != MISSING_OFFICIAL_FFP10_CMB_REALIZATION
    )


def official_ffp10_smica_noise_indices() -> tuple[int, ...]:
    """Return the complete released SMICA noise-MC index set."""

    return tuple(range(SMICA_EXISTING_NULL_ROWS))


def _inspect_smica_component(root: Path, *, kind: str) -> Mapping[int, Path]:
    if kind not in {"cmb", "noise"}:
        raise PlanckPreparationError("SMICA component kind must be cmb or noise")
    if root.is_symlink() or not root.is_dir() or root.resolve() != root:
        raise PlanckPreparationError(f"SMICA {kind} inventory root is not regular")
    pattern = re.compile(rf"^dx12_v3_smica_{kind}_mc_(\d{{5}})_raw\.fits$")
    rows: dict[int, Path] = {}
    for path in root.iterdir():
        match = pattern.fullmatch(path.name)
        if match is None:
            continue
        index = int(match.group(1))
        if index in rows:
            raise PlanckPreparationError(
                f"SMICA {kind} has duplicate realization {index:05d}"
            )
        if path.is_symlink() or not path.is_file() or path.stat().st_size <= 0:
            raise PlanckPreparationError(
                f"SMICA {kind} realization {index:05d} is not regular"
            )
        rows[index] = path
    required = set(official_ffp10_smica_noise_indices())
    missing = sorted(required - set(rows))
    allowed = required if kind == "noise" else set(official_ffp10_cmb_indices())
    unexpected = sorted(set(rows) - allowed)
    if missing or unexpected:
        details = []
        if missing:
            details.append("missing=" + ",".join(f"{row:05d}" for row in missing))
        if unexpected:
            details.append(
                "unexpected=" + ",".join(f"{row:05d}" for row in unexpected)
            )
        raise PlanckPreparationError(
            f"SMICA {kind} inventory is not the exact released pairing surface: "
            + " ".join(details)
        )
    return {index: rows[index] for index in official_ffp10_smica_noise_indices()}


def inspect_smica_cmb_noise_inventory(
    *, cmb_root: Path, noise_root: Path
) -> Mapping[int, tuple[Path, Path]]:
    """Return exactly 300 SMICA CMB-plus-noise pairs in release order."""

    cmb = _inspect_smica_component(cmb_root, kind="cmb")
    noise = _inspect_smica_component(noise_root, kind="noise")
    if tuple(cmb) != tuple(noise):
        raise PlanckPreparationError("SMICA CMB/noise row order differs")
    return {index: (cmb[index], noise[index]) for index in cmb}


def build_smica_existing_preflight(
    *,
    cmb_root: Path,
    noise_root: Path,
    observed_smica: Path,
    temperature_mask: Path,
) -> dict[str, object]:
    """Inspect the SMICA-only fast path without opening temperature arrays."""

    observed = {
        label: path.is_file() and not path.is_symlink() and path.stat().st_size > 0
        for label, path in (
            ("smica_map", observed_smica),
            ("temperature_mask", temperature_mask),
        )
    }
    try:
        pairs = inspect_smica_cmb_noise_inventory(
            cmb_root=cmb_root, noise_root=noise_root
        )
        inventory_ready = len(pairs) == SMICA_EXISTING_NULL_ROWS
        blocker = None
    except PlanckPreparationError as exc:
        inventory_ready = False
        blocker = str(exc)
    if not all(observed.values()):
        blocker = "SMICA_OBSERVED_SOURCE_INCOMPLETE"
    ready = inventory_ready and all(observed.values())
    return {
        "preflight_mode": "METADATA_ONLY_NO_TEMPERATURE_PAYLOAD_OPEN",
        "pipeline_scope": "SMICA_ONLY",
        "expected_null_rows": SMICA_EXISTING_NULL_ROWS,
        "null_semantics": "FFP10_CMB_PLUS_NOISE_PAIRED_BY_ID",
        "observed_regular_files": observed,
        "observed_temperature_payload_opened": False,
        "ready": ready,
        "blocker": None if ready else blocker,
    }


def reduce_temperature_map(
    values: np.ndarray,
    *,
    source_unit: str,
    source_ordering: str,
    output_nside: int,
) -> np.ndarray:
    """Band-limit a delivered PR3 map and convert K_CMB to microK_CMB."""

    import healpy as hp

    if source_unit != "K_CMB":
        raise PlanckPreparationError("source unit must be exactly K_CMB")
    if source_ordering not in {"RING", "NESTED"}:
        raise PlanckPreparationError("source ordering must be RING or NESTED")
    source = np.asarray(values, dtype=np.float64)
    if source.ndim != 1 or not np.all(np.isfinite(source)):
        raise PlanckPreparationError("temperature map is not a finite vector")
    try:
        source_nside = hp.npix2nside(source.size)
    except ValueError as exc:
        raise PlanckPreparationError("temperature map is not HEALPix") from exc
    if (
        type(output_nside) is not int
        or output_nside < 4
        or output_nside > source_nside
        or not hp.isnsideok(output_nside)
    ):
        raise PlanckPreparationError("output nside is invalid")
    if source_ordering == "NESTED":
        source = hp.reorder(source, n2r=True)
    alm_kcmb = hp.map2alm(source, lmax=LMAX, iter=3, pol=False)
    reduced = hp.alm2map(
        alm_kcmb * 1.0e6,
        nside=output_nside,
        lmax=LMAX,
        pol=False,
    )
    if not np.all(np.isfinite(reduced)):
        raise PlanckPreparationError("band-limited map reduction became nonfinite")
    return np.asarray(reduced, dtype=np.float64)


def read_temperature_fits(
    path: Path,
    *,
    allowed_column_names: Sequence[str],
    declared_coordinate_frame: str,
) -> TemperatureMap:
    """Read one explicitly identified Planck temperature FITS payload."""

    from astropy.io import fits
    import healpy as hp

    if path.is_symlink() or not path.is_file():
        raise PlanckPreparationError("temperature FITS must be a regular file")
    if declared_coordinate_frame != "GALACTIC":
        raise PlanckPreparationError("declared coordinate frame must be GALACTIC")
    try:
        with fits.open(path, memmap=True, lazy_load_hdus=True) as bundle:
            if len(bundle) < 2 or bundle[1].data is None:
                raise PlanckPreparationError("temperature FITS table is missing")
            header = bundle[1].header
            if header.get("PIXTYPE") != "HEALPIX":
                raise PlanckPreparationError("temperature FITS is not HEALPix")
            ordering = header.get("ORDERING")
            column = header.get("TTYPE1")
            unit = header.get("TUNIT1")
            frame = header.get("COORDSYS")
            if ordering not in {"RING", "NESTED"}:
                raise PlanckPreparationError("temperature FITS ORDERING drifted")
            if column not in set(allowed_column_names):
                raise PlanckPreparationError("temperature FITS TTYPE1 drifted")
            if unit != "K_CMB":
                raise PlanckPreparationError("temperature FITS TUNIT1 must be K_CMB")
            if frame not in {None, "GALACTIC"}:
                raise PlanckPreparationError("temperature FITS frame drifted")
            values = np.asarray(bundle[1].data.field(0), dtype=np.float64).reshape(-1)
            declared_nside = header.get("NSIDE")
    except (OSError, ValueError, IndexError) as exc:
        raise PlanckPreparationError("temperature FITS could not be read") from exc
    if not np.all(np.isfinite(values)):
        raise PlanckPreparationError("temperature FITS contains nonfinite values")
    try:
        observed_nside = hp.npix2nside(values.size)
    except ValueError as exc:
        raise PlanckPreparationError("temperature FITS pixel count is invalid") from exc
    if type(declared_nside) is not int or declared_nside != observed_nside:
        raise PlanckPreparationError("temperature FITS NSIDE drifted")
    return TemperatureMap(values, unit, ordering, declared_coordinate_frame, observed_nside)


def read_temperature_beam(path: Path) -> np.ndarray:
    """Read the delivered intensity beam through the frozen analysis band.

    The PR3 SMICA product stores zero placeholders at ell=0 and ell=1.  Those
    modes are removed before the retained ell=2..5 operator, so their transfer
    is frozen to a unit no-op instead of being divided by the release zeros.
    """

    from astropy.io import fits

    try:
        with fits.open(path, memmap=True, lazy_load_hdus=True) as bundle:
            if len(bundle) < 3 or bundle[2].data is None:
                raise PlanckPreparationError("temperature beam extension is missing")
            if bundle[2].header.get("TTYPE1") != "INT_BEAM":
                raise PlanckPreparationError("temperature INT_BEAM identity drifted")
            beam = np.asarray(bundle[2].data.field(0), dtype=np.float64).reshape(-1)
    except (OSError, ValueError, IndexError) as exc:
        raise PlanckPreparationError("temperature beam could not be read") from exc
    selected = beam[: LMAX + 1].copy()
    if selected.size != LMAX + 1 or not np.all(np.isfinite(selected)):
        raise PlanckPreparationError("temperature beam does not cover l=0..5")
    if np.any(selected[LMIN:] <= 0.0):
        raise PlanckPreparationError("temperature beam is not positive in l=2..5")
    selected[:LMIN] = 1.0
    return selected


def read_mask_fits(path: Path) -> MaskMap:
    """Read the exact Planck common temperature-mask FITS payload."""

    from astropy.io import fits
    import healpy as hp

    if path.is_symlink() or not path.is_file():
        raise PlanckPreparationError("mask FITS must be a regular file")
    try:
        with fits.open(path, memmap=True, lazy_load_hdus=True) as bundle:
            if len(bundle) < 2 or bundle[1].data is None:
                raise PlanckPreparationError("mask FITS table is missing")
            header = bundle[1].header
            if (
                header.get("PIXTYPE") != "HEALPIX"
                or header.get("TTYPE1") != "TMASK"
                or header.get("COORDSYS") != "GALACTIC"
            ):
                raise PlanckPreparationError("mask FITS identity drifted")
            ordering = header.get("ORDERING")
            if ordering not in {"RING", "NESTED"}:
                raise PlanckPreparationError("mask FITS ORDERING drifted")
            values = np.asarray(bundle[1].data.field(0), dtype=np.float64).reshape(-1)
            declared_nside = header.get("NSIDE")
    except (OSError, ValueError, IndexError) as exc:
        raise PlanckPreparationError("mask FITS could not be read") from exc
    try:
        observed_nside = hp.npix2nside(values.size)
    except ValueError as exc:
        raise PlanckPreparationError("mask FITS pixel count is invalid") from exc
    if (
        type(declared_nside) is not int
        or declared_nside != observed_nside
        or not np.all(np.isfinite(values))
        or np.any((values < 0.0) | (values > 1.0))
    ):
        raise PlanckPreparationError("mask FITS values or NSIDE drifted")
    return MaskMap(values, ordering, "GALACTIC", observed_nside)


def reduce_mask(mask: MaskMap, *, output_nside: int) -> np.ndarray:
    import healpy as hp

    values = mask.values
    if mask.ordering == "NESTED":
        values = hp.reorder(values, n2r=True)
    reduced = hp.ud_grade(
        values,
        nside_out=output_nside,
        order_in="RING",
        order_out="RING",
        power=0,
        pess=True,
    )
    reduced = np.clip(np.asarray(reduced, dtype=np.float64), 0.0, 1.0)
    if not np.all(np.isfinite(reduced)) or not np.any(reduced > 0.0):
        raise PlanckPreparationError("reduced mask is invalid")
    return reduced


def reduce_smica_cmb_plus_noise(
    *, cmb_path: Path, noise_path: Path, output_nside: int
) -> np.ndarray:
    """Reduce one official SMICA simulation as CMB plus matching noise."""

    cmb = read_temperature_fits(
        cmb_path,
        allowed_column_names=("INTENSITY",),
        declared_coordinate_frame="GALACTIC",
    )
    noise = read_temperature_fits(
        noise_path,
        allowed_column_names=("INTENSITY",),
        declared_coordinate_frame="GALACTIC",
    )
    if (
        cmb.unit != noise.unit
        or cmb.ordering != noise.ordering
        or cmb.coordinate_frame != noise.coordinate_frame
        or cmb.nside != noise.nside
        or cmb.values.shape != noise.values.shape
    ):
        raise PlanckPreparationError("SMICA CMB/noise map metadata differs")
    return reduce_temperature_map(
        cmb.values + noise.values,
        source_unit=cmb.unit,
        source_ordering=cmb.ordering,
        output_nside=output_nside,
    )


def write_smica_operator_metadata(
    *,
    smica_beam_source: Path,
    mask_path: Path,
    output_root: Path,
    output_nside: int = 16,
) -> None:
    """Write single-component beam, pixel-window, and mask inputs."""

    import healpy as hp

    component_dir = output_root / "components"
    beam = read_temperature_beam(smica_beam_source)
    pixel = np.asarray(hp.pixwin(output_nside, lmax=LMAX), dtype=np.float64)
    mask = reduce_mask(read_mask_fits(mask_path), output_nside=output_nside)
    _atomic_npy(component_dir / "smica_mask.npy", mask)
    _atomic_npy(component_dir / "smica_beam.npy", beam)
    _atomic_npz(
        component_dir / "smica_window_operator.npz",
        source_pixel_window=pixel,
        target_beam=beam,
        target_pixel_window=pixel,
    )


def write_smica_existing_null_inventory(
    *,
    cmb_root: Path,
    noise_root: Path,
    output_root: Path,
    output_nside: int = 16,
) -> Path:
    """Build a resumable exact 300-row SMICA CMB-plus-noise bundle."""

    import healpy as hp

    pairs = inspect_smica_cmb_noise_inventory(cmb_root=cmb_root, noise_root=noise_root)
    shape = (SMICA_EXISTING_NULL_ROWS, hp.nside2npix(output_nside))
    output = output_root / "components/smica_ffp10_cmb_plus_noise_300.npz"
    expected_row_ids = tuple(
        f"FFP10-SMICA-CMBNOISE-{index:05d}" for index in pairs
    )
    if output.exists():
        if output.is_symlink() or not output.is_file():
            raise PlanckPreparationError("SMICA compact null output is not regular")
        try:
            with np.load(output, allow_pickle=False) as bundle:
                if set(bundle.files) != {"row_ids", "smica_maps"}:
                    raise PlanckPreparationError("SMICA compact null keys drifted")
                row_ids = tuple(str(value) for value in bundle["row_ids"].tolist())
                maps = np.asarray(bundle["smica_maps"])
                if (
                    row_ids != expected_row_ids
                    or maps.shape != shape
                    or maps.dtype != np.dtype("float64")
                    or not np.all(np.isfinite(maps))
                ):
                    raise PlanckPreparationError(
                        "SMICA compact null identity or values drifted"
                    )
        except (OSError, ValueError) as exc:
            raise PlanckPreparationError("SMICA compact null could not be read") from exc
        return output
    scratch = output_root / ".pr314-smica-null-reduction"
    scratch.mkdir(parents=True, exist_ok=True)
    rows_path = scratch / "smica_maps.npy"
    done_path = scratch / "completed.npy"
    if rows_path.exists():
        rows = np.lib.format.open_memmap(rows_path, mode="r+")
        if rows.shape != shape or rows.dtype != np.dtype("float64"):
            raise PlanckPreparationError("SMICA reduction checkpoint drifted")
    else:
        rows = np.lib.format.open_memmap(
            rows_path, mode="w+", dtype=np.float64, shape=shape
        )
    if done_path.exists():
        completed = np.lib.format.open_memmap(done_path, mode="r+")
        if (
            completed.shape != (SMICA_EXISTING_NULL_ROWS,)
            or completed.dtype != np.dtype("bool")
        ):
            raise PlanckPreparationError("SMICA progress checkpoint drifted")
    else:
        completed = np.lib.format.open_memmap(
            done_path,
            mode="w+",
            dtype=np.bool_,
            shape=(SMICA_EXISTING_NULL_ROWS,),
        )
        completed[:] = False
        completed.flush()
    for ordinal, index in enumerate(pairs):
        if bool(completed[ordinal]):
            continue
        cmb_path, noise_path = pairs[index]
        rows[ordinal] = reduce_smica_cmb_plus_noise(
            cmb_path=cmb_path,
            noise_path=noise_path,
            output_nside=output_nside,
        )
        rows.flush()
        completed[ordinal] = True
        completed.flush()
    if not np.all(completed):
        raise PlanckPreparationError("SMICA null-reduction checkpoint is incomplete")
    row_ids = np.asarray(expected_row_ids, dtype="U27")
    _atomic_npz(output, row_ids=row_ids, smica_maps=np.asarray(rows))
    rows_path.unlink()
    done_path.unlink()
    scratch.rmdir()
    return output


def write_smica_existing_operator_components(
    *,
    output_root: Path,
    observed_smica: Path,
    temperature_mask: Path,
    output_nside: int = 16,
) -> dict[str, object]:
    """Freeze the complete SMICA-only covariance and local execution plan."""

    import healpy as hp
    from obsstat.planck_pr3_operator import COMPONENT_FEATURE_IDS, ordered_row_id_hash
    from scripts.observed_runs import run_planck_pr3 as worker

    component_dir = output_root / "components"
    paths = {
        "mask": component_dir / "smica_mask.npy",
        "beam": component_dir / "smica_beam.npy",
        "window": component_dir / "smica_window_operator.npz",
        "null": component_dir / "smica_ffp10_cmb_plus_noise_300.npz",
        "covariance": component_dir / "smica_covariance.npy",
        "selection": component_dir / "smica_existing_selection.json",
    }
    mask = worker._load_npy(paths["mask"], label="SMICA mask", dimension=1)
    beam = worker._load_npy(paths["beam"], label="SMICA beam", dimension=1)
    window = worker._load_window(paths["window"], label="SMICA window")
    npix = hp.nside2npix(output_nside)
    context = worker.build_smica_operator_context(
        smica_map=np.zeros(npix),
        mask=mask,
        beam=beam,
        window=window,
        declared_nside=output_nside,
    )
    try:
        with np.load(paths["null"], allow_pickle=False) as bundle:
            if set(bundle.files) != {"row_ids", "smica_maps"}:
                raise PlanckPreparationError("SMICA compact null keys drifted")
            row_ids = tuple(str(value) for value in bundle["row_ids"].tolist())
            map_shape = bundle["smica_maps"].shape
    except (OSError, ValueError) as exc:
        raise PlanckPreparationError("SMICA compact null could not be read") from exc
    expected_ids = tuple(
        f"FFP10-SMICA-CMBNOISE-{index:05d}"
        for index in official_ffp10_smica_noise_indices()
    )
    if row_ids != expected_ids or map_shape != (SMICA_EXISTING_NULL_ROWS, npix):
        raise PlanckPreparationError("SMICA compact null identity or shape drifted")
    features = worker._process_ffp10_component(
        paths["null"],
        array_name="smica_maps",
        row_ids=row_ids,
        component="SMICA",
        context=context,
    )
    covariance = np.cov(features, rowvar=False, ddof=1)
    try:
        validation = worker._smica_covariance_diagnostics(covariance)
    except worker.PlanckWorkerError as exc:
        raise PlanckPreparationError(str(exc)) from exc
    _atomic_npy(paths["covariance"], covariance)
    inventory_identity = ordered_row_id_hash(row_ids)
    _atomic_json(
        paths["selection"],
        {
            "pipeline_scope": "SMICA_ONLY",
            "release": "Planck PR3 R3.00 and FFP10 v3",
            "lmin": 2,
            "lmax": LMAX,
            "nside": output_nside,
            "ordering": "RING",
            "map_unit": "microK_CMB",
            "coordinate_frame": "GALACTIC",
            "beam_outside_analysis_band": "ELL_0_1_UNIT_NOOP_AFTER_REMOVAL",
            "covariance_condition_basis": "DIAGONAL_STANDARDIZED",
            "feature_ids": list(COMPONENT_FEATURE_IDS),
            "expected_null_rows": SMICA_EXISTING_NULL_ROWS,
            "null_semantics": "FFP10_CMB_PLUS_NOISE_PAIRED_BY_ID",
            "ordered_row_ids_sha256": inventory_identity,
            "commander_robustness": "NOT_EVALUATED",
        },
    )
    components = {
        name: {
            "path": str(path.resolve()),
            "byte_size": path.stat().st_size,
            "sha256": "sha256:" + _file_sha256(path),
        }
        for name, path in paths.items()
    }
    plan = {
        "format": "PLANCK_PR3_SMICA_EXISTING_PLAN_V1",
        "pipeline_scope": "SMICA_ONLY",
        "release_identity": "Planck PR3 R3.00 plus FFP10 v3",
        "observed_smica": {
            "path": str(observed_smica.resolve()),
            "filename": observed_smica.name,
            "byte_size": observed_smica.stat().st_size,
            "temperature_column": "I_STOKES",
            "native_unit": "K_CMB",
        },
        "temperature_mask_source": {
            "path": str(temperature_mask.resolve()),
            "filename": temperature_mask.name,
            "byte_size": temperature_mask.stat().st_size,
        },
        "components": components,
        "ordered_row_ids_sha256": inventory_identity,
        "beam_outside_analysis_band": "ELL_0_1_UNIT_NOOP_AFTER_REMOVAL",
        "covariance_condition_basis": "DIAGONAL_STANDARDIZED",
        "observed_temperature_payload_opened": False,
        "observed_statistic_seen": False,
        "commander_robustness": "NOT_EVALUATED",
        "joint_covariance": "NOT_APPLICABLE_SMICA_ONLY",
    }
    plan_path = output_root / "smica_existing_plan.json"
    _atomic_json(plan_path, plan)
    return {
        "plan_path": str(plan_path),
        "null_rows": SMICA_EXISTING_NULL_ROWS,
        "null_ordered_row_ids_sha256": inventory_identity,
        "covariance_rank": int(validation["rank"]),
        "covariance_condition": float(validation["standardized_condition"]),
        "covariance_raw_condition": float(validation["raw_condition"]),
    }


def prepare_smica_existing_products(
    *,
    output_root: Path,
    cmb_root: Path,
    noise_root: Path,
    observed_smica: Path,
    temperature_mask: Path,
    output_nside: int = 16,
) -> dict[str, object]:
    """Prepare the exact locally complete SMICA-only analysis surface."""

    if not output_root.is_absolute() or output_root.is_symlink():
        raise PlanckPreparationError("SMICA output root must be absolute and regular")
    preflight = build_smica_existing_preflight(
        cmb_root=cmb_root,
        noise_root=noise_root,
        observed_smica=observed_smica,
        temperature_mask=temperature_mask,
    )
    if preflight["ready"] is not True:
        raise PlanckPreparationError(
            "SMICA source preflight blocked: " + str(preflight["blocker"])
        )
    output_root.mkdir(parents=True, exist_ok=True)
    write_smica_operator_metadata(
        smica_beam_source=observed_smica,
        mask_path=temperature_mask,
        output_root=output_root,
        output_nside=output_nside,
    )
    write_smica_existing_null_inventory(
        cmb_root=cmb_root,
        noise_root=noise_root,
        output_root=output_root,
        output_nside=output_nside,
    )
    operator = write_smica_existing_operator_components(
        output_root=output_root,
        observed_smica=observed_smica,
        temperature_mask=temperature_mask,
        output_nside=output_nside,
    )
    return {
        "preflight": preflight,
        "operator": operator,
        **operator,
        "pipeline_scope": "SMICA_ONLY",
        "observed_temperature_payload_opened": False,
        "observed_statistic_seen": False,
        "observed_science_executed": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight-smica-existing", action="store_true")
    mode.add_argument("--prepare-smica-existing", action="store_true")
    mode.add_argument("--write-raw-manifest", action="store_true")
    parser.add_argument("--smica-cmb-root", type=Path, required=True)
    parser.add_argument("--smica-noise-root", type=Path, required=True)
    parser.add_argument("--observed-smica", type=Path, required=True)
    parser.add_argument("--temperature-mask", type=Path, required=True)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--raw-manifest-output", type=Path)
    parser.add_argument("--output-nside", type=int, default=16)
    args = parser.parse_args(argv)
    if args.write_raw_manifest:
        if args.raw_manifest_output is None:
            parser.error("--write-raw-manifest requires --raw-manifest-output")
        try:
            payload = write_raw_input_manifest(
                output=args.raw_manifest_output,
                cmb_root=args.smica_cmb_root,
                noise_root=args.smica_noise_root,
                observed_smica=args.observed_smica,
                temperature_mask=args.temperature_mask,
            )
        except PlanckPreparationError as exc:
            print(json.dumps({"ready": False, "blocker": str(exc)}, sort_keys=True))
            return 3
    elif args.prepare_smica_existing:
        if args.output_root is None:
            parser.error("--prepare-smica-existing requires --output-root")
        try:
            payload = prepare_smica_existing_products(
                output_root=args.output_root,
                cmb_root=args.smica_cmb_root,
                noise_root=args.smica_noise_root,
                observed_smica=args.observed_smica,
                temperature_mask=args.temperature_mask,
                output_nside=args.output_nside,
            )
        except PlanckPreparationError as exc:
            print(
                json.dumps(
                    {
                        "ready": False,
                        "blocker": str(exc),
                        "observed_temperature_payload_opened": False,
                        "observed_statistic_seen": False,
                    },
                    sort_keys=True,
                )
            )
            return 3
    else:
        payload = build_smica_existing_preflight(
            cmb_root=args.smica_cmb_root,
            noise_root=args.smica_noise_root,
            observed_smica=args.observed_smica,
            temperature_mask=args.temperature_mask,
        )
    print(json.dumps(payload, sort_keys=True, allow_nan=False))
    return 0 if payload.get("ready", True) else 3


if __name__ == "__main__":
    raise SystemExit(main())
