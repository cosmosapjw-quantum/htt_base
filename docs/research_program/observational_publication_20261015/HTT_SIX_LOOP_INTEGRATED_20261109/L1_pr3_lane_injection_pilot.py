"""L1 PR3-local control lane: masked-sky injection/recovery PILOT (SYNTHETIC; no observed map used).

Data: Planck PR3 FFP10 SMICA CMB + noise simulations (same release as the PR3 SMICA map/mask),
      PR3 common intensity mask. No observed SMICA map is read.
Operator R: nside-2048 -> nside-16 mean-degrade, PR3 common T mask (pixels with >=90% unmasked children),
            monopole+dipole fitted as nuisance, ordinary least squares on 5 STF Bianchi-I basis maps.
Estimator: linear template regression (first order in B*); injection uses the EXACT nonlinear map.
Not done: beam/pixel window, foreground model, covariance-weighted (full Sigma_d) likelihood, polarization.
Usage: python3 L1_pr3_lane_injection_pilot.py --raw <workdir/raw> --n 24 --out result.json
"""
import argparse, json, math, time, warnings
import numpy as np, healpy as hp
from astropy.io import fits
from scipy.linalg import expm
warnings.filterwarnings("ignore")

NS_OUT, NS_TPL, T_BAR = 16, 128, 2.7255
G_STF5 = np.array([[2, 1, 0, 0, 0], [1, 2, 0, 0, 0], [0, 0, 2, 0, 0], [0, 0, 0, 2, 0], [0, 0, 0, 0, 2]], float)

def gram_norm(b):
    return float(np.sqrt(b @ G_STF5 @ b))

def stf_matrix(b):                      # (Bxx,Byy,Bxy,Bxz,Byz) -> 3x3 trace-free
    a, c, d, e, f = b
    return np.array([[a, d, e], [d, c, f], [e, f, -a - c]], float)

