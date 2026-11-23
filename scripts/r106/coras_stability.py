"""CORAS H02 covariance stability: seed halves, residual mean, leading subspace and mesh axes.

Main configuration (radial 36, ell 8, FFT 24): the pooled seeds are split into two
contiguous halves (1-128, 129-256), as in coras_reduce.split_diagnostic.

Descriptive quadratics (zero cross-covariance between measurement and CORAS scatter,
Gaussian-approximate, no calibrated p):

* ``quadratic_obs_minus_analytic_mean_meas_plus_sample_cov``: r = obs - m_CORAS,
  the R105 coras_reduce definition (``measurement_plus_sample_cov_quadratic_minus_coras``);
* ``quadratic_obs_minus_ensemble_mean_meas_plus_sample_cov``: r = obs - m_CORAS - rbar,
  where rbar is the mean of the residual draws (``_inflated`` adds C/n for the noise in rbar);
* measurement-only quadratics against both means.

The CORAS residual files hold random signal minus mock estimate and are not zero-mean
by construction.  The residual mean is reported as a systematic with low-dimensional
statistics (per-coefficient z, shell monopoles, leading-PC Hotelling T^2, per-site
means by radius); the 36-D T^2 is shown with the share carried by trailing
principal directions.  Optional FFT probe runs test whether the offset moves with
FFT resolution.

Covariance noise: a Gaussian Monte Carlo (truth = pooled sample covariance) gives the
debias factor and SD of the meas+S quadratic.  The Hartlap factor applies only to
sample-only inversion and is shown only as a check of that Monte Carlo.

Leading subspace: leading spectrum and gap ratios, principal angles for k = 1..8,
and a permutation null (random 128/128 splits of the pooled seeds) for the largest
angle at each k.

Mesh axes (radial 36->48, ell 8->12, same seeds and FFT, so the same random Fourier
field): per-seed differences, a paired bootstrap over seeds for the trace ratio and
for the quadratic shift.  A change resolved by the paired interval is a truncation
systematic; convergence beyond the largest tested value is not assessed.

Units: coefficients in the R98 natural-log distance basis; site means in km/s;
angles in degrees.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import scipy
from scipy import stats

from scripts.r105 import coras_reduce as cr

SCHEMA = "htt.r106.coras_stability/2"
P = 36
COEFFS_PER_SHELL = 9  # columns (1, n, STF) of h03_tomography.velocity_design per window
COMPONENT_NAMES = ("monopole", "dipole_1", "dipole_2", "dipole_3",
                   "quadrupole_stf_1", "quadrupole_stf_2", "quadrupole_stf_3", "quadrupole_stf_4", "quadrupole_stf_5")
SHELL_MONOPOLES = tuple(range(0, P, COEFFS_PER_SHELL))
RADIUS_EDGES_MPCH = (0., 60., 100., 150., 200.)
LEADING_PCS = (8, 10)
KMAX_ANGLES = 8
KMAX_NULL = 15
SPECTRUM_SHOWN = 16  # >= KMAX_NULL + 1 so any gap index is printable
SIGN_FLIP_REPS = 20000
RNG_SEEDS = dict(sign_flip=10601, permutation=10602, degenerate_block=10603, debias=10604,
                 axis_bootstrap=10605)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path) -> str:
    return cr._sha(Path(path))


def array_digest(a) -> str:
    a = np.ascontiguousarray(a)
    return sha256_bytes(a.dtype.str.encode() + str(a.shape).encode() + a.tobytes())


def load(directory, geometry, edges=RADIUS_EDGES_MPCH):
    """Digest-checked conditional mean, projected residual draws and per-site radius-bin means of one run."""
    directory = Path(directory)
    rec, _, identity, first, last = cr.metadata(directory, geometry)
    ids = np.asarray(geometry["ids"])
    w = np.asarray(geometry["weights"], float)
    radius = np.asarray(geometry["radius"], float)
    bins = [(lo, hi, (radius >= lo) & (radius < hi)) for lo, hi in zip(edges[:-1], edges[1:])]
    bins = [b for b in bins if b[2].any()]
    expected = rec["output_sha256"]
    names = {f"residual_{s}.tsv" for s in range(first, last + 1)}
    if set(expected) != names | {"mean.tsv"} or {p.name for p in directory.glob("residual_*.tsv")} != names:
        raise ValueError(f"partial or stale CORAS draw set in {directory}")
    if cr._sha(directory / "mean.tsv") != expected["mean.tsv"]:
        raise ValueError(f"mean digest mismatch in {directory}")
    mean = w @ cr.read_radial(directory / "mean.tsv", ids)
    draws, site = {}, {}
    for s in range(first, last + 1):
        f = directory / f"residual_{s}.tsv"
        if cr._sha(f) != expected[f.name]:
            raise ValueError(f"residual digest mismatch: {f}")
        v = cr.read_radial(f, ids)
        draws[s] = w @ v
        site[s] = np.array([v[m].mean() for _, _, m in bins])
    run_file = dict(directory=str(directory.resolve()), run_json_sha256=cr._sha(directory / "run.json"),
                    seed_range=[first, last], n_draws=last - first + 1, mean_sha256=expected["mean.tsv"],
                    config=identity["config"])
    return dict(identity=identity, mean=mean, draws=draws, site_bin_means=site, run_file=run_file,
                site_bins=[dict(radius_Mpch=[lo, hi], n_sites=int(m.sum())) for lo, hi, m in bins])


def leading(c, k):
    vals, vecs = np.linalg.eigh(c)
    order = np.argsort(vals)[::-1][:k]
    return vals[order], vecs[:, order]


def angles(u, v):
    s = np.linalg.svd(u.T @ v, compute_uv=False)
    return np.degrees(np.arccos(np.clip(s, -1.0, 1.0))).tolist()


def sym_rel_frobenius(a, b):
    """||A-B||_F / (0.5 (||A||_F + ||B||_F)); the coras_reduce.split_diagnostic convention."""
    den = 0.5 * (np.linalg.norm(a) + np.linalg.norm(b))
    return float(np.linalg.norm(a - b) / den) if den else None


def quad(r, c):
    return cr.quadratic(np.asarray(r, float), np.asarray(c, float))


def quantiles(x, qs=(0.05, 0.5, 0.95)):
    return [float(v) for v in np.quantile(np.asarray(x, float), qs)]


def hotelling_one_sample(x):
    """One-sample Hotelling T^2 of the column means, Gaussian F reference."""
    n, k = x.shape
    m = x.mean(0)
    t2 = float(n * m @ np.linalg.solve(cr.cov(x), m))
    return dict(dims=k, T2=t2, expected_T2_if_zero_mean=k * (n - 1) / (n - k - 2),
                gaussian_F_p=float(stats.f.sf(t2 * (n - k) / (k * (n - 1)), k, n - k)))


def hotelling_two_sample(x, y):
    n1, k = x.shape
    n2 = len(y)
    d = x.mean(0) - y.mean(0)
    sp = ((n1 - 1) * cr.cov(x) + (n2 - 1) * cr.cov(y)) / (n1 + n2 - 2)
    t2 = float(n1 * n2 / (n1 + n2) * d @ np.linalg.solve(sp, d))
    f = t2 * (n1 + n2 - k - 1) / (k * (n1 + n2 - 2))
    return dict(dims=k, T2=t2, gaussian_F_p=float(stats.f.sf(f, k, n1 + n2 - k - 1)))


def residual_mean(draws, site_bin_means, site_bins, rng):
    """Residual-draw mean as a systematic: per coefficient, shell monopoles, leading PCs, sites by radius."""
    n = len(draws)
    rbar = draws.mean(0)
    sd = draws.std(0, ddof=1)
    z = np.sqrt(n) * rbar / sd
    flips = rng.choice([-1.0, 1.0], size=(SIGN_FLIP_REPS, n))
    null = np.abs(flips @ draws) / n
    sign_p = (np.sum(null >= np.abs(rbar), axis=0) + 1) / (SIGN_FLIP_REPS + 1)
    coeffs = []
    for i in range(P):
        coeffs.append(dict(index=i, shell=i // COEFFS_PER_SHELL, component=COMPONENT_NAMES[i % COEFFS_PER_SHELL],
                           mean=float(rbar[i]), sd=float(sd[i]), z=float(z[i]),
                           wilcoxon_p=float(stats.wilcoxon(draws[:, i]).pvalue), sign_flip_p=float(sign_p[i]),
                           fraction_same_sign_as_mean=float(np.mean(np.sign(draws[:, i]) == np.sign(rbar[i])))))
    c = cr.cov(draws)
    vals, vecs = leading(c, P)
    proj = vecs.T @ rbar
    contrib = n * proj ** 2 / vals
    full = hotelling_one_sample(draws)
    pcs = {f"leading{k}": hotelling_one_sample(draws @ vecs[:, :k]) for k in LEADING_PCS}
    site = np.array([site_bin_means[s] for s in sorted(site_bin_means)])
    half = n // 2
    by_radius = []
    for j, b in enumerate(site_bins):
        x = site[:, j]
        by_radius.append(dict(**b, mean_kms=float(x.mean()), z=float(x.mean() / (x.std(ddof=1) / np.sqrt(n))),
                              first_half_mean_kms=float(x[:half].mean()), second_half_mean_kms=float(x[half:].mean())))
    order = np.argsort(-np.abs(z))
    return dict(n_draws=n, sign_flip_reps=SIGN_FLIP_REPS, sign_flip_p_resolution=1 / (SIGN_FLIP_REPS + 1),
                per_coefficient=coeffs, largest_abs_z=[[int(i), float(z[i])] for i in order[:6]],
                shell_monopoles=dict(indices=list(SHELL_MONOPOLES), z=[float(z[i]) for i in SHELL_MONOPOLES],
                                     hotelling=hotelling_one_sample(draws[:, list(SHELL_MONOPOLES)])),
                leading_pc_hotelling=pcs,
                full_36_hotelling=dict(**full, covariance_condition_number=float(vals[0] / vals[-1]),
                                       share_of_T2_from_trailing_pcs_beyond_10=float(contrib[10:].sum() / contrib.sum())),
                site_mean_by_radius=by_radius)


def describe(draws, mean, geometry):
    obs = np.asarray(geometry["observed"], float)
    meas = np.asarray(geometry["measurement_cov"], float)
    n = len(draws)
    c = cr.cov(draws)
    rbar = draws.mean(0)
    vals = np.sort(np.linalg.eigvalsh(c))[::-1]
    r_an, r_en = obs - mean, obs - mean - rbar
    m = SPECTRUM_SHOWN
    return {"n_draws": n, "trace": float(np.trace(c)),
            "leading_eigenvalues": vals[:m].tolist(),
            "consecutive_eigenvalue_ratios": (vals[:m] / vals[1:m + 1]).tolist(),
            "leading8_fraction_of_trace": float(vals[:8].sum() / np.trace(c)),
            "quadratic_obs_minus_analytic_mean_meas_plus_sample_cov": quad(r_an, meas + c),
            "quadratic_obs_minus_ensemble_mean_meas_plus_sample_cov": quad(r_en, meas + c),
            "quadratic_obs_minus_ensemble_mean_meas_plus_sample_cov_inflated": quad(r_en, meas + c * (1 + 1 / n)),
            "quadratic_obs_minus_analytic_mean_meas_only": quad(r_an, meas),
            "quadratic_obs_minus_ensemble_mean_meas_only": quad(r_en, meas),
            "residual_mean_norm": float(np.linalg.norm(rbar)),
            "residual_mean_meas_mahalanobis": float(np.sqrt(quad(rbar, meas)))}


def mc_debias(residuals, meas, c_true, n, reps, rng):
    """Gaussian Monte Carlo of q = r^T (M + S)^-1 r with S the sample covariance of n draws from C_true."""
    chol_true = np.linalg.cholesky(c_true)
    q = {k: [] for k in residuals}
    q_s = {k: [] for k in residuals}
    for _ in range(reps):
        s = cr.cov(rng.standard_normal((n, P)) @ chol_true.T)
        for k, r in residuals.items():
            q[k].append(quad(r, meas + s))
            q_s[k].append(quad(r, s))
    out = {}
    for k, r in residuals.items():
        truth, truth_s = quad(r, meas + c_true), quad(r, c_true)
        out[k] = dict(n=n, reps=reps, q_with_truth_cov=truth, mc_mean_q=float(np.mean(q[k])),
                      mc_sd_q=float(np.std(q[k], ddof=1)), debias_factor_truth_over_mean=float(truth / np.mean(q[k])),
                      sample_only_reference=dict(mc_factor=float(truth_s / np.mean(q_s[k])),
                                                 hartlap=(n - P - 2) / (n - 1)))
    return out


def subspace(first, second, pooled, reps, rng):
    """Leading spectrum, principal angles between the halves and a permutation null of the largest angle."""
    c1, c2, ca = cr.cov(first), cr.cov(second), cr.cov(pooled)
    w1, u1 = leading(c1, P)
    w2, u2 = leading(c2, P)
    wa, ua = leading(ca, P)
    ks = range(1, KMAX_NULL + 1)
    obs_max = {k: max(angles(u1[:, :k], u2[:, :k])) for k in ks}
    obs_v1 = angles(u1[:, :1], u2[:, :2])[0]
    obs_frob = sym_rel_frobenius(c1, c2)
    n1 = len(first)
    null = {k: [] for k in ks}
    null_frob, null_v1 = [], []
    for _ in range(reps):
        p = rng.permutation(len(pooled))
        a, b = pooled[p[:n1]], pooled[p[n1:]]
        ca_, cb_ = cr.cov(a), cr.cov(b)
        _, ea = leading(ca_, KMAX_NULL)
        _, eb = leading(cb_, KMAX_NULL)
        for k in ks:
            null[k].append(max(angles(ea[:, :k], eb[:, :k])))
        null_frob.append(sym_rel_frobenius(ca_, cb_))
        null_v1.append(angles(ea[:, :1], eb[:, :2])[0])
    null_summary = {}
    for k in ks:
        x = np.asarray(null[k])
        null_summary[f"k{k}"] = dict(observed_largest_angle=float(obs_max[k]), null_q05_q50_q95=quantiles(x),
                                     fraction_null_ge_observed=float(np.mean(x >= obs_max[k])),
                                     gap_pooled_lambda_k_over_k1=float(wa[k - 1] / wa[k]))
    gaps = wa[:KMAX_NULL] / wa[1:KMAX_NULL + 1]
    k_gap = int(np.argmax(gaps)) + 1
    medians = {k: null_summary[f"k{k}"]["null_q05_q50_q95"][1] for k in ks}
    return dict(
        halves_seed_counts=[len(first), len(second)],
        spectra=dict(first_half=w1[:SPECTRUM_SHOWN].tolist(), second_half=w2[:SPECTRUM_SHOWN].tolist(),
                     pooled=wa[:SPECTRUM_SHOWN].tolist()),
        gap_ratios_lambda_k_over_k1=dict(first_half=(w1[:KMAX_NULL] / w1[1:KMAX_NULL + 1]).tolist(),
                                         second_half=(w2[:KMAX_NULL] / w2[1:KMAX_NULL + 1]).tolist(),
                                         pooled=gaps.tolist()),
        principal_angles_deg_by_k={f"k{k}": angles(u1[:, :k], u2[:, :k]) for k in range(1, KMAX_ANGLES + 1)},
        v1_vs_other_half_topk_span_deg=dict(
            first_v1_vs_second=[angles(u1[:, :1], u2[:, :k])[0] for k in range(1, KMAX_ANGLES + 1)],
            second_v1_vs_first=[angles(u2[:, :1], u1[:, :k])[0] for k in range(1, KMAX_ANGLES + 1)]),
        permutation_null=dict(reps=reps, resolution=1 / reps, largest_angle_by_k=null_summary,
                              first_v1_vs_second_top2_span=dict(observed=float(obs_v1), null_q05_q50_q95=quantiles(null_v1),
                                                                fraction_null_ge_observed=float(np.mean(np.asarray(null_v1) >= obs_v1))),
                              symmetric_relative_frobenius=dict(observed=obs_frob, null_q05_q50_q95=quantiles(null_frob),
                                                                fraction_null_ge_observed=float(np.mean(np.asarray(null_frob) >= obs_frob)))),
        largest_pooled_gap_k=k_gap,
        null_median_largest_angle_at_gap_k=medians[k_gap],
        smallest_null_median_largest_angle_below_gap_k=(min(medians[k] for k in range(1, k_gap)) if k_gap > 1 else None),
        _pooled=(wa, ua))


def degenerate_block_check(wa, ua, k, ns, reps, observed, rng):
    """Is the leading k-block exactly degenerate?  Gaussian population with the top-k eigenvalues averaged."""
    lam = wa.copy()
    lam[:k] = wa[:k].mean()
    root = ua * np.sqrt(lam)
    out = dict(block_dim=k, population_leading_eigenvalue=float(lam[0]), reps=reps, observed_lambda1_over_lambdak=observed)
    for n in ns:
        r = []
        for _ in range(reps):
            v = np.sort(np.linalg.eigvalsh(cr.cov(rng.standard_normal((n, P)) @ root.T)))[::-1]
            r.append(v[0] / v[k - 1])
        out[f"n{n}_lambda1_over_lambdak_q05_q50_q95"] = quantiles(r)
    return out


def subspace_statement(sub, obs_ratio, n_half, n_full):
    """Wording generated from the computed spectrum, angles and nulls (no fixed numbers)."""
    k = sub["largest_pooled_gap_k"]
    if k < 2:
        return dict(stable_leading_subspace_dim=k, text="The largest pooled gap follows mode 1.")
    row = sub["permutation_null"]["largest_angle_by_k"][f"k{k}"]
    below = sub["smallest_null_median_largest_angle_below_gap_k"]
    at = sub["null_median_largest_angle_at_gap_k"]
    q95 = sub["degenerate_block_check"][f"n{n_full}_lambda1_over_lambdak_q05_q50_q95"][2]
    identifiable_below = below <= at
    spread_resolved = obs_ratio["pooled"] > q95
    text = (f"Leading {k}-dimensional subspace ends at the largest pooled gap (lambda_{k}/lambda_{k + 1} = "
            f"{sub['gap_ratios_lambda_k_over_k1']['pooled'][k - 1]:.2f}). Its largest half-to-half principal angle is "
            f"{row['observed_largest_angle']:.1f} deg; random {n_half}/{n_full - n_half} splits give "
            f"{row['null_q05_q50_q95'][0]:.1f}/{row['null_q05_q50_q95'][1]:.1f}/{row['null_q05_q50_q95'][2]:.1f} deg "
            f"(5/50/95%). For k<{k} the smallest null median is {below:.1f} deg")
    text += (f", so individual leading eigenvectors and the k<{k} subspaces are not identifiable at n={n_half}; "
             f"the {k}-dimensional subspace is the stable object." if not identifiable_below else
             f", not larger than at k={k}; the gap subspace is not singled out by the null.")
    text += (f" Pooled lambda_1/lambda_{k} = {obs_ratio['pooled']:.2f} exceeds the exactly-degenerate-block 95% quantile "
             f"{q95:.2f} (n={n_full}), so the leading block has a resolved spread and is not called degenerate."
             if spread_resolved else
             f" Pooled lambda_1/lambda_{k} = {obs_ratio['pooled']:.2f} is within the exactly-degenerate-block 95% "
             f"quantile {q95:.2f} (n={n_full}).")
    return dict(stable_leading_subspace_dim=k if not identifiable_below else None,
                leading_block_spread_resolved=bool(spread_resolved), text=text)


def axis_compare(base_mean, base_draws, other, geometry, boot, rng, label="axis"):
    """Matched-seed comparison of one mesh axis against the main configuration (same seeds and FFT field)."""
    obs = np.asarray(geometry["observed"], float)
    meas = np.asarray(geometry["measurement_cov"], float)
    seeds = sorted(set(base_draws) & set(other["draws"]))
    a = np.array([base_draws[s] for s in seeds])
    b = np.array([other["draws"][s] for s in seeds])
    m = len(seeds)
    ca, cb = cr.cov(a), cr.cov(b)
    ma, mb = base_mean, other["mean"]
    da, db = a - a.mean(0), b - b.mean(0)
    corr = np.sum(da * db, 1) / np.linalg.norm(da, axis=1) / np.linalg.norm(db, axis=1)
    _, ua = leading(ca, KMAX_ANGLES)
    _, ub = leading(cb, KMAX_ANGLES)

    def qpair(ix):
        xa, xb = a[ix], b[ix]
        sa, sb = cr.cov(xa), cr.cov(xb)
        return (np.trace(sb) / np.trace(sa),
                quad(obs - mb, meas + sb) - quad(obs - ma, meas + sa),
                quad(obs - mb - xb.mean(0), meas + sb) - quad(obs - ma - xa.mean(0), meas + sa))

    ratio, d_an, d_en = qpair(np.arange(m))
    bs = np.array([qpair(rng.integers(0, m, m)) for _ in range(boot)])
    qs = (0.025, 0.05, 0.95, 0.975)

    def interval(col, point, null):
        q = [float(v) for v in np.quantile(bs[:, col], qs)]
        return dict(point=float(point), paired_bootstrap_q025_q05_q95_q975=q,
                    resolved_at_95=bool(q[0] > null or q[3] < null))

    trace = interval(0, ratio, 1.0)
    shift_an, shift_en = interval(1, d_an, 0.0), interval(2, d_en, 0.0)
    q_base_an, q_other_an = quad(obs - ma, meas + ca), quad(obs - mb, meas + cb)
    resolved = trace["resolved_at_95"] or shift_an["resolved_at_95"] or shift_en["resolved_at_95"]
    classification = "resolved_truncation_systematic" if resolved else "not_resolved_by_paired_bootstrap"
    ci_t, ci_q = trace["paired_bootstrap_q025_q05_q95_q975"], shift_an["paired_bootstrap_q025_q05_q95_q975"]
    statement = (f"{label}: trace ratio {ratio:.4f} (paired 95% {ci_t[0]:.4f}-{ci_t[3]:.4f}); R105-definition quadratic "
                 f"shift {d_an:+.2f} (paired 95% {ci_q[0]:+.2f} to {ci_q[3]:+.2f}) at matched seeds "
                 f"{seeds[0]}-{seeds[-1]}. ")
    statement += ("Resolved: a truncation systematic of the base configuration, not seed noise; the base value is not "
                  "called converged and convergence beyond the tested value is untested." if resolved else
                  "Not resolved by the paired bootstrap at this seed count; convergence beyond the tested value is untested.")
    scatter = float(np.sqrt(np.mean(np.sum(da ** 2, axis=1))))
    return {"common_seeds": [seeds[0], seeds[-1], m],
            "conditional_mean_change_norm": float(np.linalg.norm(mb - ma)),
            "conditional_mean_change_meas_mahalanobis": float(np.sqrt(quad(mb - ma, meas))),
            "per_seed_difference_rms_norm": float(np.sqrt(np.mean(np.sum((b - a) ** 2, axis=1)))),
            "seed_scatter_rms_norm_reference_only": scatter,
            "per_seed_correlation_min_median": [float(corr.min()), float(np.median(corr))],
            "covariance_symmetric_relative_frobenius": sym_rel_frobenius(ca, cb),
            "trace_ratio_other_over_base": trace,
            "quadratic_matched_seeds": dict(
                analytic_mean_definition=dict(base=q_base_an, other=q_other_an, shift=shift_an,
                                              shift_from_mean_change_only=quad(obs - mb, meas + ca) - q_base_an,
                                              shift_from_covariance_change_only=quad(obs - ma, meas + cb) - q_base_an),
                ensemble_mean_definition=dict(base=quad(obs - ma - a.mean(0), meas + ca),
                                              other=quad(obs - mb - b.mean(0), meas + cb), shift=shift_en)),
            "leading8_principal_angles_deg": angles(ua, ub),
            "bootstrap_reps": boot,
            "classification": classification,
            "statement": statement,
            "convergence_beyond_tested_value": "untested"}


def fft_probe(runs):
    """Shell-monopole residual means of reduced-mesh runs; Welch z between runs that differ only in FFT."""
    rows = []
    for r in runs:
        x = np.array([r["draws"][s] for s in sorted(r["draws"])])
        n = len(x)
        rbar, sd = x.mean(0), x.std(0, ddof=1)
        rows.append(dict(config=r["identity"]["config"], run_file=r["run_file"], n_draws=n,
                         monopole_mean=[float(rbar[i]) for i in SHELL_MONOPOLES],
                         monopole_se=[float(sd[i] / np.sqrt(n)) for i in SHELL_MONOPOLES],
                         monopole_z=[float(np.sqrt(n) * rbar[i] / sd[i]) for i in SHELL_MONOPOLES]))
    pairs = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            ci, cj = rows[i]["config"], rows[j]["config"]
            diff = {k for k in ci if ci[k] != cj[k]}
            if diff == {"fft"}:
                d = np.subtract(rows[i]["monopole_mean"], rows[j]["monopole_mean"])
                se = np.hypot(rows[i]["monopole_se"], rows[j]["monopole_se"])
                pairs.append(dict(fft=[ci["fft"], cj["fft"]], monopole_mean_difference=d.tolist(),
                                  welch_z=(d / se).tolist()))
    return dict(runs=rows, fft_only_pairs=pairs)


FFT_RESOLVED_ABS_Z = 3.0


def residual_mean_statement(rm, probe):
    """Wording generated from the residual-mean statistics and the optional FFT probe."""
    mono = rm["shell_monopoles"]
    lead = rm["leading_pc_hotelling"]["leading8"]
    full = rm["full_36_hotelling"]
    text = (f"Shell-monopole residual means have z = {', '.join(f'{v:.2f}' for v in mono['z'])} (shells 0-3); "
            f"4-D monopole T^2 = {mono['hotelling']['T2']:.1f} (zero-mean expectation "
            f"{mono['hotelling']['expected_T2_if_zero_mean']:.2f}). Over the leading 8 principal directions T^2 = "
            f"{lead['T2']:.2f} (expectation {lead['expected_T2_if_zero_mean']:.2f}); "
            f"{full['share_of_T2_from_trailing_pcs_beyond_10']:.1%} of the 36-D T^2 = {full['T2']:.1f} lies beyond the "
            f"leading 10 directions (condition number {full['covariance_condition_number']:.3g}). Site means by radius: "
            + "; ".join(f"{b['radius_Mpch'][0]:g}-{b['radius_Mpch'][1]:g} Mpc/h {b['mean_kms']:.2f} km/s (z {b['z']:.1f})"
                        for b in rm["site_mean_by_radius"]) + ".")
    resolved = None
    if probe and probe["fft_only_pairs"]:
        pair = probe["fft_only_pairs"][0]
        zmax = max(abs(v) for v in pair["welch_z"])
        resolved = bool(zmax >= FFT_RESOLVED_ABS_Z)
        text += (f" FFT {pair['fft'][0]} vs {pair['fft'][1]} at fixed radial/ell: monopole-difference Welch z = "
                 f"{', '.join(f'{v:.2f}' for v in pair['welch_z'])}; ")
        text += ("the offset changes with FFT resolution, so it may be partly numerical and is not attributed to a "
                 "physical near-field monopole." if resolved else
                 "no FFT change is resolved at these seed counts; FFT convergence is not established.")
    else:
        text += " FFT dependence untested; no physical attribution."
    return dict(fft_dependence_resolved=resolved, fft_resolved_abs_z_threshold=FFT_RESOLVED_ABS_Z, text=text)


def write_json(path, obj, *, supersede=False):
    """Atomic write.  An existing identical file is kept; a differing one is replaced only with supersede=True."""
    path = Path(path)
    payload = (json.dumps(obj, indent=1, allow_nan=False) + "\n").encode()
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(payload)
            out.flush()
            os.fsync(out.fileno())
        try:
            os.link(tmp, path)
            status = "created"
        except FileExistsError:
            if path.is_file() and not path.is_symlink() and path.read_bytes() == payload:
                status = "identical_existing"
            elif not supersede:
                raise FileExistsError(f"conflicting output preserved: {path}") from None
            else:
                old = sha256_file(path)
                os.replace(tmp, path)
                status = f"superseded_sha256:{old}"
        dfd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
        return status, sha256_bytes(payload)
    finally:
        tmp.unlink(missing_ok=True)


def analysis_command(argv):
    """Command line without the write-mode flag, so an identical analysis reproduces identical bytes."""
    return [str(x) for x in argv if x != "--supersede"]


REVIEW_CORRECTIONS = [
    dict(id="F2", change="Quadratic keys renamed to state the subtracted mean "
                         "(quadratic_obs_minus_ensemble_mean_meas_plus_sample_cov); the R105 analytic-mean version, the "
                         "C(1+1/n)-inflated version and both measurement-only quadratics are reported beside it; the "
                         "residual mean is reported as a systematic (per-coefficient z with Wilcoxon and sign-flip p, "
                         "shell-monopole and leading-PC T^2, trailing-PC share of the 36-D T^2, site means by radius); "
                         "optional FFT probe runs test FFT dependence; the docstring no longer implies zero-mean residuals."),
    dict(id="F3", change="Near-degeneracy wording removed; full leading spectrum and gap ratios, principal angles for "
                         "k=1..8, v1-versus-top-k spans, permutation null of the largest angle for k=1..15 and an "
                         "exactly-degenerate-block Gaussian check; the stable subspace is identified from the largest "
                         "pooled spectral gap."),
    dict(id="F4", change="hartlap_factor_sample_only removed; replaced by a Gaussian Monte Carlo debias factor and SD of "
                         "the meas+S quadratic (Hartlap shown only as a check of the sample-only Monte Carlo)."),
    dict(id="F5", change="symmetric_relative_frobenius now uses the mean-norm denominator of "
                         "coras_reduce.split_diagnostic and is cross-checked against it; a permutation null is reported."),
    dict(id="F6", change="Mesh-axis changes reported with paired-bootstrap intervals for the trace ratio and the quadratic "
                         "shift (both definitions, split into mean and covariance parts); a resolved change is labelled a "
                         "truncation systematic and convergence beyond the tested value is marked untested; seed scatter "
                         "kept for reference only."),
    dict(id="F7", change="run_files (directory, run.json SHA-256, seed range, mean SHA-256) recorded for every input; "
                         "stale/partial draw sets rejected; atomic no-clobber write with explicit --supersede; "
                         "script, dependency and geometry digests and the command recorded."),
]


def main(argv=None):
    from scripts.r105.coras_flow import samples
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--main", type=Path, nargs="+", required=True, help="main-configuration run directories")
    p.add_argument("--radial48", type=Path)
    p.add_argument("--ell12", type=Path)
    p.add_argument("--fft-probe", type=Path, nargs="*", default=[],
                   help="reduced-mesh runs used only for the FFT dependence of the residual mean")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--supersede", action="store_true", help="replace a differing existing output")
    p.add_argument("--permutation-reps", type=int, default=2000)
    p.add_argument("--debias-reps", type=int, default=1000)
    p.add_argument("--degenerate-reps", type=int, default=400)
    p.add_argument("--bootstrap-reps", type=int, default=2000)
    a = p.parse_args(argv)
    geometry = samples()
    loaded = [load(d, geometry) for d in a.main]
    identities = {json.dumps(x["identity"], sort_keys=True) for x in loaded}
    if len(identities) != 1:
        raise ValueError("main runs differ in configuration, binary or sites")
    mean = loaded[0]["mean"]
    draws, site = {}, {}
    for x in loaded:
        if not np.array_equal(x["mean"], mean) or set(x["draws"]) & set(draws):
            raise ValueError("conditional mean differs or duplicate seeds")
        draws.update(x["draws"])
        site.update(x["site_bin_means"])
    seeds = sorted(draws)
    full = np.array([draws[s] for s in seeds])
    first, second = np.array_split(full, 2)
    s1, s2 = np.array_split(np.asarray(seeds), 2)
    meas = np.asarray(geometry["measurement_cov"], float)
    obs = np.asarray(geometry["observed"], float)

    sub = subspace(first, second, full, a.permutation_reps, np.random.default_rng(RNG_SEEDS["permutation"]))
    wa, ua = sub.pop("_pooled")
    k_gap = sub["largest_pooled_gap_k"]
    obs_ratio = {"first_half": float(sub["spectra"]["first_half"][0] / sub["spectra"]["first_half"][k_gap - 1]),
                 "second_half": float(sub["spectra"]["second_half"][0] / sub["spectra"]["second_half"][k_gap - 1]),
                 "pooled": float(wa[0] / wa[k_gap - 1])}
    sub["degenerate_block_check"] = degenerate_block_check(
        wa, ua, k_gap, (len(first), len(full)), a.degenerate_reps, obs_ratio,
        np.random.default_rng(RNG_SEEDS["degenerate_block"]))
    sub["interpretation"] = subspace_statement(sub, obs_ratio, len(first), len(full))

    halves = dict(seed_ranges=[[int(s1[0]), int(s1[-1])], [int(s2[0]), int(s2[-1])]],
                  symmetric_relative_frobenius=sym_rel_frobenius(cr.cov(first), cr.cov(second)),
                  split_diagnostic_symmetric_relative_frobenius=cr.split_diagnostic(full)["symmetric_relative_frobenius"],
                  relative_frobenius_to_second=cr.rel_diff(cr.cov(first), cr.cov(second)),
                  mean_two_sample_hotelling=dict(full_36=hotelling_two_sample(first, second),
                                                 leading8_pooled_pcs=hotelling_two_sample(first @ ua[:, :8], second @ ua[:, :8])))

    rng = np.random.default_rng(RNG_SEEDS["debias"])
    rbar = full.mean(0)
    residuals = {"obs_minus_analytic_mean": obs - mean, "obs_minus_ensemble_mean": obs - mean - rbar}
    debias = {f"n{n}": mc_debias(residuals, meas, cr.cov(full), n, a.debias_reps, rng) for n in (len(first), len(full))}

    site_bins = loaded[0]["site_bins"]
    rm = residual_mean(full, site, site_bins, np.random.default_rng(RNG_SEEDS["sign_flip"]))
    rm["halves_shell_monopole_z"] = [[float(np.sqrt(len(h)) * h[:, i].mean() / h[:, i].std(ddof=1)) for i in SHELL_MONOPOLES]
                                     for h in (first, second)]

    out = {"schema": SCHEMA, "main_identity": json.loads(identities.pop()),
           "n_common_groups": len(geometry["ids"]), "seed_range": [seeds[0], seeds[-1]], "n_seeds": len(seeds),
           "seeds_first_half": describe(first, mean, geometry), "seeds_second_half": describe(second, mean, geometry),
           "seeds_pooled": describe(full, mean, geometry),
           "halves": halves, "leading_subspace": sub, "residual_mean_systematic": rm,
           "covariance_noise_debias_gaussian_approx": debias}
    axes_rng = np.random.default_rng(RNG_SEEDS["axis_bootstrap"])
    axis_runs = []
    for name, path in (("radial48", a.radial48), ("ell12", a.ell12)):
        if path is None:
            continue
        other = load(path, geometry)
        axis_runs.append(other)
        x = np.array([other["draws"][s] for s in sorted(other["draws"])])
        out[f"axis_{name}_vs_main"] = {
            "identity": other["identity"], "run_file": other["run_file"],
            **axis_compare(mean, draws, other, geometry, a.bootstrap_reps, axes_rng,
                           label=f"{name} vs main"),
            "residual_mean_shell_monopole_z": [float(np.sqrt(len(x)) * x[:, i].mean() / x[:, i].std(ddof=1))
                                               for i in SHELL_MONOPOLES],
            "residual_mean_note": "Same seeds and FFT field as the main run: not an independent confirmation."}
    probes = [load(path, geometry) for path in a.fft_probe]
    if probes:
        out["residual_mean_fft_probe"] = fft_probe(probes)
    rm["interpretation"] = residual_mean_statement(rm, out.get("residual_mean_fft_probe"))

    from scripts.r98 import cf4_p1 as old
    out["coefficient_layout"] = dict(coefficients_per_shell=COEFFS_PER_SHELL, components=list(COMPONENT_NAMES),
                                     shell_window_centres_z=[float(c) for c in old.r95._load_h03().CENTERS],
                                     source="h03_tomography.velocity_design columns (1, n, STF) per window; "
                                            "scripts/r98/cf4_p1.py tomography (A @ y).reshape(4, 9)")
    out["claim_classes"] = {
        "quadratics": "conditional descriptive statistic (fixed CF3-calibrated growth and bulk; no calibrated p)",
        "residual_mean_systematic": "numerical-or-model systematic of the CORAS residual draws; FFT dependence is tested "
                                    "only by the probe runs; no physical attribution",
        "leading_subspace": "numerical convergence in the number of seeds",
        "axes": "numerical convergence in radial/ell truncation at fixed FFT and seeds",
        "covariance_noise_debias_gaussian_approx": "Gaussian-approximate covariance-noise correction"}
    out["physical_Pi"] = None
    out["calibrated_p"] = None
    out["scope"] = ("Conditional CORAS realization scatter given the 2MRS constraints at the CF3-calibrated growth "
                    "(f sigma8 0.405) and bulk (95, -172, 28) km/s; quadratic forms are descriptive.")
    out["inputs"] = dict(main_run_files=[x["run_file"] for x in loaded],
                         axis_run_files=[x["run_file"] for x in axis_runs],
                         fft_probe_run_files=[x["run_file"] for x in probes],
                         geometry_sha256={k: array_digest(np.asarray(geometry[k])) for k in
                                          ("ids", "radius", "weights", "observed", "measurement_cov")})
    root = Path(__file__).resolve().parents[2]
    out["provenance"] = dict(
        script=str(Path(__file__).resolve().relative_to(root)), script_sha256=sha256_file(Path(__file__).resolve()),
        dependency_sha256={str(Path(m.__file__).resolve().relative_to(root)): sha256_file(m.__file__)
                           for m in (cr, sys.modules["scripts.r105.coras_flow"], old)},
        command=analysis_command(sys.orig_argv if argv is None else ["scripts.r106.coras_stability.main", *map(str, argv)]),
        numpy=np.__version__, scipy=scipy.__version__, rng_seeds=RNG_SEEDS,
        reps=dict(permutation=a.permutation_reps, debias=a.debias_reps, degenerate=a.degenerate_reps,
                  bootstrap=a.bootstrap_reps, sign_flip=SIGN_FLIP_REPS))
    out["review_corrections"] = REVIEW_CORRECTIONS
    status, digest = write_json(a.output, out, supersede=a.supersede)
    print(f"{a.output}: {status} sha256={digest}", flush=True)


if __name__ == "__main__":
    main()
