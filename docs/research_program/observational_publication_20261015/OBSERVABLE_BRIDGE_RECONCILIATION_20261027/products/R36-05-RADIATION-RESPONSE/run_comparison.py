"""Frozen R36-05 conditional comparison; run once with IMPLEMENTATION_CONTRACT.json.

The generator has no measured CMB input. Its confidence regions are oracle
noise-propagation regions around known synthetic temperature skies.
"""

from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations_with_replacement
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import time

import numpy as np
from numpy.polynomial.legendre import legval
from scipy.constants import Boltzmann as K_B, hbar, c
from scipy.stats import beta as beta_law, binomtest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from radiation_core import (ETA, STF_BASIS, coercivity_diagnostic, moments,
                            response_direct, response_from_moments, sphere_rule,
                            stf2)


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
CONTRACT = Path("/mnt/extdrive/workdir/htt_open_data/r36_radiation_contract_preparation/IMPLEMENTATION_CONTRACT.json")
RAW = Path("/mnt/extdrive/workdir/htt_open_data/r36_radiation_response_actual")
PARENT = HERE.parent.parent
RHO_REF = 4 * np.pi * (np.pi * K_B ** 4 / (60 * hbar ** 3 * c ** 3)) * 2.7255 ** 4
SIGMA = np.array([7.5e-6] * 3 + [9.375e-7] * 5)
SIGN = np.array([1, -1, 1, 1, -1, 1, -1, 1])
CORR = .8 * np.eye(8) + .2 * np.outer(SIGN, SIGN)
C_THETA = SIGMA[:, None] * CORR * SIGMA[None, :]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_source_bindings(contract: dict) -> dict:
    out = {}
    for name, binding in contract["source_bindings"].items():
        path = REPO / binding["path"]
        observed = sha(path)
        if observed != binding["sha256"]:
            raise RuntimeError(f"immutable source mismatch: {name}: {observed}")
        out[name] = {"path": binding["path"], "sha256": observed}
    if sha(REPO / PARENT.relative_to(REPO) / "EVIDENCE_MANIFEST.json") != contract["input_identity"].split(":", 1)[1]:
        raise RuntimeError("packet input identity changed")
    return out


def boost(v: np.ndarray) -> np.ndarray:
    b2 = float(v @ v)
    if b2 >= 1:
        raise ValueError("superluminal beta")
    gamma = 1 / np.sqrt(1 - b2)
    l = np.eye(4)
    l[0, 0] = gamma
    l[0, 1:] = l[1:, 0] = gamma * v
    if b2:
        l[1:, 1:] += (gamma - 1) * np.outer(v, v) / b2
    return l


def truth_sky(n: np.ndarray, a: float, b: float) -> tuple[np.ndarray, np.ndarray]:
    v = b * np.array([.6, 0, .8])
    e = -n
    lminus = boost(-v)
    p0 = lminus[0, 0] + e @ lminus[0, 1:]
    pspace = lminus[1:, 0] + e @ lminus[1:, 1:].T
    nrest_z = -pspace[:, 2] / p0
    brightness_rest = 1 + a * (3 * nrest_z ** 2 - 1) / 2
    if np.any(brightness_rest <= 0):
        raise ValueError("nonpositive source brightness")
    t = brightness_rest ** .25 / p0
    rest = np.diag([1., 1 / 3 - a / 15, 1 / 3 - a / 15,
                    1 / 3 + 2 * a / 15])
    expected = boost(v) @ rest @ boost(v).T
    return t, expected


def chart(n: np.ndarray, weights: np.ndarray, t: np.ndarray) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    tbar = float(weights @ t)
    theta = t / tbar - 1
    d = 3 * (weights * theta) @ n
    q = 7.5 * np.einsum("n,na->a", weights * theta,
                       np.einsum("aij,ni,nj->na", STF_BASIS, n, n))
    return tbar, theta, d, q


def feature_matrix(n: np.ndarray) -> np.ndarray:
    return np.column_stack([n, np.einsum("aij,ni,nj->na", STF_BASIS, n, n)])


def moment_operator(n: np.ndarray, weights: np.ndarray) -> np.ndarray:
    e = -n
    return np.column_stack([np.ones(len(n)), e,
                            np.einsum("aij,ni,nj->na", STF_BASIS, e, e)]) * weights[:, None]


