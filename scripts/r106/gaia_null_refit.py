"""R106 Gaia/Quaia redshift-curvature refit without the R104-selected patches 8/47, against
same-estimator relabeling nulls with a selection-matched exclusion.

Estimator (unchanged from R103-R105): R98 per-shell, per-NSIDE-2-patch weighted normal
equations of the 16 tangent VSH coefficients (glide, spin, E2, B2) in four Quaia redshift
shells, and the two R103 second-difference rows (shells 0-2, 1-3) built on the four shell
MEDIAN redshifts. The rows annihilate a common frame whose coefficients are affine in z
only when that frame is evaluated at the shell medians, which is all the shell-median
injection check tests. A frame that is linear in each source's own z leaks into curvature,
because the precision-weighted effective redshift of a shell differs from its median;
observed.json reports that leak from a direct per-source injection. Both rows are kept
together (32 dim) with the delete-one and delete-two shared-patch jackknife covariance, so
the covariance BETWEEN the rows enters.

Configurations
  all48      all 48 NSIDE-2 RING patches (replays R105 GAIA_FRAME_PARITY.json).
  excl_8_47  patches 8 and 47 removed from every shell. They were selected on these data by
             the R104 influence rule: 47 is the top delete-one shift-norm patch in curvature
             row 0 (every sector) and 8 the top row-1 patch for E2 and B2. They are not the
             top row-1 glide/spin patch (32), and (43,47) is the worst delete-two pair in 7
             of 8 row-sectors; observed.json replays that ranking and reports the observed
             statistics under those spin-relevant alternative exclusions (observed only, no
             null tables).

Selection-matched exclusion. Because 8/47 were chosen on the observed data, every null draw
applies the same rule to its OWN all-48 delete-one refits: the top row-0 patch plus the top
row-1 patch distinct from it, ranked by the delete-one shift norm of a sector variant (B2,
E2, or the 10-dim E2+B2 shift, which is the primary variant). The excluded-configuration
null tables and the exclusion ratios use that per-draw selection. Null tables with the
fixed patches 8/47 are kept only as a diagnostic conditional on fixed patches.

Nulls, each pushed through the identical estimator, exclusion rule and jackknife:
  patch            redshift labels permuted among the qualified Quaia sources inside each
                   sky patch (keeps footprint, per-source astrometry and noise; removes any
                   z dependence).
  patch_gmag       the same inside patch x 8 Gaia-G quantile strata.
  patch_gmag_colour  the same inside patch x 4 G x 4 BP-RP strata. It keeps most of the
                   shell BP-RP curvature but only part of the shell G curvature, and the
                   8-bin patch_gmag null is not nested in it; observed.json reports the
                   retained fractions. No null keeps both G and colour at high fidelity.
  crf3_complement  Gaia-CRF3 rows absent from the pinned Quaia joins, with the Quaia quality
                   cuts and G inside the Quaia range, assigned to pseudo-shells with the
                   Quaia shell fractions of their patch x G x BP-RP stratum.
  crf3_complement_all_g  the same disjoint CRF3 rows without the G restriction (mostly
                   G > 20), assigned with the Quaia shell fractions of patch x BP-RP.
The three permutation nulls are relabelings of ONE Quaia realization (the same 634,233
rows). The two complement nulls are relabelings of two FIXED complement samples (the
summary checks whether the G-matched usable set is a subset of the all-G one). For a
permutation null, (b+1)/(N+1) is an exact conditional Monte Carlo permutation p-value for
within-stratum z-exchangeability of this one realization and a pre-specified statistic;
spin was singled out after R104 saw these data, so spin p-values are post-selection. The
complement draws use other sources with other noise, so the observed value is not
exchangeable with them and only its rank is reported. Draws of different nulls are never
pooled. No null is an independent noise/AGIS-scan/AGN-centroid mock ensemble, so no
calibrated significance is produced.
Units: curvature coefficients in microarcsec/yr per unit z^2 (R98 VSH basis); frame
coefficients in microarcsec/yr; quadratic forms dimensionless.

Subcommands: observed | null | selmatch (replays the cached null draws, checks them
bit-for-bit, and adds the selection-matched exclusion) | summarize.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

import healpy as hp
import numpy as np
from astropy.io import fits

from scripts.r69.gaia_e2_b2 import templates
from scripts.r103 import gaia_frame_curvature as g
from scripts.r105 import gaia_frame_parity as par

REPO = Path(__file__).resolve().parents[2]
JOIN = Path("/mnt/extdrive/workdir/htt_open_data/a22_20261023/quaia_join/quaia_crf3_join.npz")
JOIN_SHA = "2fbaa40a8afe58066064efa8a7784ac508c5b2c67b41c779676eab7df8cf9ef4"
FULL_JOIN = Path("/mnt/extdrive/workdir/htt_open_data/a22_20261023/quaia_join/quaia_gaia_full_join.npz")
FULL_JOIN_SHA = "4cd83b1e8bb9f71f89aacfc2db5daba87f9a79f2af8ccd2e7e94b0be57252dae"
CRF3 = Path("/mnt/extdrive/workdir/raw/observational_bundles/Gaia_CRF3_astrometry/gaia_crf3_astrometry_full.fits")
CRF3_SHA = "e69cfff82f762c00d1d6a259c6d003fd20f805f3b1fcd4acc81d847c485120c0"
R105_JSON = g.BASE / "R105_RESEARCH_20261124/GAIA_FRAME_PARITY.json"
R105_JSON_SHA = "6c5d595048d4eb2ac25a780a8d23812b04b571419675423b4d89dfc389375cda"
R104_JSON = g.BASE / "R104_DATA_SOLVER_CONTINUATION_20261124/GAIA_PATCH_INFLUENCE.json"
# File state of this script when the R106 review read it (after the cached null runs). The
# cached draws are certified by bit-identical replay under the current script, not by this hash.
PRE_REVIEW_SCRIPT_SHA = "9dd338268206c950caff6fbc6a234a505a4ad2de5e58b44b26628cc0e612189b"
OUT = Path("/home/cosmosapjw/Downloads/htt_r106_analysis/gaia")
EXCLUDE = (8, 47)
EDGES = (0.8, 1.5, 2.1)
NPATCH, NSHELL, NCOEF = 48, 4, 16
NULLS = ("patch", "patch_gmag", "patch_gmag_colour", "crf3_complement", "crf3_complement_all_g")
PERMUTATION_NULLS = NULLS[:3]
COMPLEMENTS = ("crf3_complement", "crf3_complement_all_g")
# R104 influence rule variants: delete-one shift norm over these coefficient indices of a row.
SECTOR_RULES = {"EB": np.r_[6:16], "B2": np.r_[11:16], "E2": np.r_[6:11]}
PRIMARY_RULE = "EB"
ALT_EXCLUSIONS = ((32,), (43, 47), (8, 47, 32), (8, 47, 43), (8, 47, 32, 43))
# R105 frame_shifted_rhs test frame on glide+spin (checked against par.frame_shifted_rhs).
FRAME_BASE = np.array([8., -3., 2., -4., 5., 6.])
FRAME_SLOPE = np.array([-3., 4., 5., 2., -7., 1.])

STAT_SETS = {
    "joint32": np.arange(32),
    "electric16": par.ELE,
    "magnetic16": par.MAG,
    "glide6": np.r_[0:3, 16:19],
    "spin6": np.r_[3:6, 19:22],
    "E2_10": np.r_[6:11, 22:27],
    "B2_10": np.r_[11:16, 27:32],
    "row0_16": np.arange(16),
    "row1_16": np.arange(16, 32),
}
DERIVED = ("magnetic_given_electric", "magnetic16_rows_without_crosscov")
STAT_NAMES = tuple(STAT_SETS) + DERIVED
RANK_STATS = ("spin6", "magnetic16", "joint32")
RATIO_STATS = ("joint32", "electric16", "magnetic16", "magnetic_given_electric", "spin6", "E2_10", "B2_10")

REVIEW_CORRECTIONS = [
    {"id": "GNR-1", "change": "Pooled '6000 draws' statements withdrawn; draws of different nulls are never pooled. "
     "per_null_ranks gives, for every null separately, draws_ge_observed, rank, max, q95 and q99 for spin6, magnetic16 and "
     "joint32 (all48 and the selection-matched exclusion, jk1 and jk2). null_structure states that the three permutation "
     "nulls relabel one Quaia realization and the two complement nulls relabel fixed complement samples (subset relation "
     "computed). (b+1)/(N+1) is reported only for the within-stratum permutation nulls, as an exact conditional permutation "
     "p-value; complement nulls get the rank only. Spin is flagged as selected after R104."},
    {"id": "GNR-2", "change": "Each null draw applies the R104 influence rule (top delete-one shift-norm patch in curvature "
     "row 0, top distinct patch in row 1) to its own all-48 delete-one refits in three sector variants (E2+B2 primary, B2, "
     "E2). The excluded-configuration null tables and exclusion ratios use that per-draw selection; the rule spread is "
     "reported; the fixed-(8,47) tables survive only under fixed_patch_conditional_diagnostic."},
    {"id": "GNR-3", "change": "Docstring describes 8/47 as the top row-0 (every sector) and row-1 E2/B2 patches. observed.json "
     "replays the R104 per-row/sector delete-one top-5 and worst delete-two pair from the R98 cache (checked against "
     "GAIA_PATCH_INFLUENCE.json) and reports observed statistics after the alternative exclusions {32}, {43,47}, {8,47,32}, "
     "{8,47,43}, {8,47,32,43} with the largest relative spin6 change."},
    {"id": "GNR-4", "change": "Docstring restricted to frames evaluated at the shell medians. observed.json adds a direct "
     "per-source z-linear frame injection (R105 test frame), its curvature leak, the precision-weighted effective shell "
     "redshifts, the leak's own spin6 quadratic form, and the spin slope that a leak-only explanation would need."},
    {"id": "GNR-5", "change": "Docstring no longer says patch_gmag_colour keeps the magnitude composition. observed.json "
     "reports the exact within-stratum-permutation expectation of the shell G and BP-RP curvature and the retained fraction "
     "for each permutation null, plus a patch x G8 x C4 stratification that is evaluated but not run as a null."},
    {"id": "GNR-6", "change": "idealized_hotelling_reference carries a scope string and the empirical/Hotelling q95 ratio "
     "for every null, configuration and statistic."},
    {"id": "GNR-7", "change": "FULL_JOIN sha256 pinned, fail closed if missing or changed, and recorded; the CRF3 FITS sha is "
     "verified for every null kind (it sets the BP-RP strata); the R105 parity JSON is checked against a pinned sha; every "
     "output JSON records the sha256 of this script and of every imported scripts.* module, git HEAD, the git status of "
     "those files, and the command."},
]


def sha_file(path):
    h = sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def check_pinned(path, expected, label):
    """sha256 of a pinned input; fail closed when it is missing or changed."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"pinned input missing: {label} {path}")
    got = sha_file(path)
    if got != expected:
        raise ValueError(f"pinned input identity mismatch: {label} {got} != {expected}")
    return got


