"""One-sky PR4 observed A/B low-ell morphology pilot.

The two maps are temporal splits of one observed sky. This code never uses the
simulation residual as a total map and never estimates a processed-null p value.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import sys
import time
from pathlib import Path

import healpy as hp
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
VALIDATION = REPO / "docs/research_program/observational_publication_20261015/RESEARCH_LOOP_20261022/data/pr4/VALIDATION.json"
FEATURE_SOURCE = REPO / "docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/cmb_counterpairs/morphology.py"
EXTERNAL = Path("/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual")
PACKET = "902ebd6a521d6b31864e0bfce63336c62d6cec5ff2f6c3128de7ab68046fce35"
INPUT = "sha256:83ebf1cd2ce7ae18a486506219c0a93ec939a74cfa06c21a1316c938678f1c43"
NSIDE = 1024
MASK_NSIDE = 16
LMAX = 4
EXPECTED = {
    "PR4_LFI30_OBS_YEAR13": "7dc8414835f5041ad51373505e15a17f3fb286fac1f41a48e72f09f46aa901b0",
    "PR4_LFI30_OBS_YEAR24": "b7de3e4fbafb2553db26d2c24b5d91f68dd42b86135e989c25d095a63e611c8f",
    "PR4_LOLLIPOP_NS16_MASK": "7d7df63e77066a7739cc7faed3a005593bb3612af6cdeea2ed48a37fb600946d",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def available_bytes() -> int:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    raise RuntimeError("MemAvailable unavailable")


def source_entries() -> tuple[dict, dict[str, dict]]:
    report = json.loads(VALIDATION.read_text())
    if report.get("qualification") != "TRANSPORT_SCHEMA_PIXEL_ONLY":
        raise ValueError("unexpected prior intake scope")
    entries = {item["id"]: item for item in report["resources"]}
    if set(entries) != set(EXPECTED):
        raise ValueError("observed A/B/mask source list changed")
    for key, item in entries.items():
        path = Path(item["path"])
        if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"] or item["sha256"] != EXPECTED[key]:
            raise ValueError(f"immutable source identity mismatch: {key}")
    return report, entries


def exact_native_mask(mask_path: Path) -> tuple[np.ndarray, dict]:
    with fits.open(mask_path, memmap=True) as hdus:
        h = hdus[1].header
        if (h["NSIDE"], h["ORDERING"], h["COORDSYS"], h["PIXTYPE"]) != (MASK_NSIDE, "RING", "G", "HEALPIX"):
            raise ValueError("mask geometry changed")
        ring = np.asarray(hdus[1].data["T"]).reshape(-1)
        if ring.shape != (hp.nside2npix(MASK_NSIDE),) or not np.all((ring == 0) | (ring == 1)):
            raise ValueError("mask is not the pinned binary NS16 support")
        nested = ring[hp.nest2ring(MASK_NSIDE, np.arange(ring.size))].astype(bool)
    if int(nested.sum()) != 1273:
        raise ValueError("mask selected-parent count changed")
    child_count = (NSIDE // MASK_NSIDE) ** 2
    native_nested = np.repeat(nested, child_count)
    ring_to_nested = hp.ring2nest(NSIDE, np.arange(hp.nside2npix(NSIDE), dtype=np.int64))
    native_ring = native_nested[ring_to_nested]
    if int(native_ring.sum()) != 5_214_208:
        raise ValueError("lifted selected-pixel count changed")
    return native_ring, {"coarse_ordering": "RING", "native_map_ordering": "NESTED",
                         "operator_ordering": "RING", "coarse_nside": MASK_NSIDE,
                         "native_nside": NSIDE, "selected_coarse_pixels": int(nested.sum()),
                         "selected_native_pixels": int(native_ring.sum()),
                         "same_mask_for_all_views": True,
                         "rule": "mask_NESTED16=mask_RING16[nest2ring16]; repeat each parent 4096 times in NESTED1024; index by ring2nest1024"}, ring_to_nested


def load_mask() -> tuple[np.ndarray, dict, np.ndarray]:
    report, entries = source_entries()
    mask, meta, index = exact_native_mask(Path(entries["PR4_LOLLIPOP_NS16_MASK"]["path"]))
    meta["validation_sha256"] = sha256(VALIDATION)
    return mask, meta, index


def alm_for_map(path: Path, mask_ring: np.ndarray, ring_to_nested: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    with fits.open(path, memmap=True) as hdus:
        hdu = hdus[1]
        h = hdu.header
        if (h["NSIDE"], h["ORDERING"], h["COORDSYS"], h["POLCCONV"], h["PIXTYPE"]) != (NSIDE, "NESTED", "G", "COSMO", "HEALPIX"):
            raise ValueError(f"observed map geometry/frame changed: {path.name}")
        if tuple(hdu.columns.names[:3]) != ("I_STOKES", "Q_STOKES", "U_STOKES"):
            raise ValueError("observed I/Q/U field order changed")
        if (h["TUNIT2"], h["TUNIT3"]) != ("K_CMB", "K_CMB"):
            raise ValueError("observed Q/U units changed")
        fields = []
        for name in ("Q_STOKES", "U_STOKES"):
            nested = np.asarray(hdu.data[name]).reshape(-1)
            if nested.size != hp.nside2npix(NSIDE):
                raise ValueError("observed field pixel count changed")
            ring = np.asarray(nested[ring_to_nested], dtype=np.float64)
            if not np.isfinite(ring).all() or np.any(np.abs(ring) >= 1e20):
                raise ValueError("nonfinite or sentinel observed Q/U")
            ring *= mask_ring
            fields.append(ring)
        e, b = hp.map2alm_spin(fields, spin=2, lmax=LMAX, mmax=LMAX)
    if e.shape != (hp.Alm.getsize(LMAX),) or b.shape != e.shape or not np.isfinite(e).all() or not np.isfinite(b).all():
        raise ValueError("invalid spin-2 output")
    return e, b, {"map_name": path.name, "frame": "Galactic", "polconv": "COSMO",
                  "units": "K_CMB", "input_ordering": "NESTED", "analysis_ordering": "RING"}


def dense_e(alm: np.ndarray) -> dict[tuple[int, int], complex]:
    result = {}
    for ell in (2, 3, 4):
        for m in range(ell + 1):
            value = complex(alm[hp.Alm.getidx(LMAX, ell, m)])
            result[ell, m] = value
            if m:
                result[ell, -m] = (-1) ** m * value.conjugate()
    return result


def run() -> dict:
    before = time.monotonic()
    report, entries = source_entries()
    mask_ring, mask_meta, ring_to_nested = load_mask()
    spec = importlib.util.spec_from_file_location("r36_pr4_existing_morphology", FEATURE_SOURCE)
    if spec is None or spec.loader is None:
        raise ImportError("existing morphology feature source cannot load")
    donor = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = donor
    spec.loader.exec_module(donor)
    alms = {}
    input_meta = {}
    for key, label in (("PR4_LFI30_OBS_YEAR13", "A"), ("PR4_LFI30_OBS_YEAR24", "B")):
        e, b, meta = alm_for_map(Path(entries[key]["path"]), mask_ring, ring_to_nested)
        alms[f"{label}_E"] = e
        alms[f"{label}_B"] = b
        input_meta[label] = meta
    alms["C_E"] = (alms["A_E"] + alms["B_E"]) / 2
    alms["C_B"] = (alms["A_B"] + alms["B_B"]) / 2
    features = {label: donor.features(dense_e(alms[f"{label}_E"])) for label in ("A", "B", "C")}
    scan = {label: abs(features[label]["J234"]) for label in ("A", "B", "C")}
    winner = max(("A", "B", "C"), key=lambda label: scan[label])
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    npz_path = EXTERNAL / "observed_lowell_alms.npz"
    np.savez_compressed(npz_path, **alms)
    result = {
        "schema": "htt.r36_pr4_observed_morphology_pilot/1", "packet_id": PACKET,
        "task_id": "R36-06-PR4-MORPHOLOGY", "input_identity": INPUT,
        "owner": "obsstat", "claim_tier": "C0_DIAGNOSTIC_ONLY",
        "status": "OBSERVED_ONE_SKY_PILOT_PENDING_PROCESSED_NULL",
        "transfer_source": "none; no Bianchi transfer or beam inversion",
        "observed_quantity": "PR4 30 GHz Q/U E-pseudoalm from A/B time splits; synthetic coefficient coadd C",
        "physical_target": "processed low-ell morphology compatibility; no family or sky-origin inference",
        "source_validation": {"path": str(VALIDATION), "sha256": sha256(VALIDATION),
                              "resources": [{"id": k, "path": v["path"], "sha256": v["sha256"], "bytes": v["bytes"], "url": v["url"]} for k, v in entries.items()]},
        "operator": {"input_frame": "Galactic", "polarization": "COSMO", "input_units": "K_CMB",
                     "spin": 2, "lmax": LMAX, "method": "healpy.map2alm_spin on masked native-resolution Q/U",
                     "map2alm_spin_defaults": "mmax=lmax; no extra smoothing or beam inversion",
                     "mask": mask_meta, "split_roles": "A=years1,3; B=years2,4,start5 per NPIPE source; one observed sky",
                     "coadd_C": "(E_A+E_B)/2 and (B_A+B_B)/2; synthetic coefficient coadd, not released FULL"},
        "input_metadata": input_meta,
        "feature_source": {"path": str(FEATURE_SOURCE), "sha256": sha256(FEATURE_SOURCE),
                           "reused_function": "features only"},
        "lowell_alms": {"path": str(npz_path), "sha256": sha256(npz_path), "bytes": npz_path.stat().st_size,
                          "contents": "all l<=4 complex E/B alm for A,B,C; full tensor carrier retained"},
        "features": features,
        "single_within_sky_scan": {"formula": "T=max(|J234_A|,|J234_B|,|J234_C|)",
                                   "T": scan[winner], "winner": winner,
                                   "abs_J234_by_view": scan, "independent_sky_count": 1},
        "ideal_U_law": "3 sqrt(3)|z1 z2 z3| for z uniform on S6, independent isotropic Gaussian STF3 conditional on simple STF2; separate mathematical reference only",
        "processed_null_rank": None, "processed_null_p": None,
        "null_mock_status": "MISSING_SOURCE_QUALIFIED_PROCESSED_TOTAL_ENSEMBLE_AND_MATCHED_OBSERVATION_OPERATOR",
        "sky_support_status": "one observed PR4 sky; A/B/C share it",
        "caveats": ["Mask was released for LoLLiPoP spectra, not calibrated for this morphology statistic.",
                    "No beam/pixel-window inversion or deprojection; A/B response may differ.",
                    "No foreground subtraction, adaptive weight fitting, simulation null rank or p-value.",
                    "The cached CMB and noise-labeled maps are symmetric-beam reference and post-regression residual products, not an established processed total map.",
                    "Original PR3 L03 and original 42-node acceptance remain unchanged."],
        "execution": {"python": platform.python_version(), "executable": sys.executable,
                      "numpy": np.__version__, "healpy": hp.__version__, "astropy": fits.__version__ if hasattr(fits, "__version__") else "see environment",
                      "mem_available_after_bytes": available_bytes(),
                      "elapsed_seconds": time.monotonic() - before,
                      "command": ".venv/bin/python -B pr4_observed_pilot.py"},
    }
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    labels = ("A", "B", "C")
    ax.bar(labels, [features[x]["J234"] for x in labels], color="#3b6f93")
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set(ylabel="signed normalized J234", title="One observed PR4 sky")
    bx.bar(labels, [features[x]["alignment23_squared"] for x in labels], color="#9f703a")
    bx.set(ylabel="quadrupole/octupole axis alignment squared", ylim=(0, 1),
           title="Descriptive shape companion")
    fig.suptitle("30 GHz A/B and synthetic coefficient coadd; no processed-null rank")
    fig.savefig(HERE / "MORPHOLOGY.png", dpi=180)
    fig.savefig(HERE / "MORPHOLOGY.pdf")
    plt.close(fig)
    return result


if __name__ == "__main__":
    outcome = run()
    print(json.dumps({"status": outcome["status"], "T": outcome["single_within_sky_scan"]["T"],
                      "winner": outcome["single_within_sky_scan"]["winner"]}))
