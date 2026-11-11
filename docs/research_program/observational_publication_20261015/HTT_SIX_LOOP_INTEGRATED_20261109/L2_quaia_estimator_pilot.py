"""L2 Quaia dipole-estimator validation pilot (SYNTHETIC mocks drawn from the AUTHENTIC Quaia randoms).

The real Quaia catalogue is NOT read (blinding-safe): only the 10x random catalogue (ra, dec, ebv), the nside-64
selection function T of Zenodo 10403370 v1.0.0, and the catalogue row count from the FITS header are used.
Mocks: N0 points drawn from the randoms, thinned with acceptance (1 + D.n)/(1+|D|) to inject a known dipole D.
Estimator: pixel counts at nside 64, weighted least squares of counts_p on E_p*(m + d.n_p) with expectation E either the
official selection function T or the random-catalogue density; D_hat = d/m.  Pixels with E below 5% of the mean
non-zero expectation are dropped.
Outputs: null bias/scatter, injection recovery, comparison with the full-sky Poisson scatter sqrt(3/N).
Usage: python3 L2_quaia_estimator_pilot.py --dir <Quaia bundle dir> --gal G20.0 --nmock 200 --out result.json
"""
import argparse, json, math, time, warnings
import numpy as np, healpy as hp
from astropy.io import fits
warnings.filterwarnings("ignore")
NS = 64

def unit(ra, dec):
    r, d = np.deg2rad(ra), np.deg2rad(dec)
    return np.stack([np.cos(d) * np.cos(r), np.cos(d) * np.sin(r), np.sin(d)], -1)

def fit_dipole(counts, Ecnt, pix_vec, floor_cnt):
    ok = Ecnt > floor_cnt
    A = np.column_stack([Ecnt, Ecnt * pix_vec[:, 0], Ecnt * pix_vec[:, 1], Ecnt * pix_vec[:, 2]])[ok]
    w = 1.0 / Ecnt[ok]                                           # Poisson variance ~ expectation
    Aw = A * w[:, None]
    beta = np.linalg.solve(A.T @ Aw, Aw.T @ counts[ok])
    return beta[1:] / beta[0], int(ok.sum())

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dir", required=True); ap.add_argument("--gal", default="G20.0")
    ap.add_argument("--nmock", type=int, default=200); ap.add_argument("--out", required=True); a = ap.parse_args(); t0 = time.time()
    with fits.open(f"{a.dir}/random_{a.gal}_10x.fits", memmap=True) as h:
        ra = np.asarray(h[1].data["ra"], float); dec = np.asarray(h[1].data["dec"], float)
    with fits.open(f"{a.dir}/selection_function_NSIDE64_{a.gal}.fits", memmap=True) as h:
        T = np.asarray(h[1].data["T"], float).reshape(-1)
    with fits.open(f"{a.dir}/quaia_{a.gal}.fits", memmap=True) as h:
        n_cat = int(h[1].header["NAXIS2"])                       # header only: number of catalogue sources (no data read)
    npix = hp.nside2npix(NS); pv = np.stack(hp.pix2vec(NS, np.arange(npix)), -1)
    v = unit(ra, dec)
    pix_c = hp.vec2pix(NS, *v.T)                                  # frame test: celestial vs galactic pixelisation
    vg = np.stack(hp.Rotator(coord=["C", "G"])(v.T), -1); pix_g = hp.vec2pix(NS, *vg.T)
    cc = np.bincount(pix_c, minlength=npix).astype(float); cg = np.bincount(pix_g, minlength=npix).astype(float)
    corr = {"celestial": float(np.corrcoef(cc, T)[0, 1]), "galactic": float(np.corrcoef(cg, T)[0, 1])}
    frame = max(corr, key=corr.get)
    pix_r, vpts = (pix_c, v) if frame == "celestial" else (pix_g, vg)
    dens = np.bincount(pix_r, minlength=npix).astype(float)       # random-catalogue density
    E_T = T / T.sum(); E_R = dens / dens.sum()
    res = {"scope": "SYNTHETIC mocks from authentic randoms; real catalogue not read", "release": "Quaia Zenodo 10403370 v1.0.0 " + a.gal,
           "n_catalogue_sources_header": n_cat, "n_random": int(len(ra)), "nside": NS, "frame_correlation_with_T": corr, "frame_used": frame,
           "frac_pix_T_zero": float((T == 0).mean()), "random_density_vs_T_corr": float(np.corrcoef(dens, T)[0, 1])}
    rng = np.random.default_rng(20261111); N0 = n_cat
    def mock(Dvec):
        idx = rng.permutation(len(ra))[: int(N0 * 1.25)]
        p = (1 + vpts[idx] @ Dvec) / (1 + np.linalg.norm(Dvec))
        keep = idx[rng.random(len(idx)) < p][:N0]
        return np.bincount(pix_r[keep], minlength=npix).astype(float)
    out = {}
    for name, E in (("expect_T", E_T), ("expect_randoms", E_R)):
        floor = 0.05 * float(E[E > 0].mean())
        per = {}
        for label, D in (("null", np.zeros(3)), ("D=0.005", np.array([0.005, 0, 0])), ("D=0.02_oblique", np.array([0.012, -0.010, 0.012]))):
            est = []; nused = None
            for _ in range(a.nmock if label == "null" else max(40, a.nmock // 4)):
                c = mock(D); d, nused = fit_dipole(c, E * c.sum(), pv, floor * c.sum()); est.append(d)
            est = np.array(est); bias = est.mean(0) - D; sd = est.std(0, ddof=1)
            per[label] = {"n_mocks": len(est), "mean_D_hat": est.mean(0).tolist(), "bias_vector": bias.tolist(), "bias_norm": float(np.linalg.norm(bias)),
                          "sd_per_axis": sd.tolist(), "n_pix_used": nused, "bias_over_sd_x_sqrt_n": (bias / sd * math.sqrt(len(est))).tolist()}
        out[name] = per
    res["estimators"] = out
    res["fullsky_poisson_sd_per_axis_sqrt3_over_N"] = math.sqrt(3.0 / N0)
    res["elapsed_s"] = time.time() - t0; res["versions"] = {"numpy": np.__version__, "healpy": hp.__version__}
    json.dump(res, open(a.out, "w"), indent=1, sort_keys=True)

if __name__ == "__main__":
    main()
