"""L6: local-boost vs global-tilt structural identifiability (collinear scalar-amplitude model; vector case multiplies ranks by 3).
Unknowns: beta (observer velocity wrt CMB rest frame), tau_k (matter-frame velocity wrt CMB frame in redshift shell k, i.e. global tilt), i_c (intrinsic CMB dipole),
alpha_k (spectral index), s_k (intrinsic/LSS count dipole in shell k).   Observables: CMB dipole d_c = beta + i_c ; CMB aberration/modulation a_c = beta ;
count dipole D_k = R_k(alpha_k)(beta - tau_k) + s_k with R_k = 2 + x_k(1+alpha_k).
Part A: Jacobian rank/nullity per scenario (exact structural).  Part B: marginal sd(tau) with DECLARED (not measured) nuisance priors and noise levels.
Usage: python3 L6_local_global_identifiability.py --out out.json
"""
import argparse, json, numpy as np
BETA = 1.23e-3; XK = {"NVSS": 1.043, "RACS": 0.948, "Quaia": 1.9}; AL0 = 0.75
DECL = {"prior_sd_alpha": 0.25, "prior_sd_s": 3e-4, "prior_sd_ic": 1e-4, "noise_count": 2.5e-3, "noise_cmb_dipole": 1e-5, "noise_cmb_aberration": 4e-4, "prior_sd_tau_shared": 1e-1}
def build(shells, aberration, tau_mode):
    """returns J (obs x unknown), names, noise sd vector"""
    names = ["beta", "i_c"] + [f"alpha_{k}" for k in shells] + [f"s_{k}" for k in shells]
    taus = ["tau"] if tau_mode == "shared" else [f"tau_{k}" for k in shells]
    names += taus; idx = {n: i for i, n in enumerate(names)}; rows = []; sd = []
    r = np.zeros(len(names)); r[idx["beta"]] = 1; r[idx["i_c"]] = 1; rows.append(r); sd.append(DECL["noise_cmb_dipole"])
    if aberration:
        r = np.zeros(len(names)); r[idx["beta"]] = 1; rows.append(r); sd.append(DECL["noise_cmb_aberration"])
    for k in shells:
        R = 2 + XK[k] * (1 + AL0); t = "tau" if tau_mode == "shared" else f"tau_{k}"; tau_val = 0.5 * BETA
        r = np.zeros(len(names)); r[idx["beta"]] = R; r[idx[t]] = -R; r[idx[f"alpha_{k}"]] = XK[k] * (BETA - tau_val); r[idx[f"s_{k}"]] = 1; rows.append(r); sd.append(DECL["noise_count"])
    return np.array(rows), names, np.array(sd)
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args(); out = {"declared_nuisance_and_noise_NOT_MEASURED": DECL, "scenarios": {}}
    for label, shells, ab, tm in (("S1_CMB+1count_sharedTau", ["NVSS"], False, "shared"), ("S2_CMB+aberration+1count_sharedTau", ["NVSS"], True, "shared"),
                                  ("S3_CMB+aberration+3count_sharedTau", ["NVSS", "RACS", "Quaia"], True, "shared"), ("S4_CMB+aberration+3count_perShellTau", ["NVSS", "RACS", "Quaia"], True, "per_shell")):
        J, names, sd = build(shells, ab, tm); s = np.linalg.svd(J, compute_uv=False); rank = int((s > 1e-9 * s[0]).sum())
        # Part B: Gaussian priors on nuisances (alpha,s,i_c) and weak prior on tau/beta; posterior sd of tau parameters
        pri = np.full(len(names), 1e3)
        for i, n in enumerate(names):
            if n.startswith("alpha"): pri[i] = DECL["prior_sd_alpha"]
            elif n.startswith("s_"): pri[i] = DECL["prior_sd_s"]
            elif n == "i_c": pri[i] = DECL["prior_sd_ic"]
            elif n.startswith("tau"): pri[i] = DECL["prior_sd_tau_shared"]
        F = (J.T / sd ** 2) @ J + np.diag(1 / pri ** 2); C = np.linalg.inv(F)
        out["scenarios"][label] = {"n_unknowns": len(names), "n_observables": J.shape[0], "jacobian_rank": rank, "nullity": len(names) - rank,
            "sd_tau_over_beta_cmb_with_declared_priors": {n: float(np.sqrt(C[i, i]) / BETA) for i, n in enumerate(names) if n.startswith("tau")}, "sd_beta_over_beta_cmb": float(np.sqrt(C[0, 0]) / BETA)}
    out["interpretation"] = ["Without independent anchors the unknown count exceeds the observable count in every scenario (nullity>0): a single dipole, or CMB+count dipoles, cannot separate observer boost from global tilt.",
        "Posterior sd(tau) is dominated by the declared nuisance priors (alpha, intrinsic dipole s); these magnitudes are declared, not measured."]
    json.dump(out, open(a.out, "w"), indent=1); print(json.dumps(out["scenarios"], indent=1))
if __name__ == "__main__": main()
