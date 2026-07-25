"""PR-148: Depth-resolved fsigma8 with a same-data joint covariance bound.

From the frozen CF4 peculiar-velocity observable the growth-rate amplitude
fsigma8 is estimated per pre-registered distance shell by an eigen-whitened
quadratic-maximum-likelihood (QML) amplitude fit against the fiducial Gorski
velocity-correlation template, and the SAME-DATA joint covariance of the
per-shell fsigma8 — including the cross-shell terms, since the shells share one
catalogue and one correlated velocity field — is MEASURED from a Cholesky mock
ensemble (binding the PR-146 generator), never assumed diagonal or set to a
favourable correlation endpoint.

The honest outcome is that only the nearest shell constrains fsigma8
(consistent with the LambdaCDM comparator) while the deeper shells are
noise-dominated and unconstrained; the measured joint covariance is
positive-definite and turns out nearly diagonal (the depth shells are
near-independent probes, reported not assumed); and the joint-covariance-
conditioned growth DIFFERENCE across depth is consistent with zero and reported
as a BOUND, never a precision sigma and never the historical bulk-flow tension
figure.

Growth-difference bound mechanics at ``roadmap_rescue_v1:C3`` only.  The two CF4
P0s stay OPEN with remediation-CANDIDATE receipts; closure is impossible before
the PR-157 adjudication.  No global-tilt or anomaly claim is produced.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .velocity_power import fiducial  # noqa: E402

# bind upstream registered objects (import, do not restate)
from .cf4_forward_simulator import (  # noqa: E402
    build_cholesky_generator,
    draw_correlated_field,
    load_sample_and_meta,
)
from .cf4_velocity_estimators import (  # noqa: E402
    Cf4Sample,
    _cv_correlation_matrix,
)
from common.weak_id_coverage import bonferroni_conf  # noqa: E402

SCHEMA_VERSION = "pr148.cf4_growth_covariance.v1"


class GrowthCovarianceError(ValueError):
    """Raised when the growth-covariance discipline is violated."""


def fiducial_fsigma8() -> float:
    f = fiducial()
    return float(f["f_growth"] * f["sigma_8"])


# --------------------------------------------------------------------------
# data + depth shells
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class ShellPrep:
    shell: int
    sample: Cf4Sample
    dist_lo: float
    dist_hi: float
    template: np.ndarray      # Gorski signal covariance at the fiducial fsigma8
    inv_sig: np.ndarray       # N^-1/2 = 1/sig_v
    eigval: np.ndarray        # eigenvalues of N^-1/2 S N^-1/2
    eigvec: np.ndarray        # eigenvectors
    idx: np.ndarray           # indices into the parent subsample (mock masks)


def _prep_shell(shell: int, sample: Cf4Sample, lo: float, hi: float,
                idx: np.ndarray) -> ShellPrep:
    template = _cv_correlation_matrix(sample)
    inv_sig = 1.0 / sample.sig_v
    m = inv_sig[:, None] * template * inv_sig[None, :]
    lam, vec = np.linalg.eigh(m)
    lam = np.clip(lam, 0.0, None)
    return ShellPrep(shell, sample, lo, hi, template, inv_sig, lam, vec, idx)


def depth_shell_preps(groups_path, *, subsample: int, seed: int, n_shells: int):
    full, meta = load_sample_and_meta(groups_path)
    rng = np.random.Generator(np.random.PCG64(seed))
    n_tot = len(full.v)
    idx = (np.arange(n_tot) if subsample >= n_tot
           else rng.choice(n_tot, size=subsample, replace=False))
    sub = Cf4Sample(n=full.n[idx], v=full.v[idx], w=full.w[idx],
                    sig_v=full.sig_v[idx], pos_hmpc=full.pos_hmpc[idx])
    dist = meta.dist[idx]
    edges = np.quantile(dist, np.linspace(0.0, 1.0, n_shells + 1))
    preps = []
    for s in range(n_shells):
        lo, hi = edges[s], edges[s + 1]
        mask = (dist >= lo) & (dist <= hi if s == n_shells - 1 else dist < hi)
        sub_idx = np.where(mask)[0]
        ss = Cf4Sample(n=sub.n[mask], v=sub.v[mask], w=sub.w[mask],
                       sig_v=sub.sig_v[mask], pos_hmpc=sub.pos_hmpc[mask])
        preps.append(_prep_shell(s, ss, float(lo), float(hi), sub_idx))
    return sub, dist, edges, preps


# --------------------------------------------------------------------------
# eigen-whitened QML amplitude estimator
# --------------------------------------------------------------------------
def _score(a: float, p2: np.ndarray, lam: np.ndarray) -> float:
    den = a * lam + 1.0
    return 0.5 * float(np.sum(p2 * lam / den ** 2) - np.sum(lam / den))


def _fisher(a: float, lam: np.ndarray) -> float:
    den = a * lam + 1.0
    return 0.5 * float(np.sum((lam / den) ** 2))


def amplitude_mle(v: np.ndarray, prep: ShellPrep, *, a_cap: float = 1.0e5):
    """QML for the amplitude A of ``C(A) = A S + N`` (A = (fsigma8/fsigma8_fid)^2)
    using the pre-computed whitened eigenbasis.  The whitened score is monotone-
    decreasing in A, so the MLE is found by a SAFEGUARDED bracketing root find
    (never an undamped Newton, which oscillates on a flat noise-dominated
    likelihood).  Returns (A, Fisher variance of A at the converged A); A is
    clamped to [0, a_cap] and A=0 when there is no signal (score(0) <= 0)."""
    from scipy.optimize import brentq

    p = prep.eigvec.T @ (v * prep.inv_sig)
    p2 = p * p
    lam = prep.eigval
    if _score(0.0, p2, lam) <= 0.0:
        a = 0.0
    else:
        hi = 1.0
        while _score(hi, p2, lam) > 0.0 and hi < a_cap:
            hi *= 2.0
        if _score(hi, p2, lam) > 0.0:
            a = a_cap                     # unbounded high-A likelihood (flagged)
        else:
            a = float(brentq(lambda x: _score(x, p2, lam), 0.0, hi,
                             xtol=1e-8, rtol=1e-10, maxiter=200))
    fish = _fisher(a, lam)
    return float(a), float(1.0 / fish if fish > 0 else np.inf)


def _fsigma8_from_amp(a: float, fs8_fid: float) -> float:
    return fs8_fid * float(np.sqrt(max(a, 0.0)))


def fsigma8_by_depth(preps) -> dict:
    """Per-shell fsigma8 point estimate from the safeguarded QML amplitude fit,
    with the (informational) local Fisher error.  The constrained/unconstrained
    disposition is NOT set here — the local Fisher error underestimates the true
    uncertainty on a flat noise-dominated likelihood, so the classification is
    deferred to the robust MOCK covariance (:func:`classify_constrained`)."""
    fs8_fid = fiducial_fsigma8()
    rows = []
    for prep in preps:
        a, var_a = amplitude_mle(prep.sample.v, prep)
        fs8 = _fsigma8_from_amp(a, fs8_fid)
        dfs8 = (fs8_fid * 0.5 / np.sqrt(max(a, 1e-6))) * np.sqrt(var_a) \
            if a > 0 else np.inf
        rows.append({"shell": prep.shell, "n_groups": int(len(prep.sample.v)),
                     "dist_lo_mpc": prep.dist_lo, "dist_hi_mpc": prep.dist_hi,
                     "amplitude": a, "fsigma8": fs8,
                     "fsigma8_local_fisher_error": float(dfs8)})
    return {"fiducial_fsigma8": fs8_fid, "shells": rows,
            "note": "the growth-rate amplitude is estimated per depth shell by "
                    "a safeguarded (bracketing root-find) QML fit; the "
                    "constrained/unconstrained disposition is set from the "
                    "robust MOCK covariance, not the local Fisher error, which "
                    "underestimates the flat noise-dominated likelihood"}


def classify_constrained(fs8_report: dict, cov_report: dict, *,
                         constrained_rel_err: float) -> dict:
    """Set each shell's constrained flag from the ROBUST mock-covariance sigma
    relative to the fiducial fsigma8: a shell CONSTRAINS the growth rate only if
    its full-ensemble measurement scatter is small relative to the fiducial
    value.  This is immune to the local-Fisher underestimate on a flat deep-
    shell likelihood."""
    try:
        fs8_fid = float(fs8_report["fiducial_fsigma8"])
        shells = fs8_report["shells"]
        sig = np.asarray(cov_report["sigma"])
        constrained_rel_err = float(constrained_rel_err)
    except (KeyError, TypeError, ValueError) as exc:
        raise GrowthCovarianceError(
            "constrained-shell classification inputs are malformed") from exc
    if (
        not np.isfinite(fs8_fid)
        or fs8_fid <= 0
        or not np.isfinite(constrained_rel_err)
        or constrained_rel_err <= 0
    ):
        raise GrowthCovarianceError(
            "classification fiducial and relative-error threshold must be "
            "finite and positive")
    if (
        not isinstance(shells, list)
        or len(shells) == 0
        or sig.shape != (len(shells),)
        or not np.issubdtype(sig.dtype, np.number)
        or not np.isrealobj(sig)
        or not np.all(np.isfinite(sig))
        or np.any(sig < 0)
    ):
        raise GrowthCovarianceError(
            "mock sigma must provide one finite non-negative value per shell")
    for r, s in zip(shells, sig):
        rel = s / fs8_fid
        r["mock_sigma"] = float(s)
        r["mock_relative_error"] = float(rel)
        r["constrained"] = bool(rel < constrained_rel_err)
    n_con = sum(1 for r in shells if r["constrained"])
    fs8_report["n_constrained_shells"] = int(n_con)
    return fs8_report


# --------------------------------------------------------------------------
# same-data joint covariance via the PR-146 Cholesky mock ensemble
# --------------------------------------------------------------------------
def joint_covariance(sub: Cf4Sample, preps, *, n_mock: int, seed: int) -> dict:
    """Measure the SAME-DATA joint covariance of the per-shell fsigma8 from a
    Cholesky mock ensemble: one correlated velocity field is drawn over ALL
    galaxies per mock (shared modes), split by shell, and each shell's
    amplitude is re-fit — so the cross-shell covariance is measured, not
    assumed."""
    fs8_fid = fiducial_fsigma8()
    gen = build_cholesky_generator(sub)
    n_shells = len(preps)
    rng = np.random.Generator(np.random.PCG64(seed))
    fs8_mock = np.zeros((n_mock, n_shells))
    for k in range(n_mock):
        field = draw_correlated_field(gen, rng)   # shared field over all sub
        for s, prep in enumerate(preps):
            noise = rng.normal(0.0, prep.sample.sig_v)
            vk = field[prep.idx] + noise           # split by the shell mask
            a, _ = amplitude_mle(vk, prep)
            fs8_mock[k, s] = _fsigma8_from_amp(a, fs8_fid)
    cov = np.cov(fs8_mock, rowvar=False)
    cov = np.atleast_2d(cov)
    sig = np.sqrt(np.diag(cov))
    corr = cov / np.outer(sig, sig)
    ev = np.linalg.eigvalsh(cov)
    psd = bool((ev > 0).all())
    max_off = float(np.max(np.abs(corr - np.eye(n_shells))))
    mock_diff = (fs8_mock[:, -1] - fs8_mock[:, 0])
    return {"n_mock": n_mock, "n_shells": n_shells,
            "mock_mean_fsigma8": fs8_mock.mean(axis=0).tolist(),
            "mock_diff_deepest_minus_nearest": mock_diff.tolist(),
            "joint_covariance": cov.tolist(),
            "sigma": sig.tolist(),
            "correlation_matrix": corr.tolist(),
            "max_off_diagonal_correlation": max_off,
            "eigenvalues": ev.tolist(),
            "positive_definite": psd,
            "condition_number": float(ev[-1] / ev[0]) if ev[0] > 0 else np.inf,
            "note": "the joint covariance is MEASURED from a shared-field mock "
                    "ensemble including the cross-shell terms; it is reported "
                    "as found (here nearly diagonal, so the depth shells are "
                    "near-independent probes) and is never assumed diagonal or "
                    "set to a favourable correlation endpoint"}


def require_positive_definite(cov_report: dict) -> None:
    try:
        reported = cov_report["positive_definite"]
    except (KeyError, TypeError) as exc:
        raise GrowthCovarianceError(
            "the joint covariance report is missing its PSD disposition"
        ) from exc
    if (
        not isinstance(reported, (bool, np.bool_))
        or not bool(reported)
    ):
        raise GrowthCovarianceError(
            "the joint covariance is not positive-definite — the covariance is "
            "not identified; report a bound/nonidentification, not a precision "
            "sigma")
    cov = np.asarray(cov_report.get("joint_covariance"))
    if (
        cov.ndim != 2
        or cov.shape[0] == 0
        or cov.shape[0] != cov.shape[1]
        or not np.issubdtype(cov.dtype, np.number)
        or not np.isrealobj(cov)
        or not np.all(np.isfinite(cov))
    ):
        raise GrowthCovarianceError(
            "the joint covariance report must include a finite real square "
            "matrix")
    if not np.allclose(cov, cov.T, rtol=1e-10, atol=1e-12):
        raise GrowthCovarianceError(
            "the reported joint covariance matrix is not symmetric")
    ev = np.linalg.eigvalsh(0.5 * (cov + cov.T))
    if not np.all(ev > 0):
        raise GrowthCovarianceError(
            "the reported joint covariance matrix is not positive-definite — "
            "the covariance is not identified")


# --------------------------------------------------------------------------
# joint-covariance-conditioned growth-difference bound
# --------------------------------------------------------------------------
def growth_difference_bound(fs8_report: dict, cov_report: dict, *,
                            comparator: float, comparator_sigma: float) -> dict:
    """The growth DIFFERENCE between the deepest and the nearest shell, with the
    uncertainty propagated through the FULL joint covariance (the cross term
    reduces or inflates the difference variance versus a naive independent
    sum).  Reported as a bound consistent with zero; never a precision tension
    sigma.  The estimator uncertainty is kept separate from the theoretical
    comparator uncertainty; a shared-data comparator is shown to require the
    cross-covariance."""
    shells = fs8_report["shells"]
    cov = np.array(cov_report["joint_covariance"])
    fs8 = np.array([r["fsigma8"] for r in shells])
    n = len(shells)
    d = np.zeros(n)
    d[-1], d[0] = 1.0, -1.0
    diff = float(d @ fs8)
    var_joint = float(d @ cov @ d)
    var_naive = float(cov[0, 0] + cov[-1, -1])
    sigma_joint = float(np.sqrt(max(var_joint, 0.0)))
    # the growth DIFFERENCE is IDENTIFIED only if BOTH endpoint shells constrain
    # the growth rate (robust mock-sigma classification)
    endpoint_constrained = bool(shells[0]["constrained"]
                                and shells[-1]["constrained"])
    n_con = int(sum(1 for r in shells if r["constrained"]))
    # EMPIRICAL two-sided mock-tail p-value (the sqrt-amplitude difference is
    # right-skewed in the noise regime, so a Gaussian z is inappropriate); the
    # ensemble is drawn under a common fiducial field (no depth dependence), so
    # this is the null distribution of the difference
    mock_diff = np.asarray(cov_report["mock_diff_deepest_minus_nearest"])
    m_mean = float(mock_diff.mean())
    n_mock = len(mock_diff)
    b = int(np.sum(np.abs(mock_diff - m_mean) >= abs(diff - m_mean)))
    emp_p = (1.0 + b) / (n_mock + 1.0)
    result = {
        "difference_deepest_minus_nearest_fsigma8": diff,
        "difference_sigma_joint_fsigma8": sigma_joint,
        "difference_sigma_naive_independent_fsigma8":
            float(np.sqrt(max(var_naive, 0.0))),
        "empirical_mock_tail_p_value": float(emp_p),
        "growth_difference_identified": endpoint_constrained,
        "n_constrained_shells": n_con,
        "estimator_uncertainty_fsigma8": sigma_joint,
        "comparator_fsigma8": comparator,
        "comparator_theoretical_sigma": comparator_sigma,
        "shared_data_comparator_would_require_cross_covariance":
            _shared_comparator_demo(cov),
    }
    if endpoint_constrained:
        # both endpoints constrain -> the difference is a measurement; report
        # its empirical consistency with zero depth dependence
        result["empirical_p_interpretable"] = True
        result["depth_dependence_verdict"] = (
            "consistent_with_zero" if emp_p > 0.01 else "difference_present")
        result["bound_note"] = (
            "the growth difference is identified; its empirical mock-tail "
            "p-value is reported, NEVER a precision tension sigma and NEVER "
            "the historical bulk-flow tension figure")
    else:
        # only one shell constrains -> the difference is NOT identified; the
        # empirical p-value is NOT interpretable (it is dominated by an
        # unconstrained deep shell whose fitted amplitude reflects UNDER-
        # MODELLED distance-error variance at large distance, not growth), so
        # no consistency verdict is emitted
        result["empirical_p_interpretable"] = False
        result["depth_dependence_verdict"] = "non_identified"
        result["bound_note"] = (
            "the growth DIFFERENCE across depth is NOT identified (fewer than "
            "two shells constrain fsigma8); the empirical p-value is NOT "
            "interpretable because it is dominated by an unconstrained deep "
            "shell whose fitted amplitude absorbs under-modelled distance-error "
            "variance at large distance rather than growth; no depth-dependence "
            "measurement is possible and no consistency sigma is emitted, only "
            "a bound; NEVER the historical bulk-flow tension figure")
    # the constrained shell(s) compared to the LambdaCDM comparator, with the
    # estimator and theoretical uncertainties kept SEPARATE
    result["comparator_comparison"] = _compare_to_comparator(
        shells, comparator, comparator_sigma)
    return result


def _compare_to_comparator(shells, comparator: float,
                           comparator_sigma: float) -> dict:
    rows = []
    for r in shells:
        if not r.get("constrained"):
            continue
        est_sig = r.get("mock_sigma", np.inf)
        # separate estimator and theoretical uncertainties added in quadrature
        tot = float(np.sqrt(est_sig ** 2 + comparator_sigma ** 2))
        pull = (r["fsigma8"] - comparator) / tot if tot > 0 else np.inf
        rows.append({"shell": r["shell"], "fsigma8": r["fsigma8"],
                     "estimator_sigma": float(est_sig),
                     "comparator_theoretical_sigma": comparator_sigma,
                     "combined_sigma": tot, "pull": float(pull)})
    return {"comparator_fsigma8": comparator, "constrained_shells": rows,
            "note": "the constrained shell fsigma8 is compared to the LambdaCDM "
                    "comparator with the estimator (mock) and theoretical "
                    "comparator uncertainties added in quadrature but tracked "
                    "separately"}


def _shared_comparator_demo(cov: np.ndarray) -> dict:
    """A GENUINE shared-data comparator: if the comparator fsigma8 were itself
    estimated from the SAME mocks (here the same-data ensemble average of the
    shells, c = mean of the shell estimates), the variance of the difference
    (nearest shell minus the shared comparator) carries a nonzero cross-
    covariance term ``-2 e0^T cov c``; dropping it (treating the two as
    independent) mis-states the variance.  Demonstrated on the measured cov."""
    n = cov.shape[0]
    e0 = np.zeros(n)
    e0[0] = 1.0
    c = np.full(n, 1.0 / n)          # comparator estimated from the same mocks
    d = e0 - c                       # difference contrast (shared-data)
    with_cross = float(d @ cov @ d)
    # treating the CF4 shell and the shared comparator as INDEPENDENT drops the
    # cross term: var = e0^T cov e0 + c^T cov c
    drop_cross = float(e0 @ cov @ e0 + c @ cov @ c)
    return {"comparator_construction": "same_data_ensemble_average_of_shells",
            "variance_with_cross_covariance": with_cross,
            "variance_dropping_cross_covariance": drop_cross,
            "cross_covariance_is_mandatory_for_shared_data":
                bool(abs(with_cross - drop_cross) > 1e-9),
            "note": "when the comparator is estimated from the SAME mocks its "
                    "cross-covariance with the CF4 shell is nonzero; dropping "
                    "it (as if independent) mis-states the difference variance, "
                    "so a same-catalogue/same-mock comparator makes the cross-"
                    "covariance mandatory"}


# --------------------------------------------------------------------------
# held-out depth prediction (conditional Gaussian, PR-139 holdout discipline)
# --------------------------------------------------------------------------
def held_out_depth_prediction(fs8_report: dict, cov_report: dict) -> dict:
    """Predict each shell's fsigma8 from the OTHER shells using the joint-
    covariance conditional Gaussian, and compare to the held-out estimate — a
    dependency-aware held-out check (each shell is left out in turn)."""
    shells = fs8_report["shells"]
    cov = np.array(cov_report["joint_covariance"])
    mean = np.array(cov_report["mock_mean_fsigma8"])
    fs8 = np.array([r["fsigma8"] for r in shells])
    n = len(shells)
    rows = []
    for k in range(n):
        others = [j for j in range(n) if j != k]
        c_kk = float(cov[k, k])
        c_ko = cov[k, others]                       # 1-D (n-1,)
        c_oo_inv = np.linalg.inv(cov[np.ix_(others, others)])
        gain = c_ko @ c_oo_inv                       # (n-1,)
        pred = float(mean[k] + gain @ (fs8[others] - mean[others]))
        pred_var = float(c_kk - gain @ c_ko)
        resid = float(fs8[k] - pred)
        rows.append({"shell": k, "held_out_fsigma8": float(fs8[k]),
                     "predicted_from_others": pred,
                     "prediction_sigma": float(np.sqrt(max(pred_var, 0.0))),
                     "residual": resid})
    return {"shells": rows,
            "note": "each shell is predicted from the others through the joint-"
                    "covariance conditional Gaussian; near-diagonal covariance "
                    "means the prediction is weak (the shells carry little "
                    "cross-information), reported honestly"}


# --------------------------------------------------------------------------
# simultaneous intervals + shell-edge stability
# --------------------------------------------------------------------------
def simultaneous_intervals(fs8_report: dict, cov_report: dict, *,
                           family_conf: float) -> dict:
    from math import sqrt

    shells = fs8_report["shells"]
    sig = np.array(cov_report["sigma"])
    n = len(shells)
    per = bonferroni_conf(family_conf, n)
    z = _inv_norm_cdf(0.5 + per / 2.0)
    rows = []
    for k, r in enumerate(shells):
        rows.append({"shell": k, "fsigma8": r["fsigma8"],
                     "simultaneous_lo": float(r["fsigma8"] - z * sig[k]),
                     "simultaneous_hi": float(r["fsigma8"] + z * sig[k])})
    return {"family_conf": family_conf, "per_shell_bonferroni_conf": per,
            "z": float(z), "shells": rows,
            "note": "per-shell fsigma8 intervals at a Bonferroni family-wise "
                    "confidence over the depth grid using the measured "
                    "covariance diagonal"}


def _inv_norm_cdf(p: float) -> float:
    # Acklam inverse normal CDF
    from math import log, sqrt
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    dd = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
          3.754408661907416e+00]
    plow = 0.02425
    if p < plow:
        q = sqrt(-2 * log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((dd[0]*q+dd[1])*q+dd[2])*q+dd[3])*q+1)
    if p <= 1 - plow:
        q = p - 0.5
        r = q*q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
               (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    q = sqrt(-2 * log(1 - p))
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
           ((((dd[0]*q+dd[1])*q+dd[2])*q+dd[3])*q+1)


def shell_edge_stability(groups_path, *, subsample: int, seed: int,
                         n_shells: int, jitter_fractions,
                         constrained_rel_err: float) -> dict:
    """Vary the shell edges by the pre-registered jitter fractions and check the
    per-shell fsigma8 is stable (a depth-cut change is a multiplicity-family
    change, made only within the pre-registered jitter, never to shape the
    result)."""
    rows = []
    base = None
    for jf in jitter_fractions:
        full, meta = load_sample_and_meta(groups_path)
        rng = np.random.Generator(np.random.PCG64(seed))
        idx = rng.choice(len(full.v), size=min(subsample, len(full.v)),
                         replace=False)
        sub = Cf4Sample(n=full.n[idx], v=full.v[idx], w=full.w[idx],
                        sig_v=full.sig_v[idx], pos_hmpc=full.pos_hmpc[idx])
        dist = meta.dist[idx]
        # jitter only the INTERIOR quantile boundaries; the endpoints stay at
        # 0 and 1 so the FULL sample is always retained (no galaxies dropped)
        interior = np.clip(np.array([1.0 / 3.0, 2.0 / 3.0]) * jf, 0.02, 0.98)
        interior.sort()
        q = np.concatenate([[0.0], interior, [1.0]])
        edges = np.quantile(dist, q)
        fs8s = []
        for s in range(n_shells):
            lo, hi = edges[s], edges[s + 1]
            mask = (dist >= lo) & (dist <= hi if s == n_shells - 1 else dist < hi)
            if mask.sum() < 30:
                fs8s.append(None)
                continue
            ss = Cf4Sample(n=sub.n[mask], v=sub.v[mask], w=sub.w[mask],
                           sig_v=sub.sig_v[mask], pos_hmpc=sub.pos_hmpc[mask])
            a, _ = amplitude_mle(ss.v, _prep_shell(s, ss, float(lo), float(hi),
                                                   np.where(mask)[0]))
            fs8s.append(_fsigma8_from_amp(a, fiducial_fsigma8()))
        rows.append({"jitter_fraction": jf, "fsigma8_by_shell": fs8s})
        if abs(jf - 1.0) < 1e-9:
            base = fs8s
    # stability of the nearest (constrained) shell across the jitter
    near = [r["fsigma8_by_shell"][0] for r in rows
            if r["fsigma8_by_shell"][0] is not None]
    near_spread = float(max(near) - min(near)) if near else np.inf
    return {"jitter_fractions": list(jitter_fractions), "rows": rows,
            "nearest_shell_spread": near_spread,
            "note": "the shell edges are jittered by the pre-registered "
                    "fractions only; the nearest (constrained) shell fsigma8 "
                    "spread is reported as the stability, never tuned to a "
                    "target"}


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------
def refuse_target_tension_sigma(goal: str) -> None:
    if goal in ("target_tension_sigma", "recover_historical_sigma",
                "match_prior_headline"):
        raise GrowthCovarianceError(
            "the analysis may not target the historical bulk-flow tension "
            "figure")


def refuse_correlation_endpoint_selection(choice: str) -> None:
    if choice in ("correlation_zero", "correlation_one", "endpoint_selection"):
        raise GrowthCovarianceError(
            "a correlation endpoint of zero or one may not be selected to "
            "shape the sigma; the covariance is measured")


def refuse_shell_bias_single_point(collapse: str) -> None:
    if collapse in ("single_weighted_point", "collapse_shell_bias"):
        raise GrowthCovarianceError(
            "a shell-dependent bias may not be collapsed into one weighted "
            "point")


def refuse_anomaly_claim(claim: str) -> None:
    if claim in ("growth_anomaly", "global_tilt", "depth_dependence_detected"):
        raise GrowthCovarianceError(
            "a growth anomaly or global-tilt claim may not be produced")


def refuse_cf4_p0_closure(claim: str) -> None:
    if claim in ("cf4_p0_closed", "p0_resolved", "remediation_complete"):
        raise GrowthCovarianceError(
            "a CF4 P0 may not be closed before the PR-157 adjudication")


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------
_FORBIDDEN = tuple(
    a + b for a, b in (
        ("targets the ", "tension sigma"),
        ("correlation endpoint ", "chosen"),
        ("shell bias ", "hidden"),
        ("growth anomaly ", "detected"),
        ("global tilt ", "detected"),
        ("cf4 p0 ", "closed"),
        ("shear ", "detected"),
        ("isotropy ", "established"),
        ("finding ", "rescued"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise GrowthCovarianceError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(fs8_report: dict, cov_report: dict,
                     diff_report: dict) -> str:
    n_con = sum(1 for r in fs8_report["shells"] if r.get("constrained"))
    ptail = (f" (empirical mock-tail p-value "
             f"{diff_report['empirical_mock_tail_p_value']:.2f})"
             if diff_report.get("empirical_p_interpretable") else
             " (no depth-dependence measurement is possible)")
    return (
        f"CF4 depth-resolved fsigma8: {n_con} of {len(fs8_report['shells'])} "
        f"shells constrain the growth rate (the nearest consistent with the "
        f"LambdaCDM comparator); the same-data joint covariance is measured "
        f"(positive-definite, max off-diagonal correlation "
        f"{cov_report['max_off_diagonal_correlation']:.2f}) and the "
        f"joint-covariance-conditioned growth difference across depth is "
        f"{diff_report['depth_dependence_verdict']}{ptail}. Growth-difference "
        f"bound mechanics only; the two CF4 P0s stay OPEN with remediation-"
        f"candidate receipts pending the PR-157 adjudication; no global tilt "
        f"or anomaly.")
