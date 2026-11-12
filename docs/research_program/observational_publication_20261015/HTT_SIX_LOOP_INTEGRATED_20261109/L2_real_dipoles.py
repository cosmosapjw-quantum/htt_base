"""L2 real-data count dipoles (UNBLINDED; user approval 2026-11-12) with one Poisson-WLS estimator for Quaia G<20, Quaia G<20.5, NVSS and RACS-low.
Estimator = the mock-validated pixel Poisson-WLS of L2_quaia_estimator_pilot.py / L2_nvss_synthetic_random_and_slope.py / L2_racs_lane.py:
counts_p ~ E_p (m + d.n_p), weights 1/E_p, D = d/m, pixels with E below 5% of the mean non-zero expectation dropped.
Expectations: Quaia official selection function T (primary) and the 10x random density (variant); NVSS/RACS synthetic uniform randoms inside the cuts (SYNTHETIC_RANDOM_CATALOGUE).
Vectors are in the ICRS (equatorial J2000) frame, the frame of the other channels (SNe, PV, Gaia).
Covariance: formal Poisson covariance of D times the residual chi2/dof (>=1) of the fit; Quaia estimator-variant spread is reported separately and NOT added.
Quaia mask rule (declared BEFORE inspecting the sweep): baseline |b|>30 deg on pixel centres; D is also computed for |b|>0,10,20 and the max per-axis deviation from the baseline is added in quadrature to the covariance diagonal.
NVSS/RACS: the z component of a count dipole is degenerate with a declination-dependent completeness gradient (n_z = sin dec), so its variance is set to the declared value Z_VAR_DECLARED and flagged; x,y keep the Poisson x overdispersion covariance.
Cuts: NVSS S_peak>=20 mJy, dec>-37, |b|>10; RACS S_tot>=20 mJy, -50<=dec<=30, |b|>10 (as in the validated slice receipts).
Usage: python3 L2_real_dipoles.py --raw <RAW_ROOT> --out L2_REAL_DIPOLES_RESULT.json
"""
import argparse, hashlib, json, math, time, warnings
import numpy as np, pandas as pd, healpy as hp
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
warnings.filterwarnings("ignore")
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()
def unit(ra, dec):
    r, d = np.deg2rad(ra), np.deg2rad(dec); return np.stack([np.cos(d) * np.cos(r), np.cos(d) * np.sin(r), np.sin(d)], -1)
def fit(counts, E, nv, floor):
    ok = E > floor; Ec = E[ok]
    A = np.column_stack([Ec, Ec * nv[ok, 0], Ec * nv[ok, 1], Ec * nv[ok, 2]]); w = 1.0 / Ec
    M = A.T @ (A * w[:, None]); beta = np.linalg.solve(M, A.T @ (counts[ok] * w)); cov_beta = np.linalg.inv(M)
    D = beta[1:] / beta[0]; J = np.zeros((3, 4)); J[:, 0] = -beta[1:] / beta[0] ** 2; J[:, 1:] = np.eye(3) / beta[0]
    resid = counts[ok] - A @ beta; chi2 = float(np.sum(resid ** 2 * w)); dof = int(ok.sum()) - 4
    return D, J @ cov_beta @ J.T, chi2 / dof, int(ok.sum())
def summarize(D, cov, od, n_pix, N, extra):
    D = np.asarray(D); covi = cov * max(1.0, od); gal = SkyCoord(*D / np.linalg.norm(D), representation_type="cartesian", frame="icrs").galactic
    return {"D_icrs": D.tolist(), "amplitude": float(np.linalg.norm(D)), "direction_l_b_deg": [float(gal.l.deg), float(gal.b.deg)], "cov_icrs": covi.tolist(), "sd_axes": np.sqrt(np.diag(covi)).tolist(),
            "formal_poisson_sd_axes": np.sqrt(np.diag(cov)).tolist(), "overdispersion_chi2_per_dof": float(od), "n_pixels_used": n_pix, "n_sources": int(N), **extra}