def nested_mean(m_nest, ns_in, ns_out):  # NESTED children are contiguous
    k = (ns_in // ns_out) ** 2
    return m_nest.reshape(-1, k).mean(1)

def to_ring16(m_nest16):
    return hp.reorder(m_nest16, n2r=True)

def template_maps(b):                    # exact nonlinear map minus 1, at nside 16 RING
    v = np.stack(hp.pix2vec(NS_TPL, np.arange(hp.nside2npix(NS_TPL)), nest=True), -1)
    E = expm(-2.0 * stf_matrix(b))
    t = np.einsum("pi,ij,pj->p", v, E, v) ** -0.5 - 1.0
    return to_ring16(nested_mean(t, NS_TPL, NS_OUT))

def basis_maps():
    v = np.stack(hp.pix2vec(NS_TPL, np.arange(hp.nside2npix(NS_TPL)), nest=True), -1)
    out = []
    for k in range(5):
        e = np.zeros(5); e[k] = 1.0
        out.append(to_ring16(nested_mean(np.einsum("pi,ij,pj->p", v, stf_matrix(e), v), NS_TPL, NS_OUT)))
    return np.array(out)

def nuisance_maps():
    v = np.stack(hp.pix2vec(NS_OUT, np.arange(hp.nside2npix(NS_OUT))), -1)   # RING, nside 16 centres (nuisance only)
    return np.vstack([np.ones(len(v)), v.T])

def read_I_ring(path):
    with fits.open(path, memmap=True) as h:
        return np.asarray(h[1].data["INTENSITY"], dtype=np.float64).reshape(-1)  # K_CMB, RING

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--raw", required=True); ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--out", required=True); a = ap.parse_args(); t0 = time.time()
    raw = a.raw.rstrip("/")
    with fits.open(f"{raw}/planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits", memmap=True) as h:
        mk = np.asarray(h[1].data["TMASK"], dtype=np.float64).reshape(-1)          # NESTED, Galactic
    frac = nested_mean(mk, 2048, NS_OUT)
    keep = to_ring16(frac) >= 0.9
    X = basis_maps(); N = nuisance_maps()
    M = np.vstack([X, N]).T[keep]                                                    # npix_keep x 9
    pinv = np.linalg.pinv(M)
    fsky = float(keep.mean())
    def fit(d_K):                                                                     # d in K -> b_hat (dimensionless)
        c = pinv @ d_K[keep]
        return c[:5] / T_BAR
    # null ensemble: cmb_i + noise_i (same release, index-paired)
    bh = []
    for i in range(a.n):
        c = read_I_ring(f"{raw}/planck_ffp10/smica/cmb_mc/dx12_v3_smica_cmb_mc_{i:05d}_raw.fits")
        n = read_I_ring(f"{raw}/planck_ffp10/smica/noise_mc/dx12_v3_smica_noise_mc_{i:05d}_raw.fits")
        d = hp.ud_grade(c + n, NS_OUT, order_in="RING", order_out="RING")
        bh.append(fit(d)); print(f"sim {i} done t={time.time()-t0:.0f}s", flush=True)
    bh = np.array(bh)
    mu, sd = bh.mean(0), bh.std(0, ddof=1)
    cov = np.cov(bh.T)
    res = {"scope": "SYNTHETIC pilot on PR3 FFP10 SMICA simulations; no observed map", "n_pairs": a.n, "nside_out": NS_OUT,
           "mask": "PR3 common Int TMASK; kept pixels with >=0.9 unmasked children", "fsky_kept": fsky,
           "sim_frame_assumption": "FFP10 files carry no COORDSYS; assumed Galactic like the PR3 maps/mask",
           "null_b_hat_mean_over_sims": mu.tolist(), "null_b_hat_sd_over_sims": sd.tolist(),
           "null_mean_over_sd_x_sqrt_n": (mu / sd * math.sqrt(a.n)).tolist(),
           "null_b_hat_gram_norm_rms": float(np.sqrt(np.mean([gram_norm(x) ** 2 for x in bh]))),
           "gram_sd_scale_sqrt_trace_G_cov": float(np.sqrt(np.trace(G_STF5 @ cov)))}
    sigma_gram = res["gram_sd_scale_sqrt_trace_G_cov"]
    # injection/recovery: exact nonlinear map, then linear-template recovery (no noise: response only)
    rng = np.random.default_rng(20261110)
    inj = []
    for label, target in (("5sigma_small", 5 * sigma_gram), ("1e-3_nonlinear_stress", 1e-3), ("1e-2_nonlinear_stress", 1e-2)):
        u = rng.normal(size=5); u /= math.sqrt(u @ G_STF5 @ u)        # Gram-unit direction
        b_true = u * target
        dmap = T_BAR * template_maps(b_true)
        b_rec = fit(dmap)
        err = b_rec - b_true
        inj.append({"label": label, "b_true_gram_norm": gram_norm(b_true), "b_rec_gram_norm": gram_norm(b_rec),
                    "recovery_error_gram_norm": gram_norm(err), "relative_error": gram_norm(err) / gram_norm(b_true),
                    "error_over_null_sigma_gram": gram_norm(err) / sigma_gram})
    res["injection_recovery_no_noise"] = inj
    # full-sky nonlinear leakage reference (no mask) for the same large amplitude
    Mf = np.vstack([X, N]).T; pf = np.linalg.pinv(Mf)
    b_true = rng.normal(size=5); b_true /= math.sqrt(b_true @ G_STF5 @ b_true); b_true *= 1e-2
    dmap = T_BAR * template_maps(b_true); b_rec = (pf @ dmap)[:5] / T_BAR
    res["fullsky_reference_1e-2"] = {"relative_error": gram_norm(b_rec - b_true) / gram_norm(b_true)}
    res["elapsed_s"] = time.time() - t0
    res["versions"] = {"numpy": np.__version__, "healpy": hp.__version__}
    json.dump(res, open(a.out, "w"), indent=1, sort_keys=True)

if __name__ == "__main__":
    main()
