#!/usr/bin/env python3
"""R59-B/C/D: build the benchmark record, the claim table, the bounded manuscript and LOCAL_RESULT.json from stored outputs.

Every number in the written files is read from RESULTS/NATIVE_REPLAY (native replay of R58), RESULTS/NATIVE_REPLAY/REFERENCE_PARITY.json,
the committed R58 receipts and the source constants of the frozen pipeline; nothing is typed. Computed here from stored quantities only
(no new data, no new fit): the same-input score checks of comparator B02 and the exact (Imhof) coverage of the block-factorized ellipsoid
from its stored actual/nominal variance eigenvalues. The final decision is read from R59_DECISION.json (written after the independent
review); without it the decision is PENDING_REVIEW.

    python scripts/r58/build_r59_outputs.py --root .
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from scipy import integrate, stats

PKG = "docs/research_program/observational_publication_20261015/R58_MIXED_TENSOR_CONVERGENCE_20261117"
MODELS = ("log", "log_mono", "log_mono_error", "log_mono_galactic", "log_mono_radial", "log_split", "log_survey")
LOG_DIR = Path("/mnt/extdrive/workdir/r59_logs")
REPLAY = f"{PKG}/RESULTS/NATIVE_REPLAY"
#: commands of R59-A exactly as executed (LOCAL_AGENT_CONTRACT.json:commands plus the parity comparison); exit codes in LOG_DIR/exit_codes.txt
COMMANDS = {
    "pytest_r58": "PYTHONPATH=htt/src:htt:. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/r58 -q",
    "runner": f"OPENBLAS_NUM_THREADS=1 python scripts/r58/run_r58_owned_tensor.py --root . --output {REPLAY}",
    "views": f"OPENBLAS_NUM_THREADS=1 python scripts/r58/build_r58_views.py --root . --results {REPLAY}",
    "checker": f"OPENBLAS_NUM_THREADS=1 python scripts/r58/check_r58_independent.py --root . --results {REPLAY} --output {REPLAY}/INDEPENDENT_CHECK.json",
    "dag": "python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --status docs/codex_handoff/pr_status.yaml",
    "mirror": "python scripts/codex_harness/sync_pr_dag_mirrors.py --check",
    "parity": "python scripts/r58/compare_r59_native_replay.py --root .",
}
#: same-topic CF4 literature checked on 2026-11-17 (abstract pages read); used only to classify comparability and novelty
LITERATURE = {
    "Tully2023": "Tully R. B. et al. 2023, ApJ 944, 94 (Cosmicflows-4).",
    "Heinesen2021": "Heinesen A. 2021, arXiv:2010.06534 (multipole decomposition of the luminosity-distance Hubble law).",
    "Maartens2024": "Maartens R., Santiago J., Clarkson C., Kalbouneh B., Marinoni C. 2024, arXiv:2312.09875 (covariant cosmography: observer dependence of H).",
    "Boubel2025": "Boubel P., Colless M., Said K., Staveley-Smith L. 2025, JCAP 03, 066, arXiv:2412.14607 (testing anisotropic Hubble expansion with CF4 Tully-Fisher distances).",
    "Stiskalek2025": "Stiskalek R., Desmond H., Lavaux G. 2025, arXiv:2509.14997 (no evidence for local H0 anisotropy from Tully-Fisher or supernova distances).",
    "Kalbouneh2025": "Kalbouneh B., Marinoni C., Maartens R. et al. 2025, arXiv:2510.02510, accepted by JCAP (anisotropic expansion rate of the local Universe, CF4 and Pantheon+).",
    "Salzano2025": "Salzano V., Beltran Jimenez J., Bettoni D., Brax P., Valade A. 2025, arXiv:2512.02526 (dipolar anisotropy of local H0 from CF4).",
    "Vicente2026": "Vicente J. G., Pereira T. S., Rodrigues R. G., Vitenti S. D. P., Gomes V. M. 2026, arXiv:2607.07821 (multipolar structure of the local expansion rate from incomplete sky data).",
    "Cowell2022": "Cowell J. A., Dhawan S., Macpherson H. J. 2022, arXiv:2212.13569 (quadrupolar Hubble expansion in Pantheon+).",
    "Alsing2018": "Alsing J., Wandelt B. 2018, arXiv:1712.00012 (generalized massive optimal data compression).",
    "Saadeh2016": "Saadeh D., Feeney S. M., Pontzen A., Peiris H. V., McEwen J. D. 2016, arXiv:1605.07178 (how isotropic is the Universe?).",
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def g(x: float, n: int = 3) -> str:
    return f"{x:.{n}g}"


def f4(x: float) -> str:
    return f"{x:.4f}"


def source_constant(root: Path, rel: str, name: str):
    """A module-level constant read from source without importing the module (the frozen pipeline checks pins at import)."""
    for node in ast.parse((root / rel).read_text()).body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return ast.literal_eval(node.value)
                if isinstance(t, ast.Tuple) and name in [e.id for e in t.elts if isinstance(e, ast.Name)]:
                    return ast.literal_eval(node.value)[[e.id for e in t.elts].index(name)]
    raise SystemExit(f"{name} not found in {rel}")


def imhof_cdf(lams: np.ndarray, x: float) -> float:
    """P(sum_j lam_j Z_j^2 <= x) for independent standard normals (Imhof 1961)."""
    lams = np.asarray(lams, float)

    def integrand(u: float) -> float:
        theta = 0.5 * np.sum(np.arctan(lams * u)) - 0.5 * x * u
        rho = np.prod((1.0 + (lams * u) ** 2) ** 0.25)
        return np.sin(theta) / (u * rho)

    val, _ = integrate.quad(integrand, 0.0, np.inf, limit=500)
    return float(0.5 - val / np.pi)


def load(root: Path) -> dict:
    pkg = root / PKG
    rep = pkg / "RESULTS" / "NATIVE_REPLAY"
    d = {"pkg": pkg, "rep": rep, "root": root,
         "owned": json.loads((rep / "OWNED_TENSOR_RESULT.json").read_text()),
         "owned_ref": json.loads((pkg / "RESULTS" / "OWNED_TENSOR_RESULT.json").read_text()),
         "views": json.loads((rep / "FIVE_VIEW_RESULT.json").read_text()),
         "indep": json.loads((rep / "INDEPENDENT_CHECK.json").read_text()),
         "parity": json.loads((rep / "REFERENCE_PARITY.json").read_text()),
         "dag": json.loads((pkg / "RESEARCH_DAG.json").read_text()),
         "bench_contract": json.loads((pkg / "BENCHMARK_CONTRACT.json").read_text()),
         "carriers": np.load(rep / "OWNED_TENSOR_CARRIERS.npz", allow_pickle=False),
         "windows": source_constant(root, "scripts/r54/run_r54_cf4_exact.py", "CENTERS"),
         "window_width": source_constant(root, "scripts/r54/run_r54_cf4_exact.py", "WIDTH"),
         "sigma_star": source_constant(root, "scripts/r54/run_r54_cf4_exact.py", "SIGMA_STAR")}
    dec = pkg / "R59_DECISION.json"
    d["decision"] = json.loads(dec.read_text()) if dec.is_file() else None
    env = LOG_DIR / "env.txt"
    d["env_native"] = env.read_text().strip().splitlines() if env.is_file() else []
    ex = LOG_DIR / "exit_codes.txt"
    d["exit_lines"] = ex.read_text().splitlines() if ex.is_file() else []
    return d


def same_input_score_checks(z) -> dict:
    """B02 from the stored 32-row carriers. (i) estimate and covariance re-solved from t = X^T C^-1 y and J = X^T C^-1 X against the stored
    values; (ii) a central finite-difference gradient of the full log-likelihood at alpha = 0 against t (the Gaussian linear-mean score);
    (iii) the arithmetic identity full(a) - [q0 - 2 t.a + a.J a] = 0 (a floating-point check, not independent evidence)."""
    out = {}
    rng = np.random.default_rng(20261117)
    for m in MODELS:
        y, c, x = z[f"{m}__y32"], z[f"{m}__cov32"], z[f"{m}__response32x11"]
        ci = np.linalg.inv(c)
        j, t = x.T @ ci @ x, x.T @ ci @ y
        q0 = float(y @ ci @ y)
        est = np.linalg.solve(j, t)
        sd = np.sqrt(np.diag(np.linalg.inv(j)))

        def full(a):
            r = y - x @ a
            return float(r @ ci @ r)

        h = 1e-3 * sd
        fd = np.array([-(full(h[k] * np.eye(11)[k]) - full(-h[k] * np.eye(11)[k])) / (4.0 * h[k]) for k in range(11)])
        ident = 0.0
        for _ in range(20):
            a = est + rng.standard_normal(11) * sd
            fa = full(a)
            ident = max(ident, abs(fa - (q0 - 2.0 * t @ a + a @ j @ a)) / max(1.0, abs(fa)))
        ref = z[f"{m}__estimate11"]
        out[m] = {"estimate_rel_error_vs_stored": float(np.max(np.abs(est - ref) / np.maximum(np.abs(ref), 1e-300))),
                  "covariance_rel_error_vs_stored": float(np.max(np.abs(np.linalg.inv(j) - z[f"{m}__cov11"])) / np.max(np.abs(z[f"{m}__cov11"]))),
                  "finite_difference_score_rel_error": float(np.max(np.abs(fd - t) * sd) / np.max(np.abs(t) * sd)),
                  "quadratic_identity_arithmetic_rel": ident,
                  "fisher_rank": int(np.linalg.matrix_rank(j))}
    return out


def collect(d: dict) -> dict:
    o, v, ind = d["owned"], d["views"], d["indep"]
    c95 = float(stats.chi2.ppf(0.95, 11))
    n = {"models": {}, "c95": c95}
    for m in MODELS:
        var = o["variants"][m]
        fit, bd = var["fit"], var["block_diagonal_uncertainty_calibration"]
        ic = ind["checks"][m]
        ev = bd["actual_to_nominal_variance_eigenvalues"]
        pp = v["models"][m]["x"]["physical_pullback"]
        n["models"][m] = {"rank": fit["rank"], "wald_p": fit["wald_p"], "null_p": fit["null_p"], "adequacy_p": fit["adequacy_p"],
                          "cc_max": var["canonical_correlations"][0], "var_ratio_min": min(ev), "var_ratio_max": max(ev),
                          "cov_block_exact": imhof_cdf(np.array(ev), c95),
                          "cov_block_20k": bd["coverage_of_nominal_95_ellipsoid_under_full_covariance"], "cov_full_20k": bd["full_GLS_reference_coverage_same_draws"],
                          "cov_block_60k": ic["independent_sampling_coverage_block_nominal95"], "cov_full_60k": ic["independent_sampling_coverage_full_nominal95"],
                          "mc_se_60k": ic["mc_se"],
                          "physical_rank": pp["rank"], "physical_dim": pp["dimension"],
                          "identified_physical": sorted(k for k, iv in pp["intervals_95_simultaneous"].items() if iv["identified"]),
                          "path_logL_error": v["models"][m]["G_F"]["likelihood_error"],
                          "occupancy": v["models"][m]["F"]["occupancy"]["status"]}
    rb = o["robust"]
    n["robust"] = {"max_wald_p": rb["max_wald_p_common_theta_zero"], "max_null_p": rb["max_null_p"], "hull": rb["coordinate_support_hull"]}
    n["hull_contains_zero"] = {k: (b["lower"] < 0 < b["upper"]) for k, b in rb["coordinate_support_hull"].items()}
    n["directions"] = {k: dd["simultaneous_95_union_interval_hull"] for k, dd in v["directional_observable"]["directions"].items()}
    n["beta_hull"] = {}
    for k in ("beta_MR_0", "beta_MR_1", "beta_MR_2"):
        ivs = [v["models"][m]["x"]["physical_pullback"]["intervals_95_simultaneous"][k] for m in MODELS]
        n["beta_hull"][k] = {"lower": min(i["lower"] for i in ivs), "upper": max(i["upper"] for i in ivs)}
    n["marginal_err"] = d["parity"]["frozen_marginal_max_abs_error"]
    n["n_groups"], n["n_models"] = o["n_groups"], o["n_models"]
    for key in ("cc_max", "var_ratio_min", "var_ratio_max", "cov_block_exact", "cov_block_20k", "cov_full_20k", "cov_block_60k", "cov_full_60k", "adequacy_p", "path_logL_error"):
        vals = [n["models"][m][key] for m in MODELS]
        n[f"range_{key}"] = (min(vals), max(vals))
    n["exact_vs_60k_max_abs"] = max(abs(n["models"][m]["cov_block_exact"] - n["models"][m]["cov_block_60k"]) for m in MODELS)
    n["score"] = same_input_score_checks(d["carriers"])
    n["gls_oracle"] = d["bench_contract"]["result_snapshot"]["independent_gls_oracle"]
    return n


def benchmark_rows(d: dict, n: dict) -> list[dict]:
    fs = d["parity"]["files_sha256"]
    inp = {"owned_result": fs.get(f"{REPLAY}/OWNED_TENSOR_RESULT.json"), "carriers": fs.get(f"{REPLAY}/OWNED_TENSOR_CARRIERS.npz")}
    sc = n["score"]
    se60 = max(n["models"][m]["mc_se_60k"] for m in MODELS)
    lit = lambda cid, key, est, why: dict(comparator_id=cid, common_estimand=est, outcome="NOT_COMPARABLE", same_data="partial",
                                          actual_execution=f"classified from the abstract only ({LITERATURE[key]})", metrics={}, limitations=why, seed_and_sample_count="n/a")
    rows = [
        dict(comparator_id="B01_DIRECT_GLS", common_estimand="11 apparent coefficients on the same 32 rows, covariance and response", outcome="TIE", same_data="yes",
             actual_execution="reused: 24 independent GLS/logL oracles (R58 review); replayed: independent checker on the native output",
             metrics={"oracle_max_estimate_abs_error": n["gls_oracle"]["max_estimate_abs_error"], "oracle_max_logL_abs_error": n["gls_oracle"]["max_logL_abs_error"],
                      "native_checker_status": d["indep"]["status"]},
             limitations="identical statistic by construction; a tie is not a win", seed_and_sample_count="n/a (deterministic)"),
        dict(comparator_id="B02_SCORE", common_estimand="same retained 32-row fixed-covariance linear-mean experiment", outcome="TIE", same_data="yes",
             actual_execution="computed from the stored carriers: re-solved estimate/covariance, finite-difference score of the full log-likelihood, quadratic identity",
             metrics={"max_estimate_rel_error_vs_stored": max(s["estimate_rel_error_vs_stored"] for s in sc.values()),
                      "max_finite_difference_score_rel_error": max(s["finite_difference_score_rel_error"] for s in sc.values()),
                      "max_quadratic_identity_arithmetic_rel": max(s["quadratic_identity_arithmetic_rel"] for s in sc.values()),
                      "fisher_rank_all_models": sorted({s["fisher_rank"] for s in sc.values()})},
             limitations="the quadratic identity is an arithmetic check, not independent evidence; the covariance does not depend on the fitted parameters, so no "
                         "covariance-derivative score term exists; exact sufficiency (Alsing & Wandelt 2018) only inside the fixed-C Gaussian law",
             seed_and_sample_count="20 parameter points per model, seed 20261117"),
        dict(comparator_id="B03_CROSS_BLOCK_ABLATION", common_estimand="same 11 coefficients; only the polar-STF cross covariance removed", outcome="BETTER_CALIBRATED_THAN_ABLATION",
             same_data="yes",
             actual_execution="exact weighted-chi-square (Imhof) coverage from the stored variance eigenvalues; reused: Gaussian 20000 draws (seed 20261117) and independent "
                              "Gaussian 60000 draws (seed 9345081), replayed natively",
             metrics={"variance_ratio_eigenvalues_range": [n["range_var_ratio_min"][0], n["range_var_ratio_max"][1]],
                      "block_nominal95_coverage_exact_range": list(n["range_cov_block_exact"]),
                      "block_nominal95_coverage_60k_range": list(n["range_cov_block_60k"]), "full_GLS_coverage_60k_range": list(n["range_cov_full_60k"]),
                      "max_mc_se_60k": se60, "max_abs_exact_minus_60k": n["exact_vs_60k_max_abs"]},
             limitations="synthetic ablation, not attributed to any published analysis; it models an error budget that treats the dipole and quadrupole blocks as "
                         "independent; full-GLS coverage is nominal by construction under the assumed law; not survey coverage, not validation of the cosmic covariance",
             seed_and_sample_count="exact; 20000 (seed 20261117) and 60000 (seed 9345081) per model as numerical checks"),
        dict(comparator_id="B03S_SURVEY_MOCK_REPLAY", common_estimand="same pipeline replayed on release-matched end-to-end CF4 survey mocks", outcome="BLOCKED_EXISTING_INPUT",
             same_data="no",
             actual_execution="not executed: no release-matched end-to-end CF4 survey mock exists locally (htt/obsstat/pv_forward_mocks.py records the CF4TF L-PICOLA mocks "
                              "of Qin et al. 2021 as request-only; its in-house Gaussian-field generator is a velocity forward model, not a catalogue mock with selection and "
                              "zero-point calibration, and its MV interpretation is quarantined)",
             metrics={}, limitations="empirical survey-level coverage of the full and block intervals stays UNRESOLVED", seed_and_sample_count="none"),
        dict(comparator_id="B04_SCALAR_ABLATION", common_estimand="scalar norm vs signed vector/STF target", outcome="NOT_COMPARABLE", same_data="yes",
             actual_execution="reused: tests/r58/test_mixed_tensor_likelihood.py::test_scalar_norm_loses_signed_target_likelihood",
             metrics={}, limitations="target mismatch: a norm cannot identify signed contrasts without a direction assumption; no power claim", seed_and_sample_count="n/a"),
        dict(comparator_id="B05_MORPHOLOGY_BIPOSH", common_estimand="none: CF4 apparent Hubble coefficients vs CMB a_lm irreps", outcome="NOT_COMPARABLE", same_data="no",
             actual_execution="classified only", metrics={}, limitations="different data, estimand and law; no common transfer response", seed_and_sample_count="n/a"),
        dict(comparator_id="B06_KINEMATIC_COSMOGRAPHY", common_estimand="same apparent low-z coefficients on the selected CF4 rows", outcome="TIE", same_data="yes",
             actual_execution="same linear model reduces to direct GLS; physical pullback recomputed natively",
             metrics={"physical_rank": sorted({n["models"][m]["physical_rank"] for m in MODELS}), "physical_dimension": sorted({n["models"][m]["physical_dim"] for m in MODELS}),
                      "identified_physical_coordinates": n["models"]["log"]["identified_physical"]},
             limitations="sigma/H, omega/H and A/(cH) individually unbounded with free calibration; beta conditional on the constant-velocity response", seed_and_sample_count="n/a"),
        lit("B06A_BOUBEL_2025", "Boubel2025", "CF4 Tully-Fisher H0 dipole vs constant H0 plus LCDM bulk flow",
            "TF subsample with differential zero points and a dipole-only model; different estimator, sample and law"),
        lit("B06B_SALZANO_2025", "Salzano2025", "CF4 log-H0 sky maps fitted with spherical harmonics to l = 3",
            "conservative distance-modulus/redshift subsample and map-based harmonic fit; different estimator and law"),
        lit("B06C_VICENTE_2026", "Vicente2026", "CF4 expansion-rate multipoles l = 1-3 in harmonics and STF tensors with mask-coupling inversion",
            "z = 0.01-0.05 in the CMB frame, pixel mask, pseudo-inverse and maximum-likelihood reconstruction; STF basis and joint mask-coupled multipoles predate this work"),
        lit("B06X_KALBOUNEH_2025", "Kalbouneh2025", "CF4+Pantheon+ expansion-rate fluctuation multipoles",
            "different sample combination, estimator and redshift binning"),
        dict(comparator_id="B07_BOOST_INTRINSIC_DIPOLE", common_estimand="none: CMB observer boost vs CF4 coherent V", outcome="NOT_COMPARABLE", same_data="no",
             actual_execution="classified only", metrics={}, limitations="no global-tilt transfer; V is not a measured global tilt", seed_and_sample_count="n/a"),
        dict(comparator_id="B08_BIANCHI", common_estimand="none: class-specific transfer parameters", outcome="NOT_COMPARABLE", same_data="no",
             actual_execution="classified only", metrics={},
             limitations="local STF eigenvalues do not determine the Lie-algebra class; no Bianchi transfer likelihood evaluated (cf. Saadeh et al. 2016 for CMB Bianchi constraints)",
             seed_and_sample_count="n/a"),
        dict(comparator_id="B09_ROBUST_ENVELOPE", common_estimand="common 11-coefficient target under the seven declared nuisance-model variants", outcome="TIE", same_data="yes",
             actual_execution="union of the seven 95% ellipsoids and max modelwise p, replayed natively",
             metrics={"max_wald_p_common_11_zero": n["robust"]["max_wald_p"], "max_null_p_32_rows_zero": n["robust"]["max_null_p"]},
             limitations="standard union-of-confidence-sets envelope; the two p-values test different nulls; post hoc nuisance family", seed_and_sample_count="n/a"),
    ]
    for r in rows:
        r.update(input_sha256=inp, response_identity="X_m = O_m [g(z) n, n, STF5(n)], orthonormal STF basis, ICRS observer-to-source, z_CMB",
                 null_hypothesis="alpha = 0 (11) and E[y32] = 0 (32), separately" if r["comparator_id"] == "B09_ROBUST_ENVELOPE" else "n/a",
                 nuisance_models=list(MODELS), uncertainty=r["metrics"].get("max_mc_se_60k", "n/a"),
                 next_action="requires release-matched CF4 survey mocks (new owner scope)" if r["outcome"] == "BLOCKED_EXISTING_INPUT" else "none (R59 terminal)")
    return rows


def claim_rows(n: dict) -> list[list[str]]:
    lo, hi = n["range_cov_block_60k"]
    elo, ehi = n["range_cov_block_exact"]
    flo, fhi = n["range_cov_full_60k"]
    b = n["beta_hull"]
    beta = "; ".join(f"{k} [{g(v['lower'], 4)}, {g(v['upper'], 4)}]" for k, v in b.items())
    return [
        ["C01", "Each of the seven nuisance-model fits of the selected CF4 groups has full rank 11 for (V, dH, kappa) on 32 rows.", "ADMITTED",
         f"{REPLAY}/OWNED_TENSOR_RESULT.json:variants.*.fit.rank", f"rank 11 in {sum(n['models'][m]['rank'] == 11 for m in MODELS)} of {len(MODELS)} models",
         "apparent coefficients only"],
        ["C02", "In a synthetic ablation that drops the polar-STF cross covariance, the coefficient variances are mis-stated along some directions.", "ADMITTED_CONDITIONAL",
         f"{REPLAY}/OWNED_TENSOR_RESULT.json:variants.*.block_diagonal_uncertainty_calibration",
         f"actual/nominal variance eigenvalues {f4(n['range_var_ratio_min'][0])} to {f4(n['range_var_ratio_max'][1])}",
         "fixed design, assumed-correct full covariance; not attributed to any published analysis"],
        ["C03", "Under that Gaussian law the block-factorized nominal 95% ellipsoid under-covers while full GLS is nominal by construction.", "ADMITTED_CONDITIONAL",
         f"{REPLAY}/INDEPENDENT_CHECK.json:checks.*; BENCHMARK_RESULTS.json:B03_CROSS_BLOCK_ABLATION",
         f"exact {f4(elo)}-{f4(ehi)}; 60000 draws {f4(lo)}-{f4(hi)}; full {f4(flo)}-{f4(fhi)}", "not survey coverage; survey-mock replay BLOCKED_EXISTING_INPUT"],
        ["C04", "Full GLS on the same carrier is an exact tie with the tensor carrier and with score compression.", "ADMITTED",
         "BENCHMARK_RESULTS.json:B01_DIRECT_GLS,B02_SCORE", "TIE", "no information advantage is claimed"],
        ["C05", "Every coordinate interval hull of the seven-model union contains zero, while the joint 11-dimensional union excludes the origin.", "ADMITTED_CONDITIONAL",
         f"{REPLAY}/OWNED_TENSOR_RESULT.json:robust", f"max modelwise p for alpha=0: {g(n['robust']['max_wald_p'], 4)}",
         "null = no coherent mean beyond the inherited linear-LCDM body plus noise; post hoc nuisance family; covariance misspecification is an alternative explanation; "
         "not a detection; the 32-row zero-mean null has max p " + g(n["robust"]["max_null_p"], 4)],
        ["C06", "Under free dipole/STF calibration the 22 kinematic+calibration coordinates map to the 11 coefficients with rank 11; sigma/H, omega/H and A/(cH) are individually unbounded.",
         "ADMITTED", f"{REPLAY}/FIVE_VIEW_RESULT.json:models.*.x.physical_pullback", f"rank {n['models']['log']['physical_rank']} of {n['models']['log']['physical_dim']}",
         "first order, low z, same congruence; omega has no scalar-distance column"],
        ["C07", "beta_MR (coherent mean velocity beyond the LCDM covariance, over c) is bounded only under the declared constant-velocity response.", "ADMITTED_CONDITIONAL",
         f"{REPLAY}/FIVE_VIEW_RESULT.json:models.*.x.physical_pullback.intervals_95_simultaneous.beta_MR_*", beta,
         "CONST_V submodel; not a global-tilt test; not the total observer or sample velocity"],
        ["C08", "Cosmic tilt, anisotropic expansion, acceleration, vorticity or a Bianchi class is detected.", "NOT_CLAIMED", "-", "-", "unidentified or not comparable"],
        ["C09", "Survey-level coverage of the intervals is validated.", "NOT_CLAIMED", "BENCHMARK_RESULTS.json:B03S_SURVEY_MOCK_REPLAY", "BLOCKED_EXISTING_INPUT",
         "no release-matched end-to-end mocks"],
        ["C10", "The joint geometry gives more information than exact same-experiment GLS.", "NOT_CLAIMED", "BENCHMARK_RESULTS.json:B01_DIRECT_GLS,B02_SCORE", "TIE",
         "tensorization cannot exceed the exact likelihood"],
        ["C11", "F_support is an occupancy or filling fraction.", "NOT_CLAIMED", f"{REPLAY}/FIVE_VIEW_RESULT.json:models.*.F.occupancy", n["models"]["log"]["occupancy"],
         "no admitted physical ceiling and measure"],
        ["C12", "The five views are independent evidence.", "NOT_CLAIMED", f"{REPLAY}/FIVE_VIEW_RESULT.json:definition_guard", "one likelihood", "never multiplied"],
        ["C13", "The STF basis or the joint fit of mask-coupled CF4 multipoles is new.", "NOT_CLAIMED", "BENCHMARK_RESULTS.json:B06A..B06C,B06X", "NOT_COMPARABLE",
         "prior CF4 multipole work (Vicente et al. 2026; Kalbouneh et al. 2025; Salzano et al. 2025; Boubel et al. 2025)"],
    ]


def manuscript(d: dict, n: dict, rows: list[dict]) -> str:
    M = n["models"]
    lo, hi = n["range_cov_block_60k"]
    elo, ehi = n["range_cov_block_exact"]
    flo, fhi = n["range_cov_full_60k"]
    se60 = max(M[m]["mc_se_60k"] for m in MODELS)
    win = ", ".join(str(w) for w in d["windows"])
    t1 = "\n".join(f"| {m} | {M[m]['rank']} | {g(M[m]['wald_p'])} | {g(M[m]['null_p'])} | {g(M[m]['adequacy_p'])} | {f4(M[m]['cc_max'])} | "
                   f"{f4(M[m]['var_ratio_min'])}-{f4(M[m]['var_ratio_max'])} | {f4(M[m]['cov_block_exact'])} | {f4(M[m]['cov_block_60k'])} | {f4(M[m]['cov_full_60k'])} |"
                   for m in MODELS)
    t2 = "\n".join(f"| {k} | {g(b['lower'], 4)} | {g(b['upper'], 4)} | {'yes' if n['hull_contains_zero'][k] else 'no'} |" for k, b in n["robust"]["hull"].items())
    t3 = "\n".join(f"| {k} | {g(b['lower'], 4)} | {g(b['upper'], 4)} |" for k, b in n["directions"].items())
    tb = "\n".join(f"| {k} | {g(b['lower'], 4)} | {g(b['upper'], 4)} |" for k, b in n["beta_hull"].items())
    tbench = "\n".join(f"| {r['comparator_id']} | {r['outcome']} | {r['limitations']} |" for r in rows)
    refs = "\n".join(f"- {v}" for v in LITERATURE.values())
    return f"""# Joint dipole-quadrupole covariance and calibration freedom in the apparent low-redshift Hubble-rate anisotropy of Cosmicflows-4 groups

