"""R108 gaia lane: per-HEALPix scan geometry of the Gaia EDR3 commanded scanning law.

Purpose
  Streams CommandedScanLaw_001.csv.gz (Gaia EDR3 auxiliary data; 10 s samples of the two field-of-view
  centres) and, over the EDR3 interval, accumulates for every HEALPix pixel (NSIDE 32 and 64, RING):
  the number of FOV-centre samples, the number of scan passes (runs of consecutive samples of one FOV
  inside the pixel), the scan-angle moments <cos 2psi>, <sin 2psi>, and the 5x5 along-scan design
  information N = sum_k a_k a_k^T with a_k = (u_E, u_N, p_k, tau_k u_E, tau_k u_N): u = along-scan unit
  vector in the local (East, North) basis, p_k the along-scan parallax factor and tau_k the time from
  J2016.0 in years. The PM block of N^{-1} is the scan-law shape of the proper-motion covariance
  (equal along-scan weights per sample; across-scan information ignored).
  It also writes, per FOV and time ordered, the sample pixel (NSIDE 64) and a_k for the scan-law
  systematic mocks of scripts/r108/gaia_scan_null.py.
Checks
  * MD5 of the CSV against _MD5SUM.txt (D09 receipt) and SHA-256 recorded.
  * Scan-angle convention: the position angle (North through East) of the motion of each FOV centre
    between consecutive 10 s samples is compared with scan_angle (mod 180 deg); the script uses
    u = (sin psi, cos psi) only if that agreement holds for > 99% of the sample pairs, the mirrored
    convention only if it holds for that one, and fails closed otherwise.
  * Time columns bjd_fov1/2 are read as days since J2010.0 (JD 2455197.5, TCB); rows outside the EDR3
    interval 2014-07-25T10:30 to 2017-05-28T08:46 (Gaia Collaboration, Brown et al. 2021, A&A 649, A1,
    Sect. 1) are counted and excluded.
Assumptions (stated in the output): commanded = realised attitude (no dead time, no data gaps of the
  real EDR3 observations), observer at the Earth barycentric position (Gaia at L2 is ~1% further out),
  pixel-level aggregation (a source sees the passes of its pixel), equal along-scan weight per sample.
Inputs: CommandedScanLaw_001.csv.gz (569,780,480 bytes, MD5 82d24407396f6008a9d72608839533a8,
  SHA-256 c0c55b1dad49a19b182955ade5693c7c74d8c313725f6679f48a3f6bfe157bf4).
Units: angles deg in, rad internally; tau years; parallax factor AU; N in those units.
Usage: python -m scripts.r108.gaia_scanlaw --csv <path> --md5sum <path> --out-dir <downloads dir>
       --summary <results json>
Deterministic (no random numbers).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time

import healpy as hp
import numpy as np

from scripts.r108.common import git_state, maxrss_mb, sha256_file, write_json

CSV_SHA256 = "c0c55b1dad49a19b182955ade5693c7c74d8c313725f6679f48a3f6bfe157bf4"
CSV_MD5 = "82d24407396f6008a9d72608839533a8"
J2010_JD = 2455197.5
J2016_DAYS = 2191.5  # J2016.0 = JD 2457389.0
EDR3_START = 2456863.9375 - J2010_JD  # 2014-07-25T10:30 UTC
EDR3_END = 2457901.8652778 - J2010_JD  # 2017-05-28T08:46 UTC
NSIDES = (32, 64)
MOCK_NSIDE = 64
SAMPLE_NS = 10_000_000_000  # 10 s in ns of OBMT
STEP_TOL_NS = 10_000_000  # consecutive samples differ from 10 s by ~1e2 ns; 10 ms tolerance


def is_step(d_obmt):
    """True where two time-ordered samples are consecutive 10 s samples of one stream."""
    return np.abs(np.asarray(d_obmt) - SAMPLE_NS) < STEP_TOL_NS
COLS = ["obmt_time", "bjd_fov1", "bjd_fov2", "ra_fov1", "dec_fov1", "scan_angle_fov1", "ra_fov2", "dec_fov2",
        "scan_angle_fov2"]
IU = np.triu_indices(5)


def position_angle(ra1, dec1, ra2, dec2):
    """Position angle (rad, North through East) at point 1 of the great-circle direction to point 2."""
    dra = ra2 - ra1
    return np.arctan2(np.sin(dra) * np.cos(dec2),
                      np.cos(dec1) * np.sin(dec2) - np.sin(dec1) * np.cos(dec2) * np.cos(dra))


def wrap180(x_deg):
    """Difference folded to [-90, 90) degrees (axial, mod 180)."""
    return (np.asarray(x_deg) + 90.0) % 180.0 - 90.0


def design_rows(ra, dec, psi, tau, bary, mirrored=False):
    """a_k = (u_E, u_N, p, tau u_E, tau u_N); ra/dec/psi rad, tau yr, bary [n,3] AU."""
    ue = -np.sin(psi) if mirrored else np.sin(psi)
    un = np.cos(psi)
    sa, ca, sd, cd = np.sin(ra), np.cos(ra), np.sin(dec), np.cos(dec)
    east = np.column_stack((-sa, ca, np.zeros_like(ra)))
    north = np.column_stack((-sd * ca, -sd * sa, cd))
    p = -(ue * np.einsum("ij,ij->i", east, bary) + un * np.einsum("ij,ij->i", north, bary))
    return np.column_stack((ue, un, p, tau * ue, tau * un))


def earth_barycentre_interpolator(t_min, t_max):
    """Earth barycentric position (AU, ICRS) on an hourly TCB grid, linearly interpolated."""
    from astropy.coordinates import get_body_barycentric
    from astropy.time import Time

    grid = np.arange(t_min - 1.0, t_max + 1.0, 1.0 / 24.0)
    pos = get_body_barycentric("earth", Time(J2010_JD + grid, format="jd", scale="tcb")).xyz.to_value("AU").T

    def interp(t):
        return np.column_stack([np.interp(t, grid, pos[:, i]) for i in range(3)])

    return interp


def accumulate(nside, pix, a, c2, s2):
    npix = hp.nside2npix(nside)
    out = {"n": np.bincount(pix, minlength=npix).astype(np.int64),
           "cos2": np.bincount(pix, weights=c2, minlength=npix), "sin2": np.bincount(pix, weights=s2, minlength=npix),
           "N": np.zeros((npix, 15))}
    for m, (i, j) in enumerate(zip(*IU)):
        out["N"][:, m] = np.bincount(pix, weights=a[:, i] * a[:, j], minlength=npix)
    return out


def unpack(Nflat):
    N = np.zeros(Nflat.shape[:-1] + (5, 5))
    N[..., IU[0], IU[1]] = Nflat
    N[..., IU[1], IU[0]] = Nflat
    return N


def pm_shape(Nflat):
    """PM block of N^{-1} per pixel, condition numbers; NaN where N is singular."""
    N = unpack(Nflat)
    good = np.linalg.matrix_rank(N) == 5 if len(N) else np.zeros(0, bool)
    cov = np.full((len(N), 2, 2), np.nan)
    cond = np.full(len(N), np.inf)
    if good.any():
        inv = np.linalg.inv(N[good])
        cov[good] = inv[:, 3:5, 3:5]
        cond[good] = np.linalg.cond(N[good])
    return cov, cond


def count_passes(pix_sorted, obmt_sorted):
    """Runs of consecutive (10 s) samples inside the same pixel, per pixel."""
    new = np.ones(len(pix_sorted), bool)
    new[1:] = (pix_sorted[1:] != pix_sorted[:-1]) | ~is_step(np.diff(obmt_sorted))
    return np.bincount(pix_sorted[new], minlength=int(pix_sorted.max()) + 1 if len(pix_sorted) else 0)


def run(csv, md5sum, out_dir, summary_path, chunksize=1_000_000):
    import pandas as pd

    t0 = time.monotonic()
    md5_line = Path(md5sum).read_text().split()
    dig_sha, dig_md5 = hashlib.sha256(), hashlib.md5()
    with open(csv, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 22), b""):
            dig_sha.update(block)
            dig_md5.update(block)
    ident = {"sha256": dig_sha.hexdigest(), "md5": dig_md5.hexdigest(), "md5sum_file": md5_line,
             "md5_matches_md5sum": dig_md5.hexdigest() == md5_line[0], "sha256_matches_pinned": dig_sha.hexdigest() == CSV_SHA256}
    if not (ident["md5_matches_md5sum"] and ident["sha256_matches_pinned"]):
        raise ValueError(f"scan-law identity mismatch: {ident}")
    # Pass 1: read the needed columns into compact arrays.
    parts = {k: [] for k in COLS}
    nrows = 0
    with gzip.open(csv, "rt") as fh:
        for ch in pd.read_csv(fh, usecols=COLS, chunksize=chunksize,
                              dtype={c: (np.int64 if c == "obmt_time" else np.float64) for c in COLS}):
            nrows += len(ch)
            for k in COLS:
                parts[k].append(ch[k].to_numpy())
    data = {k: np.concatenate(v) for k, v in parts.items()}
    del parts
    t_all = np.concatenate((data["bjd_fov1"], data["bjd_fov2"]))
    info = {"rows": nrows, "bjd_min_days_since_J2010": float(t_all.min()), "bjd_max_days_since_J2010": float(t_all.max()),
            "obmt_unique": int(len(np.unique(data["obmt_time"]))), "read_s": time.monotonic() - t0}
    earth = earth_barycentre_interpolator(t_all.min(), t_all.max())
    del t_all
    acc = {ns: None for ns in NSIDES}
    conv = {}
    mock = {}
    excluded = {}
    for fov in (1, 2):
        obmt = data["obmt_time"]
        t = data[f"bjd_fov{fov}"]
        ra = np.deg2rad(data[f"ra_fov{fov}"])
        dec = np.deg2rad(data[f"dec_fov{fov}"])
        psi = np.deg2rad(data[f"scan_angle_fov{fov}"])
        inside = (t >= EDR3_START) & (t <= EDR3_END)
        excluded[f"fov{fov}"] = int((~inside).sum())
        order = np.argsort(obmt[inside], kind="stable")
        obmt, t, ra, dec, psi = (x[inside][order] for x in (obmt, t, ra, dec, psi))
        # Convention check on consecutive 10 s pairs.
        step = is_step(np.diff(obmt))
        pa = np.rad2deg(position_angle(ra[:-1][step], dec[:-1][step], ra[1:][step], dec[1:][step]))
        d_std = wrap180(pa - np.rad2deg(psi[:-1][step]))
        d_mir = wrap180(-pa - np.rad2deg(psi[:-1][step]))
        conv[f"fov{fov}"] = {"pairs": int(step.sum()), "samples": int(len(obmt)),
                             "obmt_step_ns_q01_q50_q99": np.quantile(np.diff(obmt), [.01, .5, .99]).tolist(), "frac_abs_diff_lt_1deg_standard": float(np.mean(np.abs(d_std) < 1)),
                             "frac_abs_diff_lt_1deg_mirrored": float(np.mean(np.abs(d_mir) < 1)),
                             "median_abs_diff_standard_deg": float(np.median(np.abs(d_std))),
                             "p99_abs_diff_standard_deg": float(np.quantile(np.abs(d_std), .99)),
                             "frac_motion_pa_equals_scan_angle_mod360_within_1deg": float(np.mean(np.abs(
                                 (pa - np.rad2deg(psi[:-1][step]) + 180) % 360 - 180) < 1))}
        if conv[f"fov{fov}"]["frac_abs_diff_lt_1deg_standard"] > .99:
            mirrored = False
        elif conv[f"fov{fov}"]["frac_abs_diff_lt_1deg_mirrored"] > .99:
            mirrored = True
        else:
            raise ArithmeticError(f"scan-angle convention ambiguous: {conv}")
        conv[f"fov{fov}"]["convention_used"] = "mirrored u=(-sin psi, cos psi)" if mirrored else "u=(sin psi, cos psi)"
        tau = (t - J2016_DAYS) / 365.25
        a = design_rows(ra, dec, psi, tau, earth(t), mirrored)
        # moments of the along-scan axis angle; the mirrored convention flips the sign of sin 2psi
        c2, s2 = np.cos(2 * psi), np.sin(2 * psi) * (-1.0 if mirrored else 1.0)
        for ns in NSIDES:
            pix = hp.ang2pix(ns, np.pi / 2 - dec, ra)
            r = accumulate(ns, pix, a, c2, s2)
            r["passes"] = count_passes(pix, obmt)
            r["passes"] = np.pad(r["passes"], (0, hp.nside2npix(ns) - len(r["passes"])))
            if acc[ns] is None:
                acc[ns] = r
            else:
                for k in r:
                    acc[ns][k] = acc[ns][k] + r[k]
            if ns == MOCK_NSIDE:
                gap = np.ones(len(obmt), bool)
                gap[1:] = ~is_step(np.diff(obmt))
                mock[f"fov{fov}"] = {"pix": pix.astype(np.int32), "a": a.astype(np.float32), "segment_start": gap}
        del obmt, t, ra, dec, psi, a
    del data
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=False)
    maps_path = out_dir / "scanlaw_pixel_statistics.npz"
    arrays = {}
    summ = {}
    for ns in NSIDES:
        r = acc[ns]
        cov, cond = pm_shape(r["N"])
        n = np.maximum(r["n"], 1)
        aniso = np.hypot(r["cos2"], r["sin2"]) / n
        rho = cov[:, 0, 1] / np.sqrt(cov[:, 0, 0] * cov[:, 1, 1])
        ratio = np.sqrt(cov[:, 0, 0] / cov[:, 1, 1])
        arrays.update({f"n{ns}": r["n"], f"passes{ns}": r["passes"], f"cos2_{ns}": r["cos2"], f"sin2_{ns}": r["sin2"],
                       f"N{ns}": r["N"], f"pmcov_shape{ns}": cov, f"cond{ns}": cond})
        fin = np.isfinite(rho)
        summ[f"nside{ns}"] = {
            "pixels": int(len(r["n"])), "pixels_without_samples": int((r["n"] == 0).sum()),
            "pixels_singular_N": int((~fin).sum()),
            "samples_per_pixel_q01_q50_q99": np.quantile(r["n"], [.01, .5, .99]).tolist(),
            "passes_per_pixel_q01_q50_q99": np.quantile(r["passes"], [.01, .5, .99]).tolist(),
            "scan_anisotropy_abs_mean_exp2ipsi_q05_q50_q95": np.quantile(aniso[r["n"] > 0], [.05, .5, .95]).tolist(),
            "predicted_pm_corr_q05_q50_q95": np.quantile(rho[fin], [.05, .5, .95]).tolist(),
            "predicted_sigma_ra_over_sigma_dec_q05_q50_q95": np.quantile(ratio[fin], [.05, .5, .95]).tolist(),
            "log10_condition_number_q50_q99_max": np.quantile(np.log10(cond[np.isfinite(cond)]), [.5, .99, 1]).tolist()}
    np.savez_compressed(maps_path, **arrays)
    mock_files = {}
    for fov, d in mock.items():
        for k, v in d.items():
            pth = out_dir / f"mock_{fov}_{k}.npy"
            np.save(pth, v)
            mock_files[pth.name] = sha256_file(pth)
    res = {"schema": "htt.r108.gaia_scanlaw/1", "input": {"csv": str(csv), **ident},
           "edr3_interval_days_since_J2010": [EDR3_START, EDR3_END],
           "edr3_interval_locator": "Gaia Collaboration, Brown et al. 2021, A&A 649, A1, Sect. 1 (2014-07-25T10:30 to 2017-05-28T08:46 UTC)",
           "time_column_convention": "bjd_fov1/2 read as days since J2010.0 (JD 2455197.5); tau = (bjd - 2191.5)/365.25 yr",
           "rows": info, "samples_outside_edr3_interval": excluded, "scan_angle_convention_check": conv,
           "per_pixel": summ, "outputs": {"pixel_statistics_npz": str(maps_path), "pixel_statistics_sha256": sha256_file(maps_path),
                                          "mock_sample_arrays": mock_files, "mock_nside": MOCK_NSIDE},
           "assumptions": ["commanded attitude = realised attitude; dead time and EDR3 data gaps not removed",
                           "observer at the Earth barycentric position (astropy built-in ephemeris), not at L2",
                           "a source is assigned the samples and passes of its HEALPix pixel (FOV-centre track)",
                           "equal along-scan weight per 10 s sample; across-scan information ignored",
                           "5-parameter design (2 positions, parallax, 2 PM) at reference epoch J2016.0"],
           "git": git_state(), "runtime_s": time.monotonic() - t0, "maxrss_mb": maxrss_mb()}
    write_json(summary_path, res)
    print(json.dumps({"summary": str(summary_path), "runtime_s": res["runtime_s"], "convention": conv}))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--md5sum", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    a = ap.parse_args(argv)
    run(a.csv.expanduser(), a.md5sum.expanduser(), a.out_dir.expanduser(), a.summary)


if __name__ == "__main__":
    main()
