"""L3 slice 4: scan-aware Fisher and scan-correlated spurious low-order mode response (structural; NO proper-motion values read).

Inputs: per-pixel (nside 16) scan information tensor M=<u u^T>, u=(sin th, cos th) in (east,north), from L3_scan_law_template.py (--jdmax DR3 window);
catalogue columns ra, dec, pmra_error, pmdec_error, pmra_pmdec_corr.
Covariances compared (same per-source determinant, so only the ellipse orientation/shape differs):
  CAT : catalogue 2x2 covariance.
  TMPL: det-matched scan-law ellipse  C ~ M^-1 (normalised to det C_cat).
Spurious response: systematic vector d_p = a_p * e_p per pixel, a_p ~ N(0,1) (unit amplitude, mas/yr), e_p = along-scan principal axis of M_p
(the direction of largest information) versus an isotropic-direction control; bias = F^-1 J^T C^-1 d; reported in units of the formal sd.
Usage: python3 L3_scan_aware_fisher.py --fits F --maps dr3_maps.npz --out out.json [--ndraw 200] [--seed 20261112]
"""
import argparse, importlib.util, json, os, time, warnings
import numpy as np, healpy as hp
from astropy.io import fits
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); NS = 16
spec = importlib.util.spec_from_file_location("l3s", os.path.join(HERE, "L3_vsh_structural_identifiability.py"))
l3s = importlib.util.module_from_spec(spec); spec.loader.exec_module(l3s)

def cov_from_tensor(ss, cc, sc, detc):
    det = np.maximum(ss * cc - sc ** 2, 1e-12)
    ia, id_, ix = cc / det, ss / det, -sc / det                       # M^-1 = [[cc,-sc],[-sc,ss]]/det  (alpha*, delta)
    s = np.sqrt(detc) / np.sqrt(np.maximum(ia * id_ - ix ** 2, 1e-30))   # det(s*M^-1)=detc
    return s * ia, s * id_, s * ix                                   # Caa, Cdd, Cad

def sa_sd_rho(Caa, Cdd, Cad):
    sa, sd = np.sqrt(Caa), np.sqrt(Cdd); return sa, sd, Cad / (sa * sd)

def main():
    ap = argparse.ArgumentParser()
    for k in ("--fits", "--maps", "--out"): ap.add_argument(k, required=True)
    ap.add_argument("--ndraw", type=int, default=200); ap.add_argument("--seed", type=int, default=20261112); a = ap.parse_args(); t0 = time.time()
    m = np.load(a.maps); ss, cc, sc, nn = m["ss"], m["cc"], m["sc"], m["n"]
    with fits.open(a.fits, memmap=True) as h:
        d = h[1].data; ra = np.asarray(d["ra"], float); dec = np.asarray(d["dec"], float)
        sa = np.asarray(d["pmra_error"], float); sd = np.asarray(d["pmdec_error"], float); rho = np.asarray(d["pmra_pmdec_corr"], float)
    pix_all = hp.ang2pix(NS, np.deg2rad(90 - dec), np.deg2rad(ra))
    ok = np.isfinite(ra + dec + sa + sd + rho) & (sa > 0) & (sd > 0) & (np.abs(rho) < 0.999) & (nn[pix_all] > 100)
    ra, dec, sa, sd, rho, pix = ra[ok], dec[ok], sa[ok], sd[ok], rho[ok], pix_all[ok]
    detc = sa ** 2 * sd ** 2 * (1 - rho ** 2)
    Ta, Td, Tr = sa_sd_rho(*cov_from_tensor(ss[pix], cc[pix], sc[pix], detc))
    cols, N = l3s.design(ra, dec, l3s.stf_orthonormal()); names = [f"{g}_{k}" for g, n in (("E1", 3), ("B1", 3), ("E2", 5), ("B2", 5)) for k in range(n)]
    res = {"scope": "scan-aware Fisher and scan-aligned spurious response; no proper-motion values read", "n_sources": int(ok.sum()), "n_modes": len(names),
           "template": "DR3-window (jd<=2704) commanded scan law, nside16, det-matched to catalogue", "mode_order": names}
    F = {}; Finv = {}
    for lab, (A, D, R) in (("CAT", (sa, sd, rho)), ("TMPL", (Ta, Td, Tr))):
        F[lab] = l3s.fisher(cols, names, N, A, D, R); w = np.linalg.eigvalsh(F[lab]); Finv[lab] = np.linalg.inv(F[lab])
        res[f"sd_{lab}_masyr"] = {n: float(np.sqrt(Finv[lab][i, i])) for i, n in enumerate(names)}; res[f"cond_{lab}"] = float(w[-1] / w[0])
    ratio = np.array([res["sd_TMPL_masyr"][n] / res["sd_CAT_masyr"][n] for n in names])
    res["sd_ratio_TMPL_over_CAT"] = {"min": float(ratio.min()), "max": float(ratio.max()), "by_group": {g: [float(r) for r, n in zip(ratio, names) if n.startswith(g)] for g in ("E1", "B1", "E2", "B2")}}
    # spurious response
    rng = np.random.default_rng(a.seed); J = np.column_stack([cols[k] for k in names]); npix = hp.nside2npix(NS)
    w_, v_ = np.linalg.eigh(np.stack([np.stack([ss, sc], -1), np.stack([sc, cc], -1)], -2))        # per-pixel M (east,north) eigen
    maj = v_[:, :, 1]                                                                              # eigenvector of largest information
    out = {}
    for lab in ("CAT", "TMPL"):
        A, D, R = (sa, sd, rho) if lab == "CAT" else (Ta, Td, Tr)
        det = A ** 2 * D ** 2 * (1 - R ** 2); Cia, Cid, Cx = D ** 2 / det, A ** 2 / det, -R * A * D / det
        Ja, Jd = J[:N], J[N:]; sd_formal = np.sqrt(np.diag(Finv[lab]))
        for kind in ("scan_aligned", "isotropic_control"):
            B = np.zeros((a.ndraw, len(names)))
            for t in range(a.ndraw):
                amp = rng.standard_normal(npix)
                if kind == "scan_aligned": ea, ed = maj[:, 0], maj[:, 1]
                else:
                    ang = rng.uniform(0, 2 * np.pi, npix); ea, ed = np.sin(ang), np.cos(ang)
                da = (amp * ea)[pix]; dd = (amp * ed)[pix]
                g = Ja.T @ (Cia * da + Cx * dd) + Jd.T @ (Cid * dd + Cx * da)
                B[t] = Finv[lab] @ g
            rms = np.sqrt((B ** 2).mean(0)) / sd_formal
            out[f"{lab}_{kind}"] = {"rms_bias_over_formal_sd": {g: float(np.mean([r for r, n in zip(rms, names) if n.startswith(g)])) for g in ("E1", "B1", "E2", "B2")}, "max": float(rms.max())}
    res["spurious_unit_amplitude_per_pixel"] = out; res["ndraw"] = a.ndraw; res["seed"] = a.seed; res["elapsed_s"] = time.time() - t0; res["versions"] = {"numpy": np.__version__, "healpy": hp.__version__}
    json.dump(res, open(a.out, "w"), indent=1, sort_keys=True); print(json.dumps({k: res[k] for k in ("sd_ratio_TMPL_over_CAT", "spurious_unit_amplitude_per_pixel")}, indent=1))

if __name__ == "__main__":
    main()
