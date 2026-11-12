"""L3 slice 2: leakage of l=3 vector-field modes into the l<=2 modes on the real Gaia CRF3 sky (structural; NO proper-motion values read).

Extends L3_vsh_structural_identifiability.py (imported from the same directory): adds E3 (v = P (T:nn)) and B3 (v = n x (T:nn)) with
7 Frobenius-orthonormal rank-3 STF tensors each.  Reports (i) full-rank check of the 30-mode model, (ii) formal sd of the 16 low-order
modes with l=3 fixed at zero versus marginalised, (iii) the largest normalised cross-correlation between l<=2 and l=3 blocks.
Usage: python3 L3_l3_leakage.py --fits <gaia_crf3_astrometry_full.fits> --out result.json
"""
import argparse, importlib.util, itertools, json, os, time, warnings
import numpy as np
from astropy.io import fits
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("l3s", os.path.join(HERE, "L3_vsh_structural_identifiability.py"))
l3s = importlib.util.module_from_spec(spec); spec.loader.exec_module(l3s)

def stf3_basis():
    """7 Frobenius-orthonormal fully symmetric trace-free rank-3 tensors (3x3x3)."""
    vecs = []
    for m in itertools.combinations_with_replacement(range(3), 3):
        T = np.zeros((3, 3, 3))
        for p in set(itertools.permutations(m)): T[p] = 1.0
        tr = np.einsum("ijj->i", T); d = np.eye(3)
        T = T - (np.einsum("ij,k->ijk", d, tr) + np.einsum("ik,j->ijk", d, tr) + np.einsum("jk,i->ijk", d, tr)) / 5.0   # remove traces
        vecs.append(T.reshape(-1))
    U, s, Vt = np.linalg.svd(np.array(vecs), full_matrices=False)
    assert (s > 1e-10 * s[0]).sum() == 7, s
    return [Vt[i].reshape(3, 3, 3) for i in range(7)]

def l3_columns(ra, dec, basis):
    al, de = np.deg2rad(ra), np.deg2rad(dec)
    n = np.stack([np.cos(de) * np.cos(al), np.cos(de) * np.sin(al), np.sin(de)], -1)
    ea = np.stack([-np.sin(al), np.cos(al), np.zeros_like(al)], -1)
    ed = np.stack([-np.cos(al) * np.sin(de), -np.sin(al) * np.sin(de), np.cos(de)], -1)
    cols = {}
    for k, T in enumerate(basis):
        g = np.einsum("ijk,nj,nk->ni", T, n, n)                     # T:nn
        gt = g - np.einsum("ni,ni->n", g, n)[:, None] * n           # tangential gradient (E3)
        cols[f"E3_{k}"] = np.concatenate([np.einsum("ij,ij->i", gt, ea), np.einsum("ij,ij->i", gt, ed)])
        b = np.cross(n, g)                                          # B3
        cols[f"B3_{k}"] = np.concatenate([np.einsum("ij,ij->i", b, ea), np.einsum("ij,ij->i", b, ed)])
    return cols

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fits", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); t0 = time.time()
    with fits.open(a.fits, memmap=True) as h:
        d = h[1].data; ra = np.asarray(d["ra"], float); dec = np.asarray(d["dec"], float); sa = np.asarray(d["pmra_error"], float)
        sd = np.asarray(d["pmdec_error"], float); rho = np.asarray(d["pmra_pmdec_corr"], float); g = np.asarray(d["phot_g_mean_mag"], float)
    ok = np.isfinite(ra + dec + sa + sd + rho) & (sa > 0) & (sd > 0) & (np.abs(rho) < 0.999)
    res = {"scope": "STRUCTURAL leakage of l=3 into l<=2; no proper-motion values read", "n_used": int(ok.sum()), "samples": {}}
    low = ["E1_0", "E1_1", "E1_2", "B1_0", "B1_1", "B1_2"] + [f"E2_{k}" for k in range(5)] + [f"B2_{k}" for k in range(5)]
    hi = [f"E3_{k}" for k in range(7)] + [f"B3_{k}" for k in range(7)]; basis3 = stf3_basis()
    for label, sel in (("all", ok), ("G<19", ok & (g < 19.0))):
        cols, N = l3s.design(ra[sel], dec[sel], l3s.stf_orthonormal()); cols.update(l3_columns(ra[sel], dec[sel], basis3))
        s_a, s_d, r = sa[sel], sd[sel], rho[sel]
        full = low + hi
        F = l3s.fisher(cols, full, N, s_a, s_d, r)
        w = np.linalg.eigvalsh(F)[::-1]; rank = int((w > 1e-10 * w[0]).sum())
        Fl = l3s.fisher(cols, low, N, s_a, s_d, r)
        sd_fixed = np.sqrt(np.diag(np.linalg.inv(Fl))); sd_marg = np.sqrt(np.diag(np.linalg.inv(F))[: len(low)])
        dg = np.sqrt(np.diag(F)); Cn = F / np.outer(dg, dg); X = np.abs(Cn[: len(low), len(low):])
        blocks = {}
        for gl in ("E1", "B1", "E2", "B2"):
            ids = [i for i, n_ in enumerate(low) if n_.startswith(gl)]
            for gh in ("E3", "B3"):
                jd = [j for j, n_ in enumerate(hi) if n_.startswith(gh)]
                blocks[f"{gl}-{gh}"] = float(X[np.ix_(ids, jd)].max())
        infl = sd_marg / sd_fixed
        res["samples"][label] = {"n_sources": int(sel.sum()), "n_params": len(full), "rank": rank, "cond": float(w[0] / w[rank - 1]),
            "max_abs_normalised_correlation_low_vs_l3": blocks,
            "sd_inflation_when_l3_marginalised": {"E1": infl[:3].tolist(), "B1": infl[3:6].tolist(), "E2": infl[6:11].tolist(), "B2": infl[11:16].tolist()},
            "sd_fixed_l3_masyr_max": float(sd_fixed.max()), "sd_marginalised_l3_masyr_max": float(sd_marg.max())}
        print(label, "done", round(time.time() - t0), "s", flush=True)
    res["elapsed_s"] = time.time() - t0; res["versions"] = {"numpy": np.__version__}
    json.dump(res, open(a.out, "w"), indent=1, sort_keys=True)

if __name__ == "__main__":
    main()
