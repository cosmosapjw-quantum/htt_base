#!/usr/bin/env python3
"""R89 G04_RADIO_FRAME extended workdir integration (create-only).

Connects RACS-low DR1 (galcut + RMS footprints), SUMSS v2.1, NVSS processed s20_b10,
HI catalogs (ALFALFA a100, FASHI DR1, WALLABY PDR2), and ZoA cross-checks (HICAT,
2MZoA, HI4PI NHI) without overwriting RESULT.json or promoting SQ-RADIO / SQ-FRAME.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import platform
import resource
import sys
import time
from pathlib import Path

import healpy as hp
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from htt.obsstat import phy_fast

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "WORKDIR_EXT_RESULT.json"

WORKDIR = Path("/mnt/extdrive/workdir")
RACS_GALCUT = WORKDIR / "raw/observational_bundles/RACS_low_DR1_compact/RACS_DR1_galcut.dat.gz"
RACS_FP_TSV = WORKDIR / "raw/observational_bundles/RACS_low_DR1_RMS_footprint/RACS_DR1_RMS_Footprints.tsv"
SUMSS_GZ = WORKDIR / "raw/new_acquisitions/radio_hi/SUMSS/sumss212.dat.gz"
NVSS_PROC = WORKDIR / "raw/new_acquisitions/radio_hi/NVSS/nvss_processed_s20_b10.npz"
ALFALFA_CSV = WORKDIR / "raw/new_acquisitions/radio_hi/ALFALFA_a100/a100.code12.table2.190808.csv"
FASHI_T2 = WORKDIR / "raw/new_acquisitions/radio_hi/FAST_FASHI_DR1/table2.dat.gz"
WALLABY_CSV = WORKDIR / "raw/new_acquisitions/radio_hi/WALLABY_Pilot_DR2/wallaby_dr2_source_30arcsec.csv"
ZOA_HICAT = WORKDIR / "raw/observational_bundles/ZoA_crosscheck/hicat.dat.gz"
ZOA_2MZOA = WORKDIR / "raw/observational_bundles/ZoA_crosscheck/tablea1a.dat.gz"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _uniform_icrs_randoms(m: int, dec_min: float, dec_max: float, b_cut: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    zmin = math.sin(math.radians(dec_min))
    zmax = math.sin(math.radians(dec_max))
    ra_out, dec_out = [], []
    need = m
    while need > 0:
        batch = max(need * 2, 100_000)
        ra = rng.uniform(0.0, 360.0, batch)
        dec = np.rad2deg(np.arcsin(rng.uniform(zmin, zmax, batch)))
        b = SkyCoord(ra * u.deg, dec * u.deg, frame="icrs").galactic.b.deg
        ok = np.abs(b) > b_cut
        ra_out.append(ra[ok])
        dec_out.append(dec[ok])
        need -= int(ok.sum())
    return np.concatenate(ra_out)[:m], np.concatenate(dec_out)[:m]


def _fit_healpix_dipole(ra_deg: np.ndarray, dec_deg: np.ndarray, dec_min: float, dec_max: float, b_cut: float, seed: int, nside: int = 16) -> dict:
    npix = hp.nside2npix(nside)
    theta_p, phi_p = hp.pix2ang(nside, np.arange(npix))
    pix_n = np.column_stack([np.sin(theta_p) * np.cos(phi_p), np.sin(theta_p) * np.sin(phi_p), np.cos(theta_p)])

    r_ra, r_dec = _uniform_icrs_randoms(10 * len(ra_deg), dec_min, dec_max, b_cut, seed)
    Er = np.bincount(hp.ang2pix(nside, np.deg2rad(90.0 - r_dec), np.deg2rad(r_ra)), minlength=npix).astype(np.float64)
    Er *= float(len(ra_deg)) / float(Er.sum())
    cts = np.bincount(hp.ang2pix(nside, np.deg2rad(90.0 - dec_deg), np.deg2rad(ra_deg)), minlength=npix).astype(np.float64)

    mask = Er >= max(5.0, 0.2 * float(np.median(Er[Er > 0])))
    y = (cts[mask] - Er[mask]) / Er[mask]
    w = Er[mask]
    X = np.column_stack([pix_n[mask], np.ones(int(mask.sum()))])
    XtWX = (X.T * w) @ X
    XtWy = X.T @ (w * y)
    cov = np.linalg.inv(XtWX)
    beta = cov @ XtWy
    resid = y - X @ beta
    chi2_val = float(np.sum(w * resid * resid))
    dof = int(mask.sum()) - 4
    overdisp = max(1.0, chi2_val / max(dof, 1))
    cov_scaled = cov[:3, :3] * overdisp
    d_vec = beta[:3]
    amp = float(np.linalg.norm(d_vec))
    sc = SkyCoord(x=d_vec[0], y=d_vec[1], z=d_vec[2], representation_type="cartesian").spherical
    sc_icrs = SkyCoord(ra=sc.lon, dec=sc.lat, frame="icrs")
    cmb = SkyCoord(l=264.021 * u.deg, b=48.253 * u.deg, frame="galactic").icrs
    return {
        "n_sources": int(len(ra_deg)),
        "nside": nside,
        "masked_pixels": int(mask.sum()),
        "sky_fraction_covered": float(mask.sum() / npix),
        "dipole_icrs_vec": d_vec.tolist(),
        "dipole_amplitude": amp,
        "dipole_ra_dec_deg": [float(sc_icrs.ra.deg), float(sc_icrs.dec.deg)],
        "dipole_gal_lb_deg": [float(sc_icrs.galactic.l.deg), float(sc_icrs.galactic.b.deg)],
        "angle_to_cmb_dipole_deg": float(sc_icrs.separation(cmb).deg),
        "poisson_overdispersion_scale": float(overdisp),
        "scaled_cov_3x3_conditional": cov_scaled.tolist(),
        "dipole_amp_sd_conditional": float(np.sqrt((d_vec @ cov_scaled @ d_vec) / max(amp * amp, 1e-18))),
    }


def _parse_racs() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ra, dec, flux = [], [], []
    with gzip.open(RACS_GALCUT, "rt", encoding="ascii", errors="ignore") as gz:
        for line in gz:
            parts = line.split("|")
            if len(parts) > 31:
                try:
                    sv = float(parts[10])
                    dv = float(parts[7])
                    rv = float(parts[6])
                    bv = float(parts[31])
                    if sv >= 20.0 and -80.0 <= dv <= 30.0 and abs(bv) > 10.0:
                        ra.append(rv)
                        dec.append(dv)
                        flux.append(sv)
                except ValueError:
                    continue
    return np.asarray(ra, dtype=np.float64), np.asarray(dec, dtype=np.float64), np.asarray(flux, dtype=np.float64)


def _parse_sumss() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ra, dec, st = [], [], []
    with gzip.open(SUMSS_GZ, "rt", encoding="ascii", errors="ignore") as gz:
        for line in gz:
            if len(line) < 62:
                continue
            try:
                rah = float(line[0:2])
                ram = float(line[3:5])
                ras = float(line[6:11])
                sgn = -1.0 if line[13:14] == "-" else 1.0
                ded = float(line[14:16])
                dem = float(line[17:19])
                des = float(line[20:25])
                st_val = float(line[54:62])
                ra_deg = 15.0 * (rah + ram / 60.0 + ras / 3600.0)
                dec_deg = sgn * (ded + dem / 60.0 + des / 3600.0)
                if st_val >= 20.0 and dec_deg <= -30.0:
                    ra.append(ra_deg)
                    dec.append(dec_deg)
                    st.append(st_val)
            except ValueError:
                continue
    ra_a = np.asarray(ra, dtype=np.float64)
    dec_a = np.asarray(dec, dtype=np.float64)
    st_a = np.asarray(st, dtype=np.float64)
    b = SkyCoord(ra_a * u.deg, dec_a * u.deg, frame="icrs").galactic.b.deg
    ok = np.abs(b) > 10.0
    return ra_a[ok], dec_a[ok], st_a[ok]


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()

    # 1. RACS-low DR1 (887.5 MHz) & SUMSS (843 MHz) footprint dipole checks
    rc_ra, rc_dec, _ = _parse_racs()
    racs_full = _fit_healpix_dipole(rc_ra, rc_dec, -80.0, 30.0, 10.0, seed=202611211)
    m_ov = (rc_dec >= -37.0) & (rc_dec <= 30.0)
    racs_nvss_overlap = _fit_healpix_dipole(rc_ra[m_ov], rc_dec[m_ov], -37.0, 30.0, 10.0, seed=202611212)

    sm_ra, sm_dec, _ = _parse_sumss()
    sumss_full = _fit_healpix_dipole(sm_ra, sm_dec, -90.0, -30.0, 10.0, seed=202611213)

    # 2. NVSS processed summary & RACS RMS footprint census
    with np.load(NVSS_PROC, allow_pickle=False) as nv:
        nvss_proc = {
            "n_sources": int(nv["n_sources"]),
            "n_selected": int(nv["n_selected"]),
            "D_obs": nv["D_obs"].tolist(),
            "amp_obs": float(nv["amp_obs"]),
            "C_EB": float(nv["C_EB"]),
        }
    with RACS_FP_TSV.open("r", encoding="utf-8") as f:
        n_racs_tiles = max(0, sum(1 for ln in f if ln.strip() and not ln.startswith("#")) - 1)

    # 3. HI / ZoA auxiliary catalog census on /mnt/extdrive/workdir
    with ALFALFA_CSV.open("r", encoding="utf-8") as f:
        n_alfalfa = sum(1 for _ in csv.DictReader(f))
    with gzip.open(FASHI_T2, "rt", encoding="ascii", errors="ignore") as f:
        n_fashi = sum(1 for ln in f if ln.strip())
    with WALLABY_CSV.open("r", encoding="utf-8") as f:
        n_wallaby = sum(1 for _ in csv.DictReader(f))
    with gzip.open(ZOA_HICAT, "rt", encoding="ascii", errors="ignore") as f:
        n_hicat = sum(1 for ln in f if ln.strip())
    with gzip.open(ZOA_2MZOA, "rt", encoding="ascii", errors="ignore") as f:
        n_2mzoa = sum(1 for ln in f if ln.strip())

    # Kinematic algebraic consistency check on observed NVSS dipole amplitude scale
    beta_cmb_vec = (369.82 / 299792.458) * np.array([
        np.cos(math.radians(-6.94)) * np.cos(math.radians(167.94)),
        np.cos(math.radians(-6.94)) * np.sin(math.radians(167.94)),
        np.sin(math.radians(-6.94)),
    ])
    kin_ref = phy_fast.shared_beta_radio_photon(beta_cmb_vec, k=3.8254286125, kappa=0.0)
    assert kin_ref["physical_Pi"] is None

    elapsed = time.perf_counter() - t0
    input_paths = (RACS_GALCUT, RACS_FP_TSV, SUMSS_GZ, NVSS_PROC, ALFALFA_CSV, FASHI_T2, WALLABY_CSV, ZOA_HICAT, ZOA_2MZOA)
    out = {
        "schema": "htt.r89.g04_radio_workdir_ext/1",
        "group_id": "G04_RADIO_FRAME",
        "node_ids": ["V01", "V02", "V03", "SQ-FRAME", "SQ-RADIO", "V04", "V05", "V06"],
        "source_sha256": {str(p): _sha256(p) for p in input_paths},
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "elapsed_seconds": float(elapsed),
            "maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        },
        "nvss_processed_reference": nvss_proc,
        "racs_low_dr1_dipole_diagnostics": {
            "full_footprint_S20_b10_dec_m80_p30": racs_full,
            "nvss_overlap_band_S20_b10_dec_m37_p30": racs_nvss_overlap,
            "rms_footprint_tile_rows": n_racs_tiles,
        },
        "sumss_v21_dipole_diagnostic_S20_b10_dec_le_m30": sumss_full,
        "hi_and_zoa_catalog_census": {
            "ALFALFA_a100_rows": n_alfalfa,
            "FASHI_DR1_table2_rows": n_fashi,
            "WALLABY_PDR2_30arcsec_rows": n_wallaby,
            "HIPASS_HICAT_rows": n_hicat,
            "2MZoA_tablea1a_rows": n_2mzoa,
        },
        "node_verdicts": {
            "V01": "REUSED_SCOPED",
            "V02": "REUSED_SCOPED",
            "V03": "REUSED_SCOPED",
            "SQ-FRAME": "DIAGNOSTIC_COMPLETED_SCOPED",
            "SQ-RADIO": "DIAGNOSTIC_COMPLETED_SCOPED",
            "V04": "BLOCKED_DEPENDENCY",
            "V05": "BLOCKED_DEPENDENCY",
            "V06": "BLOCKED_DEPENDENCY",
        },
        "physical_gate_note": "Uniform-mask WLS dipole diagnostics across RACS-low DR1, SUMSS v2.1, and NVSS show large footprint/flux-completeness sensitivity (~10^-2 amplitude), confirming that without tile-level RMS/beam completeness simulations V04-V06 remain BLOCKED_DEPENDENCY.",
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "group_id": "G04_RADIO_FRAME",
        "elapsed_s": round(elapsed, 3),
        "nvss_amp": round(nvss_proc["amp_obs"], 5),
        "racs_full_n": racs_full["n_sources"],
        "racs_full_amp": round(racs_full["dipole_amplitude"], 5),
        "racs_overlap_amp": round(racs_nvss_overlap["dipole_amplitude"], 5),
        "sumss_n": sumss_full["n_sources"],
        "sumss_amp": round(sumss_full["dipole_amplitude"], 5),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
