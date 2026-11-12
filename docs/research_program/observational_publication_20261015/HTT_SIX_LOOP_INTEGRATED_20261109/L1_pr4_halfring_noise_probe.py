"""L1 PR4/NPIPE half-ring noise probe (data-driven, NOISE ONLY; not a null for signal).

D = (ringhalf-1 - ringhalf-2)/2 of the NPIPE R4.00 HFI frequency map contains instrument noise but no sky signal.
The same operator as the PR3 pilot (nside 2048 -> 16 mean degrade, PR3 common T mask >=90% unmasked children,
monopole+dipole nuisance, OLS on 5 STF Bianchi-I basis maps) is applied to D at 100/143/217 GHz.
One realisation per frequency => no distribution; only (i) a white-noise expectation check and (ii) a magnitude
comparison with the PR3 FFP10 SMICA noise-only scatter are possible.
Matched PR4 simulations are NOT available (NERSC account), so no PR4 null/coverage is formed here.
Usage: python3 L1_pr4_halfring_noise_probe.py --raw <workdir/raw> --out result.json
"""
import argparse, json, math, time, warnings
import numpy as np, healpy as hp
from astropy.io import fits
warnings.filterwarnings("ignore")

NS_OUT, NS_TPL, T_BAR = 16, 128, 2.7255
G = np.array([[2, 1, 0, 0, 0], [1, 2, 0, 0, 0], [0, 0, 2, 0, 0], [0, 0, 0, 2, 0], [0, 0, 0, 0, 2]], float)

def gram(b): return float(np.sqrt(b @ G @ b))
def stf(b):
    a, c, d, e, f = b
    return np.array([[a, d, e], [d, c, f], [e, f, -a - c]], float)
def nmean(m, nin, nout): return m.reshape(-1, (nin // nout) ** 2).mean(1)
def ring16(m): return hp.reorder(m, n2r=True)

def read_I_nested(path):
    with fits.open(path, memmap=True) as h:
        hd = h[1].header
        assert hd["ORDERING"] == "NESTED" and hd["NSIDE"] == 2048, (hd["ORDERING"], hd["NSIDE"])
        assert str(hd["TUNIT1"]).strip() == "K_CMB", hd["TUNIT1"]
        return np.asarray(h[1].data["I_STOKES"], dtype=np.float64).reshape(-1), hd.get("PROCVER")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--raw", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); t0 = time.time(); raw = a.raw.rstrip("/")
    with fits.open(f"{raw}/planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits", memmap=True) as h:
        mk = np.asarray(h[1].data["TMASK"], dtype=np.float64).reshape(-1)
    keep = ring16(nmean(mk, 2048, NS_OUT)) >= 0.9
    v = np.stack(hp.pix2vec(NS_TPL, np.arange(hp.nside2npix(NS_TPL)), nest=True), -1)
    X = np.array([ring16(nmean(np.einsum("pi,ij,pj->p", v, stf(np.eye(5)[k]), v), NS_TPL, NS_OUT)) for k in range(5)])
    vv = np.stack(hp.pix2vec(NS_OUT, np.arange(hp.nside2npix(NS_OUT))), -1)
    N = np.vstack([np.ones(len(vv)), vv.T])
    Mfull = np.vstack([X, N]).T
    res = {"scope": "NOISE-ONLY data-driven probe on real PR4 half-ring difference; one realisation per frequency; not a null",
           "fsky_kept": float(keep.mean()),
           "mask_note": "PR3 common Int mask applied to PR4 maps (same operator as PR3 lane); not the PR4/Hillipop mask", "frequencies": {}}
    for g in (100, 143, 217):
        base = f"{raw}/planck_npipe_pr4/frequency_maps/Single-frequency/HFI_SkyMap_{g}_2048_R4.00_full-ringhalf-"
        p1, pv = read_I_nested(base + "1.fits")
        p2, _ = read_I_nested(base + "2.fits")
        bad = (p1 < -1e20) | (p2 < -1e20)                                # BAD_DATA = -1.6375e30
        D = 0.5 * (p1 - p2); D[bad] = np.nan
        dm = np.nanmean(D.reshape(-1, (2048 // NS_OUT) ** 2), axis=1)    # mean of valid children, NESTED
        d16 = ring16(dm)
        ok = keep & np.isfinite(d16)
        M = Mfull[ok]
        c = np.linalg.pinv(M) @ d16[ok]; b = c[:5] / T_BAR
        resid = d16[ok] - M @ c
        s2 = float(resid @ resid / (ok.sum() - 9))                      # pixel variance (K^2), white assumption
        cov_w = s2 * np.linalg.inv(M.T @ M)[:5, :5] / T_BAR ** 2
        res["frequencies"][str(g)] = {"procver": pv, "frac_bad_pixels_nside2048": float(bad.mean()), "n_pix_used_nside16": int(ok.sum()),
            "pixel_rms_uK_nside16": math.sqrt(s2) * 1e6, "b_hat": b.tolist(), "b_hat_gram_norm": gram(b),
            "white_noise_sd_per_component": np.sqrt(np.diag(cov_w)).tolist(),
            "chi2_5dof_under_white_assumption": float(b @ np.linalg.solve(cov_w, b))}
        print(f"{g} GHz done t={time.time()-t0:.0f}s", flush=True)
    res["elapsed_s"] = time.time() - t0; res["versions"] = {"numpy": np.__version__, "healpy": hp.__version__}
    json.dump(res, open(a.out, "w"), indent=1, sort_keys=True)

if __name__ == "__main__":
    main()
