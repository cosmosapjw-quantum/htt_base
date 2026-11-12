"""L2 slice 5: RACS-low DR1 replication lane: count slope, footprint pixel scatter, Poisson-WLS estimator validation on synthetic randoms.
NO real dipole is computed. Columns by position in the VizieR galcut.dat '|' table, identified from the data (the ReadMe HTML was not machine-readable):
 col7 RA, col8 Dec (deg), col11 total flux (mJy; identification inferred: equals col14 peak for point sources), col31 l, col32 b (deg).
Cuts: S_tot>=S_MIN mJy, dec in [DEC_LO, 30], |b|>10. Synthetic randoms: uniform within the same dec/b cuts, label SYNTHETIC_RANDOM_CATALOGUE.
Usage: python3 L2_racs_lane.py --dat galcut.dat.gz --out out.json [--smin 20]
"""
import argparse, json, time, numpy as np, pandas as pd, healpy as hp
NS = 32
def wls(counts, E, nvec):
    A = np.column_stack([np.ones(len(E)), nvec]) * E[:, None]; w = 1 / np.maximum(E, 1e-9)
    ATA = (A.T * w) @ A; ATb = (A.T * w) @ counts; p = np.linalg.solve(ATA, ATb); return p[1:] / p[0]
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dat", required=True); ap.add_argument("--out", required=True); ap.add_argument("--smin", type=float, default=20.0); ap.add_argument("--nmock", type=int, default=60)
    a = ap.parse_args(); t0 = time.time(); rng = np.random.default_rng(20261112); DEC_LO = -50.0
    df = pd.read_csv(a.dat, sep="|", header=None, usecols=[6, 7, 10, 30, 31], names=["ra", "dec", "S", "l", "b"], dtype=float)
    n_all = len(df); df = df[np.isfinite(df.S)]
    sel = (df.S >= a.smin) & (df.dec >= DEC_LO) & (df.dec <= 30) & (df.b.abs() > 10); d = df[sel]; N = len(d)
    # slope of integral counts over [smin, 4 smin]
    ss = np.geomspace(a.smin, 4 * a.smin, 12); Ncum = np.array([(d.S >= s).sum() for s in ss]); x = -np.polyfit(np.log(ss), np.log(Ncum), 1)[0]
    bs = []
    for _ in range(30):
        dd = d.S.to_numpy()[rng.integers(0, N, N)]; bs.append(-np.polyfit(np.log(ss), np.log([(dd >= s).sum() for s in ss]), 1)[0])
    # synthetic randoms uniform on sphere within cuts (rejection via galactic latitude)
    M = 10 * N; v = rng.normal(size=(int(M * 3), 3)); v /= np.linalg.norm(v, axis=1)[:, None]
    dec = np.degrees(np.arcsin(v[:, 2])); ra = np.degrees(np.arctan2(v[:, 1], v[:, 0])) % 360
    from astropy.coordinates import SkyCoord; import astropy.units as u
    b = SkyCoord(ra * u.deg, dec * u.deg, frame="icrs").galactic.b.deg; ok = (dec >= DEC_LO) & (dec <= 30) & (np.abs(b) > 10); ra, dec = ra[ok][:M], dec[ok][:M]
    npix = hp.nside2npix(NS); pr = hp.ang2pix(NS, np.radians(90 - dec), np.radians(ra)); Er = np.bincount(pr, minlength=npix).astype(float); Er *= N / Er.sum()
    pc = hp.ang2pix(NS, np.radians(90 - d.dec.to_numpy()), np.radians(d.ra.to_numpy())); Cc = np.bincount(pc, minlength=npix).astype(float)
    use = Er > 0.05 * Er[Er > 0].mean(); nv = np.array(hp.pix2vec(NS, np.arange(npix))).T
    ratio = Cc[use] / Er[use]; psd = float(np.std(ratio)); pois = float(np.sqrt(np.mean(1 / Er[use])))
    sd_axis = float(np.sqrt(3 / N)); nulls = []; injs = {}
    for k in range(a.nmock):
        nulls.append(wls(rng.poisson(Er)[use].astype(float), Er[use], nv[use]))
    Dn = np.array(nulls)
    for lab, D in (("D0.01_z", np.array([0, 0, 0.01])), ("oblique", np.array([0.006, 0.004, 0.005]))):
        est = []
        for k in range(a.nmock // 2):
            lam = Er * (1 + nv @ D); est.append(wls(rng.poisson(lam)[use].astype(float), Er[use], nv[use]))
        est = np.array(est); injs[lab] = {"bias_over_se": ((est.mean(0) - D) / (est.std(0) / np.sqrt(len(est)))).tolist(), "sd": est.std(0).tolist()}
    res = {"scope": "RACS lane: slope, footprint scatter, estimator validation on synthetic randoms; no real dipole", "rows_all": int(n_all), "cuts": {"S_min_mJy": a.smin, "dec": [DEC_LO, 30], "abs_b_min": 10}, "n_selected": int(N),
           "count_slope_x": {"value": float(x), "boot_sd": float(np.std(bs)), "fit_S_range_mJy": [a.smin, 4 * a.smin]}, "EB_amplitude_over_beta": {f"alpha{al}": 2 + x * (1 + al) for al in (0.5, 0.75, 1.0)},
           "catalogue_vs_synthetic_pixel_ratio_sd": psd, "poisson_expected_sd": pois, "fullsky_poisson_sd_per_axis": sd_axis,
           "null": {"bias_over_se": (Dn.mean(0) / (Dn.std(0) / np.sqrt(len(Dn)))).tolist(), "sd": Dn.std(0).tolist(), "n": a.nmock}, "injection": injs, "synthetic_randoms": {"label": "SYNTHETIC_RANDOM_CATALOGUE", "n": int(len(ra))},
           "elapsed_s": time.time() - t0, "seed": 20261112, "versions": {"numpy": np.__version__, "pandas": pd.__version__, "healpy": hp.__version__}}
    json.dump(res, open(a.out, "w"), indent=1); print(json.dumps(res, indent=1))
if __name__ == "__main__": main()
