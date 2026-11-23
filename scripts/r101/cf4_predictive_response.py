"""R101 apparent CF4 covariance-path and optional observed 6dFGSv mark experiment."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from htt.infer.cf4_predictive_response import (
    predictive_contrasts, predictive_covariance_response, selected_probit_field_response,
)

ROOT = Path(__file__).resolve().parents[2]
R100 = (ROOT / "docs/research_program/observational_publication_20261015"
        / "R100_SOURCE_LAW_OPTICAL_MULTIPROBE_20261123")


def matrix_response(directory):
    path = directory / "CF4_FULL_KBAND_COVARIANCES.npz"
    with np.load(path, allow_pickle=False) as f:
        y = f["b_published_4x9"].reshape(36)
        c0, c1 = f["C_WF_R5_inherited"], f["C_WF_R5_full_k"]
    dc = c1 - c0
    x = np.tile(np.eye(9), (2, 1))
    contrast = predictive_contrasts(x, x)

    def evaluate(alpha):
        return predictive_covariance_response(y, c0 + alpha * dc, dc, contrast)

    rows = []
    fd_chi, fd_log = [], []
    for alpha in np.linspace(0, 1, 5):
        a = evaluate(alpha)
        rows.append(dict(alpha=float(alpha), **{k: v for k, v in a.items() if np.isscalar(v)}))
        step = 1.e-5
        plus, minus = evaluate(alpha + step), evaluate(alpha - step)
        for key, residuals in (("chi2", fd_chi), ("log_density", fd_log)):
            fd = (plus[key] - minus[key]) / (2 * step)
            residuals.append(abs(fd - a[key + "_tangent"]))
    # Integrate the analytic score along the measured matrix interpolation.
    nodes, weights = np.polynomial.legendre.leggauss(12)
    integral = np.zeros(2)
    for node, wt in zip(nodes, weights):
        out = evaluate((node+1)/2)
        integral += 0.5*wt*np.asarray([out["chi2_tangent"], out["log_density_tangent"]])
    delta = np.asarray([rows[-1][k] - rows[0][k] for k in ("chi2", "log_density")])
    return dict(input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                train_dimensions=18, test_dimensions=18, shared_mean_dimension=9,
                alpha_rows=rows, max_abs_fd_error_chi2=max(fd_chi),
                max_abs_fd_error_log_density=max(fd_log),
                endpoint_change=delta.tolist(), integrated_derivative=integral.tolist(),
                endpoint_integral_abs_errors=np.abs(delta-integral).tolist())


def source_marks(reference):
    """Replay R100's exact matched cohort; switch only the selection function."""
    from scripts.r100 import cf4_upstream_and_kband as r100

    t2 = r100.load_cf4_table2()
    six = r100.load_sixdf_pv()
    # Bind the rows to the same artifacts as the fitted inclusion coefficients.
    for name, path in (("cf4_table2", t2["path"]), ("sixdf_pv_table1", r100.SIXDF_PATH)):
        if r100.sha256(path) != reference["inputs"][name]["sha256"]:
            raise ValueError(f"source mark cohort identity mismatch for {name}")
    radius = 2*np.sin(np.deg2rad(15./3600)/2)
    tree = cKDTree(r100._sph_vec(t2["ra"], t2["dec"]))
    cand = tree.query_ball_point(r100._sph_vec(six["ra"], six["dec"]), radius)
    match = np.array([sum(abs(t2["vcmb"][j]-cz) <= 500 for j in jj) == 1
                      for jj, cz in zip(cand, six["cz_gal"])])
    n = int(match.sum())
    expected = reference["A2_upstream_genealogy_and_sign_audit"]["sixdf_pv_census"]
    if n != expected["unique_match_15arcsec_500kms"]:
        raise ValueError("R100 match count changed")
    fit = reference["A4_selection_likelihood_and_4term_cov"]["empirical_probit_inclusion_6df"]
    b0, bz, beta, bg = fit["beta_probit"]
    cz, y, sigma = (six[k][match] for k in ("cz_gal", "delta_d", "epsilon_d"))
    a = b0 + bz*(cz/1e4-1.1) + bg*six["is_grouped"][match]
    audited = fit["joint_selected_logpdf_5field_mix"]
    fields = np.asarray(audited["fields_kms"])
    probs = np.full(len(fields), 1.0/len(fields))
    sci, *_ = r100.old._load_r30_and_bridge()
    z = cz / r100.C
    # Fixed model means, reported per dex of the native eta. mu=mu0-5*eta.
    means = np.stack([r100.r99.finite_shift(sci, z, np.arctanh(v/r100.C), "bolometric")
                      / (5*r100.MAG) for v in fields])
    zero = np.zeros((1, n))
    rows = {}
    # Historic Phi((mu0+.55-mu)/.30) becomes Phi(.55/.30+5*eta/.30).
    for label, intercept, slope in (("historic_fixed_cut", .55/.30, 5/.30),
                                    ("fitted_match_probit", a, beta)):
        joint = selected_probit_field_response(y, means, sigma, intercept, slope, probs,
                                               mean_tangent=means)
        single = selected_probit_field_response(y, zero, sigma, intercept, slope, [1.])
        rows[label] = dict(dex_logpdf=joint["log_density"],
                           mag_logpdf=joint["log_density"]-n*np.log(5),
                           zero_field_mag_logpdf=single["log_density"]-n*np.log(5),
                           log_density_mix_minus_zero=joint["log_density"]-single["log_density"],
                           log_joint_inclusion=joint["log_joint_inclusion"],
                           field_mark_posterior_weights=joint["observed_field_weights"].tolist(),
                           field_inclusion_weights=joint["included_field_weights"].tolist(),
                           fixed_mean_template_amplitude_score=joint["log_density_tangent"])
    # Keep the observed nonmatches in the factorization. Their native marks
    # are available upstream but are integrated out in this conditional experiment.
    z_parent = six["cz_gal"] / r100.C
    parent_means = np.stack([r100.r99.finite_shift(sci, z_parent, np.arctanh(v/r100.C),
                                                   "bolometric") / (5*r100.MAG) for v in fields])
    parent_a = b0 + bz*(six["cz_gal"]/1e4-1.1) + bg*six["is_grouped"]
    input_mark = np.where(match, six["delta_d"], np.nan)

    def pattern(amplitude, gradient=False):
        return selected_probit_field_response(input_mark, amplitude*parent_means, six["epsilon_d"],
                                              parent_a, beta, probs, included=match,
                                              mean_tangent=parent_means if gradient else None)

    full = pattern(1., gradient=True)
    zero_parent = pattern(0.)
    step = 1e-5
    fd = (pattern(1.+step)["log_density"]-pattern(1.-step)["log_density"])/(2*step)
    pattern_output = dict(rejected_status_count=int((~match).sum()),
                          mag_logpdf=full["log_density"]-n*np.log(5),
                          zero_field_mag_logpdf=zero_parent["log_density"]-n*np.log(5),
                          log_density_mix_minus_zero=full["log_density"]-zero_parent["log_density"],
                          log_inclusion_pattern=full["log_inclusion_pattern"],
                          field_inclusion_pattern_weights=full["included_field_weights"].tolist(),
                          field_mark_posterior_weights=full["observed_field_weights"].tolist(),
                          fixed_mean_template_amplitude_score=full["log_density_tangent"],
                          amplitude_score_fd_abs_error=abs(fd-full["log_density_tangent"]))
    historic = rows["historic_fixed_cut"]
    replay_error = max(abs(historic[key] - audited[prior])
                       for key, prior in (("mag_logpdf", "log_density"),
                                          ("log_joint_inclusion", "log_joint_inclusion"),
                                          ("zero_field_mag_logpdf", "zero_field_log_density")))
    if replay_error > 1e-6:
        raise ArithmeticError(f"R100 same-row fixed-cut replay failed: {replay_error:.3g}")
    return dict(parent_rows=int(six["n"]), matched_rows=n, fields_kms=fields.tolist(),
                selection_index_slope_per_mag_fixed=-1/.30,
                selection_index_slope_per_mag_fitted=-beta/5,
                plug_in_beta=fit["beta_probit"], source_sha256={
                    k: reference["inputs"][k]["sha256"] for k in ("cf4_table2", "sixdf_pv_table1")},
                historic_fixed_cut_replay_max_abs_error=float(replay_error), models=rows,
                fitted_with_all_parent_match_indicators=pattern_output,
                scope="Same already released 6dFGSv targets; plug-in probability of unique match "
                      "to CF4 table 2. Gaussian native eta width, correlated finite field, fixed "
                      "empirical coefficients. Same-cohort sensitivity; no independent calibration.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r100-dir", type=Path, default=R100)
    parser.add_argument("--source-marks", action="store_true")
    parser.add_argument("--output", type=Path)
    arg = parser.parse_args()
    reference = json.loads((arg.r100_dir / "CF4_UPSTREAM_KBAND_RESULTS.json").read_text())
    matrix = matrix_response(arg.r100_dir)
    orig = reference["A3_full_kband_correlated_pv"]["models"]["WF_log_R5"]
    endpoint_err = max(abs(matrix["alpha_rows"][idx][key] - orig[name][legacy])
                       for idx, name in ((0, "schur_18dof_inherited"), (-1, "schur_18dof_full_k"))
                       for key, legacy in (("chi2", "chi2"), ("log_density", "loglik")))
    if endpoint_err > 1e-8:
        raise ArithmeticError(f"R100 conditional endpoint reconstruction failed: {endpoint_err}")
    matrix["r100_replay_max_abs_error"] = endpoint_err
    out = dict(schema="htt.r101.cf4_predictive_response/1",
               scope="Conditional R100 apparent tomography and release-match sensitivity",
               source_qualification="BLOCKED_INPUT", physical_Pi=None, physical_GF=None,
               covariance_path=matrix, source_marks=source_marks(reference) if arg.source_marks else None)
    text = json.dumps(out, indent=2, allow_nan=False) + "\n"
    if arg.output is not None:
        arg.output.parent.mkdir(parents=True, exist_ok=True)
        arg.output.write_text(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