def polynomial_adapter(t: np.ndarray, tbar: float, f: np.ndarray,
                       weighted_output: np.ndarray) -> tuple[np.ndarray, list[tuple[int, ...]]]:
    """Exact quartic polynomial in the eight observed temperature coordinates."""
    monomials: list[tuple[int, ...]] = [()]
    coefficients = [np.einsum("n,nj->j", t ** 4, weighted_output)]
    for degree in range(1, 5):
        for indices in combinations_with_replacement(range(8), degree):
            count = Counter(indices)
            factor = math.factorial(4) / math.factorial(4 - degree)
            for multiplicity in count.values():
                factor /= math.factorial(multiplicity)
            term = t ** (4 - degree)
            for index in indices:
                term = term * (tbar * f[:, index])
            coefficients.append(factor * np.einsum("n,nj->j", term, weighted_output))
            monomials.append(indices)
    return np.array(coefficients), monomials


def evaluate_polynomial(eta: np.ndarray, coefficients: np.ndarray,
                        monomials: list[tuple[int, ...]]) -> np.ndarray:
    terms = np.ones((len(eta), len(monomials)))
    for j, indices in enumerate(monomials[1:], 1):
        for index in indices:
            terms[:, j] *= eta[:, index]
    return terms @ coefficients


def check_polynomial(t: np.ndarray, tbar: float, feature: np.ndarray,
                     weighted_output: np.ndarray, coefficients: np.ndarray,
                     monomials: list[tuple[int, ...]]) -> float:
    fixed = np.random.default_rng(31536).multivariate_normal(
        np.zeros(8), C_THETA, size=16)
    draws = np.vstack([np.zeros(8), fixed])
    actual = evaluate_polynomial(draws, coefficients, monomials)
    direct = np.array([((t + tbar * (feature @ eta)) ** 4) @ weighted_output
                       for eta in draws])
    error = float(np.max(abs(actual - direct)))
    if error > 2e-12:
        raise RuntimeError(f"quartic adapter mismatch {error}")
    return error


def analyze_moments(v: np.ndarray) -> dict:
    """Vectorized physical guards, D and Landau scalar on normalized tensors."""
    count = len(v)
    base = np.isfinite(v).all(axis=1) & (v[:, 0] > 0)
    # A benign temporary matrix keeps batched eigensolvers defined. Masked
    # outputs become NaN and remain invalid; no missing physical value is used.
    work = v.copy()
    work[~base] = np.array([1., 0., 0., 0., 0., 0., 0., 0., 0.])
    rho = work[:, 0]
    j = work[:, 1:4]
    pi = work[:, 4:9]
    f = j / rho[:, None]
    p = pi / rho[:, None]
    spatial = np.einsum("na,aij->nij", pi, STF_BASIS)
    spatial += rho[:, None, None] * np.eye(3) / 3
    t = np.zeros((count, 4, 4))
    t[:, 0, 0] = rho
    t[:, 0, 1:] = t[:, 1:, 0] = j
    t[:, 1:, 1:] = spatial
    mat = t / rho[:, None, None]
    eig_moment = np.linalg.eigvalsh(mat)
    cone = (base &
            (np.sum(f * f, axis=1) < 1) &
            (eig_moment[:, 0] >= -64 * np.finfo(float).eps * 4 *
             np.linalg.norm(mat, axis=(1, 2))))
    eigen, vectors = np.linalg.eig(mat @ ETA)
    imag = np.max(np.abs(eigen.imag), axis=1)
    euc = np.sum(np.abs(vectors) ** 2, axis=1)
    mink = -np.abs(vectors[:, 0, :]) ** 2 + np.sum(np.abs(vectors[:, 1:, :]) ** 2, axis=1)
    branch = mink < -1e-8 * euc
    branch_count = branch.sum(axis=1)
    index = np.argmax(branch, axis=1)
    rho_l = -np.real(eigen[np.arange(count), index])
    pressures = np.real(eigen).copy()
    pressures[np.arange(count), index] = np.nan
    # NaN-safe row deletion, with exactly one timelike branch required.
    pressure3 = pressures[~np.isnan(pressures)].reshape(count, 3)
    a = np.linalg.norm(pressure3 - rho_l[:, None] / 3, axis=1) / rho_l
    valid = (cone & (imag <= 1e-12 * np.linalg.norm(mat, axis=(1, 2)))
             & (branch_count == 1) & (rho_l > 0)
             & np.all(pressure3 >= -64 * np.finfo(float).eps, axis=1)
             & np.isfinite(a))
    kap = 3 / (2 + np.sqrt(np.maximum(4 - 3 * np.sum(f * f, axis=1), 0)))
    ff_stf = np.einsum("aij,ni,nj->na", STF_BASIS, f, f)
    d = p - kap[:, None] * ff_stf
    f[~base] = np.nan
    p[~base] = np.nan
    d[~base] = np.nan
    a[~base] = np.nan
    t[~base] = np.nan
    return {"valid": valid, "cone": cone, "branch_count": branch_count,
            "fP": np.column_stack([f, p]), "D": d, "A": a,
            "rho": np.where(base, rho, np.nan), "stress": t,
            "min_moment_eigen": eig_moment[:, 0]}


