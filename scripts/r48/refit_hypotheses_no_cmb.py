"""Re-fit of the four R40 hypotheses (H_0, H_loc, H_tilt, H_mix) on the real-data channels WITHOUT the Planck PR4 CMB probe.

User decisions 2026-11-12: NPIPE/PR4 path excluded; unblinding of the remaining channels approved for this re-fit.
Channel inputs: Quasars/Radio/Gaia are earlier DERIVED result files (measured dipoles, VSH coefficients), SNe is the Pantheon+ 490 residual cache,
PV is the CF4 operator file, DESI is the BAO mean/cov text; every loaded file is SHA256-hashed into the output.
Free theta_K (index): H_loc beta_MO[14:17]; H_tilt beta_RM[11:14]; H_mix sigma5[0:5]+beta_RM+beta_MO.
Modes: fixed psi (likelihood fiducial) and free psi = (H_0, Omega_m, DeltaOmega_k) with declared bounds; r_d fixed at 147.09 (H_0*r_d degeneracy in BAO).
Objective: total chi2 (maximum likelihood, no prior); SNe/PV absolute offsets are analytically marginalised inside the likelihood.
Usage: PYTHONPATH=htt/src:htt:. python3 scripts/r48/refit_hypotheses_no_cmb.py --repo-root <checkout with data> --out result.json
"""
import argparse, hashlib, json, math, platform, time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from htt.htt.infer.tensor_joint_multiprobe_likelihood import TensorJointMultiprobeLikelihood
PROBES = ["Quasars", "Radio", "Gaia", "SNe", "PV", "DESI"]
TSCALE = np.array([1e-4] * 5 + [1e-4] * 3 + [1e-3] * 3 + [1e-3] * 3 + [1e-3] * 3)
HYP = {"H_0": [], "H_loc": list(range(14, 17)), "H_tilt": list(range(11, 14)), "H_mix": list(range(0, 5)) + list(range(11, 17))}
PSI = [(17, 1.0, 67.4, (50.0, 90.0), "H_0"), (18, 0.1, 0.315, (0.05, 0.60), "Omega_m"), (20, 0.1, 0.0, (-0.30, 0.30), "DeltaOmega_k")]   # (state index, scale, start, bounds, name)
FIXED_PSI = np.array([67.4, 0.315, 147.09, 0.0])
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--repo-root", required=True); ap.add_argument("--out", required=True); a = ap.parse_args(); t0 = time.time(); root = Path(a.repo_root)
    lik = TensorJointMultiprobeLikelihood(repo_root=root, enabled_probes=PROBES); n = lik.n_data; rng = np.random.default_rng(20261112)
    files = {p: lik.all_probes[p].source_path for p in PROBES}
    extra = root / "docs/research_program/observational_publication_20261015/OBSERVATIONAL_CONVERGENCE_20261107/COUNT_SELECTION_DIAGNOSTICS/count_dipole_summary.json"
    extra_cov = Path("/mnt/extdrive/workdir/raw/observational_bundles/DESI_BAO_compact/bao_desi_gaussian_bao_ALL_GCcomb_cov.txt")
    hashes = {p: {"path_tail": "/".join(Path(f).parts[-3:]), "sha256": sha(f)} for p, f in files.items()}
    hashes["Quasars_cov"] = {"path_tail": "/".join(extra.parts[-3:]), "sha256": sha(extra)}; hashes["DESI_cov"] = {"path_tail": extra_cov.name, "sha256": sha(extra_cov)}
    out = {"scope": "re-fit without CMB/PR4; unblinding approved by user 2026-11-12", "probes": PROBES, "n_data": n, "probe_dof": lik.probe_dof, "input_files": hashes, "r_d_fixed": 147.09,
           "versions": {"python": platform.python_version(), "numpy": np.__version__}, "modes": {}}
    for mode in ("fixed_psi", "free_psi"):
        free_psi = PSI if mode == "free_psi" else []
        res = {}
        for h, idx in HYP.items():
            nth = len(idx)
            def state(x):
                s = np.concatenate([np.zeros(17), FIXED_PSI]); s[idx] = x[:nth] * TSCALE[idx]
                for j, (si, sc, st, bd, nm) in enumerate(free_psi): s[si] = st + x[nth + j] * sc
                return s
            f = lambda x: lik.chi2(state(x))
            nfree = nth + len(free_psi)
            if nfree == 0: best = {"x": np.zeros(0), "fun": f(np.zeros(0)), "message": "no free parameters", "success": True, "nit": 0, "nfev": 1, "fun_by_start": []}
            else:
                bounds = [(None, None)] * nth + [((bd[0] - st) / sc, (bd[1] - st) / sc) for (si, sc, st, bd, nm) in free_psi]
                runs = []
                for k in range(3):
                    x0 = np.zeros(nfree) if k == 0 else rng.normal(size=nfree) * 0.5
                    if free_psi:
                        for j, b in enumerate(bounds[nth:]): x0[nth + j] = min(max(x0[nth + j], b[0] + 1e-6), b[1] - 1e-6)
                    runs.append(minimize(f, x0, method="L-BFGS-B", bounds=bounds, options={"maxiter": 500, "ftol": 1e-12, "gtol": 1e-8}))
                r = min(runs, key=lambda q: q.fun)
                best = {"x": r.x, "fun": float(r.fun), "message": str(r.message), "success": bool(r.success), "nit": int(r.nit), "nfev": int(r.nfev), "fun_by_start": [float(q.fun) for q in runs]}
            s = state(best["x"]); k = nfree
            res[h] = {"k": k, "theta_hat": s[:17].tolist(), "psi_hat": s[17:].tolist(), "chi2_total": float(best["fun"]), "chi2_by_probe": lik.chi2_breakdown(s),
                      "optimizer": {kk: best[kk] for kk in best if kk not in ("x", "fun")}, "AIC": float(best["fun"] + 2 * k), "BIC": float(best["fun"] + k * math.log(n))}
        mb = min(v["BIC"] for v in res.values()); ma = min(v["AIC"] for v in res.values())
        for v in res.values(): v["Delta_BIC"] = v["BIC"] - mb; v["Delta_AIC"] = v["AIC"] - ma
        out["modes"][mode] = {"hypotheses": res, "best_by_BIC": min(res, key=lambda q: res[q]["BIC"])}
        print(mode, {h: (round(v["chi2_total"], 1), round(v["Delta_BIC"], 1)) for h, v in res.items()}, "best", out["modes"][mode]["best_by_BIC"])
    out["elapsed_s"] = time.time() - t0
    json.dump(out, open(a.out, "w"), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
if __name__ == "__main__": main()
