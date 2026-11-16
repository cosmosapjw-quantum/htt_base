#!/usr/bin/env python3
"""R54-L05: CF4 apparent-Hubble multipoles at catalogue level, from committed files only.

Inputs (all committed; hashes are bound to the R36-01 result):
  docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz   35970 CF4 groups
  R36-01-CF4-OPERATOR/audit_backup/derived/A_RAW_36x35970.npz                             R36 linear operator
  tests/fixtures/r54/planck18_linear_pk_z0.csv                                            linear P(k)

What it does
  S1  rebuilds the R36 linear operator from the source rows (parity gate) and builds the unbiased
      log-distance operators (R54-EQ-34): all methods, method/hemisphere zero-point split,
      per-method global fits, declination jackknives;
  S2  exact linear-LCDM body O C_uu O^T by a chunked pair sum over all 35970^2 pairs (R54-EQ-30/31),
      linear and damped variants; the result is cached in RESULTS/R54_L05_COSMIC_COV.npz;
  S3  R36 linear estimator with the exact body, and its same-estimator errors-in-variables null;
  S4  log-distance estimator with the exact body: nulls, depth laws (V: 1/d, A: constant), pole
      decomposition, axis locking with a null law drawn from the exact body;
  S5  cross-indicator common-mode test of the fractional dipole (FP, TF, SN, OTHER) with the exact
      cross-covariance; a physical dipole or a flow is common to all indicators, a calibration term is not;
  S6  method/hemisphere zero-point split, declination jackknives, injection power checks, decision.

Claim ceiling C0. Linear theory at z = 0, redshift-space positions, no selection or Malmquist model,
no calibration covariance between objects; see "limitations" in the output.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
import time
from pathlib import Path

import numpy as np
import scipy
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "htt", ROOT / "htt/src", ROOT, ROOT / "scripts/r54"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from htt.htt.infer import r54_distance_estimators as de  # noqa: E402
from htt.htt.infer import r54_lcdm_body as lb  # noqa: E402
from htt.htt.infer import r54_survey as sv  # noqa: E402
from htt.htt.infer import r54_tensor_five_view as fv  # noqa: E402
import run_r54_lowz_frames as lz  # noqa: E402  (analysis functions and the single definition of the frame constants)

PUB = ROOT / "docs/research_program/observational_publication_20261015"
R36 = PUB / "OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-01-CF4-OPERATOR"
SRC = ROOT / "docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
OPF = R36 / "audit_backup/derived/A_RAW_36x35970.npz"
R36_RESULT = R36 / "RESULT.json"
PK = ROOT / "tests/fixtures/r54/planck18_linear_pk_z0.csv"
OUT_DIR = PUB / "R54_TENSOR_FRAME_TOMOGRAPHY_20261116/RESULTS"
OUT = OUT_DIR / "R54_L05_CF4_EXACT.json"
COV = OUT_DIR / "R54_L05_COSMIC_COV.npz"
IDEAL = OUT_DIR / "R54_L5_LOWZ_FRAMES.json"

CENTERS, WIDTH, SIGMA_STAR = (0.025, 0.04, 0.06, 0.08), 0.012, 250.0
H_FID, OMEGA_M = 67.36, 0.3153                     # fiducial of the P(k) fixture (positions and growth)
DAMPING_MPC = 13.0 / 0.6736                        # sinc damping scale sigma_u = 13 h^-1 Mpc (variant)
METHODS = ("FP", "OTHER", "SN", "TF")
Z_COMMON = (0.01, 0.055)                           # every family has objects in both hemispheres here
Z_BINS = (0.01, 0.02, 0.03, 0.04, 0.055)
SEED, N_NULL, N_INJ, N_EIV = 20261116, 4000, 1000, 400
N_SCAN_AXES, N_SCAN_NULL, MIN_SIDE = 150, 200000, 50   # hemisphere-step scan: axes, null draws, minimum objects of a family per side
SCAN = OUT_DIR / "R54_L05_STEP_SCAN_COV.npz"
STEP_MAG, FLOW_KM_S, FLOW_L_B = 0.05, 300.0, (298.0, -8.0)
GAIN_99_2DOF = float(stats.chi2.ppf(0.99, 2))      # 9.21 = 99% point of chi2 with 2 dof, threshold of the decision rule
RENAME = {"km_s_Mpc_icrs": "fraction_icrs", "amplitude_km_s_Mpc": "amplitude_fraction", "A_km_s_Mpc_icrs": "A_fraction_icrs",
          "dH_dipole_km_s_Mpc": "dipole_fraction", "axisymmetric_quadrupole_km_s_Mpc": "axisymmetric_quadrupole_fraction",
          "q_km_s_Mpc": "kappa_fraction"}


def as_fraction(obj):
    """Rename unit-bearing keys of analyse_window_multipoles for the dimensionless log estimator."""
    if isinstance(obj, dict):
        return {RENAME.get(k, k): as_fraction(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [as_fraction(v) for v in obj]
    return obj


def load() -> dict:
    res = json.loads(R36_RESULT.read_text())
    if lz.sha256(SRC) != res["source_sha256"] or lz.sha256(OPF) != res["artifact_sha256"]:
        raise SystemExit("committed CF4 source or operator does not match the R36-01 result binding")
    with np.load(SRC, allow_pickle=False) as z:
        cat = {k: z[k].copy() for k in ("z_CMB", "dmzp", "e_dmzp", "n_J2000", "method_family", "group_id")}
    with np.load(OPF, allow_pickle=False) as z:
        a_raw, cov36, theta36 = z["A_raw"].copy(), z["covariance36"].copy(), z["theta36"].copy()
    if not np.array_equal(np.load(OPF, allow_pickle=False)["group_id"], cat["group_id"]):
        raise SystemExit("operator and source rows are not in the same order")
    if set(np.unique(cat["method_family"])) != set(METHODS):
        raise SystemExit("unexpected method families")
    theta_ref = np.asarray(res["theta4x9"], float).ravel()
    return {"cat": cat, "a_raw": a_raw, "cov36": cov36, "theta36": theta36, "theta_ref": theta_ref}


def build_operators(cat: dict, a_raw: np.ndarray, tau2: np.ndarray, survey: dict | None = None) -> tuple[dict, np.ndarray]:
    """Window and step operators of the cloud run. With ``survey`` (R54-L04: {"labels": pooled survey label per group,
    "raw_labels": unpooled labels, "min_side": groups per hemisphere}) the survey-resolved operators are added under new
    names; the existing operators are unchanged. The row order of the survey operators is written back into ``survey``."""
    z, n, meth = cat["z_CMB"], cat["n_J2000"], cat["method_family"]
    dec = np.degrees(np.arcsin(np.clip(n[:, 2], -1.0, 1.0)))
    ind = {m: (meth == m).astype(float) for m in METHODS}
    step = np.where(dec >= 0.0, 1.0, -1.0)
    nuisance = np.column_stack([ind[m] for m in ("FP", "SN", "TF")] + [ind[m] * step for m in METHODS])
    ops = {"lin": a_raw,
           "log": de.log_window_operator(tau2, z, n, CENTERS, WIDTH),
           "log_split": de.log_window_operator(tau2, z, n, CENTERS, WIDTH, nuisance=nuisance),
           "log_mono": de.log_window_operator(tau2, z, n, CENTERS, WIDTH, nuisance=nuisance[:, :3])}
    base = de.multipole_basis(n)
    zbin = np.digitize(z, Z_BINS[1:-1])
    mono = np.column_stack([(zbin == b).astype(float) for b in range(len(Z_BINS) - 1)])
    in_range = (z >= Z_COMMON[0]) & (z < Z_COMMON[1])
    design = np.column_stack((mono, base[:, 1:]))
    ops["log_method"] = np.concatenate([de.wls_operator(design, (in_range & (meth == m)) / tau2)[mono.shape[1]:] for m in METHODS], axis=0)
    step_design = np.column_stack((mono, step))
    ops["method_step"] = np.stack([de.wls_operator(step_design, (in_range & (meth == m)) / tau2)[mono.shape[1]] for m in METHODS])
    for tag, sel in (("jk_no_equator", np.abs(dec) >= 10.0), ("jk_no_north_cap", dec <= 60.0), ("jk_no_south_cap", dec >= -60.0)):
        ops[tag] = de.log_window_operator(tau2, z, n, CENTERS, WIDTH, select=sel)
    if survey is not None:
        ops.update(survey_operators(cat, tau2, survey, nuisance[:, :3], dec, in_range))
    return ops, dec


def survey_operators(cat: dict, tau2: np.ndarray, survey: dict, mono_nuisance: np.ndarray, dec: np.ndarray, in_range: np.ndarray) -> dict:
    """R54-L04 steps 4, 5 and 8: survey steps, survey offsets, log_survey and the three log_mono + one-column variants."""
    z, n, meth = cat["z_CMB"], cat["n_J2000"], cat["method_family"]
    lab, raw = np.asarray(survey["labels"]), np.asarray(survey["raw_labels"])
    north = dec >= 0.0
    ops, layout = {}, {}

    def steps(name: str, sel: np.ndarray) -> None:
        eligible = [s for s in np.unique(lab) if min(int(np.sum(sel & (lab == s) & north)), int(np.sum(sel & (lab == s) & ~north))) >= survey["min_side"]]
        if eligible:
            ops[name] = np.stack([sv.survey_step_operator(z, n, tau2, sel & (lab == s), Z_BINS) for s in eligible])
        layout[name] = eligible

    def offsets(name: str, sel: np.ndarray) -> None:
        rows, names = [], []
        for fam in METHODS:
            fs = sel & (meth == fam)
            members = [s for s in np.unique(lab[fs]) if int(np.sum(fs & (lab == s))) > 0]
            if len(members) < 2:
                continue
            ref = max(members, key=lambda s: int(np.sum(fs & (lab == s))))
            others = [s for s in members if s != ref]
            rows.append(sv.survey_offset_operator(z, tau2, lab, fs, ref, others, Z_BINS))
            names += [f"{s}-{ref}" for s in others]
        if rows:
            ops[name] = np.concatenate(rows, axis=0)
        layout[name] = names

    steps("survey_step", in_range)
    offsets("survey_offsets", in_range)
    terc = np.quantile(cat["e_dmzp"][in_range], [1.0 / 3.0, 2.0 / 3.0])
    zmid = 0.5 * (Z_COMMON[0] + Z_COMMON[1])
    splits = {"e_tercile_1": in_range & (cat["e_dmzp"] < terc[0]), "e_tercile_2": in_range & (cat["e_dmzp"] >= terc[0]) & (cat["e_dmzp"] < terc[1]),
              "e_tercile_3": in_range & (cat["e_dmzp"] >= terc[1]), "z_low_half": in_range & (z < zmid), "z_high_half": in_range & (z >= zmid)}
    for tag, sel in splits.items():
        steps(f"survey_step_{tag}", sel)
        offsets(f"survey_offsets_{tag}", sel)
    ref_label = "OTHER_ALL"
    cols = [(lab == s).astype(float) for s in np.unique(lab) if s != ref_label]
    ops["log_survey"] = de.log_window_operator(tau2, z, n, CENTERS, WIDTH, nuisance=np.column_stack(cols))
    g = n @ lz.R_I2G.T                                                      # Galactic unit vectors (R_I2G defined once in run_r54_lowz_frames)
    extra = {"log_mono_radial": z, "log_mono_galactic": np.abs(g[:, 2]), "log_mono_error": (de.LN10_OVER_5 * cat["e_dmzp"]) ** 2}
    for name, col in extra.items():
        ops[name] = de.log_window_operator(tau2, z, n, CENTERS, WIDTH, nuisance=np.column_stack([mono_nuisance, col]))
    keep = ~np.isin(raw, ["FP_NOT_SDSS", "FP_MIXED"])
    ops["log_mono_no_6dfgs_proxy"] = de.log_window_operator(tau2, z, n, CENTERS, WIDTH, nuisance=mono_nuisance, select=keep)
    survey["layout"] = layout
    survey["splits"] = {k: int(v.sum()) for k, v in splits.items()}
    survey["e_terciles"] = terc.tolist()
    return ops


#: False inside tests: a cache miss then fails instead of rewriting a committed pair-sum file (R54-IR-04)
CACHE_WRITE = True


def _digest(*arrays: np.ndarray) -> str:
    h = hashlib.sha256()
    for a in arrays:
        a = np.ascontiguousarray(np.asarray(a, dtype=np.float64))
        h.update(str(a.shape).encode())
        h.update(a.tobytes())
    return h.hexdigest()


def operator_fingerprint(stack: np.ndarray) -> np.ndarray:
    """sha256 of the operator stack bytes and shape: changes under any row permutation or value change (R54-IR-03)."""
    return np.array(_digest(stack))


def model_key(n: np.ndarray | None = None, r: np.ndarray | None = None, r_grid: np.ndarray | None = None) -> str:
    """Everything besides the operator that fixes a pair sum: P(k) fixture, fiducial constants, growth rate, damping scale,
    the body module source, and (when given) the directions, positions and kernel table grid (R54-IR-03)."""
    key = (f"pk={lz.sha256(PK)}|H={H_FID}|Om={OMEGA_M}|f={lb.growth_rate(OMEGA_M):.15g}|damping_mpc={DAMPING_MPC:.12g}"
           f"|body_module={lz.sha256(Path(lb.__file__))}|linear_z0_redshift_space_positions")
    if n is not None:
        key += f"|geometry={_digest(n, r, r_grid)}"
    return key


def cache_matches(z, fp: np.ndarray, n_rows: int, key: str) -> bool:
    return ("model_key" in z.files and str(z["model_key"]) == key and str(z["operator_fingerprint"]) == str(fp)
            and int(z["n_rows"]) == n_rows)


def cache_miss(path: Path) -> None:
    if not CACHE_WRITE:
        raise SystemExit(f"pair-sum cache {path.name} does not match the operator or model in read-only mode")


def cosmic_covariances(stack: np.ndarray, labels: list[str], n: np.ndarray, r: np.ndarray, path: Path = COV, damped: bool = True) -> dict:
    """Pair-sum body O C_uu O^T (linear and, when ``damped``, the sinc-damped variant), cached in ``path`` (R54-L04 passes its own file)."""
    fp = operator_fingerprint(stack)
    grid = np.linspace(0.0, 2.0 * float(r.max()) * 1.001, 4001)
    key = model_key(n, r, grid)
    if path.is_file():
        with np.load(path, allow_pickle=False) as z:
            if list(z["labels"]) == labels and cache_matches(z, fp, stack.shape[0], key) and ("cosmic_damped" in z.files or not damped):
                return {"linear": z["cosmic_linear"].copy(), "damped": z["cosmic_damped"].copy() if damped else None, "psi0": float(z["psi0"]),
                        "psi0_damped": float(z["psi0_damped"]) if damped else None, "cached": True, "seconds": 0.0}
    cache_miss(path)
    tab = np.loadtxt(PK, delimiter=",", skiprows=1)
    f_growth = lb.growth_rate(OMEGA_M)
    t0 = time.time()
    lin = lb.velocity_correlation(tab[:, 0], tab[:, 1], f_growth, H_FID, grid)
    if damped:
        dmp = lb.velocity_correlation(tab[:, 0], tab[:, 1], f_growth, H_FID, grid, damping_mpc=DAMPING_MPC)
        m_lin, m_dmp = lb.radial_velocity_covariance_product(stack, n, r, grid, [lin, dmp])
    else:
        dmp, m_dmp = None, None
        m_lin = lb.radial_velocity_covariance_product(stack, n, r, grid, [lin])[0]
    seconds = time.time() - t0
    path.parent.mkdir(parents=True, exist_ok=True)
    extra = {"cosmic_damped": m_dmp, "psi0_damped": dmp[0][0]} if damped else {}
    np.savez_compressed(path, labels=np.array(labels), cosmic_linear=m_lin, operator_fingerprint=fp, psi0=lin[0][0], r_grid_max_mpc=grid[-1],
                        model_key=np.array(key), n_rows=stack.shape[0], **extra)
    return {"linear": m_lin, "damped": m_dmp, "psi0": float(lin[0][0]), "psi0_damped": float(dmp[0][0]) if damped else None,
            "cached": False, "seconds": seconds}


def block(mat: np.ndarray, sl: slice) -> np.ndarray:
    return mat[sl, sl]


def pole_decomposition(theta: np.ndarray, cov: np.ndarray, an: np.ndarray) -> dict:
    """Components of the constant (A) and velocity (V) dipole terms parallel and perpendicular to the celestial pole."""
    dip = lz.block_rows("dipole")
    y, c = theta[dip], cov[np.ix_(dip, dip)]
    a_const = np.tile(np.eye(3), (4, 1))

    def comp(est: np.ndarray, cv: np.ndarray) -> dict:
        perp, cperp = est[:2], cv[:2, :2]
        chi2 = float(perp @ np.linalg.solve(cperp, perp))
        return {"parallel": float(est[2]), "parallel_sd": float(math.sqrt(cv[2, 2])), "parallel_z_score": float(est[2] / math.sqrt(cv[2, 2])),
                "perpendicular": perp, "perpendicular_chi2_2dof": chi2, "perpendicular_p_value": float(stats.chi2.sf(chi2, 2))}

    fa, fv_, fva = fv.gls_fit(y, c, a_const), fv.gls_fit(y, c, an[dip]), fv.gls_fit(y, c, np.hstack([an[dip], a_const]))
    return {"A_only": comp(fa["theta"], fa["cov"]), "V_only": comp(fv_["theta"], fv_["cov"]),
            "V_plus_A": {"V": comp(fva["theta"][:3], fva["cov"][:3, :3]), "A": comp(fva["theta"][3:], fva["cov"][3:, 3:])},
            "units": "A in units of theta (fraction of H for the log estimator); V in km/s; ICRS z = celestial north"}


class AxisScan:
    """Vectorised gain of the two-parameter axis template over a fixed grid of axes (same statistic for data and null)."""

    def __init__(self, cov_dq: np.ndarray, n_grid: int = 4000) -> None:
        self.ci = np.linalg.inv(cov_dq)
        self.grid = fv.fibonacci_sphere(n_grid)
        jn = np.stack([lz.axis_template(ax) for ax in self.grid])
        self.pn = np.einsum("ij,gjk->gik", self.ci, jn)
        self.finv = np.linalg.inv(np.einsum("gik,gil->gkl", jn, self.pn))
        pole = lz.AXES_ICRS["equatorial_pole"]
        jp = lz.axis_template(pole)
        self.pp = self.ci @ jp
        self.fpinv = np.linalg.inv(jp.T @ self.pp)
        self.pole_angle = np.degrees(np.arccos(np.clip(np.abs(self.grid @ pole), 0.0, 1.0)))

    def stats(self, ys: np.ndarray) -> dict:
        t = np.einsum("gik,mi->mgk", self.pn, ys)
        gains = np.einsum("mgk,gkl,mgl->mg", t, self.finv, t)
        tp = ys @ self.pp
        gp = np.einsum("mk,kl,ml->m", tp, self.fpinv, tp)
        best = np.argmax(gains, axis=1)
        return {"gain_pole": gp, "sky_fraction": (gains >= gp[:, None]).mean(axis=1), "best_angle": self.pole_angle[best],
                "best_gain": gains.max(axis=1)}


def locking_null(theta: np.ndarray, cov: np.ndarray, rng: np.random.Generator, n_draw: int) -> dict:
    dq = np.sort(np.concatenate([lz.block_rows("dipole"), lz.block_rows("quadrupole")]))
    c = cov[np.ix_(dq, dq)]
    scan = AxisScan(c)
    obs = {k: float(v[0]) for k, v in scan.stats(theta[dq][None, :]).items()}
    chol = np.linalg.cholesky(c)
    null = {k: [] for k in obs}
    for a in range(0, n_draw, 250):
        res = scan.stats(rng.standard_normal((min(250, n_draw - a), dq.size)) @ chol.T)
        for k in null:
            null[k].append(res[k])
    null = {k: np.concatenate(v) for k, v in null.items()}

    def lower(k: str) -> float:
        return float((1 + np.sum(null[k] <= obs[k])) / (n_draw + 1))

    def upper(k: str) -> float:
        return float((1 + np.sum(null[k] >= obs[k])) / (n_draw + 1))

    return {"statistic": "grid of 4000 axes; identical statistic for data and null draws", "n_null_draws": n_draw,
            "law": "Gaussian draws from white + exact linear LCDM body (dipole and quadrupole rows, 32)",
            "observed": obs,
            "tails": {"gain_pole_chi2_2dof": float(stats.chi2.sf(obs["gain_pole"], 2)), "gain_pole_empirical": upper("gain_pole"),
                      "sky_fraction_at_most_observed": lower("sky_fraction"), "best_axis_angle_at_most_observed": lower("best_angle"),
                      "best_gain_at_least_observed": upper("best_gain")},
            "null_summary": {"mean_gain_pole": float(null["gain_pole"].mean()), "median_best_axis_angle_deg": float(np.median(null["best_angle"])),
                             "fraction_best_axis_within_10deg_of_pole": float(np.mean(null["best_angle"] <= 10.0)),
                             "isotropic_fraction_within_10deg": float(1.0 - math.cos(math.radians(10.0))),
                             "median_sky_fraction": float(np.median(null["sky_fraction"])),
                             "sky_fraction_quantile_0p01": float(np.quantile(null["sky_fraction"], 0.01))}}


def common_mode(theta: np.ndarray, white: np.ndarray, body: np.ndarray) -> dict:
    """Per-method fractional dipoles (rows 8m..8m+2) and their consistency with one common vector."""
    drows = np.array([8 * m + k for m in range(4) for k in range(3)])
    qrows = np.array([8 * m + k for m in range(4) for k in range(3, 8)])
    y, yq = theta[drows], theta[qrows]
    out = {"z_range": list(Z_COMMON), "monopole_bins": list(Z_BINS), "methods": list(METHODS),
           "convention": "delta points toward higher apparent Hubble rate; Delta mu = -(5/ln10) delta.n"}
    for tag, cov in (("white", white), ("white_plus_exact_body", white + body)):
        c, cq = cov[np.ix_(drows, drows)], cov[np.ix_(qrows, qrows)]
        per = {}
        for i, m in enumerate(METHODS):
            b, cb = y[3 * i:3 * i + 3], c[3 * i:3 * i + 3, 3 * i:3 * i + 3]
            w = float(b @ np.linalg.solve(cb, b))
            per[m] = {"delta": b, "sd": np.sqrt(np.diag(cb)), "wald_3dof": w, "p_value": float(stats.chi2.sf(w, 3)),
                      "amplitude_percent": 100.0 * float(np.linalg.norm(b)), "equivalent_mag": de.magnitude_equivalent(float(np.linalg.norm(b))),
                      "direction_l_b_deg": lz.icrs_to_lb(b), "pole_component": float(b[2]), "pole_component_sd": float(math.sqrt(cb[2, 2])),
                      "angle_to_equatorial_pole_axis_deg": lz.angle_deg(b, lz.AXES_ICRS["equatorial_pole"], axis=True)}
        fit = fv.gls_fit(y, c, np.tile(np.eye(3), (4, 1)))
        zrows = np.array([2, 5, 8, 11])
        fz = fv.gls_fit(y[zrows], c[np.ix_(zrows, zrows)], np.ones((4, 1)))
        fq = fv.gls_fit(yq, cq, np.tile(np.eye(5), (4, 1)))
        loo = {}
        for i, m in enumerate(METHODS):
            rest = np.array([k for k in range(12) if k // 3 != i])
            fr = fv.gls_fit(y[rest], c[np.ix_(rest, rest)], np.tile(np.eye(3), (3, 1)))
            cross = c[np.ix_(np.arange(3 * i, 3 * i + 3), rest)]
            h = np.tile(np.eye(3), (3, 1))
            k_est = fr["cov"] @ h.T @ np.linalg.inv(c[np.ix_(rest, rest)])     # GLS estimator of the common vector from the other methods
            diff = y[3 * i:3 * i + 3] - fr["theta"]
            cdiff = c[3 * i:3 * i + 3, 3 * i:3 * i + 3] + fr["cov"] - cross @ k_est.T - k_est @ cross.T
            chi2 = float(diff @ np.linalg.solve(cdiff, diff))
            loo[m] = {"difference_from_common_of_others": diff, "chi2_3dof": chi2, "p_value": float(stats.chi2.sf(chi2, 3))}
        sd = np.sqrt(np.diag(c))
        out[tag] = {"per_method": per,
                    "common_dipole": {"delta": fit["theta"], "sd": np.sqrt(np.diag(fit["cov"])), "wald_3dof": fit["wald"],
                                      "wald_p_value": float(stats.chi2.sf(fit["wald"], 3)), "amplitude_percent": 100.0 * float(np.linalg.norm(fit["theta"])),
                                      "equivalent_mag": de.magnitude_equivalent(float(np.linalg.norm(fit["theta"]))),
                                      "direction_l_b_deg": lz.icrs_to_lb(fit["theta"]),
                                      "angle_to_equatorial_pole_axis_deg": lz.angle_deg(fit["theta"], lz.AXES_ICRS["equatorial_pole"], axis=True),
                                      "consistency_chi2": fit["chi2"], "consistency_dof": fit["dof"], "consistency_p_value": fit["p_value"]},
                    "pole_component": {"common": float(fz["theta"][0]), "sd": float(math.sqrt(fz["cov"][0, 0])),
                                       "consistency_chi2": fz["chi2"], "consistency_dof": fz["dof"], "consistency_p_value": fz["p_value"]},
                    "common_quadrupole": {"kappa": fq["theta"], "sd": np.sqrt(np.diag(fq["cov"])), "wald_5dof": fq["wald"],
                                          "wald_p_value": float(stats.chi2.sf(fq["wald"], 5)), "consistency_chi2": fq["chi2"],
                                          "consistency_dof": fq["dof"], "consistency_p_value": fq["p_value"]},
                    "leave_one_method_out": loo,
                    "pole_component_correlation_between_methods": (c[np.ix_(zrows, zrows)] / np.outer(sd[zrows], sd[zrows]))}
    return out


def hemisphere_steps(theta: np.ndarray, white: np.ndarray, body: np.ndarray) -> dict:
    """Per-method hemisphere step s_m of eta (model eta = h_bin + s_m sign(dec)), z in Z_COMMON, with white and exact-body errors."""
    out = {"model": "eta = monopole per redshift bin + s_m * sign(declination), fitted per method family",
           "convention": "s > 0: apparent Hubble rate higher in the north; Delta mu (north - south) = -(5/ln10) * 2 s", "z_range": list(Z_COMMON)}
    for tag, cov in (("white", white), ("white_plus_exact_body", white + body)):
        sd = np.sqrt(np.diag(cov))
        fit = fv.gls_fit(theta, cov, np.ones((4, 1)))
        out[tag] = {"per_method": {m: {"step": float(theta[i]), "sd": float(sd[i]), "z_score": float(theta[i] / sd[i]),
                                       "delta_mu_north_minus_south_mag": float(-2.0 * theta[i] / de.LN10_OVER_5),
                                       "delta_mu_sd_mag": float(2.0 * sd[i] / de.LN10_OVER_5)} for i, m in enumerate(METHODS)},
                    "common_step": float(fit["theta"][0]), "common_step_sd": float(math.sqrt(fit["cov"][0, 0])),
                    "common_delta_mu_north_minus_south_mag": float(-2.0 * fit["theta"][0] / de.LN10_OVER_5),
                    "common_delta_mu_sd_mag": float(2.0 * math.sqrt(fit["cov"][0, 0]) / de.LN10_OVER_5),
                    "common_wald_p_value": float(stats.chi2.sf(fit["wald"], 1)),
                    "consistency_chi2": fit["chi2"], "consistency_dof": fit["dof"], "consistency_p_value": fit["p_value"],
                    "correlation": cov / np.outer(sd, sd)}
    return out


def window_subset_nulls(theta: np.ndarray, cov: np.ndarray) -> dict:
    """Nulls of the two inner and the two outer windows separately, and the dipole chi2 of every window."""
    def one(rows: list[int]) -> dict:
        chi2 = float(theta[rows] @ np.linalg.solve(cov[np.ix_(rows, rows)], theta[rows]))
        return {"chi2": chi2, "dof": len(rows), "p_value": float(stats.chi2.sf(chi2, len(rows)))}

    out = {}
    for tag, wins in (("inner_windows_z0.025_z0.04", (0, 1)), ("outer_windows_z0.06_z0.08", (2, 3))):
        dip = [9 * w + k for w in wins for k in (1, 2, 3)]
        quad = [9 * w + k for w in wins for k in (4, 5, 6, 7, 8)]
        out[tag] = {"dipole": one(dip), "quadrupole": one(quad), "joint": one(sorted(dip + quad))}
    out["dipole_chi2_per_window_3dof"] = [one([9 * w + 1, 9 * w + 2, 9 * w + 3])["chi2"] for w in range(4)]
    return out


def step_scan(cat: dict, eta: np.ndarray, g: np.ndarray, tau2: np.ndarray, r: np.ndarray, rng: np.random.Generator,
              reference: dict) -> dict:
    """Look-elsewhere and axis specificity of the hemisphere step: the sign(dec) split was chosen after the first pass.

    For every axis a of a fixed grid (celestial pole first) and every method family the step s of
    eta = redshift-bin monopoles + s sign(n.a) is fitted on Z_COMMON; the common step of an axis is the GLS mean of the four
    families with the white + exact-body covariance (pair sum restricted to the objects in Z_COMMON). The null law of the
    scan maximum is drawn from the exact covariance of the common steps across axes.
    """
    z, n, meth = cat["z_CMB"], cat["n_J2000"], cat["method_family"]
    pole = lz.AXES_ICRS["equatorial_pole"]
    sub = np.flatnonzero((z >= Z_COMMON[0]) & (z < Z_COMMON[1]))
    zbin = np.digitize(z[sub], Z_BINS[1:-1])
    mono = np.column_stack([(zbin == b).astype(float) for b in range(len(Z_BINS) - 1)])
    grid = fv.fibonacci_sphere(2 * N_SCAN_AXES)
    candidates = np.vstack([pole, grid[grid[:, 2] > 0.0]])
    rows, axes, dropped = [], [], 0
    for ax in candidates:
        sgn = np.where(n[sub] @ ax >= 0.0, 1.0, -1.0)
        if min(min(int(np.sum((meth[sub] == m) & (sgn > 0))), int(np.sum((meth[sub] == m) & (sgn < 0)))) for m in METHODS) < MIN_SIDE:
            dropped += 1
            continue
        design = np.column_stack((mono, sgn))
        try:
            rows.append(np.stack([de.wls_operator(design, (meth[sub] == m) / tau2[sub])[mono.shape[1]] for m in METHODS]))
        except ValueError:                       # step not identified for one family on this split
            dropped += 1
            continue
        axes.append(ax)
    axes, ops = np.asarray(axes), np.concatenate(rows, axis=0)
    if not np.array_equal(axes[0], pole):
        raise SystemExit("the celestial pole must be the first scan axis")
    vel = ops * g[sub][None, :]
    fp, body, cached = operator_fingerprint(vel), None, False
    rg = np.linspace(0.0, 2.0 * float(r.max()) * 1.001, 4001)                # same table grid as the full pair sum
    key = model_key(n[sub], r[sub], rg)
    if SCAN.is_file():
        with np.load(SCAN, allow_pickle=False) as c:
            if cache_matches(c, fp, vel.shape[0], key) and c["axes_icrs"].shape == axes.shape and np.array_equal(c["axes_icrs"], axes):
                body, cached = c["body"].copy(), True
    if body is None:
        cache_miss(SCAN)
        tab = np.loadtxt(PK, delimiter=",", skiprows=1)
        lin = lb.velocity_correlation(tab[:, 0], tab[:, 1], lb.growth_rate(OMEGA_M), H_FID, rg)
        body = lb.radial_velocity_covariance_product(vel, n[sub], r[sub], rg, [lin])[0]
        np.savez_compressed(SCAN, body=body, operator_fingerprint=fp, model_key=np.array(key), n_rows=vel.shape[0], axes_icrs=axes)
    theta = ops @ eta[sub]
    total = de.white_covariance(ops, tau2[sub]) + body
    na = axes.shape[0]
    weights = np.zeros((na, 4 * na))
    for a in range(na):
        sl = slice(4 * a, 4 * a + 4)
        ci1 = np.linalg.solve(total[sl, sl], np.ones(4))
        weights[a, sl] = ci1 / ci1.sum()
    common = weights @ theta
    cov_c = weights @ total @ weights.T
    sd = np.sqrt(np.diag(cov_c))
    zsc = common / sd
    if abs(common[0] - reference["common_step"]) > 1e-9 or abs(sd[0] - reference["common_step_sd"]) > 1e-9:
        raise SystemExit("restricted pair sum does not reproduce the hemisphere step of the full pair sum")
    angle = np.degrees(np.arccos(np.clip(np.abs(axes @ pole), 0.0, 1.0)))
    best = int(np.argmax(np.abs(zsc)))
    vals, vecs = np.linalg.eigh(cov_c)
    root = vecs * np.sqrt(np.clip(vals, 0.0, None))
    max_null, angle_null = [], []
    for _ in range(N_SCAN_NULL // 20000):
        draws = np.abs((rng.standard_normal((20000, na)) @ root.T) / sd[None, :])
        k = np.argmax(draws, axis=1)
        max_null.append(draws[np.arange(20000), k])
        angle_null.append(angle[k])
    max_null, angle_null = np.concatenate(max_null), np.concatenate(angle_null)
    n_draw = max_null.size
    return {
        "grid": f"celestial pole plus the northern half of a {2 * N_SCAN_AXES}-point Fibonacci sphere; an axis is dropped if a family has fewer than {MIN_SIDE} objects on one side",
        "n_axes": int(na), "n_axes_dropped": int(dropped), "n_objects": int(sub.size), "n_null_draws": int(n_draw), "pair_sum_cached": cached,
        "law": "Gaussian draws with the white + exact-body covariance of the common steps across the axis grid",
        "pole": {"common_step": float(common[0]), "sd": float(sd[0]), "z_score": float(zsc[0]),
                 "rank_by_abs_z": int(1 + np.sum(np.abs(zsc) > abs(zsc[0])))},
        "best_axis": {"common_step": float(common[best]), "z_score": float(zsc[best]), "angle_to_pole_deg": float(angle[best]),
                      "l_b_deg": lz.icrs_to_lb(axes[best])},
        "tails": {"pole_single_axis_two_sided": float(2.0 * stats.norm.sf(abs(zsc[0]))),
                  "scan_max_at_least_pole_value": float((1 + np.sum(max_null >= abs(zsc[0]))) / (n_draw + 1)),
                  "scan_max_at_least_observed_max": float((1 + np.sum(max_null >= abs(zsc[best]))) / (n_draw + 1)),
                  "null_fraction_best_axis_within_10deg_of_pole": float(np.mean(angle_null <= 10.0)),
                  "grid_fraction_of_axes_within_10deg_of_pole": float(np.mean(angle <= 10.0))},
        "variance_ratio_best_single_family_to_common_at_pole": float((np.sqrt(np.diag(total[:4, :4])).min() / sd[0]) ** 2),
        "variance_ratio_note": "4 for four independent equal-weight families, 1 if the common step carries no more information than the best single family",
    }


def eiv_null(cat: dict, y_flrw: np.ndarray, h_ref: float, rng: np.random.Generator, n_mock: int) -> tuple[np.ndarray, np.ndarray]:
    """Same-estimator null of the R36 linear estimator: FLRW distances at the observed redshifts, Gaussian
    distance-modulus errors, white velocity noise; mean = estimator bias (errors in variables + cosmography)."""
    z, emu, n = cat["z_CMB"], cat["e_dmzp"], cat["n_J2000"]
    mu_true = 5.0 * np.log10(y_flrw / h_ref) + 25.0
    out = np.empty((n_mock, 36))
    for m in range(n_mock):
        mu_m = mu_true + emu * rng.standard_normal(z.size)
        y_m = de.C_KM_S * z + SIGMA_STAR * rng.standard_normal(z.size)
        out[m] = de.r36_linear_window_operator(mu_m, emu, z, n, CENTERS, WIDTH, SIGMA_STAR) @ y_m
    return out.mean(axis=0), np.cov(out, rowvar=False, ddof=1)


def model_chi2_many(ys: np.ndarray, ci: np.ndarray, design: np.ndarray) -> np.ndarray:
    t = ys @ (ci @ design)
    finv = np.linalg.inv(design.T @ ci @ design)
    return np.einsum("mi,ij,mj->m", ys, ci, ys) - np.einsum("mk,kl,ml->m", t, finv, t)


def injections(a_log: np.ndarray, cov: np.ndarray, an: np.ndarray, cat: dict, g: np.ndarray, dec: np.ndarray,
               rng: np.random.Generator, n_draw: int, observed_step_mag: float, observed_flow_km_s: float, lock_q01: float) -> dict:
    """Classification power on the real footprint: theta = O d_eta + noise with the total covariance (the estimator is linear).

    ``lock_q01`` is the 1% quantile of the null sky fraction of the same operator, so that
    ``fraction_pole_locked_flag`` is the rate at which the decision flag pole_locked (calibrated tail < 0.01) fires.
    """
    dip = lz.block_rows("dipole")
    dq = np.sort(np.concatenate([dip, lz.block_rows("quadrupole")]))
    pos = {int(row): i for i, row in enumerate(dq)}
    dip_in_dq = np.array([pos[int(row)] for row in dip])
    c = cov[np.ix_(dq, dq)]
    cd_inv = np.linalg.inv(cov[np.ix_(dip, dip)])
    scan, chol = AxisScan(c), np.linalg.cholesky(c)
    v_unit = cat["n_J2000"] @ (lz.R_I2G.T @ lz.gal_unit(*FLOW_L_B))
    unit_step = -de.LN10_OVER_5 * np.where(dec >= 0.0, 1.0, -1.0)          # eta shift per mag of +north / -south modulus offset
    d_step, d_flow = STEP_MAG * unit_step, FLOW_KM_S * g * v_unit
    cases = {"hemisphere_zero_point_step": d_step, "bulk_flow": d_flow, "step_plus_flow": d_step + d_flow, "none": np.zeros_like(d_step),
             "hemisphere_step_observed_size": observed_step_mag * unit_step, "bulk_flow_observed_size": observed_flow_km_s * g * v_unit}
    a_const = np.tile(np.eye(3), (4, 1))
    out = {"step_mag": STEP_MAG, "flow_km_s": FLOW_KM_S, "flow_l_b_deg": list(FLOW_L_B), "n_draws": n_draw,
           "observed_size": {"step_mag": observed_step_mag, "flow_km_s": observed_flow_km_s,
                             "note": "half of the fitted common north-south modulus difference and the fitted bulk-only amplitude; data-derived amplitudes"},
           "law": "white + exact linear LCDM body", "gain_threshold": GAIN_99_2DOF, "pole_locked_sky_fraction_threshold": lock_q01, "cases": {}}
    for name, d_eta in cases.items():
        mean = (a_log @ d_eta)[dq]
        ys = mean[None, :] + rng.standard_normal((n_draw, dq.size)) @ chol.T
        st = scan.stats(ys)
        yd = ys[:, dip_in_dq]
        chi_v, chi_a = model_chi2_many(yd, cd_inv, an[dip]), model_chi2_many(yd, cd_inv, a_const)
        out["cases"][name] = {
            "noise_free_pole_gain": float(scan.stats(mean[None, :])["gain_pole"][0]),
            "fraction_A_law_preferred": float(np.mean(chi_a < chi_v)),
            "median_chi2_V_minus_chi2_A": float(np.median(chi_v - chi_a)),
            "fraction_pole_gain_above_threshold": float(np.mean(st["gain_pole"] >= GAIN_99_2DOF)),
            "median_best_axis_angle_to_pole_deg": float(np.median(st["best_angle"])),
            "fraction_best_axis_within_10deg_of_pole": float(np.mean(st["best_angle"] <= 10.0)),
            "fraction_sky_fraction_below_0p01": float(np.mean(st["sky_fraction"] <= 0.01)),
            "fraction_pole_locked_flag": float(np.mean(st["sky_fraction"] <= lock_q01))}
    return out


def tilt_closure(v: np.ndarray, cv: np.ndarray, b: np.ndarray, sb: np.ndarray) -> float:
    """chi2 (3 dof) of V_CF4 + c beta_excess = 0 (R54-EQ-38): v in km/s with covariance cv, b = c beta_excess in km/s with sd sb."""
    s, cs = v + b, cv + np.diag(sb**2)
    return float(s @ np.linalg.solve(cs, s))


def tilt_transport(theta: np.ndarray, cov: np.ndarray, an: np.ndarray) -> dict:
    """Global-tilt transport between depths (R52 frame algebra): with beta_RM = v_R - v_M one frame offset at all depths
    gives CF4 bulk V = v_M - v_R = -c beta_RM and count-dipole excess D/c_EB - beta_CMB = +beta_RM, hence V_CF4 + c beta_excess = 0."""
    counts = json.loads(IDEAL.read_text())["count_dipoles"]["common_excess_velocity"]
    b, sb = np.asarray(counts["beta_excess_km_s_icrs"], float), np.asarray(counts["sd_km_s"], float)
    dip = lz.block_rows("dipole")
    y, c = theta[dip], cov[np.ix_(dip, dip)]
    fits = {"V_only": fv.gls_fit(y, c, an[dip]), "V_with_constant_dipole_marginalised": fv.gls_fit(y, c, np.hstack([an[dip], np.tile(np.eye(3), (4, 1))]))}
    out = {"prediction": "V_CF4 + c beta_excess(counts) = 0 for one matter-radiation frame offset at all depths",
           "count_excess_velocity_km_s_icrs": b, "count_excess_sd_km_s": sb, "count_excess_wald_p": counts["wald_p_value"],
           "status": "PRELIMINARY: the count side is the receipt estimator without a clustering body or a same-estimator null (R54-L03)"}
    for name, fit in fits.items():
        v, cv = fit["theta"][:3], fit["cov"][:3, :3]
        chi2 = tilt_closure(v, cv, b, sb)
        wv = float(v @ np.linalg.solve(cv, v))
        out[name] = {"V_km_s_icrs": v, "V_sd_km_s": np.sqrt(np.diag(cv)), "V_amplitude_km_s": float(np.linalg.norm(v)),
                     "V_direction_l_b_deg": lz.icrs_to_lb(v), "V_wald_3dof": wv, "V_wald_p_value": float(stats.chi2.sf(wv, 3)),
                     "tilt_closure_chi2_3dof": chi2, "tilt_closure_p_value": float(stats.chi2.sf(chi2, 3))}
    return out


def window_summary(theta: np.ndarray, cov: np.ndarray, white: np.ndarray) -> dict:
    t, sd, sdw = theta.reshape(4, 9), np.sqrt(np.diag(cov)).reshape(4, 9), np.sqrt(np.diag(white)).reshape(4, 9)
    return {"window_centers_z": list(CENTERS), "monopole": t[:, 0], "dipole": t[:, 1:4], "quadrupole": t[:, 4:],
            "dipole_sd_total": sd[:, 1:4], "dipole_sd_white": sdw[:, 1:4], "monopole_sd_total": sd[:, 0]}


def headline_of(res: dict, frac: bool) -> dict:
    a_key = "fraction_icrs" if frac else "km_s_Mpc_icrs"
    d, q, lock = res["dipole"], res["quadrupole"], res["axis_locking"]
    return {"dipole_null_chi2": d["null"]["statistic"], "dipole_null_p": d["null"]["p_value"],
            "quadrupole_null_chi2": q["null"]["statistic"], "quadrupole_null_p": q["null"]["p_value"],
            "joint_null_chi2": lock["null_chi2"], "joint_null_p": lock["null_p_value"],
            "chi2_V": d["models"]["V_constant_velocity"]["chi2"], "chi2_A": d["models"]["A_constant_dH"]["chi2"],
            "chi2_V_plus_A": d["models"]["V_plus_A"]["chi2"],
            "A_only": d["A_only"][a_key], "A_percent": d["A_only"]["percent_of_H"], "A_equivalent_mag": d["A_only"]["equivalent_mag"],
            "A_wald_p": d["A_only"]["wald_p_value"], "A_angle_to_pole_deg": d["A_only"]["angle_to_equatorial_pole_axis_deg"],
            "V_only_km_s": d["V_only"]["amplitude_km_s"], "V_only_l_b_deg": d["V_only"]["direction_l_b_deg"],
            "V_only_angle_to_watkins_deg": d["V_only"]["angle_to_watkins_2023_deg"],
            "V_wald_after_A": d["V_plus_A"]["V_wald_3dof"], "A_wald_after_V": d["V_plus_A"]["A_wald_3dof"],
            "pole_gain": lock["delta_chi2_at_reference_axes"]["equatorial_pole"],
            "reference_axis_gains": lock["delta_chi2_at_reference_axes"],
            "best_axis_gain": lock["best_axis"]["delta_chi2"], "best_axis_angle_to_pole_deg": lock["best_axis"]["angle_to_equatorial_pole_axis_deg"],
            "best_axis_l_b_deg": lock["best_axis"]["l_b_deg"], "sky_fraction": lock["sky_fraction_of_axes_with_gain_at_least_equatorial_pole"],
            "pole_fit_residual_p": lock["equatorial_pole_fit"]["residual_p_value"],
            "quadrupole_axis_angle_to_pole_deg": q["constant_tensor"]["principal_axis_angle_to_equatorial_pole_deg"],
            "quadrupole_constant_wald_5dof": q["constant_tensor"]["wald_5dof"],
            "quadrupole_constant_wald_p": float(stats.chi2.sf(q["constant_tensor"]["wald_5dof"], 5)),
            "quadrupole_constant_percent": q["constant_tensor"]["percent_of_H"]}


def classify(joint_p: float, removed: bool, tail: float) -> str:
    """Class rule of the cloud decision block (moved to module level unchanged for R54-L04)."""
    if joint_p >= 0.01:
        return "LCDM_BODY_COMPATIBLE"
    if removed:
        return "METHOD_HEMISPHERE_ZERO_POINT_TYPE"
    return "UNRESOLVED_POLE_LOCKED" if tail < 0.01 else "EXCESS_NOT_POLE_LOCKED"


def compute() -> dict:
    """Run every block and return the JSON-ready result (the pair sum is read from the cache when it matches)."""
    data = load()
    cat, a_raw = data["cat"], data["a_raw"]
    z, n, emu = cat["z_CMB"], cat["n_J2000"], cat["e_dmzp"]
    rng = np.random.default_rng(SEED)                 # same-estimator null of the linear estimator (first consumer, unchanged)

    def stream(tag: int) -> np.random.Generator:
        return np.random.default_rng([SEED, tag])

    # ---- S1 operators and parity
    rebuilt = de.r36_linear_window_operator(cat["dmzp"], emu, z, n, CENTERS, WIDTH, SIGMA_STAR)
    y_lin = de.C_KM_S * z
    parity = {"operator_max_abs_diff": float(np.abs(rebuilt - a_raw).max()), "operator_scale": float(np.abs(a_raw).max()),
              "theta_max_abs_diff_vs_R36_result": float(np.abs(a_raw @ y_lin - data["theta_ref"]).max()),
              "white_covariance_max_abs_diff": float(np.abs(de.white_covariance(a_raw, np.load(OPF, allow_pickle=False)["sigma"] ** 2) - data["cov36"]).max())}
    if parity["operator_max_abs_diff"] > 1e-12 * parity["operator_scale"] or parity["theta_max_abs_diff_vs_R36_result"] > 1e-8:
        raise SystemExit(f"R36 operator parity failed: {parity}")
    lr = de.log_distance_ratio(cat["dmzp"], z, OMEGA_M)
    eta, g = lr["eta"], lr["g_per_km_s"]
    tau2 = de.log_noise_variance(emu, g, SIGMA_STAR)
    ops, dec = build_operators(cat, a_raw, tau2)
    names = list(ops)
    offsets, labels, start = {}, [], 0
    for name in names:
        offsets[name] = slice(start, start + ops[name].shape[0])
        labels += [f"{name}:{i}" for i in range(ops[name].shape[0])]
        start += ops[name].shape[0]
    resp = {name: ((1.0 + z) if name == "lin" else g) for name in names}      # d(response)/du per object
    vel = np.concatenate([ops[name] * resp[name][None, :] for name in names], axis=0)

    # ---- S2 exact body
    r = de.C_KM_S / H_FID * lr["chi_hat"]
    cosmic = cosmic_covariances(vel, labels, n, r)
    body, body_d = cosmic["linear"], cosmic["damped"]
    an = {name: vel[offsets[name]] @ n for name in names}
    white = {name: de.white_covariance(ops[name], tau2) for name in names if name != "lin"}
    white["lin"] = data["cov36"]
    theta = {name: ops[name] @ (y_lin if name == "lin" else eta) for name in names}
    h_lin = float(np.mean(theta["lin"][0::9]))
    h_log = float(np.exp(np.mean(theta["log"][0::9])))

    # ---- S3 R36 linear estimator: exact body and same-estimator null
    law_lin = "R36 working measurement covariance + exact catalogue linear LCDM body"
    lin_res = lz.analyse_window_multipoles(theta["lin"], white["lin"] + block(body, offsets["lin"]), an["lin"], h_lin, law_lin)
    bias, cov_eiv = eiv_null(cat, lr["y_km_s"], h_log, rng, N_EIV)
    bias9 = bias.reshape(4, 9)
    lin_unb = lz.analyse_window_multipoles(theta["lin"] - bias, white["lin"] + block(body, offsets["lin"]), an["lin"], h_lin,
                                           law_lin + "; same-estimator bias subtracted")
    ideal = json.loads(IDEAL.read_text())["cf4"]["lcdm_body"]
    sd_exact = np.sqrt(np.diag(block(body, offsets["lin"]))).reshape(4, 9)
    linear_block = {
        "estimator": "R36/H03 linear-in-distance window fit of c z_CMB on d [1, n, STF5] (R54-EQ-35)",
        "H_fit_km_s_Mpc": h_lin, "windows": window_summary(theta["lin"], white["lin"] + block(body, offsets["lin"]), white["lin"]),
        "exact_body_sd": {"monopole": sd_exact[:, 0], "dipole_xyz": sd_exact[:, 1:4], "quadrupole": sd_exact[:, 4:]},
        "exact_over_ideal_sd": {"monopole": sd_exact[:, 0] / np.asarray(ideal["cosmic_sd_monopole_km_s_Mpc"]),
                                "dipole_xyz": sd_exact[:, 1:4] / np.asarray(ideal["cosmic_sd_dipole_km_s_Mpc"])[:, None],
                                "quadrupole_mean": sd_exact[:, 4:].mean(axis=1) / np.asarray(ideal["cosmic_sd_quadrupole_km_s_Mpc"])},
        "analysis_exact_body": lin_res, "headline": headline_of(lin_res, frac=False),
        "same_estimator_null": {
            "model": "FLRW luminosity distances at the observed redshifts (H_ref from the log estimator), Gaussian distance-modulus errors e_dmzp, "
                     "white velocity noise 250 km/s; estimator rebuilt for every draw",
            "n_mocks": N_EIV, "H_ref_km_s_Mpc": h_log, "bias_monopole_km_s_Mpc": bias9[:, 0] - h_log, "bias_dipole_km_s_Mpc": bias9[:, 1:4],
            "bias_quadrupole_km_s_Mpc": bias9[:, 4:], "observed_dipole_km_s_Mpc": theta["lin"].reshape(4, 9)[:, 1:4],
            "pole_dipole_fraction_explained_by_bias": bias9[:, 3] / theta["lin"].reshape(4, 9)[:, 3],
            "mock_over_working_sd_dipole": np.sqrt(np.diag(cov_eiv)).reshape(4, 9)[:, 1:4] / np.sqrt(np.diag(white["lin"])).reshape(4, 9)[:, 1:4],
            "analysis_bias_subtracted": lin_unb, "headline_bias_subtracted": headline_of(lin_unb, frac=False)},
    }

    # ---- S4 log-distance estimator with the exact body
    law_log = "white (distance-modulus error + 250 km/s) + exact catalogue linear LCDM body"
    cov_log = white["log"] + block(body, offsets["log"])
    log_res = as_fraction(lz.analyse_window_multipoles(theta["log"], cov_log, an["log"], 1.0, law_log, estimator="log"))
    log_white = as_fraction(lz.analyse_window_multipoles(theta["log"], white["log"], an["log"], 1.0, "white only (no cosmic body)", estimator="log"))
    lock_null = locking_null(theta["log"], cov_log, stream(1), N_NULL)
    sens = []
    for tag, mat, scale in (("linear x0.5", body, 0.5), ("linear x1", body, 1.0), ("linear x2", body, 2.0), ("damped x1", body_d, 1.0)):
        for sig in (150.0, 250.0, 350.0):
            cw = de.white_covariance(ops["log"], de.log_noise_variance(emu, g, sig))
            res = headline_of(as_fraction(lz.analyse_window_multipoles(theta["log"], cw + scale * block(mat, offsets["log"]), an["log"], 1.0, "variant", estimator="log")), True)
            sens.append({"body": tag, "sigma_star_km_s": sig, **{k: res[k] for k in ("dipole_null_p", "quadrupole_null_p", "joint_null_p", "chi2_V", "chi2_A",
                                                                                   "A_percent", "A_angle_to_pole_deg", "pole_gain", "sky_fraction",
                                                                                   "best_axis_angle_to_pole_deg", "pole_fit_residual_p")}})
    log_block = {
        "estimator": "log-distance ratio eta = ln[H0 d_L(z)/d] window fit on [1, n, STF5] (R54-EQ-34); unbiased under Gaussian distance-modulus errors",
        "theta_units": "h = ln H; dipole and quadrupole are fractions of the apparent Hubble rate",
        "H_window_km_s_Mpc": np.exp(theta["log"][0::9]), "windows": window_summary(theta["log"], cov_log, white["log"]),
        "analysis_exact_body": log_res, "headline": headline_of(log_res, True),
        "analysis_white_only": log_white, "headline_white_only": headline_of(log_white, True),
        "pole_decomposition": pole_decomposition(theta["log"], cov_log, an["log"]),
        "axis_locking_null": lock_null, "body_sensitivity": sens,
        "window_subsets": window_subset_nulls(theta["log"], cov_log),
        "tilt_transport": tilt_transport(theta["log"], cov_log, an["log"]),
        "carrier": {"row_order": "4 windows x [h, delta_x, delta_y, delta_z, kappa_1..5] (STF5_BASIS order), ICRS",
                    "theta": theta["log"], "covariance_white": white["log"], "covariance_body": block(body, offsets["log"]),
                    "velocity_response_per_km_s": an["log"]},
    }

    # ---- S5 cross-indicator common mode
    cm = common_mode(theta["log_method"], white["log_method"], block(body, offsets["log_method"]))
    counts = {m: {"n": int(np.sum((cat["method_family"] == m) & (z >= Z_COMMON[0]) & (z < Z_COMMON[1]))),
                  "n_north": int(np.sum((cat["method_family"] == m) & (z >= Z_COMMON[0]) & (z < Z_COMMON[1]) & (dec >= 0))),
                  "median_e_mu": float(np.median(emu[cat["method_family"] == m])), "median_z": float(np.median(z[cat["method_family"] == m]))}
              for m in METHODS}
    cm["sample"] = counts

    # ---- S6 zero-point split, jackknives, injections
    cov_split = white["log_split"] + block(body, offsets["log_split"])
    split_res = as_fraction(lz.analyse_window_multipoles(theta["log_split"], cov_split, an["log_split"], 1.0, law_log + "; method monopoles and method x hemisphere steps marginalised", estimator="log"))
    split_block = {"nuisance": "per window: monopole offsets of FP, SN, TF relative to OTHER and one hemisphere step sign(dec) per method (7 columns)",
                   "windows": window_summary(theta["log_split"], cov_split, white["log_split"]),
                   "analysis": split_res, "headline": headline_of(split_res, True),
                   "pole_decomposition": pole_decomposition(theta["log_split"], cov_split, an["log_split"])}
    cov_mono = white["log_mono"] + block(body, offsets["log_mono"])
    mono_res = as_fraction(lz.analyse_window_multipoles(theta["log_mono"], cov_mono, an["log_mono"], 1.0, law_log + "; method monopoles marginalised", estimator="log"))
    split_block["method_monopoles_only"] = {"nuisance": "per window: monopole offsets of FP, SN, TF relative to OTHER (3 columns); no hemisphere step",
                                            "headline": headline_of(mono_res, True),
                                            "pole_decomposition": pole_decomposition(theta["log_mono"], cov_mono, an["log_mono"])}
    split_block["hemisphere_step_by_method"] = hemisphere_steps(theta["method_step"], white["method_step"], block(body, offsets["method_step"]))
    lock_split = locking_null(theta["log_split"], cov_split, stream(2), N_NULL)
    lock_mono = locking_null(theta["log_mono"], cov_mono, stream(3), N_NULL)
    split_block["axis_locking_null"] = lock_split
    split_block["method_monopoles_only"]["axis_locking_null"] = lock_mono
    split_block["method_monopoles_only"]["window_subsets"] = window_subset_nulls(theta["log_mono"], cov_mono)
    steps_body = split_block["hemisphere_step_by_method"]["white_plus_exact_body"]
    split_block["hemisphere_step_scan"] = step_scan(cat, eta, g, tau2, r, stream(4), steps_body)
    jk = {}
    dqr = np.sort(np.concatenate([lz.block_rows("dipole"), lz.block_rows("quadrupole")]))
    for tag in ("jk_no_equator", "jk_no_north_cap", "jk_no_south_cap"):
        c = white[tag] + block(body, offsets[tag])
        fp = fv.gls_fit(theta[tag][dqr], c[np.ix_(dqr, dqr)], lz.axis_template(lz.AXES_ICRS["equatorial_pole"]))
        null = float(theta[tag][dqr] @ np.linalg.solve(c[np.ix_(dqr, dqr)], theta[tag][dqr]))
        pd = pole_decomposition(theta[tag], c, an[tag])
        jk[tag] = {"pole_dipole_fraction": float(fp["theta"][0]), "pole_dipole_sd": float(math.sqrt(fp["cov"][0, 0])),
                   "pole_quadrupole_fraction": float(fp["theta"][1]), "pole_quadrupole_sd": float(math.sqrt(fp["cov"][1, 1])),
                   "pole_gain": null - fp["chi2"], "joint_null_chi2": null, "joint_null_p": float(stats.chi2.sf(null, 32)),
                   "A_parallel": pd["A_only"]["parallel"], "A_parallel_sd": pd["A_only"]["parallel_sd"]}
    obs_step_mag = abs(steps_body["common_delta_mu_north_minus_south_mag"]) / 2.0
    obs_flow = log_block["headline"]["V_only_km_s"]
    inj = {"pooled": injections(ops["log"], cov_log, an["log"], cat, g, dec, stream(5), N_INJ, obs_step_mag, obs_flow,
                                lock_null["null_summary"]["sky_fraction_quantile_0p01"]),
           "method_monopoles_marginalised": injections(ops["log_mono"], cov_mono, an["log_mono"], cat, g, dec, stream(6), N_INJ, obs_step_mag, obs_flow,
                                                       lock_mono["null_summary"]["sky_fraction_quantile_0p01"])}

    # ---- decision (rule and thresholds were written into this script before the exact-body run and are not tuned afterwards)
    hl, hs = log_block["headline"], split_block["headline"]
    cmb = cm["white_plus_exact_body"]
    flags = {
        "lcdm_body_compatible": bool(hl["joint_null_p"] >= 0.01),
        "pole_locked": bool(lock_null["tails"]["sky_fraction_at_most_observed"] < 0.01),
        "constant_law_preferred": bool(hl["chi2_V"] - hl["chi2_A"] > 0.0),
        "common_to_indicators": bool(cmb["common_dipole"]["consistency_p_value"] >= 0.01),
        "removed_by_method_hemisphere_split": bool(hs["joint_null_p"] >= 0.01 and hs["pole_gain"] < GAIN_99_2DOF),
    }

    hm = split_block["method_monopoles_only"]["headline"]
    tails_by_variant = {"pooled": lock_null["tails"]["sky_fraction_at_most_observed"],
                        "method_monopoles_marginalised": lock_mono["tails"]["sky_fraction_at_most_observed"],
                        "method_x_hemisphere_steps_marginalised": lock_split["tails"]["sky_fraction_at_most_observed"]}
    by_variant = {"pooled": classify(hl["joint_null_p"], flags["removed_by_method_hemisphere_split"], tails_by_variant["pooled"]),
                  "method_monopoles_marginalised": classify(hm["joint_null_p"], flags["removed_by_method_hemisphere_split"],
                                                            tails_by_variant["method_monopoles_marginalised"]),
                  "method_x_hemisphere_steps_marginalised": classify(hs["joint_null_p"], False,
                                                                     tails_by_variant["method_x_hemisphere_steps_marginalised"])}
    cls = by_variant["pooled"]
    draft_rule = {
        "note": "three-way rule of the first contract draft, written before the catalogue-level run; evaluated here for transparency",
        "METHOD_ZERO_POINT": bool(hs["pole_gain"] < GAIN_99_2DOF and hs["dipole_null_p"] >= 0.01 and hs["quadrupole_null_p"] >= 0.01),
        "ESTIMATOR_MODE_COUPLING": bool(lock_null["tails"]["best_axis_angle_at_most_observed"] >= 0.05)}
    decision = {"class": cls, "class_by_nuisance_variant": by_variant,
                "robust_class": cls if len(set(by_variant.values())) == 1 else "DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL",
                "locking_tail_by_nuisance_variant": tails_by_variant,
                "joint_null_p_by_nuisance_variant": {"pooled": hl["joint_null_p"], "method_monopoles_marginalised": hm["joint_null_p"],
                                                     "method_x_hemisphere_steps_marginalised": hs["joint_null_p"]},
                "rule_status": "the rule and its thresholds were coded before the exact-body numbers were inspected, but the script was not committed "
                               "beforehand; class_by_nuisance_variant and robust_class were added after the independent review (AR-01, AR-06)",
                "flags": flags, "first_contract_draft_rule": draft_rule,
                "rule": ["LCDM_BODY_COMPATIBLE if the joint dipole+quadrupole null (log estimator, exact body) has p >= 0.01",
                         "else METHOD_HEMISPHERE_ZERO_POINT_TYPE if after the method/hemisphere split the joint null has p >= 0.01 and the pole gain is below 9.21",
                         "else UNRESOLVED_POLE_LOCKED if the calibrated sky-fraction tail is below 0.01",
                         "else EXCESS_NOT_POLE_LOCKED"],
                "claim": "C0 diagnostic; no physical anisotropy claim. A constant fractional dipole is not separable from a distance zero-point dipole inside distance-indicator data."}

    views = fv.five_view_record({
        "x": {"status": fv.AVAILABLE, "coordinates": "4 windows x [h, delta(3), kappa(5)], fractions of H; ICRS; z_CMB frame", "source": "CF4 groups, log-distance estimator"},
        "Q": {"status": fv.AVAILABLE, "body": "white + exact catalogue linear LCDM body (95% ellipsoid)",
              "dipole_Q_center": log_res["dipole"]["Q_center"], "quadrupole_Q_center": log_res["quadrupole"]["Q_center"]},
        "F": {"status": fv.UNAVAILABLE,
              "reason": "support utilization needs a declared convex body in parameter space; the axis scan is a template statistic and is reported under Pi"},
        "Pi": {"status": fv.AVAILABLE, "law": law_log, "dipole_null": log_res["dipole"]["null"], "quadrupole_null": log_res["quadrupole"]["null"],
               "axis_scan_null_law": lock_null["tails"]},
        "G_F": {"status": fv.AVAILABLE, "transport_laws": ["V: exact velocity response per window", "A: constant", "indicator transport: common vector across FP, TF, SN, OTHER"],
                "chi2_V": hl["chi2_V"], "chi2_A": hl["chi2_A"], "indicator_consistency_p": cmb["common_dipole"]["consistency_p_value"]},
    })
    out = {
        "schema": "htt.r54.cf4_exact/1", "node": "R54-L05", "claim_tier": "C0_DIAGNOSTIC_EXACT_LINEAR_BODY",
        "provenance": {"script": "scripts/r54/run_r54_cf4_exact.py", "script_sha256": lz.sha256(Path(__file__)),
                       "inputs_sha256": {str(p.relative_to(ROOT)): lz.sha256(p) for p in (SRC, OPF, R36_RESULT, PK, IDEAL)},
                       "cosmic_covariance_file": str(COV.relative_to(ROOT)), "cosmic_covariance_cached": cosmic["cached"],
                       "pair_sum_seconds": cosmic["seconds"], "seed": SEED,
                       "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "setup": {"n_groups": int(z.size), "window_centers_z": list(CENTERS), "window_width_z": WIDTH, "sigma_star_km_s": SIGMA_STAR,
                  "fiducial": {"H0": H_FID, "omega_m": OMEGA_M, "f": lb.growth_rate(OMEGA_M)}, "sigma_v_1d_linear_km_s": math.sqrt(cosmic["psi0"]),
                  "sigma_v_1d_damped_km_s": math.sqrt(cosmic["psi0_damped"]), "damping_mpc": DAMPING_MPC,
                  "operator_rows": {k: [v.start, v.stop] for k, v in offsets.items()},
                  "declination_deg": {"min": float(dec.min()), "max": float(dec.max()), "fraction_north": float(np.mean(dec >= 0))},
                  "composition_north_south": {m: {"z_below_0.055": [int(np.sum((cat["method_family"] == m) & (z < 0.055) & (dec >= 0))),
                                                                    int(np.sum((cat["method_family"] == m) & (z < 0.055) & (dec < 0)))],
                                                  "z_at_or_above_0.055": [int(np.sum((cat["method_family"] == m) & (z >= 0.055) & (dec >= 0))),
                                                                          int(np.sum((cat["method_family"] == m) & (z >= 0.055) & (dec < 0)))]}
                                              for m in METHODS}},
        "parity": parity, "linear_R36": linear_block, "log_distance": log_block, "common_mode": cm,
        "zero_point_split": split_block, "jackknife": jk, "injections": inj, "decision": decision, "five_views": views,
        "limitations": [
            "Linear theory with the z = 0 growth rate; positions are redshift-space comoving distances in the Planck 2018 fiducial.",
            "No selection function, Malmquist term or calibration covariance between objects; correlated zero-point errors are the alternative under test, not part of the null.",
            "The white term uses the catalogue distance-modulus errors and 250 km/s; variants are in body_sensitivity.",
            "A constant fractional dipole cannot be separated from a distance zero-point dipole inside distance-indicator data; the common-mode test only excludes a single-indicator origin.",
            "The source file carries four method families, not survey labels; the hemisphere step is a proxy for survey-specific zero points.",
            "Exploratory tabulations by method and hemisphere preceded the choice of the common redshift range 0.01-0.055; the range was fixed on sample-coverage grounds before the body was attached.",
            "The sign(dec) split axis, the reference axes and the two-parameter axis template were chosen after the first pass had located the pole on the same data; the hemisphere-step scan gives the look-elsewhere corrected tail and single-axis tails must not be quoted alone.",
            "The two outer windows are almost entirely northern FP, so their dipoles compare FP in the north with other indicators; window_subsets separates inner and outer windows.",
            "The class depends on the zero-point nuisance model (decision.class_by_nuisance_variant); no variant is preferred a priori.",
        ],
    }
    return lz.clean(out)


def main() -> None:
    out = compute()
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"decision": out["decision"], "log_headline": out["log_distance"]["headline"],
                      "hemisphere_step": out["zero_point_split"]["hemisphere_step_by_method"]["white_plus_exact_body"]}, indent=1))


if __name__ == "__main__":
    main()
