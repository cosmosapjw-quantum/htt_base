#!/usr/bin/env python3
"""R58 axis diagnostics (referee repair M1): which block of the committed joint fit excludes the origin, and where the
apparent quadrupole points. Reads only the committed fit (RESULTS/OWNED_TENSOR_RESULT.json: variants.<m>.fit.estimate,
.covariance, .rank). No refit, no new variant, no new data. Every alignment number is post hoc: the reference family below
was fixed after the axes had been seen.

    python scripts/r58/build_r58_axis_diagnostics.py [--root .] [--output <file>]

D1 block Wald statistics of V (3), dH (3), kappa (5): marginal blocks of one joint fit, correlated, not additive, post hoc.
D2 principal frame of K = sum_a kappa_a E_a (E_a = r54_tensor_five_view.STF5_BASIS); axes headless.
D3 eight reference axes (closed family).
D4 fixed-axis contrasts q(n) = n.K.n through r58 linear_interval / robust_interval.
D5 alignment calibration under kappa* ~ N(0, Sigma_kappa), N = 200000, default_rng(20261117) anew per variant.
D6 axes stated in published CF4 / Pantheon+ analyses (read in the primary sources on 2026-11-17), with angles to D2.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
PKG_REL = "docs/research_program/observational_publication_20261015/R58_MIXED_TENSOR_CONVERGENCE_20261117"
MODELS = ("log", "log_mono", "log_mono_error", "log_mono_galactic", "log_mono_radial", "log_split", "log_survey")
PARAMETERS = ["V_x_km_s", "V_y_km_s", "V_z_km_s", "dH_x", "dH_y", "dH_z"] + [f"kappa_{i}" for i in range(5)]
BLOCKS = {"V": slice(0, 3), "dH": slice(3, 6), "kappa": slice(6, 11)}
N_DRAWS, SEED = 200000, 20261117
#: NED object lookup of "M87" on 2026-11-17 (NED-NNS, preferred position RefCode 2017ApJS..233....3T; redshift 0.004282962982)
M87_RA_DEC = (187.7059308, 12.39112326)
M87_REDSHIFT_NED = 0.004282962982

#: axes stated in the primary sources, read on 2026-11-17 (arXiv HTML). Galactic (l, b) in degrees. Outcome labels of the
#: benchmark stay NOT_COMPARABLE: different data cuts, estimands and laws. "not stated" entries are recorded as such.
PUBLISHED_AXES = [
    {"comparator_id": "B06A_BOUBEL_2025", "paper": "Boubel et al. 2025, JCAP 03, 066 (arXiv:2412.14607)", "object": "H0 (zero-point) dipole maximum",
     "l": 142.0, "b": 52.0, "uncertainty": "+-30 deg in l, +-10 deg in b (1 sigma, Fig. 4)",
     "sign": "direction of the maximum of H0 (Sec. 1: 'the direction of the H0 dipole to be that of its maximum value')",
     "locator": "abstract; Sec. 4.1; Fig. 4", "frame": "Galactic"},
    {"comparator_id": "B06A_BOUBEL_2025", "paper": "Boubel et al. 2025", "object": "quadrupole axis", "l": None, "b": None,
     "note": "not stated (amplitude only; Sec. 4.1: 'The direction is not fixed')", "locator": "Sec. 4.1"},
    {"comparator_id": "B06B_SALZANO_2025", "paper": "Salzano et al. 2025 (arXiv:2512.02526)", "object": "H0 dipole maximum, CF4, mu in [31, 36]",
     "l": 299.0, "b": 2.0, "uncertainty": "+-2 deg", "sign": "maximum (positive excess) of the dipole", "locator": "Table 1", "frame": "Galactic"},
    {"comparator_id": "B06B_SALZANO_2025", "paper": "Salzano et al. 2025", "object": "H0 dipole maximum, CF4, z in [0.03, 0.06]",
     "l": 299.0, "b": -14.0, "uncertainty": "+-4 deg in l, +-3 deg in b", "sign": "maximum (positive excess) of the dipole", "locator": "Table 1", "frame": "Galactic"},
    {"comparator_id": "B06B_SALZANO_2025", "paper": "Salzano et al. 2025", "object": "quadrupole axis", "l": None, "b": None,
     "note": "not stated separately: axial symmetry (m = 0) about the dipole axis is assumed in the fiducial analysis", "locator": "fiducial-analysis text: 'we assumed axial symmetry and retained only the m=0 terms'"},
    {"comparator_id": "B06C_VICENTE_2026", "paper": "Vicente et al. 2026 (arXiv:2607.07821)", "object": "expansion-rate dipole maximum (Nside 8)",
     "l": 290.0, "b": -4.0, "uncertainty": "+-5 deg", "sign": "maximum of eta_1", "locator": "abstract; Sec. V.1; Table 2", "frame": "Galactic, CMB rest frame"},
    {"comparator_id": "B06C_VICENTE_2026", "paper": "Vicente et al. 2026", "object": "quadrupole multipole vector 1 (Nside 8; a Maxwell multipole vector, not a principal axis)",
     "l": 284.0, "b": 52.0, "uncertainty": "+-19 deg", "sign": "headless; listed in the hemisphere with north pole at the dipole", "locator": "Table 2", "frame": "Galactic"},
    {"comparator_id": "B06C_VICENTE_2026", "paper": "Vicente et al. 2026", "object": "quadrupole multipole vector 2 (Nside 8; a Maxwell multipole vector, not a principal axis)",
     "l": 316.0, "b": -19.0, "uncertainty": "+-14 deg", "sign": "headless; listed in the hemisphere with north pole at the dipole", "locator": "Table 2", "frame": "Galactic"},
    {"comparator_id": "B06X_KALBOUNEH_2025", "paper": "Kalbouneh et al. 2026, JCAP 03, 084 (arXiv:2510.02510)", "object": "common symmetry axis of dipole, quadrupole and octupole",
     "l": 299.0, "b": 5.0, "uncertainty": "not quoted", "sign": "direction of maximum amplitude of each multipole",
     "locator": "Sec. 4.2 (the abstract gives l = 295 deg)", "frame": "Galactic, CMB frame"},
    {"comparator_id": "B06X_KALBOUNEH_2025", "paper": "Kalbouneh et al. 2026", "object": "quadrupole maximum, CF4c", "l": 296.0, "b": 8.0,
     "uncertainty": "not quoted", "sign": "maximum of the quadrupole", "locator": "Table 2", "frame": "Galactic"},
    {"comparator_id": "COWELL_2022", "paper": "Cowell et al. 2022 (arXiv:2212.13569)", "object": "Hubble quadrupole eigenvectors, fixed a priori (not fitted)",
     "axes_lb": [[118.0, 85.0], [341.0, 4.0], [71.0, -4.0]], "uncertainty": "none (fixed to Parnovsky & Parnowski 2012)", "sign": "not stated",
     "locator": "Sec. 4.5; Sec. 5.2", "frame": "Galactic"},
]


def imports(root: Path):
    for p in (root / "htt", root / "htt/src", root, root / "scripts/r54"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    from htt.htt.infer import r54_tensor_five_view as fv
    from htt.htt.infer import r58_mixed_tensor_likelihood as mt
    import run_r54_lowz_frames as lz
    import run_r54_cf4_exact as cf
    return fv, mt, lz, cf


def unit_radec(ra: float, dec: float) -> np.ndarray:
    a, d = math.radians(ra), math.radians(dec)
    return np.array([math.cos(d) * math.cos(a), math.cos(d) * math.sin(a), math.sin(d)])


def headless(v: np.ndarray) -> np.ndarray:
    """Representative of the axis +-v with Dec >= 0 (ties: x >= 0)."""
    v = np.asarray(v, float) / np.linalg.norm(v)
    if v[2] < 0 or (v[2] == 0 and v[0] < 0):
        v = -v
    return v


def radec(v: np.ndarray) -> list[float]:
    v = np.asarray(v, float) / np.linalg.norm(v)
    return [float(math.degrees(math.atan2(v[1], v[0])) % 360.0), float(math.degrees(math.asin(np.clip(v[2], -1, 1))))]


def axis_angle(u: np.ndarray, v: np.ndarray) -> float:
    c = abs(float(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v)))
    return float(math.degrees(math.acos(min(1.0, c))))


def fit_arrays(fit: dict) -> dict:
    out = dict(fit)
    for k in ("estimate", "covariance", "_estimability_scale", "_estimability_null_basis", "_zero_design_columns"):
        out[k] = np.asarray(fit[k], dtype=bool if k == "_zero_design_columns" else float)
    return out


def reference_axes(lz, cat_n: np.ndarray) -> tuple[dict, dict]:
    t = cat_n.T @ cat_n / cat_n.shape[0]
    w, vec = np.linalg.eigh(0.5 * (t + t.T))
    axes = {
        "ICRS_pole": (np.array([0.0, 0.0, 1.0]), "ICRS (J2000) north pole, by definition"),
        "Galactic_pole": (lz.AXES_ICRS["galactic_pole"], "North Galactic pole: third row of R_I2G in scripts/r54/run_r54_lowz_frames.py"),
        "ecliptic_pole": (lz.AXES_ICRS["ecliptic_pole"], "North ecliptic pole, J2000 obliquity 23.4392911 deg (run_r54_lowz_frames.AXES_ICRS)"),
        "supergalactic_pole": (lz.AXES_ICRS["supergalactic_pole"], "Supergalactic north pole (l, b) = (47.37, +6.32) deg (run_r54_lowz_frames.AXES_ICRS)"),
        "CMB_dipole_apex": (lz.AXES_ICRS["cmb_dipole_axis"], f"Planck 2018 solar dipole apex (l, b) = ({lz.L_CMB}, {lz.B_CMB}) deg (run_r54_lowz_frames.L_CMB, B_CMB)"),
        "M87": (unit_radec(*M87_RA_DEC), "NED object lookup 2026-11-17 (NED-NNS; position RefCode 2017ApJS..233....3T); a direction label only"),
        "footprint_major": (vec[:, 2], "eigenvector with the largest eigenvalue of T = mean_i n_i n_i^T over the selected CF4 groups"),
        "footprint_minor": (vec[:, 0], "eigenvector with the smallest eigenvalue of T = mean_i n_i n_i^T over the selected CF4 groups"),
    }
    assert len(axes) == 8, "the reference family is closed at eight axes"
    axes = {k: (headless(v), s) for k, (v, s) in axes.items()}
    return axes, {"eigenvalues": [float(x) for x in w], "n_groups": int(cat_n.shape[0])}


def principal_frame(fv, kappa: np.ndarray) -> dict:
    k = np.tensordot(np.asarray(kappa, float), fv.STF5_BASIS, axes=1)
    w, vec = np.linalg.eigh(0.5 * (k + k.T))
    return {"eigenvalues": w, "neg": headless(vec[:, 0]), "mid": headless(vec[:, 1]), "pos": headless(vec[:, 2])}


def contrast(fv, n: np.ndarray) -> np.ndarray:
    c = np.zeros(11)
    c[6:] = [float(n @ e @ n) for e in fv.STF5_BASIS]
    return c


def tails(abs_cos_draws: np.ndarray, abs_cos_obs: np.ndarray) -> tuple[np.ndarray, float, np.ndarray]:
    """Per-pair tails (1 + #{|cos*| >= |cos_obs|}) / (N + 1), and the family-wise value: fraction of draws whose smallest
    per-pair tail (rank transform within each pair on the same draws, the draw itself counted) is <= the observed smallest tail."""
    n, m = abs_cos_draws.shape
    obs = np.array([(1 + np.count_nonzero(abs_cos_draws[:, j] >= abs_cos_obs[j])) / (n + 1) for j in range(m)])
    draw_tail = np.empty_like(abs_cos_draws)
    for j in range(m):
        s = np.sort(abs_cos_draws[:, j])
        draw_tail[:, j] = (n - np.searchsorted(s, abs_cos_draws[:, j], side="left")) / (n + 1)
    fw = float(np.mean(draw_tail.min(axis=1) <= obs.min()))
    return obs, fw, draw_tail


def compute(root: Path) -> dict:
    fv, mt, lz, cf = imports(root)
    res_path = root / PKG_REL / "RESULTS/OWNED_TENSOR_RESULT.json"
    res = json.loads(res_path.read_text())
    if res["parameter_names"] != PARAMETERS:
        raise ValueError("parameter order of the committed fit differs from V[0:3], dH[3:6], kappa[6:11]")
    cat = cf.load()["cat"]
    axes, footprint = reference_axes(lz, np.asarray(cat["n_J2000"], float))
    ref_names = list(axes)
    fits = {m: fit_arrays(res["variants"][m]["fit"]) for m in MODELS}
    c2 = float(stats.chi2.ppf(0.95, 11))
    out = {"schema": "htt.r58.axis_diagnostics/1", "status": "POST_HOC_DIAGNOSTIC", "claim_tier": "C0",
           "source_fit": {"file": f"{PKG_REL}/RESULTS/OWNED_TENSOR_RESULT.json", "sha256": hashlib.sha256(res_path.read_bytes()).hexdigest(),
                          "fields": "variants.<m>.fit.estimate, .covariance, .rank"},
           "conventions": {"frame": "ICRS/J2000, n from observer to source", "tensor": "K = sum_a kappa_a E_a, E_a = r54_tensor_five_view.STF5_BASIS; n.K.n = sum_a kappa_a n.E_a.n",
                           "galactic": "R_I2G of scripts/r54/run_r54_lowz_frames.py", "axes": "headless; representative with Dec >= 0",
                           "negative_axis": "eigenvector of the smallest eigenvalue of K", "positive_axis": "eigenvector of the largest eigenvalue of K"},
           "post_hoc": "the reference family was fixed after the reviewer had seen the axes; every alignment number is post hoc",
           "sample": {"n_groups": footprint["n_groups"], "z_CMB_min": float(np.min(cat["z_CMB"])), "z_CMB_max": float(np.max(cat["z_CMB"])),
                      "window_centers": list(cf.CENTERS), "window_gaussian_sd": float(cf.WIDTH), "M87_redshift_NED": M87_REDSHIFT_NED},
           "reference_axes": {k: {"icrs_unit": v.tolist(), "ra_dec": radec(v), "l_b": lz.icrs_to_lb(v), "source": s} for k, (v, s) in axes.items()},
           "footprint_tensor_eigenvalues": footprint["eigenvalues"],
           "reference_axis_angles_deg": {a: {b: axis_angle(axes[a][0], axes[b][0]) for b in ref_names if b != a} for a in ref_names},
           "variants": {}, "contrast_hulls": {}}
    for m in MODELS:
        f = fits[m]
        est, cov = f["estimate"], f["covariance"]
        d1 = {}
        for b, sl in BLOCKS.items():
            a, s = est[sl], cov[sl, sl]
            w = float(a @ np.linalg.solve(s, a))
            d1[b] = {"dim": int(sl.stop - sl.start), "wald": w, "p": float(stats.chi2.sf(w, sl.stop - sl.start))}
        pf = principal_frame(fv, est[6:])
        d2 = {"eigenvalues": [float(x) for x in pf["eigenvalues"]]}
        for ax in ("neg", "mid", "pos"):
            d2[ax] = {"icrs_unit": pf[ax].tolist(), "ra_dec": radec(pf[ax]), "l_b": lz.icrs_to_lb(pf[ax]),
                      "angle_to_reference_deg": {r: axis_angle(pf[ax], axes[r][0]) for r in ref_names}}
        d4 = {}
        for r in ref_names:
            c = contrast(fv, axes[r][0])
            sim = mt.linear_interval(f, c, level=0.95, simultaneous=True)
            pt = mt.linear_interval(f, c, level=0.95, simultaneous=False)
            d4[r] = {"estimate": sim["estimate"], "sd": sim["sd"], "z_one_degree_exploratory": sim["estimate"] / sim["sd"],
                     "simultaneous_95": [sim["lower"], sim["upper"]], "simultaneous_radius_sd": math.sqrt(sim["c2"]),
                     "pointwise_95": [pt["lower"], pt["upper"]], "identified": sim["identified"]}
        # D5: alignment calibration of the two extreme axes against the eight reference axes
        rng = np.random.default_rng(SEED)
        chol = np.linalg.cholesky(cov[6:, 6:])
        draws = rng.standard_normal((N_DRAWS, 5)) @ chol.T
        kstar = np.einsum("na,aij->nij", draws, fv.STF5_BASIS)
        _, vecs = np.linalg.eigh(0.5 * (kstar + np.transpose(kstar, (0, 2, 1))))
        refs = np.array([axes[r][0] for r in ref_names])                       # 8 x 3
        pairs = [(ax, r) for ax in ("neg", "pos") for r in ref_names]
        cos_draws = np.concatenate([np.abs(vecs[:, :, 0] @ refs.T), np.abs(vecs[:, :, 2] @ refs.T)], axis=1)   # N x 16
        cos_obs = np.array([abs(float(pf[ax] @ axes[r][0])) for ax, r in pairs])
        obs_tail, fw, _ = tails(cos_draws, cos_obs)
        d5 = {"n_draws": N_DRAWS, "seed": SEED, "pairs": {f"{ax}~{r}": {"abs_cos_observed": float(cos_obs[i]), "tail": float(obs_tail[i]),
                                                                        "binomial_se": float(math.sqrt(obs_tail[i] * (1 - obs_tail[i]) / N_DRAWS))}
                                                         for i, (ax, r) in enumerate(pairs)},
              "smallest_tail": float(obs_tail.min()), "smallest_tail_pair": "~".join(pairs[int(np.argmin(obs_tail))]),
              "familywise_16": fw, "familywise_binomial_se": float(math.sqrt(fw * (1 - fw) / N_DRAWS)),
              "law": "kappa* ~ N(0, Sigma_kappa) with Sigma_kappa = covariance[6:11, 6:11] of the committed fit; rng = default_rng(20261117) created anew for this variant; "
                     "draws = standard_normal((N, 5)) @ cholesky(Sigma_kappa).T, the same draws for all 16 pairs"}
        out["variants"][m] = {"rank": int(f["rank"]), "D1_block_wald": d1, "D2_principal_frame": d2, "D4_fixed_axis_contrasts": d4, "D5_alignment": d5}
    for r in ref_names:
        rob = mt.robust_interval([fits[m] for m in MODELS], contrast(fv, axes[r][0]), level=0.95, simultaneous=True)
        out["contrast_hulls"][r] = {"lower": rob["lower"], "upper": rob["upper"], "contains_zero": bool(rob["lower"] < 0 < rob["upper"]),
                                    "identified_in_all_models": rob["identified_in_all_models"]}
    out["simultaneous_radius_sd_rank11"] = math.sqrt(c2)
    pub = []
    for row in PUBLISHED_AXES:
        rec = dict(row)
        lbs = row.get("axes_lb") or ([[row["l"], row["b"]]] if row.get("l") is not None else [])
        if lbs:
            vs = [headless(lz.R_I2G.T @ lz.gal_unit(l, b)) for l, b in lbs]
            rec["angle_to_D2_axes_deg"] = {m: {ax: [axis_angle(v, np.array(out["variants"][m]["D2_principal_frame"][ax]["icrs_unit"])) for v in vs]
                                               for ax in ("neg", "mid", "pos")} for m in MODELS}
        pub.append(rec)
    out["D6_published_axes"] = {"rows": pub, "outcome": "NOT_COMPARABLE (different samples, estimands and laws; directions listed for orientation only)",
                                "read": "primary sources (arXiv HTML) read on 2026-11-17; values transcribed with their locators"}
    return out


def clean(x):
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    if isinstance(x, np.generic):
        return x.item()
    return x


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--output", type=Path, default=None)
    a = ap.parse_args()
    out = clean(compute(a.root.resolve()))
    path = a.output or (a.root / PKG_REL / "RESULTS/AXIS_DIAGNOSTICS.json")
    path.write_text(json.dumps(out, indent=1, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({m: {"p": {b: round(v["D1_block_wald"][b]["p"], 6) for b in BLOCKS}, "fw": v["D5_alignment"]["familywise_16"]}
                      for m, v in out["variants"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