def tensor_moment_vector(t: np.ndarray) -> np.ndarray:
    """Exact analytic T^{mu nu}/rho_ref to rho,j,STF-pi coordinates."""
    return np.r_[t[0, 0], t[0, 1:],
                 np.einsum("aij,ij->a", STF_BASIS, stf2(t[1:, 1:]))]


def cp_interval(hits: int, n: int) -> dict:
    ci = binomtest(int(hits), int(n)).proportion_ci(.95, method="exact")
    return {"hits": int(hits), "N": int(n), "fraction": hits / n,
            "lower": ci.low, "upper": ci.high,
            "max_halfwidth": max(hits / n - ci.low, ci.high - hits / n)}


def width_stats(width: np.ndarray) -> dict:
    finite = width[np.isfinite(width)]
    if not len(finite):
        return {"count": 0, "mean": None, "median": None, "p05": None, "p95": None}
    return {"count": len(finite), "mean": float(np.mean(finite)),
            "median": float(np.median(finite)),
            "p05": float(np.quantile(finite, .05)),
            "p95": float(np.quantile(finite, .95))}


def summarize_method(cal: dict, test: dict, truth: dict, physical: dict,
                     name: str, case: str) -> tuple[dict, dict]:
    m, n = len(cal["valid"]), len(test["valid"])
    output = {"method": name, "case": case,
              "calibration_valid": int(cal["valid"].sum()), "calibration_N": m,
              "test_valid": int(test["valid"].sum()), "test_N": n,
              "test_invalid_fraction": float(1 - test["valid"].mean())}
    arrays: dict[str, np.ndarray] = {}
    for prefix, data in (("cal", cal), ("test", test)):
        for key in ("valid", "rho", "stress", "fP", "D", "A"):
            arrays[f"{case}_{name}_{prefix}_{key}"] = data[key]
    if not cal["valid"].all():
        output["status"] = "HOLD_INVALID_CALIBRATION"
        return output, arrays
    fp = cal["fP"]
    covariance = np.cov(fp, rowvar=False, ddof=1)
    sd = np.sqrt(np.diag(covariance))
    standardized = covariance[:3, 3:] / sd[:3, None] / sd[None, 3:]
    output["fP_mean"] = fp.mean(axis=0).tolist()
    output["fP_covariance"] = covariance.tolist()
    output["fP_covariance_eigenvalues"] = np.linalg.eigvalsh(covariance).tolist()
    output["fP_standardized_cross_block_3x5"] = standardized.tolist()
    d0, a0 = truth[name]["D"], truth[name]["A"]
    d_true, a_true = physical["D"], physical["A"]
    output["D_noiseless"] = d0.tolist()
    output["A_noiseless"] = float(a0)
    output["D_noiseless_physical_signed_bias"] = (d0 - d_true).tolist()
    output["A_noiseless_physical_signed_bias"] = float(a0 - a_true)
    output["D_empirical_physical_signed_bias"] = (test["D"].mean(axis=0) - d_true).tolist()
    output["A_empirical_physical_signed_bias"] = float(test["A"].mean() - a_true)
    r = np.linalg.norm(cal["D"] - d0, axis=1)
    k_d = math.ceil(.95 * (m + 1))
    sorted_r = np.sort(r)
    radius = float(sorted_r[k_d - 1])
    low_k = math.floor(.025 * (m + 1))
    high_k = math.ceil(.975 * (m + 1))
    sorted_e = np.sort(cal["A"] - a0)
    e_low = float(sorted_e[low_k - 1])
    e_high = float(sorted_e[high_k - 1])
    d_inside_physical = test["valid"] & (np.linalg.norm(test["D"] - d_true, axis=1) <= radius)
    d_inside_method = test["valid"] & (np.linalg.norm(test["D"] - d0, axis=1) <= radius)
    a_low = np.maximum(0, test["A"] - e_high)
    a_high = test["A"] - e_low
    nonempty = test["valid"] & (a_high >= 0)
    a_inside_physical = nonempty & (a_low <= a_true) & (a_true <= a_high)
    a_inside_method = nonempty & (a_low <= a0) & (a0 <= a_high)
    widths = np.full(n, np.nan)
    widths[nonempty] = a_high[nonempty] - a_low[nonempty]
    output.update({"status": "PRODUCED_CONDITIONAL",
                   "quantile_indices_1based": {"D": k_d, "A_low": low_k, "A_high": high_k},
                   "D_radius": radius, "D_width": 2 * radius,
                   "A_error_quantiles": [e_low, e_high],
                   "D_physical_target_coverage": cp_interval(d_inside_physical.sum(), n),
                   "D_method_target_coverage": cp_interval(d_inside_method.sum(), n),
                   "A_physical_target_coverage": cp_interval(a_inside_physical.sum(), n),
                   "A_method_target_coverage": cp_interval(a_inside_method.sum(), n),
                   "A_empty_fraction": float((test["valid"] & ~nonempty).sum() / n),
                   "A_nonempty_width": width_stats(widths),
                   "D_calibration_ties": int(m - len(np.unique(r))),
                   "A_calibration_ties": int(m - len(np.unique(sorted_e))),
                   "calibration_content": {
                       "D_beta95": beta_law.ppf([.025, .975], k_d, m + 1 - k_d).tolist(),
                       "A_equal_tail_beta95": beta_law.ppf(
                           [.025, .975], high_k - low_k,
                           m + 1 - (high_k - low_k)).tolist()}})
    arrays[f"{case}_{name}_test_A_width"] = widths
    arrays[f"{case}_{name}_test_D_physical_hit"] = d_inside_physical
    arrays[f"{case}_{name}_test_A_physical_hit"] = a_inside_physical
    return output, arrays