def code_identity():
    """sha256 of this script and of every imported scripts.* module, plus git state."""
    mods = {}
    for name, mod in sorted(sys.modules.items()):
        path = getattr(mod, "__file__", None)
        if path and (name == "scripts" or name.startswith("scripts.")):
            p = Path(path).resolve()
            mods[str(p.relative_to(REPO)) if p.is_relative_to(REPO) else str(p)] = sha_file(p)
    me = Path(__file__).resolve()
    rel = str(me.relative_to(REPO)) if me.is_relative_to(REPO) else str(me)
    mods[rel] = sha_file(me)
    git = {}
    try:
        git["head"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True,
                                     check=True).stdout.strip()
        git["status_porcelain_of_code_files"] = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--", *mods], cwd=REPO, capture_output=True,
            text=True, check=True).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError) as exc:
        git["error"] = repr(exc)
    return {"script": rel, "script_sha256": mods[rel], "pre_review_script_sha256": PRE_REVIEW_SCRIPT_SHA,
            "module_sha256": mods, "git": git}


def command_record():
    return {"argv": [sys.executable, *sys.argv], "cwd": os.getcwd(),
            "env": {k: os.environ.get(k) for k in ("PYTHONPATH", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS",
                                                    "MKL_NUM_THREADS")}}


def whiten(ra, dec, y, e1, e2, rho, chunk=100_000):
    """Return X=(L^T B) [N,2,16] and Y=L^T y [N,2] with W=L L^T the source inverse covariance."""
    n = len(ra)
    X = np.empty((n, 2, NCOEF))
    Y = np.empty((n, 2))
    for a in range(0, n, chunk):
        b = min(n, a + chunk)
        _, B = templates(ra[a:b], dec[a:b])
        inv = 1.0 / (1.0 - rho[a:b] ** 2)
        w00 = inv / e1[a:b] ** 2
        w11 = inv / e2[a:b] ** 2
        w01 = -rho[a:b] * inv / (e1[a:b] * e2[a:b])
        l00 = np.sqrt(w00)
        l10 = w01 / l00
        l11 = np.sqrt(w11 - l10 ** 2)
        X[a:b, 0] = l00[:, None] * B[:, 0] + l10[:, None] * B[:, 1]
        X[a:b, 1] = l11[:, None] * B[:, 1]
        Y[a:b, 0] = l00 * y[a:b, 0] + l10 * y[a:b, 1]
        Y[a:b, 1] = l11 * y[a:b, 1]
    return X, Y


def group_normal(X, Y, shell, patch):
    """Shell x patch normal equations F[4,48,16,16], s[4,48,16] (R98 mas/yr units)."""
    key = shell.astype(np.int64) * NPATCH + patch
    order = np.argsort(key, kind="stable")
    counts = np.bincount(key, minlength=NSHELL * NPATCH)
    Xs = X[order].reshape(-1, NCOEF)
    Ys = Y[order].reshape(-1)
    f = np.zeros((NSHELL * NPATCH, NCOEF, NCOEF))
    s = np.zeros((NSHELL * NPATCH, NCOEF))
    start = 0
    for k, c in enumerate(counts):
        if c:
            xg = Xs[2 * start:2 * (start + c)]
            f[k] = xg.T @ xg
            s[k] = xg.T @ Ys[2 * start:2 * (start + c)]
        start += c
    return f.reshape(NSHELL, NPATCH, NCOEF, NCOEF), s.reshape(NSHELL, NPATCH, NCOEF)


def refit_parts(f, s, w, keep):
    """Curvature vector (32), delete-one/-two covariances, curvature [2,16], delete-one curvature [n,2,16]."""
    full, one, two, _ = g.shared_patch_refits(f[:, keep], s[:, keep])
    n = len(keep)
    meas, one_w = w @ full, w @ one
    y = meas.reshape(-1)
    c1 = g.delete_covariance(one_w, n, 1)
    c2 = g.delete_covariance(w @ two, n, 2)
    return y, c1, c2, meas, one_w


def refit(f, s, w, keep):
    """Curvature vector (32) and delete-one / delete-two covariance for kept patches."""
    return refit_parts(f, s, w, keep)[:3]


def qforms(y, c):
    out = {}
    for name, idx in STAT_SETS.items():
        sub = c[np.ix_(idx, idx)]
        chol = np.linalg.cholesky(sub)
        z = np.linalg.solve(chol, y[idx])
        out[name] = float(z @ z)
    out["magnetic_given_electric"] = out["joint32"] - out["electric16"]
    m0, m1 = par.MAG[:8], par.MAG[8:]
    out["magnetic16_rows_without_crosscov"] = float(
        y[m0] @ np.linalg.solve(c[np.ix_(m0, m0)], y[m0]) + y[m1] @ np.linalg.solve(c[np.ix_(m1, m1)], y[m1]))
    return out


def influence(meas, one_w, row, idx):
    """Delete-one shift norm of curvature row `row` over coefficient indices `idx`, per deleted patch."""
    return np.linalg.norm(one_w[:, row, idx] - meas[row, idx], axis=1)


def select_exclusion(meas, one_w, rule):
    """R104 rule on one data set's own delete-one refits: top row-0 patch, then top distinct row-1 patch."""
    idx = SECTOR_RULES[rule]
    a = int(np.argmax(influence(meas, one_w, 0, idx)))
    order = np.argsort(-influence(meas, one_w, 1, idx), kind="stable")
    b = int(order[0] if order[0] != a else order[1])
    return (min(a, b), max(a, b))


def null_rank(x, observed, exchangeable):
    """Rank of an observed statistic in one null; (b+1)/(N+1) only when the observed value is exchangeable."""
    x = np.asarray(x, dtype=float)
    b, n = int((x >= observed).sum()), len(x)
    return {"observed": float(observed), "draws": n, "draws_ge_observed": b, "rank_of_observed_from_top": b + 1,
            "rank_out_of": n + 1, "null_max": float(x.max()), "null_q95": float(np.quantile(x, .95)),
            "null_q99": float(np.quantile(x, .99)), "null_median": float(np.median(x)),
            "exact_conditional_permutation_p": (b + 1) / (n + 1) if exchangeable else None}


def expected_shell_means(x, shell, strata):
    """Exact expectation of the shell means of x under a uniform permutation of shell labels within strata."""
    _, inv = np.unique(strata, return_inverse=True)
    smean = np.bincount(inv, weights=x) / np.bincount(inv)
    return np.array([smean[inv[shell == k]].mean() for k in range(NSHELL)])


def frame_coefficients(zs, base=FRAME_BASE, slope=FRAME_SLOPE):
    """Glide+spin frame coefficients (microarcsec/yr) base + slope*z at each redshift -> [n,16]."""
    zs = np.asarray(zs, dtype=float)
    out = np.zeros((len(zs), NCOEF))
    out[:, :len(base)] = base + zs[:, None] * slope
    return out


def inject_rhs(X, Y, coeff):
    """Whitened data after adding B_i a_i to each proper motion (a_i in microarcsec/yr, y in mas/yr)."""
    return Y + np.einsum("nkj,nj->nk", X, coeff) / 1000.0


def curvature(f, s, w, keep):
    return (w @ g.shared_patch_refits(f[:, keep], s[:, keep])[0]).reshape(-1)


def effective_redshift_operator(F, Fz):
    """Z_s = F_s^-1 sum_i z_i X_i^T X_i per shell, for summed [4,16,16] blocks."""
    return np.stack([np.linalg.solve(F[k], Fz[k]) for k in range(len(F))])


def analytic_frame_leak(Z, w, slope16):
    """Curvature [2,16] of a frame linear in each source's own z with the given slope (base cancels)."""
    return np.einsum("rs,sij,j->ri", w, Z, slope16)


def configurations():
    allp = np.arange(NPATCH)
    return {"all48": allp, "excl_8_47": np.setdiff1d(allp, EXCLUDE)}


