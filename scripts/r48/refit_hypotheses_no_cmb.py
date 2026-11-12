"""Re-fit of the four R40 hypotheses (H_0, H_loc, H_tilt, H_mix) on the real-data channels WITHOUT the Planck PR4 CMB probe.

User decisions 2026-11-12: NPIPE/PR4 path excluded; unblinding of the remaining channels approved for this re-fit.
Free parameters (theta_K index): H_loc beta_MO[14:17]; H_tilt beta_RM[11:14]; H_mix sigma5[0:5]+beta_RM+beta_MO. psi fixed at the likelihood's fiducial.
Objective: total chi2 over enabled probes (maximum likelihood; no prior). Optimiser: BFGS in scaled variables from the zero vector and from a second start; best of the two kept.
Usage: PYTHONPATH=htt/src:htt:. python3 scripts/r48/refit_hypotheses_no_cmb.py --repo-root <checkout with data> --out result.json
"""
import argparse, json, math, platform, time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from htt.htt.infer.tensor_joint_multiprobe_likelihood import TensorJointMultiprobeLikelihood
PROBES = ["Quasars", "Radio", "Gaia", "SNe", "PV", "DESI"]
SCALE = np.array([1e-4] * 5 + [1e-4] * 3 + [1e-3] * 3 + [1e-3] * 3 + [1e-3] * 3)
HYP = {"H_0": [], "H_loc": list(range(14, 17)), "H_tilt": list(range(11, 14)), "H_mix": list(range(0, 5)) + list(range(11, 17))}
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--repo-root", required=True); ap.add_argument("--out", required=True); a = ap.parse_args(); t0 = time.time()
    lik = TensorJointMultiprobeLikelihood(repo_root=Path(a.repo_root), enabled_probes=PROBES); n = lik.n_data; rng = np.random.default_rng(20261112)
    out = {"scope": "re-fit without CMB/PR4; real-data channels; unblinding approved by user 2026-11-12", "probes": PROBES, "n_data": n, "probe_dof": lik.probe_dof, "hypotheses": {},
           "versions": {"python": platform.python_version(), "numpy": np.__version__}}
    chi2_null = lik.chi2_breakdown(np.zeros(17)); out["chi2_null_by_probe"] = chi2_null
    for h, idx in HYP.items():
        def f(x):
            th = np.zeros(17); th[idx] = x * SCALE[idx]; return lik.chi2(th)
        if not idx:
            best = {"x": np.zeros(0), "fun": f(np.zeros(0)), "message": "no free parameters", "success": True, "nit": 0, "nfev": 1}
        else:
            runs = []
            for start in (np.zeros(len(idx)), rng.normal(size=len(idx))):
                r = minimize(f, start, method="BFGS", options={"gtol": 1e-6, "maxiter": 400}); runs.append(r)
            r = min(runs, key=lambda q: q.fun)
            best = {"x": r.x, "fun": float(r.fun), "message": str(r.message), "success": bool(r.success), "nit": int(r.nit), "nfev": int(r.nfev), "fun_by_start": [float(q.fun) for q in runs]}
        th = np.zeros(17); th[idx] = np.asarray(best["x"]) * SCALE[idx]; k = len(idx)
        out["hypotheses"][h] = {"k": k, "theta_hat": th.tolist(), "chi2_total": float(best["fun"]), "chi2_by_probe": lik.chi2_breakdown(th), "optimizer": {kk: best[kk] for kk in best if kk not in ("x", "fun")},
                                "AIC": float(best["fun"] + 2 * k), "BIC": float(best["fun"] + k * math.log(n))}
    mb = min(v["BIC"] for v in out["hypotheses"].values()); ma = min(v["AIC"] for v in out["hypotheses"].values())
    for v in out["hypotheses"].values(): v["Delta_BIC"] = v["BIC"] - mb; v["Delta_AIC"] = v["AIC"] - ma
    out["best_by_BIC"] = min(out["hypotheses"], key=lambda q: out["hypotheses"][q]["BIC"]); out["elapsed_s"] = time.time() - t0
    json.dump(out, open(a.out, "w"), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    for h, v in out["hypotheses"].items(): print(h, v["k"], round(v["chi2_total"], 2), round(v["Delta_BIC"], 2), v["optimizer"].get("success"), v["optimizer"].get("message"))
    print("best", out["best_by_BIC"], round(out["elapsed_s"]))
if __name__ == "__main__": main()