def response_compression() -> dict:
    saved = json.loads((PARENT / "imports/v15/cas/entropic_shear_results.json").read_text())
    original = np.array(saved["input_brightness_legendre_coefficients"])
    rows = []
    for nodes in (256, 320):
        n, weights = sphere_rule(nodes, 12)
        mu = n[:, 2]
        target_w = legval(mu, original)
        target = moments(n, weights, target_w, 1)
        target_r = response_from_moments(target)
        for old in saved["rows"]:
            coeff = np.array(old["beta_legendre_coefficients"])
            candidate_w = legval(mu, coeff) ** -4
            candidate = moments(n, weights, candidate_w, 1)
            r = response_from_moments(candidate)
            retained = [float(weights @ ((target_w - candidate_w) * legval(mu, [0] * ell + [1])))
                        for ell in range(old["L"] + 1)]
            entropy = float(weights @ (candidate_w ** .75 - target_w ** .75))
            rows.append({"nmu": nodes, "L": old["L"],
                         "retained_moment_max_error": max(abs(x) for x in retained),
                         "entropy_difference_over_Siso": entropy,
                         "operator_error_over_rho0": float(np.linalg.norm(target_r - r, ord=2)),
                         "direct_vs_moment_operator_error": float(np.linalg.norm(
                             r - response_direct(n, weights, candidate_w, 1), ord=2)),
                         "response_matrix_over_rho0": r.tolist(),
                         "response_eigenvalues_over_rho0": np.linalg.eigvalsh(r).tolist()})
    for ell, old in ((2, saved["rows"][0]), (4, saved["rows"][1])):
        current = next(x for x in rows if x["nmu"] == 256 and x["L"] == ell)
        if abs(current["operator_error_over_rho0"] - old["operator_error_over_rho0"]) > 2e-12:
            raise RuntimeError("saved response control mismatch")
        if current["retained_moment_max_error"] > 2e-12 or current["direct_vs_moment_operator_error"] > 2e-12:
            raise RuntimeError("rank-four response assembly mismatch")
    n, weights = sphere_rule(160, 32)
    raw = np.exp(8 * n[:, 2] ** 2)
    w = raw / (weights @ raw)
    mm = moments(n, weights, w, 1)
    diag160 = coercivity_diagnostic(weights, w, response_from_moments(mm), mm.rho)
    n2, weights2 = sphere_rule(320, 32)
    raw2 = np.exp(8 * n2[:, 2] ** 2)
    w2 = raw2 / (weights2 @ raw2)
    mm2 = moments(n2, weights2, w2, 1)
    diag320 = coercivity_diagnostic(weights2, w2, response_from_moments(mm2), mm2.rho)
    if (diag160["sufficient_certificate_pass"] or not diag160["actual_positive"]
            or max(abs(np.array(diag160["actual_eigenvalues_over_rho"])
                       - np.array(diag320["actual_eigenvalues_over_rho"]))) > 2e-12):
        raise RuntimeError("entropy-fallback spectrum failed")
    return {"L2_L4": rows, "entropy_fallback_160": diag160,
            "entropy_fallback_320": diag320}