def load_r98():
    raw = Path(g.SOURCE).read_bytes()
    if sha256(raw).hexdigest() != g.SOURCE_SHA:
        raise ValueError("R98 receipt identity mismatch")
    src = json.loads(raw)
    meta = src["joint_160d_patch_covariance"]
    cache = Path(meta["cache_path"])
    if sha_file(cache) != meta["sha256"]:
        raise ValueError("R98 patch cache identity mismatch")
    with np.load(cache, allow_pickle=False) as d:
        f = np.stack([d[n + "__F"] for n in g.SHELLS])
        s = np.stack([d[n + "__s"] for n in g.SHELLS])
        nsrc = np.stack([d[n + "__n"] for n in g.SHELLS])
    return src, meta, f, s, nsrc


def load_quaia():
    with np.load(JOIN, allow_pickle=False) as z:
        d = {k: np.asarray(z[k]) for k in (
            "source_id", "ra", "dec", "redshift_quaia", "phot_g_mean_mag", "gaia_pmra", "gaia_pmdec",
            "gaia_pmra_error", "gaia_pmdec_error", "gaia_pmra_pmdec_corr", "gaia_ruwe",
            "gaia_astrometric_params_solved", "selection_relative")}
    yy = np.column_stack((d["gaia_pmra"], d["gaia_pmdec"])).astype(float)
    e1 = d["gaia_pmra_error"].astype(float)
    e2 = d["gaia_pmdec_error"].astype(float)
    rho = d["gaia_pmra_pmdec_corr"].astype(float)
    zq = d["redshift_quaia"].astype(float)
    sel = d["selection_relative"].astype(float)
    # Exact R98 qualification (scripts/r98/cross_survey.py gaia_run).
    valid = (np.isfinite(d["ra"]) & np.isfinite(d["dec"]) & np.isfinite(zq) & np.isfinite(yy).all(axis=1)
             & np.isfinite(e1) & np.isfinite(e2) & np.isfinite(rho) & (e1 > 0) & (e2 > 0) & (np.abs(rho) < .999)
             & (d["gaia_ruwe"] < 1.4) & (d["gaia_astrometric_params_solved"] == 31)
             & (np.abs(yy) < 100).all(axis=1) & (sel > 0))
    ii = np.flatnonzero(valid)
    if len(ii) != 634233:
        raise RuntimeError(f"Quaia qualified census changed: {len(ii)}")
    ra = np.deg2rad(d["ra"][ii].astype(float))
    dec = np.deg2rad(d["dec"][ii].astype(float))
    return {"source_id": d["source_id"][ii].astype(np.int64), "ra": ra, "dec": dec, "y": yy[ii],
            "e1": e1[ii], "e2": e2[ii], "rho": rho[ii], "z": zq[ii],
            "G": d["phot_g_mean_mag"][ii].astype(float), "patch": hp.ang2pix(2, np.pi / 2 - dec, ra),
            "shell": np.digitize(zq[ii], EDGES), "all_join_ids": d["source_id"].astype(np.int64)}


def load_crf3():
    cols = ("source_id", "ra", "dec", "pmra", "pmdec", "pmra_error", "pmdec_error", "pmra_pmdec_corr",
            "phot_g_mean_mag", "bp_rp", "ruwe", "astrometric_params_solved")
    with fits.open(CRF3, memmap=True) as h:
        t = h[1].data
        out = {c: np.asarray(t[c]) for c in cols}
    out["source_id"] = out["source_id"].astype(np.int64)
    for c in cols[1:]:
        out[c] = out[c].astype(float)
    return out


def lookup(ids_sorted, values_sorted, query):
    pos = np.clip(np.searchsorted(ids_sorted, query), 0, len(ids_sorted) - 1)
    hit = ids_sorted[pos] == query
    out = np.full(len(query), np.nan)
    out[hit] = values_sorted[pos[hit]]
    return out, hit


def quantile_bins(x, edges):
    b = np.digitize(x, edges)
    b[~np.isfinite(x)] = len(edges) + 1  # separate stratum for missing values
    return b


def quaia_bp_rp(q, crf3):
    order = np.argsort(crf3["source_id"])
    return lookup(crf3["source_id"][order], crf3["bp_rp"][order], q["source_id"])


def build_strata(q, crf3):
    """Strata for the Quaia permutations and the CRF3 complement assignment."""
    q_bprp, q_hit = quaia_bp_rp(q, crf3)
    g8 = np.quantile(q["G"], np.linspace(0, 1, 9)[1:-1])
    g4 = np.quantile(q["G"], [.25, .5, .75])
    c4 = np.quantile(q_bprp[np.isfinite(q_bprp)], [.25, .5, .75])
    strata = {
        "patch": q["patch"].astype(np.int64),
        "patch_gmag": q["patch"] * 16 + quantile_bins(q["G"], g8),
        "patch_gmag_colour": q["patch"] * 64 + quantile_bins(q["G"], g4) * 8 + quantile_bins(q_bprp, c4),
        "patch_colour": q["patch"] * 64 + quantile_bins(q_bprp, c4),
    }
    info = {"quaia_in_crf3_fits_by_source_id": int(q_hit.sum()),
            "quaia_bp_rp_finite": int(np.isfinite(q_bprp).sum()),
            "G_edges_8": g8.tolist(), "G_edges_4": g4.tolist(), "bp_rp_edges_4": c4.tolist(),
            "G_range_quaia": [float(q["G"].min()), float(q["G"].max())]}
    return strata, info, (g4, c4)


def excluded_quaia_ids(q):
    """Quaia source ids removed from the CRF3 complement: the qualified join plus the pinned full join."""
    check_pinned(FULL_JOIN, FULL_JOIN_SHA, "quaia_gaia_full_join")
    with np.load(FULL_JOIN, allow_pickle=False) as z:
        full = np.asarray(z["source_id"]).astype(np.int64)
    return np.union1d(np.unique(q["all_join_ids"]), full)


def complement_sample(q, crf3, g4, c4, match_g=True):
    excluded = excluded_quaia_ids(q)
    c = crf3
    yy = np.column_stack((c["pmra"], c["pmdec"]))
    gmin, gmax = q["G"].min(), q["G"].max()
    base = (np.isfinite(c["ra"]) & np.isfinite(c["dec"]) & np.isfinite(yy).all(axis=1)
            & np.isfinite(c["pmra_error"]) & np.isfinite(c["pmdec_error"]) & np.isfinite(c["pmra_pmdec_corr"])
            & (c["pmra_error"] > 0) & (c["pmdec_error"] > 0) & (np.abs(c["pmra_pmdec_corr"]) < .999)
            & (c["ruwe"] < 1.4) & (c["astrometric_params_solved"] == 31) & (np.abs(yy) < 100).all(axis=1))
    not_quaia = ~np.isin(c["source_id"], excluded)
    in_g = (c["phot_g_mean_mag"] >= gmin) & (c["phot_g_mean_mag"] <= gmax)
    keep = base & not_quaia & (in_g if match_g else True)
    ra = np.deg2rad(c["ra"][keep])
    dec = np.deg2rad(c["dec"][keep])
    patch = hp.ang2pix(2, np.pi / 2 - dec, ra)
    cbin = quantile_bins(c["bp_rp"][keep], c4)
    stratum = patch * 64 + (quantile_bins(c["phot_g_mean_mag"][keep], g4) * 8 + cbin if match_g else cbin)
    census = {"crf3_rows": int(len(c["source_id"])), "excluded_quaia_ids": int(len(excluded)),
              "crf3_quality_cuts": int(base.sum()), "crf3_quality_not_quaia": int((base & not_quaia).sum()),
              "crf3_quality_not_quaia_in_quaia_G_range": int((base & not_quaia & in_g).sum()),
              "complement_rows_used_before_stratum_match": int(keep.sum()), "G_matched": bool(match_g),
              "complement_G_quantiles_0_25_50_75_100": np.nanquantile(c["phot_g_mean_mag"][keep], [0, .25, .5, .75, 1]).tolist(),
              "complement_rows_missing_G": int((~np.isfinite(c["phot_g_mean_mag"][keep])).sum())}
    return {"source_id": c["source_id"][keep], "ra": ra, "dec": dec, "y": yy[keep], "e1": c["pmra_error"][keep],
            "e2": c["pmdec_error"][keep], "rho": c["pmra_pmdec_corr"][keep], "patch": patch,
            "stratum": stratum}, census


def permute_within(labels, strata, rng):
    """Uniform random permutation of labels inside each stratum."""
    by_stratum = np.argsort(strata, kind="stable")
    shuffled = np.lexsort((rng.random(len(strata)), strata))
    out = np.empty_like(labels)
    out[by_stratum] = labels[shuffled]
    return out


def assign_by_fraction(stratum_c, strata_q, shell_q, rng):
    nstr = int(max(stratum_c.max(), strata_q.max())) + 1
    counts = np.zeros((nstr, NSHELL))
    np.add.at(counts, (strata_q, shell_q), 1)
    tot = counts.sum(axis=1)
    usable = tot[stratum_c] > 0
    cum = np.cumsum(counts / np.maximum(tot, 1)[:, None], axis=1)
    u = rng.random(len(stratum_c))
    lab = (u[:, None] > cum[stratum_c][:, :NSHELL - 1]).sum(axis=1)
    return lab, usable


