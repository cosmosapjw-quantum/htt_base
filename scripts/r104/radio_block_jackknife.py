"""Real-data clustering check for the NVSS integrated-minus-peak same-catalogue contrast.

Selects the provider catalogue (SHA-pinned) at 20 mJy with the peak and the integrated
flux, applies |b|>10 deg and dec>-40 deg, and forms the linear vector-sum dipole
D_S = 3 sum_i n_i / N_S for each selection. The contrast D_int - D_peak is compared
under (a) the independent-source Poisson influence covariance and (b) a delete-one
HEALPix block jackknife (spatial blocks keep LSS clustering, multiplicity and survey
systematics). The ratio estimates the covariance inflation of the R65 Poisson Wald.
Units: dipole components dimensionless (ICRS x,y,z).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import healpy as hp
import numpy as np
import pandas as pd
from scipy import stats

RAW = Path("/mnt/extdrive/workdir/raw/new_acquisitions/radio_hi/RACS_SBI_20261117/Full_NVSS_combined_named.dat")
SHA = "52eb576c1e3e71837f2fca26121789ccc0b316152cca3f25ea2f37ea8ef5a38e"
R65_WALD = {"dipole": 32.792386268354115, "dipole_stf": 30.989468960483375}


def analyze(block_nside=4, threshold=20.0):
    raw = RAW.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA:
        raise ValueError("NVSS provider catalogue SHA mismatch")
    t = pd.read_csv(RAW, sep=r"\s+", quotechar='"')
    ra, dec = t.ra.to_numpy(float), t.dec.to_numpy(float)
    peak, total = t.peak_flux.to_numpy(float), t.integrated_flux.to_numpy(float)
    ok = np.isfinite(ra) & np.isfinite(dec) & (peak > 0) & (total > 0) & (dec > -40.0)
    lon, lat = hp.Rotator(coord=["C", "G"])(ra, dec, lonlat=True)
    ok &= np.abs(lat) > 10.0
    n = hp.ang2vec(ra[ok], dec[ok], lonlat=True)
    sel = {"peak": peak[ok] >= threshold, "integrated": total[ok] >= threshold}
    block = hp.ang2pix(block_nside, ra[ok], dec[ok], lonlat=True)

    def contrast(mask):
        d = {k: 3.0 * n[s & mask].sum(axis=0) / (s & mask).sum() for k, s in sel.items()}
        return d["integrated"] - d["peak"], d

    full, dips = contrast(np.ones(len(n), bool))
    infl = np.zeros_like(n)
    for sign, (k, s) in zip((-1.0, 1.0), sel.items()):
        infl[s] += sign * 3.0 * (n[s] - dips[k] / 3.0) / s.sum()
    pois = infl.T @ infl
    blocks = np.unique(block[sel["peak"] | sel["integrated"]])
    reps = np.array([contrast(block != b)[0] for b in blocks])
    k = len(reps)
    jk = (k - 1) / k * (reps - reps.mean(0)).T @ (reps - reps.mean(0))
    ratio_xy = float(np.trace(jk[:2, :2]) / np.trace(pois[:2, :2]))
    eig = np.linalg.eigvals(np.linalg.solve(pois[:2, :2], jk[:2, :2])).real
    wald_pois = float(full[:2] @ np.linalg.solve(pois[:2, :2], full[:2]))
    wald_jk = float(full[:2] @ np.linalg.solve(jk[:2, :2], full[:2]))
    inflated = {m: {"r65_poisson_wald": w, "divided_by_trace_ratio": w / ratio_xy,
                    "tail_df2": float(stats.chi2.sf(w / ratio_xy, 2))} for m, w in R65_WALD.items()}
    return {"schema": "htt.r104.radio_block_jackknife/1", "catalogue_sha256": SHA,
            "cuts": {"threshold_mJy": threshold, "abs_b_deg_gt": 10.0, "dec_deg_gt": -40.0, "block_nside": block_nside},
            "n_peak": int(sel["peak"].sum()), "n_integrated": int(sel["integrated"].sum()),
            "n_shared": int((sel["peak"] & sel["integrated"]).sum()), "n_blocks": k,
            "linear_contrast_icrs_xyz": full.tolist(), "poisson_cov": pois.tolist(), "jackknife_cov": jk.tolist(),
            "jk_over_poisson_trace_ratio_xy": ratio_xy, "jk_over_poisson_generalized_eigs_xy": sorted(eig.tolist()),
            "linear_wald_xy_poisson": wald_pois, "linear_wald_xy_jackknife": wald_jk,
            "linear_tail_xy_jackknife": float(stats.chi2.sf(wald_jk, 2)),
            "r65_wald_inflated_by_jk_ratio": inflated, "physical_LSS_calibrated": False, "physical_Pi": None,
            "scope": "Simple vector-sum estimator, not the R65 common-transverse fit; jackknife blocks share one sky "
                     "realization. The ratio is an empirical inflation estimate, not a calibrated LSS covariance."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--block-nside", type=int, default=4)
    a = p.parse_args()
    a.output.write_text(json.dumps(analyze(a.block_nside), indent=1, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