def save_plot(rows: list[dict]) -> None:
    exact = [r for r in rows if r["method"] == "exact"]
    linear = [r for r in rows if r["method"] == "linear"]
    names = [f"a={r['case'].split('_b')[0][1:]}\nβ={r['case'].split('_b')[1]}"
             for r in exact]
    x = np.arange(len(names))
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.2), constrained_layout=True)
    for ax, key, target in ((axes[0, 0], "D_physical_target_coverage", .95),
                            (axes[0, 1], "A_physical_target_coverage", .95)):
        for data, dx, label, color in ((exact, -.16, "Exact", "#176fa8"),
                                       (linear, .16, "Linear", "#bf6932")):
            values = [r[key]["fraction"] for r in data]
            lo = [r[key]["lower"] for r in data]
            hi = [r[key]["upper"] for r in data]
            ax.errorbar(x + dx, values, yerr=[np.array(values) - lo, np.array(hi) - values],
                        marker="o", linestyle="none", capsize=2, label=label, color=color)
        ax.axhline(target, color="#777", linestyle="--", linewidth=1)
        ax.set(ylim=(0, 1.03), ylabel="Physical-target coverage", xticks=x,
               xticklabels=names)
        ax.tick_params(axis="x", labelsize=8)
        ax.grid(alpha=.2)
    axes[0, 0].set_title("Five-dimensional D ball")
    axes[0, 1].set_title("Landau A interval")
    axes[0, 0].legend(frameon=False)
    for ax, key, title in ((axes[1, 0], "D_width", "D ball diameter"),
                           (axes[1, 1], "A_nonempty_width", "Mean nonempty A width")):
        for data, dx, label, color in ((exact, -.16, "Exact", "#176fa8"),
                                       (linear, .16, "Linear", "#bf6932")):
            value = [r[key] if key == "D_width" else r[key]["mean"] for r in data]
            ax.bar(x + dx, value, width=.3, label=label, color=color)
        ax.set(title=title, xticks=x, xticklabels=names)
        ax.tick_params(axis="x", labelsize=8)
        ax.grid(axis="y", alpha=.2)
    fig.suptitle("Conditional synthetic radiation stress: matched temperature inputs and errors")
    fig.savefig(HERE / "comparison.png", dpi=170)
    fig.savefig(HERE / "comparison.pdf")
    plt.close(fig)


