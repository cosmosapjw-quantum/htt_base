"""L3 slice: structural identifiability of low-order proper-motion vector-field modes on the real Gaia CRF3 sky.

NO proper-motion VALUES are read (columns used: ra, dec, pmra_error, pmdec_error, pmra_pmdec_corr, phot_g_mean_mag).
Modes (closed-form real vector fields on the sphere, n = unit vector; tangential projection P = I - n n^T):
  E1(g):  v = P g                       3 params   (glide / acceleration-like, spheroidal l=1)
  B1(w):  v = w x n                     3 params   (rotation; cosmic vorticity OR ICRF frame spin: SAME field)
  E2(S):  v = P S n                     5 params   (spheroidal l=2, STF S: shear-like)
  B2(S'): v = n x (S' n)                5 params   (toroidal l=2, STF S')
E2/B2 chart: 5 Frobenius-orthonormal trace-free symmetric basis matrices (declared orthonormal chart).
Fisher F = sum_i J_i^T C_i^{-1} J_i with the per-source 2x2 proper-motion covariance C_i from the catalogue errors/correlation.
Units: mas/yr per unit mode amplitude. Usage: python3 L3_vsh_structural_identifiability.py --fits <gaia_crf3_astrometry_full.fits> --out result.json
"""
import argparse, json, math, time, warnings
import numpy as np
from astropy.io import fits
warnings.filterwarnings("ignore")

def stf_orthonormal():
    s2, s6 = math.sqrt(2), math.sqrt(6)
    B = [np.diag([1, -1, 0]) / s2, np.diag([1, 1, -2]) / s6]
    for (i, j) in ((0, 1), (0, 2), (1, 2)):
        M = np.zeros((3, 3)); M[i, j] = M[j, i] = 1 / s2; B.append(M)
    return B                                                       # tr(B_k B_l) = delta_kl

def design(ra, dec, basis_stf):
    al, de = np.deg2rad(ra), np.deg2rad(dec)
    n = np.stack([np.cos(de) * np.cos(al), np.cos(de) * np.sin(al), np.sin(de)], -1)
    ea = np.stack([-np.sin(al), np.cos(al), np.zeros_like(al)], -1)
    ed = np.stack([-np.cos(al) * np.sin(de), -np.sin(al) * np.sin(de), np.cos(de)], -1)
    N = len(ra); cols = {}
    def put(name, v):                                                  # (N,3) field -> 2N rows (alpha*, delta)
        cols[name] = np.concatenate([np.einsum("ij,ij->i", v, ea), np.einsum("ij,ij->i", v, ed)])
    unit = np.eye(3)
    for k in range(3):
        g = unit[k]; put(f"E1_{k}", g[None, :] - (n @ g)[:, None] * n)
    for k in range(3):
        w = unit[k]; put(f"B1_{k}", np.cross(w[None, :], n))
    for k, S in enumerate(basis_stf):
        Sn = n @ S.T; put(f"E2_{k}", Sn - np.einsum("ij,ij->i", n, Sn)[:, None] * n)
    for k, S in enumerate(basis_stf):
        put(f"B2_{k}", np.cross(n, n @ S.T))
    return cols, N

def fisher(cols, names, N, sa, sd, rho):
    J = np.column_stack([cols[k] for k in names])
    Ja, Jd = J[:N], J[N:]
    det = sa ** 2 * sd ** 2 * (1 - rho ** 2)
    Cia, Cid, Cx = sd ** 2 / det, sa ** 2 / det, -rho * sa * sd / det  # inverse covariance entries
    F = (Ja.T * Cia) @ Ja + (Jd.T * Cid) @ Jd + (Ja.T * Cx) @ Jd + (Jd.T * Cx) @ Ja
    return 0.5 * (F + F.T)