*Bounded methods/application note (claim tier C0). Every number below is generated by `scripts/r58/build_r59_outputs.py` from the
native replay in `RESULTS/NATIVE_REPLAY` (parity record `RESULTS/NATIVE_REPLAY/REFERENCE_PARITY.json`).*

## Abstract

We fit one 32-row Gaussian linear experiment to {n['n_groups']} selected Cosmicflows-4 (CF4) groups (Tully et al. 2023): the dipoles
(12 rows) and the symmetric trace-free (STF) quadrupoles (20 rows) of log-distance residuals in four redshift windows, with a measurement
covariance (including a nonlinear velocity dispersion) plus a fixed linear-LCDM cosmic-velocity covariance, under seven zero-point
nuisance-model variants (one without an extra template). The apparent coefficients x = (V, d_H, kappa) - a coherent mean velocity beyond
the LCDM covariance, an apparent log-H dipole and an apparent log-H STF tensor - have full rank 11 in every variant. The polar and STF
blocks are strongly correlated (largest canonical correlation {f4(n['range_cc_max'][0])}-{f4(n['range_cc_max'][1])}). In a synthetic
ablation that keeps the response but drops the cross covariance, the actual-to-nominal variance eigenvalues span
{f4(n['range_var_ratio_min'][0])}-{f4(n['range_var_ratio_max'][1])}, and under the assumed Gaussian law the nominal 95% ellipsoid covers
{f4(elo)}-{f4(ehi)} (exact weighted chi-square; 60,000-draw check {f4(lo)}-{f4(hi)}), whereas full GLS is nominal by construction. Every
coordinate interval hull of the seven-variant union contains zero, whereas the joint 11-dimensional union excludes the origin (largest
modelwise p = {g(n['robust']['max_wald_p'], 4)}): a post hoc tension with the assumed linear-LCDM covariance, not a detection.
The map from 22 normalised kinematic and calibration coordinates to x has rank {M['log']['physical_rank']}: with free dipole and STF
calibration the shear sigma/H, the vorticity omega/H and the acceleration A/(cH) are individually unbounded. Full GLS on the same carrier
ties with the tensor carrier and with score compression. We claim no information advantage over GLS, no cosmological anisotropy, tilt or
Bianchi detection, and no survey-level coverage.