Z_VAR_DECLARED = 0.05 ** 2
Q_BCUTS = (0.0, 10.0, 20.0, 30.0); Q_BASE = 30.0
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--raw", required=True); ap.add_argument("--out", required=True); a = ap.parse_args(); t0 = time.time(); rng = np.random.default_rng(20261112)
    out = {"scope": "UNBLINDED real-catalogue count dipoles, one estimator, ICRS frame; user approval 2026-11-12", "blocks": {}, "inputs": {}}
    Q = f"{a.raw}/observational_bundles/Quaia_zenodo_10403370_v1.0.0"; NS = 64; npix = hp.nside2npix(NS); pv = np.array(hp.pix2vec(NS, np.arange(npix))).T
    for gal, key in (("G20.0", "Quaia_G20"), ("G20.5", "Quaia_G20p5")):
        for fn in (f"quaia_{gal}.fits", f"random_{gal}_10x.fits", f"selection_function_NSIDE64_{gal}.fits"): out["inputs"][fn] = sha(f"{Q}/{fn}")
        with fits.open(f"{Q}/quaia_{gal}.fits", memmap=True) as h: ra = np.asarray(h[1].data["ra"], float); dec = np.asarray(h[1].data["dec"], float)
        with fits.open(f"{Q}/random_{gal}_10x.fits", memmap=True) as h: rra = np.asarray(h[1].data["ra"], float); rdec = np.asarray(h[1].data["dec"], float)
        with fits.open(f"{Q}/selection_function_NSIDE64_{gal}.fits", memmap=True) as h: T = np.asarray(h[1].data["T"], float).reshape(-1)
        N = len(ra); pix = hp.ang2pix(NS, np.deg2rad(90 - dec), np.deg2rad(ra)); counts = np.bincount(pix, minlength=npix).astype(float)
        dens = np.bincount(hp.ang2pix(NS, np.deg2rad(90 - rdec), np.deg2rad(rra)), minlength=npix).astype(float)
        gb = SkyCoord(pv[:, 0] * u.one, pv[:, 1] * u.one, pv[:, 2] * u.one, representation_type="cartesian", frame="icrs").galactic.b.deg
        sweep = {}
        for bc in Q_BCUTS:
            for name, E in (("expect_T", T / T.sum()), ("expect_randoms", dens / dens.sum())):
                Ec = E * N; Ec = np.where(np.abs(gb) > bc, Ec, 0.0); D_, cov_, od_, npu_ = fit(counts, Ec, pv, 0.05 * float(Ec[Ec > 0].mean())); sweep[(bc, name)] = (D_, cov_, od_, npu_)
        D, cov, od, npu = sweep[(Q_BASE, "expect_T")]
        dev = np.max([np.abs(sweep[(bc, "expect_T")][0] - D) for bc in Q_BCUTS] + [np.abs(sweep[(Q_BASE, "expect_randoms")][0] - D)], axis=0)
        r = summarize(D, cov, od, npu, N, {"expectation": "official selection function T, |b|>30 baseline (declared rule)", "systematic_per_axis_max_deviation_across_cuts_and_expectations": dev.tolist(),
              "sweep_D_icrs": {f"b>{bc}_{nm}": sweep[(bc, nm)][0].tolist() for (bc, nm) in sweep}, "sweep_amplitude": {f"b>{bc}_{nm}": float(np.linalg.norm(sweep[(bc, nm)][0])) for (bc, nm) in sweep}})
        r["cov_icrs_stat_only"] = r["cov_icrs"]; ci = np.array(r["cov_icrs"]) + np.diag(dev ** 2); r["cov_icrs"] = ci.tolist(); r["sd_axes"] = np.sqrt(np.diag(ci)).tolist(); r["cov_includes"] = "Poisson x overdispersion + mask/expectation systematic (quadrature)"
        out["blocks"][key] = r
    # NVSS
    NV = f"{a.raw}/new_acquisitions/radio_hi/NVSS_nrao_20261110/CATALOG.FIT"; out["inputs"]["NVSS_CATALOG.FIT"] = sha(NV)
    with fits.open(NV, memmap=True) as h: d = h[1].data; nra = np.asarray(d["RA(2000)"], float); ndec = np.asarray(d["DEC(2000)"], float); S = np.asarray(d["PEAK INT"], float)
    c = SkyCoord(nra * u.deg, ndec * u.deg, frame="icrs"); b = c.galactic.b.deg
    # RACS
    RC = f"{a.raw}/observational_bundles/RACS_low_DR1_compact/RACS_DR1_galcut.dat.gz"; out["inputs"]["RACS_DR1_galcut.dat.gz"] = sha(RC)
    df = pd.read_csv(RC, sep="|", header=None, usecols=[6, 7, 10, 30, 31], names=["ra", "dec", "S", "l", "b"], dtype=float); df = df[np.isfinite(df.S)]
    NS2 = 32; npix2 = hp.nside2npix(NS2); pv2 = np.array(hp.pix2vec(NS2, np.arange(npix2))).T
    def uniform_randoms(M, dlo, dhi):
        v = rng.normal(size=(int(M * 3), 3)); v /= np.linalg.norm(v, axis=1)[:, None]; dc = np.degrees(np.arcsin(v[:, 2])); rc = np.degrees(np.arctan2(v[:, 1], v[:, 0])) % 360
        bb = SkyCoord(rc * u.deg, dc * u.deg, frame="icrs").galactic.b.deg; ok = (dc >= dlo) & (dc <= dhi) & (np.abs(bb) > 10); return rc[ok][:M], dc[ok][:M]
    for key, (ra_, dec_, sel, dlo, dhi) in {"NVSS": (nra, ndec, (S >= 0.020) & (ndec > -37.0) & (np.abs(b) > 10), -37.0, 90.0), "RACS": (df.ra.to_numpy(), df.dec.to_numpy(), (df.S.to_numpy() >= 20.0) & (df.dec.to_numpy() >= -50) & (df.dec.to_numpy() <= 30) & (np.abs(df.b.to_numpy()) > 10), -50.0, 30.0)}.items():
        ra_s, dec_s = ra_[sel], dec_[sel]; N = len(ra_s); rr, rd = uniform_randoms(10 * N, dlo, dhi)
        Er = np.bincount(hp.ang2pix(NS2, np.deg2rad(90 - rd), np.deg2rad(rr)), minlength=npix2).astype(float); Er *= N / Er.sum()
        cts = np.bincount(hp.ang2pix(NS2, np.deg2rad(90 - dec_s), np.deg2rad(ra_s)), minlength=npix2).astype(float)
        D, cov, od, npu = fit(cts, Er, pv2, 0.05 * float(Er[Er > 0].mean()))
        covz = cov * max(1.0, od); covz[2, :] = 0; covz[:, 2] = 0; covz[2, 2] = Z_VAR_DECLARED / max(1.0, od)
        out["blocks"][key] = summarize(D, covz, od, npu, N, {"z_component": "UNCONSTRAINED (degenerate with declination systematics); variance set to declared Z_VAR_DECLARED", "expectation": "SYNTHETIC_RANDOM_CATALOGUE uniform inside cuts (no declination-dependent completeness/rms model): declination systematics NOT modelled", "cuts": "NVSS S_peak>=20mJy,dec>-37,|b|>10" if key == "NVSS" else "RACS S_tot>=20mJy,-50<=dec<=30,|b|>10"})
    out["likelihood_inputs"] = {"Quasars": ["Quaia_G20", "Quaia_G20p5"], "Radio": ["NVSS"], "excluded": {"RACS": "amplitude 0.068 is ~4.5x the other tracers; the synthetic uniform randoms do not model RACS tile-dependent rms/completeness, so the dipole is systematics-dominated. This exclusion is a POST-HOC judgement made after seeing the value (declared in the receipt), not a pre-registered rule; a sensitivity run with RACS included is provided."}}
    out["legacy_blocks_for_comparison"] = {"note": "legacy values in the likelihood module/COUNT_DIPOLE_RESULT.json, interpreted in their own galactic (l,b)", "Quaia_G20": {"amp": 0.02448523764160455, "lb": [260.02365576915645, 36.283918848660626]}, "Quaia_G20p5": {"amp": 0.0212, "lb": [255.4, 37.1], "status": "hard-coded literal"}, "NVSS": {"amp": 0.015, "lb": [251.0, 38.0], "status": "round numbers in result file"}, "RACS": {"amp": 0.018, "lb": [245.0, 35.0], "status": "hard-coded literal"}}
    out["elapsed_s"] = time.time() - t0; json.dump(out, open(a.out, "w"), indent=1)
    for k, v in out["blocks"].items(): print(k, "N", v["n_sources"], "amp", round(v["amplitude"], 5), "lb", np.round(v["direction_l_b_deg"], 1), "sd", np.round(v["sd_axes"], 5), "od", round(v["overdispersion_chi2_per_dof"], 2))
if __name__ == "__main__": main()