def composition_retention(q, q_bprp, strata, w):
    """Shell G / BP-RP curvature kept by each within-stratum permutation (exact expectation)."""
    g8 = np.quantile(q["G"], np.linspace(0, 1, 9)[1:-1])
    c4 = np.quantile(q_bprp[np.isfinite(q_bprp)], [.25, .5, .75])
    strat = {k: strata[k] for k in PERMUTATION_NULLS}
    strat["patch_gmag8_colour4__evaluated_not_run_as_null"] = (
        q["patch"] * 128 + quantile_bins(q["G"], g8) * 8 + quantile_bins(q_bprp, c4))
    out = {"scope": "Exact expectation of the shell means of a source property under a uniform within-stratum "
                    "permutation of the shell labels, pushed through the curvature rows; retained fraction = expected "
                    "curvature / observed curvature per row. Property curvature only, not a proper-motion statistic.",
           "G4_edges_subset_of_G8_edges": bool(np.all(np.isin(np.quantile(q["G"], [.25, .5, .75]), g8))),
           "properties": {}}
    for name, x in (("G", q["G"]), ("bp_rp", q_bprp)):
        obs = np.array([x[q["shell"] == k].mean() for k in range(NSHELL)])
        rec = {"observed_shell_means": obs.tolist(), "observed_curvature_rows": (w @ obs).tolist(), "strata": {}}
        for sname, st in strat.items():
            exp = expected_shell_means(x, q["shell"], st)
            rec["strata"][sname] = {"n_strata": int(len(np.unique(st))), "expected_shell_means": exp.tolist(),
                                    "expected_curvature_rows": (w @ exp).tolist(),
                                    "retained_fraction_rows": ((w @ exp) / (w @ obs)).tolist()}
        out["properties"][name] = rec
    return out


def quaia_row_diagnostics(f_ref, s_ref, w, z_med, cov1):
    """GNR-4 per-source frame injection and GNR-5 composition retention, from the pinned Quaia/CRF3 rows."""
    check_pinned(JOIN, JOIN_SHA, "quaia_crf3_join")
    check_pinned(CRF3, CRF3_SHA, "gaia_crf3_fits")
    q = load_quaia()
    crf3 = load_crf3()
    strata, strata_info, _ = build_strata(q, crf3)
    q_bprp, _ = quaia_bp_rp(q, crf3)
    del crf3
    X, Y = whiten(q["ra"], q["dec"], q["y"], q["e1"], q["e2"], q["rho"])
    f0, s0 = group_normal(X, Y, q["shell"], q["patch"])
    replay = {"F_max_rel": float(np.max(np.abs(f0 - f_ref)) / np.max(np.abs(f_ref))),
              "s_max_rel": float(np.max(np.abs(s0 - s_ref)) / np.max(np.abs(s_ref)))}
    if max(replay.values()) > 1e-10:
        raise ArithmeticError(f"source replay of R98 shell statistics failed: {replay}")
    _, s_med = group_normal(X, inject_rhs(X, Y, frame_coefficients(z_med[q["shell"]])), q["shell"], q["patch"])
    _, s_src = group_normal(X, inject_rhs(X, Y, frame_coefficients(q["z"])), q["shell"], q["patch"])
    unit = np.zeros((1, NCOEF))
    unit[0, 3] = 1.0
    _, s_unit = group_normal(X, inject_rhs(X, Y, q["z"][:, None] * unit), q["shell"], q["patch"])
    Fz, _ = group_normal(X * np.sqrt(q["z"])[:, None, None], Y, q["shell"], q["patch"])
    del X, Y
    i6 = STAT_SETS["spin6"]
    slope16 = np.zeros(NCOEF)
    slope16[:6] = FRAME_SLOPE
    leak = {"scope": "Frame injected into each qualified Quaia proper motion before the shell fits. 'shell_median' "
                     "evaluates base+slope*z at the source's shell median redshift (what the curvature rows annihilate); "
                     "'per_source' evaluates it at the source's own redshift. The leak is the change of the curvature "
                     "vector. Frame: R105 test frame base [8,-3,2,-4,5,6] uas/yr, slope [-3,4,5,2,-7,1] uas/yr per z on "
                     "glide+spin.", "frame_base_microasyr": FRAME_BASE.tolist(),
            "frame_slope_microasyr_per_z": FRAME_SLOPE.tolist(), "configs": {}}
    for name, keep in configurations().items():
        y0 = curvature(f0, s0, w, keep)
        lm = curvature(f0, s_med, w, keep) - y0
        ls = curvature(f0, s_src, w, keep) - y0
        lu = curvature(f0, s_unit, w, keep) - y0
        Z = effective_redshift_operator(f0[:, keep].sum(1), Fz[:, keep].sum(1))
        an = analytic_frame_leak(Z, w, slope16).reshape(-1)
        A = np.einsum("rs,sij->rij", w, Z)[:, 3:6, 3:6].reshape(6, 3)
        yobs = curvature(f_ref, s_ref, w, keep)
        sol, *_ = np.linalg.lstsq(A, yobs[i6], rcond=None)
        c6 = cov1[name][np.ix_(i6, i6)]
        leak["configs"][name] = {
            "shell_median_injection_leak_max_abs": float(np.max(np.abs(lm))),
            "per_source_injection_leak_max_abs": float(np.max(np.abs(ls))),
            "per_source_injection_leak_vector": ls.tolist(),
            "per_source_injection_spin6_leak": ls[i6].tolist(),
            "per_source_injection_spin6_Q_jk1": float(ls[i6] @ np.linalg.solve(c6, ls[i6])),
            "analytic_leak_minus_injection_max_abs": float(np.max(np.abs(an - ls))),
            "unit_spin_x_slope_per_source_leak_max_abs": float(np.max(np.abs(lu))),
            "unit_spin_x_slope_spin6_Q_jk1": float(lu[i6] @ np.linalg.solve(c6, lu[i6])),
            "precision_weighted_effective_z_spin_block": [float(np.trace(Z[k][3:6, 3:6]) / 3) for k in range(NSHELL)],
            "precision_weighted_effective_z_glide_block": [float(np.trace(Z[k][0:3, 0:3]) / 3) for k in range(NSHELL)],
            "shell_median_z": z_med.tolist(),
            "spin_slope_for_leak_only_explanation_microasyr_per_z": sol.tolist(),
            "spin_residual_fraction_after_leak_only_fit": float(np.linalg.norm(A @ sol - yobs[i6])
                                                                / np.linalg.norm(yobs[i6]))}
    diag = {"source_replay_vs_r98_cache": replay, "strata": strata_info,
            "quaia_pmra_error_median_mas_per_yr": float(np.median(q["e1"])),
            "z_linear_frame_leak": leak, "composition_retention": composition_retention(q, q_bprp, strata, w)}
    return diag


def r104_influence_replay(f, s, w):
    """Per row/sector delete-one top-5 and worst delete-two pair (R104 GAIA_PATCH_INFLUENCE replay)."""
    full, one, two, pairs = g.shared_patch_refits(f, s)
    meas, one_w, two_w = w @ full, w @ one, w @ two
    rows = {}
    for i in range(2):
        for sec, sl in g.SECTORS.items():
            n1 = np.linalg.norm(one_w[:, i, sl] - meas[i, sl], axis=1)
            n2 = np.linalg.norm(two_w[:, i, sl] - meas[i, sl], axis=1)
            rows[f"row{i}_{sec}"] = {"delete_one_top5_patches": np.argsort(n1)[::-1][:5].tolist(),
                                     "delete_one_top5_shift_norm": np.sort(n1)[::-1][:5].tolist(),
                                     "delete_two_worst_pair": pairs[int(np.argmax(n2))].tolist()}
    ref = json.loads(R104_JSON.read_text())
    match = all(rows[f"row{r['curvature_row']}_{r['sector']}"]["delete_one_top5_patches"] == r["delete_one_top5_patches"]
                and rows[f"row{r['curvature_row']}_{r['sector']}"]["delete_two_worst_pair"] == r["delete_two_worst_pair"]
                for r in ref["rows"])
    if not match:
        raise ArithmeticError("R104 patch-influence replay mismatch")
    return {"rows": rows, "matches_r104_gaia_patch_influence_json": match, "r104_json_sha256": sha_file(R104_JSON)}, \
        meas, one_w


