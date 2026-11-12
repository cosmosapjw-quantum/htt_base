"""L5 slice: structural identifiability of first-order directional-Hubble modes with the Pantheon+ sky, redshifts and FULL covariance.

NO distance moduli / magnitudes are read. Columns used: zHD, RA, DEC, IS_CALIBRATOR; the full STAT+SYS covariance.
First-order law (derived in L5_OPTICAL_JET_DERIVATION.md):  delta ln d_L = -[sigma_nn - A.n/c]/Hbar  (z-independent)
plus the observer/bulk-flow Doppler term ~ beta.n / z.  Distance-modulus response columns (amplitude units in brackets):
  M0         constant offset (M / H0 degeneracy)                       1
  Q_k        -(5/ln10) n^T S_k n          sigma_STF mode k / Hbar       Frobenius-orthonormal STF basis S_k (k=1..5)
  Adip_k     +(5/ln10) n_k                A_k/(c Hbar)                  (3)
  Dop_k      (5/ln10) n_k / z             observer boost beta_MO,k      (3)
  Flow_k     (5/ln10) n_k / z             local bulk flow (SAME shape as Dop) -> structural degeneracy expected (3)
Usage: python3 L5_pantheon_structural_identifiability.py --dat <Pantheon+SH0ES.dat> --cov <..._STAT+SYS.cov> --out result.json
"""
import argparse, json, math, time, warnings
import numpy as np
warnings.filterwarnings("ignore")
K5 = 5.0 / math.log(10.0)

def stf_orthonormal():
    s2, s6 = math.sqrt(2), math.sqrt(6)
    B = [np.diag([1, -1, 0]) / s2, np.diag([1, 1, -2]) / s6]
    for (i, j) in ((0, 1), (0, 2), (1, 2)):
        M = np.zeros((3, 3)); M[i, j] = M[j, i] = 1 / s2; B.append(M)
    return B

def analyse(J, names, Cinv):
    F = J.T @ Cinv @ J; F = 0.5 * (F + F.T)
    w, V = np.linalg.eigh(F); w = w[::-1]; V = V[:, ::-1]
    rank = int((w > 1e-10 * w[0]).sum())
    out = {"n_params": len(names), "rank": rank, "nullity": len(names) - rank, "cond_nonzero": float(w[0] / w[rank - 1])}
    if rank == len(names):
        Fi = np.linalg.inv(F); d = np.sqrt(np.diag(Fi))
        out["sd"] = {n: float(d[i]) for i, n in enumerate(names)}
        R = Fi / np.outer(d, d)
        grp = lambda p: [i for i, n in enumerate(names) if n.startswith(p)]
        cross = {}
        for a in ("M0", "Q", "Adip", "Dop"):
            for b in ("M0", "Q", "Adip", "Dop"):
                if a < b and grp(a) and grp(b):
                    cross[f"{a}-{b}"] = float(np.abs(R[np.ix_(grp(a), grp(b))]).max())
        out["max_abs_posterior_correlation_between_blocks"] = cross
    else:
        out["null_space_params"] = sorted({n for i, n in enumerate(names) if np.abs(V[i, rank:]).max() > 1e-6})
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dat", required=True); ap.add_argument("--cov", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); t0 = time.time()
    with open(a.dat) as f:
        head = f.readline().split(); rows = [l.split() for l in f if l.strip()]
    ix = {n: head.index(n) for n in ("zHD", "RA", "DEC", "IS_CALIBRATOR")}
    z = np.array([float(r[ix["zHD"]]) for r in rows]); ra = np.array([float(r[ix["RA"]]) for r in rows]); dec = np.array([float(r[ix["DEC"]]) for r in rows])
    cal = np.array([int(r[ix["IS_CALIBRATOR"]]) for r in rows])
    raw = np.loadtxt(a.cov); N = int(raw[0]); C = raw[1:].reshape(N, N)
    res = {"scope": "STRUCTURAL identifiability only; no distance moduli read", "n_rows_dat": len(rows), "cov_dimension_declared": N,
           "dimension_match": bool(N == len(rows)), "row_identity_check": "COUNT ONLY (dat rows == cov dimension); order/ID mapping not verifiable from the files",
           "cov_symmetry_max_abs": float(np.abs(C - C.T).max()), "cases": {}}
    C = 0.5 * (C + C.T)
    al, de = np.deg2rad(ra), np.deg2rad(dec)
    n = np.stack([np.cos(de) * np.cos(al), np.cos(de) * np.sin(al), np.sin(de)], -1)
    S = stf_orthonormal()
    for label, sel in (("hubble_flow_z>=0.023", (cal == 0) & (z >= 0.023)), ("hubble_flow_z>=0.010", (cal == 0) & (z >= 0.010)),
                       ("hubble_flow_z>=0.050", (cal == 0) & (z >= 0.050)), ("all_rows", np.ones(len(z), bool))):
        idx = np.where(sel)[0]; Cs = C[np.ix_(idx, idx)]
        try:
            np.linalg.cholesky(Cs); spd = True; Cinv = np.linalg.inv(Cs)
        except np.linalg.LinAlgError:
            spd = False; Cinv = np.linalg.pinv(Cs)
        nn, zz = n[idx], z[idx]
        cols = {"M0": np.ones(len(idx))}
        for k, Sk in enumerate(S): cols[f"Q_{k}"] = -K5 * np.einsum("ij,jk,ik->i", nn, Sk, nn)
        for k in range(3): cols[f"Adip_{k}"] = K5 * nn[:, k]
        for k in range(3): cols[f"Dop_{k}"] = K5 * nn[:, k] / zz
        names = list(cols); J = np.column_stack([cols[k] for k in names])
        entry = {"n_sn": int(len(idx)), "cov_spd": spd, "z_median": float(np.median(zz)),
                 "model_M0_Q5_Adip3_Dop3": analyse(J, names, Cinv)}
        names2 = names + [f"Dop_flow_{k}" for k in range(3)]
        J2 = np.column_stack([J] + [cols[f"Dop_{k}"] for k in range(3)])
        entry["model_with_bulk_flow_nuisance"] = analyse(J2, names2, Cinv)
        names3 = [n_ for n_ in names if not n_.startswith("Adip")]
        J3 = np.column_stack([cols[k] for k in names3])
        entry["model_without_acceleration_dipole"] = analyse(J3, names3, Cinv)
        res["cases"][label] = entry
        print(label, "done", round(time.time() - t0), "s", flush=True)
    res["elapsed_s"] = time.time() - t0; res["versions"] = {"numpy": np.__version__}
    json.dump(res, open(a.out, "w"), indent=1, sort_keys=True)

if __name__ == "__main__":
    main()
