"""R108 radio lane D11: RACS-low DR1 empirical dipole power and a southern cross-check of the R65 NVSS estimator.

Purpose
  (A) Apply the R65 integrated-minus-peak contrast estimator (ring-conditioned multinomial common transverse dipole,
      p = 2 "dipole" and p = 6 "dipole_stf", same-source Poisson influence sandwich covariance; htt.htt.infer.r65_*
      modules unchanged) to RACS-low DR1 with an explicit NSIDE = 64 mask and flux edges, on (i) the full RACS mask and
      (ii) the NVSS-R65 / RACS overlap; and refit NVSS from the R65 carrier on the same overlap pixels. The R65 NVSS
      full-mask contrast is replayed from the carrier first (must reproduce R65 delta and Wald).
      Covariance alternatives: Poisson sandwich (R65) and the R105 delete-one NSIDE = 4 block jackknife (p = 2).
  (B) Empirical count-dipole power: 3D Poisson GLM (monopole + dipole [+ 5 quadrupole]) on the masked count map;
      C1_hat = (4 pi/9)|d|^2 (Tiwari & Nusser 2016 Eq. 3.9), noise-debiased (4 pi/9)(|d|^2 - tr Cov_d), and the
      kinematic-subtracted residual with d_kin = [2 + x(1+alpha)] beta n_CMB (Ellis & Baldwin 1984; TN16 Eq. 3.8),
      beta = 369.82/c, CMB direction (RA, Dec) = (167.942, -6.944) deg (R65 constants), x measured from the counts,
      alpha = 0.75 (assumed). One-realisation chi^2_3 intervals are given.
  (C) Empirical differential (resolved/migrating vs diagonal classes) dipole power: binomial-logit GLM of the
      off-diagonal fraction with monopole + dipole; C1_diff_hat as in (B). This is the data analogue of the R106 g_diff
      C_1 in each survey's own resolved/migrating definition.
Inputs
  RACS-low DR1 strips ~/Downloads/htt_r108/radio/racs_dr1_casda_tap/*.vot (CASDA TAP, table
  AS110.racs_dr1_sources_galacticcut_v2021_08_v01; SHA-256 per strip verified against RECEIPTS.jsonl);
  R65 carrier docs/.../R65_DIPOLE_ANOMALY_20261117/RESULTS/PROVIDER_NVSS_CARRIERS.npz (SHA a51da9a9...).
Units: flux mJy (total) and mJy/beam (peak); RACS at 887.5 MHz, NVSS at 1.4 GHz. NVSS edges 20/40/80 mJy are scaled
  to RACS by (1400/887.5)^alpha with alpha = 0.75 (assumption, stated in the output); a x1.5 higher-cut variant is run.
Usage (repo root, venv python):
  .venv/bin/python -m scripts.r108.radio_racs_dipole --out docs/.../R108_LOS_ATLAS_DATA_20261124/RADIO/RACS_DIPOLE.json
Deterministic (no random numbers).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import healpy as hp
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
from scipy import stats

from htt.htt.infer.r65_count_quotient import RingLikelihood, angular_features, fit_joint, shared_maps
from htt.htt.infer.r65_overlap import common_influences, source_overlap_sandwich
from scripts.r105.radio_matched_refits import paired_covariance, selection_fit

RADIO = Path.home() / "Downloads/htt_r108/radio"
STRIPDIR = RADIO / "racs_dr1_casda_tap"
RECEIPTS = RADIO / "RECEIPTS.jsonl"
DERIVED = RADIO / "derived"
TABLE = "AS110.racs_dr1_sources_galacticcut_v2021_08_v01"
N_ROWS_EXPECTED = 2123638
CARRIER = Path("docs/research_program/observational_publication_20261015/R65_DIPOLE_ANOMALY_20261117/RESULTS/PROVIDER_NVSS_CARRIERS.npz")
CARRIER_SHA = "a51da9a98c3d0563446eb61f21aceff69fbfeed5446ec74471177170b8664e89"
R65_RESULT = Path("docs/research_program/observational_publication_20261015/R65_DIPOLE_ANOMALY_20261117/RESULTS/PROVIDER_NVSS_RESULT.json")
NSIDE = 64
NVSS_EDGES = np.array([20.0, 40.0, 80.0])
ALPHA_SPEC = 0.75
NU_RACS, NU_NVSS = 887.5, 1400.0
BCUT = 10.0
DEC_LO, DEC_HI = -78.0, 28.0          # RACS-low DR1 pixel-centre declination window (catalogue covers about -80..+30)
NVSS_DEC_LO = -37.0                    # R65 NVSS mask (lat > -37)
COVERAGE_FRAC = 0.5                    # drop pixels with all-flux RACS counts < 0.5 x median of the base mask
SPEED_CMB, C_KM_S = 369.82, 299792.458
CMB_RA, CMB_DEC = 167.942, -6.944
MODELS = ((2, "dipole"), (6, "dipole_stf"))
COLS = ("id", "ra", "dec", "total_flux_source", "peak_flux", "e_total_flux_source", "e_peak_flux", "gal_lat", "s_code")


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def git_head():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def cmb_vec():
    ra, dec = np.deg2rad([CMB_RA, CMB_DEC])
    return np.array([np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)])


# ------------------------------------------------------------------------------------------------ data

def load_racs():
    """Concatenate the CASDA strips (SHA-256 checked against the receipts); cache columns as npz."""
    recs = {}
    for line in RECEIPTS.read_text().splitlines():
        r = json.loads(line)
        if r.get("id") == "D11" and r.get("status", "").startswith("ok"):
            recs[r["name"]] = r
    names = sorted(recs)
    digests = {n: sha256(STRIPDIR / n) for n in names}
    for n in names:
        if digests[n] != recs[n]["sha256"]:
            raise ValueError(f"strip digest mismatch {n}")
    DERIVED.mkdir(parents=True, exist_ok=True)
    cache = DERIVED / "racs_dr1_galcut_v01_columns.npz"
    key = hashlib.sha256(json.dumps(digests, sort_keys=True).encode()).hexdigest()
    if cache.exists():
        with np.load(cache, allow_pickle=False) as z:
            if str(z["source_key"]) == key:
                return {c: z[c] for c in COLS}, digests, dict(cache=str(cache), cache_sha256=sha256(cache), source_key=key)
    from astropy.io.votable import parse_single_table
    parts = {c: [] for c in COLS}
    for n in names:
        t = parse_single_table(str(STRIPDIR / n)).to_table()
        for c in COLS:
            col = t[c]
            parts[c].append(np.asarray(col.filled("") if c == "s_code" and hasattr(col, "filled") else
                                       (col.filled(np.nan) if hasattr(col, "filled") and c != "id" else col)))
    data = {c: np.concatenate(v) for c, v in parts.items()}
    data["s_code"] = data["s_code"].astype("U2")
    tmp = cache.with_suffix(".part.npz")
    np.savez(tmp, source_key=np.array(key), **data)
    tmp.rename(cache)
    return data, digests, dict(cache=str(cache), cache_sha256=sha256(cache), source_key=key)


def pixel_geometry():
    npix = hp.nside2npix(NSIDE)
    pix = np.arange(npix)
    vec = np.column_stack(hp.pix2vec(NSIDE, pix))
    lon, lat = hp.pix2ang(NSIDE, pix, lonlat=True)
    galb = SkyCoord(ra=lon * u.deg, dec=lat * u.deg, frame="icrs").galactic.b.deg
    return vec, lon, lat, galb


def racs_mask(allpix_counts, lat, galb):
    base = (np.abs(galb) > BCUT) & (lat >= DEC_LO) & (lat <= DEC_HI)
    med = float(np.median(allpix_counts[base]))
    cov = allpix_counts >= COVERAGE_FRAC * med
    mask = base & cov
    info = dict(nside=NSIDE, galactic_latitude_cut_deg=BCUT, pixel_centre_dec_window_deg=[DEC_LO, DEC_HI],
                coverage_rule=f"all-flux RACS source count per pixel >= {COVERAGE_FRAC} x median over the base mask",
                median_all_flux_count_base=med, base_pixels=int(base.sum()), removed_by_coverage=int((base & ~cov).sum()),
                retained_pixels=int(mask.sum()), sky_fraction=float(mask.mean()),
                mask_sha256=hashlib.sha256(mask.astype(np.uint8).tobytes()).hexdigest())
    return mask, info


def joint_cube(ra, dec, peak, total, edges, kept):
    npix = hp.nside2npix(NSIDE)
    pix = hp.ang2pix(NSIDE, ra, dec, lonlat=True)
    pb, tb = np.searchsorted(edges, peak, side="right"), np.searchsorted(edges, total, side="right")
    j = np.bincount((4 * pb + tb) * npix + pix, minlength=16 * npix).reshape(4, 4, npix)
    return j[:, :, kept]


# ------------------------------------------------------------------------------------------------ estimators

def contrast(joint, feats, rings):
    """R65 paired estimator on a (4,4,pix) joint class cube (as R106 estimator())."""
    peak, integ = joint[1:, :, :].sum(axis=1), joint[:, 1:, :].sum(axis=0)
    out = {}
    for p, name in MODELS:
        f = np.ascontiguousarray(feats[:, :p])
        maps, offsets = shared_maps(3, p)
        ep = [RingLikelihood(y, f, rings) for y in peak]
        ei = [RingLikelihood(y, f, rings) for y in integ]
        fp, fi = fit_joint(ep, maps, offsets), fit_joint(ei, maps, offsets)
        cov = source_overlap_sandwich(common_influences(ep, fp, maps), peak, common_influences(ei, fi, maps), integ, joint[1:, 1:])
        c = np.asarray(cov["covariance_contrast"])
        d = np.asarray(fi["estimate"][:2]) - np.asarray(fp["estimate"][:2])
        t = float(d @ np.linalg.solve(c, d))
        out[name] = dict(delta_integrated_minus_peak_xy=d, covariance_contrast_poisson_sandwich=c, wald_t_self=t,
                         poisson_chi2_2dof_p=float(stats.chi2.sf(t, 2)),
                         peak_common_dipole_xy=np.asarray(fp["estimate"][:2]), integrated_common_dipole_xy=np.asarray(fi["estimate"][:2]),
                         overdispersion_peak=fp.get("overdispersion_diagnostic"), overdispersion_integrated=fi.get("overdispersion_diagnostic"))
    return out, peak, integ


def offdiag_fraction(joint):
    j = joint.sum(axis=2).astype(float)
    off = ~np.eye(4, dtype=bool)
    fp = float(j[1:, :][off[1:, :]].sum() / j[1:, :].sum())
    fi = float(j[:, 1:][off[:, 1:]].sum() / j[:, 1:].sum())
    return dict(df=fi - fp, f_off_peak=fp, f_off_integrated=fi)


def jackknife(peak, integ, feats, rings, kept, nside_block=4):
    labels = hp.nest2ring(nside_block, hp.ring2nest(NSIDE, kept) // ((NSIDE // nside_block) ** 2))
    blocks = np.unique(labels)
    s = [selection_fit(y, feats, rings, 2) for y in (peak, integ)]
    reps = []
    for b in blocks:
        keep = labels != b
        reps.append(np.concatenate([selection_fit(y[:, keep], feats[keep], rings[keep], 2, st)[:2] for y, st in zip((peak, integ), s)]))
    joint_cov, ccov = paired_covariance(reps)
    d = np.asarray(s[1][:2]) - np.asarray(s[0][:2])
    w = float(d @ np.linalg.solve(ccov, d))
    return dict(blocks=len(blocks), contrast_covariance_xy=ccov, delta_xy=d, wald_jk=w, gaussian_chi2_2dof_p=float(stats.chi2.sf(w, 2)))


def design(vec, quad):
    x, y, z = vec.T
    cols = [np.ones_like(x), x, y, z]
    if quad:
        cols += [(x * x - y * y) / np.sqrt(2), np.sqrt(2) * x * y, np.sqrt(2) * x * z, np.sqrt(2) * y * z,
                 (2 * z * z - x * x - y * y) / np.sqrt(6)]
    return np.column_stack(cols)


def poisson_glm(y, X, iters=60):
    beta = np.zeros(X.shape[1])
    beta[0] = math.log(max(y.mean(), 1e-12))
    for _ in range(iters):
        mu = np.exp(X @ beta)
        g = X.T @ (y - mu)
        H = X.T @ (X * mu[:, None])
        step = np.linalg.solve(H, g)
        beta += step
        if np.max(np.abs(step)) < 1e-12:
            break
    mu = np.exp(X @ beta)
    cov = np.linalg.inv(X.T @ (X * mu[:, None]))
    pearson = float(np.sum((y - mu) ** 2 / mu) / (len(y) - X.shape[1]))
    return beta, cov, pearson


def binomial_glm(k, n, X, iters=60):
    ok = n > 0
    k, n, X = k[ok], n[ok], X[ok]
    p0 = k.sum() / n.sum()
    beta = np.zeros(X.shape[1])
    beta[0] = math.log(p0 / (1 - p0))
    for _ in range(iters):
        pr = 1 / (1 + np.exp(-(X @ beta)))
        g = X.T @ (k - n * pr)
        H = X.T @ (X * (n * pr * (1 - pr))[:, None])
        step = np.linalg.solve(H, g)
        beta += step
        if np.max(np.abs(step)) < 1e-12:
            break
    pr = 1 / (1 + np.exp(-(X @ beta)))
    cov = np.linalg.inv(X.T @ (X * (n * pr * (1 - pr))[:, None]))
    pearson = float(np.sum((k - n * pr) ** 2 / (n * pr * (1 - pr))) / (len(k) - X.shape[1]))
    return beta, cov, pearson, float(p0)


def c1_summary(d, cov_d, pearson, d_kin=None):
    """C1 = (4pi/9)|d|^2 forms; Poisson and Pearson-scaled noise debiasing; chi^2_3 one-realisation interval."""
    d = np.asarray(d, float)
    out = dict(dipole_xyz=d, amplitude=float(np.linalg.norm(d)), cov_dipole_poisson=cov_d, pearson_dispersion=pearson,
               C1_raw=float(4 * math.pi / 9 * d @ d),
               C1_debiased_poisson=float(4 * math.pi / 9 * (d @ d - np.trace(cov_d))),
               C1_debiased_pearson=float(4 * math.pi / 9 * (d @ d - pearson * np.trace(cov_d))),
               direction_radec_deg=list(hp.vec2ang(d / np.linalg.norm(d), lonlat=True)))
    out["direction_radec_deg"] = [float(np.ravel(v)[0]) for v in out["direction_radec_deg"]]
    q = stats.chi2.ppf([0.975, 0.84, 0.16, 0.025], 3)
    out["C1_raw_one_realisation_interval_68"] = [3 * out["C1_raw"] / q[1], 3 * out["C1_raw"] / q[2]]
    out["C1_raw_one_realisation_interval_95"] = [3 * out["C1_raw"] / q[0], 3 * out["C1_raw"] / q[3]]
    # transverse (ICRS x, y) estimate: the R65/R106 ring-conditioned model sees only these two components, each with
    # variance 3 C1/(4 pi) for an isotropic l = 1 field, so C1_xy = (2 pi/3)(d_x^2 + d_y^2) (chi^2_2 interval)
    cxy = np.asarray(cov_d)[:2, :2]
    sxy = float(d[0] ** 2 + d[1] ** 2)
    q2 = stats.chi2.ppf([0.975, 0.84, 0.16, 0.025], 2)
    out["C1_transverse_raw"] = 2 * math.pi / 3 * sxy
    out["C1_transverse_debiased_poisson"] = 2 * math.pi / 3 * (sxy - float(np.trace(cxy)))
    out["C1_transverse_debiased_pearson"] = 2 * math.pi / 3 * (sxy - pearson * float(np.trace(cxy)))
    out["C1_transverse_raw_one_realisation_interval_68"] = [2 * out["C1_transverse_raw"] / q2[1], 2 * out["C1_transverse_raw"] / q2[2]]
    out["C1_transverse_raw_one_realisation_interval_95"] = [2 * out["C1_transverse_raw"] / q2[0], 2 * out["C1_transverse_raw"] / q2[3]]
    if d_kin is not None:
        r = d - d_kin
        out["kinematic_expected_xyz"] = d_kin
        out["kinematic_expected_amplitude"] = float(np.linalg.norm(d_kin))
        out["ratio_amplitude_to_kinematic"] = float(np.linalg.norm(d) / np.linalg.norm(d_kin))
        out["residual_xyz"] = r
        out["C1_residual_raw"] = float(4 * math.pi / 9 * r @ r)
        out["C1_residual_debiased_poisson"] = float(4 * math.pi / 9 * (r @ r - np.trace(cov_d)))
        out["C1_residual_debiased_pearson"] = float(4 * math.pi / 9 * (r @ r - pearson * np.trace(cov_d)))
        out["C1_residual_one_realisation_interval_68"] = [3 * out["C1_residual_raw"] / q[1], 3 * out["C1_residual_raw"] / q[2]]
    return out


def count_dipole(counts_pix, vec, d_kin):
    res = {}
    for quad in (False, True):
        X = design(vec, quad)
        beta, cov, pearson = poisson_glm(counts_pix.astype(float), X)
        res["mono_dipole_quadrupole" if quad else "mono_dipole"] = c1_summary(beta[1:4], cov[1:4, 1:4], pearson, d_kin)
    return res


def diff_dipole(joint, vec):
    off = ~np.eye(4, dtype=bool)
    k = sum(joint[i, j] for i in range(4) for j in range(4) if off[i, j]).astype(float)
    n = k + sum(joint[i, i] for i in range(1, 4)).astype(float)
    res = {}
    for quad in (False, True):
        X = design(vec, quad)
        beta, cov, pearson, p0 = binomial_glm(k, n, X)
        r = c1_summary(beta[1:4], cov[1:4, 1:4], pearson)
        r["offdiag_fraction_mean"] = p0
        r["note"] = ("logit dipole of the resolved/migrating fraction among selected sources; logit(n_off/(n_off+n_diag)) = log(n_off/n_diag), "
                     "so this is the dipole of the R106 g_diff (log-density of off-diagonal classes relative to the diagonal classes)")
        res["mono_dipole_quadrupole" if quad else "mono_dipole"] = r
    return res


def integral_slope(total, cut):
    a, b = np.sum(total >= cut), np.sum(total >= 2 * cut)
    return float(math.log2(a / b)), int(a), int(b)


# ------------------------------------------------------------------------------------------------ driver

def survey_block(joint, kept, vec_all, rings, feats, d_kin, do_jk=True):
    vec = vec_all[kept]
    out = dict(retained_pixels=int(len(kept)), joint_class_counts=joint.sum(axis=2).tolist())
    est, peak, integ = contrast(joint, feats, rings)
    out["contrast_R65_estimator"] = est
    out["offdiag_fraction_contrast"] = offdiag_fraction(joint)
    df = out["offdiag_fraction_contrast"]["df"]
    out["required_offdiag_dipole_for_contrast"] = float(np.linalg.norm(est["dipole"]["delta_integrated_minus_peak_xy"]) / df) if df else None
    if do_jk:
        out["jackknife_nside4_p2"] = jackknife(peak, integ, feats, rings, kept)
    sel_int = integ.sum(axis=0)
    sel_peak = peak.sum(axis=0)
    out["count_dipole_integrated_selection"] = count_dipole(sel_int, vec, d_kin)
    out["count_dipole_peak_selection"] = count_dipole(sel_peak, vec, d_kin)
    out["differential_offdiag_dipole"] = diff_dipole(joint, vec)
    omega = len(kept) * 4 * math.pi / hp.nside2npix(NSIDE)
    out["solid_angle_sr"] = omega
    out["Nbar_per_sr_integrated_selection"] = float(sel_int.sum() / omega)
    out["shot_noise_integrated_selection"] = float(omega / sel_int.sum())
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-jackknife", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    data, digests, cache = load_racs()
    n = len(data["id"])
    if n != N_ROWS_EXPECTED or len(np.unique(data["id"])) != n:
        raise ValueError(f"row count {n} or duplicate ids differ from the CASDA COUNT(*) {N_ROWS_EXPECTED}")
    ra, dec, tot, pk = (np.asarray(data[c], float) for c in ("ra", "dec", "total_flux_source", "peak_flux"))
    good = np.isfinite(ra) & np.isfinite(dec) & np.isfinite(tot) & np.isfinite(pk) & (tot > 0) & (pk > 0)
    vec_all, lon, lat, galb = pixel_geometry()
    npix = hp.nside2npix(NSIDE)
    allcounts = np.bincount(hp.ang2pix(NSIDE, ra[good], dec[good], lonlat=True), minlength=npix)
    mask, minfo = racs_mask(allcounts, lat, galb)
    scale = (NU_NVSS / NU_RACS) ** ALPHA_SPEC
    edges = NVSS_EDGES * scale
    out = dict(schema="htt.r108.radio.racs_dipole/1", node="SQ-RADIO", acquisition_item="D11",
               command=" ".join([sys.executable, "-m", "scripts.r108.radio_racs_dipole", *(argv or sys.argv[1:])]),
               git_head=git_head(), started_utc=dt.datetime.now(dt.timezone.utc).isoformat(), script_sha256=sha256(Path(__file__)),
               catalogue=dict(table=TABLE, service="https://casda.csiro.au/casda_vo_tools/tap", rows=n, finite_positive_rows=int(good.sum()),
                              citation="Hale et al. 2021, PASA 38, e058", strip_sha256=digests, cache=cache,
                              note="CASDA reports Thisversion v1, Latestversion v2 for this table; v01 is used as specified by the R107 manifest"),
               input_sha256={"PROVIDER_NVSS_CARRIERS.npz": sha256(CARRIER), "PROVIDER_NVSS_RESULT.json": sha256(R65_RESULT)},
               assumptions=dict(spectral_index_alpha=ALPHA_SPEC, edge_scale_1400_to_887p5=scale, racs_edges_mJy=edges.tolist(),
                                beta=SPEED_CMB / C_KM_S, cmb_direction_radec_deg=[CMB_RA, CMB_DEC]),
               mask_racs=minfo)
    if sha256(CARRIER) != CARRIER_SHA:
        raise ValueError("R65 carrier digest mismatch")
    with np.load(CARRIER, allow_pickle=False) as z:
        npix_nv, nfeat, nrings, njoint = z["pixel_indices"], z["features"], z["groups"], z["joint_bin_pixel_counts"]
    nvec = cmb_vec()
    # ---- NVSS replay on the full R65 mask (validation of contrast())
    r65 = json.loads(R65_RESULT.read_text())
    est_nv, _, _ = contrast(njoint, nfeat, nrings)
    replay = {}
    for _, m in MODELS:
        ref_d = np.array(r65["paired_comparisons"][m]["integrated_minus_peak"])
        ref_t = r65["paired_comparisons"][m]["poisson_source_linearized_wald"]
        replay[m] = dict(delta=est_nv[m]["delta_integrated_minus_peak_xy"], r65_delta=ref_d,
                         max_abs_delta_diff=float(np.max(np.abs(est_nv[m]["delta_integrated_minus_peak_xy"] - ref_d))),
                         wald=est_nv[m]["wald_t_self"], r65_wald=ref_t, rel_wald_diff=abs(est_nv[m]["wald_t_self"] / ref_t - 1))
    out["nvss_r65_replay"] = replay
    if any(v["max_abs_delta_diff"] > 2e-9 or v["rel_wald_diff"] > 1e-7 for v in replay.values()):
        out["status"] = "NVSS_REPLAY_FAILED"
        Path(a.out).write_text(json.dumps(out, indent=1, default=lambda o: np.asarray(o).tolist()) + "\n")
        return 2
    print("replay ok", {m: (v["max_abs_delta_diff"], v["rel_wald_diff"]) for m, v in replay.items()}, flush=True)
    xn = math.log2(njoint[:, 1:].sum() / njoint[:, 2:].sum())
    dkin_nv = (2 + xn * (1 + ALPHA_SPEC)) * SPEED_CMB / C_KM_S * nvec
    out["nvss_full_R65_mask"] = survey_block(njoint, npix_nv, vec_all, nrings, nfeat, dkin_nv, do_jk=False)
    out["nvss_full_R65_mask"]["integral_slope_x_20_40"] = xn
    # ---- RACS variants
    variants = {"racs_full_mask_alpha0p75": (mask, edges), "racs_full_mask_alpha0p75_cut_x1p5": (mask, edges * 1.5)}
    nv_mask = np.zeros(npix, bool)
    nv_mask[npix_nv] = True
    overlap = mask & nv_mask & (lat >= NVSS_DEC_LO)
    variants["racs_overlap_with_R65_NVSS_mask"] = (overlap, edges)
    out["mask_overlap"] = dict(retained_pixels=int(overlap.sum()), mask_sha256=hashlib.sha256(overlap.astype(np.uint8).tobytes()).hexdigest(),
                               rule="RACS mask AND R65 NVSS carrier pixels (dec > -37, |b| > 10)")
    for name, (msk, ed) in variants.items():
        kept = np.flatnonzero(msk)
        rings = hp.pix2ring(NSIDE, kept).astype(int)
        feats = angular_features(vec_all[kept], True)
        sel = good
        joint = joint_cube(ra[sel], dec[sel], pk[sel], tot[sel], ed, kept)
        x, na, nb = integral_slope(tot[sel][msk[hp.ang2pix(NSIDE, ra[sel], dec[sel], lonlat=True)]], ed[0])
        dkin = (2 + x * (1 + ALPHA_SPEC)) * SPEED_CMB / C_KM_S * nvec
        blk = survey_block(joint, kept, vec_all, rings, feats, dkin, do_jk=not a.no_jackknife)
        blk.update(edges_mJy=ed.tolist(), integral_slope_x=x, N_ge_cut=na, N_ge_2cut=nb)
        out[name] = blk
        print(name, "delta", blk["contrast_R65_estimator"]["dipole"]["delta_integrated_minus_peak_xy"],
              "t", round(blk["contrast_R65_estimator"]["dipole"]["wald_t_self"], 3), "df", round(blk["offdiag_fraction_contrast"]["df"], 4),
              "C1raw", blk["count_dipole_integrated_selection"]["mono_dipole"]["C1_raw"], flush=True)
    # ---- NVSS on the same overlap pixels (from the carrier)
    sub = np.flatnonzero(overlap[npix_nv])
    kept_nv = npix_nv[sub]
    blk = survey_block(njoint[:, :, sub], kept_nv, vec_all, nrings[sub], nfeat[sub], dkin_nv, do_jk=not a.no_jackknife)
    out["nvss_on_overlap_pixels"] = blk
    print("nvss overlap delta", blk["contrast_R65_estimator"]["dipole"]["delta_integrated_minus_peak_xy"],
          "t", round(blk["contrast_R65_estimator"]["dipole"]["wald_t_self"], 3), flush=True)
    out["claim_labels"] = dict(
        contrast="CONDITIONAL: Poisson-sandwich and jackknife-Gaussian p are not calibrated (R106: overdispersion; no RACS null mocks run)",
        count_C1="CONDITIONAL: single-realisation dipole power on a partial sky; includes kinematic, clustering, systematic and mask-leakage parts; "
                 "kinematic subtraction assumes alpha = 0.75 and the measured x",
        differential_C1="CONDITIONAL: empirical dipole of the resolved/migrating fraction; not an LSS prediction")
    out["status"] = "OK"
    out["elapsed_s"] = time.time() - t0
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1, default=lambda o: np.asarray(o).tolist()) + "\n")
    print("wrote", a.out, round(out["elapsed_s"], 1), "s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
