#!/usr/bin/env python3
"""EXT-ACT measurement: the low-multipole ACT DR6 CMB-lensing kappa isotropy
cross-check, mean-field-debiased against the 400-sim ensemble.

The ACT DR6 lensing reconstruction is undefined at ell = 0, 1 (the convergence
monopole and dipole are not measurable -- degenerate with the reconstruction
mean field), so the lowest available multipole is the quadrupole (ell = 2). This
lane forms the reconstruction mean field MF = <kappa_alm_sim> over the 400
baseline simulations, subtracts it from the data and from each sim, and compares
the low-multipole band power of the debiased data to the sim (isotropic) null:

    S = sum_{ell=2..N} sum_m |a_{ell m}|^2   (mean-field-debiased)

The p-value is the fraction of sims with S_sim >= S_data. An independent-
instrument (ACT, not Planck) isotropy cross-check of the Planck-based K1 lane.

Model-independent; diagnostic-only. No anisotropy, geometry, family, or
inference claim; the kappa low-multipole band is reconstruction-noise-dominated,
so consistency with the isotropic sims is the expected, null result.

Outputs docs/generated/act_kappa_card.json. Deterministic (fixed sims + data);
--check. Heavy: streams the 400 sim alms (run standalone, not in the gate).
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/generated/act_kappa_card.json"
ACT = REPO / "workdir/raw/act_dr6_lensing/dr6_lensing_release/maps/baseline"
DATA_ALM = ACT / "kappa_alm_data_act_dr6_lensing_v1_baseline.fits"
SIMS_DIR = Path(os.environ.get(
    "ACT_SIMS_DIR", "/mnt/sn850x2t/htt_base_e2e/act_dr6_lensing_sims"))
ELL_MIN, ELL_MAX = 2, 10          # low-multipole isotropy band (dipole absent)
N_SIMS = 400
ACT_BASELINE_FSKY = 0.23388


def _load_alm(path):
    from astropy.io import fits
    with fits.open(path) as f:
        t = f[1].data
        return (np.asarray(t["real"], np.float64)
                + 1j * np.asarray(t["imag"], np.float64))


def _lowl_indices(lmax):
    import healpy as hp
    idx, ells = [], []
    for l in range(ELL_MIN, ELL_MAX + 1):
        for m in range(l + 1):
            idx.append(hp.Alm.getidx(lmax, l, m))
            ells.append(l)
    return np.array(idx), np.array(ells)


def measure() -> dict:
    import healpy as hp
    if not DATA_ALM.exists():
        return {"schema": "htt.act_kappa_card.v1",
                "status": "BLOCKED_MISSING_ACT_KAPPA"}
    sims = sorted(SIMS_DIR.glob("kappa_alm_sim_*_baseline_*.fits"))
    if len(sims) < N_SIMS:
        return {"schema": "htt.act_kappa_card.v1",
                "status": "BLOCKED_MISSING_ACT_LENSING_SIMS",
                "detail": f"{len(sims)}/{N_SIMS} sims present in {SIMS_DIR}"}

    data = _load_alm(DATA_ALM)
    lmax = int(hp.Alm.getlmax(len(data)))
    idx, ells = _lowl_indices(lmax)
    # per-index m (for the m>0 double-count in real-field power)
    ms = np.array([hp.Alm.getlm(lmax, i)[1] for i in idx])
    wm = np.where(ms == 0, 1.0, 2.0)

    data_low = data[idx]
    sim_low = np.empty((len(sims), len(idx)), dtype=np.complex128)
    for k, p in enumerate(sims):
        sim_low[k] = _load_alm(p)[idx]
    mf = sim_low.mean(axis=0)                      # reconstruction mean field

    def band_stat(a):
        return float(np.sum(wm * np.abs(a - mf) ** 2))

    S_data = band_stat(data_low)
    S_sim = np.array([band_stat(sim_low[k]) for k in range(len(sims))])
    p_value = float((S_sim >= S_data).mean())

    # per-multipole debiased band power C_l = (1/(2l+1)) sum_m |a_lm|^2
    def cl_of(a):
        d = a - mf
        out = {}
        for l in range(ELL_MIN, ELL_MAX + 1):
            sel = ells == l
            out[l] = float(np.sum(wm[sel] * np.abs(d[sel]) ** 2) / (2 * l + 1))
        return out
    cl_data = cl_of(data_low)
    cl_sim_mean = {l: float(np.mean([cl_of(sim_low[k])[l]
                                     for k in range(len(sims))]))
                   for l in range(ELL_MIN, ELL_MAX + 1)}

    return {
        "schema": "htt.act_kappa_card.v1",
        "status": "MEASURED_MEAN_FIELD_DEBIASED",
        "product": "ACT DR6 baseline kappa (data + 400 recon sims)",
        "n_sims": len(sims),
        "ell_band": [ELL_MIN, ELL_MAX],
        "dipole_note": "ell=0,1 not reconstructed (NaN); lowest available "
                       "multipole is the quadrupole ell=2",
        "mask_fsky": ACT_BASELINE_FSKY,
        "mean_field_subtracted": True,
        "band_statistic_data": round(S_data, 6),
        "band_statistic_sim_median": round(float(np.median(S_sim)), 6),
        "p_value_data_vs_isotropic_sims": round(p_value, 4),
        "consistent_with_isotropic_sims": bool(0.02 < p_value < 0.98),
        "cl_debiased_data": {str(k): round(v, 8) for k, v in cl_data.items()},
        "cl_debiased_sim_mean": {str(k): round(v, 8)
                                 for k, v in cl_sim_mean.items()},
        "caveats": [
            "ell=0,1 (monopole+dipole) not reconstructed by ACT lensing -- "
            "the low-multipole cross-check is ell=2..%d only" % ELL_MAX,
            "the kappa low-multipole band is reconstruction-noise-dominated; "
            "consistency with the isotropic sims is the expected null result",
            "mean field from the 400 baseline sims; N0/N1 not separately "
            "debiased (the band statistic uses the sim ensemble as the null)",
        ],
        "scope_not_claimed": "independent-instrument low-multipole kappa "
                             "isotropy cross-check; diagnostic-only; no "
                             "anisotropy, geometry, family, or inference claim",
    }


def _render(p):
    return json.dumps(p, indent=2, sort_keys=True, default=str) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    card = measure()
    rendered = _render(card)
    if args.check:
        if not OUT.exists() or OUT.read_text() != rendered:
            print("STALE act_kappa_card.json", file=sys.stderr)
            return 1
        print("act kappa card current")
        return 0
    OUT.write_text(rendered)
    print(f"wrote {OUT} status={card['status']} "
          f"p={card.get('p_value_data_vs_isotropic_sims')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
