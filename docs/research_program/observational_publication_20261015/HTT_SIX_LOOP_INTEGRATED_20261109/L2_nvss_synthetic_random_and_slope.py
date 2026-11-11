"""L2 NVSS slice: (a) measured integral-count slope x at the flux cut, (b) SYNTHETIC_RANDOM_CATALOGUE footprint, (c) estimator validation on mocks.

Blinding-safe: the real NVSS dipole is NOT computed. Columns read: RA(2000), DEC(2000), PEAK INT.
(a) x = -d ln N(>S) / d ln S from the catalogue's own integral counts (peak intensity as a flux proxy; NVSS has no integrated-flux column).
    Ellis-Baldwin amplitude  D = [2 + x (1 + alpha)] beta  with alpha NOT measured by NVSS (single frequency): reported as a grid, no point value.
(b) Randoms: uniform on the sphere inside the declared footprint (dec > dec_min, |b| > b_min), 10x the catalogue size.
    Label: SYNTHETIC_RANDOM_CATALOGUE (a model, not an observed product; NVSS blank/low-quality areas are NOT modelled).
(c) Mocks: N0 points drawn from the synthetic randoms, thinned to inject a known dipole; Poisson-weighted LS at nside 32, expectation = random density.
Usage: python3 L2_nvss_synthetic_random_and_slope.py --fits CATALOG.FIT --out result.json
"""
import argparse, json, math, time, warnings
import numpy as np, healpy as hp
from astropy.io import fits
warnings.filterwarnings("ignore")
NS = 32

def vec(ra, dec):
    r, d = np.deg2rad(ra), np.deg2rad(dec)
    return np.stack([np.cos(d) * np.cos(r), np.cos(d) * np.sin(r), np.sin(d)], -1)

def galactic_b_deg(v):
    z = hp.Rotator(coord=["C", "G"])(v.T)                      # rotated vectors (galactic frame)
    return np.rad2deg(np.arcsin(np.clip(z[2], -1, 1)))

def fit_dipole(counts, Ecnt, pix_vec, floor):
    ok = Ecnt > floor
    A = np.column_stack([Ecnt, Ecnt * pix_vec[:, 0], Ecnt * pix_vec[:, 1], Ecnt * pix_vec[:, 2]])[ok]; w = 1.0 / Ecnt[ok]
    beta = np.linalg.solve(A.T @ (A * w[:, None]), (A * w[:, None]).T @ counts[ok]); return beta[1:] / beta[0]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fits", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--smin", type=float, default=0.020); ap.add_argument("--decmin", type=float, default=-37.0); ap.add_argument("--bmin", type=float, default=10.0)
    ap.add_argument("--nmock", type=int, default=60); a = ap.parse_args(); t0 = time.time()
    with fits.open(a.fits, memmap=True) as h:
        d = h[1].data; ra = np.asarray(d["RA(2000)"], float); dec = np.asarray(d["DEC(2000)"], float); S = np.asarray(d["PEAK INT"], float)
    res = {"scope": "slope + synthetic randoms + estimator validation; real dipole NOT computed", "n_rows": int(len(ra)),
           "cuts": {"S_peak_min_Jy": a.smin, "dec_min_deg": a.decmin, "abs_b_min_deg": a.bmin}}
    v = vec(ra, dec); b = galactic_b_deg(v)
    sel = (S > a.smin) & (dec > a.decmin) & (np.abs(b) > a.bmin); N0 = int(sel.sum()); res["n_selected"] = N0
    base = (dec > a.decmin) & (np.abs(b) > a.bmin)             # footprint cut only; the fit range straddles the flux cut
    grid = np.exp(np.linspace(math.log(0.020), math.log(0.080), 12))
    def slope(Sv):
        Sv = np.sort(Sv)[::-1]; N = np.array([np.searchsorted(-Sv, -g, side="right") for g in grid], float)
        return -np.polyfit(np.log(grid), np.log(N), 1)[0], N
    x_hat, Ngrid = slope(S[base]); rng = np.random.default_rng(20261112)
    boots = [slope(S[base][rng.integers(0, int(base.sum()), int(base.sum()))])[0] for _ in range(30)]
    res["x_integral_slope"] = {"value": float(x_hat), "bootstrap_sd": float(np.std(boots, ddof=1)), "fit_range_Jy": [0.020, 0.080],
                               "flux_proxy": "PEAK INT (not integrated flux)", "N_gt_grid": Ngrid.tolist()}
    res["EB_amplitude_over_beta_grid"] = {str(al): float(2 + x_hat * (1 + al)) for al in (0.5, 0.75, 1.0)}
    res["EB_note"] = "alpha is not measurable from NVSS alone; the response is a range over a declared alpha grid, not a point value"
    nr = 10 * N0; vr = []; need = nr
    while need > 0:
        u = rng.normal(size=(int(need * 3), 3)); u /= np.linalg.norm(u, axis=1)[:, None]
        keep = (np.rad2deg(np.arcsin(u[:, 2])) > a.decmin) & (np.abs(galactic_b_deg(u)) > a.bmin); vr.append(u[keep]); need -= int(keep.sum())
    vr = np.vstack(vr)[:nr]
    res["synthetic_randoms"] = {"label": "SYNTHETIC_RANDOM_CATALOGUE", "n": int(nr), "geometry": "uniform on sphere inside footprint cuts; no completeness/rms modulation"}
    npix = hp.nside2npix(NS); pv = np.stack(hp.pix2vec(NS, np.arange(npix)), -1); pix_r = hp.vec2pix(NS, *vr.T)
    dens = np.bincount(pix_r, minlength=npix).astype(float); E = dens / dens.sum(); floor = 0.05 * float(E[E > 0].mean())
    cnt = np.bincount(hp.vec2pix(NS, *v[sel].T), minlength=npix).astype(float)
    okp = E > floor; ratio = cnt[okp] / (E[okp] * cnt.sum())
    res["catalogue_vs_synthetic_footprint"] = {"pixel_ratio_sd": float(ratio.std()), "poisson_expected_sd": float(np.sqrt(np.mean(1.0 / (E[okp] * cnt.sum())))),
        "note": "excess over Poisson = real-sky structure + unmodelled footprint/rms variation; NOT a dipole measurement"}
    def mock(D):
        idx = rng.permutation(len(vr))[: int(N0 * 1.25)]; p = (1 + vr[idx] @ D) / (1 + np.linalg.norm(D)); keep = idx[rng.random(len(idx)) < p][:N0]
        return np.bincount(pix_r[keep], minlength=npix).astype(float)
    out = {}
    for label, D in (("null", np.zeros(3)), ("D=0.01", np.array([0.01, 0, 0])), ("D=0.02_oblique", np.array([0.012, -0.010, 0.012]))):
        est = np.array([fit_dipole(c, E * c.sum(), pv, floor * c.sum()) for c in (mock(D) for _ in range(a.nmock))])
        bias = est.mean(0) - D; sd = est.std(0, ddof=1)
        out[label] = {"n_mocks": a.nmock, "bias": bias.tolist(), "sd": sd.tolist(), "bias_over_se": (bias / sd * math.sqrt(a.nmock)).tolist()}
    res["estimator_validation"] = out; res["fullsky_poisson_sd_sqrt3_over_N"] = math.sqrt(3 / N0)
    res["elapsed_s"] = time.time() - t0; res["versions"] = {"numpy": np.__version__, "healpy": hp.__version__}
    json.dump(res, open(a.out, "w"), indent=1, sort_keys=True)

if __name__ == "__main__":
    main()
