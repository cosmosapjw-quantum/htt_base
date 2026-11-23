"""R106 D3: independent null mocks for the R65 NVSS integrated-minus-peak contrast.

Statistic (identical to R65 run_r65_integrated_flux.py): for the provider peak and
provider integrated selections (20-40, 40-80, >=80 mJy bins) on the identical NSIDE=64
R65 mask, fit the ring-conditioned multinomial common transverse dipole (p=2, "dipole")
or common dipole plus four free STF coefficients per bin (p=6, "dipole_stf") with
fit_joint/shared_maps; contrast delta = integrated - peak (ICRS x,y); covariance is the
same-source Poisson influence sandwich (common_influences + source_overlap_sandwich with
the actual joint-bin memberships). Wald T = delta^T C^-1 delta.

Null mocks (Cox processes; positions independent of the flux pair):
  * the footprint's actual (peak, integrated) flux pairs are retained; each mock perturbs
    them with the provider 1-sigma uncertainties (shared deviate when integrated == peak,
    independent deviates otherwise, integrated >= peak enforced) and recomputes the 4x4
    joint class counts;
  * every class is placed on the 33,000 mask pixels by a multinomial with intensity
    exp(g_common [+ g_diff for off-diagonal i.e. resolved/migrating classes] + D0.n_xy),
    D0 = mean of the observed R65 peak/integrated common dipoles (common to both
    selections, so the null contrast has zero mean);
  * g_common (family LSS_COMMON): Gaussian field, C_l = A_c l^-1.2 (l>=1); A_c fitted so the
    mock delete-one NSIDE=4 block-jackknife trace of the two single-selection dipoles (same
    166 deletion blocks as R105) equals the data value;
  * g_diff: an EMPIRICAL DIFFERENTIAL-SELECTION FIELD, not large-scale structure. Families
    EMPIRICAL_DIFF_SELECTION_RED / _MID / _FLAT (internal keys LSS_DIFF_RED / LSS_DIFF_MID /
    LSS_DIFF_FLAT are kept so that seeds and the 2000-mock R106 outputs stay addressable):
    independent field on the resolved (off-diagonal) classes, C_l = A_m l^-1.2, A_m l^-0.6 or
    flat C_l = A_m for 1<=l<=48, with A_m fitted so the mock jackknife trace of the contrast
    equals the data value while A_c is held at the LSS_COMMON value. The DIFF families are
    therefore not jointly calibrated: at the fitted A_m their single-selection jackknife trace
    exceeds the data target the common field was fitted to (R106 review F4);
  * l=1 of g_diff (option --diff-c1-scale, follow-up stages): every shape sets C_1 = A_m by
    extrapolating its assumed power law down to l=1. The transverse l=1 mode lies inside the
    fitted log-linear dipole model, so it shifts the full fit and every delete-one replicate
    coherently. The NSIDE=4/8 jackknife traces (the calibration target) and the NSIDE8/4 ratio
    are therefore insensitive to it, yet it sets most of the null contrast covariance. To
    first order, Cov(delta) = Cov_{C_1=0} + df^2 (3 C_1/4pi) I_2 with
    df = f_off(integrated) - f_off(peak). Each family's null is "a random dipole of per-
    component RMS sqrt(3 C_1/4pi) in the log-density of the resolved/migrating classes", and
    every p_mc is conditional on the extrapolated C_1. No family's p_mc is the LSS/selection-
    null p-value. C_1 = 0 is the opposite extreme, not a conservative limit (R106 review F1);
  * shape diagnostic: the ratio of NSIDE=8 (594 blocks) to NSIDE=4 (166 blocks) jackknife
    traces in 9 mocks per family is compared with the same ratio in the data (R105). It does not
    exclude any family at 2 sigma and is blind to C_1. MID is only the family whose ratio is
    closest to the data. The MID family and this diagnostic were introduced after smoke run 1
    had displayed RED/FLAT p-values (R106 review F2/F6).
Calibration uses common random numbers across amplitude levels.

R106 review follow-up stages (--followup; amplitudes reused from the 2000-mock reference run so
that every follow-up mock is a common-random-number partner of a reference mock):
  c1zero     DIFF families at C_1 = 0 on the main-run seeds; nominal replay subset; jackknife
             C_1-insensitivity on the calibration and scale seeds; overdispersion (F1, F2, F5);
  amplitude  amplitude nuisance = jk4-trace scatter (fresh jackknife mocks) combined with the
             calibration MC error; per-mock amplitude draws and 16%/84% amplitude ensembles (F3);
  validate   direct mocks at the closed-form C_1 where p(t_self, dipole) crosses 0.05 (F1);
  report     closed-form p versus C_1, crossings, validations, amplitude-marginal p with band,
             overdispersion validity table, per-run provenance; updates RUN_RECORD.json
             (pre-review copy kept) (F1-F6).
No file under the committed R65/R105 directories is written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import multiprocessing as mp
import platform
import re
import resource
import shutil
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import healpy as hp
import numpy as np
import pandas as pd
import scipy
from scipy.optimize import brentq
from scipy.stats import spearmanr, truncnorm

from htt.htt.infer.r65_count_quotient import RingLikelihood, fit_joint, shared_maps
from htt.htt.infer.r65_overlap import common_influences, source_overlap_sandwich
from scripts.r105.radio_matched_refits import CARRIER_SHA, paired_covariance, selection_fit

BASE = Path("docs/research_program/observational_publication_20261015")
R65_RESULT = BASE / "R65_DIPOLE_ANOMALY_20261117/RESULTS/PROVIDER_NVSS_RESULT.json"
R65_CARRIER = BASE / "R65_DIPOLE_ANOMALY_20261117/RESULTS/PROVIDER_NVSS_CARRIERS.npz"
R105_REFITS = BASE / "R105_RESEARCH_20261124/RADIO_MATCHED_REFITS.json"
RAW = Path("/mnt/extdrive/workdir/raw/new_acquisitions/radio_hi/RACS_SBI_20261117/Full_NVSS_combined_named.dat")
RAW_SHA = "52eb576c1e3e71837f2fca26121789ccc0b316152cca3f25ea2f37ea8ef5a38e"
OUTDIR = Path.home() / "Downloads/htt_r106_analysis/nvss"
FOLLOWUP_DIR = OUTDIR / "review_followup"
EDGES = [20.0, 40.0, 80.0]
NSIDE = 64
LMAX = 3 * NSIDE - 1
SLOPE = -1.2
MID_SLOPE = -0.6
FLAT_LMAX = 48
MODELS = ((2, "dipole"), (6, "dipole_stf"))
FAMILIES = {"LSS_COMMON": 1, "LSS_DIFF_RED": 2, "LSS_DIFF_FLAT": 3, "LSS_DIFF_MID": 4}
DIFF_FAMILIES = ("LSS_DIFF_RED", "LSS_DIFF_MID", "LSS_DIFF_FLAT")
FAMILY_LABELS = {"LSS_COMMON": "LSS_COMMON",
                 "LSS_DIFF_RED": "EMPIRICAL_DIFF_SELECTION_RED",
                 "LSS_DIFF_MID": "EMPIRICAL_DIFF_SELECTION_MID",
                 "LSS_DIFF_FLAT": "EMPIRICAL_DIFF_SELECTION_FLAT"}
STATS = ("t_self", "t_fixed", "t_jk4", "t_jk8")
STAT_NAMES = {"t_self": "wald_self_R65_estimator", "t_fixed": "wald_fixed_R65_poisson_cov",
              "t_jk4": "wald_fixed_R105_jk4_cov", "t_jk8": "wald_fixed_R105_jk8_cov"}
ALPHAS = (0.05, 0.01)
ROOT_SEED = 20261124
# Seed streams: main mocks [ROOT_SEED, FAMILIES[f], i]; calibration [ROOT_SEED, 100, i]; scale
# diagnostic [ROOT_SEED, 200, i]; follow-up amplitude-scatter jackknife mocks [ROOT_SEED, 300, i];
# per-mock amplitude ratios [ROOT_SEED, 500, FAMILIES[f], i]; bootstrap [ROOT_SEED, 900, ...].
REVIEW_FINDINGS = {
    "F1": "p is driven by the extrapolated C_1 of g_diff, which no same-sky jackknife constrains",
    "F2": "labelling MID as favoured by the data was unsupported; the NSIDE8/4 selector does not discriminate and is blind to C_1",
    "F3": "amplitude calibration uncertainty not propagated; p quoted to 4 digits",
    "F4": "DIFF families not jointly calibrated; they are empirical differential-selection fields, not LSS",
    "F5": "mock overdispersion never used as a validity check",
    "F6": "provenance did not record per-run script SHAs or the post-smoke design change",
}

G = {}  # read-only state inherited by forked workers


def sha256(path):
    with open(path, "rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def classes(peak, total):
    return 4 * np.searchsorted(EDGES, peak, side="right") + np.searchsorted(EDGES, total, side="right")


def load():
    t0 = time.time()
    digests = {"raw_catalogue": sha256(RAW), "r65_carrier": sha256(R65_CARRIER),
               "r65_result": sha256(R65_RESULT), "r105_matched_refits": sha256(R105_REFITS)}
    if digests["raw_catalogue"] != RAW_SHA or digests["r65_carrier"] != CARRIER_SHA:
        raise ValueError("pinned input digest mismatch")
    tab = pd.read_csv(RAW, sep=r"\s+", quotechar='"',
                      usecols=["ra", "dec", "peak_flux", "integrated_flux", "peak_flux_unc", "integrated_flux_unc"])
    a, d, p, t, sp, si = (tab[k].to_numpy(float) for k in
                          ["ra", "dec", "peak_flux", "integrated_flux", "peak_flux_unc", "integrated_flux_unc"])
    ok = (np.isfinite(a) & np.isfinite(d) & np.isfinite(p) & np.isfinite(t) &
          (a >= 0) & (a < 360) & (np.abs(d) <= 90) & (p > 0) & (t > 0))
    if not ok.all():
        raise ValueError("R65 used all rows as finite positive pairs; schema drift")
    with np.load(R65_CARRIER, allow_pickle=False) as src:
        pix, feat, rings, joint = (src[k] for k in ["pixel_indices", "features", "groups", "joint_bin_pixel_counts"])
    lookup = -np.ones(hp.nside2npix(NSIDE), dtype=np.int64)
    lookup[pix] = np.arange(len(pix))
    where = lookup[hp.ang2pix(NSIDE, a, d, lonlat=True)]
    infp = where >= 0
    replay = np.bincount(classes(p[infp], t[infp]) * len(pix) + where[infp],
                         minlength=16 * len(pix)).reshape(4, 4, len(pix))
    if not np.array_equal(replay, joint):
        raise ValueError("raw replay differs from R65 joint carrier")
    unc = np.maximum(np.nan_to_num(sp), np.nan_to_num(si))
    cand = infp & (t + 8.0 * unc >= EDGES[0])
    if np.any(~np.isfinite(sp[cand])) or np.any(~np.isfinite(si[cand])) or np.any(sp[cand] < 0) or np.any(si[cand] < 0):
        raise ValueError("non-finite provider uncertainties among candidates")
    r65 = json.loads(R65_RESULT.read_text())
    r105 = json.loads(R105_REFITS.read_text())
    G.update(pix=pix, rings=rings, joint=joint,
             feats={q: np.ascontiguousarray(feat[:, :q]) for q in (2, 6)},
             labels={n: hp.nest2ring(n, hp.ring2nest(NSIDE, pix) // ((NSIDE // n) ** 2)) for n in (4, 8)},
             cand=dict(peak=p[cand], total=t[cand], sp=sp[cand], si=si[cand], same=(t[cand] == p[cand])),
             n_footprint=int(infp.sum()), n_candidates=int(cand.sum()))
    G["blocks"] = {n: np.unique(v) for n, v in G["labels"].items()}
    ell, emm = hp.Alm.getlm(LMAX)
    G["ell"], G["m0"] = ell, emm == 0
    est = {f"{s}_{m}": r65["models"][f"provider_{s}_{m}"]["common_transverse_fit"]["estimate"][:2]
           for _, m in MODELS for s in ("peak", "integrated")}
    G["D0"] = 0.5 * (np.array(r65["models"]["provider_peak_dipole"]["common_transverse_fit"]["estimate"][:2]) +
                     np.array(r65["models"]["provider_integrated_dipole"]["common_transverse_fit"]["estimate"][:2]))
    G["cov_fixed"] = {m: np.array(r65["paired_comparisons"][m]["covariance"]["covariance_contrast"]) for _, m in MODELS}
    G["delta_r65"] = {m: np.array(r65["paired_comparisons"][m]["integrated_minus_peak"]) for _, m in MODELS}
    G["wald_r65"] = {m: r65["paired_comparisons"][m]["poisson_source_linearized_wald"] for _, m in MODELS}
    G["cov_jk"] = {(n, m): np.array(r105["spatial_deletions"][n][m]["contrast_covariance_xy"])
                   for n in ("4", "8") for _, m in MODELS}
    G["wald_jk"] = {(n, m): r105["spatial_deletions"][n][m]["direct_matched_Wald"] for n in ("4", "8") for _, m in MODELS}
    j4 = np.array(r105["spatial_deletions"]["4"]["dipole"]["joint_covariance_peak_xy_integrated_xy"])
    G["target_single"] = float(np.trace(j4[:2, :2]) + np.trace(j4[2:, 2:]))
    G["target_contrast"] = float(np.trace(np.array(r105["spatial_deletions"]["4"]["dipole"]["contrast_covariance_xy"])))
    j8 = np.array(r105["spatial_deletions"]["8"]["dipole"]["joint_covariance_peak_xy_integrated_xy"])
    G["data_scale"] = dict(
        trace_single_nside4=G["target_single"], trace_single_nside8=float(np.trace(j8[:2, :2]) + np.trace(j8[2:, 2:])),
        trace_contrast_nside4=G["target_contrast"],
        trace_contrast_nside8=float(np.trace(np.array(r105["spatial_deletions"]["8"]["dipole"]["contrast_covariance_xy"]))),
        jk_wald_self_nside4=G["wald_jk"]["4", "dipole"], jk_wald_self_nside8=G["wald_jk"]["8", "dipole"])
    G["data_scale"]["ratio_single_8_over_4"] = G["data_scale"]["trace_single_nside8"] / G["target_single"]
    G["data_scale"]["ratio_contrast_8_over_4"] = G["data_scale"]["trace_contrast_nside8"] / G["target_contrast"]
    meta = dict(input_sha256=digests, raw_rows=len(tab), footprint_sources=G["n_footprint"],
                scatter_candidates=G["n_candidates"], footprint_pixels=len(pix), deletion_blocks_nside4=len(G["blocks"][4]), deletion_blocks_nside8=len(G["blocks"][8]),
                joint_class_counts_observed=joint.sum(axis=2).tolist(), common_dipole_injected_xy=G["D0"].tolist(),
                load_seconds=time.time() - t0, observed_fits_r65=est)
    return meta


def estimator(joint):
    """Exact R65 paired estimator on a 4x4xpix joint class count cube."""
    peak, integ = joint[1:, :, :].sum(axis=1), joint[:, 1:, :].sum(axis=0)
    out = {}
    for p, name in MODELS:
        f = G["feats"][p]
        maps, offsets = shared_maps(3, p)
        ep = [RingLikelihood(y, f, G["rings"]) for y in peak]
        ei = [RingLikelihood(y, f, G["rings"]) for y in integ]
        fp, fi = fit_joint(ep, maps, offsets), fit_joint(ei, maps, offsets)
        cov = source_overlap_sandwich(common_influences(ep, fp, maps), peak,
                                      common_influences(ei, fi, maps), integ, joint[1:, 1:])
        c = cov["covariance_contrast"]
        d = fi["estimate"][:2] - fp["estimate"][:2]
        out[name] = dict(delta=d, cov=c, t_self=float(d @ np.linalg.solve(c, d)),
                         t_fixed=float(d @ np.linalg.solve(G["cov_fixed"][name], d)),
                         t_jk4=float(d @ np.linalg.solve(G["cov_jk"]["4", name], d)),
                         t_jk8=float(d @ np.linalg.solve(G["cov_jk"]["8", name], d)),
                         est_peak=fp["estimate"][:2], est_int=fi["estimate"][:2],
                         od=(fp["overdispersion_diagnostic"], fi["overdispersion_diagnostic"]))
    return out, peak, integ


def offdiag_overdispersion(joint):
    """Pearson overdispersion of the summed resolved/migrating (off-diagonal) classes, R65 ring likelihood, p=2."""
    off = sum(joint[i, j] for i in range(4) for j in range(4) if i != j)
    return float(fit_joint([RingLikelihood(off, G["feats"][2], G["rings"])])["overdispersion_diagnostic"])


def jackknife(peak, integ, nside=4):
    """R105 delete-one NSIDE=4/8 block jackknife of the p=2 dipole fits (exact summed reduction)."""
    f, r = G["feats"][2], G["rings"]
    s = [selection_fit(y, f, r, 2) for y in (peak, integ)]
    reps = []
    for b in G["blocks"][nside]:
        keep = G["labels"][nside] != b
        reps.append(np.concatenate([selection_fit(y[:, keep], f[keep], r[keep], 2, st)[:2]
                                    for y, st in zip((peak, integ), s)]))
    joint_cov, ccov = paired_covariance(reps)
    d = s[1][:2] - s[0][:2]
    return dict(trace_single=float(np.trace(joint_cov[:2, :2]) + np.trace(joint_cov[2:, 2:])),
                trace_contrast=float(np.trace(ccov)), wald_self=float(d @ np.linalg.solve(ccov, d)), replicates=len(reps))


def spectrum(amp, kind):
    ell = np.arange(LMAX + 1, dtype=float)
    cl = np.zeros(LMAX + 1)
    if kind == "red":
        cl[1:] = amp * ell[1:] ** SLOPE
    elif kind == "mid":
        cl[1:] = amp * ell[1:] ** MID_SLOPE
    elif kind == "flat":
        cl[1:FLAT_LMAX + 1] = amp
    else:
        raise ValueError(kind)
    return cl


def diff_spectrum(amp, kind, c1_scale=1.0):
    """Differential-field spectrum with C_1 multiplied by c1_scale (0 removes the l=1 mode; 1 is the legacy spectrum)."""
    if not np.isfinite(c1_scale) or c1_scale < 0:
        raise ValueError("c1_scale must be finite and non-negative")
    cl = spectrum(amp, kind)
    cl[1] *= c1_scale
    return cl


def field(z, cl):
    """Gaussian field on the mask pixels from fixed unit normals z=(re,im)."""
    amp = np.sqrt(cl[G["ell"]])
    alm = np.where(G["m0"], amp * z[0], amp * (z[0] + 1j * z[1]) / np.sqrt(2.0)).astype(complex)
    return hp.alm2map(alm, NSIDE, lmax=LMAX)[G["pix"]]


def l1_dipole_xy(z, c1, lmax=LMAX):
    """Transverse (x, y) coefficients d of the l=1 part g_1(n) = d.n_xy + d_z n_z of field(z, cl) with cl[1] = c1.

    field() sets a_11 = sqrt(C_1)(z0 + i z1)/sqrt(2); with healpy's Y_11 = -sqrt(3/8pi) sin(theta) e^{i phi} this gives
    d_x = -sqrt(3 C_1/4pi) z0[a_11] and d_y = +sqrt(3 C_1/4pi) z1[a_11]; each component has variance 3 C_1/(4 pi).
    """
    if c1 < 0:
        raise ValueError("C_1 must be non-negative")
    i11 = hp.Alm.getidx(lmax, 1, 1)
    k = math.sqrt(3.0 * c1 / (4.0 * math.pi))
    z = np.asarray(z, dtype=float)
    return np.array([-k * z[0, i11], k * z[1, i11]])


def make_mock(seed, amp_c, amp_m, kind_m, c1_scale=None):
    """One null mock. c1_scale multiplies C_1 of g_diff (None: G['diff_c1_scale'] or 1, i.e. the legacy spectrum)."""
    if c1_scale is None:
        c1_scale = G.get("diff_c1_scale", 1.0)
    rng = np.random.default_rng(seed)
    nalm = len(G["ell"])
    zc, zm = rng.standard_normal((2, nalm)), rng.standard_normal((2, nalm))
    c = G["cand"]
    e1, e2 = rng.standard_normal((2, len(c["peak"])))
    pk = c["peak"] + c["sp"] * e1
    tt = np.maximum(c["total"] + c["si"] * np.where(c["same"], e1, e2), pk)
    nclass = np.bincount(classes(pk, tt), minlength=16)
    logw = G["feats"][2] @ G["D0"]
    gc = field(zc, spectrum(amp_c, "red")) if amp_c > 0 else 0.0
    gm = field(zm, diff_spectrum(amp_m, kind_m, c1_scale)) if amp_m > 0 else 0.0
    joint = np.zeros((4, 4, len(G["pix"])), dtype=np.int64)
    for k in range(1, 16):
        bp, bt = divmod(k, 4)
        if nclass[k] == 0 or (bp == 0 and bt == 0):
            continue
        lw = logw + gc + (gm if bp != bt else 0.0)
        w = np.exp(lw - np.max(lw))
        joint[bp, bt] = rng.multinomial(nclass[k], w / w.sum())
    return joint, nclass


def mock_unit_l1_dipole(seed):
    """Transverse l=1 dipole of g_diff at C_1 = 1 for the mock with this seed (same RNG stream as make_mock)."""
    rng = np.random.default_rng(seed)
    nalm = len(G["ell"])
    rng.standard_normal((2, nalm))  # g_common normals
    return l1_dipole_xy(rng.standard_normal((2, nalm)), 1.0, LMAX)


# ----------------------------------------------------------------------------------------------
# Pure helpers for the C_1 dependence and the amplitude nuisance (tested in
# tests/obsstat/test_r106_radio_null_mocks.py).

def offdiag_fraction_contrast(joint_counts):
    """df = f_off(integrated) - f_off(peak) from 4x4 joint class counts (rows: peak bin, columns: integrated bin)."""
    j = np.asarray(joint_counts, dtype=float)
    if j.ndim == 3:
        j = j.sum(axis=2)
    if j.shape != (4, 4):
        raise ValueError("need 4x4 joint class counts")
    off = ~np.eye(4, dtype=bool)
    f_peak = float(j[1:, :][off[1:, :]].sum() / j[1:, :].sum())
    f_int = float(j[:, 1:][off[:, 1:]].sum() / j[:, 1:].sum())
    return dict(df=f_int - f_peak, f_off_peak=f_peak, f_off_integrated=f_int)


def l1_cov_term(df, c1):
    """First-order l=1 contribution to each diagonal element of the contrast covariance."""
    return df * df * 3.0 * c1 / (4.0 * math.pi)


def closed_form_cov(cov0, df, c1):
    """Cov(C_1) = Cov_{C_1=0} + df^2 (3 C_1/4pi) I_2."""
    return np.asarray(cov0, dtype=float) + l1_cov_term(df, c1) * np.eye(2)


def wald(d, cov):
    d = np.asarray(d, dtype=float)
    return float(d @ np.linalg.solve(np.asarray(cov, dtype=float), d))


def c1_crossing_gaussian(d, cov0, df, alpha, c1_hi):
    """C_1 at which the 2-dof Gaussian tail exp(-W/2) of d under closed_form_cov reaches alpha (W decreases with C_1).

    Returns 0.0 if p >= alpha already at C_1 = 0 and None if p < alpha at c1_hi."""
    target = -2.0 * math.log(alpha)

    def f(c):
        return wald(d, closed_form_cov(cov0, df, c)) - target
    if f(0.0) <= 0:
        return 0.0
    if f(c1_hi) > 0:
        return None
    return float(brentq(f, 0.0, c1_hi, xtol=1e-16, rtol=1e-12, maxiter=500))


def tself_coefficients(delta0, prec, u, df):
    """t_i(C_1) = a_i + 2 b_i sqrt(C_1) + c_i C_1 for delta_i(C_1) = delta0_i + df sqrt(C_1) u_i under precision prec_i."""
    delta0, prec, u = (np.asarray(x, dtype=float) for x in (delta0, prec, u))
    a = np.einsum("ni,nij,nj->n", delta0, prec, delta0)
    b = df * np.einsum("ni,nij,nj->n", delta0, prec, u)
    c = df * df * np.einsum("ni,nij,nj->n", u, prec, u)
    return a, b, c


def tself_curve(coeffs, c1):
    """Matrix (len(c1), n) of t_i at each C_1."""
    a, b, c = coeffs
    s = np.sqrt(np.atleast_1d(np.asarray(c1, dtype=float)))[:, None]
    return a[None, :] + 2.0 * b[None, :] * s + c[None, :] * s * s


def exceed_counts(coeffs, observed, c1):
    return (tself_curve(coeffs, c1) >= observed).sum(axis=1)


def c1_crossing_mc(coeffs, observed, alpha, c1_hi, n_grid=600):
    """Smallest C_1 with p_mc = (k+1)/(n+1) >= alpha (log grid down to 1e-6 c1_hi, then bisection in the bracket).

    Returns (c1 or None, monotone flag of k on the grid)."""
    n = len(coeffs[0])
    grid = np.concatenate([[0.0], np.logspace(math.log10(c1_hi) - 6.0, math.log10(c1_hi), n_grid)])
    k = exceed_counts(coeffs, observed, grid)
    monotone = bool(np.all(np.diff(k) >= 0))
    hit = np.flatnonzero(k + 1 >= alpha * (n + 1))
    if len(hit) == 0:
        return None, monotone
    j = int(hit[0])
    if j == 0:
        return 0.0, monotone
    lo, hi = float(grid[j - 1]), float(grid[j])
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if exceed_counts(coeffs, observed, [mid])[0] + 1 >= alpha * (n + 1):
            hi = mid
        else:
            lo = mid
    return hi, monotone


def amplitude_ratio_quantiles(sigma, q=(0.16, 0.5, 0.84)):
    """Quantiles of the amplitude ratio r ~ N(1, sigma) truncated to r > 0."""
    return truncnorm(-1.0 / sigma, np.inf, loc=1.0, scale=sigma).ppf(q)


def draw_amplitude_ratio(seed, sigma):
    """Deterministic draw of r ~ N(1, sigma) truncated to r > 0 (rejection) from its own seed stream."""
    rng = np.random.default_rng(seed)
    while True:
        r = 1.0 + sigma * rng.standard_normal()
        if r > 0:
            return float(r)


def p_display(k, n):
    """p_mc to two significant figures, with the counts it came from."""
    p = (k + 1) / (n + 1)
    return f"{p:.2g} ({k}/{n})"


def od_summary(values, data):
    v = np.asarray(values, dtype=float)
    return dict(n=len(v), mean=float(v.mean()), sd=float(v.std(ddof=1)) if len(v) > 1 else None, min=float(v.min()),
                max=float(v.max()), data=float(data), frac_ge_data=float(np.mean(v >= data)))


# ----------------------------------------------------------------------------------------------

def calib_task(args):
    seed, amp_c, amp_m, kind_m = args
    t0 = time.time()
    joint, _ = make_mock(seed, amp_c, amp_m, kind_m)
    peak, integ = joint[1:, :, :].sum(axis=1), joint[:, 1:, :].sum(axis=0)
    out = jackknife(peak, integ, 4)
    out["seconds"] = time.time() - t0
    return out


def scale_task(args):
    seed, amp_c, amp_m, kind_m = args
    t0 = time.time()
    joint, _ = make_mock(seed, amp_c, amp_m, kind_m)
    peak, integ = joint[1:, :, :].sum(axis=1), joint[:, 1:, :].sum(axis=0)
    out = {n: jackknife(peak, integ, n) for n in (4, 8)}
    out["seconds"] = time.time() - t0
    return out


def scale_diagnostic(pool, seeds, amp_c, amp_m, kind_m):
    rows = list(pool.map(scale_task, [(s, amp_c, amp_m, kind_m) for s in seeds]))
    res = dict(n=len(rows), seconds=[r["seconds"] for r in rows])
    for key in ("trace_single", "trace_contrast", "wald_self"):
        for n in (4, 8):
            res[f"{key}_nside{n}"] = [r[n][key] for r in rows]
    for key in ("single", "contrast"):
        a4, a8 = np.array(res[f"trace_{key}_nside4"]), np.array(res[f"trace_{key}_nside8"])
        res[f"ratio_{key}_8_over_4_of_means"] = float(a8.mean() / a4.mean())
        res[f"ratio_{key}_8_over_4_per_mock_mean"] = float(np.mean(a8 / a4))
        res[f"ratio_{key}_8_over_4_per_mock_se"] = float(np.std(a8 / a4, ddof=1) / np.sqrt(len(a4)))
    for n in (4, 8):
        w = np.array(res[f"wald_self_nside{n}"])
        res[f"jk_wald_self_nside{n}_vs_observed"] = summarise(w, G["data_scale"][f"jk_wald_self_nside{n}"])
    return res


def main_task(args):
    family, index, seed, amp_c, amp_m, kind_m = args
    t0 = time.time()
    joint, nclass = make_mock(seed, amp_c, amp_m, kind_m)
    res, _, _ = estimator(joint)
    return family, index, res, nclass, time.time() - t0


def followup_mock_task(args):
    """Main-estimator mock with explicit C_1 scale; also off-diagonal overdispersion and the unit l=1 dipole."""
    tag, family, index, seed, amp_c, amp_m, kind_m, c1_scale = args
    t0 = time.time()
    joint, nclass = make_mock(seed, amp_c, amp_m, kind_m, c1_scale)
    res, _, _ = estimator(joint)
    row = dict(tag=tag, family=family, index=index, nclass=nclass, amp_m=amp_m, c1_scale=c1_scale,
               offdiag_od=offdiag_overdispersion(joint), u_l1=mock_unit_l1_dipole(seed))
    for _, m in MODELS:
        r = res[m]
        row[m] = dict(delta=np.asarray(r["delta"]), cov=np.asarray(r["cov"]), od=np.array(r["od"], dtype=float),
                      **{k: r[k] for k in STATS})
    row["seconds"] = time.time() - t0
    return row


def followup_jk_task(args):
    """Jackknife traces (NSIDE in nsides) of one mock with explicit C_1 scale; optionally the main estimator too."""
    tag, family, index, seed, amp_c, amp_m, kind_m, c1_scale, nsides, with_estimator = args
    t0 = time.time()
    joint, _ = make_mock(seed, amp_c, amp_m, kind_m, c1_scale)
    peak, integ = joint[1:, :, :].sum(axis=1), joint[:, 1:, :].sum(axis=0)
    row = dict(tag=tag, family=family, index=index, jk={n: jackknife(peak, integ, n) for n in nsides})
    if with_estimator:
        res, _, _ = estimator(joint)
        row["t_self_dipole"] = res["dipole"]["t_self"]
        row["delta_dipole"] = np.asarray(res["dipole"]["delta"])
    row["seconds"] = time.time() - t0
    return row


def calibrate_level(pool, seeds, amp_c, amp_m, kind_m):
    rows = list(pool.map(calib_task, [(s, amp_c, amp_m, kind_m) for s in seeds]))
    ts = np.array([r["trace_single"] for r in rows])
    tc = np.array([r["trace_contrast"] for r in rows])
    return dict(amp_common=amp_c, amp_diff=amp_m, kind_diff=kind_m, n=len(rows),
                trace_single_mean=float(ts.mean()), trace_single_se=float(ts.std(ddof=1) / np.sqrt(len(ts))),
                trace_contrast_mean=float(tc.mean()), trace_contrast_se=float(tc.std(ddof=1) / np.sqrt(len(tc))),
                jk_wald_self_dipole=[r["wald_self"] for r in rows],
                trace_single=ts.tolist(), trace_contrast=tc.tolist(), seconds=[r["seconds"] for r in rows])


def secant(level0, level1, key, target, amp_key):
    x0, y0 = level0[amp_key], level0[key]
    x1, y1 = level1[amp_key], level1[key]
    if not np.isfinite(y1 - y0) or (y1 - y0) * (target - y0) <= 0 or x1 == x0:
        raise RuntimeError(f"calibration slope unusable for {key}: ({x0},{y0}) ({x1},{y1}) target {target}")
    return float(x0 + (target - y0) * (x1 - x0) / (y1 - y0))


def fit_amplitude(pool, seeds, base, amp_pilot, key, target, vary, kind_m, log):
    """Two-point linear calibration with one secant refinement if the excess misses by >15%."""
    amp_key = "amp_common" if vary == "c" else "amp_diff"
    levels = [base]
    trial = calibrate_level(pool, seeds, *((amp_pilot, 0.0, "red") if vary == "c" else (base["amp_common"], amp_pilot, kind_m)))
    levels.append(trial)
    log(f"  pilot {amp_key}={amp_pilot:.4g}: {key}={trial[key]:.4g}+-{trial[key.replace('mean', 'se')]:.2g} target {target:.4g}")
    amp = secant(base, trial, key, target, amp_key)
    for step in range(2):
        args = (amp, 0.0, "red") if vary == "c" else (base["amp_common"], amp, kind_m)
        check = calibrate_level(pool, seeds, *args)
        levels.append(check)
        log(f"  step{step} {amp_key}={amp:.4g}: {key}={check[key]:.4g}+-{check[key.replace('mean', 'se')]:.2g}")
        miss = abs(check[key] - target) / max(abs(target - base[key]), 1e-30)
        if miss <= 0.15 or step == 1:
            return amp, check, levels, miss
        amp = secant(trial, check, key, target, amp_key)
        trial = check
    raise AssertionError


def summarise(stat, observed):
    s = np.asarray(stat, float)
    k = int(np.count_nonzero(s >= observed))
    return dict(observed=observed, n_mocks=len(s), mocks_ge_observed=k, rank_descending=int(np.count_nonzero(s > observed)) + 1,
                p_mc=(k + 1) / (len(s) + 1), resolution=1 / (len(s) + 1), mean=float(s.mean()),
                p_display=p_display(k, len(s)), p_mc_binomial_se=math.sqrt(((k + 1) / (len(s) + 1)) * (1 - (k + 1) / (len(s) + 1)) / len(s)),
                quantiles_50_90_95_99=np.quantile(s, [.5, .9, .95, .99]).tolist(), max=float(s.max()))


def clean(x):
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    if isinstance(x, np.ndarray):
        return clean(x.tolist())
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, float) and not math.isfinite(x):
        raise ValueError("non-finite value in JSON output")
    return x


def modules_sha256():
    return {m: sha256(Path(p)) for m, p in [("r65_count_quotient", "htt/htt/htt/infer/r65_count_quotient.py"),
                                            ("r65_overlap", "htt/htt/htt/infer/r65_overlap.py"),
                                            ("r105_radio_matched_refits", "scripts/r105/radio_matched_refits.py")]}


def script_path():
    p = Path(__file__)
    return str(p.relative_to(Path.cwd())) if p.is_absolute() and Path.cwd() in p.parents else str(p)


def provenance(argv, inputs):
    def git(*args):
        try:
            return subprocess.run(["git", *args], capture_output=True, text=True, timeout=60).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None
    return dict(script=script_path(), script_sha256=sha256(Path(__file__)), modules_sha256=modules_sha256(),
                command="python -B -m scripts.r106.radio_null_mocks " + " ".join(argv),
                shell_setup=("cd <repo> && export PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 "
                             "MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1"),
                repo_head=git("rev-parse", "HEAD"), script_git_status=git("status", "--porcelain", "--", script_path()),
                python=sys.version.split()[0], platform=platform.platform(), numpy=np.__version__, healpy=hp.__version__,
                scipy=scipy.__version__, root_seed=ROOT_SEED, input_sha256=inputs)


def write_json(path, obj):
    Path(path).write_text(json.dumps(clean(obj), indent=1, allow_nan=False) + "\n")


def run_main(a, logf, log, start):
    """Original R106 D3 pipeline (calibration, shape diagnostic, main mocks)."""
    if a.diff_c1_scale != 1.0 and a.output.resolve() == OUTDIR.resolve():
        raise ValueError("--diff-c1-scale != 1 needs its own --output; the 2000-mock reference results are kept")
    if a.output.resolve() == OUTDIR.resolve() and (OUTDIR / "NVSS_NULL_MOCKS.json").exists() and not a.timing_only and not a.overwrite:
        raise ValueError("refusing to overwrite the 2000-mock reference results; pass --overwrite or another --output")
    G["diff_c1_scale"] = float(a.diff_c1_scale)
    meta = load()
    log(f"loaded: {json.dumps({k: v for k, v in meta.items() if k != 'observed_fits_r65'})}")
    obs, _, _ = estimator(G["joint"])
    replay = {}
    for _, m in MODELS:
        err = float(np.max(np.abs(obs[m]["delta"] - G["delta_r65"][m])))
        rel = abs(obs[m]["t_self"] - G["wald_r65"][m]) / G["wald_r65"][m]
        if err > 2e-9 or rel > 1e-7:
            raise ValueError(f"observed R65 replay failed for {m}: {err} {rel}")
        replay[m] = dict(delta=obs[m]["delta"].tolist(), wald_self=obs[m]["t_self"], max_delta_error=err, wald_rel_error=rel,
                         overdispersion_peak_int=list(obs[m]["od"]))
    log(f"R65 replay: {json.dumps(replay)}")
    ctx = mp.get_context("fork")
    with ProcessPoolExecutor(max_workers=a.workers, mp_context=ctx) as pool:
        t0 = time.time()
        one = list(pool.map(main_task, [("TIMING", i, [ROOT_SEED, 0, i], 1e-4, 1e-3, "red") for i in range(a.workers)]))
        tj = calib_task(([ROOT_SEED, 9, 0], 1e-4, 0.0, "red"))
        log(f"timing: main mock {[round(r[4], 2) for r in one]} s; jackknife mock {tj['seconds']:.2f} s; wall {time.time() - t0:.1f} s")
        if a.timing_only:
            return
        calib = {}
        cseeds = [[ROOT_SEED, 100, i] for i in range(a.calib_mocks)]
        log("calibration LSS_COMMON (target: single-selection NSIDE4 jackknife trace)")
        zero = calibrate_level(pool, cseeds, 0.0, 0.0, "red")
        log(f"  A=0: single {zero['trace_single_mean']:.4g}+-{zero['trace_single_se']:.2g} contrast {zero['trace_contrast_mean']:.4g}+-{zero['trace_contrast_se']:.2g}")
        amp_c, base, levels, miss = fit_amplitude(pool, cseeds, zero, a.pilot_common, "trace_single_mean",
                                                  G["target_single"], "c", "red", log)
        calib["LSS_COMMON"] = dict(amp_common=amp_c, amp_diff=0.0, kind_diff=None, target="trace_single_mean",
                                   target_value=G["target_single"], relative_excess_miss=miss, final=base, levels=[zero] + levels)
        log(f"  LSS_COMMON contrast jackknife trace at fitted A_c: {base['trace_contrast_mean']:.4g} (data {G['target_contrast']:.4g})")
        for fam, kind, pilot in (("LSS_DIFF_RED", "red", a.pilot_red), ("LSS_DIFF_MID", "mid", a.pilot_mid),
                                 ("LSS_DIFF_FLAT", "flat", a.pilot_flat)):
            if fam not in a.families:
                continue
            log(f"calibration {fam} (target: contrast NSIDE4 jackknife trace)")
            amp_m, fin, lv, miss = fit_amplitude(pool, cseeds, base, pilot, "trace_contrast_mean",
                                                 G["target_contrast"], "m", kind, log)
            calib[fam] = dict(amp_common=amp_c, amp_diff=amp_m, kind_diff=kind, target="trace_contrast_mean",
                              target_value=G["target_contrast"], relative_excess_miss=miss, final=fin, levels=lv)
        log(f"calibration done at {time.time() - start:.1f} s")
        fams = [f for f in a.families if f in calib]
        sseeds = [[ROOT_SEED, 200, i] for i in range(a.scale_mocks)]
        for f in fams:
            c = calib[f]
            c["scale_diagnostic"] = scale_diagnostic(pool, sseeds, c["amp_common"], c["amp_diff"], c["kind_diff"] or "red")
            sd = c["scale_diagnostic"]
            log(f"  scale {f}: contrast jk8/jk4 {sd['ratio_contrast_8_over_4_of_means']:.3f} (data {G['data_scale']['ratio_contrast_8_over_4']:.3f}); "
                f"single {sd['ratio_single_8_over_4_of_means']:.3f} (data {G['data_scale']['ratio_single_8_over_4']:.3f}); "
                f"jk4 trace contrast {np.mean(sd['trace_contrast_nside4']):.4g}")
        log(f"scale diagnostics done at {time.time() - start:.1f} s")
        draws = {f: [] for f in fams}
        index = 0
        chunk = 6 * a.workers
        while index < a.max_mocks:
            elapsed = time.time() - start
            per = np.mean([r[3] for f in fams for r in draws[f]]) if any(draws[f] for f in fams) else 1.0
            if elapsed + per * chunk * len(fams) / a.workers * 1.1 > a.budget_seconds:
                break
            tasks = [(f, i, [ROOT_SEED, FAMILIES[f], i], calib[f]["amp_common"], calib[f]["amp_diff"], calib[f]["kind_diff"] or "red")
                     for i in range(index, min(index + chunk, a.max_mocks)) for f in fams]
            for f, i, res, nclass, sec in pool.map(main_task, tasks):
                draws[f].append((i, res, nclass, sec))
            index += chunk
            log(f"mocks per family completed: {index} ({', '.join(f'{f}={len(draws[f])}' for f in fams)})")
    out = dict(schema="htt.r106.radio_null_mocks/1", script=script_path(),
               script_sha256=sha256(Path(__file__)), modules_sha256=modules_sha256(),
               python=sys.version.split()[0], platform=platform.platform(), numpy=np.__version__, healpy=hp.__version__,
               inputs=meta, observed_replay=replay, root_seed=ROOT_SEED, family_labels=FAMILY_LABELS,
               mock_design=dict(spectrum_common=f"C_l = A_c * l^{SLOPE}, 1<=l<={LMAX}", spectrum_diff_red=f"C_l = A_m * l^{SLOPE}",
                                spectrum_diff_flat=f"C_l = A_m for 1<=l<={FLAT_LMAX}",
                                spectrum_diff_mid=f"C_l = A_m * l^{MID_SLOPE}", diff_c1_scale=float(a.diff_c1_scale),
                                diff_c1_note="C_1 of g_diff = diff_c1_scale * (power-law value at l=1 = A_m); "
                                             "the NSIDE4/8 jackknife calibration is insensitive to C_1",
                                lognormal="intensity exp(g), normalised per class",
                                diff_classes="off-diagonal joint classes (peak bin != integrated bin): resolved/migrating components",
                                dipole="common exp(D0.n_xy) for every class", flux_scatter="provider 1-sigma; shared deviate if integrated==peak, else independent; integrated>=peak enforced",
                                totals="each class total fixed by the perturbed footprint catalogue; pixel placement multinomial"),
               targets=dict(single_trace_nside4=G["target_single"], contrast_trace_nside4=G["target_contrast"],
                            r65_poisson_contrast_trace={m: float(np.trace(G["cov_fixed"][m])) for _, m in MODELS}),
               data_jackknife_scale=G["data_scale"], calibration=calib, families={})
    arrays = {}
    for f in fams:
        rows = sorted(draws[f], key=lambda r: r[0])
        if not rows:
            continue
        fam = dict(n_mocks=len(rows), label=FAMILY_LABELS[f], amp_common=calib[f]["amp_common"], amp_diff=calib[f]["amp_diff"],
                   kind_diff=calib[f]["kind_diff"], mean_seconds_per_mock=float(np.mean([r[3] for r in rows])),
                   mean_class_counts=np.mean([r[2] for r in rows], axis=0).reshape(4, 4).tolist(), models={})
        arrays[f"{f}_index"] = np.array([r[0] for r in rows])
        arrays[f"{f}_class_counts"] = np.array([r[2] for r in rows])
        for _, m in MODELS:
            d = np.array([r[1][m]["delta"] for r in rows])
            stats_ = {k: np.array([r[1][m][k] for r in rows]) for k in STATS}
            od = np.array([r[1][m]["od"] for r in rows])
            arrays.update({f"{f}_{m}_delta": d, f"{f}_{m}_od": od,
                           f"{f}_{m}_est_peak": np.array([r[1][m]["est_peak"] for r in rows]),
                           f"{f}_{m}_est_int": np.array([r[1][m]["est_int"] for r in rows]),
                           **{f"{f}_{m}_{k}": v for k, v in stats_.items()}})
            cmock = np.cov(d.T)
            dobs = obs[m]["delta"]
            wm = np.einsum("ni,ij,nj->n", d, np.linalg.inv(cmock), d)
            fam["models"][m] = dict(
                mock_delta_mean=d.mean(0).tolist(), mock_delta_mean_se=(d.std(0, ddof=1) / np.sqrt(len(d))).tolist(),
                mock_delta_covariance=cmock.tolist(),
                mock_cov_trace_over_r65_poisson=float(np.trace(cmock) / np.trace(G["cov_fixed"][m])),
                mock_cov_trace_over_r105_jk4=float(np.trace(cmock) / np.trace(G["cov_jk"]["4", m])),
                mean_overdispersion_peak_int=od.mean(0).tolist(), observed_overdispersion_peak_int=list(obs[m]["od"]),
                **{STAT_NAMES[k]: summarise(stats_[k], obs[m][k]) for k in STATS},
                observed_wald_under_mock_covariance=float(dobs @ np.linalg.solve(cmock, dobs)),
                rank_vs_mock_covariance_walds=summarise(wm, float(dobs @ np.linalg.solve(cmock, dobs))))
        out["families"][f] = fam
    out["elapsed_seconds"] = time.time() - start
    ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rc = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    out["peak_rss_kB"] = dict(parent=ru, largest_child=rc)
    out["scope"] = SCOPE
    write_json(a.output / "NVSS_NULL_MOCKS.json", out)
    np.savez_compressed(a.output / "NVSS_NULL_MOCK_DRAWS.npz", **arrays)
    log(f"wrote {a.output / 'NVSS_NULL_MOCKS.json'} elapsed {out['elapsed_seconds']:.1f} s")


SCOPE = ("Null mocks are Cox processes with positions independent of the flux pair; the common dipole cancels in the "
         "contrast by construction. Clustering amplitudes are fitted to the data's own NSIDE=4 delete-one jackknife "
         "traces (one sky); the angular shape of each field is assumed, not fitted. The DIFF families are empirical "
         "differential-selection (excess-variance) fields on the resolved/migrating classes, not large-scale structure, "
         "and are not jointly calibrated (their single-selection jackknife trace exceeds the data target). Their C_1 is "
         "the power law extrapolated to l=1; the NSIDE=4/8 jackknife traces and the NSIDE8/4 ratio are insensitive to the "
         "transverse l=1 mode, which lies inside the fitted log-linear model, while that mode sets most of the null "
         "contrast covariance. Every p_mc is therefore conditional on an assumed C_1 (a random resolved-fraction dipole of "
         "per-component RMS sqrt(3 C_1/4pi)); no family's p_mc is the LSS/selection-null p-value, and C_1 = 0 is not a "
         "conservative limit. The mocks do not model source multiplicity, spatially varying flux calibration or a physical "
         "redshift-dependent bias, and they under-predict the data's per-selection pixel overdispersion. No physical Pi or "
         "Bianchi inference is made.")


# ----------------------------------------------------------------------------------------------
# R106 review follow-up stages.

def load_reference(path):
    path = Path(path)
    npz = path.with_name("NVSS_NULL_MOCK_DRAWS.npz")
    js = json.loads(path.read_text())
    with np.load(npz, allow_pickle=False) as z:
        arrays = {k: z[k] for k in z.files}
    return dict(json=js, npz=arrays, path=str(path), sha={"reference_json": sha256(path), "reference_npz": sha256(npz)})


def family_params(ref, f):
    c = ref["json"]["calibration"][f]
    return float(c["amp_common"]), float(c["amp_diff"]), (c["kind_diff"] or "red")


def stack_rows(rows):
    rows = sorted(rows, key=lambda r: r["index"])
    out = dict(index=np.array([r["index"] for r in rows]), nclass=np.array([r["nclass"] for r in rows]),
               offdiag_od=np.array([r["offdiag_od"] for r in rows]), u_l1=np.array([r["u_l1"] for r in rows]),
               amp_m=np.array([r["amp_m"] for r in rows]), seconds=np.array([r["seconds"] for r in rows]))
    for _, m in MODELS:
        out[f"{m}_delta"] = np.array([r[m]["delta"] for r in rows])
        out[f"{m}_cov"] = np.array([r[m]["cov"] for r in rows])
        out[f"{m}_od"] = np.array([r[m]["od"] for r in rows])
        for k in STATS:
            out[f"{m}_{k}"] = np.array([r[m][k] for r in rows])
    return out


def group(rows, tag, family):
    return stack_rows([r for r in rows if r["tag"] == tag and r["family"] == family])


def observed_state():
    obs, _, _ = estimator(G["joint"])
    for _, m in MODELS:
        err = float(np.max(np.abs(obs[m]["delta"] - G["delta_r65"][m])))
        rel = abs(obs[m]["t_self"] - G["wald_r65"][m]) / G["wald_r65"][m]
        if err > 2e-9 or rel > 1e-7:
            raise ValueError(f"observed R65 replay failed for {m}: {err} {rel}")
    obs["offdiag_od"] = offdiag_overdispersion(G["joint"])
    return obs


def ensemble_summary(arr, obs, label):
    """p summaries for every statistic and model, mock-covariance Wald, overdispersion, for one stacked ensemble."""
    out = dict(label=label, n_mocks=int(len(arr["index"])), mean_seconds_per_mock=float(arr["seconds"].mean()),
               offdiag_overdispersion=od_summary(arr["offdiag_od"], obs["offdiag_od"]), models={})
    for _, m in MODELS:
        d = arr[f"{m}_delta"]
        cm = np.cov(d.T)
        w = wald(obs[m]["delta"], cm)
        out["models"][m] = dict(
            **{STAT_NAMES[k]: summarise(arr[f"{m}_{k}"], obs[m][k]) for k in STATS},
            mock_delta_mean=d.mean(0), mock_delta_mean_se=d.std(0, ddof=1) / math.sqrt(len(d)), mock_delta_covariance=cm,
            mock_cov_trace_over_r65_poisson=float(np.trace(cm) / np.trace(G["cov_fixed"][m])),
            observed_wald_under_mock_covariance=w, gaussian_p_exp_minus_w_over_2=math.exp(-w / 2),
            overdispersion_peak=od_summary(arr[f"{m}_od"][:, 0], obs[m]["od"][0]),
            overdispersion_integrated=od_summary(arr[f"{m}_od"][:, 1], obs[m]["od"][1]))
    return out


def save_arrays(path, groups):
    flat = {}
    for name, arr in groups.items():
        for k, v in arr.items():
            flat[f"{name}__{k}"] = v
    np.savez_compressed(path, **flat)


def load_arrays(path):
    out = {}
    with np.load(path, allow_pickle=False) as z:
        for k in z.files:
            name, key = k.split("__", 1)
            out.setdefault(name, {})[key] = z[k]
    return out


def stage_c1zero(a, pool, ref, obs, log):
    """F1/F2/F5: DIFF families at C_1 = 0 on the main-run seeds; nominal replay subset; jackknife insensitivity."""
    par = {f: family_params(ref, f) for f in FAMILIES}
    tasks = ([("nominal", f, i, [ROOT_SEED, FAMILIES[f], i], *par[f], 1.0) for f in FAMILIES for i in range(a.n_nominal)] +
             [("c1zero", f, i, [ROOT_SEED, FAMILIES[f], i], *par[f], 0.0) for f in DIFF_FAMILIES for i in range(a.n_mocks)])
    t0 = time.time()
    rows = list(pool.map(followup_mock_task, tasks, chunksize=8))
    log(f"c1zero: {len(rows)} main-estimator mocks in {time.time() - t0:.1f} s")
    cal = ref["json"]["calibration"]
    n_cal = min(int(cal[f]["final"]["n"]) for f in DIFF_FAMILIES)
    n_scale = min(int(cal[f]["scale_diagnostic"]["n"]) for f in DIFF_FAMILIES)
    if a.n_jk_check is not None:
        n_cal, n_scale = min(n_cal, a.n_jk_check), min(n_scale, a.n_jk_check)
    jtasks = ([("calib_c1zero", f, i, [ROOT_SEED, 100, i], *par[f], 0.0, (4,), False) for f in DIFF_FAMILIES for i in range(n_cal)] +
              [("scale_c1zero", f, i, [ROOT_SEED, 200, i], *par[f], 0.0, (4, 8), False) for f in DIFF_FAMILIES for i in range(n_scale)])
    t0 = time.time()
    jrows = list(pool.map(followup_jk_task, jtasks))
    log(f"c1zero: {len(jrows)} jackknife mocks in {time.time() - t0:.1f} s")
    groups, fams, determinism, jk = {}, {}, {}, {}
    npz = ref["npz"]
    for f in FAMILIES:
        nom = group(rows, "nominal", f)
        groups[f"nominal_{f}"] = nom
        n = len(nom["index"])
        determinism[f] = {m: dict(n=n, max_abs_delta_vs_reference=float(np.max(np.abs(nom[f"{m}_delta"] - npz[f"{f}_{m}_delta"][:n]))),
                                  max_abs_t_self_vs_reference=float(np.max(np.abs(nom[f"{m}_t_self"] - npz[f"{f}_{m}_t_self"][:n]))))
                          for _, m in MODELS}
        fams[f"nominal_{f}"] = ensemble_summary(nom, obs, f"{FAMILY_LABELS[f]} nominal (C_1 = A_m), replay subset")
    for f in DIFF_FAMILIES:
        z0 = group(rows, "c1zero", f)
        groups[f"c1zero_{f}"] = z0
        s = ensemble_summary(z0, obs, f"{FAMILY_LABELS[f]} with C_1 = 0 (l>=2 spectrum at the reference A_m)")
        s.update(amp_common=par[f][0], amp_diff=par[f][1], kind_diff=par[f][2], c1_nominal=par[f][1], c1_run=0.0)
        fams[f"c1zero_{f}"] = s
        cj = sorted([r for r in jrows if r["tag"] == "calib_c1zero" and r["family"] == f], key=lambda r: r["index"])
        sj = sorted([r for r in jrows if r["tag"] == "scale_c1zero" and r["family"] == f], key=lambda r: r["index"])
        ref_cal = np.array(cal[f]["final"]["trace_contrast"][:len(cj)])
        ref_cal_single = np.array(cal[f]["final"]["trace_single"][:len(cj)])
        z_cal = np.array([r["jk"][4]["trace_contrast"] for r in cj])
        z_cal_single = np.array([r["jk"][4]["trace_single"] for r in cj])
        sd = cal[f]["scale_diagnostic"]
        r4, r8 = np.array(sd["trace_contrast_nside4"][:len(sj)]), np.array(sd["trace_contrast_nside8"][:len(sj)])
        z4 = np.array([r["jk"][4]["trace_contrast"] for r in sj])
        z8 = np.array([r["jk"][8]["trace_contrast"] for r in sj])
        jk[f] = dict(
            calibration_seeds=dict(n=len(cj), seeds="[ROOT_SEED, 100, i]",
                                   jk4_contrast_trace_c1zero=z_cal, jk4_contrast_trace_reference=ref_cal,
                                   mean_c1zero=float(z_cal.mean()), mean_reference=float(ref_cal.mean()),
                                   mean_ratio_c1zero_over_reference=float(z_cal.mean() / ref_cal.mean()),
                                   jk4_single_trace_mean_ratio_c1zero_over_reference=float(z_cal_single.mean() / ref_cal_single.mean()),
                                   data_target=G["target_contrast"]),
            scale_seeds=dict(n=len(sj), seeds="[ROOT_SEED, 200, i]",
                             jk4_c1zero=z4, jk8_c1zero=z8, jk4_reference=r4, jk8_reference=r8,
                             ratio_8_over_4_of_means_c1zero=float(z8.mean() / z4.mean()),
                             ratio_8_over_4_of_means_reference=float(r8.mean() / r4.mean()),
                             ratio_8_over_4_per_mock_c1zero=z8 / z4, ratio_8_over_4_per_mock_reference=r8 / r4,
                             data_ratio=G["data_scale"]["ratio_contrast_8_over_4"]),
            seconds=[r["seconds"] for r in cj + sj])
    summary = dict(determinism_vs_reference=determinism, ensembles=fams, jackknife_c1_insensitivity=jk,
                   observed=dict(offdiag_overdispersion=obs["offdiag_od"],
                                 **{m: dict(delta=obs[m]["delta"], t_self=obs[m]["t_self"], od=obs[m]["od"]) for _, m in MODELS}))
    return summary, groups


def stage_amplitude(a, pool, ref, obs, log):
    """F3: amplitude nuisance from the jk4-trace scatter plus calibration MC error; marginal and 16/84% ensembles."""
    par = {f: family_params(ref, f) for f in DIFF_FAMILIES}
    cal = ref["json"]["calibration"]
    t0 = time.time()
    jrows = list(pool.map(followup_jk_task, [("amp_jk", f, i, [ROOT_SEED, 300, i], *par[f], 1.0, (4,), True)
                                             for f in DIFF_FAMILIES for i in range(a.n_jk)]))
    log(f"amplitude: {len(jrows)} jackknife+estimator mocks in {time.time() - t0:.1f} s")
    target, base = G["target_contrast"], float(cal["LSS_COMMON"]["final"]["trace_contrast_mean"])
    excess = target - base
    nuisance = {}
    for f in DIFF_FAMILIES:
        rr = sorted([r for r in jrows if r["family"] == f], key=lambda r: r["index"])
        new = np.array([r["jk"][4]["trace_contrast"] for r in rr])
        new_single = np.array([r["jk"][4]["trace_single"] for r in rr])
        tself = np.array([r["t_self_dipole"] for r in rr])
        old = np.array(cal[f]["final"]["trace_contrast"] + cal[f]["scale_diagnostic"]["trace_contrast_nside4"])
        pooled = np.concatenate([new, old])
        sd_t = float(pooled.std(ddof=1))
        sd_a = sd_t / excess
        se_cal = float(cal[f]["final"]["trace_contrast_se"]) / excess
        sigma = math.hypot(sd_a, se_cal)
        q = amplitude_ratio_quantiles(sigma)
        rho = spearmanr(new, tself)
        nuisance[f] = dict(
            n_new_jk_mocks=len(new), n_reference_jk_mocks=len(old), jk4_contrast_trace_new=new,
            jk4_contrast_trace_new_mean=float(new.mean()), jk4_contrast_trace_new_rel_sd=float(new.std(ddof=1) / new.mean()),
            jk4_contrast_trace_pooled_mean=float(pooled.mean()), jk4_contrast_trace_pooled_sd=sd_t,
            jk4_contrast_trace_pooled_rel_sd=float(sd_t / pooled.mean()),
            data_target=target, common_only_base=base, excess=excess,
            amplitude_rel_sd_from_trace_scatter=sd_a, calibration_mc_rel_se=se_cal, sigma_r=sigma,
            calibration_relative_excess_miss=float(cal[f]["relative_excess_miss"]),
            r_quantiles_16_50_84=q, spearman_jk4_trace_vs_t_self_dipole=dict(rho=float(rho.statistic), p=float(rho.pvalue), n=len(new)),
            single_selection_jk4_trace_new_mean=float(new_single.mean()), single_selection_target=G["target_single"],
            single_selection_ratio_to_target=float(new_single.mean() / G["target_single"]))
        log(f"  {f}: jk4 rel sd new {nuisance[f]['jk4_contrast_trace_new_rel_sd']:.3f} pooled {nuisance[f]['jk4_contrast_trace_pooled_rel_sd']:.3f}; "
            f"sd_A {sd_a:.3f} se_cal {se_cal:.3f} sigma_r {sigma:.3f}; r16/50/84 {np.round(q, 3).tolist()}")
    tasks = []
    for f in DIFF_FAMILIES:
        ac, am, kind = par[f]
        sg = nuisance[f]["sigma_r"]
        r16, _, r84 = nuisance[f]["r_quantiles_16_50_84"]
        tasks += [("marginal", f, i, [ROOT_SEED, FAMILIES[f], i], ac, am * draw_amplitude_ratio([ROOT_SEED, 500, FAMILIES[f], i], sg), kind, 1.0)
                  for i in range(a.n_mocks)]
        tasks += [("r16", f, i, [ROOT_SEED, FAMILIES[f], i], ac, am * float(r16), kind, 1.0) for i in range(a.n_band)]
        tasks += [("r84", f, i, [ROOT_SEED, FAMILIES[f], i], ac, am * float(r84), kind, 1.0) for i in range(a.n_band)]
    t0 = time.time()
    rows = list(pool.map(followup_mock_task, tasks, chunksize=8))
    log(f"amplitude: {len(rows)} main-estimator mocks in {time.time() - t0:.1f} s")
    groups, ens = {}, {}
    for f in DIFF_FAMILIES:
        for tag in ("marginal", "r16", "r84"):
            arr = group(rows, tag, f)
            groups[f"{tag}_{f}"] = arr
            s = ensemble_summary(arr, obs, f"{FAMILY_LABELS[f]} amplitude {tag}")
            s["amp_ratio_mean"] = float(arr["amp_m"].mean() / par[f][1])
            s["amp_ratio_sd"] = float(arr["amp_m"].std(ddof=1) / par[f][1]) if len(arr["amp_m"]) > 1 else 0.0
            ens[f"{tag}_{f}"] = s
    return dict(nuisance=nuisance, ensembles=ens, jk_seconds=[r["seconds"] for r in jrows]), groups


def c1_analysis(ref, z0groups, obs, df_info, a):
    """Closed-form p versus C_1, crossings with bootstrap intervals, and validation against the reference (C_1 = A_m)."""
    df = df_info["df"]
    npz = ref["npz"]
    grid_abs = sorted(set([0.0, 1e-5, 2e-5, 5e-5, 1e-4, 2e-4, 3e-4, 5e-4, 7e-4, 1e-3, 1.5e-3, 2e-3, 3e-3, 5e-3, 7e-3,
                           1e-2, 1.5e-2, 2e-2, 3e-2, 5e-2] + [family_params(ref, f)[1] for f in DIFF_FAMILIES]))
    rng = np.random.default_rng([ROOT_SEED, 900])
    out = {}
    for f in DIFF_FAMILIES:
        z0 = z0groups[f"c1zero_{f}"]
        am = family_params(ref, f)[1]
        n = len(z0["index"])
        boot_idx = rng.integers(0, n, size=(a.n_boot, n))
        fam = dict(label=FAMILY_LABELS[f], A_m=am, C1_nominal=am, n_c1zero_mocks=n,
                   rms_dipole_per_component_at_nominal_C1=math.sqrt(3 * am / (4 * math.pi)), models={})
        for _, m in MODELS:
            d0, u = z0[f"{m}_delta"], z0["u_l1"]
            prec = np.linalg.inv(z0[f"{m}_cov"])
            prec = 0.5 * (prec + np.transpose(prec, (0, 2, 1)))
            coeffs = tself_coefficients(d0, prec, u, df)
            cov0 = np.cov(d0.T)
            dob, tob = np.asarray(obs[m]["delta"]), float(obs[m]["t_self"])
            curve = []
            k_grid = exceed_counts(coeffs, tob, grid_abs)
            for c1, k in zip(grid_abs, k_grid):
                w = wald(dob, closed_form_cov(cov0, df, c1))
                curve.append(dict(C1=c1, C1_over_A_m=c1 / am, rms_dipole_per_component=math.sqrt(3 * c1 / (4 * math.pi)),
                                  closed_form_cov_trace_over_r65_poisson=float(np.trace(closed_form_cov(cov0, df, c1)) / np.trace(G["cov_fixed"][m])),
                                  gaussian_wald=w, gaussian_p=math.exp(-w / 2),
                                  t_self_semi_analytic_k=int(k), t_self_semi_analytic_p_mc=(int(k) + 1) / (n + 1),
                                  t_self_semi_analytic_p_display=p_display(int(k), n)))
            crossings = {}
            for alpha in ALPHAS:
                cg = c1_crossing_gaussian(dob, cov0, df, alpha, a.c1_hi)
                cm_, mono = c1_crossing_mc(coeffs, tob, alpha, a.c1_hi)
                bg, bm = [], []
                for idx in boot_idx:
                    bg.append(c1_crossing_gaussian(dob, np.cov(d0[idx].T), df, alpha, a.c1_hi))
                    bm.append(c1_crossing_mc(tuple(x[idx] for x in coeffs), tob, alpha, a.c1_hi, n_grid=200)[0])

                def pct(v):
                    v = np.array([x for x in v if x is not None], dtype=float)
                    return dict(n_finite=len(v), p16_50_84=np.percentile(v, [16, 50, 84]).tolist() if len(v) else None)
                crossings[str(alpha)] = dict(
                    gaussian_closed_form_C1=cg, gaussian_C1_over_A_m=None if cg is None else cg / am,
                    gaussian_rms_dipole=None if cg is None else math.sqrt(3 * cg / (4 * math.pi)),
                    gaussian_bootstrap_C1=pct(bg),
                    t_self_semi_analytic_C1=cm_, t_self_semi_analytic_C1_over_A_m=None if cm_ is None else cm_ / am,
                    t_self_semi_analytic_rms_dipole=None if cm_ is None else math.sqrt(3 * cm_ / (4 * math.pi)),
                    t_self_semi_analytic_bootstrap_C1=pct(bm), t_self_k_monotone_on_grid=mono)
            # validation at C_1 = A_m against the reference ensemble (same seeds)
            dref, tref = npz[f"{f}_{m}_delta"][:n], npz[f"{f}_{m}_t_self"][:n]
            pred = df * math.sqrt(am) * u
            diff = dref - d0
            slope = float(np.sum(diff * pred) / np.sum(pred * pred))
            resid = diff - pred
            t_pred = tself_curve(coeffs, [am])[0]
            k_pred, k_ref = int(np.sum(t_pred >= tob)), int(np.sum(tref >= tob))
            full = npz[f"{f}_{m}_delta"]
            cov_ref_full = np.cov(full.T)
            cf = closed_form_cov(cov0, df, am)
            fam["models"][m] = dict(
                observed_delta=dob, observed_abs_delta=float(np.linalg.norm(dob)), observed_t_self=tob,
                cov_c1zero=cov0, cov_c1zero_trace_over_r65_poisson=float(np.trace(cov0) / np.trace(G["cov_fixed"][m])),
                p_versus_C1=curve, crossings=crossings,
                validation_at_C1_equals_A_m=dict(
                    n_paired=n, per_mock_delta_shift_regression_slope=slope,
                    per_mock_delta_shift_correlation=float(np.corrcoef(diff.ravel(), pred.ravel())[0, 1]),
                    per_mock_residual_rms_over_predicted_rms=float(np.sqrt(np.mean(resid ** 2)) / np.sqrt(np.mean(pred ** 2))),
                    t_self_predicted_vs_reference_spearman=float(spearmanr(t_pred, tref).statistic),
                    k_ge_observed_predicted=k_pred, k_ge_observed_reference_paired=k_ref,
                    p_predicted=p_display(k_pred, n), p_reference_paired=p_display(k_ref, n),
                    p_reference_full=p_display(int(np.sum(npz[f"{f}_{m}_t_self"] >= tob)), len(full)),
                    exceedance_agreement=dict(both=int(np.sum((t_pred >= tob) & (tref >= tob))),
                                              predicted_only=int(np.sum((t_pred >= tob) & (tref < tob))),
                                              reference_only=int(np.sum((t_pred < tob) & (tref >= tob)))),
                    closed_form_cov_trace=float(np.trace(cf)), reference_full_cov_trace=float(np.trace(cov_ref_full)),
                    closed_form_over_reference_trace=float(np.trace(cf) / np.trace(cov_ref_full)),
                    closed_form_cov=cf, reference_full_cov=cov_ref_full,
                    gaussian_wald_closed_form=wald(dob, cf), gaussian_wald_reference_full=wald(dob, cov_ref_full),
                    gaussian_p_closed_form=math.exp(-wald(dob, cf) / 2), gaussian_p_reference_full=math.exp(-wald(dob, cov_ref_full) / 2)))
        out[f] = fam
    return out


def stage_validate(a, pool, ref, obs, log):
    """F1: direct mocks at the semi-analytic C_1 where p(t_self, dipole) crosses 0.05 (l>=2 spectrum at the reference A_m)."""
    z0groups = load_arrays(a.followup_dir / "C1ZERO_DRAWS.npz")
    if a.n_mocks > min(len(z0groups[f"c1zero_{f}"]["index"]) for f in DIFF_FAMILIES):
        raise ValueError("validate --n-mocks exceeds the C_1 = 0 ensemble it is paired with")
    df_info = offdiag_fraction_contrast(G["joint"])
    analysis = c1_analysis(ref, z0groups, obs, df_info, a)
    par = {f: family_params(ref, f) for f in DIFF_FAMILIES}
    targets = {}
    for f in DIFF_FAMILIES:
        c1 = analysis[f]["models"]["dipole"]["crossings"]["0.05"]["t_self_semi_analytic_C1"]
        if c1 is None or c1 <= 0:
            targets[f] = dict(C1=None, skipped=f"no positive 0.05 crossing below --c1-hi (semi-analytic value {c1})")
            log(f"validate: {f} skipped ({targets[f]['skipped']})")
            continue
        targets[f] = dict(C1=c1, c1_scale=c1 / par[f][1])
    run = [f for f in DIFF_FAMILIES if targets[f]["C1"] is not None]
    tasks = [("validate", f, i, [ROOT_SEED, FAMILIES[f], i], *par[f], targets[f]["c1_scale"])
             for f in run for i in range(a.n_mocks)]
    t0 = time.time()
    rows = list(pool.map(followup_mock_task, tasks, chunksize=8))
    log(f"validate: {len(rows)} main-estimator mocks in {time.time() - t0:.1f} s")
    groups, res = {}, {}
    df = df_info["df"]
    for f in run:
        v = group(rows, "validate", f)
        groups[f"validate_{f}"] = v
        z0 = z0groups[f"c1zero_{f}"]
        n = len(v["index"])
        c1 = targets[f]["C1"]
        s = ensemble_summary(v, obs, f"{FAMILY_LABELS[f]} at C_1 = {c1:.4g} (closed-form 0.05 crossing)")
        s.update(C1=c1, c1_scale=targets[f]["c1_scale"], rms_dipole_per_component=math.sqrt(3 * c1 / (4 * math.pi)))
        for _, m in MODELS:
            d0 = z0[f"{m}_delta"][:n]
            prec = np.linalg.inv(z0[f"{m}_cov"][:n])
            coeffs = tself_coefficients(d0, 0.5 * (prec + np.transpose(prec, (0, 2, 1))), z0["u_l1"][:n], df)
            tob = float(obs[m]["t_self"])
            t_pred = tself_curve(coeffs, [c1])[0]
            pred = df * math.sqrt(c1) * z0["u_l1"][:n]
            diff = v[f"{m}_delta"] - d0
            cov0_all = np.cov(z0[f"{m}_delta"].T)
            cf = closed_form_cov(cov0_all, df, c1)
            k_pred, k_dir = int(np.sum(t_pred >= tob)), int(np.sum(v[f"{m}_t_self"] >= tob))
            s["models"][m]["closed_form_check"] = dict(
                n_paired=n, k_ge_observed_direct=k_dir, k_ge_observed_semi_analytic=k_pred,
                p_direct=p_display(k_dir, n), p_semi_analytic=p_display(k_pred, n),
                p_direct_value=(k_dir + 1) / (n + 1), p_direct_binomial_se=math.sqrt(((k_dir + 1) / (n + 1)) * (1 - (k_dir + 1) / (n + 1)) / n),
                t_self_semi_analytic_vs_direct_spearman=float(spearmanr(t_pred, v[f"{m}_t_self"]).statistic),
                per_mock_delta_shift_regression_slope=float(np.sum(diff * pred) / np.sum(pred * pred)),
                per_mock_residual_rms_over_predicted_rms=float(np.sqrt(np.mean((diff - pred) ** 2)) / np.sqrt(np.mean(pred ** 2))),
                closed_form_cov_trace=float(np.trace(cf)), direct_cov_trace=float(np.trace(np.cov(v[f"{m}_delta"].T))),
                closed_form_over_direct_trace=float(np.trace(cf) / np.trace(np.cov(v[f"{m}_delta"].T))),
                gaussian_wald_closed_form=wald(obs[m]["delta"], cf),
                gaussian_wald_direct=wald(obs[m]["delta"], np.cov(v[f"{m}_delta"].T)))
        res[f] = s
    return dict(targets=targets, ensembles=res), groups


def run_followup_stage(a, log, start):
    stage = a.followup
    a.followup_dir.mkdir(parents=True, exist_ok=True)
    ref = load_reference(a.reference)
    meta = load()
    if meta["input_sha256"] != ref["json"]["inputs"]["input_sha256"]:
        raise ValueError("reference run used different input files")
    obs = observed_state()
    log(f"{stage}: loaded; reference {ref['path']} sha {ref['sha']['reference_json'][:12]}; data offdiag OD {obs['offdiag_od']:.4f}")
    inputs = dict(meta["input_sha256"], **ref["sha"])
    if stage == "validate":
        inputs["c1zero_npz"] = sha256(a.followup_dir / "C1ZERO_DRAWS.npz")
        inputs["c1zero_json"] = sha256(a.followup_dir / "C1ZERO.json")
    ctx = mp.get_context("fork")
    with ProcessPoolExecutor(max_workers=a.workers, mp_context=ctx) as pool:
        if stage == "c1zero":
            summary, groups = stage_c1zero(a, pool, ref, obs, log)
            name, corr = "C1ZERO", ["F1", "F2", "F5"]
        elif stage == "amplitude":
            summary, groups = stage_amplitude(a, pool, ref, obs, log)
            name, corr = "AMPLITUDE_NUISANCE", ["F3", "F4"]
        elif stage == "validate":
            summary, groups = stage_validate(a, pool, ref, obs, log)
            name, corr = "C1_VALIDATION", ["F1"]
        else:
            raise ValueError(stage)
    out = dict(schema=f"htt.r106.radio_null_mocks.followup.{stage}/1", stage=stage, provenance=provenance(sys.argv[1:], inputs),
               family_labels=FAMILY_LABELS, reference_amplitudes={f: family_params(ref, f) for f in FAMILIES},
               settings={k: (str(v) if isinstance(v, Path) else v) for k, v in vars(a).items()},
               review_corrections=[dict(id=i, finding=REVIEW_FINDINGS[i], change=STAGE_CHANGES[stage][i]) for i in corr],
               result=summary, scope=SCOPE)
    ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rc = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    out["elapsed_seconds"] = time.time() - start
    out["peak_rss_kB"] = dict(parent=ru, largest_child=rc)
    save_arrays(a.followup_dir / f"{name}_DRAWS.npz", groups)
    out["provenance"]["output_npz_sha256"] = sha256(a.followup_dir / f"{name}_DRAWS.npz")
    write_json(a.followup_dir / f"{name}.json", out)
    log(f"wrote {a.followup_dir / (name + '.json')} elapsed {out['elapsed_seconds']:.1f} s")


STAGE_CHANGES = {
    "c1zero": {
        "F1": "new --diff-c1-scale option; each DIFF family rerun at C_1 = 0 on the main-run seeds (CRN partners of the 2000-mock reference)",
        "F2": "NSIDE4 calibration traces and NSIDE8/4 ratios recomputed at C_1 = 0 on the reference calibration and scale seeds",
        "F5": "off-diagonal-class and per-selection overdispersion recorded for nominal and C_1 = 0 mocks"},
    "amplitude": {
        "F3": "amplitude nuisance sigma_r = hypot(jk4-trace scatter / excess, calibration SE / excess); per-mock truncated-normal "
              "amplitude draws give the marginal p; fixed 16%/84% amplitude ensembles give the band",
        "F4": "single-selection jackknife trace of the DIFF families measured against its data target in fresh mocks"},
    "validate": {
        "F1": "direct mocks at the semi-analytic C_1 where p(t_self, dipole) crosses 0.05 validate the first-order closed form"},
}


def shape_selector(ref):
    """F2: per-mock NSIDE8/4 contrast-ratio z-scores of the data from the reference 9-mock scale diagnostic."""
    cal = ref["json"]["calibration"]
    data = G["data_scale"]["ratio_contrast_8_over_4"]
    data_single = G["data_scale"]["ratio_single_8_over_4"]
    out = {}
    for f in FAMILIES:
        sd = cal[f]["scale_diagnostic"]
        r = np.array(sd["trace_contrast_nside8"]) / np.array(sd["trace_contrast_nside4"])
        rs = np.array(sd["trace_single_nside8"]) / np.array(sd["trace_single_nside4"])
        out[f] = dict(label=FAMILY_LABELS[f], n_mocks=len(r), contrast_ratio_per_mock_mean=float(r.mean()),
                      contrast_ratio_per_mock_sd=float(r.std(ddof=1)), z_data_contrast=float((data - r.mean()) / r.std(ddof=1)),
                      single_ratio_per_mock_mean=float(rs.mean()), single_ratio_per_mock_sd=float(rs.std(ddof=1)),
                      z_data_single=float((data_single - rs.mean()) / rs.std(ddof=1)))
    closest = min(DIFF_FAMILIES, key=lambda f: abs(out[f]["z_data_contrast"]))
    return dict(data_contrast_ratio=data, data_single_ratio=data_single, families=out,
                closest_contrast_ratio_family=FAMILY_LABELS[closest],
                statement=("The NSIDE8/4 contrast ratio is closest to the data for " + FAMILY_LABELS[closest] +
                           ". With 9 mocks per family no DIFF family is excluded at 2 sigma, and the ratio is blind to C_1 "
                           "(see C1ZERO jackknife_c1_insensitivity), so it does not select a family and does not set p."))


def od_validity_table(ref, obs, c1z, amp, val):
    """F5: data versus mock overdispersion for every family and ensemble."""
    rows = []
    npz = ref["npz"]
    for f in FAMILIES:
        od = npz[f"{f}_dipole_od"]
        rows.append(dict(family=FAMILY_LABELS[f], ensemble="reference nominal (2000 mocks)", quantity="per-selection OD, peak",
                         **od_summary(od[:, 0], obs["dipole"]["od"][0])))
        rows.append(dict(family=FAMILY_LABELS[f], ensemble="reference nominal (2000 mocks)", quantity="per-selection OD, integrated",
                         **od_summary(od[:, 1], obs["dipole"]["od"][1])))
    sources = [("nominal replay subset", c1z["result"]["ensembles"], "nominal_"),
               ("C_1 = 0", c1z["result"]["ensembles"], "c1zero_"),
               ("amplitude-marginal", amp["result"]["ensembles"], "marginal_"),
               ("closed-form 0.05 crossing", val["result"]["ensembles"], "")]
    for name, ens, prefix in sources:
        for f in FAMILIES:
            e = ens.get(prefix + f)
            if e is None:
                continue
            rows.append(dict(family=FAMILY_LABELS[f], ensemble=name, quantity="off-diagonal-class OD", **e["offdiag_overdispersion"]))
            if name != "nominal replay subset":
                continue
            rows.append(dict(family=FAMILY_LABELS[f], ensemble=name, quantity="per-selection OD, peak", **e["models"]["dipole"]["overdispersion_peak"]))
            rows.append(dict(family=FAMILY_LABELS[f], ensemble=name, quantity="per-selection OD, integrated",
                             **e["models"]["dipole"]["overdispersion_integrated"]))
    return rows


def prior_runs_provenance(rr):
    """F6: per-run script SHAs of the original R106 runs, taken from each run's own JSON where one exists."""
    runs = []
    for r in rr["runs"]:
        m = re.search(r"--output (\S+)", r["command"])
        outdir = Path(m.group(1)) if m else None
        js = outdir / "NVSS_NULL_MOCKS.json" if outdir else None
        entry = dict(r)
        if "IndexError" in r.get("note", ""):
            entry["script_sha256"] = None
            entry["script_sha256_source"] = "not recorded: the run crashed before writing JSON (logs moved to failed_attempt1/)"
        elif js is not None and js.exists():
            j = json.loads(js.read_text())
            entry["script_sha256"] = j["script_sha256"]
            entry["script_sha256_source"] = f"{js} (script_sha256 written by that run)"
            entry["families_in_run"] = list(j["families"])
            entry["output_json_mtime"] = time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime(js.stat().st_mtime))
            entry["p_self_dipole_shown"] = {FAMILY_LABELS[f]: p_display(v["models"]["dipole"]["wald_self_R65_estimator"]["mocks_ge_observed"],
                                                                     v["models"]["dipole"]["wald_self_R65_estimator"]["n_mocks"])
                                            for f, v in j["families"].items()}
        else:
            entry["script_sha256"] = None
            entry["script_sha256_source"] = "not recorded: the run wrote no JSON (timing-only run, log only)"
        runs.append(entry)
    return runs


