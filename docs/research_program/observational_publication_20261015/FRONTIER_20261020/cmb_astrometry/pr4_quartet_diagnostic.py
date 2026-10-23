"""Describe one released NPIPE quartet at matched HEALPix pixel positions.

This is a C0 source/data diagnostic. It does not form a total sky, a null
ensemble, or a likelihood, and it does not modify downloaded FITS files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import healpy as hp
import numpy as np
from astropy.io import fits


NAMES = {
    "cmb_A": "npipe6v20_cmb_030_A_mc_00200.fits",
    "cmb_B": "npipe6v20_cmb_030_B_mc_00200.fits",
    "residual_A": "npipe6v20_noise_030_A_mc_00200.fits",
    "residual_B": "npipe6v20_noise_030_B_mc_00200.fits",
}
COMPONENTS = ("TEMPERATURE", "Q_POLARISATION", "U_POLARISATION")
NSIDE = 1024
NPIX = hp.nside2npix(NSIDE)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sample(path: Path, expected_ordering: str, expected_prefix_sha256: str, ring_indices: np.ndarray) -> dict:
    with path.open("rb") as stream:
        prefix_sha256 = hashlib.sha256(stream.read(11_520)).hexdigest()
    if prefix_sha256 != expected_prefix_sha256:
        raise ValueError(f"{path.name}: complete file disagrees with prior public FITS prefix")
    with fits.open(path, memmap=True, checksum=False) as hdus:
        if len(hdus) != 2 or not isinstance(hdus[1], fits.BinTableHDU):
            raise ValueError(f"{path.name}: expected one BINTABLE and no extra HDUs")
        header = hdus[1].header
        if (header.get("NSIDE"), header.get("ORDERING"), header.get("FIRSTPIX"), header.get("LASTPIX")) != (NSIDE, expected_ordering, 0, NPIX - 1):
            raise ValueError(f"{path.name}: HEALPix geometry or ordering mismatch")
        if tuple(hdus[1].columns.names) != COMPONENTS:
            raise ValueError(f"{path.name}: T/Q/U schema mismatch")
        pixel_indices = hp.ring2nest(NSIDE, ring_indices) if expected_ordering == "NESTED" else ring_indices
        if expected_ordering == "NESTED" and not np.array_equal(hp.nest2ring(NSIDE, pixel_indices), ring_indices):
            raise ValueError("HEALPix index round trip failed")
        values = {}
        for name in COMPONENTS:
            column = np.asarray(hdus[1].data[name]).reshape(-1)
            if column.size != NPIX:
                raise ValueError(f"{path.name}: pixel count mismatch")
            selected = np.asarray(column[pixel_indices], dtype=np.float64)
            values[name] = selected
        metadata = {
            "bytes": path.stat().st_size,
            "sha256": digest(path),
            "prefix_sha256": prefix_sha256,
            "ordering": expected_ordering,
            "coordsys_header": header.get("COORDSYS"),
            "tunit_header": [header.get(f"TUNIT{i}") for i in range(1, 4)],
            "nside": NSIDE,
            "npix": NPIX,
        }
    return {"metadata": metadata, "values": values}


def summary(a: np.ndarray, b: np.ndarray) -> dict:
    valid = np.isfinite(a) & np.isfinite(b) & (np.abs(a) < 1e20) & (np.abs(b) < 1e20)
    count = int(np.count_nonzero(valid))
    if count < 2:
        raise ValueError("Fewer than two jointly valid sampled pixels")
    a, b = a[valid], b[valid]
    return {
        "joint_valid_pixels": count,
        "excluded_pixels": int(valid.size - count),
        "A_mean": float(a.mean()),
        "B_mean": float(b.mean()),
        "A_std": float(a.std()),
        "B_std": float(b.std()),
        "A_B_pearson": float(np.corrcoef(a, b)[0, 1]),
        "difference_rms": float(np.sqrt(np.mean(np.square(a - b)))),
    }


def full_pair_difference(path_a: Path, path_b: Path) -> dict:
    """Count unequal stored float32 pixels without combining sky components."""
    out = {}
    with fits.open(path_a, memmap=True) as left, fits.open(path_b, memmap=True) as right:
        for name in COMPONENTS:
            a = np.asarray(left[1].data[name]).reshape(-1)
            b = np.asarray(right[1].data[name]).reshape(-1)
            unequal = 0
            finite_pair = 0
            max_abs = 0.0
            for start in range(0, NPIX, 1_048_576):
                x = a[start:start + 1_048_576]
                y = b[start:start + 1_048_576]
                unequal += int(np.count_nonzero(x.view(np.uint32) != y.view(np.uint32)))
                valid = np.isfinite(x) & np.isfinite(y) & (np.abs(x) < 1e20) & (np.abs(y) < 1e20)
                finite_pair += int(np.count_nonzero(valid))
                if np.any(valid):
                    max_abs = max(max_abs, float(np.max(np.abs(x[valid].astype(np.float64) - y[valid].astype(np.float64)))))
            out[name] = {"unequal_float32_bit_patterns": unequal, "joint_valid_pixels": finite_pair, "max_abs_difference_on_joint_valid": max_abs}
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("/mnt/extdrive/workdir/htt_open_data"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample-count", type=int, default=100_000)
    args = parser.parse_args()
    if not 2 <= args.sample_count <= NPIX:
        parser.error("sample-count must be between 2 and NPIX")
    quartet = args.data_root / "frontier20261020/planck/quartet"
    candidate = json.loads(Path(__file__).with_name("minimal_acquisition_candidate.json").read_text())
    prefix_hashes = {item["product_id"]: item["prefix_sha256"] for item in candidate["products"]}
    ring_indices = np.linspace(0, NPIX - 1, args.sample_count, dtype=np.int64)
    if len(np.unique(ring_indices)) != args.sample_count:
        raise ValueError("Selected ring pixels are not unique")
    data = {
        key: sample(quartet / name, "NESTED" if key.startswith("cmb") else "RING", prefix_hashes[name], ring_indices)
        for key, name in NAMES.items()
    }
    out = {
        "schema": "htt.npipe_pr4_quartet_diagnostic/1",
        "scope": "C0_DIAGNOSTIC_ONLY_ONE_REALIZATION_NO_FOREGROUND_OR_COVERAGE",
        "realization": "00200",
        "frequency_GHz": 30,
        "sample_count": args.sample_count,
        "sample_selection": "uniformly spaced RING pixel indices; CMB NESTED indices obtained with healpy.ring2nest",
        "unit_binding": "K_CMB release-wide source inference; simulation TUNIT headers absent",
        "frame_binding": "Galactic/COSMO source-supported inference; exact cache-to-PLA packaging unverified",
        "products": {key: value["metadata"] for key, value in data.items()},
        "split_descriptives": {
            group: {
                component: summary(data[f"{group}_A"]["values"][component], data[f"{group}_B"]["values"][component])
                for component in COMPONENTS
            }
            for group in ("cmb", "residual")
        },
        "full_pair_difference": {
            group: full_pair_difference(quartet / NAMES[f"{group}_A"], quartet / NAMES[f"{group}_B"])
            for group in ("cmb", "residual")
        },
        "interpretation_limit": "Descriptive values at one shared-sky realization. No independent-sky count, foreground uncertainty law, observed-map match, mask, beam closure, or statistic-specific coverage.",
    }
    args.output.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output), "sample_count": args.sample_count, "products": len(data)}))


if __name__ == "__main__":
    main()