def observed(args):
    t0 = time.monotonic()
    src, meta, f, s, nsrc = load_r98()
    z = np.asarray(src["redshift_bin_medians"])
    w = g.curvature_rows(z)
    r105_sha = check_pinned(R105_JSON, R105_JSON_SHA, "R105 GAIA_FRAME_PARITY.json")
    r105 = json.loads(R105_JSON.read_text())
    out = {"schema": "htt.r106.gaia_null_refit.observed/2", "units": "microarcsec/yr per unit z^2; Q dimensionless",
           "code_identity": code_identity(), "command": command_record(), "review_corrections": REVIEW_CORRECTIONS,
           "input_sha256": {"r98_receipt": g.SOURCE_SHA, "r98_patch_cache": meta["sha256"],
                            "r105_gaia_frame_parity_json": r105_sha, "quaia_crf3_join": JOIN_SHA,
                            "gaia_crf3_fits": CRF3_SHA},
           "median_redshifts": z.tolist(), "curvature_rows": w.tolist(), "excluded_patches": list(EXCLUDE),
           "configs": {}}
    centres = hp.pix2ang(2, np.array(EXCLUDE), lonlat=True)
    out["excluded_patch_icrs_centres_deg"] = {int(p): [float(a), float(b)] for p, a, b in zip(EXCLUDE, *centres)}
    out["excluded_patch_source_counts_per_shell"] = {int(p): nsrc[:, p].astype(int).tolist() for p in EXCLUDE}
    rhs_shifted = par.frame_shifted_rhs(f, s, z)
    mine = s + np.einsum("spij,sj->spi", f, frame_coefficients(z)) / 1000
    if not np.allclose(rhs_shifted, mine, rtol=1e-12, atol=1e-15 * np.max(np.abs(s))):
        raise ArithmeticError("frame constants differ from R105 frame_shifted_rhs")
    vec, cov1 = {}, {}
    for name, keep in configurations().items():
        y, c1, c2 = refit(f, s, w, keep)
        ys = (w @ g.shared_patch_refits(f[:, keep], rhs_shifted[:, keep])[0]).reshape(-1)
        rec = {"n_patches": int(len(keep)), "n_sources_per_shell": nsrc[:, keep].sum(axis=1).astype(int).tolist(),
               "curvature_vector_row0_row1": y.tolist(),
               "shell_fit_coefficients_microasyr": g.shared_patch_refits(f[:, keep], s[:, keep])[0].tolist(),
               "shell_median_affine_frame_rhs_injection_max_abs": float(np.max(np.abs(ys - y))),
               "shell_median_affine_frame_scope": "R105 frame injected at the shell MEDIAN redshifts, which the "
                                                  "curvature rows annihilate by construction; see "
                                                  "quaia_rows.z_linear_frame_leak for a per-source z-linear frame.",
               "jk1": qforms(y, c1), "jk2": qforms(y, c2),
               "jk1_r105_joint_modes": {k: v for k, v in par.joint_modes(y, c1).items()
                                         if not isinstance(v, list)},
               "jk1_eigenvalues_microasyr2": np.linalg.eigvalsh(c1).tolist(),
               "jk1_rank": int(np.linalg.matrix_rank(c1)),
               "sector_norms": {sec: [float(np.linalg.norm(y[i * 16:(i + 1) * 16][sl])) for i in range(2)]
                                for sec, sl in g.SECTORS.items()},
               "sector_jk1_rms": {sec: [float(np.sqrt(np.trace(c1[np.ix_(np.arange(i * 16, (i + 1) * 16)[sl],
                                                                              np.arange(i * 16, (i + 1) * 16)[sl])])))
                                       for i in range(2)] for sec, sl in g.SECTORS.items()}}
        out["configs"][name] = rec
        vec[name], cov1[name] = y, c1
    r = r105["covariance_diagnostics"]
    a = out["configs"]["all48"]
    out["r105_replay_abs_diff"] = {
        "jk1_joint32": abs(a["jk1"]["joint32"] - r["delete_1"]["joint_working_quadratic"]),
        "jk1_magnetic16": abs(a["jk1"]["magnetic16"] - r["delete_1"]["magnetic_marginal_working_quadratic"]),
        "jk1_electric16": abs(a["jk1"]["electric16"] - r["delete_1"]["electric_working_quadratic"]),
        "jk1_magnetic_rows_without_crosscov": abs(a["jk1"]["magnetic16_rows_without_crosscov"]
                                                  - r["delete_1"]["magnetic_row_0_plus_row_1_discarding_crosscov"]),
        "jk2_joint32": abs(a["jk2"]["joint32"] - r["delete_2"]["joint_working_quadratic"]),
        "jk2_magnetic16": abs(a["jk2"]["magnetic16"] - r["delete_2"]["magnetic_marginal_working_quadratic"]),
        "magnetic_vector_max_abs": float(np.max(np.abs(np.asarray(r105["magnetic_vector"])
                                                       - vec["all48"][par.MAG])))}
    if max(out["r105_replay_abs_diff"].values()) > 1e-8:
        raise ArithmeticError("R105 replay failed")
    # GNR-2/GNR-3: the selection rule on the observed data and the R104 ranking it comes from.
    infl, meas, one_w = r104_influence_replay(f, s, w)
    pairs = {rule: list(select_exclusion(meas, one_w, rule)) for rule in SECTOR_RULES}
    if any(p != sorted(EXCLUDE) for p in pairs.values()):
        raise ArithmeticError(f"R104 rule does not select {EXCLUDE} on the observed data: {pairs}")
    out["exclusion_selection"] = {
        "rule": "Top delete-one shift-norm patch in curvature row 0, then the top patch in row 1 that differs from it, "
                "on the data set's own all-48 delete-one refits; shift norm over the sector variant's coefficients.",
        "variants": {k: v.tolist() for k, v in SECTOR_RULES.items()}, "primary_variant": PRIMARY_RULE,
        "observed_pairs": pairs, "r104_influence_replay": infl}
    alt = {}
    for ex in ALT_EXCLUSIONS:
        y, c1, c2 = refit(f, s, w, np.setdiff1d(np.arange(NPATCH), ex))
        q1, q2 = qforms(y, c1), qforms(y, c2)
        alt["_".join(map(str, ex))] = {
            "excluded": list(ex), **{f"{k}__{st}": q[st] for k, q in (("jk1", q1), ("jk2", q2)) for st in RANK_STATS},
            "spin6_jk1_relative_change_vs_all48": q1["spin6"] / a["jk1"]["spin6"] - 1,
            "spin6_jk1_relative_change_vs_excl_8_47": q1["spin6"] / out["configs"]["excl_8_47"]["jk1"]["spin6"] - 1}
    out["alternative_exclusions_observed_only"] = {
        "scope": "Observed statistics only (no null tables): patch 32 is the top row-1 glide/spin patch and (43,47) the "
                 "worst delete-two pair in 7 of 8 row-sectors (r104_influence_replay).", "sets": alt,
        "max_abs_spin6_jk1_relative_change_vs_all48": max(abs(v["spin6_jk1_relative_change_vs_all48"])
                                                          for v in alt.values())}
    y48, c48 = vec["all48"], cov1["all48"]
    d = vec["excl_8_47"] - y48
    out["exclusion_shift"] = {
        "delta_curvature_vector": d.tolist(),
        "delta_norm_per_sector_row": {sec: [float(np.linalg.norm(d[i * 16:(i + 1) * 16][sl])) for i in range(2)]
                                      for sec, sl in g.SECTORS.items()},
        "delta_quadratic_in_all48_jk1_cov": float(d @ np.linalg.solve(c48, d)),
        "note": "the 46-patch vector is a subset refit of the same data, so delta is not independent of the 48-patch vector"}
    out["quaia_rows"] = quaia_row_diagnostics(f, s, w, z, cov1)
    out["runtime_seconds"] = time.monotonic() - t0
    out["maxrss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "observed.json").write_text(json.dumps(out, indent=1, allow_nan=False) + "\n")
    print(json.dumps({"observed": str(args.out / "observed.json"), "runtime_s": out["runtime_seconds"]}))


def null_context(kind):
    """Inputs of one null kind, identity-checked, with the R98 source replay."""
    src, meta, f_ref, s_ref, _ = load_r98()
    z = np.asarray(src["redshift_bin_medians"])
    w = g.curvature_rows(z)
    inputs = {"r98_receipt": g.SOURCE_SHA, "r98_patch_cache": meta["sha256"],
              "quaia_crf3_join": check_pinned(JOIN, JOIN_SHA, "quaia_crf3_join"),
              "gaia_crf3_fits": check_pinned(CRF3, CRF3_SHA, "gaia_crf3_fits")}
    q = load_quaia()
    crf3 = load_crf3()
    strata, strata_info, (g4, c4) = build_strata(q, crf3)
    Xq, Yq = whiten(q["ra"], q["dec"], q["y"], q["e1"], q["e2"], q["rho"])
    # Source-row replay of the R98 cache with the true redshift labels.
    f0, s0 = group_normal(Xq, Yq, q["shell"], q["patch"])
    replay = {"F_max_rel": float(np.max(np.abs(f0 - f_ref)) / np.max(np.abs(f_ref))),
              "s_max_rel": float(np.max(np.abs(s0 - s_ref)) / np.max(np.abs(s_ref)))}
    if max(replay.values()) > 1e-10:
        raise ArithmeticError(f"source replay of R98 shell statistics failed: {replay}")
    ctx = {"w": w, "q": q, "strata": strata, "strata_info": strata_info, "replay": replay, "inputs": inputs,
           "census": None, "Xq": Xq, "Yq": Yq}
    if kind in COMPLEMENTS:
        inputs["quaia_gaia_full_join"] = FULL_JOIN_SHA  # checked inside complement_sample
        match_g = kind == "crf3_complement"
        comp, ctx["census"] = complement_sample(q, crf3, g4, c4, match_g)
        ctx["Xc"], ctx["Yc"] = whiten(comp["ra"], comp["dec"], comp["y"], comp["e1"], comp["e2"], comp["rho"])
        ctx["comp"] = comp
        ctx["sq"] = strata["patch_gmag_colour" if match_g else "patch_colour"]
        ctx["n_strata"] = int(len(np.unique(comp["stratum"])))
    else:
        ctx["n_strata"] = int(len(np.unique(strata[kind])))
    return ctx


def draw(ctx, kind, rng):
    """One null realization of the shell x patch normal equations (same RNG use as the cached runs)."""
    q = ctx["q"]
    if kind in COMPLEMENTS:
        comp = ctx["comp"]
        lab, usable = assign_by_fraction(comp["stratum"], ctx["sq"], q["shell"], rng)
        f, s = group_normal(ctx["Xc"][usable], ctx["Yc"][usable], lab[usable], comp["patch"][usable])
        return f, s, np.nan, int(usable.sum()), np.bincount(lab[usable], minlength=NSHELL), usable
    lab = permute_within(q["shell"], ctx["strata"][kind], rng)
    f, s = group_normal(ctx["Xq"], ctx["Yq"], lab, q["patch"])
    return f, s, float(np.mean(lab != q["shell"])), len(lab), np.bincount(lab, minlength=NSHELL), None


def _store(n):
    return {"vec": np.empty((n, 32)), "jk1": {k: np.empty(n) for k in STAT_NAMES},
            "jk2": {k: np.empty(n) for k in STAT_NAMES}}


def _put(store, t, y, q1, q2):
    store["vec"][t] = y
    for key, qq in (("jk1", q1), ("jk2", q2)):
        for name, val in qq.items():
            store[key][name][t] = val


def run_draws(ctx, kind, seed, draws, fixed_draws, label):
    """all48, fixed-(8,47) (first fixed_draws) and per-draw rule-selected exclusions for each draw."""
    w, allp = ctx["w"], np.arange(NPATCH)
    fixed_keep = configurations()["excl_8_47"]
    rng = np.random.default_rng(seed)
    res = {"all48": _store(draws), "excl_8_47": _store(fixed_draws), **{r: _store(draws) for r in SECTOR_RULES}}
    pairs = {r: np.empty((draws, 2), dtype=np.int64) for r in SECTOR_RULES}
    changed, used = np.empty(draws), np.empty(draws, dtype=np.int64)
    shell_counts = np.empty((draws, NSHELL), dtype=np.int64)
    usable_ids, t0 = None, time.monotonic()
    for t in range(draws):
        f, s, changed[t], used[t], shell_counts[t], usable = draw(ctx, kind, rng)
        if usable is not None and usable_ids is None:
            usable_ids = np.sort(ctx["comp"]["source_id"][usable])
        y, c1, c2, meas, one_w = refit_parts(f, s, w, allp)
        _put(res["all48"], t, y, qforms(y, c1), qforms(y, c2))
        if t < fixed_draws:
            ye, c1e, c2e = refit(f, s, w, fixed_keep)
            _put(res["excl_8_47"], t, ye, qforms(ye, c1e), qforms(ye, c2e))
        sel = {r: select_exclusion(meas, one_w, r) for r in SECTOR_RULES}
        fitted = {}
        for p in sorted(set(sel.values())):
            ye, c1e, c2e = refit(f, s, w, np.setdiff1d(allp, p))
            fitted[p] = (ye, qforms(ye, c1e), qforms(ye, c2e))
        for r, p in sel.items():
            pairs[r][t] = p
            _put(res[r], t, *fitted[p])
        if (t + 1) % max(1, draws // 10) == 0:
            print(json.dumps({"stage": label, "kind": kind, "done": t + 1,
                              "elapsed_s": round(time.monotonic() - t0, 1)}), flush=True)
    return res, pairs, changed, used, shell_counts, usable_ids


def _flat(res, names):
    return {f"{c}__{k}__{n}": res[c][k][n] for c in names for k in ("jk1", "jk2") for n in STAT_NAMES}


def _pair_stats(p):
    tup = [tuple(int(v) for v in row) for row in p]
    return {"fraction_pair_is_8_47": float(np.mean([x == EXCLUDE for x in tup])),
            "fraction_pair_contains_8_or_47": float(np.mean([(8 in x) or (47 in x) for x in tup])),
            "n_distinct_pairs": len(set(tup)),
            "most_common_pairs": [[list(k), v] for k, v in Counter(tup).most_common(5)]}


def _write_selmatch(out, kind, seed, draws, res, pairs, usable_ids, receipt):
    arrays = {**{f"pairs__{r}": pairs[r] for r in SECTOR_RULES}, **{f"vec__{r}": res[r]["vec"] for r in SECTOR_RULES},
              **_flat(res, SECTOR_RULES)}
    if usable_ids is not None:
        arrays["usable_source_id"] = usable_ids
    path = out / f"selmatch_{kind}.npz"
    np.savez_compressed(path, **arrays)
    receipt.update({"schema": "htt.r106.gaia_null_refit.selmatch/1", "kind": kind, "seed": seed, "draws": draws,
                    "rules": {k: v.tolist() for k, v in SECTOR_RULES.items()}, "primary_rule": PRIMARY_RULE,
                    "pair_statistics": {r: _pair_stats(pairs[r]) for r in SECTOR_RULES},
                    "rule_pair_agreement": {f"{a}_vs_{b}": float(np.mean(np.all(pairs[a] == pairs[b], axis=1)))
                                            for a, b in (("EB", "B2"), ("EB", "E2"), ("B2", "E2"))},
                    "npz_sha256": sha_file(path), "review_corrections": REVIEW_CORRECTIONS})
    (out / f"selmatch_{kind}.json").write_text(json.dumps(receipt, indent=1, allow_nan=False) + "\n")


def _complement_info(ctx, usable_ids):
    if usable_ids is None:
        return None
    comp = ctx["comp"]
    mask = np.isin(comp["source_id"], usable_ids)
    return {"usable_rows": int(len(usable_ids)), "usable_source_id_sha256": sha256(usable_ids.tobytes()).hexdigest(),
            "usable_pmra_error_median_mas_per_yr": float(np.median(comp["e1"][mask])),
            "usable_overlap_with_quaia_qualified_ids": int(np.isin(usable_ids, ctx["q"]["source_id"]).sum())}


def null(args):
    """Fresh null draws: the R106 tables (all48, fixed 8/47) plus the selection-matched exclusion."""
    t0 = time.monotonic()
    ctx = null_context(args.kind)
    res, pairs, changed, used, shell_counts, usable_ids = run_draws(ctx, args.kind, args.seed, args.draws,
                                                                     args.draws, "null")
    args.out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.out / f"null_{args.kind}.npz", changed=changed, used=used, shell_counts=shell_counts,
                        **{f"vec__{c}": res[c]["vec"] for c in configurations()}, **_flat(res, configurations()))
    common = {"code_identity": code_identity(), "command": command_record(), "input_sha256": ctx["inputs"],
              "source_replay_vs_r98_cache": ctx["replay"], "complement_usable": _complement_info(ctx, usable_ids),
              "runtime_seconds": time.monotonic() - t0, "maxrss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    receipt = {"schema": "htt.r106.gaia_null_refit.null/2", "kind": args.kind, "draws": args.draws, "seed": args.seed,
               **common, "strata": ctx["strata_info"], "complement_census": ctx["census"], "n_strata": ctx["n_strata"],
               "npz_sha256": sha_file(args.out / f"null_{args.kind}.npz"), "review_corrections": REVIEW_CORRECTIONS}
    (args.out / f"null_{args.kind}.json").write_text(json.dumps(receipt, indent=1, allow_nan=False) + "\n")
    _write_selmatch(args.out, args.kind, args.seed, args.draws, res, pairs, usable_ids,
                    {**common, "replay_vs_cache": None, "generated_with_null_draws": True})
    print(json.dumps({"kind": args.kind, "runtime_s": time.monotonic() - t0, "replay": ctx["replay"]}))


def selmatch(args):
    """Replay cached null draws (same seed and RNG use), check them bit-for-bit, add the selected exclusion."""
    t0 = time.monotonic()
    rec_path, npz_path = args.cache_dir / f"null_{args.kind}.json", args.cache_dir / f"null_{args.kind}.npz"
    rec = json.loads(rec_path.read_text())
    if sha_file(npz_path) != rec["npz_sha256"]:
        raise ValueError(f"null cache identity mismatch for {args.kind}")
    draws = rec["draws"] if args.limit is None else min(args.limit, rec["draws"])
    ctx = null_context(args.kind)
    if ctx["census"] != rec["complement_census"]:
        raise ArithmeticError("complement census differs from the cached receipt")
    if ctx["strata_info"] != rec["strata"] or ctx["n_strata"] != rec["n_strata"]:
        raise ArithmeticError("strata differ from the cached receipt")
    fixed = min(args.verify_fixed, draws)
    res, pairs, changed, used, shell_counts, usable_ids = run_draws(ctx, args.kind, rec["seed"], draws, fixed,
                                                                     "selmatch")
    diff = {}
    with np.load(npz_path) as d:
        for c, n in (("all48", draws), ("excl_8_47", fixed)):
            diff[f"{c}_vec_max_abs"] = float(np.max(np.abs(res[c]["vec"] - d[f"vec__{c}"][:n])))
            diff[f"{c}_stat_max_rel"] = max(
                float(np.max(np.abs(res[c][k][s_] - d[f"{c}__{k}__{s_}"][:n])
                             / np.maximum(np.abs(d[f"{c}__{k}__{s_}"][:n]), 1e-300)))
                for k in ("jk1", "jk2") for s_ in STAT_NAMES)
        diff["used_equal"] = bool(np.array_equal(used, d["used"][:draws]))
        diff["shell_counts_equal"] = bool(np.array_equal(shell_counts, d["shell_counts"][:draws]))
        diff["changed_equal"] = bool(np.array_equal(changed, d["changed"][:draws], equal_nan=True))
    if (max(v for v in diff.values() if isinstance(v, float)) > 1e-12
            or not all(v for v in diff.values() if isinstance(v, bool))):
        raise ArithmeticError(f"cached null draws do not replay: {diff}")
    diff.update({"draws_checked_all48": draws, "draws_checked_fixed_8_47": fixed})
    args.out.mkdir(parents=True, exist_ok=True)
    _write_selmatch(args.out, args.kind, rec["seed"], draws, res, pairs, usable_ids, {
        "code_identity": code_identity(), "command": command_record(), "input_sha256": ctx["inputs"],
        "cached_null_receipt_sha256": sha_file(rec_path), "cached_null_npz_sha256": rec["npz_sha256"],
        "replay_vs_cache": diff, "source_replay_vs_r98_cache": ctx["replay"],
        "complement_usable": _complement_info(ctx, usable_ids), "generated_with_null_draws": False,
        "runtime_seconds": time.monotonic() - t0, "maxrss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
    print(json.dumps({"kind": args.kind, "draws": draws, "runtime_s": time.monotonic() - t0, "replay": diff}))


def hotelling_reference(p, n):
    """p(n-1)/(n-p) F(p, n-p): idealized iid-Gaussian-patch reference, not a calibration."""
    from scipy.stats import f as fdist
    m = n - p
    scale = p * (n - 1) / m
    return {"mean": float(scale * m / (m - 2)) if m > 2 else None,
            "q95": float(scale * fdist.ppf(.95, p, m)), "q99": float(scale * fdist.ppf(.99, p, m))}


def stat_table(x, o):
    return {"observed": o, "null_mean": float(x.mean()), "null_sd": float(x.std(ddof=1)),
            "null_q05_q50_q95_q99": np.quantile(x, [.05, .5, .95, .99]).tolist(),
            "null_max": float(x.max()), "draws_ge_observed": int((x >= o).sum()),
            "draws": int(len(x)), "observed_over_null_median": float(o / np.median(x))}


def ensemble_block(v, yo, exchangeable):
    mu, cv = v.mean(axis=0), np.cov(v, rowvar=False)
    out = {"null_mean_curvature_norm_per_sector_row": {
               sec: [float(np.linalg.norm(mu[i * 16:(i + 1) * 16][sl])) for i in range(2)]
               for sec, sl in g.SECTORS.items()},
           "null_ensemble_rms_per_sector_row": {
               sec: [float(np.sqrt(np.trace(cv[np.ix_(np.arange(i * 16, (i + 1) * 16)[sl],
                                                      np.arange(i * 16, (i + 1) * 16)[sl])])))
                     for i in range(2)] for sec, sl in g.SECTORS.items()}}
    if exchangeable:
        dlt = yo - mu
        out["observed_quadratic_in_null_ensemble_cov_joint32"] = float(yo @ np.linalg.solve(cv, yo))
        out["observed_minus_null_mean_quadratic_in_null_ensemble_cov_joint32"] = float(dlt @ np.linalg.solve(cv, dlt))
        out["null_mean_quadratic_in_null_ensemble_cov_joint32"] = float(mu @ np.linalg.solve(cv, mu))
    return out


def summarize(args):
    obs_path = args.out / "observed.json"
    obs = json.loads(obs_path.read_text())
    if any(p != sorted(EXCLUDE) for p in obs["exclusion_selection"]["observed_pairs"].values()):
        raise ArithmeticError("observed exclusion is not the rule-selected pair")
    oc = obs["configs"]
    o_ex = oc["excl_8_47"]
    inputs = {"observed.json": sha_file(obs_path)}
    commands = {"observed": obs["command"]}
    report = {"schema": "htt.r106.gaia_null_refit/2", "units": obs["units"],
              "estimator": "R98 shell x patch normal equations -> R103 curvature rows at shell medians (both, 32 dim) -> "
                           "shared-patch delete-one/delete-two jackknife covariance -> quadratic forms",
              "code_identity": code_identity(), "review_corrections": REVIEW_CORRECTIONS,
              "calibrated_p": None, "significance_sigma": None, "physical_Pi": None, "physical_GF": None}
    dims = {k: len(v) for k, v in STAT_SETS.items()}
    hot = {c: {k: hotelling_reference(p, n) for k, p in dims.items()} for c, n in (("all48", 48), ("excl", 46))}
    nulls, ranks, sel_summary, ratio_spread, hot_ratio = {}, {}, {}, {}, {}
    usable = {}
    for kind in NULLS:
        rec = json.loads((args.out / f"null_{kind}.json").read_text())
        smr = json.loads((args.out / f"selmatch_{kind}.json").read_text())
        for key in ("null", "selmatch"):
            jp, zp = args.out / f"{key}_{kind}.json", args.out / f"{key}_{kind}.npz"
            inputs[jp.name], inputs[zp.name] = sha_file(jp), sha_file(zp)
        if inputs[f"null_{kind}.npz"] != rec["npz_sha256"] or inputs[f"selmatch_{kind}.npz"] != smr["npz_sha256"]:
            raise ValueError(f"null cache identity mismatch for {kind}")
        if smr["draws"] != rec["draws"] or smr["seed"] != rec["seed"]:
            raise ValueError(f"selection-matched replay does not cover the cached draws of {kind}")
        if not smr["generated_with_null_draws"] and smr.get("cached_null_receipt_sha256") != inputs[f"null_{kind}.json"]:
            raise ValueError(f"selection-matched replay was made against another cached receipt for {kind}")
        commands[f"selmatch_{kind}"] = smr["command"]
        commands[f"null_{kind}"] = rec.get("command", {"reconstructed_from_logs_run_nulls_sh_and_jobs_txt": (
            f".venv/bin/python -B -m scripts.r106.gaia_null_refit null --kind {kind} --draws {rec['draws']} "
            f"--seed {rec['seed']} --out {OUT}")})
        exch = kind in PERMUTATION_NULLS
        entry = {"receipt": rec, "selmatch_receipt": smr, "configs": {}, "exchangeable_with_observed": exch}
        with np.load(args.out / f"null_{kind}.npz") as d, np.load(args.out / f"selmatch_{kind}.npz") as e:
            ch = d["changed"]
            entry["label_change_fraction_mean"] = None if np.all(np.isnan(ch)) else float(np.nanmean(ch))
            entry["sources_used_per_draw"] = [int(d["used"].min()), int(d["used"].max())]
            entry["shell_counts_mean"] = d["shell_counts"].mean(axis=0).tolist()
            if "usable_source_id" in e:
                usable[kind] = e["usable_source_id"]
            src = {"all48": (d, "all48", oc["all48"]),
                   **{f"excl_selected__{r}": (e, r, o_ex) for r in SECTOR_RULES}}
            for cname, (store, prefix, ob) in src.items():
                cc = {}
                if cname in ("all48", f"excl_selected__{PRIMARY_RULE}"):
                    cc.update(ensemble_block(store[f"vec__{prefix}"], np.asarray(ob["curvature_vector_row0_row1"]), exch))
                for key in ("jk1", "jk2"):
                    cc[key] = {n: stat_table(store[f"{prefix}__{key}__{n}"], ob[key][n]) for n in STAT_NAMES}
                if cname.startswith("excl_selected"):
                    cc["observed_exclusion"] = list(EXCLUDE)
                    cc["null_exclusion"] = f"per-draw R104 rule, variant {prefix}"
                entry["configs"][cname] = cc
                for n in RANK_STATS:
                    for key in ("jk1", "jk2"):
                        ranks.setdefault(n, {}).setdefault(cname, {}).setdefault(key, {})[kind] = null_rank(
                            store[f"{prefix}__{key}__{n}"], ob[key][n], exch)
                hc = "all48" if cname == "all48" else "excl"
                if cname in ("all48", f"excl_selected__{PRIMARY_RULE}"):
                    hot_ratio.setdefault(kind, {})[cname] = {
                        f"{key}__{n}": float(np.quantile(store[f"{prefix}__{key}__{n}"], .95) / hot[hc][n]["q95"])
                        for key in ("jk1", "jk2") for n in STAT_SETS}
            ratio = {}
            for r in SECTOR_RULES:
                ratio[r] = {}
                for key in ("jk1", "jk2"):
                    for n in RATIO_STATS:
                        x = e[f"{r}__{key}__{n}"] / d[f"all48__{key}__{n}"]
                        o = o_ex[key][n] / oc["all48"][key][n]
                        ratio[r][f"{key}__{n}"] = {"observed": o, "null_q05_q50_q95_q99": np.quantile(
                            x, [.05, .5, .95, .99]).tolist(), "draws_ge_observed": int((x >= o).sum()), "draws": int(len(x))}
            entry["exclusion_ratio_selected_over_all48"] = ratio
            fixed = {}
            for key in ("jk1", "jk2"):
                fixed[key] = {n: stat_table(d[f"excl_8_47__{key}__{n}"], o_ex[key][n]) for n in STAT_NAMES}
            fratio = {}
            for key in ("jk1", "jk2"):
                for n in RATIO_STATS:
                    x = d[f"excl_8_47__{key}__{n}"] / d[f"all48__{key}__{n}"]
                    o = o_ex[key][n] / oc["all48"][key][n]
                    fratio[f"{key}__{n}"] = {"observed": o, "draws_ge_observed": int((x >= o).sum()), "draws": int(len(x)),
                                             "null_q05_q50_q95_q99": np.quantile(x, [.05, .5, .95, .99]).tolist()}
            entry["fixed_patch_conditional_diagnostic"] = {
                "scope": "Every null draw removes the fixed patches 8 and 47, which were selected on the observed data "
                         "only. Conditional on fixed patches; NOT comparable to the post-selected observed exclusion. "
                         "Use excl_selected__* and exclusion_ratio_selected_over_all48 instead.",
                "excl_8_47_fixed": fixed, "exclusion_ratio_fixed": fratio}
            for key in ("jk1", "jk2"):
                for n in RATIO_STATS:
                    ratio_spread.setdefault(f"{key}__{n}", {})[kind] = {
                        "observed": o_ex[key][n] / oc["all48"][key][n],
                        "draws": int(len(d["used"])),
                        "draws_ge_observed_by_rule": {r: ratio[r][f"{key}__{n}"]["draws_ge_observed"] for r in SECTOR_RULES},
                        "draws_ge_observed_min_max_over_rules": [
                            min(ratio[r][f"{key}__{n}"]["draws_ge_observed"] for r in SECTOR_RULES),
                            max(ratio[r][f"{key}__{n}"]["draws_ge_observed"] for r in SECTOR_RULES)],
                        "draws_ge_observed_fixed_8_47_conditional": fratio[f"{key}__{n}"]["draws_ge_observed"]}
        sel_summary[kind] = {"pair_statistics": smr["pair_statistics"], "rule_pair_agreement": smr["rule_pair_agreement"]}
        nulls[kind] = entry
    # GNR-1: null structure.
    gm, ag = usable.get("crf3_complement"), usable.get("crf3_complement_all_g")
    shared = int(np.isin(gm, ag).sum()) if gm is not None and ag is not None else None
    qrows = nulls["patch"]["selmatch_receipt"]
    structure = {
        "pooled_counts": "Not reported. Draws of different nulls test different hypotheses on shared or fixed rows and "
                         "are never pooled; there is no exceedance bound from a pooled draw count.",
        "same_source_permutation_nulls": {
            "kinds": list(PERMUTATION_NULLS),
            "description": "Relabelings of ONE Quaia realization: the same qualified Quaia rows (positions, proper "
                           "motions, noise) with redshift-shell labels permuted within strata.",
            "rows_per_draw": {k: nulls[k]["sources_used_per_draw"] for k in PERMUTATION_NULLS},
            "hypotheses": {"patch": "z labels exchangeable within each NSIDE-2 patch",
                           "patch_gmag": "exchangeable within patch x 8 G-quantile strata",
                           "patch_gmag_colour": "exchangeable within patch x 4 G x 4 BP-RP strata"},
            "nesting": "Patch-level exchangeability implies exchangeability within both refinements. patch x G8 and "
                       "patch x G4 x BP-RP4 both refine patch x G4 (G4 edges are G8 edges; "
                       f"G4_edges_subset_of_G8_edges={obs['quaia_rows']['composition_retention']['G4_edges_subset_of_G8_edges']}) "
                       "but neither refines the other.",
            "p_value_rule": "(b+1)/(N+1) with b = draws >= observed is an exact conditional (Monte Carlo) permutation "
                            "p-value for the stated within-stratum exchangeability of this one realization and a "
                            "pre-specified statistic. The three nulls share one realization: their p-values are not "
                            "independent evidence and are not combined."},
        "complement_nulls": {
            "kinds": list(COMPLEMENTS),
            "description": "Relabelings of two FIXED Gaia-CRF3 complement samples; only the pseudo-shell labels are "
                           "redrawn.",
            "usable_rows": {k: int(len(v)) for k, v in usable.items()},
            "g_matched_rows_shared_with_all_g": shared,
            "g_matched_is_strict_subset_of_all_g": bool(shared == len(gm) and len(gm) < len(ag)) if shared is not None else None,
            "usable_pmra_error_median_mas_per_yr": {k: nulls[k]["selmatch_receipt"]["complement_usable"][
                "usable_pmra_error_median_mas_per_yr"] for k in COMPLEMENTS},
            "quaia_pmra_error_median_mas_per_yr": obs["quaia_rows"]["quaia_pmra_error_median_mas_per_yr"],
            "overlap_with_quaia_qualified_ids": {k: nulls[k]["selmatch_receipt"]["complement_usable"][
                "usable_overlap_with_quaia_qualified_ids"] for k in COMPLEMENTS},
            "p_value_rule": None,
            "why_no_p": "Observed curvature comes from the Quaia rows; complement draws come from other fixed sources "
                        "with other noise, so the observed value is not exchangeable with them. Rank only."},
        "post_selection": "Spin was singled out after R104 saw these data (R104 RESULTS_KO.md sec. 3) among 11 statistics "
                          "x 2 configurations x 2 jackknifes; permutation p-values for spin6 are conditional on that "
                          "choice and are not corrected for it.",
        "quaia_rows_checked_in_replay": qrows["source_replay_vs_r98_cache"]}

    def line(stat, cname, key):
        parts = []
        for kind in NULLS:
            rr = ranks[stat][cname][key][kind]
            pv = rr["exact_conditional_permutation_p"]
            parts.append(f"{kind} {rr['draws_ge_observed']}/{rr['draws']} (max {rr['null_max']:.4g}, q99 "
                         f"{rr['null_q99']:.4g}" + (f", permutation p={pv:.3g})" if pv is not None else ", rank only)"))
        return f"{stat} {cname} {key}: observed {ranks[stat][cname][key][NULLS[0]]['observed']:.6g}; " + "; ".join(parts)

    report["headline_per_null"] = [line(st, c, k) for st in RANK_STATS
                                   for c in ("all48", f"excl_selected__{PRIMARY_RULE}") for k in ("jk1", "jk2")]
    report["per_null_ranks"] = ranks
    report["null_structure"] = structure
    report["exclusion_selection"] = {
        "rule": obs["exclusion_selection"]["rule"], "variants": obs["exclusion_selection"]["variants"],
        "primary_variant": PRIMARY_RULE, "observed_pairs": obs["exclusion_selection"]["observed_pairs"],
        "per_null_selected_pairs": sel_summary, "ratio_rule_spread": ratio_spread,
        "scope": "The observed exclusion (8,47) is post-selected; each null draw applies the same rule to its own "
                 "data. Ratio exceedances and excl_selected tables are selection-matched; the fixed-(8,47) values are "
                 "a conditional diagnostic only."}
    report["observed"] = obs
    report["nulls"] = nulls
    allr = [v for k in hot_ratio.values() for c in k.values() for v in c.values()]
    report["idealized_hotelling_reference"] = {
        "scope": "Idealized reference: p(n-1)/(n-p) F(p, n-p) for iid Gaussian patch contributions and a linear "
                 "delete-one jackknife. NOT a calibration. Same-estimator null q95 / Hotelling q95 exceeds 1 in "
                 f"{sum(v > 1 for v in allr)} of {len(allr)} null x configuration x jackknife x statistic cells "
                 f"(range {min(allr):.3g}-{max(allr):.3g}), so reading observed values against it would be "
                 "anti-conservative where the ratio exceeds 1.",
        "all48": hot["all48"], "excl_46_patches": hot["excl"], "empirical_over_hotelling_q95": hot_ratio}
    rp = obs["r105_replay_abs_diff"]
    rep = {k: nulls[k]["selmatch_receipt"]["replay_vs_cache"] for k in NULLS}
    leak = obs["quaia_rows"]["z_linear_frame_leak"]["configs"]["all48"]
    report["claim_classes"] = {
        "numerical_convergence": {
            "r105_replay_max_abs": max(rp.values()),
            "r98_source_replay": obs["quaia_rows"]["source_replay_vs_r98_cache"],
            "cached_null_draw_replay": rep,
            "statement": "Replays and refits reproduce cached values; this certifies the arithmetic, not any "
                         "scientific claim."},
        "conditional_prediction": {
            "statement": "Permutation p-values are conditional on one Quaia realization, on within-stratum "
                         "z-exchangeability and on the post-selected statistic; the excluded-configuration and ratio "
                         "results are conditional on the R104 selection rule applied per draw. Complement nulls give "
                         "ranks only."},
        "physical_attribution": {
            "statement": "None. No null models AGIS scan, AGN-centroid or noise physics; physical_Pi and physical_GF "
                         "are None. The per-source z-linear frame leak quantifies one frame-systematic pathway only.",
            "per_source_frame_leak_all48_max_abs_microasyr_per_z2": leak["per_source_injection_leak_max_abs"],
            "per_source_frame_leak_all48_spin6_Q_jk1": leak["per_source_injection_spin6_Q_jk1"]}}
    report["provenance"] = {"input_sha256": inputs, "commands": {**commands, "summarize": command_record()},
                            "cached_null_run_logs": {p.name: sha_file(p) for p in sorted((args.out / "logs").glob(
                                "*")) if p.is_file() and p.name in ("run_nulls.sh", "jobs.txt")}}
    report["interpretation_scope"] = (
        "Every null is a randomization of real catalogue rows through the identical estimator; none is an independent "
        "noise/AGIS-scan/AGN-centroid mock ensemble, so no significance or calibrated p is produced. Permutation nulls "
        "test within-stratum z-exchangeability of one realization and get an exact conditional permutation p per null; "
        "complement nulls use disjoint fixed sources and get ranks only; nulls are never pooled. The excluded "
        "configuration is selection-matched per draw.")
    (args.out / "GAIA_NULL_REFIT.json").write_text(json.dumps(report, indent=1, allow_nan=False) + "\n")
    print(json.dumps({"summary": str(args.out / "GAIA_NULL_REFIT.json")}))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("observed")
    a.add_argument("--out", type=Path, default=OUT)
    b = sub.add_parser("null")
    b.add_argument("--kind", choices=NULLS, required=True)
    b.add_argument("--draws", type=int, default=1000)
    b.add_argument("--seed", type=int, required=True)
    b.add_argument("--out", type=Path, default=OUT)
    m = sub.add_parser("selmatch")
    m.add_argument("--kind", choices=NULLS, required=True)
    m.add_argument("--cache-dir", type=Path, default=OUT)
    m.add_argument("--out", type=Path, default=OUT)
    m.add_argument("--limit", type=int, default=None, help="replay only the first N cached draws (smoke test)")
    m.add_argument("--verify-fixed", type=int, default=25, help="draws whose fixed-(8,47) refit is checked")
    c = sub.add_parser("summarize")
    c.add_argument("--out", type=Path, default=OUT)
    args = p.parse_args()
    {"observed": observed, "null": null, "selmatch": selmatch, "summarize": summarize}[args.cmd](args)


if __name__ == "__main__":
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    main()
