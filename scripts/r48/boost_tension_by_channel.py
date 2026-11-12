"""Per-channel constraints on the observer boost beta_MO and the chi2 cost of the count-dipole best fit in the other channels.
No CMB/PR4 probe is constructed. All models are linear in beta_MO, so each probe's chi2 is an exact quadratic: beta_hat = -H^-1 g, cov = 2 H^-1 (H = d2chi2/dbeta2).
Count blocks are also reported one by one (beta = d/f) with a flag for blocks whose data are hard-coded literals in the likelihood module (no source file).
Usage: PYTHONPATH=htt/src:htt:. python3 scripts/r48/boost_tension_by_channel.py --repo-root <checkout with data> --out result.json
"""
import argparse, json, platform
from pathlib import Path
import numpy as np
from htt.htt.infer.tensor_joint_multiprobe_likelihood import TensorJointMultiprobeLikelihood, ThetaKinematic, PsiCosmology
PROBES = ["Quasars", "Radio", "Gaia", "SNe", "PV"]
def chi2_p(lik, p, beta):
    v = np.zeros(17); v[14:17] = beta; return float(lik.all_probes[p].compute(ThetaKinematic.from_vector(v), PsiCosmology())[0])
def quad(f, h=1e-3):
    """exact gradient/Hessian of a quadratic in 3 variables from finite differences"""
    g = np.zeros(3); H = np.zeros((3, 3)); f0 = f(np.zeros(3)); E = np.eye(3) * h
    for i in range(3):
        fp, fm = f(E[i]), f(-E[i]); g[i] = (fp - fm) / (2 * h); H[i, i] = (fp - 2 * f0 + fm) / h ** 2
    for i in range(3):
        for j in range(i + 1, 3):
            H[i, j] = H[j, i] = (f(E[i] + E[j]) - f(E[i] - E[j]) - f(-E[i] + E[j]) + f(-E[i] - E[j])) / (4 * h * h)
    return f0, g, H
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--repo-root", required=True); ap.add_argument("--out", required=True); ap.add_argument("--count-alpha", type=float, default=0.75); a = ap.parse_args()
    lik = TensorJointMultiprobeLikelihood(repo_root=Path(a.repo_root), enabled_probes=PROBES, count_alpha=a.count_alpha); out = {"versions": {"python": platform.python_version(), "numpy": np.__version__}, "channels": {}, "count_blocks": {}}
    fits = {}
    for p in PROBES:
        f0, g, H = quad(lambda b: chi2_p(lik, p, b)); Hi = np.linalg.inv(H); bh = -Hi @ g; cov = 2 * Hi
        fits[p] = (bh, cov, f0 + g @ bh + 0.5 * bh @ H @ bh, H, f0, g)
        out["channels"][p] = {"beta_hat": bh.tolist(), "sd_axes": np.sqrt(np.diag(cov)).tolist(), "norm": float(np.linalg.norm(bh)), "chi2_at_null": f0, "chi2_at_own_best": float(f0 + g @ bh + 0.5 * bh @ H @ bh),
                              "delta_chi2_null_vs_best_3dof": float(f0 - (f0 + g @ bh + 0.5 * bh @ H @ bh))}
    # joint count fit and chi2 cost in the other channels at the count best fit
    cnt = ["Quasars", "Radio"]
    def fc(b): return sum(chi2_p(lik, p, b) for p in cnt)
    f0, g, H = quad(fc); Hi = np.linalg.inv(H); bc = -Hi @ g; covc = 2 * Hi
    out["count_joint"] = {"beta_hat": bc.tolist(), "sd_axes": np.sqrt(np.diag(covc)).tolist(), "norm": float(np.linalg.norm(bc))}
    out["cost_of_count_best_fit_in_other_channels"] = {}
    for p in ("Gaia", "SNe", "PV"):
        bh, cov, fmin, H_, f0p, gp = fits[p]; fb = chi2_p(lik, p, bc)
        out["cost_of_count_best_fit_in_other_channels"][p] = {"chi2_at_count_best": fb, "chi2_at_own_best": fmin, "delta_chi2_vs_own_best_3dof": fb - fmin, "chi2_at_null": f0p}
    # individual count blocks
    lit = {"Quasars_G20": ("sourced result file", 0), "Quasars_G20p5": ("HARD-CODED LITERAL in likelihood module (no source file)", 3), "NVSS": ("sourced result file", 0), "RACS": ("HARD-CODED LITERAL in likelihood module (no source file)", 3)}
    for name, (p, sl, f, note) in {"Quasars_G20": ("Quasars", slice(0, 3), lik.all_probes["Quasars"].predict(ThetaKinematic.from_vector(np.r_[np.zeros(14), 1, 0, 0]), PsiCosmology())[0], lit["Quasars_G20"][0]),
                                    "Quasars_G20p5": ("Quasars", slice(3, 6), lik.all_probes["Quasars"].predict(ThetaKinematic.from_vector(np.r_[np.zeros(14), 1, 0, 0]), PsiCosmology())[3], lit["Quasars_G20p5"][0]),
                                    "NVSS": ("Radio", slice(0, 3), lik.all_probes["Radio"].predict(ThetaKinematic.from_vector(np.r_[np.zeros(14), 1, 0, 0]), PsiCosmology())[0], lit["NVSS"][0]),
                                    "RACS": ("Radio", slice(3, 6), lik.all_probes["Radio"].predict(ThetaKinematic.from_vector(np.r_[np.zeros(14), 1, 0, 0]), PsiCosmology())[3], lit["RACS"][0])}.items():
        pr = lik.all_probes[p]; d = pr.data_vector[sl]; c = pr.cov_matrix[sl, sl]
        out["count_blocks"][name] = {"data_provenance": note, "response_factor_used": float(f), "dipole_vector": d.tolist(), "dipole_amplitude": float(np.linalg.norm(d)), "beta_equiv": (d / f).tolist(), "beta_equiv_norm": float(np.linalg.norm(d / f)), "sd_axes": (np.sqrt(np.diag(c)) / f).tolist()}
    json.dump(out, open(a.out, "w"), indent=1)
    for p, v in out["channels"].items(): print(p, "beta_hat", np.round(v["beta_hat"], 5), "sd", np.round(v["sd_axes"], 5), "dchi2(null->best)", round(v["delta_chi2_null_vs_best_3dof"], 1))
    print("count joint", np.round(out["count_joint"]["beta_hat"], 5), "|b|", round(out["count_joint"]["norm"], 5))
    for p, v in out["cost_of_count_best_fit_in_other_channels"].items(): print("cost in", p, round(v["delta_chi2_vs_own_best_3dof"], 1))
    for n, v in out["count_blocks"].items(): print(n, v["data_provenance"][:12], "f", v["response_factor_used"], "|D|", round(v["dipole_amplitude"], 4), "beta_eq", round(v["beta_equiv_norm"], 5))
if __name__ == "__main__": main()
