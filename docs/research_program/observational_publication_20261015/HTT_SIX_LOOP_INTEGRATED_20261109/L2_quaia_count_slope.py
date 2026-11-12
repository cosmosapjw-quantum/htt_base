"""L2 slice 4: Quaia G<20 integral count slope x_Q = dlog10 N(<G)/dG / 0.4 from phot_g_mean_mag ONLY (no positions, no dipole).
Fit windows swept to expose incompleteness near the limit. Usage: python3 L2_quaia_count_slope.py --fits quaia_G20.0.fits --out out.json"""
import argparse, json, numpy as np
from astropy.io import fits
ap = argparse.ArgumentParser(); ap.add_argument("--fits", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
G = np.asarray(fits.open(a.fits, memmap=True)[1].data["phot_g_mean_mag"], float); G = G[np.isfinite(G)]; rng = np.random.default_rng(20261112)
def slope(g, lo, hi):
    m = np.linspace(lo, hi, 11); N = np.array([(g < x).sum() for x in m]); return np.polyfit(m, np.log10(N), 1)[0] / 0.4
res = {"scope": "magnitude counts only; no positions or dipole", "n": int(len(G)), "G_range": [float(G.min()), float(G.max())], "windows": {}}
for lo, hi in ((17.5, 18.5), (18.0, 19.0), (18.5, 19.5), (19.0, 19.8), (17.0, 19.0)):
    bs = [slope(rng.choice(G, len(G)), lo, hi) for _ in range(30)]; res["windows"][f"{lo}-{hi}"] = {"x": slope(G, lo, hi), "boot_sd": float(np.std(bs))}
json.dump(res, open(a.out, "w"), indent=1); print(json.dumps(res, indent=1))