def main() -> None:
    started = time.time()
    contract = json.loads(CONTRACT.read_text())
    if contract["status"] != "PREPARATION_ONLY_FROZEN_BEFORE_STATISTICAL_PRODUCTION":
        raise RuntimeError("frozen contract not available")
    sources = check_source_bindings(contract)
    raw = RAW / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    n, weights = sphere_rule(36, 73)
    n_ref, weights_ref = sphere_rule(72, 145)
    features = feature_matrix(n)
    weighted_output = moment_operator(n, weights)
    children = np.random.SeedSequence(2026102705).spawn(12)
    truth = {}
    summary = []
    arrays: dict[str, np.ndarray] = {}
    preflight = []
    cases = [(a, b) for a in (0, 2e-5, .02) for b in (.00123, .3)]
    # All source/analytic/adaptor checks precede the first MC draw.
    prepared = []
    for index, (a, b) in enumerate(cases):
        name = f"a{a:g}_b{b:g}"
        t, analytic = truth_sky(n, a, b)
        t_ref, analytic_ref = truth_sky(n_ref, a, b)
        m = moments(n, weights, t ** 4, 1)
        m_ref = moments(n_ref, weights_ref, t_ref ** 4, 1)
        err = float(np.max(abs(m.stress - analytic)))
        refine = float(np.max(abs(m.stress - m_ref.stress)))
        if err > 2e-12 or refine > 2e-12 or np.max(abs(analytic - analytic_ref)) > 1e-14:
            raise RuntimeError(f"Lorentz/moment quadrature mismatch {name}: {err},{refine}")
        tbar, theta, d_true, q_true = chart(n, weights, t)
        coefficients, monomials = polynomial_adapter(t, tbar, features, weighted_output)
        poly_error = check_polynomial(t, tbar, features, weighted_output, coefficients, monomials)
        exact0 = analyze_moments(coefficients[:1])
        linear0_v = np.zeros((1, 9))
        linear0_v[:, 0] = tbar ** 4
        linear0_v[:, 1:4] = -4 * tbar ** 4 * d_true / 3
        linear0_v[:, 4:] = 8 * tbar ** 4 * q_true / 15
        linear0 = analyze_moments(linear0_v)
        if not exact0["valid"][0] or not linear0["valid"][0]:
            raise RuntimeError(f"noiseless physical guard failed {name}")
        analytic_readout = analyze_moments(tensor_moment_vector(analytic)[None, :])
        if not analytic_readout["valid"][0]:
            raise RuntimeError(f"analytic boosted tensor outside physical domain {name}")
        d_true_target = analytic_readout["D"][0]
        a_true_target = np.sqrt(6) * abs(a) / 15
        if a == 0:
            if np.linalg.norm(d_true_target) > 2e-12 or abs(exact0["A"][0]) > 2e-12:
                raise RuntimeError("pure boost null failed")
            d_true_target = np.zeros(5)
            a_true_target = 0.0
        if abs(exact0["A"][0] - a_true_target) > 2e-12:
            raise RuntimeError(f"Landau analytic target mismatch {name}")
        bound = (1 - a / 2) ** .25 / (1 / np.sqrt(1 - b * b) * (1 + b) * tbar)
        preflight.append({"case": name, "analytic_tensor_max_error_over_rho_ref": err,
                          "resolution_tensor_max_difference_over_rho_ref": refine,
                          "polynomial_adapter_max_difference": poly_error,
                          "temperature_sufficient_lower_ratio": bound})
        prepared.append((name, a, b, t, tbar, d_true, q_true, bound, analytic,
                         coefficients, monomials, exact0, linear0,
                         {"D": d_true_target, "A": a_true_target}))
    compression = response_compression()
    for index, entry in enumerate(prepared):
        (name, a, b, t, tbar, d_true, q_true, bound, analytic,
         coefficients, monomials, exact0, linear0, physical) = entry
        rng_cal = np.random.default_rng(children[2 * index])
        rng_test = np.random.default_rng(children[2 * index + 1])
        eta_cal = rng_cal.multivariate_normal(np.zeros(8), C_THETA, size=8191)
        eta_test = rng_test.multivariate_normal(np.zeros(8), C_THETA, size=4096)
        arrays[f"{name}_eta_cal"] = eta_cal
        arrays[f"{name}_eta_test"] = eta_test
        truth[name] = {"a": a, "b": b, "physical_D": physical["D"].tolist(),
                       "physical_A": physical["A"], "tbar": tbar,
                       "d_true": d_true.tolist(), "Q_true": q_true.tolist(),
                       "analytic_T_over_rho_ref": analytic.tolist(),
                       "noiseless_exact_T_over_rho_ref": exact0["stress"][0].tolist(),
                       "noiseless_linear_T_over_rho_ref": linear0["stress"][0].tolist()}
        method_truth = {"exact": {"D": exact0["D"][0], "A": exact0["A"][0]},
                        "linear": {"D": linear0["D"][0], "A": linear0["A"][0]}}
        outputs = {}
        for sample_name, eta in (("cal", eta_cal), ("test", eta_test)):
            magnitude = np.linalg.norm(eta[:, :3], axis=1) + np.sqrt(2 / 3) * np.linalg.norm(eta[:, 3:], axis=1)
            positivity = magnitude < bound
            exact_v = evaluate_polynomial(eta, coefficients, monomials)
            exact = analyze_moments(exact_v)
            exact["valid"] &= positivity
            linear_v = np.empty((len(eta), 9))
            linear_v[:, 0] = tbar ** 4
            linear_v[:, 1:4] = -4 * tbar ** 4 * (d_true + eta[:, :3]) / 3
            linear_v[:, 4:] = 8 * tbar ** 4 * (q_true + eta[:, 3:]) / 15
            linear = analyze_moments(linear_v)
            linear["valid"] &= positivity
            outputs[sample_name] = {"exact": exact, "linear": linear}
            arrays[f"{name}_{sample_name}_temperature_positivity"] = positivity
        for method in ("exact", "linear"):
            row, data = summarize_method(outputs["cal"][method], outputs["test"][method],
                                         method_truth, physical, method, name)
            summary.append(row)
            arrays.update(data)
    for i in range(0, len(summary), 2):
        exact, linear = summary[i:i + 2]
        if exact["status"] == linear["status"] == "PRODUCED_CONDITIONAL":
            name = exact["case"]
            w1 = arrays[f"{name}_exact_test_A_width"]
            w2 = arrays[f"{name}_linear_test_A_width"]
            both = np.isfinite(w1) & np.isfinite(w2)
            diff = w1[both] - w2[both]
            paired = {"count": int(len(diff)), "mean_exact_minus_linear": float(diff.mean()),
                      "MC_SE": float(diff.std(ddof=1) / np.sqrt(len(diff)))}
            exact["paired_A_width_difference"] = paired
            linear["paired_A_width_difference"] = paired
    if any(row["status"] != "PRODUCED_CONDITIONAL" for row in summary):
        status = "HOLD_INVALID_CALIBRATION"
    else:
        status = "PROPOSED_PENDING_INDEPENDENT_REVIEW"
        save_plot(summary)
    np.savez_compressed(RAW / "sample_arrays.npz", **arrays)
    result = {"task_id": "R36-05-RADIATION-RESPONSE",
              "packet_id": "1a4ba501f02b8e078ab488ce45996b4415b55ce96308ec4dc5c2b3701a9a5371",
              "input_identity": contract["input_identity"], "status": status,
              "claim_tier": "conditional_synthetic_method_experiment",
              "owner": "htt", "transfer_source": "none",
              "units": {"normalized_stress": "rho_ref", "rho_ref_J_m-3": RHO_REF,
                        "flux": "c*rho_ref W m^-2", "dimensionless": ["f", "P", "D", "A_gamma"]},
              "frame": "declared local observer, (-,+,+,+), e=-n",
              "source_bindings": sources, "contract_sha256": sha(CONTRACT),
              "rng": {"bit_generator": "PCG64", "seed_sequence_entropy": 2026102705,
                      "spawn_count": 12, "calibration_per_case": 8191, "test_per_case": 4096},
              "temperature_law": {"coordinate_sigma": SIGMA.tolist(),
                                  "correlation": CORR.tolist(), "covariance": C_THETA.tolist()},
              "preflight": preflight, "truth": truth, "methods": summary,
              "response_compression": compression,
              "limits": "One-event radiation operator only; no transport derivative R or matter shear inference. No empirical Planck interval or spectral completion.",
              "environment": {"python": platform.python_version(), "numpy": np.__version__,
                              "scipy": __import__("scipy").__version__,
                              "matplotlib": matplotlib.__version__},
              "elapsed_seconds": time.time() - started}
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": status, "cases": len(cases),
                      "methods": len(summary), "elapsed_seconds": result["elapsed_seconds"]}))


if __name__ == "__main__":
    main()