## 1. Data, response and covariance

The rows are the {n['n_groups']} selected CF4 groups of an earlier catalogue-level analysis of the same data (selection fixed there and
not revisited), with the catalogue z_CMB and ICRS/J2000 observer-to-source directions. The four redshift windows are Gaussian
redshift weights exp[-(z - z_w)^2 / (2 s^2)] centred at z_w = {win} with dispersion s = {d['window_width']}. For object i,

    eta_i = N_(m,i) gamma_m + g(z_i) n_i.V + n_i.d_H + sum_A kappa_A E^A_ab n_i^a n_i^b + eps_i,   y_m = O_m eta,   X_m = O_m D,

where eta_i is the log ratio of the redshift distance to the indicator distance, g(z) = [(1+z)/(E(z) chi_hat(z)) - 1]/c is the response
of eta to a radial velocity, E^A is an orthonormal STF5 basis, V is in km/s and d_H and kappa are dimensionless; O_m is the window and
nuisance projection of variant m. The design keeps the velocity leakage into the STF rows.

The covariance is C_m = O_m C_noise O_m^T + C_cos. C_noise is diagonal per object: the indicator distance-modulus error plus a
nonlinear velocity dispersion of {g(d['sigma_star'])} km/s propagated through g(z). C_cos is the undamped linear-LCDM pair-sum
covariance of the catalogue peculiar velocities, reused from a cache (operator byte fingerprints differ from the recorded ones; reuse
rests on equal model keys, equal row labels and numerical parity). Every null below is therefore relative to this body: alpha = 0 means
"no coherent mean beyond linear-LCDM flows and the stated noise", not "no bulk flow". The seven variants were fixed before this analysis
and not pruned by its p-values; the family itself was assembled across earlier analyses of the same catalogue, so every statement below
is post hoc with respect to these data.