def stage_report(a, log, start):
    ref = load_reference(a.reference)
    meta = load()
    obs = observed_state()
    fd = a.followup_dir
    c1z = json.loads((fd / "C1ZERO.json").read_text())
    amp = json.loads((fd / "AMPLITUDE_NUISANCE.json").read_text())
    val = json.loads((fd / "C1_VALIDATION.json").read_text())
    z0groups = load_arrays(fd / "C1ZERO_DRAWS.npz")
    df_info = offdiag_fraction_contrast(G["joint"])
    df_mock = offdiag_fraction_contrast(np.array(ref["json"]["families"]["LSS_DIFF_RED"]["mean_class_counts"]))
    analysis = c1_analysis(ref, z0groups, obs, df_info, a)
    cur = sha256(Path(__file__))
    stage_files = {n: fd / f"{n}.json" for n in ("C1ZERO", "AMPLITUDE_NUISANCE", "C1_VALIDATION")}
    def stage_record(p):
        j = json.loads(p.read_text())
        tf = p.parent / f"{j['stage']}.time"
        wall = rss = None
        if tf.exists():
            mm = re.search(r"([\d.]+) s (\d+) kB", tf.read_text())
            if mm:
                wall, rss = float(mm.group(1)), int(mm.group(2))
        return dict(stage=j["stage"], command=j["provenance"]["command"], script_sha256=j["provenance"]["script_sha256"],
                    script_sha256_equals_current=j["provenance"]["script_sha256"] == cur, json_sha256=sha256(p),
                    npz_sha256=j["provenance"]["output_npz_sha256"], elapsed_seconds=j["elapsed_seconds"],
                    wall_s_gnu_time=wall, maxrss_kB_gnu_time=rss, return_code=0)
    stage_runs = {n: stage_record(p) for n, p in stage_files.items()}
    smoke_dir = fd.parent / (fd.name + "_smoke")
    smoke_runs = ({n: dict(stage_record(smoke_dir / f"{n}.json"), note="smoke test of the follow-up stages, tiny ensembles, superseded")
                   for n in stage_files if (smoke_dir / f"{n}.json").exists()} if smoke_dir != fd else {})
    rr_path, rr_pre = OUTDIR / "RUN_RECORD.json", OUTDIR / "RUN_RECORD.pre_r106_review.json"
    rr = json.loads((rr_pre if rr_pre.exists() else rr_path).read_text())
    prior = prior_runs_provenance(rr)
    smoke1 = next(r for r in prior if "smoke" in r["command"] and "smoke2" not in r["command"])
    design_note = ("LSS_DIFF_MID (MID_SLOPE=-0.6) and the NSIDE8/4 jackknife shape diagnostic were introduced after smoke run 1 "
                   f"(script {smoke1['script_sha256'][:12]}..., JSON written {smoke1['output_json_mtime']}) had displayed RED/FLAT "
                   f"dipole p_self values ({json.dumps(smoke1['p_self_dipole_shown'])}); smoke2 and the FINAL run used script "
                   f"{rr['script_sha256'][:12]}....")
    # amplitude-marginal p with 16-84% band
    marginal = {}
    for f in DIFF_FAMILIES:
        e = amp["result"]["ensembles"]
        nu = amp["result"]["nuisance"][f]
        fam = dict(label=FAMILY_LABELS[f], sigma_r=nu["sigma_r"], r_quantiles_16_50_84=nu["r_quantiles_16_50_84"],
                   conditional_on="the family's assumed shape with C_1 = r A_m", models={})
        for _, m in MODELS:
            fam["models"][m] = {}
            for k in STATS:
                mg = e[f"marginal_{f}"]["models"][m][STAT_NAMES[k]]
                lo = e[f"r16_{f}"]["models"][m][STAT_NAMES[k]]
                hi = e[f"r84_{f}"]["models"][m][STAT_NAMES[k]]
                nom = summarise(ref["npz"][f"{f}_{m}_{k}"], obs[m][k])
                nom_paired = summarise(ref["npz"][f"{f}_{m}_{k}"][:lo["n_mocks"]], obs[m][k])
                fam["models"][m][STAT_NAMES[k]] = dict(
                    marginal_p=mg["p_mc"], marginal_p_display=mg["p_display"], marginal_p_mc_se=mg["p_mc_binomial_se"],
                    band_16_84=[lo["p_mc"], hi["p_mc"]], band_display=f"[{lo['p_display']}, {hi['p_display']}]",
                    band_mc_se=[lo["p_mc_binomial_se"], hi["p_mc_binomial_se"]],
                    nominal_amplitude_p_display=nom["p_display"],
                    nominal_amplitude_same_seeds_as_band_p_display=nom_paired["p_display"])
        marginal[f] = fam
    ens0 = c1z["result"]["ensembles"]
    f4 = {}
    cal = ref["json"]["calibration"]
    for f in DIFF_FAMILIES:
        _, am, kind = family_params(ref, f)
        ac = cal["LSS_COMMON"]["amp_common"]
        f4[f] = dict(label=FAMILY_LABELS[f],
                     reference_calibration_single_trace_ratio_to_target=float(cal[f]["final"]["trace_single_mean"] / G["target_single"]),
                     fresh_jk_single_trace_ratio_to_target=amp["result"]["nuisance"][f]["single_selection_ratio_to_target"],
                     C10_diff_over_C10_common=float(spectrum(am, kind)[10] / spectrum(ac, "red")[10]),
                     statement="not jointly calibrated: the single-selection constraint is violated at the fitted A_m")
    f1_summary = {}
    for f in DIFF_FAMILIES:
        fa = analysis[f]
        md = fa["models"]["dipole"]
        vc1 = val["result"]["targets"][f]["C1"]
        vmax = max(fa["A_m"], vc1 or 0.0)
        within = {a_: {kind: (None if md["crossings"][a_][key] is None else bool(md["crossings"][a_][key] <= vmax))
                       for kind, key in (("semi_analytic", "t_self_semi_analytic_C1"), ("gaussian", "gaussian_closed_form_C1"))}
                  for a_ in ("0.05", "0.01")}
        f1_summary[f] = dict(
            directly_validated_C1_points=[c for c in (0.0, fa["A_m"], vc1) if c is not None],
            crossing_within_validated_C1_range=within,
            label=FAMILY_LABELS[f], A_m=fa["A_m"], null_restated=("random dipole in the log-density of the resolved/migrating classes, "
                                                                   f"per-component RMS sqrt(3 C_1/4pi) = {fa['rms_dipole_per_component_at_nominal_C1']:.3g} at C_1 = A_m"),
            required_dipole_for_observed_contrast=float(np.linalg.norm(obs["dipole"]["delta"]) / df_info["df"]),
            p_t_self_dipole_at_C1_0=ens0[f"c1zero_{f}"]["models"]["dipole"]["wald_self_R65_estimator"]["p_display"],
            p_t_self_dipole_at_C1_A_m_reference=summarise(ref["npz"][f"{f}_dipole_t_self"], obs["dipole"]["t_self"])["p_display"],
            cov_c1zero_trace_over_r65_poisson=md["cov_c1zero_trace_over_r65_poisson"],
            crossing_0p05_C1_semi_analytic=md["crossings"]["0.05"]["t_self_semi_analytic_C1"],
            crossing_0p01_C1_semi_analytic=md["crossings"]["0.01"]["t_self_semi_analytic_C1"],
            crossing_0p05_C1_gaussian=md["crossings"]["0.05"]["gaussian_closed_form_C1"],
            crossing_0p01_C1_gaussian=md["crossings"]["0.01"]["gaussian_closed_form_C1"],
            validation_at_A_m=md["validation_at_C1_equals_A_m"]["p_predicted"] + " predicted vs " +
            md["validation_at_C1_equals_A_m"]["p_reference_paired"] + " direct (paired seeds)",
            validation_at_0p05_crossing=(val["result"]["ensembles"][f]["models"]["dipole"]["closed_form_check"]["p_direct"] + " direct"
                                         if f in val["result"]["ensembles"] else "not run: " + val["result"]["targets"][f]["skipped"]))
    out = dict(
        schema="htt.r106.radio_null_mocks.review_corrections/1", stage="report",
        provenance=provenance(sys.argv[1:], dict(meta["input_sha256"], **ref["sha"],
                                                 **{f"{n.lower()}_json": sha256(p) for n, p in stage_files.items()},
                                                 c1zero_npz=sha256(fd / "C1ZERO_DRAWS.npz"),
                                                 run_record_pre_review=sha256(rr_pre if rr_pre.exists() else rr_path))),
        review_corrections=[
            dict(id="F1", finding=REVIEW_FINDINGS["F1"],
                 change=("--diff-c1-scale option; C_1 = 0 runs (CRN with the reference); first-order closed form Cov = Cov_{C_1=0} + "
                         "df^2 (3 C_1/4pi) I_2 with df from the observed joint class counts, validated per mock at C_1 = A_m (reference) "
                         "and by direct mocks at the 0.05 crossing; p versus C_1 and the 0.05/0.01 crossings reported; docstring and "
                         "scope restate each null as an assumed resolved-fraction dipole and forbid quoting a family p as the "
                         "LSS/selection-null p")),
            dict(id="F2", finding=REVIEW_FINDINGS["F2"],
                 change=("MID is not labelled as favoured by the data anywhere in code or outputs; it is reported only as the family whose NSIDE8/4 "
                         "contrast ratio is closest to the data, with the 9-mock z-scores; NSIDE4 calibration traces and the 8/4 ratio "
                         "shown to be C_1-insensitive at C_1 = 0 on the same seeds; full family range of p reported")),
            dict(id="F3", finding=REVIEW_FINDINGS["F3"],
                 change=("amplitude ratio r ~ N(1, sigma_r) truncated at r > 0 with sigma_r = hypot(jk4-trace SD/excess, calibration "
                         "SE/excess) from fresh and reference jackknife mocks; marginal p from per-mock r draws, 16-84% band from fixed "
                         "r16/r84 ensembles; p shown to two significant figures with counts")),
            dict(id="F4", finding=REVIEW_FINDINGS["F4"],
                 change=("DIFF families renamed EMPIRICAL_DIFF_SELECTION_{RED,MID,FLAT} in docstring and outputs (internal keys kept "
                         "for seeds); the violated single-selection constraint is stated with its measured ratio")),
            dict(id="F5", finding=REVIEW_FINDINGS["F5"],
                 change="overdispersion validity table (per-selection and off-diagonal-class) for every family and ensemble"),
            dict(id="F6", finding=REVIEW_FINDINGS["F6"],
                 change="per-run script SHAs taken from each run's own JSON and a design-change note added to RUN_RECORD.json"),
        ],
        family_labels=FAMILY_LABELS,
        df_offdiag_fraction=dict(observed_counts=df_info, reference_mock_mean_counts_RED=df_mock),
        f1_c1_dependence=dict(summary=f1_summary, closed_form="Cov(C_1) = Cov_{C_1=0}(mocks) + df^2 (3 C_1/4pi) I_2",
                              semi_analytic="t_i(C_1) = (delta0_i + df sqrt(C_1) u_i)^T S_i^-1 (...) with u_i the mock's own unit-C_1 l=1 dipole",
                              per_family=analysis, validation_at_crossing=val["result"]),
        f2_shape_selector=dict(selector=shape_selector(ref), c1_insensitivity=c1z["result"]["jackknife_c1_insensitivity"],
                               p_t_self_dipole_range_at_reference={FAMILY_LABELS[f]: summarise(ref["npz"][f"{f}_dipole_t_self"], obs["dipole"]["t_self"])["p_display"]
                                                                   for f in FAMILIES}),
        f3_amplitude_marginal=dict(per_family=marginal, nuisance=amp["result"]["nuisance"]),
        f4_joint_calibration=f4,
        f5_overdispersion_validity=dict(table=od_validity_table(ref, obs, c1z, amp, val),
                                        note=("Model-adequacy checks only: pixel overdispersion is dominated by high l and does not "
                                              "constrain C_1. No source-multiplicity or white small-scale term was added in this "
                                              "follow-up, so its effect on the contrast-null spread is untested.")),
        f6_provenance=dict(prior_runs=prior, design_change_note=design_note, followup_runs=stage_runs,
                           followup_smoke_runs=smoke_runs, current_script_sha256=cur),
        claim_classes=dict(
            physical_attribution="none: no statement that the NVSS integrated-minus-peak contrast is or is not caused by LSS or selection; C_1 is not anchored by independent data",
            conditional_prediction=("every p here is conditional on a family shape and its C_1; p versus C_1, the crossings and the "
                                    "amplitude-marginal p with band are conditional predictions"),
            numerical_convergence=("MC binomial SEs, bootstrap intervals of the crossings, per-mock validation of the first-order closed "
                                   "form at C_1 = A_m and at the 0.05 crossing, and the bit-exact replay of the reference mocks")),
        scope=SCOPE)
    out["elapsed_seconds"] = time.time() - start
    write_json(fd / "NVSS_REVIEW_CORRECTIONS.json", out)
    log(f"wrote {fd / 'NVSS_REVIEW_CORRECTIONS.json'}")
    if a.update_run_record:
        if not rr_pre.exists():
            shutil.copy2(rr_path, rr_pre)
        new = json.loads(rr_pre.read_text())
        new["script_sha256_note"] = "script_sha256 above is the script of smoke2 and the FINAL run; see per-run script_sha256"
        new["runs"] = prior
        new["design_change_note"] = design_note
        new["r106_review_followup"] = dict(
            current_script_sha256=cur, outputs_dir=str(fd), runs=stage_runs, smoke_runs=smoke_runs,
            report=dict(command=out["provenance"]["command"], json_sha256=sha256(fd / "NVSS_REVIEW_CORRECTIONS.json")),
            outputs_sha256={p.name: sha256(p) for p in sorted(fd.glob("*.json")) + sorted(fd.glob("*.npz"))})
        write_json(rr_path, new)
        log(f"updated {rr_path} (pre-review copy {rr_pre})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output", type=Path, default=OUTDIR)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--calib-mocks", type=int, default=8)
    ap.add_argument("--max-mocks", type=int, default=2000, help="per family")
    ap.add_argument("--budget-seconds", type=float, default=1200.0, help="wall budget for the whole run")
    ap.add_argument("--families", nargs="+", default=list(FAMILIES))
    ap.add_argument("--pilot-common", type=float, default=1e-4)
    ap.add_argument("--pilot-red", type=float, default=1e-3)
    ap.add_argument("--pilot-flat", type=float, default=1e-3)
    ap.add_argument("--pilot-mid", type=float, default=5e-3)
    ap.add_argument("--scale-mocks", type=int, default=8, help="mocks per family for the NSIDE 4/8 jackknife shape diagnostic")
    ap.add_argument("--timing-only", action="store_true")
    ap.add_argument("--overwrite", action="store_true", help="allow the main pipeline to overwrite the reference outputs")
    ap.add_argument("--diff-c1-scale", type=float, default=1.0,
                    help="multiply C_1 of the differential field (0 removes its l=1 mode; 1 = legacy power-law value A_m)")
    ap.add_argument("--followup", choices=("c1zero", "amplitude", "validate", "report"),
                    help="R106 review follow-up stage (amplitudes reused from --reference)")
    ap.add_argument("--reference", type=Path, default=OUTDIR / "NVSS_NULL_MOCKS.json")
    ap.add_argument("--followup-dir", type=Path, default=FOLLOWUP_DIR)
    ap.add_argument("--n-mocks", type=int, default=1000, help="follow-up main-estimator mocks per family (c1zero, amplitude-marginal, validate)")
    ap.add_argument("--n-nominal", type=int, default=100, help="c1zero: nominal replay mocks per family")
    ap.add_argument("--n-jk-check", type=int, default=None, help="c1zero: cap on jackknife C_1-insensitivity mocks per family")
    ap.add_argument("--n-jk", type=int, default=48, help="amplitude: fresh NSIDE4 jackknife mocks per family")
    ap.add_argument("--n-band", type=int, default=600, help="amplitude: mocks per family at each of r16 and r84")
    ap.add_argument("--n-boot", type=int, default=200, help="bootstrap replicates for crossing intervals")
    ap.add_argument("--c1-hi", type=float, default=0.1, help="upper C_1 searched for p crossings")
    ap.add_argument("--update-run-record", action="store_true", help="report: rewrite RUN_RECORD.json (pre-review copy kept)")
    a = ap.parse_args()
    if a.workers < 1 or a.workers > 3:
        raise ValueError("1-3 workers allowed on the shared workstation")
    start = time.time()
    logdir = a.followup_dir if a.followup else a.output
    logdir.mkdir(parents=True, exist_ok=True)
    logname = f"{a.followup}.log" if a.followup else "radio_null_mocks.log"
    with open(logdir / logname, "a") as logf:
        def log(msg):
            line = f"[{time.time() - start:8.1f}s] {msg}"
            print(line, flush=True)
            logf.write(line + "\n")
            logf.flush()
        if a.followup == "report":
            stage_report(a, log, start)
        elif a.followup:
            run_followup_stage(a, log, start)
        else:
            run_main(a, logf, log, start)


if __name__ == "__main__":
    main()
