"""R53: adversarial methods benchmark on the R51 CMB lane and the R52 joint lane, plus figures.

Run: PYTHONPATH=htt/src:htt:. python scripts/r53/run_r53_benchmark.py

Same law / prior / selection / nuisance for every method within a lane:
  CMB lane (finite-MC t law, T45, flat box prior, S from FFP10 ids 0-199, noise from heldout ids 200-299)
    full 45D t-law | tensor (F,t,Q0) | Gaussian score (F,t) plug-in | LOO-calibrated Gaussian |
    scalar e1 projection | power-only |s|^2
  Joint lane (R52 linear Gaussian, declared Gaussian priors), estimand beta_RM(0)
    full joint 17D | tensor (F,t) | scalar projection on CMB-dipole axis | power-only |beta_RM0|
"""
from __future__ import annotations

import importlib.util
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy.stats import beta as beta_dist  # noqa: E402
from scipy.stats import t as t_dist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "htt"), str(ROOT / "htt/src")]

from htt.htt.infer.r51_source_bound_response import heldout_pit, signed_linear_carrier  # noqa: E402
from htt.htt.infer.r52_joint_identification import C_KM_S, SL, gaussian_posterior, joint  # noqa: E402

R50 = ROOT / "docs/research_program/observational_publication_20261015/R50_OBSERVED_CONVERGENCE_20261115"
OUT = R50 / "R53"
FIG = OUT / "FIGURES"
CACHE = Path("/mnt/extdrive/workdir/r49_chains/ffp10_300_debiased_135.npz")
RNG_SEED = 53053


def cp(k, n):
    return [0.0 if k == 0 else float(beta_dist.ppf(0.025, k, n - k + 1)), 1.0 if k == n else float(beta_dist.ppf(0.975, k + 1, n - k))]