The log-likelihood is -2 log L_m(alpha) = q0 - 2 t^T alpha + alpha^T J alpha + log|C_m| + 32 log 2 pi, with J = X_m^T C_m^-1 X_m and
t = X_m^T C_m^-1 y_m, evaluated through Cholesky whitening and a scaled SVD; q0 and log|C_m| are kept; a disagreement between the scaled
and the unit-equilibrated rank stops the computation. Likelihood values of different O_m are not compared as model evidence.

## 2. Results per nuisance-model variant

Table 1. Fits on 32 rows: rank; p-values of the named fixed-Gaussian nulls (alpha = 0 against chi2 with 11 dof, E[y] = 0 against chi2
with 32 dof, residual adequacy against chi2 with 21 dof); largest polar-STF canonical correlation; range of actual/nominal variance
eigenvalues in the synthetic block-factorized ablation; coverage of its nominal 95% ellipsoid, exact and from 60,000 independent draws
(Monte Carlo s.e. at most {g(se60, 2)}); and the full-GLS coverage of the same draws.

| variant | rank | p(alpha=0) | p(E y=0) | p(adequacy) | max can. corr. | var. ratio | block cov. exact | block cov. 60k | full cov. 60k |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
{t1}

The exact coverage is P(sum_j lambda_j Z_j^2 <= c95) with the variance eigenvalues lambda_j and c95 the 95% point of chi2 with 11 dof
(Imhof's formula); it agrees with the draws to {g(n['exact_vs_60k_max_abs'], 2)}. Full GLS is nominal by construction under the assumed
law, so the comparison measures what a block-factorized error budget would mis-state if this covariance were correct; it is not
attributed to any published analysis. The two p-values test different nulls (11 coefficients zero vs 32 compressed rows zero). Adequacy
p-values {g(n['range_adequacy_p'][0])}-{g(n['range_adequacy_p'][1])} show no rejection of the declared 11-parameter mean, which does not
establish its physical truth. The per-variant p-values depend strongly on the nuisance model; only the union statements of Section 3 are
reported as results.

## 3. The seven-variant union

Table 2. Simultaneous 95% interval hulls per coordinate of the union of the seven variant ellipsoids (the convex hull of a finite union,
not the joint set; valid at the nominal level if at least one listed fixed-Gaussian variant is correct).

| coordinate | lower | upper | contains 0 |
|---|---:|---:|---|
{t2}

All coordinate hulls contain zero, yet the joint union excludes alpha = 0 (largest modelwise p {g(n['robust']['max_wald_p'], 4)}):
coordinate-wise zero inclusion is not a joint test. Over all 32 rows the largest modelwise p for E[y] = 0 is
{g(n['robust']['max_null_p'], 4)}. The joint exclusion is a post hoc tension with the assumed linear-LCDM covariance; covariance
misspecification (for example an under-estimated nonlinear dispersion, or the choice of the undamped body) could also explain it; this
is not quantified here.

Table 3. Directional projection h(n) = d_H.n + kappa:nn (apparent log-H anisotropy without the coherent velocity and the monopole, first
order) on the six fixed ICRS axes; simultaneous 95% union hulls. The axes were not chosen from the data.

| direction | lower | upper |
|---|---:|---:|
{t3}

## 4. What the coefficients identify

At low redshift and first order, with the same congruence for sources and observer, the directional Hubble rate is
H_dir/H = 1 + sigma_ab n^a n^b / H - A_a n^a/(cH) + O(z, eps^2) (Heinesen 2021; Maartens et al. 2024), with the sign tied to the
observer-to-source convention. With theta = (sigma/H [5], omega/H [3], A/(cH) [3], beta_MR [3], d_cal [3], q_cal [5]) and
V = c beta_MR, d_H = -A/(cH) + d_cal, kappa = sigma/H + q_cal, the map K from theta to x has rank {M['log']['physical_rank']} in
{M['log']['physical_dim']} dimensions in every variant. The free calibration dipole and STF cancel A and sigma; omega has no column in a
scalar distance response. The only identified physical coordinates are {', '.join(M['log']['identified_physical'])}, conditional on the
constant-velocity response (Table 4); beta_MR is the coherent mean velocity beyond the LCDM covariance over c, not the total observer or
sample velocity. No ridge or prior was added to bound the null directions. Stiskalek, Desmond & Lavaux (2025) likewise model an H0
anisotropy through a dipole in the indicator zero point or absolute magnitude, which a fit with free calibration cannot separate from it.

Table 4. Union hull of beta_MR = V/c (simultaneous 95%), constant-velocity response only (CONST_V; not a test of an evolving global tilt).

| coordinate | lower | upper |
|---|---:|---:|
{tb}

## 5. Five views of one likelihood

x (signed estimate with J, t and the full covariance), Q (gauge of the declared coefficient-noise ellipsoid; physical ceiling
UNAVAILABLE), Pi (named fixed-Gaussian tails), F_support (directional support utilisation; occupancy {M['log']['occupancy']} because no
physical ceiling and measure are admitted) and G_F (initial level plus full-covariance depth contrasts; the invertible depth transform
reproduces the normalised log-likelihood to {g(n['range_path_logL_error'][1])}) are representations of one likelihood and are never
multiplied.

## 6. Prior work and comparison

Anisotropy of the local expansion rate in CF4 has been studied with several estimators: a Tully-Fisher H0 dipole tested against a
constant H0 with an LCDM bulk flow (Boubel et al. 2025); log-H0 sky maps fitted with harmonics to l = 3 (Salzano et al. 2025);
expansion-rate multipoles of CF4 and Pantheon+ (Kalbouneh et al. 2025; see Cowell et al. 2022 for a Pantheon+ quadrupole); and dipole to
octupole in harmonic and STF bases with an inverted mask-coupling kernel and a maximum-likelihood reconstruction (Vicente et al. 2026).
The STF basis and the joint treatment of mask-coupled multipoles are therefore not new here. Each of these studies differs from this one
in sample, estimator or law, so no numerical comparison is made. What this note adds is narrower: the size of the error-budget change
when the dipole-quadrupole cross covariance of the exact catalogue operator is dropped, and the explicit calibration quotient (22
coordinates to rank 11) under a seven-variant nuisance union.

| comparator | outcome | limitation |
|---|---|---|
{tbench}

## 7. Limitations

- Kinematics: with free dipole and STF calibration only beta_MR (under the constant-velocity response) is bounded; sigma/H, omega/H and
  A/(cH) are individually unbounded, and omega has no column in a scalar distance response.
- Directional Hubble factor: the fit uses a common constant coefficient across the four windows at first order; the depth contrasts of
  G_F are a re-representation of the same likelihood, not a measured evolution.
- Boost versus tilt: only a constant coherent velocity across the windows (CONST_V) is modelled; a homogeneous tilt that evolves with
  depth is neither tested nor excluded.
- Anisotropy classification: an apparent STF tensor does not determine a Bianchi class; no class-specific transfer was evaluated.
- Survey coverage is unresolved: no release-matched end-to-end CF4 survey mock exists locally, so the
coverage numbers above hold only under the fixed Gaussian law with the assumed covariance. The cosmic-variance body was inherited, not
recomputed; unknown systematics, selection misspecification and model-search multiplicity are outside the stated coverage. A Bianchi
interpretation would need class-specific transfer likelihoods such as those used for the CMB (Saadeh et al. 2016); none was evaluated.

## 8. Conclusion

In the selected CF4 groups the dipole and quadrupole blocks of the apparent low-redshift Hubble-rate anisotropy are strongly correlated
through the catalogue operator. Under the assumed covariance, an error budget that ignores this correlation mis-states variances along
some directions and under-covers. Free calibration leaves shear, vorticity and acceleration individually unidentified. The analysis ties
with exact GLS and makes no detection claim.

## Reproducibility

Native replay: {n['n_groups']} groups, {n['n_models']} variants, frozen-marginal error {g(n['marginal_err'])}, every numeric output within
rtol 1e-7 / atol 1e-9 of the committed reference (null-space bases compared as subspaces), independent checker status
`{d['indep']['status']}`. Commands, versions and exit codes: `LOCAL_RESULT.json` and `BENCHMARK_EXECUTION_LOG.txt`.

## References

{refs}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = ap.parse_args()
    root = args.root
    d = load(root)
    n = collect(d)
    rows = benchmark_rows(d, n)
    pkg = d["pkg"]
    claims = claim_rows(n)

    (pkg / "BENCHMARK_RESULTS.json").write_text(json.dumps({"schema": "htt.r59.benchmark_results/1", "claim_tier": "C0", "rows": rows, "score_checks": n["score"],
                                                            "literature_checked_2026_11_17": LITERATURE}, indent=1, sort_keys=True) + "\n")
    with (pkg / "BENCHMARK_TABLE.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["competitor", "same_data", "same_estimand", "same_law", "metric", "value", "uncertainty", "verdict", "limitation"])
        for r in rows:
            same = r["outcome"] in ("TIE", "BETTER_CALIBRATED_THAN_ABLATION")
            w.writerow([r["comparator_id"], r["same_data"], "yes" if same else "no", "yes" if same else "no", ";".join(r["metrics"]) or "-",
                        json.dumps(r["metrics"], sort_keys=True) if r["metrics"] else "-", r["uncertainty"], r["outcome"], r["limitations"]])
    ref_impl, rep_impl = d["owned_ref"]["implementation"], d["owned"]["implementation"]
    env = {"native": d["env_native"], "replay_result_implementation": rep_impl, "reference_result_implementation": ref_impl}
    log_lines = ["R59 native execution log", f"logs: {LOG_DIR} (outside the repository)", "environment:"] + [f"  {x}" for x in d["env_native"]] + ["commands:"]
    log_lines += [f"  [{k}] {v}" for k, v in COMMANDS.items()] + ["exit codes:"] + [f"  {x}" for x in d["exit_lines"]]
    (pkg / "BENCHMARK_EXECUTION_LOG.txt").write_text("\n".join(log_lines) + "\n")
    with (pkg / "CLAIM_TABLE.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["claim_id", "statement", "status", "evidence", "value", "limitation"])
        w.writerows(claims)
    (pkg / "MANUSCRIPT.md").write_text(manuscript(d, n, rows))

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip()
    code = {p: sha(root / p) for p in ("scripts/r58/run_r58_owned_tensor.py", "scripts/r58/build_r58_views.py", "scripts/r58/check_r58_independent.py",
                                         "scripts/r58/compare_r59_native_replay.py", "scripts/r58/build_r59_outputs.py", "htt/htt/htt/infer/r58_mixed_tensor_likelihood.py")}
    dec = d["decision"] or {"decision": "PENDING_REVIEW", "basis": [], "review": None}
    local = {
        "schema": "htt.r59.local_result/1", "base_sha": d["dag"]["base_sha"], "head_sha": head,
        "input_hashes": d["owned"]["inputs_sha256"], "replay_output_hashes": d["parity"]["files_sha256"], "code_hashes": code,
        "environment": env,
        "changed_dependencies": {"inputs": d["parity"]["changed_inputs"], "allowed_repaired_hashes": d["parity"]["allowed_repaired_hashes"],
                                 "explanation": "r54_tensor_five_view.py differs from the R58 base only by input validation of the finite-MC helper (allowlisted repair); "
                                                "Python/NumPy differ from the reference environment"},
        "commands": COMMANDS, "commands_exit_codes": d["exit_lines"],
        "reference_parity": {"accepted": d["parity"]["accepted"], "acceptance": d["parity"]["acceptance"], "tolerances": d["parity"]["tolerances"],
                             "basis_leaves_elementwise_different": d["parity"]["five_view_result"]["basis_leaves_elementwise_different"],
                             "null_subspace_max_principal_angle": d["parity"]["five_view_result"]["null_subspace_max_principal_angle"],
                             "provenance_differences": d["parity"]["owned_result"]["provenance_differences"]},
        "benchmark_decisions": {r["comparator_id"]: r["outcome"] for r in rows},
        "claim_admissions": {c[0]: c[2] for c in claims},
        "unmeasured": ["survey-level coverage (no release-matched end-to-end CF4 survey mocks)", "individual sigma/H, omega/H, A/(cH)", "evolving global tilt",
                       "Bianchi class", "E-mode physical calibration", "occupancy F_occupancy", "true cosmic covariance (inherited linear body, not recomputed)"],
        "failures": [{"category": "INPUT", "command": "survey-mock replay (B03S_SURVEY_MOCK_REPLAY)", "exit_code": None, "affected_claim": "C09 survey coverage",
                      "minimal_next_action": "release-matched CF4 end-to-end mocks under a new owner scope"},
                     {"category": "ENVIRONMENT", "command": COMMANDS["parity"], "exit_code": 0,
                      "affected_claim": "none: null_basis entries differ elementwise between LAPACK builds while the null subspaces agree",
                      "minimal_next_action": "none"}],
        "decision": dec["decision"], "decision_basis": dec.get("basis", []), "decision_review": dec.get("review"),
        "next_action": "STOP (R59 terminal; no R60, no new data, no native solver)",
    }
    (pkg / "LOCAL_RESULT.json").write_text(json.dumps(local, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"decision": local["decision"], "benchmark": local["benchmark_decisions"],
                      "exact_block_coverage": [round(x, 5) for x in n["range_cov_block_exact"]], "exact_vs_60k": n["exact_vs_60k_max_abs"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
