"""L3 slice 3: Gaia scan-pattern template from the commanded scanning law, validated against the catalogue's own error ellipses.

Scan law (ESA, FullGaiaMissionScanningLaw.zip): 10 s samples, FOV1 and FOV2 pointings with position angle theta (0 = toward North,
90 = toward East).  Each transit measures along the direction u = (sin theta, cos theta) in the (east, north) = (alpha*, delta) basis.
Per HEALPix pixel p (nside 16) the information tensor is  M_p = < u u^T > over transits, so the predicted proper-motion covariance is
proportional to M_p^-1:   sigma_alpha*/sigma_delta = sqrt(<cos^2>/<sin^2>),   corr = -<sin cos>/sqrt(<sin^2><cos^2>).
Validation (no proper-motion VALUES read): per-pixel medians of pmra_error/pmdec_error and pmra_pmdec_corr from the CRF3 sample are
compared with the predictions.  Usage:
  python3 L3_scan_law_template.py --zip FullGaiaMissionScanningLaw.zip --fits gaia_crf3_astrometry_full.fits --out result.json
"""
import argparse, gzip, io, json, time, warnings, zipfile
import numpy as np, pandas as pd, healpy as hp
from astropy.io import fits
warnings.filterwarnings("ignore")
NS = 16

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--zip", required=True); ap.add_argument("--fits", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--maxrows", type=int, default=0); ap.add_argument("--jdmax", type=float, default=0.0)
    a = ap.parse_args(); t0 = time.time()
    npix = hp.nside2npix(NS); acc = {k: np.zeros(npix) for k in ("n", "ss", "cc", "sc")}; total = 0; tmin = np.inf; tmax = -np.inf
    z = zipfile.ZipFile(a.zip)
    with z.open("FullGaiaMissionScanningLaw/commanded_scan_law.csv.gz") as raw:
        txt = io.TextIOWrapper(gzip.GzipFile(fileobj=raw), encoding="utf-8")
        cols = ["jd_time", "ra_fov1", "dec_fov1", "scan_angle_fov1", "ra_fov2", "dec_fov2", "scan_angle_fov2"]
        for chunk in pd.read_csv(txt, comment="#", chunksize=2_000_000, usecols=cols):
            if a.jdmax > 0:
                chunk = chunk[chunk["jd_time"] <= a.jdmax]                  # e.g. Gaia DR3 end 2017-05-28 = 2704.0 (JD - 2455197.5)
                if len(chunk) == 0: break
            tmin = min(tmin, float(chunk["jd_time"].min())); tmax = max(tmax, float(chunk["jd_time"].max()))
            for f in ("fov1", "fov2"):
                ra = chunk[f"ra_{f}"].to_numpy(float); dec = chunk[f"dec_{f}"].to_numpy(float); th = np.deg2rad(chunk[f"scan_angle_{f}"].to_numpy(float))
                pix = hp.ang2pix(NS, np.deg2rad(90 - dec), np.deg2rad(ra)); s, c = np.sin(th), np.cos(th)
                acc["n"] += np.bincount(pix, minlength=npix); acc["ss"] += np.bincount(pix, s * s, npix)
                acc["cc"] += np.bincount(pix, c * c, npix); acc["sc"] += np.bincount(pix, s * c, npix)
            total += len(chunk)
            print("rows", total, round(time.time() - t0), "s", flush=True)
            if a.maxrows and total >= a.maxrows: break
    n = np.maximum(acc["n"], 1); ss, cc, sc = acc["ss"] / n, acc["cc"] / n, acc["sc"] / n
    ratio_pred = np.sqrt(cc / np.maximum(ss, 1e-12)); corr_pred = -sc / np.sqrt(np.maximum(ss * cc, 1e-12))
    with fits.open(a.fits, memmap=True) as h:
        d = h[1].data; ra = np.asarray(d["ra"], float); dec = np.asarray(d["dec"], float); sa = np.asarray(d["pmra_error"], float)
        sd = np.asarray(d["pmdec_error"], float); rho = np.asarray(d["pmra_pmdec_corr"], float)
    ok = np.isfinite(ra + dec + sa + sd + rho) & (sa > 0) & (sd > 0); pix = hp.ang2pix(NS, np.deg2rad(90 - dec[ok]), np.deg2rad(ra[ok]))
    rat = (sa / sd)[ok]; rh = rho[ok]
    def pix_median(v):
        o = np.argsort(pix, kind="stable"); ps = pix[o]; vs = v[o]; b = np.searchsorted(ps, np.arange(npix + 1)); out = np.full(npix, np.nan)
        for p in range(npix):
            if b[p + 1] - b[p] >= 20: out[p] = np.median(vs[b[p]:b[p + 1]])
        return out
    rat_med = pix_median(rat); rho_med = pix_median(rh); good = np.isfinite(rat_med) & np.isfinite(rho_med) & (acc["n"] > 100)
    def reg(x, y):
        return float(np.corrcoef(x, y)[0, 1]), float(np.polyfit(x, y, 1)[0])
    c_r, s_r = reg(ratio_pred[good], rat_med[good]); c_c, s_c = reg(corr_pred[good], rho_med[good])
    res = {"scope": "scan-pattern template + validation against catalogue error ellipses; no proper-motion values read", "scan_law_rows": int(total), "n_pixels_nside16": int(npix),
           "n_pixels_compared": int(good.sum()), "time_span_jd_minus_2455197.5": [tmin, tmax], "transits_per_pixel_median": float(np.median(acc["n"])),
           "ratio_sigma_alpha_over_sigma_delta": {"pearson_pred_vs_catalogue": c_r, "slope": s_r, "pred_range": [float(ratio_pred[good].min()), float(ratio_pred[good].max())],
                                                  "catalogue_median_range": [float(np.nanmin(rat_med[good])), float(np.nanmax(rat_med[good]))]},
           "correlation_pmra_pmdec": {"pearson_pred_vs_catalogue": c_c, "slope": s_c, "pred_range": [float(corr_pred[good].min()), float(corr_pred[good].max())],
                                      "catalogue_median_range": [float(np.nanmin(rho_med[good])), float(np.nanmax(rho_med[good]))]},
           "pixel_tensor_summary": {"mean_sin2": float(ss[good].mean()), "mean_cos2": float(cc[good].mean()), "max_abs_sincos": float(np.abs(sc[good]).max())},
           "elapsed_s": time.time() - t0, "versions": {"numpy": np.__version__, "pandas": pd.__version__, "healpy": hp.__version__}}
    json.dump(res, open(a.out, "w"), indent=1, sort_keys=True)
    np.savez_compressed(a.out.replace(".json", "_maps.npz"), n=acc["n"], ss=ss, cc=cc, sc=sc, ratio_pred=ratio_pred, corr_pred=corr_pred, ratio_cat=rat_med, corr_cat=rho_med)

if __name__ == "__main__":
    main()