def r52_module():
    spec = importlib.util.spec_from_file_location("r52run", ROOT / "scripts/r52/run_r52_joint.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def flat_prior_finite_mc_posterior(car: dict, F: np.ndarray, N: int):
    """Flat-prior Sellentin-Heavens posterior for linear model: multivariate t, nu=N-k,
    location F^-1 t, scale (N-1+Qmin)/nu F^-1."""
    Finv = np.linalg.inv(F)
    sh = Finv @ car["t"]
    nu = N - F.shape[0]
    Qmin = car["Q0"] - car["t"] @ sh
    return sh, (N - 1 + Qmin) / nu * Finv, nu


def power_only_loglr(T: float, lam: float, k: int) -> float:
    """log LR(s vs 0) from the sign-even statistic T = s_hat^T F s_hat ~ noncentral chi2_k(lam) (Gaussian law)."""
    from scipy.stats import chi2 as _chi2, ncx2
    if lam <= 0:
        return 0.0
    return float(ncx2.logpdf(T, k, lam) - _chi2.logpdf(T, k))


def analytic_sd_inflation(N: int, p: int, k: int) -> float:
    """Sampling sd of the GLS estimate with a noisy precision, relative to the plug-in Fisher sd:
    sqrt[(N-1)/(N-p-2) * (N-2)/(N-p+k-1)] (Hartlap et al. 2007; Dodelson & Schneider 2013; Percival et al. 2022)."""
    return math.sqrt((N - 1) / (N - p - 2) * (N - 2) / (N - p + k - 1))


def cmb_lane(rng):
    with np.load(R50 / "R51/observed_carrier.npz", allow_pickle=False) as z:
        J = z["response_J_135x5_uK"]
        labels = z["mode_labels"]
    with np.load(CACHE, allow_pickle=False) as z:
        sims = z["sim_tot"].copy()
    T = np.array([str(l).startswith("T_") for l in labels])
    JT = J[T]
    p, k = int(T.sum()), 5
    folds = [np.arange(0, 100), np.arange(100, 200), np.arange(200, 300)]
    # Coverage is truth-independent for this linear model (s_hat - s and Qmin do not depend on s),
    # so it is evaluated over independent noise draws: 3-fold held-out (S from the other 200 sims).
    hits = {m: np.zeros(5, int) for m in ("full_t_law", "gaussian_score_plugin", "loo_calibrated_gaussian")}
    n_draw = 0
    errs, loo_ratio = [], []
    truths = [np.zeros(5)] + [sgn * 1e-5 * np.eye(5)[a] for a in range(5) for sgn in (1, -1)]
    for _ in range(10):
        v = rng.normal(size=5)
        truths.append(2e-5 * v / np.linalg.norm(v))
    lr_err = {"gaussian_score_plugin": [], "scalar_e1": [], "power_only_vs_zero": []}
    tensor_identity = []
    signed = []
    for fold in folds:
        tr = np.setdiff1d(np.arange(300), fold)
        train, held = sims[tr][:, T], sims[fold][:, T]
        N = train.shape[0]
        S = np.cov(train.T, ddof=1); S = 0.5 * (S + S.T)
        Si = np.linalg.inv(S)
        F = JT.T @ Si @ JT
        Finv = np.linalg.inv(F); Finv = 0.5 * (Finv + Finv.T)
        sdF = np.sqrt(np.diag(Finv))
        loo = []
        for i in range(N):
            Sm = np.cov(np.delete(train, i, axis=0).T, ddof=1); Sm = 0.5 * (Sm + Sm.T)
            Smi = np.linalg.inv(Sm)
            loo.append(np.linalg.solve(JT.T @ Smi @ JT, JT.T @ Smi @ train[i]))
        C_emp = np.cov(np.array(loo).T, ddof=1)
        loo_ratio.append(np.sqrt(np.diag(C_emp)) / sdF)
        for x in held:
            car = signed_linear_carrier(JT, x, S)
            sh, scale, nu = flat_prior_finite_mc_posterior(car, F, N)
            tq = t_dist.ppf(0.975, nu)
            hits["full_t_law"] += (np.abs(sh) <= tq * np.sqrt(np.diag(scale))).astype(int)
            hits["gaussian_score_plugin"] += (np.abs(sh) <= 1.959964 * sdF).astype(int)
            hits["loo_calibrated_gaussian"] += (np.abs(sh) <= 1.959964 * np.sqrt(np.diag(C_emp))).astype(int)
            errs.append(sh / sdF)
            n_draw += 1
            for s_true in truths[1:]:
                d = x + JT @ s_true
                c1 = signed_linear_carrier(JT, d, S)
                r1 = d - JT @ s_true
                q1, q0 = r1 @ Si @ r1, d @ Si @ d
                full = -0.5 * N * (math.log1p(q1 / (N - 1)) - math.log1p(q0 / (N - 1)))
                Qc1 = c1["Q0"] - 2 * s_true @ c1["t"] + s_true @ F @ s_true
                tensor_identity.append(abs(-0.5 * N * (math.log1p(Qc1 / (N - 1)) - math.log1p(c1["Q0"] / (N - 1))) - full))
                gau = s_true @ c1["t"] - 0.5 * s_true @ F @ s_true
                s1 = Finv @ c1["t"]
                sc = -0.5 * ((s1[1] - s_true[1]) ** 2 - s1[1] ** 2) / sdF[1] ** 2
                pw = power_only_loglr(float(s1 @ F @ s1), float(s_true @ F @ s_true), 5)
                lr_err["gaussian_score_plugin"].append(abs(gau - full))
                lr_err["scalar_e1"].append(abs(sc - full))
                lr_err["power_only_vs_zero"].append(abs(pw - full))
                signed.append(float(s1 @ s_true > 0))
    N = 200
    cover = {}
    for m, h in hits.items():
        cover[m] = {"per_component_rate": (h / n_draw).tolist(),
                    "per_component_CI95": [cp(int(c), n_draw) for c in h],
                    "pooled_rate": float(h.sum() / (5 * n_draw)), "n_independent_draws": n_draw,
                    "note": "components within a draw are correlated; CIs are per component over independent draws"}
    cover["tensor_F_t_Q0"] = "identical to full_t_law by algebraic identity (same posterior)"
    T0 = sims[200:][:, T][0]
    S = np.cov(sims[:200][:, T].T, ddof=1); S = 0.5 * (S + S.T)
    car = signed_linear_carrier(JT, T0, S)
    Lc = np.linalg.cholesky(S)
    Fm = car["F"]
    s0 = np.full(5, 1e-6)
    times = {}
    for name, fn in {"full_t_law": lambda: np.sum(np.linalg.solve(Lc, T0 - JT @ s0) ** 2),
                     "tensor_F_t_Q0": lambda: car["Q0"] - 2 * s0 @ car["t"] + s0 @ Fm @ s0}.items():
        t0 = time.perf_counter()
        for _ in range(2000):
            fn()
        times[name] = (time.perf_counter() - t0) / 2000
    bias = np.mean(errs, axis=0)
    res = {
        "design": "3-fold held-out over FFP10 ids (100 each); S and LOO calibration from the other 200; coverage over 300 independent noise draws (truth-independent for this linear model)",
        "N_train": N, "p": p, "k": k,
        "coverage_nominal95": cover,
        "loo_sd_over_fisher_sd": np.mean(loo_ratio, axis=0).tolist(),
        "analytic_sd_inflation_N200": analytic_sd_inflation(200, p, k),
        "analytic_sd_inflation_N300": analytic_sd_inflation(300, p, k),
        "bias_mean_in_fisher_sd": bias.tolist(),
        "bias_SE_in_fisher_sd": float(np.mean(np.mean(loo_ratio, axis=0)) / math.sqrt(n_draw)),
        "logLR_error_vs_full_t_law": {m: {"max": float(np.max(v)), "median": float(np.median(v))} for m, v in lr_err.items()},
        "tensor_F_t_Q0_logLR_identity_max_abs": float(np.max(tensor_identity)),
        "logLR_note": "point-vs-point logLR(s_true vs 0) per truth x draw; power-only uses the noncentral-chi2 law of s_hat^T F s_hat; power-only logLR(+s vs -s) = 0 identically",
        "signed_direction_recovery_rate_full": float(np.mean(signed)),
        "fisher_retention_analytic": {"tensor": 1.0, "optimal_score": 1.0, "scalar_e1_worst_direction": 0.0, "power_only_local_at_zero": 0.0,
                                      "note": "analytic: rank-one projection keeps 1 of 5 directions; a sign-even statistic has zero local Fisher at s=0"},
        "runtime_s_per_eval": times,
    }
    pits = {}
    for cname, rows in (("T45", T), ("TEB135", np.ones(135, bool))):
        u = [heldout_pit(x[rows], sims[:200][:, rows]) for x in sims[200:]]
        pits[cname] = {k_: np.array([q[k_] for q in u]) for k_ in ("pit_finite_mc", "pit_plugin_gaussian")}
    return res, pits


def joint_lane(rng):
    m = r52_module()
    om_r = m.radiation_density_parameter(m.PLANCK18["H0"] / 100)
    probes, _ = m.build_probes(om_r, {})
    jt = joint(probes)
    mean, cov = gaussian_posterior(jt["F"], jt["t"], m.SCALE)
    sub = cov[SL["bRM"], SL["bRM"]]
    l, b = math.radians(m.SOLAR_DIPOLE["l_deg"]), math.radians(m.SOLAR_DIPOLE["b_deg"])
    ax = np.array([math.cos(b) * math.cos(l), math.cos(b) * math.sin(l), math.sin(b)])
    Ls = [np.linalg.cholesky(p.C) for p in probes]
    hits = {"full_tensor_per_component": 0, "scalar_axis": 0}
    n_rep = 2000
    ests = []
    for _ in range(n_rep):
        reps = []
        for p, L in zip(probes, Ls):
            y = p.J @ mean + L @ rng.normal(size=p.y.size)
            if p.N.shape[1]:
                y = y + p.N @ rng.normal(size=p.N.shape[1])
            reps.append(type(p)(p.name, y, p.C, p.J, p.N, block_id=p.block_id))
        jj = joint(reps)
        mm, cc = gaussian_posterior(jj["F"], jj["t"], m.SCALE)
        e = mm[SL["bRM"]]
        ests.append(e)
        hits["full_tensor_per_component"] += int(np.sum(np.abs(e - mean[SL["bRM"]]) <= 1.959964 * np.sqrt(np.diag(cc[SL["bRM"], SL["bRM"]]))))
        hits["scalar_axis"] += int(abs(ax @ (e - mean[SL["bRM"]])) <= 1.959964 * math.sqrt(ax @ cc[SL["bRM"], SL["bRM"]] @ ax))
    ests = np.array(ests)
    Fb = np.linalg.inv(sub)
    FI = np.outer(ax, ax) / (ax @ sub @ ax)
    gen = np.sort(np.real(np.linalg.eigvals(np.linalg.solve(Fb, FI))))
    a = mean[SL["bRM"]]
    ppc = json.loads((R50 / "R52/R52_JOINT_RESULT.json").read_text())["baseline"]["ppc_at_posterior_mean"]["CF4_H03"]
    cf4_scale = ppc["chi2"] / ppc["effective_dof"]
    tension = {}
    for nm, var in {"measurement_cov": {}, "bulk_150kms": {"cf4_bulk_sd_kms": 150.0}, "bulk_250kms": {"cf4_bulk_sd_kms": 250.0},
                    "cf4_cov_ppc_scaled": {"cf4_cov_scale": cf4_scale},
                    "bulk_250kms_plus_cf4_ppc": {"cf4_bulk_sd_kms": 250.0, "cf4_cov_scale": cf4_scale}}.items():
        def sub(drop):
            pr, _ = m.build_probes(om_r, {**var, "drop": drop})
            jj = joint(pr)
            return gaussian_posterior(jj["F"], jj["t"], m.SCALE)
        mA, cA = sub(["CF4_H03"])
        mB, cB = sub(["Quaia_dipole", "NVSS_dipole", "RACS_dipole"])
        dl = mA[SL["bRM"]] - mB[SL["bRM"]]
        c2 = float(dl @ np.linalg.solve(cA[SL["bRM"], SL["bRM"]] + cB[SL["bRM"], SL["bRM"]], dl))
        from scipy.stats import chi2 as _c2
        tension[nm] = {"chi2_3": c2, "working_tail": float(_c2.sf(c2, 3))}
    res = {
        "frame_consistency_counts_vs_cf4": tension,
        "estimand": "beta_RM(0), Galactic, v/c",
        "n_replications": n_rep,
        "coverage_check_type": "code-consistency check: replications drawn from the model's own Gaussian law",
        "coverage_per_component_nominal95": {"k": hits["full_tensor_per_component"], "n": 3 * n_rep, "rate": hits["full_tensor_per_component"] / (3 * n_rep),
                                             "CI95": cp(hits["full_tensor_per_component"], 3 * n_rep),
                                             "note": "replications at truth = posterior mean; prior shrinkage is negligible for beta_RM"},
        "coverage_scalar_axis_nominal95": {"k": hits["scalar_axis"], "n": n_rep, "rate": hits["scalar_axis"] / n_rep, "CI95": cp(hits["scalar_axis"], n_rep)},
        "replication_bias_kms": (C_KM_S * (ests.mean(axis=0) - a)).tolist(),
        "fisher_retention_analytic": {"tensor": 1.0, "scalar_cmb_axis_worst": float(max(gen[0], 0.0)), "power_only_local": 0.0,
                                      "scalar_eigs": np.clip(gen, 0, None).tolist()},
        "signed_logLR_plus_vs_minus_posterior_mean": {"full_tensor": float(2 * a @ Fb @ a), "power_only": 0.0},
        "beta_RM0_along_cmb_axis_kms": float(C_KM_S * ax @ a),
        "beta_RM0_perp_norm_kms": float(C_KM_S * np.linalg.norm(a - (ax @ a) * ax)),
        "tie_tensor_vs_raw": "exact by linear-Gaussian algebra ((F,t) sufficient); Cobaya chain ties analytic (R52)",
    }
    return res, (mean, cov, probes, m)


EQUIVALENCE = [
    {"family": "FLRW", "constraint": "valid", "source_bound_transfer": "yes (trivial)", "lowell_T_class": "Sigma=0"},
    {"family": "I", "constraint": "valid (no tilt)", "source_bound_transfer": "yes: first-order integrated shear", "lowell_T_class": "Sigma (ell=2 only)"},
    {"family": "V / VII_0 / VII_h / IX", "constraint": "R49 GBI-02 scoped", "source_bound_transfer": "no: finite-curvature focus/twist is a working model",
     "lowell_T_class": "equals I only at the exact abelian zero-curvature boundary; otherwise NOT EVALUABLE"},
    {"family": "II / III / IV / VI_0 / VI_h / VIII", "constraint": "R49 GBI-02 scoped", "source_bound_transfer": "no FLRW limit; geodesic transfer conditional on trajectory",
     "lowell_T_class": "NOT EVALUABLE"},
    {"family": "VI_h, h=-1/9 exceptional stratum", "constraint": "special tilted solutions", "source_bound_transfer": "none", "lowell_T_class": "NOT EVALUABLE"},
    {"family": "multi-fluid tilt history", "constraint": "per-fluid momentum constraints", "source_bound_transfer": "no evolution map beta_RM(z*) -> beta_RM(0)",
     "lowell_T_class": "only beta_RM(0) enters R52; z* tilt NOT EVALUABLE"},
]


def figures(cmb_pits, cmb_res, joint_state):
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "figure.dpi": 150})
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.8), sharey=True)
    bins = np.linspace(0, 1, 11)
    for a, (cn, d) in zip(axs, cmb_pits.items()):
        a.hist(d["pit_finite_mc"], bins=bins, histtype="step", lw=1.6, color="#1f5aa6", label="finite-MC (Sellentin-Heavens)")
        a.hist(d["pit_plugin_gaussian"], bins=bins, histtype="step", lw=1.6, ls="--", color="#c0392b", label="plug-in Gaussian")
        a.axhline(10, color="0.5", lw=0.8)
        a.set_title(f"{cn}: FFP10 heldout ids 200-299", fontsize=8)
        a.set_xlabel("predictive PIT")
    axs[0].set_ylabel("count (100 heldout)")
    axs[0].legend(frameon=False, fontsize=7, loc="upper left")
    fig.tight_layout(); fig.savefig(FIG / "F1_heldout_pit.pdf"); fig.savefig(FIG / "F1_heldout_pit.png"); plt.close(fig)
    r51 = json.loads((R50 / "R51/R51_PR3_LOWELL_RESULT.json").read_text())
    s = np.array(r51["Sigma_hat"]) * 1e5
    sd = np.array(r51["Sigma_sd_gaussian"]) * np.array(r51["interval_calibration"]["loo_sampling_sd_over_fisher_sd"]) * 1e5
    fig, a = plt.subplots(figsize=(3.6, 2.6))
    a.errorbar(np.arange(5), s, yerr=1.96 * sd, fmt="o", color="#1f5aa6", capsize=3)
    a.axhline(0, color="0.5", lw=0.8)
    a.set_xticks(range(5)); a.set_xticklabels([f"$e_{k}$" for k in range(5)])
    a.set_ylabel(r"$\hat\Sigma_k\ [10^{-5}]$")
    a.set_title(r"SMICA PR3 T, $\ell=2$-6, 95% (LOO-calibrated)", fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "F2_integrated_shear.pdf"); fig.savefig(FIG / "F2_integrated_shear.png"); plt.close(fig)
    mean, cov, probes, m = joint_state
    subsets = {"counts + CMB dipole (+Gaia, CMB Σ)": ["CF4_H03"], "CF4 + CMB dipole (+Gaia, CMB Σ)": ["Quaia_dipole", "NVSS_dipole", "RACS_dipole"], "joint": []}
    cols = dict(zip(subsets, ["#c0392b", "#27ae60", "#1f5aa6"]))
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.6), sharey=True)
    om_r = m.radiation_density_parameter(m.PLANCK18["H0"] / 100)
    for j, (nm, drop) in enumerate(subsets.items()):
        pr, _ = m.build_probes(om_r, {"drop": drop})
        jj = joint(pr)
        mm, cc = gaussian_posterior(jj["F"], jj["t"], m.SCALE)
        bb = C_KM_S * mm[SL["bRM"]]
        ee = C_KM_S * np.sqrt(np.diag(cc[SL["bRM"], SL["bRM"]]))
        for i, a in enumerate(axs):
            a.errorbar([j], [bb[i]], yerr=[1.96 * ee[i]], fmt="o", color=cols[nm], capsize=3, label=nm if i == 0 else None)
    for i, a in enumerate(axs):
        a.axhline(0, color="0.5", lw=0.8)
        a.set_xticks([]); a.set_title(f"$\\beta_{{RM}}(0)$, Galactic {'xyz'[i]}", fontsize=8)
    axs[0].set_ylabel("km/s (95%)")
    fig.legend(frameon=False, fontsize=6, loc="lower center", ncol=3)
    fig.tight_layout(rect=(0, 0.08, 1, 1)); fig.savefig(FIG / "F3_beta_RM0_subsets.pdf"); fig.savefig(FIG / "F3_beta_RM0_subsets.png"); plt.close(fig)
    cf = [p for p in probes if p.name == "CF4_H03"][0]
    pred = cf.J @ mean
    se = np.sqrt(np.diag(cf.C))
    zc = json.loads((ROOT / "docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-01-CF4-OPERATOR/RESULT.json").read_text())["window_centers"]
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.4), sharey=True)
    for i, a in enumerate(axs):
        rows = [9 * w + 1 + i for w in range(4)]
        a.errorbar(zc, cf.y[rows], yerr=se[rows], fmt="o", color="k", capsize=2, label="CF4 H03")
        a.plot(zc, pred[rows], "s--", color="#1f5aa6", ms=4, label="joint model")
        a.axhline(0, color="0.5", lw=0.8)
        a.set_xlabel("window $z_{\\rm CMB}$ centre"); a.set_title(f"ICRS apparent-H dipole {'xyz'[i]}", fontsize=8)
    axs[0].set_ylabel("km/s/Mpc"); axs[0].legend(frameon=False, fontsize=6)
    fig.tight_layout(); fig.savefig(FIG / "F4_cf4_window_dipoles.pdf"); fig.savefig(FIG / "F4_cf4_window_dipoles.png"); plt.close(fig)
    cv = {k_: v for k_, v in cmb_res["coverage_nominal95"].items() if isinstance(v, dict)}
    names = list(cv)
    fig, a = plt.subplots(figsize=(4.6, 2.8))
    for i, n in enumerate(names):
        r_ = np.array(cv[n]["per_component_rate"]); ci = np.array(cv[n]["per_component_CI95"])
        xs = i + np.linspace(-0.2, 0.2, 5)
        a.errorbar(xs, r_, yerr=[r_ - ci[:, 0], ci[:, 1] - r_], fmt="o", ms=3, color="#1f5aa6", capsize=2)
    a.axhline(0.95, color="#c0392b", lw=0.8, ls="--", label="nominal 0.95")
    a.set_ylim(0.8, 1.0); a.legend(frameon=False, fontsize=7, loc="lower right")
    a.set_xticks(range(len(names))); a.set_xticklabels([n.replace("_", "\n") for n in names], fontsize=6)
    a.set_ylabel("95% interval coverage per component"); a.set_title("300 independent FFP10 noise draws (3-fold, T45)", fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "F5_method_coverage.pdf"); fig.savefig(FIG / "F5_method_coverage.png"); plt.close(fig)
    return sorted(p.name for p in FIG.glob("*.png"))


def main():
    t0 = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)
    git_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    cmb_res, pits = cmb_lane(rng)
    joint_res, state = joint_lane(rng)
    figs = figures(pits, cmb_res, state)
    out = {"node_id": "R53", "source_git_sha": git_sha, "claim_tier": "C0", "seed": RNG_SEED,
           "cmb_lane": cmb_res, "joint_lane": joint_res, "bianchi_observational_equivalence": EQUIVALENCE,
           "figures": figs, "elapsed_s": time.monotonic() - t0}
    (OUT / "R53_BENCHMARK.json").write_text(json.dumps(out, indent=1, allow_nan=False) + "\n")
    return out


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: r[k] for k in ("cmb_lane", "joint_lane", "figures", "elapsed_s")}, indent=1))
