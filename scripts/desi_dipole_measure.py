#!/usr/bin/env python3
"""EXT-DESI measurement: the window-corrected DESI DR1 BGS number-count dipole.

Binds the real DESI DR1 BGS_ANY data (compact npz) and the DESI random
catalogues (BGS_ANY_{NGC,SGC}_0_clustering.ran.fits) and computes the
selection-function-deconvolved overdensity dipole:

    delta_pix = (D_pix - alpha * R_pix) / (alpha * R_pix),   alpha = sum w_D / sum w_R

per cap (NGC, SGC combined over their disjoint footprints), then the linear
number-count dipole estimator D = 3 * <delta n_hat>_R over the footprint. The
randoms encode the angular + radial selection, so this removes the survey
window that dominated the raw footprint value.

Model-independent kinematic descriptor. Diagnostic-only: the BGS sample is
low-z (z < 0.5), so the measured dipole MIXES the local large-scale-structure
(clustering) dipole with the kinematic dipole and is NOT a clean kinematic
signal; and at fsky ~ 0.19-0.35 the partial-sky mask couples multipoles, so
the amplitude and its significance require release-matched mock calibration
(a further exit gate). No anisotropy, geometry, family, or inference claim.

Outputs docs/generated/desi_dipole_card.json. Deterministic; --check.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/generated/desi_dipole_card.json"
COMPACT = REPO / "workdir/compact_products/desi"
RAW = REPO / "workdir/raw/desi"
CMB_DIPOLE_LB = (264.021, 48.253)          # Planck 2018 Galactic
CMB_KINEMATIC_NUMBER_COUNT_DIPOLE = 7.0e-3
NSIDE = 64


def _round(x, n=6):
    return round(float(x), n)


def _load_cap(cap: str):
    import healpy as hp
    from astropy.io import fits
    npz = COMPACT / f"BGS_ANY_{cap}_clustering_extended.npz"
    ran = RAW / f"BGS_ANY_{cap}_0_clustering.ran.fits"
    if not npz.exists() or not ran.exists():
        return None
    d = np.load(npz)
    dnh = d["n_hat"].astype(np.float64)
    dw = d["weight"].astype(np.float64)
    with fits.open(ran) as f:
        t = f[1].data
        ra = np.asarray(t["RA"], np.float64)
        dec = np.asarray(t["DEC"], np.float64)
        rw = np.asarray(t["WEIGHT"], np.float64)
    rnh = hp.ang2vec(ra, dec, lonlat=True)
    npix = hp.nside2npix(NSIDE)
    Dp = np.bincount(hp.vec2pix(NSIDE, *dnh.T), weights=dw, minlength=npix)
    Rp = np.bincount(hp.vec2pix(NSIDE, *rnh.T), weights=rw, minlength=npix)
    alpha = dw.sum() / rw.sum()
    return {"Dp": Dp, "Rp": Rp, "alpha": float(alpha),
            "n_data": int(len(dw)), "n_random": int(len(rw))}


def measure() -> dict:
    import healpy as hp
    npix = hp.nside2npix(NSIDE)
    vec = np.asarray(hp.pix2vec(NSIDE, np.arange(npix)))   # (3, npix)
    num = np.zeros(3)
    den = 0.0
    occ = np.zeros(npix, dtype=bool)
    caps = {}
    for cap in ("NGC", "SGC"):
        c = _load_cap(cap)
        if c is None:
            continue
        mask = c["Rp"] > 0
        delta = np.zeros(npix)
        delta[mask] = (c["Dp"][mask] - c["alpha"] * c["Rp"][mask]) \
            / (c["alpha"] * c["Rp"][mask])
        w = c["Rp"] * delta
        num += (w[mask][None, :] * vec[:, mask]).sum(axis=1)
        den += c["Rp"][mask].sum()
        occ |= mask
        caps[cap] = {"n_data": c["n_data"], "n_random": c["n_random"],
                     "alpha": _round(c["alpha"]),
                     "fsky": _round(mask.sum() / npix, 4)}
    if not caps:
        return {"schema": "htt.desi_dipole_card.v1",
                "status": "BLOCKED_MISSING_DESI_RANDOMS",
                "detail": "no cap has both compact npz and random on disk"}
    dvec = 3.0 * num / den
    amp = float(np.linalg.norm(dvec))
    u = dvec / amp
    lb = hp.vec2ang(np.asarray([u]), lonlat=True)
    cmb = hp.ang2vec(*CMB_DIPOLE_LB, lonlat=True)
    sep = float(np.degrees(np.arccos(np.clip(u @ cmb, -1, 1))))
    return {
        "schema": "htt.desi_dipole_card.v1",
        "status": "MEASURED_WINDOW_CORRECTED",
        "sample": "DESI DR1 BGS_ANY (" + "+".join(caps) + ")",
        "estimator": "window-corrected overdensity dipole "
                     "D = 3 <delta n_hat>_R, delta = (D - alpha R)/(alpha R)",
        "nside": NSIDE,
        "caps": caps,
        "combined_fsky": _round(occ.sum() / npix, 4),
        "dipole_amplitude": _round(amp),
        "dipole_direction_l_b_deg": [_round(float(lb[0][0]), 3),
                                     _round(float(lb[1][0]), 3)],
        "separation_from_cmb_dipole_deg": _round(sep, 3),
        "cmb_kinematic_number_count_dipole_ref": CMB_KINEMATIC_NUMBER_COUNT_DIPOLE,
        "raw_footprint_dipole_before_randoms": 2.129222,
        "window_suppression_factor": _round(2.129222 / amp, 1),
        "caveats": [
            "BGS is low-z (z<0.5): the measured dipole mixes the local "
            "large-scale-structure (clustering) dipole with the kinematic "
            "dipole; it is NOT a clean kinematic signal",
            "partial-sky mask (fsky~0.2-0.35) couples multipoles: the "
            "amplitude and its significance require release-matched mock "
            "calibration (further exit gate)",
            "single random per cap; radial selection removed via the random "
            "z-distribution",
        ],
        "scope_not_claimed": "model-independent kinematic descriptor; "
                             "diagnostic-only; no anisotropy, geometry, "
                             "family, or inference claim",
    }


def _render(p: dict) -> str:
    return json.dumps(p, indent=2, sort_keys=True, default=str) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    card = measure()
    rendered = _render(card)
    if args.check:
        if not OUT.exists() or OUT.read_text() != rendered:
            print("STALE desi_dipole_card.json", file=sys.stderr)
            return 1
        print("desi dipole card current")
        return 0
    OUT.write_text(rendered)
    print(f"wrote {OUT} status={card['status']} "
          f"D={card.get('dipole_amplitude')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
