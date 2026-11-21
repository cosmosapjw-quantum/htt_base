#!/usr/bin/env python3
"""R89 G03_GAIA Phase-3 deep scanning-law, ecliptic-band, and VLBA VSH analysis (create-only).

Combines FullGaiaMissionScanningLaw (~17M ECSV rows streamed via zip+gzip),
full Gaia CRF3 1,614,173-source astrometry across ecliptic/Galactic/scan-hit splits
using `pre_dag_fast.accumulate_gaia`, and VLBA 233_3 extragalactic proper motions.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import math
import os
import platform
import resource
import sys
import time
import zipfile
from pathlib import Path

import healpy as hp
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from htt.obsstat import phy_fast, pre_dag_fast
from scripts.r68.fiveview_geometry import stf_matrix
from scripts.r69.gaia_e2_b2 import fit_case, prepare, templates

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "DEEP_SCANLAW_VLBA_RESULT.json"

WORKDIR = Path("/mnt/extdrive/workdir")
SCANLAW_ZIP = WORKDIR / "raw/gaia_scanning_law_20261110/FullGaiaMissionScanningLaw.zip"
SCANLAW_MEMBER = "FullGaiaMissionScanningLaw/commanded_scan_law.csv.gz"
GAIA_FULL_FITS = WORKDIR / "raw/observational_bundles/Gaia_CRF3_astrometry/gaia_crf3_astrometry_full.fits"
VLBA_T6 = WORKDIR / "htt_open_data/vlba/233_3/table6.dat"

NSIDE_SCAN = 32
NPIX_SCAN = hp.nside2npix(NSIDE_SCAN)
THREADS = int(os.environ.get("OMP_NUM_THREADS", "4"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _accumulate_from_arrays(
    ra_deg: np.ndarray,
    dec_deg: np.ndarray,
    pmra: np.ndarray,
    pmdec: np.ndarray,
    e1: np.ndarray,
    e2: np.ndarray,
    rho: np.ndarray,
) -> dict:
    n_tot = len(ra_deg)
    F = np.zeros((16, 16), dtype=np.float64)
    score = np.zeros(16, dtype=np.float64)
    chisq = 0.0
    chunk = 65536
    for i in range(0, n_tot, chunk):
        j = min(i + chunk, n_tot)
        _, B = templates(np.deg2rad(ra_deg[i:j]), np.deg2rad(dec_deg[i:j]))
        yy = np.column_stack([pmra[i:j], pmdec[i:j]])
        FF, sc, c2 = pre_dag_fast.accumulate_gaia(B, yy, e1[i:j], e2[i:j], rho[i:j], threads=THREADS)
        F += FF
        score += sc
        chisq += c2
    return {"F": F, "score": score, "chisq": chisq, "N": n_tot}


def _finalize_vsh(acc: dict) -> dict:
    fit = fit_case(acc)
    cov = np.asarray(fit["formal_cov_microasyr2"], dtype=np.float64)
    alias = phy_fast.gaia_eb_mask_alias(cov)
    beta = np.asarray(fit["coefs_microasyr"], dtype=np.float64)
    return {
        "n_sources": fit["n_sources"],
        "rank": fit["rank"],
        "F_condition": fit["F_condition"],
        "coefs_microasyr": fit["coefs_microasyr"],
        "formal_errors_microasyr": fit["formal_errors_microasyr"],
        "groups_amplitude_microasyr": fit["groups_amplitude_microasyr"],
        "E1_amp_microasyr": fit["groups_amplitude_microasyr"]["E1"],
        "B1_amp_microasyr": fit["groups_amplitude_microasyr"]["B1"],
        "E2_amp_microasyr": fit["groups_amplitude_microasyr"]["E2"],
        "B2_amp_microasyr": fit["groups_amplitude_microasyr"]["B2"],
        "E2_shape_chi": fit["E2_shape_chi"],
        "chi2_per_dof_working": fit["chi2_per_dof_working"],
        "nominal_within_fixed_Gaussian": fit["nominal_within_fixed_Gaussian"],
        "E2_B2_mask_alias_maxcanonical": float(alias["maxcanonical"]),
        "last_chunk_backend_receipt": pre_dag_fast.last_backend_receipt(),
        "_beta_e2": beta[6:11].tolist(),
        "_cov_16": cov.tolist(),
    }


def _wald_diff(a: dict, b: dict, label_a: str, label_b: str, *, relation: str = "disjoint") -> dict:
    ba = np.asarray(a["coefs_microasyr"], dtype=np.float64)
    bb = np.asarray(b["coefs_microasyr"], dtype=np.float64)
    ca = np.asarray(a["_cov_16"], dtype=np.float64)
    cb = np.asarray(b["_cov_16"], dtype=np.float64)
    delta = ba - bb
    if relation == "b_subset_of_a":
        # Exact Hausman difference covariance when subset b is nested inside a: Var(beta_b - beta_a) = C_b - C_a
        cdiff = cb - ca
        cov_note = "C_sub - C_all (Hausman nested-subset difference)"
    elif relation == "a_subset_of_b":
        cdiff = ca - cb
        cov_note = "C_sub - C_all (Hausman nested-subset difference)"
    else:
        cdiff = ca + cb
        cov_note = "C_a + C_b (disjoint subsets)"
    out = {}
    for name, sl in [("all_16D", slice(0, 16)), ("E1_3D", slice(0, 3)), ("B1_3D", slice(3, 6)), ("E2_5D", slice(6, 11)), ("B2_5D", slice(11, 16))]:
        d = delta[sl]
        c = 0.5 * (cdiff[sl, sl] + cdiff[sl, sl].T)
        if np.linalg.eigvalsh(c).min() <= 0.0:
            raise ValueError(f"Non-PD contrast covariance for {label_a} vs {label_b} ({name}, relation={relation})")
        w = float(d @ np.linalg.solve(c, d))
        out[name] = {
            "delta_norm_microasyr": float(np.linalg.norm(d)),
            "formal_wald_chi2": w,
            "dof": len(d),
            "formal_p_not_calibrated": float(chi2.sf(w, len(d))),
        }
    return {
        "subset_a": label_a,
        "subset_b": label_b,
        "relation": relation,
        "cov_formula": cov_note,
        "n_a": a["n_sources"],
        "n_b": b["n_sources"],
        "contrasts": out,
    }


def _process_scanning_law() -> tuple[dict, np.ndarray, np.ndarray]:
    hits = np.zeros(NPIX_SCAN, dtype=np.float64)
    c2_sum = np.zeros(NPIX_SCAN, dtype=np.float64)
    s2_sum = np.zeros(NPIX_SCAN, dtype=np.float64)
    total_rows = 0

    with zipfile.ZipFile(SCANLAW_ZIP, "r") as zf:
        zinfo = zf.getinfo(SCANLAW_MEMBER)
        member_size = int(zinfo.file_size)
        with zf.open(SCANLAW_MEMBER, "r") as raw_f:
            with gzip.GzipFile(fileobj=raw_f) as gz:
                try:
                    import pandas as pd  # faster C CSV engine

                    reader = pd.read_csv(
                        gz,
                        comment="#",
                        usecols=["ra_fov1", "dec_fov1", "scan_angle_fov1", "ra_fov2", "dec_fov2", "scan_angle_fov2"],
                        chunksize=500000,
                        dtype=np.float64,
                    )
                    for df in reader:
                        total_rows += len(df)
                        for suff in ("fov1", "fov2"):
                            ra = df[f"ra_{suff}"].to_numpy()
                            dec = df[f"dec_{suff}"].to_numpy()
                            psi = np.deg2rad(df[f"scan_angle_{suff}"].to_numpy())
                            theta = np.deg2rad(90.0 - dec)
                            phi = np.deg2rad(ra)
                            pix = hp.ang2pix(NSIDE_SCAN, theta, phi)
                            np.add.at(hits, pix, 1.0)
                            np.add.at(c2_sum, pix, np.cos(2.0 * psi))
                            np.add.at(s2_sum, pix, np.sin(2.0 * psi))
                except ImportError:
                    txt = io.TextIOWrapper(gz, encoding="utf-8")
                    hdr = None
                    for ln in txt:
                        if not ln or ln[0] == "#":
                            continue
                        hdr = ln.strip().split(",")
                        break
                    if hdr is None:
                        raise RuntimeError("Missing ECSV CSV header in scan law")
                    idx_cols = [hdr.index(k) for k in ("ra_fov1", "dec_fov1", "scan_angle_fov1", "ra_fov2", "dec_fov2", "scan_angle_fov2")]
                    buf_ra, buf_dec, buf_psi = [], [], []
                    for ln in txt:
                        parts = ln.split(",")
                        if len(parts) <= max(idx_cols):
                            continue
                        total_rows += 1
                        buf_ra.append(float(parts[idx_cols[0]])); buf_dec.append(float(parts[idx_cols[1]])); buf_psi.append(float(parts[idx_cols[2]]))
                        buf_ra.append(float(parts[idx_cols[3]])); buf_dec.append(float(parts[idx_cols[4]])); buf_psi.append(float(parts[idx_cols[5]]))
                        if len(buf_ra) >= 500000:
                            pix = hp.ang2pix(NSIDE_SCAN, np.deg2rad(90.0 - np.array(buf_dec)), np.deg2rad(np.array(buf_ra)))
                            p2 = 2.0 * np.deg2rad(np.array(buf_psi))
                            np.add.at(hits, pix, 1.0); np.add.at(c2_sum, pix, np.cos(p2)); np.add.at(s2_sum, pix, np.sin(p2))
                            buf_ra.clear(); buf_dec.clear(); buf_psi.clear()
                    if buf_ra:
                        pix = hp.ang2pix(NSIDE_SCAN, np.deg2rad(90.0 - np.array(buf_dec)), np.deg2rad(np.array(buf_ra)))
                        p2 = 2.0 * np.deg2rad(np.array(buf_psi))
                        np.add.at(hits, pix, 1.0); np.add.at(c2_sum, pix, np.cos(p2)); np.add.at(s2_sum, pix, np.sin(p2))

    mean_hits = float(np.mean(hits))
    delta_n = (hits / max(mean_hits, 1.0)) - 1.0
    q_scan = np.divide(c2_sum, np.maximum(hits, 1.0))
    u_scan_iau = np.divide(s2_sum, np.maximum(hits, 1.0))
    # FullGaiaMissionScanningLaw defines scan_angle in IAU convention (N through E);
    # healpy defaults to COSMO polarization where U_COSMO = -U_IAU.
    u_scan_cosmo = -u_scan_iau

    alms = hp.map2alm([delta_n, q_scan, u_scan_cosmo], lmax=8, pol=True)
    cl_t = hp.alm2cl(alms[0])
    cl_e = hp.alm2cl(alms[1])
    cl_b = hp.alm2cl(alms[2])

    # Ecliptic latitude profile of NSIDE=32 hit density
    th_p, ph_p = hp.pix2ang(NSIDE_SCAN, np.arange(NPIX_SCAN))
    sc_pix = SkyCoord(ra=np.rad2deg(ph_p) * u.deg, dec=(90.0 - np.rad2deg(th_p)) * u.deg, frame="icrs")
    abs_beta = np.abs(sc_pix.barycentricmeanecliptic.lat.deg)
    ecl_profile = {}
    for lo, hi in [(0, 20), (20, 40), (40, 50), (50, 70), (70, 91)]:
        m = (abs_beta >= lo) & (abs_beta < hi)
        ecl_profile[f"abs_beta_{lo}_{hi}"] = {
            "n_pix": int(np.count_nonzero(m)),
            "mean_hits": float(np.mean(hits[m])),
            "mean_rel_density": float(np.mean(hits[m] / mean_hits)),
            "mean_pol_amp": float(np.mean(np.hypot(q_scan[m], u_scan_cosmo[m]))),
        }

    # Quadrupole STF projection of delta_n for orientation comparison
    pix_n = np.column_stack([np.sin(th_p) * np.cos(ph_p), np.sin(th_p) * np.sin(ph_p), np.cos(th_p)])
    from docs.research_program.observational_publication_20261015.H03_20261016.src.h03_tomography import STF
    stf_feat = np.einsum("ni,aij,nj->na", pix_n, STF, pix_n, optimize=True)
    # Orthogonal projection onto NSIDE=32 pixels
    q_scan_5 = (15.0 / (2.0 * len(pix_n))) * (stf_feat.T @ delta_n)

    summary = {
        "scanlaw_zip_sha256": _sha256(SCANLAW_ZIP),
        "member_uncompressed_bytes": member_size,
        "n_time_rows": total_rows,
        "nside": NSIDE_SCAN,
        "fov_visits_total": int(np.sum(hits)),
        "stokes_u_convention": "IAU_scan_angle_negated_to_HEALPix_COSMO",
        "hits_per_pixel": {
            "min": float(np.min(hits)),
            "median": float(np.median(hits)),
            "mean": mean_hits,
            "max": float(np.max(hits)),
        },
        "low_ell_cl_ell_1_to_6": {
            "C_ell_density_contrast": [float(cl_t[l]) for l in range(1, 7)],
            "C_ell_scan_angle_E": [float(cl_e[l]) for l in range(1, 7)],
            "C_ell_scan_angle_B": [float(cl_b[l]) for l in range(1, 7)],
        },
        "ecliptic_caustic_profile": ecl_profile,
        "delta_n_quad_stf5": q_scan_5.tolist(),
    }
    return summary, hits, q_scan_5


def _analyze_gaia_slices(hits_scan: np.ndarray, q_scan_5: np.ndarray) -> dict:
    # Pre-pass to determine median scan hits across quality QSOs
    subset_names = [
        "quality_all",
        "ecl_abs_lt_20",
        "ecl_abs_20_to_45",
        "ecl_abs_ge_45",
        "gal_abs_b_ge_20",
        "scan_hits_low_half",
        "scan_hits_high_half",
    ]
    # Collect hit distribution first in chunked streaming pass
    hit_samples = []
    with fits.open(GAIA_FULL_FITS, memmap=True) as hd:
        tab = hd[1].data
        n_rows = len(tab)
        chunk = 150000
        for i in range(0, n_rows, chunk):
            z = tab[i : i + chunk]
            ra_r, dec_r, y1, y2, e1, e2, rho, valid, qual = prepare(z)
            solved = np.asarray(z["astrometric_params_solved"], dtype=np.int64)
            keep = valid & qual & (solved == 31) & (np.abs(y1) < 100.0) & (np.abs(y2) < 100.0)
            if not np.any(keep):
                continue
            pix = hp.ang2pix(NSIDE_SCAN, 0.5 * np.pi - dec_r[keep], ra_r[keep])
            hit_samples.append(hits_scan[pix])
    med_hits = float(np.median(np.concatenate(hit_samples)))

    accum = {k: {"F": np.zeros((16, 16)), "score": np.zeros(16), "chisq": 0.0, "N": 0} for k in subset_names}
    with fits.open(GAIA_FULL_FITS, memmap=True) as hd:
        tab = hd[1].data
        n_rows = len(tab)
        chunk = 100000
        for i in range(0, n_rows, chunk):
            z = tab[i : i + chunk]
            ra_r, dec_r, y1, y2, e1, e2, rho, valid, qual = prepare(z)
            solved = np.asarray(z["astrometric_params_solved"], dtype=np.int64)
            keep = valid & qual & (solved == 31) & (np.abs(y1) < 100.0) & (np.abs(y2) < 100.0)
            if not np.any(keep):
                continue
            ra_k = ra_r[keep]; dec_k = dec_r[keep]
            sc = SkyCoord(ra=ra_k * u.rad, dec=dec_k * u.rad, frame="icrs")
            abs_beta = np.abs(sc.barycentricmeanecliptic.lat.deg)
            abs_galb = np.abs(sc.galactic.b.deg)
            pix = hp.ang2pix(NSIDE_SCAN, 0.5 * np.pi - dec_k, ra_k)
            h_src = hits_scan[pix]

            _, B = templates(ra_k, dec_k)
            yy = np.column_stack([y1[keep], y2[keep]])
            e1k, e2k, rhok = e1[keep], e2[keep], rho[keep]

            masks = {
                "quality_all": np.ones(len(ra_k), dtype=bool),
                "ecl_abs_lt_20": abs_beta < 20.0,
                "ecl_abs_20_to_45": (abs_beta >= 20.0) & (abs_beta < 45.0),
                "ecl_abs_ge_45": abs_beta >= 45.0,
                "gal_abs_b_ge_20": abs_galb >= 20.0,
                "scan_hits_low_half": h_src < med_hits,
                "scan_hits_high_half": h_src >= med_hits,
            }
            for k, m in masks.items():
                if not np.any(m):
                    continue
                FF, sc_v, c2 = pre_dag_fast.accumulate_gaia(B[m], yy[m], e1k[m], e2k[m], rhok[m], threads=THREADS)
                accum[k]["F"] += FF
                accum[k]["score"] += sc_v
                accum[k]["chisq"] += c2
                accum[k]["N"] += int(np.count_nonzero(m))

    fits_out = {k: _finalize_vsh(accum[k]) for k in subset_names}
    # Quadrupole STF cosine with scanning-law density quadrupole
    q_scan_norm = np.linalg.norm(q_scan_5)
    for k, res in fits_out.items():
        qe2 = np.asarray(res["_beta_e2"], dtype=np.float64)
        denom = np.linalg.norm(qe2) * q_scan_norm
        res["E2_cosine_with_scanlaw_delta_n_quad"] = float(np.dot(qe2, q_scan_5) / denom) if denom > 0 else 0.0

    contrasts = {
        "ecl_low_vs_high": _wald_diff(fits_out["ecl_abs_lt_20"], fits_out["ecl_abs_ge_45"], "ecl_abs_lt_20", "ecl_abs_ge_45", relation="disjoint"),
        "scan_low_half_vs_high_half": _wald_diff(fits_out["scan_hits_low_half"], fits_out["scan_hits_high_half"], "scan_hits_low_half", "scan_hits_high_half", relation="disjoint"),
        "quality_all_vs_gal_b20": _wald_diff(fits_out["quality_all"], fits_out["gal_abs_b_ge_20"], "quality_all", "gal_abs_b_ge_20", relation="b_subset_of_a"),
    }
    for v in fits_out.values():
        v.pop("_cov_16", None)
        v.pop("_beta_e2", None)

    return {
        "gaia_full_fits_sha256": _sha256(GAIA_FULL_FITS),
        "n_fits_rows": int(n_rows),
        "median_scan_hits_quality_all": med_hits,
        "subsets": fits_out,
        "nominal_contrasts": contrasts,
    }


def _analyze_vlba() -> dict:
    ra_l, dec_l, pmra_l, pmdec_l, epmra_l, epmdec_l, ora_l, odec_l = [], [], [], [], [], [], [], []
    with VLBA_T6.open("r", encoding="ascii", errors="ignore") as f:
        for ln in f:
            if not ln.strip():
                continue
            try:
                rah, ram, ras = float(ln[9:11]), float(ln[12:14]), float(ln[15:24])
                # ReadMe 1-based bytes 33 (DE-), 34-35 (DEd), 37-38 (DEm), 40-48 (DEs)
                sign = -1.0 if ln[32] == "-" else 1.0
                ded, dem, des = float(ln[33:35]), float(ln[36:38]), float(ln[39:48])
                pmra = float(ln[56:64]) * 1e-3  # uas/yr -> mas/yr
                epmra = float(ln[65:72]) * 1e-3
                ora = int(ln[73:77])
                pmdec = float(ln[84:91]) * 1e-3
                epmdec = float(ln[92:99]) * 1e-3
                odec = int(ln[100:104])
            except (ValueError, IndexError):
                continue
            if not (epmra > 0 and epmdec > 0 and math.isfinite(pmra) and math.isfinite(pmdec)):
                continue
            ra_l.append(15.0 * (rah + ram / 60.0 + ras / 3600.0))
            dec_l.append(sign * (ded + dem / 60.0 + des / 3600.0))
            pmra_l.append(pmra); pmdec_l.append(pmdec)
            epmra_l.append(epmra); epmdec_l.append(epmdec)
            ora_l.append(ora); odec_l.append(odec)

    ra = np.array(ra_l); dec = np.array(dec_l)
    if len(dec) == 0 or np.min(dec) >= -40.0 or np.max(dec) <= 60.0 or np.min(dec) < -90.0 or np.max(dec) > 90.0:
        raise ValueError(f"VLBA Dec sky span sanity check failed: min={np.min(dec):.2f}, max={np.max(dec):.2f}")
    pmra = np.array(pmra_l); pmdec = np.array(pmdec_l)
    e1 = np.array(epmra_l); e2 = np.array(epmdec_l)
    ora = np.array(ora_l); odec = np.array(odec_l)
    rho = np.zeros_like(ra)

    zmax = np.maximum(np.abs(pmra) / e1, np.abs(pmdec) / e2)
    subsets = {
        "all_valid": np.ones(len(ra), dtype=bool),
        "obs_ge_10": (ora >= 10) & (odec >= 10),
        "err_lt_100uas": (e1 < 0.1) & (e2 < 0.1),
        "clean_5sigma": zmax < 5.0,
        "clean_5sigma_obs_ge_10": (zmax < 5.0) & (ora >= 10) & (odec >= 10),
    }
    out = {}
    for k, m in subsets.items():
        acc = _accumulate_from_arrays(ra[m], dec[m], pmra[m], pmdec[m], e1[m], e2[m], rho[m])
        res = _finalize_vsh(acc)
        res.pop("_cov_16", None)
        res.pop("_beta_e2", None)
        out[k] = res
    return {"vlba_table6_sha256": _sha256(VLBA_T6), "n_parsed": int(len(ra)), "subsets": out}


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()

    scan_summary, hits_scan, q_scan_5 = _process_scanning_law()
    gaia_res = _analyze_gaia_slices(hits_scan, q_scan_5)
    vlba_res = _analyze_vlba()

    dt = time.perf_counter() - t0
    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    payload = {
        "artifact_id": "R89_G03_GAIA_DEEP_SCANLAW_VLBA_V1",
        "group_id": "G03_GAIA",
        "create_only": True,
        "sq_gaia_status": "DIAGNOSTIC_COMPLETED_SCOPED",
        "runtime_sec": round(dt, 3),
        "max_rss_mb": round(rss_mb, 2),
        "platform": platform.platform(),
        "env": {
            "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
            "OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS"),
        },
        "gaia_scanning_law": scan_summary,
        "gaia_crf3_slices": gaia_res,
        "vlba_233_3_vsh": vlba_res,
        "claim_hygiene": {
            "physical_Pi": None,
            "physical_GF": None,
            "bianchi_family_identified": False,
            "statement": (
                "Source-conditioned Gaia scanning-law, ecliptic/Galactic/hit-density VSH slices and "
                "VLBA optical/radio reference-frame tangent diagnostics within fixed astrometric errors only; "
                "not a calibrated cosmological normal-shear detection."
            ),
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSON} in {dt:.2f}s (max RSS {rss_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
