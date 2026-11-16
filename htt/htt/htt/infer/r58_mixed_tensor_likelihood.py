"""Full-covariance Gaussian carriers for mixed polar/STF kinematic targets.

This is conventional GLS, not an improvement on the exact Gaussian likelihood.
The carrier retains J, t, q0 and log(det C), where
    -2 log L(theta) = theta.T J theta - 2 t.T theta + q0
                     + log(det C) + n log(2 pi).
J is named ``precision`` to avoid confusing it with the five-view F observable.
All probability statements are conditional on the supplied, fixed SPD C and
linear design. Estimated or misspecified covariances need external calibration.
Carriers obtained with different data operators are different experiments;
their normalized likelihoods must not be used for cross-operator model odds.

Parameter units are explicit in caller-supplied scales. Singular response
directions stay unidentified. No ridge, zero-variance prior or synthetic null
is introduced. A singular covariance returned below describes an estimator
representative, not bounded uncertainty in unidentified directions.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
from scipy import linalg, stats


def _array(value, name: str, ndim: int) -> np.ndarray:
    a = np.asarray(value, dtype=float)
    if a.ndim != ndim or not np.isfinite(a).all():
        raise ValueError(f"{name} must be a finite {ndim}-D array")
    return a


def fit_linear(y, cov, design, parameter_scale=None, *, rank_rtol: float = 1e-12) -> dict:
    """Fit y = design @ theta + N(0,cov), preserving cross-block covariance.

    ``parameter_scale[j]`` is a positive characteristic size in parameter j's
    units. Rank is computed for C**(-1/2) design diag(parameter_scale), using
    the stated relative singular-value threshold. The returned representative
    minimizes the Euclidean norm of theta / parameter_scale. In a singular
    problem the representative and its full covariance depend on this gauge;
    only estimable contrasts and their variances are gauge independent.
    A second column-equilibrated rank check protects estimability from units.
    If these numerical ranks disagree, fitting fails closed; the caller must
    choose an explicit rank/scale model before publishing calibrated tests.
    Chi-square calibration assumes that discarded singular modes are truly
    zero in the declared model. Truncating a genuinely nonzero response can
    otherwise produce noncentral residuals under truths in that mode.
    """
    y = _array(y, "y", 1)
    c = _array(cov, "covariance", 2)
    x = _array(design, "design", 2)
    n, p = x.shape
    if n == 0 or p == 0 or y.shape != (n,) or c.shape != (n, n):
        raise ValueError("need n,p > 0, y(n), covariance(n,n), design(n,p)")
    if not np.isfinite(rank_rtol) or not 0 < rank_rtol < 1:
        raise ValueError("rank_rtol must be finite and between 0 and 1")
    magnitude = float(np.max(np.abs(c)))
    if magnitude == 0 or np.max(np.abs(c - c.T)) > 1e-10 * magnitude:
        raise ValueError("covariance must be symmetric positive definite")
    c = 0.5 * (c + c.T)
    try:
        chol = linalg.cholesky(c, lower=True, check_finite=False)
    except linalg.LinAlgError as exc:
        raise ValueError("covariance must be symmetric positive definite") from exc
    scale = np.ones(p) if parameter_scale is None else _array(parameter_scale, "parameter_scale", 1)
    if scale.shape != (p,) or np.any(scale <= 0):
        raise ValueError("parameter_scale must have p finite positive entries")
    yw = linalg.solve_triangular(chol, y, lower=True, check_finite=False)
    xw = linalg.solve_triangular(chol, x, lower=True, check_finite=False)
    scaled = xw * scale
    if not np.isfinite(scaled).all():
        raise ValueError("scaled design overflowed; use physically meaningful units/scales")
    # Economy SVD avoids an n by n U for tall designs; for p > n, full V is
    # necessary to retain every null direction.
    u, singular, vt = linalg.svd(scaled, full_matrices=p > n, check_finite=False)
    rank = int(np.count_nonzero(singular > rank_rtol * singular[0])) if singular.size and singular[0] > 0 else 0
    vr = vt[:rank].T
    projected = u[:, :rank].T @ yw
    phi = vr @ (projected / singular[:rank]) if rank else np.zeros(p)
    estimate = scale * phi
    cov_phi = (vr / singular[:rank]) @ (vr / singular[:rank]).T if rank else np.zeros((p, p))
    parameter_cov = scale[:, None] * cov_phi * scale[None, :]
    null_scaled = vt[rank:].T.copy()
    null_original = scale[:, None] * null_scaled
    # Estimability needs a separate, unit-equilibrated chart. The scale of a
    # user's parameter gauge can make an actually nonzero null projection
    # arbitrarily small. Conversely, a termwise relative cancellation test
    # mistakes a roundoff-sized null entry for real non-identifiability.
    column_norms = np.linalg.norm(xw, axis=0)
    eq_scale = np.ones(p)
    nonzero_columns = column_norms > 0
    eq_scale[nonzero_columns] = 1.0 / column_norms[nonzero_columns]
    if not np.isfinite(eq_scale).all():
        raise ValueError("design column norms underflowed; rescale the experiment")
    _, eq_singular, eq_vt = linalg.svd(xw * eq_scale, full_matrices=p > n, check_finite=False)
    eq_rank = int(np.count_nonzero(eq_singular > rank_rtol * eq_singular[0])) if eq_singular.size and eq_singular[0] > 0 else 0
    if rank != eq_rank:
        raise ValueError(f"numerically unresolved rank disagreement: declared-scale rank {rank}, column-equilibrated rank {eq_rank}; revise parameter scales/rank tolerance before inference")
    identification_status = "NUMERICAL_RANK_AGREEMENT"
    resid = yw - u[:, :rank] @ projected
    precision = xw.T @ xw
    score = xw.T @ yw
    q0 = float(yw @ yw)
    residual_chi2 = float(resid @ resid)
    wald = float(projected @ projected)
    dof = n - rank
    logdet = float(2 * np.log(np.diag(chol)).sum())
    # This centered linear term also retains tiny discarded singular modes;
    # centered log L is algebraically exact for the original design, even
    # when rank is interpreted at finite numerical tolerance.
    centered_score = xw.T @ (yw - xw @ estimate)
    actual_residual = yw - xw @ estimate
    result = {
        "estimate": estimate,
        "covariance": 0.5 * (parameter_cov + parameter_cov.T),
        "precision": 0.5 * (precision + precision.T),
        "score": score,
        # The quadratic sufficient statistics are retained above. This PSD
        # factor is a numerical representation used by the evaluator: forming
        # delta.T J delta can produce a large negative value far along a null
        # direction, from cancellation in the rounded matrix J.
        "likelihood_factor": xw,
        "likelihood_offset": yw,
        "null_basis": null_original,
        "_scaled_null_basis": null_scaled,
        "_estimability_scale": eq_scale,
        "_estimability_null_basis": eq_vt[eq_rank:].T.copy(),
        "_zero_design_columns": ~nonzero_columns,
        "parameter_scale": scale.copy(),
        "singular_values_scaled": singular,
        "singular_values_equilibrated": eq_singular,
        "rank_rtol": float(rank_rtol),
        "rank": rank,
        "rank_equilibrated": eq_rank,
        "identification_status": identification_status,
        "n_parameters": p,
        "n_observed": n,
        "dof": dof,
        "residual_chi2": residual_chi2,
        "null_chi2": q0,
        "wald": wald,
        "adequacy_p": float(stats.chi2.sf(residual_chi2, dof)) if dof else None,
        "null_p": float(stats.chi2.sf(q0, n)),
        "wald_p": float(stats.chi2.sf(wald, rank)) if rank else 1.0,
        "logdet_cov": logdet,
        "q0": q0,
        "_centered_score": centered_score,
        "_centered_q0": float(actual_residual @ actual_residual),
        "law": "fixed-covariance Gaussian linear experiment",
        "covariance_role": "estimator representative; use null_basis for unidentified directions",
        "rank_calibration_condition": "discarded modes are zero in the declared model; a truncated nonzero response need not have central residual chi-square",
    }
    for key in ("estimate", "covariance", "precision", "score", "q0", "logdet_cov"):
        if not np.isfinite(result[key]).all():
            raise ValueError(f"{key} overflowed; rescale the input experiment")
    return result


def gaussian_log_likelihood(fit: Mapping, theta) -> float:
    """Normalized log L in this fixed experiment; q0 and logdet are retained.

    The retained whitened factor evaluates a squared residual, preserving
    nonnegativity even far along an unidentified direction. J,t,q0 still give
    the algebraically sufficient carrier; a minimal singular carrier without
    the factor is rejected because its rounded J need not preserve its null
    space under quadratic evaluation at arbitrarily large displacements.
    """
    th = _array(theta, "theta", 1)
    if th.shape != np.asarray(fit["estimate"]).shape:
        raise ValueError("theta has the wrong number of components")
    if "likelihood_factor" in fit and "likelihood_offset" in fit:
        residual = np.asarray(fit["likelihood_offset"]) - np.asarray(fit["likelihood_factor"]) @ th
        chi2 = float(residual @ residual)
    elif fit["rank"] < fit["n_parameters"]:
        raise ValueError("stable evaluation of a singular carrier requires its likelihood_factor and likelihood_offset")
    elif "_centered_q0" in fit and "_centered_score" in fit:
        delta = th - fit["estimate"]
        chi2 = fit["_centered_q0"] - 2 * float(fit["_centered_score"] @ delta) + float(delta @ fit["precision"] @ delta)
    else:
        # A persisted minimal carrier need contain only J, t and q0, besides
        # the normalization and parameter layout. Extended precision reduces
        # (but cannot eliminate) cancellation in this uncentered expression.
        th_ext = np.asarray(th, dtype=np.longdouble)
        j_ext = np.asarray(fit["precision"], dtype=np.longdouble)
        t_ext = np.asarray(fit["score"], dtype=np.longdouble)
        chi2 = float(np.longdouble(fit["q0"]) - 2 * (t_ext @ th_ext) + th_ext @ j_ext @ th_ext)
    return -0.5 * (chi2 + fit["logdet_cov"] + fit["n_observed"] * math.log(2 * math.pi))


def linear_interval(fit: Mapping, contrast, level: float = 0.95, simultaneous: bool = True) -> dict:
    """Support interval of contrast @ theta; unidentified contrasts are unbounded.

    ``simultaneous=True`` projects the one rank-r confidence cylinder, with
    chi2_r(level) radius, so all linear contrasts share its simultaneous
    guarantee. ``False`` gives a pointwise normal interval for a fixed contrast.
    These guarantees require the stated fixed-covariance Gaussian law.
    """
    if not np.isfinite(level) or not 0 < level < 1:
        raise ValueError("level must lie strictly between 0 and 1")
    if not isinstance(simultaneous, (bool, np.bool_)):
        raise ValueError("simultaneous must be boolean")
    v = _array(contrast, "contrast", 1)
    if v.shape != np.asarray(fit["estimate"]).shape:
        raise ValueError("contrast has the wrong number of components")
    scaled = v * fit["_estimability_scale"]
    null_component = np.asarray(fit["_estimability_null_basis"]).T @ scaled
    zero_contrast = bool(np.all(v == 0))
    rank_agrees = fit["identification_status"] == "NUMERICAL_RANK_AGREEMENT"
    zero_column_component = bool(np.any(v[np.asarray(fit["_zero_design_columns"], dtype=bool)] != 0))
    identified = zero_contrast or (rank_agrees and not zero_column_component and
                                  bool(np.linalg.norm(null_component) <= 1e-10 * np.linalg.norm(scaled)))
    rank = int(fit["rank"])
    c2 = float(stats.chi2.ppf(level, rank)) if simultaneous and rank else (0.0 if simultaneous else float(stats.chi2.ppf(level, 1)))
    if not identified:
        return {"identified": False, "lower": -math.inf, "upper": math.inf,
                "estimate": None, "sd": math.inf, "c2": c2, "level": float(level),
                "simultaneous": bool(simultaneous), "null_component_norm_scaled": float(np.linalg.norm(null_component)),
                "identification_status": fit["identification_status"]}
    estimate = float(v @ fit["estimate"])
    variance = float(v @ fit["covariance"] @ v)
    # Roundoff of a PSD quadratic form may be slightly negative; larger
    # inconsistencies indicate a malformed carrier and are not hidden.
    tol = 1e-12 * max(float(np.linalg.norm(v)**2 * np.linalg.norm(fit["covariance"], 2)), np.finfo(float).tiny)
    if variance < -tol:
        raise ValueError("carrier covariance gives a negative contrast variance")
    sd = math.sqrt(max(variance, 0.0))
    radius = math.sqrt(c2) * sd
    return {"identified": True, "lower": estimate - radius, "upper": estimate + radius,
            "estimate": estimate, "sd": sd, "c2": c2, "level": float(level),
            "simultaneous": bool(simultaneous), "null_component_norm_scaled": float(np.linalg.norm(null_component)),
            "identification_status": fit["identification_status"]}


def robust_interval(fits: Sequence[Mapping], contrast, level: float = 0.95, simultaneous: bool = True) -> dict:
    """Interval hull of the projected finite union of confidence cylinders.

    The target, coordinate units and scientific meaning must be common across
    models. Coverage is conditional on at least one listed model being valid;
    arbitrary omitted systematics are not covered. This is no new theorem.
    """
    fits = list(fits)
    if not fits:
        raise ValueError("need at least one nuisance model")
    rows = [linear_interval(f, contrast, level, simultaneous) for f in fits]
    return {"identified_in_all_models": all(row["identified"] for row in rows),
            "lower": min(row["lower"] for row in rows), "upper": max(row["upper"] for row in rows),
            "per_model": rows, "model_count": len(rows), "level": float(level),
            "simultaneous": bool(simultaneous), "definition_id": "R7_R9_FINITE_MODEL_UNION_LINEAR_IMAGE",
            "region_representation": "interval hull; per_model preserves potentially disconnected projected union",
            "assumption": "one included model is valid; common estimand and units across models"}


def robust_null_p(fits: Sequence[Mapping], *, same_hypothesis: bool, p_field: str = "null_p") -> float:
    """Max model-wise p for a union null; no independence assumption is needed.

    ``null_p`` tests mean(y)=0 in each experiment. ``wald_p`` tests the
    identifiable design coefficients at zero under that model. The caller must
    establish that the chosen fields test the SAME scientific null in every
    model. Taking a minimum, selecting models by the data or multiplying tails
    does not have this union-null validity.
    """
    if same_hypothesis is not True:
        raise ValueError("the common scientific null must be explicitly affirmed")
    if p_field not in ("null_p", "wald_p"):
        raise ValueError("p_field must be null_p or wald_p")
    fits = list(fits)
    if not fits:
        raise ValueError("need at least one nuisance model")
    values = np.asarray([fit[p_field] for fit in fits], dtype=float)
    if not np.isfinite(values).all() or np.any((values < 0) | (values > 1)):
        raise ValueError("model p-values must be finite and in [0,1]")
    return float(np.max(values))
