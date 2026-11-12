"""L2 slice 3: joint Quaia+NVSS kinematic-dipole estimand, structural identifiability over a declared (x, alpha) grid.
Model: tracer i dipole amplitude D_i = [2 + x_i (1 + a_i)] beta (Ellis-Baldwin), common direction. Unknowns (beta, a_N, a_Q) with x_i treated as
known-from-counts (NVSS x measured as proxy: 1.043; Quaia x NOT measured here -> declared grid). Poisson-only noise, no cross-covariance (distinct sources).
Reports: Fisher rank/nullity for (beta,a_N,a_Q) from (D_N,D_Q); joint sd(beta) vs single-tracer for fixed alpha; response ratio R=D_N/D_Q map over grids.
No dipole values read. Usage: python3 L2_joint_estimand.py --out out.json
"""
import argparse, json, numpy as np
SD_N, SD_Q = 3.56e-3, 1.99e-3          # full-sky Poisson sd per axis from the validated pilots (NVSS: sqrt(3/N) mock-validated; Quaia sqrt(3/N)); effective-footprint inflation not applied
def resp(x, a): return 2 + x * (1 + a)
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
    xN = 1.043; res = {"scope": "structural joint estimand; no dipole read", "sd_per_axis": {"NVSS": SD_N, "Quaia": SD_Q}, "x_NVSS_proxy": xN, "grids": {}}
    # 1) identifiability of (beta, aN, aQ) from (D_N, D_Q): Jacobian rank at sample points
    ranks = []
    for xQ in (1.0, 1.5, 2.0, 2.5):
        for aN in (0.5, 0.75, 1.0):
            for aQ in (0.5, 1.0, 1.5):
                beta = 1.23e-3
                J = np.array([[resp(xN, aN), beta * xN, 0.0], [resp(xQ, aQ), 0.0, beta * xQ]])
                s = np.linalg.svd(J, compute_uv=False); ranks.append(int((s > 1e-9 * s[0]).sum()))
    res["rank_beta_aN_aQ_from_DN_DQ"] = {"unique_ranks": sorted(set(ranks)), "unknowns": 3, "observables": 2, "nullity": 1}
    # 2) joint beta sd with alpha fixed on a grid (GLS, independent noise)
    out = {}
    for xQ in (1.0, 1.5, 2.0, 2.5):
        for aN in (0.5, 0.75, 1.0):
            for aQ in (0.5, 1.0, 1.5):
                rN, rQ = resp(xN, aN), resp(xQ, aQ); F = (rN / SD_N) ** 2 + (rQ / SD_Q) ** 2
                out[f"xQ{xQ}_aN{aN}_aQ{aQ}"] = {"R_N": rN, "R_Q": rQ, "sd_beta_joint": F ** -0.5, "sd_beta_NVSS": SD_N / rN, "sd_beta_Quaia": SD_Q / rQ,
                                                 "R_N_over_R_Q": rN / rQ}
    res["grid"] = out
    sj = [v["sd_beta_joint"] for v in out.values()]; rr = [v["R_N_over_R_Q"] for v in out.values()]
    res["summary"] = {"sd_beta_joint_range": [min(sj), max(sj)], "R_N_over_R_Q_range": [min(rr), max(rr)]}
    # 3) systematic-model-error: wrong alpha for NVSS shifts beta by response ratio (relative bias of beta-hat from alpha misassumption)
    res["alpha_misassumption_relative_beta_bias"] = {f"aN_true{t}_assumed{s}": resp(xN, t) / resp(xN, s) - 1 for t in (0.5, 1.0) for s in (0.5, 0.75, 1.0) if t != s}
    json.dump(res, open(a.out, "w"), indent=1, sort_keys=True); print(json.dumps({k: res[k] for k in ("rank_beta_aN_aQ_from_DN_DQ", "summary", "alpha_misassumption_relative_beta_bias")}, indent=1))
if __name__ == "__main__": main()
