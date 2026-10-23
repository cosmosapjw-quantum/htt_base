"""R25 retained-cohort conditional composite-null diagnostic.

Reads only the R23/R24 frozen, small products. No old loader or fit is invoked.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import solve_triangular, lstsq
from scipy.special import logsumexp

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
R24 = BASE / "METHOD_EXECUTION_20261023/distance"
R23 = BASE / "CONTINUOUS_RESEARCH_20261023/execution/R23-DISTANCE"
INPUT = HERE.parent / "R25-DISTANCE-CONDITIONAL-EVIDENCE_INPUT.json"
SOURCES = {
    INPUT: "77439c5b5966f6f0c6a4d4e2819b28b76b7a3c24523e9b08ec9f7e12fd5ca2b8",
    R24 / "analyze.py": "5177f93c0c0e575b135c27dc3abe1fb3223fef421dae6bf571cbfb09fde4a63d",
    R24 / "RESULT.json": "330066f4a8605caa9874f192a938d4ef1d84cf8933bdd3e6059a40b011c28bd0",
    R24 / "OOF_ROWS.csv": "6fd8356e041e1ece186b79bf1506b04af5411e17e6c31a489a1f66da977a3c40",
    R24 / "DIRECTION_JOIN.csv": "4e6e9c991ecdf2fda2a403f68a4ea5d744e244c73478eef1c70efbf007852b9a",
    R24 / "CONTRACT.json": "150ce8734027c228af6daa042349f287d8de99dd71f60ffb79c26a7483f756fd",
    R24 / "ARTIFACT_MANIFEST.json": "1e1e0b6fabdc535bae1060b1ba3d1c61b2b1302001119c67d4a43f035dec521b",
    R23 / "RELEASED_ROWS.csv": "c7912bd7dd983cdcdf47408a89da9f2b76887a0cc37fd9b5a9a8e83e03d3fe20",
}
PACKET = "80be2c56bc7d24f05d364fb63ce7fea134178e25b6a9ee5aaf96378c95f2b9ad"
STF = np.array([
    np.diag([1, -1, 0]) / math.sqrt(2),
    np.diag([-1, -1, 2]) / math.sqrt(6),
    [[0, 1 / math.sqrt(2), 0], [1 / math.sqrt(2), 0, 0], [0, 0, 0]],
    [[0, 0, 1 / math.sqrt(2)], [0, 0, 0], [1 / math.sqrt(2), 0, 0]],
    [[0, 0, 0], [0, 0, 1 / math.sqrt(2)], [0, 1 / math.sqrt(2), 0]],
])
BASE_NAMES = ["intercept", "log10_vcmb", "measured_logWmxi", "e_logWmxi"]
ANG_NAMES = ["n_x", "n_y", "n_z"]
FLOW_NAMES = ["K_n_x", "K_n_y", "K_n_z"]
STF_NAMES = [f"STF_{j}" for j in range(1, 6)]
MODEL_NAMES = {
    "A_calibration_flow": BASE_NAMES + ANG_NAMES + FLOW_NAMES,
    "B_optical_STF": BASE_NAMES + ANG_NAMES + STF_NAMES,
    "C_union": BASE_NAMES + ANG_NAMES + FLOW_NAMES + STF_NAMES,
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_close(a, b, label, rtol=1e-9, atol=1e-8):
    np.testing.assert_allclose(a, b, rtol=rtol, atol=atol, err_msg=label)


def read_sources():
    for path, expected in SOURCES.items():
        if sha(path) != expected:
            raise ValueError(f"IMMUTABLE_SOURCE_MISMATCH {path}")
    rows = list(csv.DictReader((R23 / "RELEASED_ROWS.csv").open(newline="")))
    directions = list(csv.DictReader((R24 / "DIRECTION_JOIN.csv").open(newline="")))
    oof = list(csv.DictReader((R24 / "OOF_ROWS.csv").open(newline="")))
    saved = json.loads((R24 / "RESULT.json").read_text())
    ids = [int(r["pgc"]) for r in rows]
    by_id = {int(d["pgc"]): d for d in directions}
    if len(rows) != 274 or len(set(ids)) != 274 or len(directions) != 274 or set(ids) != set(by_id):
        raise ValueError("COHORT_JOIN_UNDEFINED")
    folds = np.array([int(by_id[i]["fold"]) for i in ids])
    if [int(np.sum(folds == f)) for f in range(5)] != [47, 55, 53, 69, 50]:
        raise ValueError("FROZEN_FOLD_MISMATCH")
    groups = [by_id[i]["group"] for i in ids]
    if any(len({folds[j] for j, g in enumerate(groups) if g == group}) != 1 for group in set(groups)):
        raise ValueError("GROUP_SPLIT")
    y = np.array([float(r["DMbest_mag"]) for r in rows])
    s = np.array([float(r["e_DMbest_mag"]) for r in rows])
    v = np.array([float(r["vcmb_km_s"]) for r in rows])
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(s)) and np.all(s > 0)
            and np.all(np.isfinite(v)) and np.all(v > 0)):
        raise ValueError("INVALID_RELEASED_VALUES")
    for j, i in enumerate(ids):
        d = by_id[i]
        check_close(float(d["Vcmb_km_s"]), v[j], "joined velocity", atol=0)
        if d["outcome"] != rows[j]["outcome"]:
            raise ValueError("JOIN_OUTCOME_MISMATCH")
    if float(rows[ids.index(9031)]["vcmb_km_s"]) != 317:
        raise ValueError("LOW_VELOCITY_ROW_MISSING")
    angles = np.radians([[float(by_id[i]["ra_J2000_deg"]), float(by_id[i]["dec_J2000_deg"])] for i in ids])
    n = np.column_stack((np.cos(angles[:, 1]) * np.cos(angles[:, 0]),
                         np.cos(angles[:, 1]) * np.sin(angles[:, 0]), np.sin(angles[:, 1])))
    check_close(np.sum(n*n, axis=1), np.ones(274), "unit vectors", atol=1e-12)
    check_close(np.einsum("aij,bij->ab", STF, STF), np.eye(5), "STF orthonormal", atol=1e-12)
    q = np.einsum("ni,aij,nj->na", n, STF, n)
    k = -5 / (math.log(10) * v)
    all_x = np.column_stack((np.ones(274), np.log10(v),
                             [float(r["logWmxi"]) for r in rows],
                             [float(r["e_logWmxi"]) for r in rows], n, k[:, None]*n, q))
    names = BASE_NAMES + ANG_NAMES + FLOW_NAMES + STF_NAMES
    features = {name: all_x[:, j] for j, name in enumerate(names)}
    if not np.all(np.isfinite(all_x)):
        raise ValueError("INVALID_DESIGN")
    oof_map = {(r["scenario"], r["model"], int(r["pgc"])): r for r in oof}
    if len(oof) != 274*4*3 or len(oof_map) != len(oof):
        raise ValueError("OOF_IDENTITY_MISMATCH")
    return rows, ids, groups, folds, y, s, features, oof_map, saved


def covariance(s, groups, a, b):
    if a < 0 or b < 0 or a > min(s):
        raise ValueError("INVALID_COVARIANCE_SCALE")
    V = np.diag(s*s-a*a) + a*a*np.ones((len(s), len(s)))
    V += b*b*np.equal.outer(groups, groups)
    np.linalg.cholesky(V)
    return V


def conditional(V, y, train, test):
    Vtt = V[np.ix_(train, train)]
    Vjt = V[np.ix_(test, train)]
    Lt = np.linalg.cholesky(Vtt)
    B = solve_triangular(Lt.T, solve_triangular(Lt, Vjt.T, lower=True), lower=False).T
    S = V[np.ix_(test, test)] - B @ Vjt.T
    check_close(S, S.T, "Schur symmetry", atol=1e-10)
    L = np.linalg.cholesky(S)
    r = y[test] - B @ y[train]
    return B, S, L, r


def density(y, pred, L, sigma2):
    if sigma2 <= 0 or not np.isfinite(sigma2):
        raise ValueError("INVALID_TRAINING_DENSITY")
    e = solve_triangular(L, y-pred, lower=True)
    terms = -.5*(math.log(2*math.pi*sigma2) + 2*np.log(np.diag(L)) + e*e/sigma2)
    return float(np.sum(terms)), terms


def null_supremum(r, Z, L, S):
    m = len(r)
    W = solve_triangular(L, Z, lower=True)
    t = solve_triangular(L, r, lower=True)
    scales = np.linalg.norm(W, axis=0)
    if np.any(scales <= 0) or not np.all(np.isfinite(scales)):
        raise ValueError("NULL_DESIGN_ZERO_COLUMN")
    Wn = W/scales
    U, sv, Vh = np.linalg.svd(Wn, full_matrices=False)
    ranks = [int(np.sum(sv > z*sv[0])) for z in (1e-8, 1e-10, 1e-12)]
    if len(set(ranks)) != 1:
        raise ValueError(f"NUMERICALLY_UNRESOLVED rank thresholds {ranks}")
    rank = ranks[1]
    coef = Vh[:rank].T @ ((U[:, :rank].T @ t)/sv[:rank])
    residual = t-Wn@coef
    R = float(residual @ residual)
    if R <= 1e-20*max(1.0, float(t@t)):
        return {"status": "CONSERVATIVE_ZERO_NUMERICALLY_UNRESOLVED", "rank": rank,
                "rank_sensitivity": ranks, "rss": R, "ellstar": math.inf}
    # Pivoted QR (gelsy) is independent of the SVD solution above.
    qrcoef, _, _, _ = lstsq(Wn, t, lapack_driver="gelsy")
    Rqr = float(np.sum((t-Wn@qrcoef)**2))
    check_close(Rqr, R, "QR versus SVD RSS", atol=1e-9)
    normal = float(np.linalg.norm(Wn.T@residual)/max(1, np.linalg.norm(Wn)*np.linalg.norm(t)))
    if normal >= 1e-10:
        raise ValueError(f"NULL_NORMAL_EQUATION_FAIL {normal}")
    sigma2 = R/m
    logdet = 2*float(np.log(np.diag(L)).sum())
    ell = -.5*(m*(math.log(2*math.pi)+1+math.log(sigma2))+logdet)
    pred_residual = r-Z@(coef/scales)
    direct, _ = density(r, r-pred_residual, L, sigma2)
    check_close(direct, ell, "direct Gaussian at null MLE", atol=1e-8)
    return {"status": "FINITE", "rank": rank, "rank_sensitivity": ranks,
            "rss": R, "sigma2_ML": sigma2, "ellstar": float(ell),
            "normal_equation_scaled": normal, "qr_rss": Rqr,
            "direct_logdensity": direct}


def fixture_controls():
    # Exact conditional law for correlated (T,J) Gaussian with fixed null.
    C = np.array([[1., .3], [.3, 1.5]])
    B = C[1, 0]/C[0, 0]
    S = C[1, 1]-B*C[0, 1]
    x, w = np.polynomial.hermite.hermgauss(80)
    z = np.sqrt(2*S)*x
    delta = .2
    ratio = np.exp((delta*z-.5*delta*delta)/S)
    expected = float(np.sum(w*ratio)/math.sqrt(math.pi))
    check_close(expected, 1, "conditional normalization", atol=1e-12)
    saturated = null_supremum(np.array([2.]), np.ones((1, 1)), np.array([[math.sqrt(S)]]), np.array([[S]]))
    if not (math.isinf(saturated["ellstar"]) and saturated["status"].startswith("CONSERVATIVE_ZERO")):
        raise ValueError("SATURATED_CONTROL_FAILED")
    return {"correlated_B": B, "conditional_variance": S,
            "quadrature_conditional_expectation": expected,
            "saturated_fold_E": 0, "saturated_status": saturated["status"]}


def run():
    rows, ids, groups, folds, y, s, features, oof, saved = read_sources()
    scenarios = list(saved["scenarios"])
    if len(scenarios) != 4:
        raise ValueError("SCENARIO_COUNT_MISMATCH")
    X = {m: np.column_stack([features[z] for z in names]) for m, names in MODEL_NAMES.items()}
    out = {"task_id": "R25-DISTANCE-CONDITIONAL-EVIDENCE", "packet_id": PACKET,
           "input_identity": "sha256:"+SOURCES[INPUT], "status": "EXECUTED_EXPLORATORY",
           "claim_tier": "exploratory conditional-evidence diagnostic",
           "cohort": {"released": len(rows), "selected": 628, "undefined": 354,
                      "fold_sizes": [int(np.sum(folds == j)) for j in range(5)],
                      "PGC9031_Vcmb_km_s": 317},
           "formula": {"numerator": "logsumexp(eight saved training-fixed conditional block log densities)-log(8)",
                       "denominator": "maximum of four conditional Gaussian null ML log densities per fold",
                       "aggregate": "logsumexp(five fold log E)-log(5)"},
           "components": [], "null_fits": [], "folds": [],
           "full_tensor_carrier": {}, "controls": {}}
    for scen in scenarios:
        sc = saved["scenarios"][scen]
        V = covariance(s, groups, sc["a_mag"], sc["b_mag"])
        out["full_tensor_carrier"][scen] = {}
        for model in ("B_optical_STF", "C_union"):
            item = sc["models"][model]
            if item["column_names_raw_units"] != MODEL_NAMES[model]:
                raise ValueError("SAVED_DESIGN_NAMES_MISMATCH")
            full = item["full_fit"]
            out["full_tensor_carrier"][scen][model] = {
                "source": str(R24/"RESULT.json"), "source_sha256": SOURCES[R24/"RESULT.json"],
                "column_names_raw_units": item["column_names_raw_units"],
                "coefficient_raw_units": full["coefficient_raw_units"],
                "coefficient_covariance_raw_units": full["coefficient_covariance_raw_units"],
                "angular_tensor_state": full.get("angular_tensor_state")}
        for fold in range(5):
            tr = np.flatnonzero(folds != fold)
            te = np.flatnonzero(folds == fold)
            B, S, L, r = conditional(V, y, tr, te)
            for model in ("B_optical_STF", "C_union"):
                fit = sc["models"][model]["folds"][fold]
                if fit["fold"] != fold or fit["n_train"] != len(tr) or fit["n_test"] != len(te):
                    raise ValueError("SAVED_FOLD_IDENTITY_MISMATCH")
                beta = np.asarray(fit["coefficient_raw_units"])
                if beta.shape != (X[model].shape[1],):
                    raise ValueError("MISSING_SAVED_COEFFICIENT")
                pred = X[model][te]@beta + B@(y[tr]-X[model][tr]@beta)
                logd, terms = density(y[te], pred, L, fit["sigma2_ML_train"])
                check_close(logd, fit["joint_log_predictive_score"], "retained joint score")
                ref = [oof[(scen, model, ids[k])] for k in te]
                check_close(pred, [float(z["OOF_predicted_DMbest_mag"]) for z in ref], "retained OOF mean")
                check_close(terms, [float(z["OOF_ordered_conditional_log_score"]) for z in ref],
                            "retained OOF ordered log density")
                out["components"].append({"scenario": scen, "model": model, "fold": fold,
                                          "n": len(te), "log_density": logd,
                                          "mean_by_pgc": {str(ids[k]): float(pred[j]) for j, k in enumerate(te)}})
            Z = X["A_calibration_flow"][te]-B@X["A_calibration_flow"][tr]
            nf = null_supremum(r, Z, L, S)
            fitA = sc["models"]["A_calibration_flow"]["folds"][fold]
            if nf["ellstar"]+1e-8 < fitA["joint_log_predictive_score"]:
                raise ValueError("NULL_SUPREMUM_BELOW_SAVED_TRAINING_A")
            out["null_fits"].append({"scenario": scen, "fold": fold, "n": len(te),
                                     "training_A_logdensity_control": fitA["joint_log_predictive_score"], **nf})
    if len(out["components"]) != 40 or len(out["null_fits"]) != 20:
        raise ValueError("FIT_COUNT_MISMATCH")
    for fold in range(5):
        logs = [z["log_density"] for z in out["components"] if z["fold"] == fold]
        den = [z["ellstar"] for z in out["null_fits"] if z["fold"] == fold]
        logq = float(logsumexp(logs)-math.log(8))
        logE = float(logq-max(den))
        if np.all(np.isfinite(logs)):
            check_close(math.exp(logq-max(logs)), sum(math.exp(x-max(logs)) for x in logs)/8,
                        "ordinary/log arithmetic mixture")
        out["folds"].append({"fold": fold, "n": int(np.sum(folds == fold)), "logq": logq,
                             "max_null_logdensity": max(den), "logE": logE,
                             "E": float(math.exp(logE)) if logE > -745 else 0.0})
    out["logE_arithmetic_fold_average"] = float(logsumexp([z["logE"] for z in out["folds"]])-math.log(5))
    out["E_arithmetic_fold_average"] = float(math.exp(out["logE_arithmetic_fold_average"]))
    check_close(out["E_arithmetic_fold_average"], sum(z["E"] for z in out["folds"])/5,
                "ordinary/log arithmetic fold mean")
    out["controls"]["fixture"] = fixture_controls()
    out["controls"]["saved_40_component_means_and_scores"] = "PASS"
    out["controls"]["saved_20_training_A_lower_bound"] = "PASS"
    out["controls"]["independent_QR_vs_SVD_20_RSS"] = "PASS"
    out["controls"]["direct_Gaussian_vs_analytic_20"] = "PASS"
    out["controls"]["null_scaled_normal_equations_20"] = "PASS"
    # Reorder both train and test in one nontrivial correlated scenario.
    sc = saved["scenarios"]["a_0.055_b_0.290"]
    V = covariance(s, groups, sc["a_mag"], sc["b_mag"])
    tr = np.flatnonzero(folds != 0); te = np.flatnonzero(folds == 0)
    B, S, L, _ = conditional(V, y, tr, te)
    fit = sc["models"]["C_union"]["folds"][0]
    beta = np.asarray(fit["coefficient_raw_units"])
    pred = X["C_union"][te]@beta+B@(y[tr]-X["C_union"][tr]@beta)
    reference, _ = density(y[te], pred, L, fit["sigma2_ML_train"])
    tp = tr[::-1]; jp = te[::-1]
    Bp, Sp, Lp, _ = conditional(V, y, tp, jp)
    predp = X["C_union"][jp]@beta+Bp@(y[tp]-X["C_union"][tp]@beta)
    permuted, _ = density(y[jp], predp, Lp, fit["sigma2_ML_train"])
    check_close(permuted, reference, "row permutation block density", atol=1e-8)
    out["controls"]["train_test_permutation"] = {"original": reference, "permuted": permuted}
    (HERE/"RESULT.json").write_text(json.dumps(out, indent=2, allow_nan=False)+"\n")
    fig, ax = plt.subplots(figsize=(7, 3.7))
    xx = np.arange(5)
    ax.bar(xx, [z["logE"] for z in out["folds"]], color="#3776a8")
    ax.axhline(0, color="black", linewidth=.8)
    ax.set_xticks(xx, [str(i) for i in xx]); ax.set_xlabel("Held-out group fold")
    ax.set_ylabel("log conditional E")
    ax.set_title("Selected-cohort conditional composite-null diagnostic")
    fig.text(.01, .01, "Exploratory; unqualified selection law and numerical bound", fontsize=8)
    fig.tight_layout(rect=(0,.05,1,1)); fig.savefig(HERE/"figure.png", dpi=140); plt.close(fig)
    return out


if __name__ == "__main__":
    result = run()
    print(json.dumps({"status": result["status"], "logEbar": result["logE_arithmetic_fold_average"],
                      "components": len(result["components"]), "null_fits": len(result["null_fits"])}, indent=2))
