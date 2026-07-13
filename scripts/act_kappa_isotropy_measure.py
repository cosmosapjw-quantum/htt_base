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

Beyond the consistency p-value the lane sets a real CONSTRAINT: a 95% CL
model-independent UPPER LIMIT on excess low-multipole convergence power beyond
the isotropic-LambdaCDM end-to-end expectation. A flat-in-ell signal template of
angular power C_sig is injected into the debiased sims (the sims are the
N0+N1-inclusive isotropic null), and the limit C_sig^95 is the smallest signal
excluded at 95% by the observed band statistic:

    P( S_inj(C_sig^95) <= S_data ) = 0.05 .

Because S_inj is exactly quadratic in sqrt(C_sig) for a fixed unit-excess draw,
the limit is computed deterministically (no per-trial resampling).

Model-independent; the limit is a genuine upper-limit claim, not a detection and
not a Bianchi family/geometry claim (theory-g is fail-closed). The kappa
low-multipole band is reconstruction-noise-dominated, so the data band power is
consistent with the isotropic sims (the expected null) and the limit is
noise-floor-limited.

Outputs docs/generated/act_kappa_card.json. Deterministic (fixed sims + data +
seed); --check. Heavy: streams the 400 sim alms (run standalone, not the gate).
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
UL_SEED = 20260713                # deterministic upper-limit injection seed
UL_CL = 0.95                      # upper-limit confidence level
UL_NREP = 40                      # excess draws per sim (MC smoothing of p(C))


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


def _upper_limit(d, ms, wm, S_data, S_sim):
    """95% CL upper limit on a flat-in-ell excess convergence power C_sig.

    A unit-power (C_sig = 1) complex excess e is drawn per (rep, sim, mode):
    m = 0 real N(0,1); m > 0 real + imag N(0, 1/2) each, so E|e|^2 = 1 and
    E[sum wm |e|^2] = sum_l (2l+1). For a fixed draw the injected band
    statistic is exactly quadratic in sqrt(C_sig):

        S_inj(C) = S_sim + 2 sqrt(C) X + C Y ,
        X = sum_modes wm Re(conj(d) e) ,   Y = sum_modes wm |e|^2 ,

    so no per-trial resampling is needed. p(C) = mean_{rep,sim}[S_inj(C) <=
    S_data] is a (noisily) decreasing function of C; C_95 is the interpolated
    crossing p = 1 - 0.95. Deterministic given (UL_SEED, UL_NREP, grid)."""
    rng = np.random.default_rng(UL_SEED)
    n_sims, n_modes = d.shape
    m0 = ms == 0
    mp = ~m0
    npos = int(mp.sum())
    e = np.zeros((UL_NREP, n_sims, n_modes), dtype=np.complex128)
    e[:, :, m0] = rng.normal(0.0, 1.0, size=(UL_NREP, n_sims, int(m0.sum())))
    e[:, :, mp] = (rng.normal(0.0, np.sqrt(0.5), size=(UL_NREP, n_sims, npos))
                   + 1j * rng.normal(0.0, np.sqrt(0.5),
                                     size=(UL_NREP, n_sims, npos)))
    X = np.einsum("m,rsm->rs", wm, (np.conj(d)[None] * e).real).reshape(-1)
    Y = np.einsum("m,rsm->rs", wm, np.abs(e) ** 2).reshape(-1)
    Sflat = np.broadcast_to(S_sim, (UL_NREP, n_sims)).reshape(-1)

    def p_of(C):
        S_inj = Sflat + 2.0 * np.sqrt(C) * X + C * Y
        return float(np.mean(S_inj <= S_data))

    norm = float(sum(2 * l + 1 for l in range(ELL_MIN, ELL_MAX + 1)))
    C_scale = S_data / norm                              # C giving dS ~ S_data
    grid = np.concatenate([[0.0],
                           np.geomspace(1e-4 * C_scale, 1e2 * C_scale, 4000)])
    ps = np.array([p_of(C) for C in grid])
    target = 1.0 - UL_CL
    below = np.where(ps <= target)[0]
    if len(below) == 0:
        C95 = float(grid[-1])
    elif below[0] == 0:
        C95 = 0.0
    else:
        j = below[0]
        c0, c1, p0, p1 = grid[j - 1], grid[j], ps[j - 1], ps[j]
        C95 = float(c1) if p0 == p1 else float(
            c0 + (c1 - c0) * (p0 - target) / (p0 - p1))
    return {"c_sig_95ul": C95, "band_power_95ul": norm * C95,
            "norm": norm, "p_at_c0": p_of(0.0)}


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
    S_med = float(np.median(S_sim))

    # 95% CL model-independent upper limit on excess low-multipole power
    ul = _upper_limit(sim_low - mf, ms, wm, S_data, S_sim)

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
        "band_statistic_sim_median": round(S_med, 6),
        "p_value_data_vs_isotropic_sims": round(p_value, 4),
        "consistent_with_isotropic_sims": bool(0.02 < p_value < 0.98),
        "upper_limit_95cl": {
            "signal_template":
                "flat-in-ell excess convergence power C_sig over ell=2..%d"
                % ELL_MAX,
            "confidence_level": UL_CL,
            "c_sig_95ul": round(ul["c_sig_95ul"], 12),
            "band_power_95ul": round(ul["band_power_95ul"], 10),
            "band_power_95ul_over_sim_median":
                round(ul["band_power_95ul"] / S_med, 4),
            "interpretation":
                "95% CL upper limit on excess low-multipole kappa power "
                "beyond the isotropic-LambdaCDM end-to-end expectation; "
                "model-independent (flat template); the sim ensemble is the "
                "N0+N1-inclusive isotropic null",
        },
        "cl_debiased_data": {str(k): round(v, 8) for k, v in cl_data.items()},
        "cl_debiased_sim_mean": {str(k): round(v, 8)
                                 for k, v in cl_sim_mean.items()},
        "caveats": [
            "ell=0,1 (monopole+dipole) not reconstructed by ACT lensing -- "
            "the low-multipole cross-check is ell=2..%d only" % ELL_MAX,
            "the kappa low-multipole band is reconstruction-noise-dominated; "
            "consistency with the isotropic sims is the expected null result",
            "mean field from the 400 baseline sims; N0/N1 enter through the "
            "end-to-end sim ensemble used as the null, not as a separate "
            "analytic subtraction, so the upper limit is on power ABOVE that "
            "realistic-noise null",
        ],
        "claim": "95%% CL model-independent upper limit on excess low-multipole "
                 "(ell=2..%d) CMB-lensing convergence power beyond the "
                 "isotropic-LambdaCDM end-to-end expectation (band power < "
                 "%.3g); independent-instrument (ACT DR6) statistical-isotropy "
                 "constraint" % (ELL_MAX, ul["band_power_95ul"]),
        "scope_not_claimed": "an upper-limit / consistency constraint, NOT a "
                             "detection and NOT a Bianchi family/geometry claim "
                             "(the theory-g prediction is fail-closed, needs "
                             "the native low-multipole solver); the band is "
                             "reconstruction-noise-dominated so the limit is "
                             "noise-floor-limited",
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