def analyse(cols, names, N, sa, sd, rho):
    F = fisher(cols, names, N, sa, sd, rho)
    w, V = np.linalg.eigh(F); w = w[::-1]; V = V[:, ::-1]
    rank = int((w > 1e-10 * w[0]).sum())
    dg = np.sqrt(np.diag(F)); Cn = F / np.outer(dg, dg)
    out = {"n_params": len(names), "rank_F_rel_tol_1e-10": rank, "nullity": len(names) - rank,
           "eigs_max_min_nonzero": [float(w[0]), float(w[rank - 1])], "cond_nonzero_block": float(w[0] / w[rank - 1])}
    if rank == len(names):
        Finv = np.linalg.inv(F); out["sd_per_param_masyr"] = {n: float(math.sqrt(Finv[i, i])) for i, n in enumerate(names)}
    groups = {g: [i for i, n in enumerate(names) if n.startswith(g)] for g in ("E1", "B1", "E2", "B2")}
    blocks = {}
    for x in groups:
        for y in groups:
            if x < y and groups[x] and groups[y]:
                blocks[f"{x}-{y}"] = float(np.abs(Cn[np.ix_(groups[x], groups[y])]).max())
    out["max_abs_normalised_cross_block_correlation"] = blocks
    return out, V

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fits", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); t0 = time.time()
    with fits.open(a.fits, memmap=True) as h:
        d = h[1].data
        ra = np.asarray(d["ra"], float); dec = np.asarray(d["dec"], float)
        sa = np.asarray(d["pmra_error"], float); sd = np.asarray(d["pmdec_error"], float)
        rho = np.asarray(d["pmra_pmdec_corr"], float); g = np.asarray(d["phot_g_mean_mag"], float)
    ok = np.isfinite(ra + dec + sa + sd + rho) & (sa > 0) & (sd > 0) & (np.abs(rho) < 0.999)
    res = {"scope": "STRUCTURAL identifiability only; no proper-motion values read", "n_rows": int(len(ra)), "n_used": int(ok.sum()),
           "units": "mas/yr per unit mode amplitude", "chart_E2_B2": "Frobenius-orthonormal STF basis (declared)", "samples": {}}
    full = ["E1_0", "E1_1", "E1_2", "B1_0", "B1_1", "B1_2"] + [f"E2_{k}" for k in range(5)] + [f"B2_{k}" for k in range(5)]
    for label, sel in (("all", ok), ("G<19", ok & (g < 19.0))):
        cols, N = design(ra[sel], dec[sel], stf_orthonormal())
        s_a, s_d, r = sa[sel], sd[sel], rho[sel]
        entry = {"n_sources": int(sel.sum()), "median_pm_error_masyr": [float(np.median(s_a)), float(np.median(s_d))]}
        entry["model_E1_B1_E2_B2_16"], _ = analyse(cols, full, N, s_a, s_d, r)
        cols2 = dict(cols)                                           # vorticity w AND ICRF frame spin eps: identical B1 field
        for k in range(3): cols2[f"B1spin_{k}"] = cols[f"B1_{k}"].copy()
        names19 = full + [f"B1spin_{k}" for k in range(3)]
        e19, V19 = analyse(cols2, names19, N, s_a, s_d, r)
        null = V19[:, -3:]
        e19["null_vectors_support_params"] = sorted({n for i, n in enumerate(names19) if np.abs(null[i]).max() > 1e-6})
        e19["null_space_confined_to_B1_and_B1spin"] = bool(max(np.abs(null[i]).max() for i, n in enumerate(names19) if n.startswith(("E", "B2"))) < 1e-8)
        entry["model_with_frame_spin_nuisance_19"] = e19
        entry["vorticity_identifiable_without_frame_spin_anchor"] = bool(e19["nullity"] == 0)
        res["samples"][label] = entry
        print(label, "done", round(time.time() - t0), "s", flush=True)
    res["elapsed_s"] = time.time() - t0; res["versions"] = {"numpy": np.__version__}
    json.dump(res, open(a.out, "w"), indent=1, sort_keys=True)

if __name__ == "__main__":
    main()
