#!/usr/bin/env python3
"""R54-L03: count-dipole clustering body, same-estimator velocity null and competitor estimators.

Steps follow LOCAL_AGENT_CONTRACT.json:nodes[R54-L03]; deviations are in DEVIATIONS.json (DV-L03-*):
 1. HTT_SIX_LOOP_INTEGRATED_20261109/L2_real_dipoles.py re-run; D_icrs compared with the receipt (1e-4)
 2. clustering body per catalogue (R54-EQ-32, exact j_1): Quaia N(z) from the catalogue, NVSS two N(z) models; bias bracket; z_min cuts
 3. 500 Poisson mocks per catalogue on the data expectation map x (1 + d_kin.n + d_clust.n); identical estimator and sweep
 4. excess test per catalogue and common excess with the calibrated covariance; five views
 5. competitor estimators (Poisson likelihoods of Wagenveld et al. 2023 on NVSS and Mittal et al. 2024 on Quaia)
Claim tier C0.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import platform
import subprocess
import sys
import time
from pathlib import Path

import astropy.units as u
import healpy as hp
import numpy as np
import scipy
from astropy.coordinates import SkyCoord
from astropy.io import fits
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "htt", ROOT / "htt/src", ROOT, ROOT / "scripts/r54"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from htt.htt.infer import r54_calibration as cal  # noqa: E402
from htt.htt.infer import r54_counts as ct  # noqa: E402
from htt.htt.infer import r54_tensor_five_view as fv  # noqa: E402
import run_r54_lowz_frames as lz  # noqa: E402

PUB = ROOT / "docs/research_program/observational_publication_20261015"
R54 = PUB / "R54_TENSOR_FRAME_TOMOGRAPHY_20261116"
L2 = PUB / "HTT_SIX_LOOP_INTEGRATED_20261109/L2_real_dipoles.py"
RECEIPT = PUB / "HTT_SIX_LOOP_INTEGRATED_20261109/COUNT_DIPOLES_REAL_RECEIPT.json"
OUT = R54 / "RESULTS/R54_L03_RESULT.json"
RAW = Path("/mnt/extdrive/workdir/raw")
QUAIA = RAW / "observational_bundles/Quaia_zenodo_10403370_v1.0.0"
NVSS = RAW / "new_acquisitions/radio_hi/NVSS_nrao_20261110/CATALOG.FIT"
SCRATCH = Path("/mnt/extdrive/workdir/r54_logs")
PK = ROOT / "tests/fixtures/r54/planck18_linear_pk_z0.csv"
H0, OMEGA_M = 67.36, 0.3153
SEED, N_MOCK = 20261116, 500
Z_MIN = (0.0, 0.01, 0.03)
Q_BCUTS, Q_BASE = (0.0, 10.0, 20.0, 30.0), 30.0
Z_VAR_DECLARED = 0.05 ** 2
WAGENVELD = {"D": 1.40e-2, "sd": 0.29e-2, "ra": 146.0, "dec": -5.0, "nside": 32, "s_min_mJy": 15.0, "b_min": 7.0, "n_sources": 345803,
             "boxes": [(82.0, 90.0, -7.0, -1.0), (49.0, 52.0, -39.0, -36.0), (185.0, 189.0, 11.0, 14.0)], "bright_jy": 2.5, "bright_radius_deg": 0.3,
             "source": "Wagenveld, Kloeckner & Schwarz 2023, A&A 675, A72 (arXiv:2305.15335), Table 3, NVSS Poisson, NSIDE 32"}
MITTAL = {"D": 11e-3, "plus95": 6e-3, "minus95": 5e-3, "b_min": 40.0, "nside": 64,
          "source": "Mittal, Oayda & Lewis 2024, MNRAS 527, 8497 (arXiv:2311.14938), Quaia G<20.0, |b| > 40 deg, Poisson likelihood"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def l2_module():
    spec = importlib.util.spec_from_file_location("l2_real_dipoles", L2)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def laurent_bias(z):   # Laurent et al. 2017, b = 0.278 ((1+z)^2 - 6.565) + 2.393 (coefficients UNVERIFIED)
    return 0.278 * ((1.0 + np.asarray(z)) ** 2 - 6.565) + 2.393


def croom_bias(z):     # Croom et al. 2005, b = 0.53 + 0.289 (1+z)^2 (UNVERIFIED)
    return 0.53 + 0.289 * (1.0 + np.asarray(z)) ** 2


def data_inputs() -> dict:
    """Pixel counts and expectation maps exactly as built by L2_real_dipoles.py (Quaia G<20.0 and NVSS)."""
    rng = np.random.default_rng(20261112)                  # receipt seed; Quaia does not consume it, NVSS is its first consumer
    ns = 64
    npix = hp.nside2npix(ns)
    pv = np.array(hp.pix2vec(ns, np.arange(npix))).T
    with fits.open(QUAIA / "quaia_G20.0.fits", memmap=True) as h:
        ra, dec, zq = (np.asarray(h[1].data[c], float) for c in ("ra", "dec", "redshift_quaia"))
    with fits.open(QUAIA / "random_G20.0_10x.fits", memmap=True) as h:
        rra, rdec = np.asarray(h[1].data["ra"], float), np.asarray(h[1].data["dec"], float)
    with fits.open(QUAIA / "selection_function_NSIDE64_G20.0.fits", memmap=True) as h:
        t_sel = np.asarray(h[1].data["T"], float).reshape(-1)
    counts_q = np.bincount(hp.ang2pix(ns, np.deg2rad(90 - dec), np.deg2rad(ra)), minlength=npix).astype(float)
    dens = np.bincount(hp.ang2pix(ns, np.deg2rad(90 - rdec), np.deg2rad(rra)), minlength=npix).astype(float)
    gb = SkyCoord(pv[:, 0] * u.one, pv[:, 1] * u.one, pv[:, 2] * u.one, representation_type="cartesian", frame="icrs").galactic.b.deg
    quaia = {"counts": counts_q, "t_sel": t_sel, "dens": dens, "gb": gb, "pv": pv, "N": ra.size, "z": zq, "nside": ns}
    with fits.open(NVSS, memmap=True) as h:
        d = h[1].data
        nra, ndec, s = np.asarray(d["RA(2000)"], float), np.asarray(d["DEC(2000)"], float), np.asarray(d["PEAK INT"], float)
    b = SkyCoord(nra * u.deg, ndec * u.deg, frame="icrs").galactic.b.deg
    ns2 = 32
    npix2 = hp.nside2npix(ns2)
    pv2 = np.array(hp.pix2vec(ns2, np.arange(npix2))).T

    def uniform_randoms(m, dlo, dhi):                       # identical to the closure of L2_real_dipoles.main
        v = rng.normal(size=(int(m * 3), 3))
        v /= np.linalg.norm(v, axis=1)[:, None]
        dc = np.degrees(np.arcsin(v[:, 2]))
        rc = np.degrees(np.arctan2(v[:, 1], v[:, 0])) % 360
        bb = SkyCoord(rc * u.deg, dc * u.deg, frame="icrs").galactic.b.deg
        ok = (dc >= dlo) & (dc <= dhi) & (np.abs(bb) > 10)
        return rc[ok][:m], dc[ok][:m]

    sel = (s >= 0.020) & (ndec > -37.0) & (np.abs(b) > 10)
    n_n = int(sel.sum())
    rr, rd = uniform_randoms(10 * n_n, -37.0, 90.0)
    er = np.bincount(hp.ang2pix(ns2, np.deg2rad(90 - rd), np.deg2rad(rr)), minlength=npix2).astype(float)
    er *= n_n / er.sum()
    cts = np.bincount(hp.ang2pix(ns2, np.deg2rad(90 - ndec[sel]), np.deg2rad(nra[sel])), minlength=npix2).astype(float)
    nvss = {"counts": cts, "expect": er, "pv": pv2, "N": n_n, "nside": ns2, "ra": nra, "dec": ndec, "s": s, "b": b}
    return {"quaia": quaia, "nvss": nvss}


def quaia_estimate(l2, counts: np.ndarray, q: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """Receipt estimator for Quaia: baseline |b| > 30 with the selection function, systematic = max deviation over the sweep."""
    sweep, base = {}, None
    for bc in Q_BCUTS:
        for name, e in (("expect_T", q["t_sel"] / q["t_sel"].sum()), ("expect_randoms", q["dens"] / q["dens"].sum())):
            ec = np.where(np.abs(q["gb"]) > bc, e * q["N"], 0.0)
            floor = 0.05 * float(ec[ec > 0].mean())
            d_, cov_, od_, _ = l2.fit(counts, ec, q["pv"], floor)
            sweep[(bc, name)] = d_
            if bc == Q_BASE and name == "expect_T":
                base = (d_, cov_ * max(1.0, od_), ct.mask_hash(ec > floor))
    dev = np.max([np.abs(sweep[(bc, "expect_T")] - base[0]) for bc in Q_BCUTS] + [np.abs(sweep[(Q_BASE, "expect_randoms")] - base[0])], axis=0)
    return base[0], base[1], dev, base[2]


def nvss_estimate(l2, counts: np.ndarray, nv: dict) -> tuple[np.ndarray, np.ndarray, str]:
    floor = 0.05 * float(nv["expect"][nv["expect"] > 0].mean())
    d, cov, od, _ = l2.fit(counts, nv["expect"], nv["pv"], floor)
    covz = cov * max(1.0, od)
    covz[2, :] = 0.0
    covz[:, 2] = 0.0
    covz[2, 2] = Z_VAR_DECLARED / max(1.0, od)
    return d, covz, ct.mask_hash(nv["expect"] > floor)


def clustering_body(q: dict) -> dict:
    tab = np.loadtxt(PK, delimiter=",", skiprows=1)
    k, pk = tab[:, 0], tab[:, 1]
    good = pk > 0
    kk = np.geomspace(max(k[good].min(), 1e-5), min(k[good].max(), 0.5), 600)
    pkk = np.exp(np.interp(np.log(kk), np.log(k[good]), np.log(pk[good])))
    out = {}
    hist, edges = np.histogram(q["z"], bins=np.linspace(0.0, 4.5, 451))
    zc = 0.5 * (edges[1:] + edges[:-1])
    for bname, bfun in (("Laurent2017", laurent_bias), ("Croom2005", croom_bias)):
        for zmin in Z_MIN:
            cl1 = ct.dipole_clustering_cl1(kk, pkk, zc, hist.astype(float), bfun, OMEGA_M, H0, zmin)
            out[f"Quaia_G20/{bname}/zmin={zmin}"] = {"C1": cl1, "sd_axis": math.sqrt(ct.dipole_axis_variance(cl1))}
    zn = np.linspace(0.0, 6.0, 601)
    for nzname, zstar in (("Ho2008", 0.79), ("Ho2008_zstar_halved", 0.395)):
        nz = ct.ho_nz(zn, zstar, 1.18)
        for bias in (1.6, 2.0):
            for zmin in Z_MIN:
                cl1 = ct.dipole_clustering_cl1(kk, pkk, zn, nz, lambda z, b0=bias: np.full_like(z, b0), OMEGA_M, H0, zmin)
                out[f"NVSS/{nzname}/b={bias}/zmin={zmin}"] = {"C1": cl1, "sd_axis": math.sqrt(ct.dipole_axis_variance(cl1))}
    return out


def mocks(l2, data: dict, body_sd: dict, d_kin: dict, hashes_data: dict, rng: np.random.Generator) -> dict:
    """Poisson mocks on the data expectation map x (1 + (d_kin + d_clust).n), d_clust ~ N(0, sd^2 I); identical estimators."""
    out = {}
    q, nv = data["quaia"], data["nvss"]
    for name in ("Quaia_G20", "NVSS"):
        ds, hashes = [], set()
        for _ in range(N_MOCK):
            dc = rng.normal(0.0, body_sd[name], 3)
            if name == "Quaia_G20":
                lam = q["t_sel"] / q["t_sel"].sum() * q["N"] * (1.0 + q["pv"] @ (d_kin[name] + dc))
                d, _, _, h = quaia_estimate(l2, rng.poisson(np.clip(lam, 0.0, None)).astype(float), q)
            else:
                lam = nv["expect"] * (1.0 + nv["pv"] @ (d_kin[name] + dc))
                d, _, h = nvss_estimate(l2, rng.poisson(np.clip(lam, 0.0, None)).astype(float), nv)
            ds.append(d)
            hashes.add(h)
        ds = np.array(ds)
        cov = np.cov(ds.T, ddof=1)
        bias = ds.mean(axis=0) - d_kin[name]
        out[name] = {"n_mocks": N_MOCK, "d_kin_icrs": d_kin[name], "clustering_sd_axis": body_sd[name], "mean_D": ds.mean(axis=0), "bias": bias,
                     "cov": cov, "sd": np.sqrt(np.diag(cov)), "bias_over_sd": bias / np.sqrt(np.diag(cov)),
                     "mask_hash_data": hashes_data[name], "mask_hashes_mocks": sorted(hashes), "draws": ds}
    return out


def competitor_wagenveld(nv: dict) -> dict:
    p = WAGENVELD
    ns = p["nside"]
    npix = hp.nside2npix(ns)
    ra, dec, s, b = nv["ra"], nv["dec"], nv["s"], nv["b"]
    sel = (s >= p["s_min_mJy"] / 1000.0) & (np.abs(b) >= p["b_min"]) & (dec >= -40.0)
    for ra0, ra1, d0, d1 in p["boxes"]:
        sel &= ~((ra >= ra0) & (ra <= ra1) & (dec >= d0) & (dec <= d1))
    bright = s >= p["bright_jy"]
    near_map = np.zeros(hp.nside2npix(512), bool)
    for v in np.array(hp.ang2vec(np.deg2rad(90 - dec[bright]), np.deg2rad(ra[bright]))).reshape(-1, 3):
        near_map[hp.query_disc(512, v, math.radians(p["bright_radius_deg"]))] = True
    sel &= ~near_map[hp.ang2pix(512, np.deg2rad(90 - dec), np.deg2rad(ra))]
    pv = np.array(hp.pix2vec(ns, np.arange(npix))).T
    pra, pdec = hp.pix2ang(ns, np.arange(npix), lonlat=True)
    pgb = SkyCoord(pra * u.deg, pdec * u.deg, frame="icrs").galactic.b.deg
    pix_ok = (np.abs(pgb) >= p["b_min"]) & (pdec >= -40.0)
    for ra0, ra1, d0, d1 in p["boxes"]:
        pix_ok &= ~((pra >= ra0) & (pra <= ra1) & (pdec >= d0) & (pdec <= d1))
    counts = np.bincount(hp.ang2pix(ns, np.deg2rad(90 - dec[sel]), np.deg2rad(ra[sel])), minlength=npix).astype(float)
    counts[~pix_ok] = 0.0
    fit = ct.poisson_dipole_fit(counts, pix_ok.astype(float), pv)
    d = fit["D_icrs"]
    radec = [float(math.degrees(math.atan2(d[1], d[0])) % 360.0), float(math.degrees(math.asin(d[2] / np.linalg.norm(d))))]
    dz = (fit["amplitude"] - p["D"]) / p["sd"]
    return {"published": p, "owned": {"D": fit["amplitude"], "ra_dec_deg": radec, "n_sources_in_pixels": float(counts[pix_ok].sum()),
                                     "n_pixels": int(pix_ok.sum()), "sd_D_axes": np.sqrt(np.diag(fit["cov_D"]))},
            "amplitude_difference_in_published_sd": dz, "tolerance_published_sd": 1.5,
            "status": "REPRODUCED" if abs(dz) <= 1.5 else "NOT_REPRODUCED",
            "note": "pixels masked by their centres; the paper's pixel treatment of the boxes and bright-source discs is not given beyond the text"}


def competitor_mittal(q: dict) -> dict:
    p = MITTAL
    ok = np.abs(q["gb"]) > p["b_min"]
    fit = ct.poisson_dipole_fit(np.where(ok, q["counts"], 0.0), np.where(ok, q["t_sel"], 0.0), q["pv"])
    sd_pub = 0.5 * (p["plus95"] + p["minus95"]) / 1.96
    dz = (fit["amplitude"] - p["D"]) / sd_pub
    return {"published": {**p, "sd_from_95": sd_pub}, "owned": {"D": fit["amplitude"], "l_b_deg": lz.icrs_to_lb(fit["D_icrs"]),
                                                                "sd_D_axes": np.sqrt(np.diag(fit["cov_D"])), "n_pixels": fit["n_pixels"]},
            "amplitude_difference_in_published_sd": dz, "tolerance_published_sd": 1.5,
            "status": "REPRODUCED" if abs(dz) <= 1.5 else "NOT_REPRODUCED",
            "note": "Poisson rate N (1 + D cos theta) s_p with the Quaia selection function; |b| > 40 deg by pixel centre"}


def compute() -> dict:
    t0 = time.monotonic()
    missing = [str(p) for p in (QUAIA / "quaia_G20.0.fits", NVSS, L2, RECEIPT, PK) if not p.exists()]
    if missing:
        return {"status": "BLOCKED_MISSING_INPUT", "reason": "missing: " + ", ".join(missing)}
    # ---- step 1: receipt reproduction
    out_json = SCRATCH / "l03_L2_REAL_DIPOLES_RESULT.json"
    run = subprocess.run([sys.executable, str(L2), "--raw", str(RAW), "--out", str(out_json)], capture_output=True, text=True)
    if run.returncode != 0:
        raise SystemExit("L2_real_dipoles.py failed: " + run.stderr[-2000:])
    fresh = json.loads(out_json.read_text())["blocks"]
    receipt = json.loads(RECEIPT.read_text())["results"]
    diffs = {k: float(np.max(np.abs(np.asarray(fresh[k]["D_icrs"]) - np.asarray(receipt[k]["D_icrs"])))) for k in receipt}
    repro = max(diffs.values())
    print(f"[L03] receipt reproduction {repro:.2e} {time.monotonic() - t0:.0f}s", flush=True)
    l2 = l2_module()
    data = data_inputs()
    q, nv = data["quaia"], data["nvss"]
    dq, cq, devq, hq = quaia_estimate(l2, q["counts"], q)
    dn, cn, hn = nvss_estimate(l2, nv["counts"], nv)
    same = {"Quaia_G20": float(np.max(np.abs(dq - np.asarray(fresh["Quaia_G20"]["D_icrs"])))),
            "NVSS": float(np.max(np.abs(dn - np.asarray(fresh["NVSS"]["D_icrs"]))))}
    if max(same.values()) > 1e-12:
        raise SystemExit(f"the mock estimator does not reproduce the receipt estimator: {same}")
    # ---- step 2: clustering body
    body = clustering_body(q)
    body_sd = {"Quaia_G20": max(v["sd_axis"] for k, v in body.items() if k.startswith("Quaia") and k.endswith("zmin=0.0")),
               "NVSS": max(v["sd_axis"] for k, v in body.items() if k.startswith("NVSS") and k.endswith("zmin=0.0"))}
    print(f"[L03] clustering body {time.monotonic() - t0:.0f}s {body_sd}", flush=True)
    # ---- step 3: same-estimator mocks
    beta = lz.V_SUN_CMB / lz.C_KM_S
    d_kin = {name: lz.C_EB[name] * beta * lz.AXES_ICRS["cmb_dipole_axis"] for name in ("Quaia_G20", "NVSS")}
    mk = mocks(l2, data, body_sd, d_kin, {"Quaia_G20": hq, "NVSS": hn}, np.random.default_rng([SEED, 31]))
    print(f"[L03] mocks {time.monotonic() - t0:.0f}s", flush=True)
    hash_ok = all(v["mask_hashes_mocks"] == [v["mask_hash_data"]] for v in mk.values())
    # ---- step 4: excess tests
    obs = {"Quaia_G20": (dq, np.diag(devq**2)), "NVSS": (dn, np.diag([0.0, 0.0, Z_VAR_DECLARED]))}
    excess, ys, covs, taus = {}, [], [], []
    for name, (d, syst) in obs.items():
        m = mk[name]
        bias_small = bool(np.all(np.abs(m["bias_over_sd"]) <= 0.2))
        d_corr = d if bias_small else d - m["bias"]
        cov = m["cov"] + syst
        x = d_corr - d_kin[name]
        chi2 = float(x @ np.linalg.solve(cov, x))
        resid = m["draws"] - m["mean_D"]
        null_q = np.einsum("ij,ij->i", resid @ np.linalg.inv(m["cov"]), resid)
        excess[name] = {"bias_rule": "|mock bias| <= 0.2 sd on every axis", "bias_small": bias_small,
                        "bias_treatment": "estimator used as is" if bias_small else "mock bias subtracted; covariance from the mock scatter",
                        "D_icrs": d, "excess_icrs": x, "covariance": cov,
                        "chi2": fv.chi2_null_tail(chi2, 3, "gaussian with the mock covariance + receipt systematics"),
                        "Pi_mock": cal.EmpiricalNull(null_q, f"Poisson + clustering mocks (N={N_MOCK}), same estimator").upper_tail(
                            float(x @ np.linalg.solve(m["cov"], x))),
                        "implied_excess_velocity_km_s": float(np.linalg.norm(x)) / lz.C_EB[name] * lz.C_KM_S}
        ys.append(x)
        covs.append(cov)
        taus.append(lz.C_EB[name])
    big = np.zeros((6, 6))
    big[:3, :3], big[3:, 3:] = covs
    common = fv.gls_fit(np.concatenate(ys), big, fv.transport_design(taus, 3))
    pass_all = all(v["chi2"]["p_value"] >= 0.01 for v in excess.values())
    common_block = {"beta_excess_km_s_icrs": common["theta"] * lz.C_KM_S, "sd_km_s": np.sqrt(np.diag(common["cov"])) * lz.C_KM_S,
                    "wald": fv.chi2_null_tail(common["wald"], 3, "gaussian with the calibrated covariance"),
                    "consistency": {"chi2": common["chi2"], "dof": common["dof"], "p_value": common["p_value"]}}
    views = fv.five_view_record({
        "x": {"status": fv.AVAILABLE, "coordinates": "count-dipole excess D - c_EB beta_CMB (ICRS) per catalogue", "source": "Quaia G<20.0, NVSS"},
        "Q": {"status": fv.AVAILABLE, "body": "Poisson + linear LCDM clustering dipole (mock covariance), 95% ellipsoid",
              "Q_center": {k: math.sqrt(v["chi2"]["statistic"] / stats.chi2.ppf(0.95, 3)) for k, v in excess.items()}},
        "F": {"status": fv.UNAVAILABLE, "reason": "no declared convex body for a directional support functional of the excess"},
        "Pi": {"status": fv.AVAILABLE, "law": f"same-estimator Poisson + clustering mocks (N={N_MOCK})", "tails": {k: v["Pi_mock"] for k, v in excess.items()}},
        "G_F": {"status": fv.AVAILABLE, "transport": "excess_k = c_EB,k beta_excess (one frame offset shared by both catalogues)",
                "consistency_p": common["p_value"]}})
    # ---- step 5: competitor estimators
    comp = {"Wagenveld2023_NVSS_Poisson": competitor_wagenveld(nv), "Mittal2024_Quaia_Poisson": competitor_mittal(q)}
    reproduced = [k for k, v in comp.items() if v["status"] == "REPRODUCED"]
    print(f"[L03] competitors {time.monotonic() - t0:.0f}s {reproduced}", flush=True)
    for v in mk.values():
        v.pop("draws")
    decision = {
        "mock_bias": {k: v["bias_treatment"] for k, v in excess.items()},
        "excess": "H-L2a stays REJECTED for the owned estimators" if pass_all else "excess reported with its law; H-L2a is REOPENED",
        "excess_all_pass": pass_all,
        "competitor": "score benchmark target B05" if reproduced else "B05 is NOT_REPRODUCIBLE_FROM_TEXT; no comparison claim",
        "reproduced_competitors": reproduced}
    return {
        "status": "DONE_SCOPED_C0",
        "receipt_reproduction": {"max_abs_D_icrs_difference": repro, "per_catalogue": diffs, "mock_estimator_vs_receipt_estimator": same,
                                 "tolerance": 1e-4, "note": "receipt D_icrs is rounded to 1e-4"},
        "clustering_body": {"models": body, "mock_sd_axis": body_sd, "shot_plus_overdispersion_sd_axis": {"Quaia_G20": np.sqrt(np.diag(cq)), "NVSS": np.sqrt(np.diag(cn))},
                            "rule": "largest per-axis sd over the bias/N(z) bracket at z_min = 0 enters the mocks (DV-L03-3)",
                            "verification": "bias and N(z) parameters UNVERIFIED (DV-L03-2): bracket only"},
        "velocity_null": mk, "excess_tests": excess, "common_excess": common_block, "five_views": views, "competitors": comp, "decision": decision,
        "acceptance": {"receipt_reproduction_max_abs": {"value": repro, "op": "<=", "threshold": 1e-4, "pass": repro <= 1e-4},
                       "mask_hash_of_mocks_equals_mask_hash_of_data": {"value": hash_ok, "op": "==", "threshold": True, "pass": hash_ok}},
        "runtime_s": time.monotonic() - t0}


def main() -> None:
    res = compute()
    prov = {"script": "scripts/r54/run_r54_l03_counts.py", "script_sha256": sha256(Path(__file__)),
            "inputs_sha256": {**{str(p): sha256(p) for p in (QUAIA / "quaia_G20.0.fits", QUAIA / "random_G20.0_10x.fits",
                                                             QUAIA / "selection_function_NSIDE64_G20.0.fits", NVSS) if p.exists()},
                              **{str(p.relative_to(ROOT)): sha256(p) for p in (L2, RECEIPT, PK)}},
            "seed": SEED, "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__}
    out = {"schema": "htt.r54.l03_count_dipoles/1", "node": "R54-L03", "claim_tier": "C0", **res, "provenance": prov,
           "limitations": ["Bias and N(z) parameters are UNVERIFIED and enter as a bracket; the mocks use the largest bracket variance.",
                           "Mocks are Poisson on the data expectation map with a Gaussian clustering dipole only (no higher clustering multipoles, no selection systematics).",
                           "NVSS keeps the receipt's declared z variance (declination systematics); Quaia keeps the receipt's latitude/expectation sweep deviation.",
                           "Competitor estimators use pixel-centre masks; details not given in the papers are recorded in each entry."]}
    OUT.write_text(json.dumps(lz.clean(out), indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(lz.clean({"status": out["status"], "acceptance": out.get("acceptance"), "decision": out.get("decision")}), indent=1))
    if out["status"] != "DONE_SCOPED_C0":
        raise SystemExit(out["status"])


if __name__ == "__main__":
    main()
