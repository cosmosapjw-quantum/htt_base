"""R106 D4: CF3 / CF4 / 6dFGSv / 2MRS object and calibration lineage, with exclusion-fold rescoring.

The R105 relative held-out scores (CF4_FIELD_HOLDOUT.json from
scripts/r105/cf4_field_holdout.py and CF4_CORAS_MARKS.json from
scripts/r105/cf4_coras_marks.py) predict 6dFGSv Table 1 log-distance marks with
the R104 2MRS-NeuralNet velocity grid and with 2MRS-constrained CORAS fields
whose growth rate (f sigma8 = 0.405) and external bulk flow (95, -172, 28) km/s
were calibrated by CORAS on Cosmicflows-3 (CF3) group distances.  CF3 itself
contains the 6dFGSv Fundamental-Plane distances.  This module

1. cross-matches the 8,885 6dFGSv rows to CF4 table2 (R103 rule: 15 arcsec,
   500 km/s), to the CF3 member catalogue distributed with CORAS (PGC route and
   sky+cz route) and to the 2MRS group-member catalogue read by the CORAS pilot
   (sky+cz route and 2MASS/6dF designation-coordinate route);
2. reproduces the CORAS pilot 2MRS input cut (frame, Ks limit, partial volume
   limit, maximum radius; before zone-of-avoidance cloning) and the CORAS
   parameter-estimation window for CF3 groups (2000 <= cz <= 16000 km/s in the
   CMB and LG frames).  The 5-sigma clip of CORAS needs the fiducial
   reconstruction and is not reproduced: window membership is a superset of
   calibration membership;
3. counts CF4 galaxies and R98 groups that are CF3 members by CF4 method and,
   for FP, by survey (6dFGSv, SDSS PV, other);
4. measures the common zero points among CF3, CF4 and 6dFGSv distance moduli;
5. rescores the R105 relative held-out scores on exclusion folds: overlapping
   objects are removed from the R105 held-out test sets with training unchanged
   ("test_only"), or from both train and test with the selection probit refit
   ("drop"); each against cz x inclusion stratified random-exclusion controls.

Review corrections (R106 review CF3-1..CF3-4):

* The 2MRS exclusion sets are defined by an apparent-magnitude cut (2MRS Ks
  limit), which selects 6dFGSv rows with a cz-dependent mark zero point.  Their
  test_only and non-recentred drop scores are therefore NOT comparable to the
  cz x inclusion controls; each such block carries comparable_to_controls=false
  and a mark-zero-point confound record (kept set vs the same control masks).
  The comparable statistic is drop mode with the mark zero point removed per
  2000 km/s cz bin (drop_recentered_czbin), against cz x inclusion controls and
  against cz x inclusion x epsilon_d-quintile controls.  Control fractions of
  non-comparable blocks are not overlap or leakage evidence.
* CORAS scores are conditional on the CF3-calibrated f sigma8 = 0.405 and
  external bulk (95, -172, 28) km/s; they are not held out with respect to the
  CF3 calibration.  The CF3_calibration_window fold only scores the cz-edge
  rows outside the window and has no power for full-sample parameter leakage.
  A bulk decomposition and a parameter-sensitivity bound are computed here.
* "CF3 member" is operational: a match to the CORAS-distributed CF3 member file
  (not VizieR table3).  A tight position-only route (2 arcsec, no cz gate) is
  reported beside it.  Exclusions leaving no selected held-out row are marked
  degenerate with null fractions; every control fraction carries k, (k+1)/(R+1)
  and the resolution 1/(R+1).

Every score here is a conditional working-model log predictive difference.
No calibrated p-value, no physical Pi/G_F attribution.
"""
import argparse
import hashlib
import json
import multiprocessing as mp
import os
import platform
import re
import resource
import shlex
import shutil
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree
from scipy.special import logsumexp
from scipy.stats import chi2 as chi2_dist

ROOT = Path(__file__).resolve().parents[2]
R105 = ROOT / "docs/research_program/observational_publication_20261015/R105_RESEARCH_20261124"
HOME = Path.home()
DONOR = HOME / "Downloads/htt_r105_coras/deps/CORAS"
DONOR_COMMIT = "45ab25635aa32869ce207511d556ea257ab8a591"
DEFAULT_OUT = HOME / "Downloads/htt_r106_analysis/cf3"
DEFAULT_CORAS = [f"{HOME}/Downloads/htt_r105_coras/sixdf8={R105}/CF4_CORAS_MARKS.json"]
CF3_README = ROOT / ".agent-harness/runs/R9-SELECTED-LAW-20260913/artifacts/calibration_candidate/sources/CF3_ReadMe.txt"
CF3_TABLE3_EXPECTED = {
    "catalogue": "VizieR J/AJ/152/50 table3.dat (Tully, Courtois & Sorce 2016), 17,669 rows",
    "recorded_path": "/home/cosmosapjw/.cache/htt-r9/cf3_tempel_2017/CF3_table3.dat",
    "bytes": 7191283,
    "sha256": "8acd4718ffe370e58d9747ffa3d8aeafcf3f554c698c82c00f29f5dec270aa19",
    "url": "https://cdsarc.cds.unistra.fr/ftp/J/AJ/152/50/table3.dat",
    "recorded_in": "docs/research_program/tensor_joint_r9/revision2/selected_law/acquired_inputs.json",
    "needed_columns": "r_Dist (bytes 29-41, source letters C/T/L/M/S/N/H/I/F/P), o_Dist, DM-P/e_DM-P "
                      "(6dFGS FP with CF3 zero point), DM-I, DM-N, DM-CF2, Nest",
}
C = 299792.458
ARCSEC, DV = 15., 500.
CZ_BIN = 500.
CZ_RECENTER_BIN = 2000.      # km/s; cz-binned mark recentring (review CF3-1)
RECENTER_MIN_ROWS = 5        # selected training rows needed for a bin's own zero point
TIGHT_ARCSEC = 2.            # position-only CF3 route, no cz gate (review CF3-3)
CF3_FP_ERROR_FINGERPRINT = .50   # CF3 ReadMe e_DM-P [0.5]: 6dFGS FP error, a 6dF-attribution proxy
METHODS = (("SNIa", "dmsn"), ("TF", "dmtf"), ("FP", "dmfp"), ("SBF", "dmsbf"), ("SNII", "dmsn2"),
           ("TRGB", "dmtrgb"), ("Cepheid", "dmceph"), ("Maser", "dmmas"))
# Exclusion sets whose membership is defined by the 2MRS apparent-magnitude (Ks) limit, alone or in a union.
MAGNITUDE_DEFINED = ("2MRS_galaxy", "2MRS_coras_input", "complement_keep_only_2MRS_coras_input",
                     "union_2MRS_coras_or_CF3_window")
REVIEW_CORRECTIONS = [
    dict(id="CF3-1", severity="major",
         change="Apparent-magnitude-defined exclusion sets (2MRS_galaxy, 2MRS_coras_input, complement, union) now carry "
                "apparent_magnitude_defined=true, comparable_to_controls=false on their test_only, drop and constant-"
                "recentred drop blocks (constant recentring is flagged comparable only for offset-marginalised "
                "contrasts), and a mark_zero_point_confound record (kept-set inverse-variance mean delta_d vs the same "
                "control masks, overall and per 2000 km/s bin, plus mean epsilon_d). Added drop_recentered_czbin "
                "(mark zero point removed per 2000 km/s cz bin from selected training rows) against cz x inclusion "
                "controls and against cz x inclusion x epsilon_d-quintile controls as the comparable statistic. The "
                "2MRS member/non-member zero-point split now reports chi2 heterogeneity, an error inflated by "
                "sqrt(chi2/dof), and an exact velocity equivalent labelled selection-induced, not a flow. f=0 "
                "fractions are not cited as overlap/leakage evidence."),
    dict(id="CF3-2", severity="major (reviewer-downgraded to minor)",
         change="Every CORAS scorer carries coras_conditioning: scores conditional on the CF3-calibrated fsigma8=0.405 "
                "and bulk (95,-172,28) km/s, not held out w.r.t. the CF3 calibration; bulk decomposition (offset_only, "
                "bulk_only, bulk_removed, as_run) and a parameter-sensitivity bound (bulk +/- eTot and +/- eDist per "
                "axis, fsigma8 +/- eTot and +/- eDist, in-sample 6dF-preferred bulk, B_other=(B_CF3-w B_6dF)/(1-w) for "
                "the computed velocity and mu 6dF shares) computed in this run. The CF3_calibration_window fold carries "
                "a scope note: it scores only the cz-edge rows outside the window and has no power for full-sample "
                "parameter leakage (leakage-size score change on those rows vs control sd computed here)."),
    dict(id="CF3-3", severity="minor",
         change="Added cf3_member_definition (CORAS-distributed CF3 copy, not VizieR table3; galaxy/nest count "
                "differences read from the CF3 ReadMe), a tight position-only route (<=2 arcsec, no cz gate) with "
                "counts and the list of cz-discrepant counterparts missed by the 500 km/s gate, the e_mu=0.50 "
                "6dF-attribution fingerprint count, and the statement that CF3_member covers ~all rows by construction."),
    dict(id="CF3-4", severity="minor",
         change="Exclusions with zero selected kept rows (test_only per key, drop overall) are marked degenerate with null "
                "fractions. Every control fraction now carries k, (k+1)/(R+1) for both tails and the resolution "
                "1/(R+1)."),
]


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def tail_record(ctl, obs):
    """Finite-replicate tail record of control values against an observed value.

    k_le = #(control <= observed), k_ge = #(control >= observed); fractions k/R, the add-one
    estimates (k+1)/(R+1) and the resolution 1/(R+1).  Null fractions when R == 0 or obs is undefined."""
    ctl = np.asarray(ctl, float)
    R = int(len(ctl))
    rec = dict(replicates=R, resolution_1_over_R_plus_1=1. / (R + 1))
    if R == 0 or obs is None or not np.isfinite(obs):
        return dict(rec, k_control_le_observed=None, fraction_control_le_observed=None, p_le_plus_one=None,
                    k_control_ge_observed=None, fraction_control_ge_observed=None, p_ge_plus_one=None)
    kle, kge = int(np.sum(ctl <= obs)), int(np.sum(ctl >= obs))
    return dict(rec, k_control_le_observed=kle, fraction_control_le_observed=kle / R, p_le_plus_one=(kle + 1) / (R + 1),
                k_control_ge_observed=kge, fraction_control_ge_observed=kge / R, p_ge_plus_one=(kge + 1) / (R + 1))


def czbin_zero_points(cz, y, sig, rows, width=CZ_RECENTER_BIN, min_rows=RECENTER_MIN_ROWS):
    """Per-row mark zero point: inverse-variance mean of y over `rows` (selected training rows) inside each cz bin
    of `width`; every row of a bin with fewer than `min_rows` such rows gets the inverse-variance mean over all
    `rows`.  Returns (c, n_fallback_bins)."""
    rows = np.asarray(rows, np.int64)
    cz = np.asarray(cz, float)
    w = 1. / sig[rows] ** 2
    c = np.full(len(cz), float(np.sum(w * y[rows]) / w.sum()))
    bins = np.floor(cz / width).astype(np.int64)
    fallback = 0
    for k in np.unique(bins):
        r = rows[bins[rows] == k]
        if len(r) >= min_rows:
            ww = 1. / sig[r] ** 2
            c[bins == k] = np.sum(ww * y[r]) / ww.sum()
        else:
            fallback += 1
    return c, fallback


def eps_quintile_strata(strata, cz, eps, width=CZ_RECENTER_BIN):
    """Refine strata by the epsilon_d quintile inside each cz bin of `width` (bins with <= 10 rows: one quintile)."""
    cz, eps = np.asarray(cz, float), np.asarray(eps, float)
    q = np.zeros(len(cz), np.int64)
    bins = np.floor(cz / width).astype(np.int64)
    for k in np.unique(bins):
        sb = bins == k
        if sb.sum() > 10:
            q[sb] = np.searchsorted(np.quantile(eps[sb], [.2, .4, .6, .8]), eps[sb])
    return np.asarray(strata, np.int64) * 5 + q


def heterogeneity(diff, err):
    """Inverse-variance combination with chi2 heterogeneity and an error inflated by sqrt(max(1, chi2/dof))."""
    diff, err = np.asarray(diff, float), np.asarray(err, float)
    w = 1. / err ** 2
    m, e = float(np.sum(w * diff) / w.sum()), float(w.sum() ** -.5)
    chi2 = float(np.sum(((diff - m) / err) ** 2))
    dof = len(diff) - 1
    return dict(combined=m, combined_err=e, chi2_about_combined=chi2, dof=dof,
                chi2_per_dof=chi2 / dof if dof > 0 else None,
                p_value_homogeneous=float(chi2_dist.sf(chi2, dof)) if dof > 0 else None,
                combined_err_inflated=e * float(np.sqrt(max(1., chi2 / dof))) if dof > 0 else e)


def summary_stats(v):
    v = np.asarray(v, float)
    return dict(mean=float(v.mean()) if len(v) else None, sd=float(v.std(ddof=1)) if len(v) > 1 else None,
                min=float(v.min()) if len(v) else None, max=float(v.max()) if len(v) else None)


def zero_point_record(obs_num, obs_den, ctl_num, ctl_den, obs_eps, ctl_eps, bin_labels, obs_bnum, obs_bden,
                      ctl_bnum, ctl_bden, obs_bn):
    """Kept-set mark zero point (inverse-variance mean delta_d of selected kept rows) vs control keep-sets."""
    obs = obs_num / obs_den if obs_den > 0 else None
    with np.errstate(invalid="ignore", divide="ignore"):
        ctl = ctl_num / ctl_den
        cb = ctl_bnum / ctl_bden
    st = summary_stats(ctl)
    rec = dict(statistic="inverse-variance mean delta_d [dex] of selected kept rows (epsilon_d weights)",
               observed=obs, control=dict(st, **tail_record(ctl, obs)),
               z_observed_minus_control_mean_over_sd=(obs - st["mean"]) / st["sd"] if obs is not None and st["sd"] else None,
               mean_epsilon_d_selected_kept=dict(observed=obs_eps, control=summary_stats(ctl_eps)),
               per_cz_bin_2000kms={})
    for i, lab in enumerate(bin_labels):
        if obs_bn[i] == 0 and not np.any(ctl_bden[i] > 0):
            continue
        good = np.isfinite(cb[i])
        rec["per_cz_bin_2000kms"][lab] = dict(
            n_selected_kept_observed=int(obs_bn[i]),
            observed=float(obs_bnum[i] / obs_bden[i]) if obs_bden[i] > 0 else None,
            control_mean=float(cb[i][good].mean()) if good.any() else None,
            control_sd=float(cb[i][good].std(ddof=1)) if good.sum() > 1 else None)
    return rec


def robust(d):
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    if not len(d):
        return dict(n=0)
    med = float(np.median(d))
    return dict(n=int(len(d)), median=med, robust_sd_1p4826mad=float(1.4826 * np.median(abs(d - med))),
                mean=float(d.mean()), rms_about_mean=float(d.std()),
                percentiles_1_16_50_84_99=np.percentile(d, [1, 16, 50, 84, 99]).tolist(),
                fraction_within_0p05_of_median=float(np.mean(abs(d - med) < .05)))


# ----------------------------------------------------------------------------- CORAS constants

def coras_constants():
    """Read the CORAS constants that define the 2MRS input cut and the CF3 calibration window."""
    cfg = (DONOR / "configuration.hpp").read_text()
    tr = (DONOR / "src/transformations.cpp").read_text()
    cosmo = (DONOR / "src/cosmology.cpp").read_text()

    def num(name):
        m = re.search(rf"\b{name}\s*=\s*([-0-9.eE+]+)\s*;", cfg)
        if not m:
            raise ValueError(f"missing CORAS constant {name}")
        return float(m.group(1))

    def vec(name):
        return [float(t) for t in re.search(rf"{name}\s*=\s*\{{([^}}]*)\}}", cfg).group(1).split(",")]

    def frame(name):
        m = re.search(rf"{name} = \{{([-0-9.]+),[^\n]*\n\s*\(90\.0 - \(?(-?[0-9.]+)\)?\) \* RadiansPerDegree,"
                      rf"\s*\n\s*([-0-9.]+) \* RadiansPerDegree\}};", tr)
        if not m:
            raise ValueError(f"missing CORAS frame {name}")
        return tuple(float(t) for t in m.groups())   # amplitude km/s, galactic latitude, longitude

    for token in ("return -2.1 * z;", "return 0.8 * z;"):
        if token not in cosmo:
            raise ValueError("CORAS 2MRS k-/evolution correction changed")
    files = {k: cfg.split(f"{k} = \"")[1].split("\"")[0] for k in
             ("REDSHIFT_CATALOG_FILE_NAME", "DISTANCE_CATALOG_GROUPS_FILE_NAME", "DISTANCE_CATALOG_GALAXIES_FILE_NAME")}
    smoothing, czmin = vec("PARAMETER_ESTIMATE_SMOOTHING_SCALES"), vec("PARAMETER_ESTIMATE_MIN_REDSHIFT_VELOCITIES")
    note = re.search(r"ESTIMATED_NORMALIZED_GROWTH_RATE\s*=\s*0\.405;\s*//\s*([^\n]*)", cfg).group(1).strip()
    out = dict(files=files, max_apparent_magnitude=num("REDSHIFT_CATALOG_MAX_APPARENT_MAGNITUDE"),
               volume_limit_radius_Mpch=num("REDSHIFT_CATALOG_VOLUME_LIMIT_RADIUS"),
               reconstruction_max_radius_Mpch=num("RECONSTRUCTION_MAX_RADIUS"),
               fiducial_omega_matter=num("FIDUCIAL_OMEGA_MATTER"),
               distance_catalog_max_cz_kms=num("DISTANCE_CATALOG_MAX_REDSHIFT_VELOCITY"),
               outlier_max_sigma=num("DISTANCE_CATALOG_OUTLIER_MAX_SIGMA"),
               estimate_smoothing_scales_Mpch=smoothing, estimate_min_cz_kms=czmin,
               estimated=dict(fsigma8=num("ESTIMATED_NORMALIZED_GROWTH_RATE"),
                              bulk_galactic_kms=[num(f"ESTIMATED_EXTERNAL_BULK_{a}_VELOCITY") for a in "XYZ"],
                              distance_catalog_h=num("ESTIMATED_DISTANCE_CATALOG_HUBBLE"), source_comment=note),
               frames=dict(CMB=frame("HELIOCENTRIC_TO_CMB"), LG=frame("HELIOCENTRIC_TO_LOCAL_GROUP")))
    if "smoothing scale of 15 Mpc/h and a minimal redshift cutoff of 2000 km/s" not in note:
        raise ValueError("CORAS calibration provenance comment changed")
    out["calibration_cz_window_kms"] = [2000., out["distance_catalog_max_cz_kms"]]
    if 2000. not in czmin or 15. not in smoothing:
        raise ValueError("CORAS calibration cut not in the estimation grid")
    cal = np.loadtxt(DONOR / "data/calibrated_parameters_CR1-50.dat", comments="#")
    row = cal[(cal[:, 0] == 15.) & (cal[:, 1] == 2000.)]
    if len(row) != 1:
        raise ValueError("calibrated row rs=15, czMin=2000 missing")
    r = row[0]
    hdr = [line for line in (DONOR / "data/calibrated_parameters_CR1-50.dat").read_text().splitlines()
           if line.startswith("#")][0].lstrip("# ").split("\t")
    expect = {2: "fSig8", 4: "fSig8_eDist", 6: "fSig8_eTot", 12: "BExtX[km/s]", 14: "BExtX_eDist[km/s]",
              16: "BExtX_eTot[km/s]", 17: "BExtY[km/s]", 19: "BExtY_eDist[km/s]", 21: "BExtY_eTot[km/s]",
              22: "BExtZ[km/s]", 24: "BExtZ_eDist[km/s]", 26: "BExtZ_eTot[km/s]", 27: "h", 31: "h_eTot"}
    if any(hdr[i] != v for i, v in expect.items()):
        raise ValueError("calibrated_parameters_CR1-50.dat column layout changed")
    out["calibrated_row_rs15_czmin2000"] = dict(fsigma8=r[2], fsigma8_err_total=r[6], fsigma8_err_dist=r[4],
                                               bulk_galactic_kms=[r[12], r[17], r[22]],
                                               bulk_err_total_kms=[r[16], r[21], r[26]],
                                               bulk_err_dist_kms=[r[14], r[19], r[24]], h=r[27], h_err_total=r[31])
    return out


def unit_gal(lat, lon):
    b, l = np.deg2rad(np.asarray(lat, float)), np.deg2rad(np.asarray(lon, float))
    return np.column_stack((np.cos(b) * np.cos(l), np.cos(b) * np.sin(l), np.sin(b)))


def frame_shift(lat, lon, frame):
    """CORAS change_reference_frame from heliocentric: v + A cos(angle to apex)."""
    amp, alat, alon = frame
    return amp * (unit_gal(lat, lon) @ unit_gal([alat], [alon])[0])


def coras_comoving(v, om):
    z = v / C
    return C / 100. * (z - .75 * om * z * z + (-.5 + 9. / 8. * om) * om * z ** 3)


def coras_luminosity(v, om):
    z = v / C
    return C / 100. * (z + (1. - .75 * om) * z * z + (-1.25 + 9. / 8. * om) * om * z ** 3)


def coras_v_from_comoving(d, om):
    x = d / (C / 100.)
    return C * (x + .75 * om * x * x + .5 * om * x ** 3)


def coras_absmag(vcos, vobs, m, om):
    with np.errstate(invalid="ignore", divide="ignore"):
        return m - (25. + 5. * np.log10(coras_luminosity(vcos, om))) - (-2.1 * vobs / C) + .8 * vcos / C


# ----------------------------------------------------------------------------- catalogues

def load_cf3():
    mem = np.loadtxt(DONOR / "data/CF3_group_member_catalog.dat", comments="#", delimiter="\t")
    grp = np.loadtxt(DONOR / "data/CF3_group_catalog.dat", comments="#", delimiter="\t")
    if mem.shape != (17647, 13) or grp.shape != (11500, 7):
        raise ValueError(f"CF3 catalogue shapes changed: {mem.shape} {grp.shape}")
    pgc = mem[:, 0].astype(np.int64)
    if len(np.unique(pgc)) != len(pgc):
        raise ValueError("CF3 PGC not unique")
    # Non-zero nests map by identifier.  Singletons (id 0) keep their relative order in both files;
    # the mapping is then verified by position, cz and modulus.
    gid = mem[:, 6].astype(np.int64)
    ggid = grp[:, 0].astype(np.int64)
    nz = ggid[ggid != 0]
    if len(np.unique(nz)) != len(nz):
        raise ValueError("CF3 nest identifiers not unique")
    by_id = {int(g): i for i, g in enumerate(ggid) if g != 0}
    row = np.empty(len(mem), np.int64)
    row[gid != 0] = [by_id[int(g)] for g in gid[gid != 0]]
    zm, zg = np.flatnonzero(gid == 0), np.flatnonzero(ggid == 0)
    if len(zm) != len(zg):
        raise ValueError("CF3 singleton counts differ")
    # id-0 members: the id-0 group row equal to the member's own group columns (2-decimal position, cz)
    m = sky_match(unit_gal(mem[zm, 8], mem[zm, 9]), mem[zm, 10], unit_gal(grp[zg, 2], grp[zg, 3]), grp[zg, 4],
                  arcsec=40., dv=5.)
    if np.any(m["best"] < 0):
        raise ValueError("CF3 id-0 member without a group row")
    row[zm] = zg[m["best"]]
    singleton_check = dict(n_id0_members=int(len(zm)), n_id0_rows=int(len(zg)),
                           n_id0_rows_used=int(len(np.unique(m["best"]))),
                           n_id0_members_own_position_ne_group_position_gt_0p01deg=int(np.sum(
                               np.rad2deg(np.arccos(np.clip(np.sum(unit_gal(mem[zm, 1], mem[zm, 2]) *
                                                                   unit_gal(mem[zm, 8], mem[zm, 9]), 1), -1, 1))) > .01)))
    if not np.array_equal(ggid[row], gid):
        raise ValueError("CF3 member-to-group mapping failed")
    sep = np.rad2deg(np.arccos(np.clip(np.sum(unit_gal(grp[row, 2], grp[row, 3]) * unit_gal(mem[:, 8], mem[:, 9]), 1), -1, 1)))
    dcz = np.abs(grp[row, 4] - mem[:, 10])
    dmu = np.maximum(abs(grp[row, 5] - mem[:, 11]), abs(grp[row, 6] - mem[:, 12]))
    # The group table carries the nest position/velocity CORAS reads; the member file's group columns can
    # differ in position and cz (different nest averaging) but must carry the same group modulus and error.
    if np.sum(dmu > .011) > 5:
        raise ValueError(f"CF3 group modulus mismatch for {int(np.sum(dmu > .011))} members")
    return dict(pgc=pgc, lat=mem[:, 1], lon=mem[:, 2], cz_helio=mem[:, 3], mu=mem[:, 4], emu=mem[:, 5], group=gid,
                group_size=mem[:, 7].astype(np.int64), group_row=row, glat=grp[:, 2], glon=grp[:, 3],
                gcz_helio=grp[:, 4], gmu=grp[:, 5], gemu=grp[:, 6], gid=grp[:, 0].astype(np.int64),
                mapping_check=dict(
                    n_members_group_modulus_or_error_differs_gt_0p011=int(np.sum(dmu > .011)),
                    n_members_group_position_differs_gt_0p01deg=int(np.sum(sep > .01)),
                    n_members_group_cz_differs_gt_5kms=int(np.sum(dcz > 5.)),
                    member_vs_group_table_cz_abs_diff_kms_p50_p99_max=np.percentile(dcz, [50, 99, 100]).tolist(),
                    authority="CF3_group_catalog.dat columns (as read by CORAS estimate_parameters)",
                    **singleton_check))


def load_2mrs():
    dt = [("id", "U16"), ("lat", "f8"), ("lon", "f8"), ("cz", "f8"), ("ks", "f8"), ("group", "i8"),
          ("size", "i8"), ("glat", "f8"), ("glon", "f8"), ("gcz", "f8")]
    t = np.loadtxt(DONOR / "data/2MRS_group_member_catalog.dat", comments="#", delimiter="\t", dtype=dt)
    if len(t) != 44572 or any(len(x) != 16 for x in t["id"]):
        raise ValueError("2MRS catalogue changed")
    return t


def coras_2mrs_input(t, const, frame):
    """apply_partial_volume_limit of CORAS (FoG-collapsed group cz for distance, galaxy cz for k-correction)."""
    om, mmax = const["fiducial_omega_matter"], const["max_apparent_magnitude"]
    v = t["gcz"] + frame_shift(t["lat"], t["lon"], const["frames"][frame])
    r = coras_comoving(v, om)
    vlim = coras_v_from_comoving(const["volume_limit_radius_Mpch"], om)
    mlim = coras_absmag(np.array([vlim]), np.array([vlim]), np.array([mmax]), om)[0]
    M = coras_absmag(v, t["cz"], t["ks"], om)
    with np.errstate(invalid="ignore"):
        keep = (r > 0) & (r <= const["reconstruction_max_radius_Mpch"]) & (t["ks"] <= mmax) & (M <= mlim)
    return keep, dict(frame=frame, n_input=int(len(t)), n_kept=int(keep.sum()), absolute_magnitude_threshold=float(mlim),
                      n_fail_radius=int(np.sum(~((r > 0) & (r <= const["reconstruction_max_radius_Mpch"])))),
                      n_fail_apparent=int(np.sum(t["ks"] > mmax)),
                      n_fail_absolute_only=int(np.sum((r > 0) & (r <= const["reconstruction_max_radius_Mpch"]) &
                                                      (t["ks"] <= mmax) & ~(M <= mlim))))


def sky_match(nq, czq, nr, czr, arcsec=ARCSEC, dv=DV):
    """R103 metric: candidates within arcsec and |dcz|<=dv, closest by (sep/arcsec)^2+(dcz/dv)^2."""
    tree = cKDTree(nr)
    hits = tree.query_ball_point(nq, 2 * np.sin(np.deg2rad(arcsec / 3600.) / 2))
    count = np.zeros(len(nq), np.int64)
    best = np.full(len(nq), -1, np.int64)
    sep = np.full(len(nq), np.nan)
    dvel = np.full(len(nq), np.nan)
    for i, cand in enumerate(hits):
        if not cand:
            continue
        cand = np.asarray(cand)
        cand = cand[np.abs(czr[cand] - czq[i]) <= dv]
        count[i] = len(cand)
        if len(cand):
            a = np.rad2deg(2 * np.arcsin(np.clip(.5 * np.linalg.norm(nr[cand] - nq[i], axis=1), 0, 1))) * 3600.
            d = czr[cand] - czq[i]
            k = int(np.argmin((a / arcsec) ** 2 + (d / dv) ** 2))
            best[i], sep[i], dvel[i] = cand[k], a[k], d[k]
    return dict(count=count, best=best, sep_arcsec=sep, dv_kms=dvel)


def match_summary(m):
    ok = m["best"] >= 0
    return dict(multiplicity_histogram={int(k): int(v) for k, v in zip(*np.unique(m["count"], return_counts=True))},
                n_matched=int(ok.sum()), n_distinct_reference=int(len(np.unique(m["best"][ok]))),
                separation_arcsec_p50_p95_p99=np.percentile(m["sep_arcsec"][ok], [50, 95, 99]).tolist() if ok.any() else None,
                dcz_kms_p5_p50_p95=np.percentile(m["dv_kms"][ok], [5, 50, 95]).tolist() if ok.any() else None)


def cf3_readme_counts(text):
    """Counts stated by the VizieR J/AJ/152/50 (CF3) ReadMe: table2 nests, table3 galaxies, 6dFGS FP distances,
    and the single e_DM-P value."""
    t2 = re.search(r"^table2\.dat\s+\d+\s+(\d+)\s", text, re.M)
    t3 = re.search(r"^table3\.dat\s+\d+\s+(\d+)\s", text, re.M)
    fp = re.search(r"and\s+(\d+)\s+distances\s+based\s+on\s+the\s+Fundamental\s+Plane", text)
    edmp = re.search(r"e_DM-P\s+\[([0-9.]+)\]", text)
    if not (t2 and t3 and fp and edmp):
        raise ValueError("CF3 ReadMe layout changed")
    return dict(table2_nests=int(t2.group(1)), table3_galaxies=int(t3.group(1)),
                sixdfgs_fp_distances=int(fp.group(1)), e_DM_P_stated_mag=float(edmp.group(1)))


def cf3_member_record(names, route, via_pos, via_pgc, cf3_row, mt, n6, n3, cz6, cz3_cmb, cf3, inc):
    """Operational CF3-member definition, the tight position-only route and the cz-discrepant counterparts."""
    any_route = cf3_row >= 0
    tight = mt["best"] >= 0
    missed = np.flatnonzero(tight & (via_pos < 0))
    listing = [dict(sixdf_id=str(names[i]), route=str(route[i]), operational_cf3_member=bool(any_route[i]),
                    r105_selected=bool(inc[i]), cf3_pgc=int(cf3["pgc"][mt["best"][i]]),
                    pgc_route_points_to_same_cf3_row=bool(via_pgc[i] == mt["best"][i]),
                    sep_arcsec=float(mt["sep_arcsec"][i]), cf3_minus_6df_cz_cmb_kms=float(mt["dv_kms"][i]))
               for i in missed]
    lost = np.flatnonzero(~any_route & ~tight)
    chord, near = cKDTree(n3).query(n6[lost]) if len(lost) else (np.zeros(0), np.zeros(0, np.int64))
    nearest = [dict(sixdf_id=str(names[i]), r105_selected=bool(inc[i]), nearest_cf3_pgc=int(cf3["pgc"][j]),
                    nearest_sep_arcsec=float(np.rad2deg(2 * np.arcsin(min(1., c / 2))) * 3600.),
                    cf3_minus_6df_cz_cmb_kms=float(cz3_cmb[j] - cz6[i]))
               for i, c, j in zip(lost, chord, near)]
    sep_t = mt["sep_arcsec"][tight]
    emu = np.round(cf3["emu"], 2)
    fpv = CF3_FP_ERROR_FINGERPRINT
    readme = cf3_readme_counts(CF3_README.read_text())
    n_union = int(np.sum(any_route | tight))
    return dict(
        operational_definition=(
            "A 6dFGSv row is a 'CF3 member' when it matches a galaxy of the CF3 group-member file distributed with the "
            f"CORAS donor (data/CF3_group_member_catalog.dat) either by the sky route ({ARCSEC:g} arcsec and |cz_CMB "
            f"difference| <= {DV:g} km/s, R103 metric) or by the CF4 table2 PGC route. This is not VizieR J/AJ/152/50 "
            "table3, which is not read here (cf3_source.missing_for_cf3_internal_method_attribution)."),
        coras_copy=dict(galaxies=int(len(cf3["pgc"])), group_rows_including_singletons=int(len(cf3["gid"]))),
        vizier_readme_counts=readme,
        coras_copy_minus_readme=dict(galaxies=int(len(cf3["pgc"])) - readme["table3_galaxies"],
                                     nests=int(len(cf3["gid"])) - readme["table2_nests"],
                                     note="the CORAS copy is not table3/table2 row for row; the difference is not "
                                          "resolved without table3"),
        n_any_route=int(any_route.sum()), n_selected_any_route=int(np.sum(any_route & inc)),
        tight_position_route=dict(
            arcsec=TIGHT_ARCSEC, cz_gate=None, n_matched=int(tight.sum()), n_selected_matched=int(np.sum(tight & inc)),
            multiplicity_histogram={int(k): int(v) for k, v in zip(*np.unique(mt["count"], return_counts=True))},
            separation_arcsec_p50_p99_max=np.percentile(sep_t, [50, 99, 100]).tolist() if len(sep_t) else None,
            n_with_abs_dcz_gt_500kms=int(np.sum(tight & (np.abs(np.nan_to_num(mt["dv_kms"])) > DV))),
            n_tight_and_any_route=int(np.sum(tight & any_route)),
            n_tight_not_any_route=int(np.sum(tight & ~any_route)),
            n_any_route_not_tight=int(np.sum(any_route & ~tight)),
            n_tight_route_points_to_other_cf3_row_than_any_route=int(np.sum(tight & any_route & (mt["best"] != cf3_row)))),
        n_any_route_or_tight=n_union, n_parent=int(len(names)),
        counterparts_missed_by_sky_route_cz_gate=listing,
        rows_without_any_counterpart=nearest,
        emu_fingerprint=dict(value_mag=fpv, readme_e_DM_P_mag=readme["e_DM_P_stated_mag"],
                             n_any_route_with_emu=int(np.sum(any_route & (emu[np.maximum(cf3_row, 0)] == fpv))),
                             n_tight_with_emu=int(np.sum(tight & (emu[np.maximum(mt["best"], 0)] == fpv))),
                             n_cf3_copy_with_emu=int(np.sum(emu == fpv)),
                             note="CF3 6dFGS FP distances carry e_DM-P = 0.5 mag (ReadMe); used as a 6dF-attribution "
                                  "proxy only (the CF3 mu error is the combined error of the adopted distance)"),
        by_construction=(
            f"The CF3 ReadMe states CF3 includes {readme['sixdfgs_fp_distances']} 6dFGS Fundamental-Plane distances; "
            f"{n_union} of {len(names)} 6dFGSv rows have a CF3 counterpart by an operational route or the tight "
            "position route. The CF3_member exclusion is therefore ~all rows by construction and its folds are "
            "degenerate, not an overlap measurement."))


def designation_radec(names, kind):
    """Decode designations: 6dF gHHMMSSs+DDMMSS (rounded) and 2MASS HHMMSSss+DDMMSSs (truncated)."""
    out = np.empty((len(names), 2))
    for i, x in enumerate(names):
        if kind == "6df":
            ra = (int(x[1:3]) + int(x[3:5]) / 60. + float(x[5:7] + "." + x[7]) / 3600.) * 15.
            sg, d, mi, se = x[8], int(x[9:11]), int(x[11:13]), float(x[13:15])
        else:
            ra = (int(x[0:2]) + int(x[2:4]) / 60. + float(x[4:6] + "." + x[6:8]) / 3600.) * 15.
            sg, d, mi, se = x[8], int(x[9:11]), int(x[11:13]), float(x[13:15] + "." + x[15])
        out[i] = ra, (-1 if sg == "-" else 1) * (d + mi / 60. + se / 3600.)
    return out


def icrs_unit(ra, dec):
    r, d = np.deg2rad(ra), np.deg2rad(dec)
    return np.column_stack((np.cos(r) * np.cos(d), np.sin(r) * np.cos(d), np.sin(d)))


# ----------------------------------------------------------------------------- lineage

def comoving_mpc(z, om=.3, h0=75.):
    x, w = np.polynomial.legendre.leggauss(64)
    zz = np.asarray(z)[:, None] * (x + 1) / 2
    return C / h0 * np.asarray(z) / 2 * np.sum(w / np.sqrt(om * (1 + zz) ** 3 + 1 - om), axis=1)


def mu_from_delta(cz, delta):
    """Springob+14 delta_d = log10(D_z/D_H), D_z comoving at CMB cz (Om=0.3); mu with D_L=(1+z)D_H, H0=75."""
    z = np.asarray(cz, float) / C
    return 5. * np.log10((1 + z) * comoving_mpc(z) / 10 ** np.asarray(delta)) + 25.


# ----------------------------------------------------------------------------- scoring

def choice_scores(train, Jsum, Dsum, choices):
    """Equal prior inside each declared subset; log predictive density of test marks/indicators minus zero."""
    out = {}
    for name, mask in choices.items():
        lt = train[mask]
        w = lt - logsumexp(lt)
        out[name] = logsumexp(w[:, None] + Jsum[mask], axis=0) - logsumexp(w[:, None] + Dsum[mask], axis=0)
    return {k: v - out["zero"] for k, v in out.items()}


def stratified_masks(strata, n_keep, R, rng):
    """(n, R) float 0/1 matrix: each column keeps n_keep[s] random rows of each stratum s (without replacement)."""
    M = np.zeros((len(strata), R))
    for s in np.unique(strata):
        idx = np.flatnonzero(strata == s)
        k = int(n_keep.get(int(s), 0))
        if k == 0:
            continue
        if k == len(idx):
            M[idx] = 1.
            continue
        pick = np.argsort(rng.random((len(idx), R)), axis=0)[:k]
        M[idx[pick], np.arange(R)[None, :]] = 1.
    return M


class Scorer:
    """One score family (R105 field holdout or CORAS marks) over the R105 PGC/PGC1 folds."""

    def __init__(self, name, mus, choices, base, reference_folds, tol, contrasts=None):
        self.name, self.mus, self.choices, self.b = name, mus, choices, base
        self.reference_folds, self.tol = reference_folds, tol
        self.contrasts = contrasts or {}
        self.keys = list(choices) + list(self.contrasts)

    def scores(self, train, Jsum, Dsum):
        sc = choice_scores(train, Jsum, Dsum, self.choices)
        for name, (a, b) in self.contrasts.items():
            sc[name] = sc[a] - sc[b]
        return sc

    def fit(self, tr, recenter=False):
        """Selection probit on training rows.  recenter: False (R105 model), True/'constant' (one mark zero point
        c = inverse-variance mean delta_d of selected training rows removed from marks and the probit covariate),
        'czbin' (the same, per 2000 km/s cz bin; sparse bins use the constant).  Returns (y, a, beta2, n_fallback)."""
        b = self.b
        y, x = b["y"], b["x"]
        c, fallback = np.zeros(len(y)), 0
        if recenter:
            sel = tr[b["inc"][tr]]
            if recenter == "czbin":
                c, fallback = czbin_zero_points(b["cz"], y, b["sig"], sel)
            else:
                wt = 1. / b["sig"][sel] ** 2
                c = np.full(len(y), float(np.sum(wt * y[sel]) / wt.sum()))
            y = y - c
            x = x.copy()
            x[:, 2] -= c
        fit = b["old"].fit_probit_with_hessian(x[tr], b["inc"][tr])
        if not fit.converged:
            return None
        beta = fit.beta_hat
        return y, beta[0] + beta[1] * x[:, 1] + beta[3] * x[:, 3], beta[2], fallback

    def matrices(self, tr, te, recenter=False):
        """Per-component log factors: summed training joint, held-out joint and held-out pattern."""
        f = self.fit(tr, recenter)
        if f is None:
            return None
        y, a, b2, fallback = f
        j, d = self.b["mark"].components(y, self.mus, self.b["sig"], a, b2, self.b["inc"])
        return j[:, tr].sum(1), j[:, te], d[:, te], fallback

    def replay(self):
        """Full R105 held-out sets: must reproduce the stored relative scores."""
        self.cache, self.probit, worst, rows = {}, {}, 0., {}
        for key, folds in self.b["folds"].items():
            for f, (tr, te) in enumerate(folds):
                y, a, b2, _ = self.fit(tr)
                self.probit[key, f] = (a, b2)
                j, d = self.b["mark"].components(y, self.mus, self.b["sig"], a, b2, self.b["inc"])
                train, Jte, Dte = j[:, tr].sum(1), j[:, te], d[:, te]
                self.cache[key, f] = (train, Jte, Dte)
                sc = self.scores(train, Jte.sum(1)[:, None], Dte.sum(1)[:, None])
                ref = self.reference_folds[key][f]
                for k, v in ref.items():
                    worst = max(worst, abs(float(sc[k][0]) - v))
                rows.setdefault(key, []).append({k: float(v[0]) for k, v in sc.items()})
        if worst > self.tol:
            raise ValueError(f"{self.name}: R105 replay error {worst}")
        return dict(max_abs_fold_replay_error=worst,
                    sum_full={key: {k: float(sum(r[k] for r in rs)) for k in self.keys} for key, rs in rows.items()},
                    folds_full=rows)

    def subset_score(self, mus_field, test_keep=None, keys=None):
        """Relative score (field subset minus zero) of an alternative 5-offset field with the replayed R105 probit
        fits; held-out columns optionally restricted to test_keep (training unchanged, as test_only)."""
        b = self.b
        mus = np.vstack([np.zeros(mus_field.shape[1]), mus_field])
        choices = dict(zero=np.r_[True, np.zeros(len(mus_field), bool)], field=np.r_[False, np.ones(len(mus_field), bool)])
        out = {}
        for key, folds in b["folds"].items():
            if keys is not None and key not in keys:
                continue
            tot = 0.
            for f, (tr, te) in enumerate(folds):
                a, b2 = self.probit[key, f]
                j, d = b["mark"].components(b["y"], mus, b["sig"], a, b2, b["inc"])
                cols = te if test_keep is None else te[test_keep[te]]
                tot += float(choice_scores(j[:, tr].sum(1), j[:, cols].sum(1)[:, None], d[:, cols].sum(1)[:, None],
                                           choices)["field"][0])
            out[key] = tot
        return out

    def test_only(self, excluded, R, seed, comparable=True):
        b = self.b
        zp = b["zp"]
        out = {}
        empty = not excluded.any()
        R = 1 if empty else R
        nb = len(zp["bin_labels"])
        for key, folds in b["folds"].items():
            obs_total = {k: 0. for k in self.keys}
            ctl_total = {k: np.zeros(R) for k in self.keys}
            acc = dict(num=np.zeros(R), den=np.zeros(R), eps=np.zeros(R), nsel=np.zeros(R),
                       bnum=np.zeros((nb, R)), bden=np.zeros((nb, R)))
            oacc = dict(num=0., den=0., eps=0., nsel=0., bnum=np.zeros(nb), bden=np.zeros(nb), bn=np.zeros(nb))
            fold_rows = []
            rng = np.random.default_rng([seed, 0 if key == "pgc" else 1])
            for f, (tr, te) in enumerate(folds):
                train, Jte, Dte = self.cache[key, f]
                keep = ~excluded[te]
                strata = b["strata"][te]
                n_keep = {int(s): int(np.sum(keep & (strata == s))) for s in np.unique(strata)}
                obs = self.scores(train, Jte[:, keep].sum(1)[:, None], Dte[:, keep].sum(1)[:, None])
                M = stratified_masks(strata, n_keep, R, rng)
                ctl = self.scores(train, Jte @ M, Dte @ M)
                full = self.scores(train, Jte.sum(1)[:, None], Dte.sum(1)[:, None])
                for k in self.keys:
                    obs_total[k] += float(obs[k][0])
                    ctl_total[k] += ctl[k]
                # mark zero point of kept selected held-out rows, observed and under the same control masks
                kt = te[keep]
                oacc["num"] += zp["wy"][kt].sum()
                oacc["den"] += zp["w"][kt].sum()
                oacc["eps"] += zp["eps_sel"][kt].sum()
                oacc["nsel"] += zp["sel"][kt].sum()
                oacc["bnum"] += zp["wy"][kt] @ zp["binm"][kt]
                oacc["bden"] += zp["w"][kt] @ zp["binm"][kt]
                oacc["bn"] += zp["sel"][kt] @ zp["binm"][kt]
                acc["num"] += zp["wy"][te] @ M
                acc["den"] += zp["w"][te] @ M
                acc["eps"] += zp["eps_sel"][te] @ M
                acc["nsel"] += zp["sel"][te] @ M
                acc["bnum"] += (zp["binm"][te] * zp["wy"][te, None]).T @ M
                acc["bden"] += (zp["binm"][te] * zp["w"][te, None]).T @ M
                fold_rows.append(dict(fold=f, n_test=int(len(te)), n_kept=int(keep.sum()),
                                      n_kept_selected=int(np.sum(keep & b["inc"][te])),
                                      kept_minus_zero={k: float(v[0]) for k, v in obs.items()},
                                      full_minus_zero={k: float(v[0]) for k, v in full.items()},
                                      control_mean={k: float(v.mean()) for k, v in ctl.items()}))
            n_kept_sel = int(sum(r["n_kept_selected"] for r in fold_rows))
            degenerate = empty or n_kept_sel == 0
            if degenerate:
                reason = ("no row excluded (the kept set is the full held-out set)" if empty else
                          "no selected held-out row kept: mark and indicator terms cancel against 'zero', so every "
                          "score and control is identically 0; fractions are undefined")
                control = dict(degenerate=True, reason=reason, replicates=R,
                               **{k: dict(fraction_control_le_observed=None, p_le_plus_one=None,
                                          fraction_control_ge_observed=None, p_ge_plus_one=None)
                                  for k in self.keys if k != "zero"})
                confound = None
            else:
                control = dict(degenerate=False, replicates=R, stratification="cz_gal 500 km/s bins x R105 inclusion",
                               **{k: dict(mean=float(v.mean()), sd=float(v.std(ddof=1)),
                                          q05_q50_q95=np.percentile(v, [5, 50, 95]).tolist(), **tail_record(v, obs_total[k]))
                                  for k, v in ctl_total.items() if k != "zero"})
                with np.errstate(invalid="ignore", divide="ignore"):
                    ctl_eps = acc["eps"] / acc["nsel"]
                confound = zero_point_record(oacc["num"], oacc["den"], acc["num"], acc["den"],
                                             oacc["eps"] / oacc["nsel"] if oacc["nsel"] else None, ctl_eps,
                                             zp["bin_labels"], oacc["bnum"], oacc["bden"], acc["bnum"], acc["bden"], oacc["bn"])
            out[key] = dict(folds=fold_rows, sum_kept_minus_zero=obs_total,
                            sum_full_minus_zero={k: sum(r["full_minus_zero"][k] for r in fold_rows) for k in self.keys},
                            n_kept=int(sum(r["n_kept"] for r in fold_rows)), n_kept_selected=n_kept_sel,
                            kept_minus_zero_per_kept_selected_row={k: v / max(1, n_kept_sel) for k, v in obs_total.items()},
                            degenerate=degenerate, comparable_to_controls=None if degenerate else bool(comparable),
                            control=control, mark_zero_point_confound=confound)
            if not comparable and not degenerate:
                out[key]["not_comparable_reason"] = (
                    "apparent-magnitude-defined exclusion: the kept held-out set has a mark zero point the cz x inclusion "
                    "controls do not reproduce (see mark_zero_point_confound); training is unchanged, so the score mixes "
                    "the train/test zero-point mismatch with any tracer information. Control fractions are not overlap "
                    "or leakage evidence.")
        return out

    def drop(self, excluded, R, seed, recenter=False, strata=None, strata_label=None, stream=2, comparable=True):
        b = self.b
        zp = b["zp"]
        strata = b["strata"] if strata is None else strata
        n_keep = {int(s): int(np.sum(excluded & (strata == s))) for s in np.unique(strata)}
        rng = np.random.default_rng([seed, stream])
        mode = "czbin" if recenter == "czbin" else ("constant" if recenter else "none")

        def run(mask):
            tot, nk, failed, fb = {}, 0, 0, 0
            for key, folds in b["folds"].items():
                for f, (tr, te) in enumerate(folds):
                    tr2, te2 = tr[~mask[tr]], te[~mask[te]]
                    if len(te2) == 0 or len(tr2) < 20:
                        failed += 1
                        continue
                    m = self.matrices(tr2, te2, recenter=recenter)
                    if m is None:
                        failed += 1
                        continue
                    train, Jte, Dte, fallback = m
                    fb += fallback
                    sc = self.scores(train, Jte.sum(1)[:, None], Dte.sum(1)[:, None])
                    for k in self.keys:
                        tot[(key, k)] = tot.get((key, k), 0.) + float(sc[k][0])
                    nk += len(te2)
            return tot, nk, failed, fb

        n_kept_sel = int(np.sum(~excluded & b["inc"]))
        degenerate = n_kept_sel == 0
        if degenerate:
            R = 0
        obs, nk, failed, fb_obs = run(excluded) if not degenerate else ({}, 0, 0, 0)
        ctl, cfail, cfb, cmasks = [], 0, 0, []
        for _ in range(R):
            Mx = stratified_masks(strata, n_keep, 1, rng)[:, 0].astype(bool)
            t, _, fl, fb = run(Mx)
            cfail += fl
            cfb += fb
            if fl == 0:
                ctl.append(t)
                cmasks.append(~Mx)
        res = {}
        for key in b["folds"]:
            o = {k: obs.get((key, k)) for k in self.keys}
            c = {k: np.array([t[(key, k)] for t in ctl]) for k in self.keys}
            res[key] = dict(sum_kept_minus_zero=o, control={
                k: dict(n=int(len(v)), mean=float(v.mean()) if len(v) else None,
                        sd=float(v.std(ddof=1)) if len(v) > 1 else None, **tail_record(v, o[k]))
                for k, v in c.items() if k != "zero"})
        keep_obs = ~excluded
        K = np.array(cmasks, float).T if cmasks else np.zeros((len(excluded), 0))
        confound = None if degenerate else zero_point_record(
            float(zp["wy"][keep_obs].sum()), float(zp["w"][keep_obs].sum()), zp["wy"] @ K, zp["w"] @ K,
            float(zp["eps_sel"][keep_obs].sum() / zp["sel"][keep_obs].sum()),
            (zp["eps_sel"] @ K) / np.maximum(zp["sel"] @ K, 1.), zp["bin_labels"],
            zp["wy"][keep_obs] @ zp["binm"][keep_obs], zp["w"][keep_obs] @ zp["binm"][keep_obs],
            (zp["binm"] * zp["wy"][:, None]).T @ K, (zp["binm"] * zp["w"][:, None]).T @ K,
            zp["sel"][keep_obs] @ zp["binm"][keep_obs])
        out = dict(per_key=res, n_kept_test_rows_over_both_keys=nk, n_kept_selected_rows=n_kept_sel,
                   degenerate=degenerate, folds_failed_observed=failed,
                   recentered_mark_zero_point=mode != "none", recentering=mode,
                   recentering_bin_kms=CZ_RECENTER_BIN if mode == "czbin" else None,
                   recentering_fallback_bins_observed=fb_obs if mode == "czbin" else None,
                   recentering_fallback_bins_controls=cfb if mode == "czbin" else None,
                   control_replicates_requested=R, control_replicates_used=len(ctl), control_fold_failures=cfail,
                   stratification=strata_label or "global random exclusion with the same cz_gal 500 km/s bin x inclusion counts",
                   comparable_to_controls=None if degenerate else bool(comparable),
                   mark_zero_point_confound=confound,
                   mark_zero_point_confound_note="raw delta_d of the kept selected rows before any recentring")
        if degenerate:
            out["degenerate_reason"] = "no selected row outside the exclusion set"
        return out


# ----------------------------------------------------------------------------- pooled blocks and review records

_POOL = {}
EPS_STRATA_LABEL = ("global random exclusion with the same cz_gal 500 km/s bin x inclusion x epsilon_d-quintile "
                    "(within 2000 km/s cz bin) counts")
RAW_ZERO_POINT_BLOCKS = ("test_only", "drop", "drop_recentered")
ALL_BLOCKS = ("test_only", "drop", "drop_recentered", "drop_recentered_czbin", "drop_recentered_czbin_eps_strata")


def _run_block(task):
    """One scoring block on the fork-inherited context; returns (result, seconds)."""
    si, ename, blk = task
    t = time.time()
    sc, args = _POOL["scorers"][si], _POOL["args"]
    if blk == "coras_sensitivity":
        return coras_sensitivity(sc, _POOL["coras_ctx"][sc.name], _POOL["const"], _POOL["shares"],
                                 _POOL["window_keep"]), time.time() - t
    X = _POOL["exclusions"][ename]
    mag = ename in MAGNITUDE_DEFINED
    R = args.drop_replicates if X.any() else 0
    if blk == "test_only":
        r = sc.test_only(X, args.replicates, args.seed, comparable=not mag)
    elif blk == "drop":
        r = sc.drop(X, R, args.seed, comparable=not mag)
    elif blk == "drop_recentered":
        r = sc.drop(X, R, args.seed, recenter=True, comparable=not mag)
    elif blk == "drop_recentered_czbin":
        r = sc.drop(X, R, args.seed, recenter="czbin")
    elif blk == "drop_recentered_czbin_eps_strata":
        r = sc.drop(X, R, args.seed, recenter="czbin", strata=_POOL["strata_eps"], strata_label=EPS_STRATA_LABEL, stream=3)
    else:
        raise ValueError(blk)
    return r, time.time() - t


def comparability_record(ename, mag, rec):
    """Which blocks of one exclusion set are comparable to their controls, with the raw mark-zero-point z-scores."""
    z = {}
    t = rec.get("test_only")
    if isinstance(t, dict):
        for key, r in t.items():
            c = r.get("mark_zero_point_confound")
            z[f"test_only:{key}"] = c["z_observed_minus_control_mean_over_sd"] if c else None
    for blk in RAW_ZERO_POINT_BLOCKS[1:]:
        r = rec.get(blk)
        if isinstance(r, dict) and r.get("mark_zero_point_confound") and r["control_replicates_used"] > 1:
            z[blk] = r["mark_zero_point_confound"]["z_observed_minus_control_mean_over_sd"]
    finite = [abs(v) for v in z.values() if v is not None]
    run = [b for b in ALL_BLOCKS if isinstance(rec.get(b), dict)]
    degenerate = [b for b in run if (rec[b].get("degenerate") if b != "test_only" else
                                     any(r["degenerate"] for r in rec[b].values()))]
    out = dict(apparent_magnitude_defined=mag, degenerate_blocks=degenerate,
               raw_mark_zero_point_z_by_block=z, max_abs_raw_mark_zero_point_z=max(finite) if finite else None,
               raw_zero_point_outside_control_spread_3sd=bool(finite and max(finite) > 3.),
               zero_point_note="z = (kept-set inverse-variance mean delta_d - control mean)/control sd on raw marks; "
                               "the czbin blocks remove this zero point per 2000 km/s bin inside each fit")
    if mag:
        out.update(
            non_comparable_blocks=[b for b in ("test_only", "drop") if b in run and b not in degenerate],
            comparable_with_scope={"drop_recentered": "offset-marginalised contrasts (*_minus_offset_only) only"}
            if "drop_recentered" in run else {},
            comparable_statistic=[b for b in ("drop_recentered_czbin", "drop_recentered_czbin_eps_strata") if b in run],
            citation_rule="Control fractions of non-comparable blocks (including fractions of 0) are not overlap or "
                          "leakage evidence and must not be cited as such.",
            residual=("Per-2000 km/s recentring removes the cz-dependent mark zero point; epsilon_d-quintile strata match "
                      "the noise level. Any remaining difference is unresolved: at fixed cz the Ks cut also selects galaxies "
                      "that are truly nearer (selection on true peculiar velocity), so magnitude selection and 2MRS-tracer "
                      "information cannot be separated in this design."))
    else:
        out.update(comparable_statistic=[b for b in run if b not in degenerate],
                   note="not defined by apparent magnitude; comparability rests on the stratified controls and the "
                        "raw zero-point z-scores above")
    return out


def coras_sensitivity(sc, ctx, const, shares, window_keep):
    """Bulk decomposition and parameter sensitivity of the CORAS mean-field score (5 offsets) on the R105 folds."""
    old, sci, z, growth, ng = ctx["old"], ctx["sci"], ctx["z"], ctx["growth"], ctx["ng"]

    def mus_for(v):
        return np.array([old.r99.finite_shift(sci, z, np.arctanh((o + growth * v) / old.r100.C), "bolometric")
                         / (5 * old.r100.MAG) for o in ctx["offsets"]])

    def S(v, keep=None, keys=None):
        return sc.subset_score(mus_for(v), keep, keys)

    B0 = np.array(const["estimated"]["bulk_galactic_kms"], float)
    fs8 = const["estimated"]["fsigma8"]
    cal = const["calibrated_row_rs15_czmin2000"]
    bulk = ng @ B0
    mean = ctx["mean"]
    U = mean - bulk                      # fsigma8 x 2MRS reconstruction (CORAS adds the bulk to the mean only)
    st = np.loadtxt(ctx["directory"] / "sites.tsv", dtype=[("i", "i8"), ("r", "f8"), ("th", "f8"), ("ph", "f8")])
    order = np.argsort(st["i"])
    if not np.array_equal(st["i"][order], ctx["ids"]):
        raise ValueError("sites.tsv identities differ")
    proj = np.sin(st["th"]) * (B0[0] * np.cos(st["ph"]) + B0[1] * np.sin(st["ph"])) + B0[2] * np.cos(st["th"])
    projerr = float(np.max(np.abs(proj[order] - bulk)))
    if projerr > 1e-6:
        raise ValueError(f"bulk projection mismatch {projerr}")
    keys = list(sc.b["folds"])
    decomp = dict(offset_only=sc.subset_score(ctx["offset_mus"]), bulk_only=S(bulk), bulk_removed=S(U), as_run=S(mean))
    window = dict(as_run=S(mean, window_keep), offset_only=sc.subset_score(ctx["offset_mus"], window_keep))
    shifts = {}
    for lab, errs in (("eTot", cal["bulk_err_total_kms"]), ("eDist", cal["bulk_err_dist_kms"])):
        for ax in range(3):
            for sgn in (-1., 1.):
                B = B0.copy()
                B[ax] += sgn * errs[ax]
                shifts[f"bulk_{'XYZ'[ax]}{'+' if sgn > 0 else '-'}{lab}"] = dict(bulk_galactic_kms=B.tolist(), score=S(U + ng @ B))
    for lab, e in (("eTot", cal["fsigma8_err_total"]), ("eDist", cal["fsigma8_err_dist"])):
        for sgn in (-1., 1.):
            f = fs8 + sgn * e
            shifts[f"fsigma8{'+' if sgn > 0 else '-'}{lab}"] = dict(fsigma8=f, score=S(U * (f / fs8) + bulk))
    pref = {}
    for key in keys:
        opt = minimize(lambda B: -S(U + ng @ B, keys=(key,))[key], B0, method="Nelder-Mead",
                       options=dict(xatol=1., fatol=1e-3, maxiter=400))
        pref[key] = dict(bulk_galactic_kms=opt.x.tolist(), score=float(-opt.fun), n_evaluations=int(opt.nfev),
                         converged=bool(opt.success))
    mix = {}
    for wlab, w in shares.items():
        mix[wlab] = {}
        for key in keys:
            Bo = (B0 - w * np.array(pref[key]["bulk_galactic_kms"])) / (1. - w)
            v = U + ng @ Bo
            mix[wlab][key] = dict(w=float(w), B_other_galactic_kms=Bo.tolist(), score=S(v, keys=(key,))[key],
                                  window_kept_score=S(v, window_keep, keys=(key,))[key])
    return dict(bulk_projection_max_abs_error_kms=projerr, sites_tsv_sha256=sha(ctx["directory"] / "sites.tsv"),
                decomposition=decomp, window_kept=window, shifts=shifts, preferred=pref, mixture=mix)


def coras_conditioning(sc, rep, sens, ctx, const, ex):
    """CF3-calibration conditioning record of one CORAS scorer (review CF3-2)."""
    cfg, est = ctx["config"], const["estimated"]
    if cfg["growth_fsigma8"] != est["fsigma8"] or [float(t) for t in cfg["external_bulk_galactic_kms"]] != est["bulk_galactic_kms"]:
        raise ValueError("CORAS run configuration differs from the CF3-calibrated constants")
    keys = list(sc.b["folds"])
    d = sens["decomposition"]
    for key in keys:
        checks = ((d["as_run"][key], rep["sum_full"][key]["coras_mean_offset"]),
                  (d["offset_only"][key], rep["sum_full"][key]["offset_only"]),
                  (sens["window_kept"]["as_run"][key],
                   ex["CF3_calibration_window"]["test_only"][key]["sum_kept_minus_zero"]["coras_mean_offset"]))
        for a, b in checks:
            if abs(a - b) > 1e-8:
                raise ValueError(f"sensitivity scorer disagrees with replay: {a} vs {b}")
    bound = {}
    for key in keys:
        a = d["as_run"][key]
        contrast = a - d["offset_only"][key]
        tot = [v["score"][key] for n, v in sens["shifts"].items() if n.endswith("eTot")]
        dist = [v["score"][key] for n, v in sens["shifts"].items() if n.endswith("eDist")]
        leak = {w: a - m[key]["score"] for w, m in sens["mixture"].items()}
        lmax = max(leak.values())
        bound[key] = dict(
            contrast_coras_mean_offset_minus_offset_only=contrast,
            bulk_only_minus_offset_only=d["bulk_only"][key] - d["offset_only"][key],
            as_run_minus_bulk_removed=a - d["bulk_removed"][key],
            eTot_shift_delta_vs_as_run_min_max=[min(tot) - a, max(tot) - a],
            eDist_shift_delta_vs_as_run_min_max=[min(dist) - a, max(dist) - a],
            preferred_bulk_in_sample_gain=sens["preferred"][key]["score"] - a,
            leakage_proxy_as_run_minus_B_other=leak, leakage_proxy_max=lmax,
            leakage_proxy_max_fraction_of_contrast=lmax / contrast,
            contrast_after_max_leakage_proxy=contrast - lmax)
    return dict(
        classification="conditional prediction (working-model relative scores under alternative CORAS mean fields); "
                       "sensitivity bound is an approximation, not a CORAS re-calibration; no physical attribution",
        conditional_on=dict(fsigma8=est["fsigma8"], external_bulk_galactic_kms=est["bulk_galactic_kms"],
                            source_comment=est["source_comment"],
                            calibrated_row_rs15_czmin2000=const["calibrated_row_rs15_czmin2000"]),
        held_out_with_respect_to_cf3_calibration=False,
        statement=("All CORAS scores are conditional on the CF3-calibrated fsigma8=0.405 and external bulk (95,-172,28) km/s, "
                   "applied at every 6dFGSv site (fsigma8 scales mean and draws; the bulk is added to the mean). The CF3 "
                   "calibration groups (2000-16000 km/s) contain most 6dFGSv rows (cf3_calibration_window), so the CORAS "
                   "scores are not held out with respect to the CF3 calibration, and row-exclusion folds cannot remove this "
                   "parameter-level lineage from the full-sample score."),
        statistic="coras_mean_offset (CORAS mean field with 5 common offsets, equal prior) minus zero, summed over the R105 "
                  "folds with the replayed R105 probit fits; offset_only = R105 offset-only components",
        bulk_projection_check=dict(max_abs_error_kms=sens["bulk_projection_max_abs_error_kms"],
                                   sites_tsv_sha256=sens["sites_tsv_sha256"],
                                   note="bulk projection on the C++ driver's site angles vs galactic unit vectors"),
        bulk_decomposition=dict(
            definitions=dict(offset_only="no field, 5 offsets", bulk_only="CF3 bulk dipole only (no 2MRS field), 5 offsets",
                             bulk_removed="CORAS mean minus the CF3 bulk projection, 5 offsets",
                             as_run="CORAS mean as run (2MRS field x fsigma8 + CF3 bulk), 5 offsets"),
            **{k: d[k] for k in ("offset_only", "bulk_only", "bulk_removed", "as_run")}),
        parameter_sensitivity=dict(
            method=("Scores recomputed with the CF3 bulk shifted by +/- its total and distance-error parts per galactic axis, "
                    "fsigma8 shifted by +/- its total and distance-error parts (2MRS part rescaled), the in-sample "
                    "6dF-preferred bulk (Nelder-Mead on the full-sample score; an in-sample reference, not held out), and "
                    "B_other = (B_CF3 - w B_6dF)/(1 - w) for w = the 6dFGSv information shares of the CF3 window computed "
                    "here (velocity- and mu-space; velocity space is the relevant weight for a bulk fit). Leakage proxy = "
                    "as_run - score(B_other): a linear information-weighting approximation, not CORAS estimate_parameters "
                    "re-run without 6dF."),
            shifts=sens["shifts"], preferred_bulk_in_sample=sens["preferred"], mixture=sens["mixture"], bound=bound),
        definitive_control_not_run="CORAS estimate_parameters on CF3 groups with 6dF-contributed moduli removed, then rescore")


def window_scope_record(cal_any, inc, cz, scoring):
    """Scope of the CF3_calibration_window fold (review CF3-2)."""
    kept = ~cal_any
    base = dict(
        n_kept=int(kept.sum()), n_kept_selected=int((kept & inc).sum()),
        kept_cz_gal_p10_p50_p90_kms=np.percentile(cz[kept], [10, 50, 90]).tolist(),
        n_kept_cz_below_2000=int(np.sum(kept & (cz < 2000.))), n_kept_cz_above_16000=int(np.sum(kept & (cz > 16000.))),
        n_kept_cz_2000_16000=int(np.sum(kept & (cz >= 2000.) & (cz <= 16000.))),
        statement=("This fold removes 6dFGSv rows whose CF3 group lies in the CORAS calibration window (CMB or LG frame). "
                   "The kept rows never entered the CF3 (fsigma8, bulk) fit, so the fold is a leakage-free score of the "
                   "CF3-calibrated parameters on those rows only; they are cz-edge rows (galaxy cz percentiles above; the "
                   "window is defined on CF3 group cz). It tests only these rows, has no power for full-sample parameter "
                   "leakage, and cannot bound leakage in the full-sample score (see coras_conditioning)."))
    out = {}
    for name, res in scoring.items():
        coras = "coras_conditioning" in res
        contrast = "coras_mean_offset_minus_offset_only" if coras else "fixed_2mrs_offset_minus_offset_only"
        t = res["exclusions"]["CF3_calibration_window"]["test_only"]
        rec = dict(base, contrast=contrast, per_key={})
        for key, r in t.items():
            c = r["control"][contrast]
            row = dict(observed=r["sum_kept_minus_zero"][contrast], control_mean=c["mean"], control_sd=c["sd"],
                       p_le_plus_one=c["p_le_plus_one"], replicates=c["replicates"])
            if coras:
                mix = res["coras_conditioning"]["parameter_sensitivity"]["mixture"]
                a = res["coras_conditioning"]["bulk_decomposition"]["as_run"][key]
                full_leak = {w: a - m[key]["score"] for w, m in mix.items()}
                kept_leak = {w: r["sum_kept_minus_zero"]["coras_mean_offset"] - m[key]["window_kept_score"]
                             for w, m in mix.items()}
                row.update(leakage_proxy_on_kept_rows=kept_leak,
                           max_abs_leakage_proxy_on_kept_rows_over_control_sd=max(abs(v) for v in kept_leak.values()) / c["sd"],
                           leakage_proxy_full_sample=full_leak)
            rec["per_key"][key] = row
        if coras:
            ratio = max(r_["max_abs_leakage_proxy_on_kept_rows_over_control_sd"] for r_ in rec["per_key"].values())
            full = max(max(r_["leakage_proxy_full_sample"].values()) for r_ in rec["per_key"].values())
            rec["power_statement"] = (
                f"The leakage-proxy score change on the kept rows is at most {ratio:.2f} control sd (largest share tried), "
                f"against at most {full:.2f} nats on the full sample: a single fold realisation cannot detect it, and "
                "the fold cannot bound the full-sample leakage.")
        else:
            rec["note"] = "R104 2MRS-NeuralNet field: no CF3 parameter lineage is evaluated here"
        out[name] = rec
    return out


def _cmp(block, key, stat):
    """Observed vs control summary of one statistic in a test_only or drop block."""
    if not isinstance(block, dict):
        return None
    r = block["per_key"][key] if "per_key" in block else block[key]
    o, c = r["sum_kept_minus_zero"].get(stat), r["control"].get(stat)
    if not isinstance(c, dict):
        return dict(observed=o)
    return dict(observed=o, control_mean=c.get("mean"), control_sd=c.get("sd"), p_le_plus_one=c.get("p_le_plus_one"),
                p_ge_plus_one=c.get("p_ge_plus_one"), replicates=c.get("replicates"))


def review_summary(scoring, zp, cfdef):
    """Compact extract of the review-relevant numbers of this run (no new computation)."""
    out = dict(note="extracted from this run's scoring blocks; full records in scoring.*")
    for name, res in scoring.items():
        coras = "coras_conditioning" in res
        stats = (["offset_only", "coras_mean", "coras_mean_offset", "coras_mean_offset_minus_offset_only"] if coras else
                 ["offset_only", "fixed_2mrs", "fixed_2mrs_offset", "fixed_2mrs_offset_minus_offset_only"])
        r = {}
        for ename in MAGNITUDE_DEFINED[1:]:
            ex = res["exclusions"][ename]
            e = {blk: {key: {st: _cmp(ex[blk], key, st) for st in stats} for key in ("pgc", "pgc1")}
                 for blk in ALL_BLOCKS if isinstance(ex.get(blk), dict)}
            conf = ex["test_only"]["pgc"]["mark_zero_point_confound"]
            e.update(comparable_statistic=ex["comparability"]["comparable_statistic"],
                     non_comparable_blocks=ex["comparability"].get("non_comparable_blocks"),
                     test_only_kept_zero_point_dex=dict(observed=conf["observed"], control_mean=conf["control"]["mean"],
                                                        control_sd=conf["control"]["sd"],
                                                        z=conf["z_observed_minus_control_mean_over_sd"]) if conf else None)
            r[ename] = e
        nz = res["exclusions"]["none"].get("drop_recentered_czbin")
        if isinstance(nz, dict):
            r["none_drop_recentered_czbin_full_sample"] = {key: {st: nz["per_key"][key]["sum_kept_minus_zero"][st]
                                                                 for st in stats} for key in ("pgc", "pgc1")}
        r["CF3_calibration_window_scope"] = res["exclusions"]["CF3_calibration_window"].get("scope_note", {}).get("per_key")
        r["CF3_member_degenerate"] = {key: res["exclusions"]["CF3_member"]["test_only"][key]["degenerate"]
                                      for key in ("pgc", "pgc1")}
        if coras:
            cc = res["coras_conditioning"]
            r["coras_bulk_decomposition"] = {k: cc["bulk_decomposition"][k]
                                             for k in ("offset_only", "bulk_only", "bulk_removed", "as_run")}
            r["coras_parameter_bound"] = cc["parameter_sensitivity"]["bound"]
        out[name] = r
    sp = zp["sixdf_delta_d_2mrs_member_minus_nonmember"]
    out["zero_point_2mrs_member_minus_nonmember_dex"] = dict(
        per_bin={k: v["difference_dex"] for k, v in sp["bins"].items()}, heterogeneity=sp["heterogeneity"],
        velocity_equivalent_exact=sp["velocity_equivalent_exact_at_median_cz"], label=sp["label"])
    out["cf3_member"] = dict(n_any_route=cfdef["n_any_route"], tight=cfdef["tight_position_route"],
                             n_any_route_or_tight=cfdef["n_any_route_or_tight"], n_parent=cfdef["n_parent"],
                             coras_copy_minus_readme=cfdef["coras_copy_minus_readme"],
                             n_counterparts_missed_by_cz_gate=len(cfdef["counterparts_missed_by_sky_route_cz_gate"]),
                             n_rows_without_any_counterpart=len(cfdef["rows_without_any_counterpart"]),
                             emu_fingerprint=cfdef["emu_fingerprint"])
    return out


# ----------------------------------------------------------------------------- main analysis

def build(args):
    t0 = time.time()
    from scripts.r105 import cf4_field_holdout as mark
    from scripts.r105 import cf4_coras_marks as cmarks
    from scripts.r105 import coras_reduce
    from scripts.r104 import cf4_2mrs_field as field
    from scripts.r103 import manticore_cf4_pv as pv

    if os.popen(f"git -C '{DONOR}' rev-parse HEAD").read().strip() != DONOR_COMMIT:
        raise ValueError("CORAS donor commit changed")
    const = coras_constants()
    old, s, inc, x, nn_mu, links, alpha, u, models, field_sha = mark.source_sample()
    r100 = old.r100
    t2 = r100.load_cf4_table2()
    sdss = r100.load_sdss_pv()
    cf3 = load_cf3()
    mrs = load_2mrs()
    N = s["n"]
    names = np.asarray(s["ids"])
    cz6 = s["cz_gal"].astype(float)
    n6 = field.to_galactic(field.hp.ang2vec(s["ra"], s["dec"], lonlat=True))

    # -- 6dFGSv -> CF4 table2 (R103 rule) and PGC route to CF3
    m4 = old.sixdf_match_ambiguity_policies(t2, s, arcsec=ARCSEC, dv_kms=DV)
    cl = m4["closest_table2_indices"]
    if not np.array_equal(m4["policies"]["unique_only_r101"]["included"], inc):
        raise ValueError("R105 inclusion changed")
    pgc4 = np.where(cl >= 0, t2["pgc"][np.maximum(cl, 0)], -1)
    cf4_count = np.where(cl < 0, "0", np.where(inc, "1", "2+"))
    cf3_index = {int(p): i for i, p in enumerate(cf3["pgc"])}
    via_pgc = np.array([cf3_index.get(int(p), -1) for p in pgc4])

    # -- 6dFGSv -> CF3 by sky + CMB cz
    n3 = unit_gal(cf3["lat"], cf3["lon"])
    cz3_cmb = cf3["cz_helio"] + frame_shift(cf3["lat"], cf3["lon"], const["frames"]["CMB"])
    m3 = sky_match(n6, cz6, n3, cz3_cmb)
    via_pos = m3["best"]
    cf3_row = np.where(via_pos >= 0, via_pos, via_pgc)
    route = np.where((via_pos >= 0) & (via_pgc >= 0), np.where(via_pos == via_pgc, "both_agree", "both_disagree"),
                     np.where(via_pos >= 0, "position_only", np.where(via_pgc >= 0, "pgc_only", "none")))
    # -- tight position-only route (review CF3-3): nearest CF3 galaxy within TIGHT_ARCSEC, no cz gate
    mt = sky_match(n6, cz6, n3, cz3_cmb, arcsec=TIGHT_ARCSEC, dv=np.inf)
    via_tight = mt["best"]
    cf3_definition = cf3_member_record(names, route, via_pos, via_pgc, cf3_row, mt, n6, n3, cz6, cz3_cmb, cf3, inc)

    # -- 6dFGSv -> 2MRS by sky + CMB cz, and by designation coordinates
    nm = unit_gal(mrs["lat"], mrs["lon"])
    czm_cmb = mrs["cz"] + frame_shift(mrs["lat"], mrs["lon"], const["frames"]["CMB"])
    mm = sky_match(n6, cz6, nm, czm_cmb)
    d6, dm = designation_radec(names, "6df"), designation_radec(mrs["id"], "2mass")
    mdes = sky_match(icrs_unit(*d6.T), cz6, icrs_unit(*dm.T), czm_cmb, arcsec=2.5)
    des_check = dict(arcsec=2.5, n_matched=int((mdes["best"] >= 0).sum()),
                     n_agree_with_sky_route=int(np.sum((mdes["best"] >= 0) & (mdes["best"] == mm["best"]))),
                     n_designation_only=int(np.sum((mdes["best"] >= 0) & (mm["best"] < 0))),
                     n_sky_only=int(np.sum((mdes["best"] < 0) & (mm["best"] >= 0))),
                     n_disagree=int(np.sum((mdes["best"] >= 0) & (mm["best"] >= 0) & (mdes["best"] != mm["best"]))),
                     sixdf_designation_vs_table_position_arcsec_p50_max=[
                         float(np.median(np.rad2deg(np.arccos(np.clip(np.sum(icrs_unit(*d6.T) * icrs_unit(s["ra"], s["dec"]), 1), -1, 1))) * 3600)),
                         float(np.max(np.rad2deg(np.arccos(np.clip(np.sum(icrs_unit(*d6.T) * icrs_unit(s["ra"], s["dec"]), 1), -1, 1))) * 3600))])
    keep_cmb, cut_cmb = coras_2mrs_input(mrs, const, "CMB")
    keep_lg, cut_lg = coras_2mrs_input(mrs, const, "LG")
    mrs_row = mm["best"]
    in_2mrs = mrs_row >= 0
    in_coras = in_2mrs & keep_cmb[np.maximum(mrs_row, 0)]

    # -- CF3 groups: calibration window and 6dF information share
    six_cf3 = np.zeros(len(cf3["pgc"]), bool)
    six_cf3[cf3_row[cf3_row >= 0]] = True
    w = 1. / cf3["emu"] ** 2
    G = len(cf3["gid"])
    wden = np.bincount(cf3["group_row"], weights=w, minlength=G)
    share = np.divide(np.bincount(cf3["group_row"], weights=w * six_cf3, minlength=G), wden,
                      out=np.zeros(G), where=wden > 0)
    n6_in_group = np.bincount(cf3["group_row"], weights=six_cf3.astype(float), minlength=G).astype(int)
    window, window_summary = {}, {}
    lo, hi = const["calibration_cz_window_kms"]
    for fr in ("CMB", "LG"):
        v = cf3["gcz_helio"] + frame_shift(cf3["glat"], cf3["glon"], const["frames"][fr])
        window[fr] = (v >= lo) & (v <= hi)
        wm = 1. / cf3["gemu"] ** 2
        wv = 1. / (np.log(10.) / 5. * np.maximum(v, 1.) * cf3["gemu"]) ** 2
        W = window[fr]
        window_summary[fr] = dict(
            n_groups_in_window=int(W.sum()), n_groups_total=int(G),
            n_window_groups_with_6dfgsv_member=int(np.sum(W & (n6_in_group > 0))),
            n_6dfgsv_galaxies_in_window_groups=int(n6_in_group[W].sum()),
            mu_inverse_variance_share_of_groups_with_6dfgsv=float(wm[W & (n6_in_group > 0)].sum() / wm[W].sum()),
            mu_inverse_variance_share_attributable_to_6dfgsv=float((share * wm)[W].sum() / wm[W].sum()),
            velocity_inverse_variance_share_attributable_to_6dfgsv=float((share * wv)[W].sum() / wv[W].sum()),
            note="distance-error inverse variances only; CORAS likelihood also has reconstruction noise and a 5-sigma clip")
    grow = np.where(cf3_row >= 0, cf3["group_row"][np.maximum(cf3_row, 0)], -1)
    cal_cmb = (grow >= 0) & window["CMB"][np.maximum(grow, 0)]
    cal_lg = (grow >= 0) & window["LG"][np.maximum(grow, 0)]
    in_cf3 = cf3_row >= 0
    cal_any = cal_cmb | cal_lg

    # -- CF4 table2 galaxies: CF3 membership by method / FP survey; 2MRS by sky
    t2_in_cf3 = np.isin(t2["pgc"], cf3["pgc"])
    t2_6df = np.zeros(t2["n"], bool)
    t2_6df[cl[cl >= 0]] = True
    t2_sdss = np.isin(t2["pgc"], sdss["pgc"])
    meth = {lab: np.isfinite(t2[k]) for lab, k in METHODS}
    gal_counts = {}
    for lab, has in meth.items():
        gal_counts[lab] = dict(n_cf4=int(has.sum()), n_cf4_in_cf3=int((has & t2_in_cf3).sum()))
    fp = meth["FP"]
    fp_label = np.where(t2_6df, "6dFGSv", np.where(t2_sdss, "SDSS_PV", "other"))
    gal_counts["FP_by_survey"] = {lab: dict(n_cf4=int(np.sum(fp & (fp_label == lab))),
                                            n_cf4_in_cf3=int(np.sum(fp & (fp_label == lab) & t2_in_cf3)))
                                  for lab in ("6dFGSv", "SDSS_PV", "other")}
    gal_counts["FP_6dFGSv_and_SDSS_PV_both"] = int(np.sum(fp & t2_6df & t2_sdss))
    gal_counts["all"] = dict(n_cf4=int(t2["n"]), n_cf4_in_cf3=int(t2_in_cf3.sum()))
    n4 = field.to_galactic(field.hp.ang2vec(t2["ra"], t2["dec"], lonlat=True))
    m42 = sky_match(n4, t2["vcmb"].astype(float), nm, czm_cmb)
    t2_in_2mrs = m42["best"] >= 0
    t2_in_coras = t2_in_2mrs & keep_cmb[np.maximum(m42["best"], 0)]
    gal_counts["all"].update(n_cf4_matched_2mrs=int(t2_in_2mrs.sum()), n_cf4_in_coras_2mrs_input=int(t2_in_coras.sum()))
    m32 = sky_match(n3, cz3_cmb, nm, czm_cmb)
    cf3_in_coras = (m32["best"] >= 0) & keep_cmb[np.maximum(m32["best"], 0)]

    # -- R98 CF4 groups
    gids, directions, distances, _ = pv.geometry()
    gal = field.to_galactic(directions)
    _, covered = field.interpolate(field.load_field(), gal * (distances * field.H_LITTLE)[:, None])
    pos = {int(g): i for i, g in enumerate(gids)}
    gi = np.array([pos.get(int(p), -1) for p in t2["pgc1"]])
    inr98 = gi >= 0
    ng = len(gids)

    def per_group(mask):
        return np.bincount(gi[inr98 & mask], minlength=ng)

    gstats = dict(members=per_group(np.ones(t2["n"], bool)), cf3=per_group(t2_in_cf3), sixdf=per_group(t2_6df),
                  coras2mrs=per_group(t2_in_coras))
    for lab, has in meth.items():
        gstats[lab] = per_group(has)
        gstats[lab + "_cf3"] = per_group(has & t2_in_cf3)
    for lab in ("6dFGSv", "SDSS_PV", "other"):
        gstats["FP_" + lab] = per_group(fp & (fp_label == lab))
        gstats["FP_" + lab + "_cf3"] = per_group(fp & (fp_label == lab) & t2_in_cf3)

    def group_counts(sel):
        out = dict(n_groups=int(sel.sum()), n_with_cf3_member=int(np.sum(sel & (gstats["cf3"] > 0))),
                   n_with_6dfgsv_member=int(np.sum(sel & (gstats["sixdf"] > 0))),
                   n_with_coras_2mrs_member=int(np.sum(sel & (gstats["coras2mrs"] > 0))),
                   n_galaxies=int(gstats["members"][sel].sum()), n_galaxies_in_cf3=int(gstats["cf3"][sel].sum()))
        for lab in [m[0] for m in METHODS] + ["FP_6dFGSv", "FP_SDSS_PV", "FP_other"]:
            out[lab] = dict(n_groups_with_method=int(np.sum(sel & (gstats[lab] > 0))),
                            n_groups_with_cf3_member_having_method=int(np.sum(sel & (gstats[lab + "_cf3"] > 0))))
        return out

    groups = dict(r98_selected=group_counts(np.ones(ng, bool)), field_covered=group_counts(covered),
                  field_missing=group_counts(~covered),
                  n_cf4_table2_rows_in_r98_groups=int(inr98.sum()))
    if (int(covered.sum()), ng) != (21860, 35970):
        raise ValueError("R98 group selection or 2MRS coverage changed")

    # -- zero-point lineage
    mu6 = mu_from_delta(cz6, s["delta_d"])
    mufid = mu_from_delta(cz6, np.zeros(N))
    k3 = in_cf3
    mu3 = np.where(k3, cf3["mu"][np.maximum(cf3_row, 0)], np.nan)
    e3 = np.where(k3, cf3["emu"][np.maximum(cf3_row, 0)], np.nan)
    fp4 = np.where(cl >= 0, t2["dmfp"][np.maximum(cl, 0)], np.nan)
    dm4 = np.where(cl >= 0, t2["dm"][np.maximum(cl, 0)], np.nan)
    both = k3 & np.isfinite(fp4)
    zp = dict(
        convention="mu_6dF = 5 log10[(1+z) D_C(z_CMB; Om=0.3, H0=75 km/s/Mpc) 10^-delta_d] + 25; CF3 mu from CORAS member file",
        cf3_minus_6dfgsv=robust(mu3[k3] - mu6[k3]),
        cf3_minus_6dfgsv_by_cz={f"{a:.0f}-{b:.0f}": robust((mu3 - mu6)[k3 & (cz6 >= a) & (cz6 < b)])
                                for a, b in ((0, 6000), (6000, 10000), (10000, 14000), (14000, 20000))},
        hubble_residual_pearson_cf3_vs_6dfgsv=float(np.corrcoef(mu3[k3] - mufid[k3], mu6[k3] - mufid[k3])[0, 1]),
        cf3_error_values_mag={f"{v:.2f}": int(c) for v, c in zip(*np.unique(np.round(e3[k3], 2), return_counts=True))},
        cf4_fp_minus_cf3=robust(fp4[both] - mu3[both]),
        cf4_fp_minus_6dfgsv=robust(fp4[np.isfinite(fp4)] - mu6[np.isfinite(fp4)]),
        cf4_all_minus_cf3_for_6dfgsv=robust(dm4[k3 & np.isfinite(dm4)] - mu3[k3 & np.isfinite(dm4)]),
        hubble_residual_pearson_cf4fp_vs_6dfgsv=float(np.corrcoef(fp4[np.isfinite(fp4)] - mufid[np.isfinite(fp4)],
                                                                  mu6[np.isfinite(fp4)] - mufid[np.isfinite(fp4)])[0, 1]),
        hubble_residual_pearson_cf4fp_vs_cf3=float(np.corrcoef(fp4[both] - mufid[both], mu3[both] - mufid[both])[0, 1]))
    single = {}
    mu3_t2 = np.array([cf3["mu"][cf3_index[int(p)]] if int(p) in cf3_index else np.nan for p in t2["pgc"]])
    nmeth = sum(h.astype(int) for h in meth.values())
    for lab, k in METHODS:
        sel = meth[lab] & (nmeth == 1) & np.isfinite(mu3_t2)
        single[lab] = robust(t2[k][sel] - mu3_t2[sel])
    zp["cf4_single_method_minus_cf3_by_method"] = single
    med_cz = float(np.median(cz6))
    zp["velocity_equivalent_kms_at_median_6dfgsv_cz"] = dict(
        median_cz_kms=med_cz, **{k: float(np.log(10.) / 5. * zp[k]["median"] * med_cz)
                                 for k in ("cf3_minus_6dfgsv", "cf4_fp_minus_cf3", "cf4_fp_minus_6dfgsv")})
    def split(flag, label):
        """Inverse-variance mean delta_d of flag minus not-flag rows, within 2000 km/s cz bins and combined."""
        rows, num, den = {}, 0., 0.
        for a in range(0, 18000, 2000):
            sel = (cz6 >= a) & (cz6 < a + 2000)
            if np.sum(sel & flag) < 5 or np.sum(sel & ~flag) < 5:
                continue
            st = []
            for f in (flag, ~flag):
                ww = 1. / s["epsilon_d"][sel & f] ** 2
                st.append((float(np.sum(ww * s["delta_d"][sel & f]) / ww.sum()), float(ww.sum() ** -.5), int(np.sum(sel & f))))
            diff, err = st[0][0] - st[1][0], float(np.hypot(st[0][1], st[1][1]))
            rows[f"{a}-{a + 2000}"] = dict(mean_flag=st[0][0], err_flag=st[0][1], n_flag=st[0][2], mean_other=st[1][0],
                                           err_other=st[1][1], n_other=st[1][2], difference_dex=diff, difference_err_dex=err)
            num, den = num + diff / err ** 2, den + 1. / err ** 2
        het = heterogeneity([r["difference_dex"] for r in rows.values()], [r["difference_err_dex"] for r in rows.values()])
        comb = num / den
        return dict(bins=rows, combined_difference_dex=comb, combined_difference_err_dex=den ** -.5,
                    combined_difference_mag=5. * comb,
                    heterogeneity=dict(het, combined_err_inflated_dex=het["combined_err_inflated"],
                                       note="bins are not consistent with one constant when p_value_homogeneous is small; "
                                            "use the per-bin rows or the inflated error, not the bare combined error"),
                    velocity_equivalent_exact_at_median_cz=dict(
                        median_cz_kms=med_cz, kms=float(med_cz * (1. - 10. ** -comb)),
                        linear_approximation_kms=float(np.log(10.) * comb * med_cz),
                        note="equivalent only; see label: not a flow"),
                    label=label,
                    mean_epsilon_d_flag=float(s["epsilon_d"][flag].mean()), mean_epsilon_d_other=float(s["epsilon_d"][~flag].mean()),
                    note="6dFGSv delta_d=log10(D_z/D_H): positive difference = flagged galaxies appear nearer than cz implies; "
                         "error from epsilon_d only (no FP covariance, no velocity field)")
    zp["sixdf_delta_d_2mrs_member_minus_nonmember"] = split(
        in_coras, "selection-induced FP-residual zero-point offset (2MRS Ks <= limit picks positive FP residuals at fixed cz), "
                  "not a peculiar velocity")
    zp["sixdf_delta_d_cf3_window_minus_outside"] = split(
        cal_any, "zero-point difference between CF3-window and cz-edge rows; not a peculiar velocity")
    zp["coras_distance_catalog_h"] = dict(fiducial=0.75, estimated=const["estimated"]["distance_catalog_h"],
                                          calibrated_row=const["calibrated_row_rs15_czmin2000"]["h"])

    # -- R105 folds and fold identities
    ref = json.loads((R105 / "CF4_FIELD_HOLDOUT.json").read_text())
    folds = {}
    for key, clusters in links.items():
        folds[key] = []
        for f, (tr, te) in enumerate(old.group_kfold_indices(clusters, n_splits=5, seed=42)):
            if hashlib.sha256(("\n".join(sorted(names[te])) + "\n").encode()).hexdigest() != \
                    ref["folds"][key]["folds"][f]["sorted_test_id_sha256"]:
                raise ValueError("R105 fold identity mismatch")
            folds[key].append((tr, te))
    fold_of = {key: np.empty(N, int) for key in folds}
    for key, fl in folds.items():
        for f, (_, te) in enumerate(fl):
            fold_of[key][te] = f

    exclusions = {"none": np.zeros(N, bool), "2MRS_galaxy": in_2mrs, "2MRS_coras_input": in_coras, "complement_keep_only_2MRS_coras_input": ~in_coras,
                  "CF3_member": in_cf3, "CF3_calibration_window": cal_any,
                  "union_2MRS_coras_or_CF3_window": in_coras | cal_any}
    crosstab = {}
    for key, fl in folds.items():
        crosstab[key] = [dict(fold=f, n_test=int(len(te)), n_test_selected=int(inc[te].sum()),
                              **{f"n_{k}": int(v[te].sum()) for k, v in exclusions.items()},
                              **{f"n_selected_{k}": int((v & inc)[te].sum()) for k, v in exclusions.items()})
                         for f, (_, te) in enumerate(fl)]
    sixdf_counts = dict(
        n_parent=N, n_r105_selected=int(inc.sum()),
        cf4_table2=dict(multiplicity_histogram={int(k): int(v) for k, v in m4["multiplicity_histogram"].items()},
                        n_closest_any=int((cl >= 0).sum())),
        cf3=dict(sky_route=match_summary(m3), pgc_route_n=int((via_pgc >= 0).sum()),
                 routes={r: int(np.sum(route == r)) for r in ("both_agree", "both_disagree", "position_only", "pgc_only", "none")},
                 n_member_any_route=int(in_cf3.sum()), n_selected_member=int((in_cf3 & inc).sum()),
                 n_distinct_cf3_galaxies=int(len(np.unique(cf3_row[in_cf3]))),
                 n_in_calibration_window_CMB=int(cal_cmb.sum()), n_in_calibration_window_LG=int(cal_lg.sum()),
                 n_in_calibration_window_either=int(cal_any.sum()), n_in_calibration_window_both=int((cal_cmb & cal_lg).sum()),
                 n_cf3_member_outside_window_both=int(np.sum(in_cf3 & ~cal_any)),
                 cf4_method_flags_of_cf3_members={lab: int(np.sum(in_cf3 & (cl >= 0) & meth[lab][np.maximum(cl, 0)]))
                                                  for lab in meth},
                 n_cf3_members_without_cf4_row=int(np.sum(in_cf3 & (cl < 0)))),
        twomrs=dict(sky_route=match_summary(mm), designation_route=des_check, n_matched=int(in_2mrs.sum()),
                    n_in_coras_input_cmb=int(in_coras.sum()),
                    n_in_coras_input_lg=int(np.sum(in_2mrs & keep_lg[np.maximum(mrs_row, 0)])),
                    n_selected_matched=int((in_2mrs & inc).sum()), n_selected_in_coras_input=int((in_coras & inc).sum()),
                    n_also_cf3_window=int((in_coras & cal_any).sum()),
                    n_neither_2mrs_coras_nor_cf3_window=int(np.sum(~in_coras & ~cal_any))),
        r105_folds=crosstab)
    twomrs_input = dict(cmb_pilot_frame=cut_cmb, lg_frame=cut_lg, zone_of_avoidance_clones="not counted (synthetic)",
                        cf3_galaxies_matched_to_coras_input=int(cf3_in_coras.sum()), cf3_galaxies=int(len(cf3["pgc"])),
                        cf3_galaxies_matched_to_any_2mrs=int((m32["best"] >= 0).sum()))

    # -- scoring
    y = np.where(inc, s["delta_d"], np.nan)
    sig = s["epsilon_d"]
    zbin = np.floor(cz6 / CZ_BIN).astype(int)
    strata = 2 * zbin + inc.astype(int)
    strata_eps = eps_quintile_strata(strata, cz6, sig)
    rb = np.floor(cz6 / CZ_RECENTER_BIN).astype(int)
    rbins = np.unique(rb)
    zp_acc = dict(wy=np.where(inc, s["delta_d"] / sig ** 2, 0.), w=np.where(inc, 1. / sig ** 2, 0.),
                  eps_sel=np.where(inc, sig, 0.), sel=inc.astype(float),
                  binm=(rb[:, None] == rbins[None, :]).astype(float),
                  bin_labels=[f"{int(k * CZ_RECENTER_BIN)}-{int((k + 1) * CZ_RECENTER_BIN)}" for k in rbins])
    base = dict(old=old, mark=mark, x=x, inc=inc, y=y, sig=sig, folds=folds, strata=strata, cz=cz6, zp=zp_acc)
    identical_sets = {a: sorted(b for b, Y in exclusions.items() if b != a and np.array_equal(X, Y))
                      for a, X in exclusions.items()}
    field_ref = {key: [r["scores_shared_minus_zero"] for r in ref["folds"][key]["folds"]] for key in folds}
    scorers = [Scorer("R105_field_holdout", nn_mu, models, base, field_ref, 1e-9,
                      contrasts={"fixed_2mrs_offset_minus_offset_only": ("fixed_2mrs_offset", "offset_only"),
                                 "trained_scale_offset_minus_offset_only": ("trained_scale_offset", "offset_only")})]

    geom, growth, sci, z = cmarks.site_geometry()
    coras_inputs, coras_ctx = {}, {}
    for spec in args.coras:
        directory, reference = (Path(t) for t in spec.split("="))
        rec, *_ = coras_reduce.metadata(directory, geom)
        if rec.get("catalogue") != geom["catalogue"] or rec.get("nodes") != ["SQ-CF4"]:
            raise ValueError("6dFGSv catalogue binding mismatch")
        seeds = list(range(rec["first"], rec["last"] + 1))
        residuals = [f"residual_{i}.tsv" for i in seeds]
        if set(rec["output_sha256"]) != set(residuals) | {"mean.tsv"}:
            raise ValueError("partial CORAS draw set")

        def read(name):
            p = directory / name
            if coras_reduce._sha(p) != rec["output_sha256"][name]:
                raise ValueError(f"field hash mismatch: {p}")
            return coras_reduce.read_radial(p, geom["ids"])

        mean = read("mean.tsv")
        offsets = np.array([-300., -100., 0., 100., 300.])
        mus = [np.zeros(N), nn_mu[models["fixed_2mrs"]][0]]
        tags = [("zero", 0.), ("nn", 0.)]
        for off in offsets:   # no-field common offsets (R105 'offset_only' components) for field-minus-offset contrasts
            mus.append(old.r99.finite_shift(sci, z, np.arctanh(off / old.r100.C), "bolometric") / (5 * old.r100.MAG))
            tags.append(("offset", off))
        for nm_ in ["mean.tsv", *residuals]:
            v = mean if nm_ == "mean.tsv" else mean + read(nm_)
            for off in offsets:
                mus.append(old.r99.finite_shift(sci, z, np.arctanh((off + growth * v) / old.r100.C), "bolometric") / (5 * old.r100.MAG))
                tags.append((nm_, off))
        mus = np.array(mus)
        tn, tu = np.array([t[0] for t in tags]), np.array([t[1] for t in tags])
        draw = np.isin(tn, residuals)
        choices = dict(zero=tn == "zero", nn=tn == "nn", offset_only=tn == "offset", coras_mean=(tn == "mean.tsv") & (tu == 0),
                       coras_mean_offset=tn == "mean.tsv", coras_draws=draw & (tu == 0), coras_draws_offset=draw)
        if len(seeds) >= 4:
            for half, subset in enumerate(np.array_split(residuals, 2)):
                choices[f"coras_half{half + 1}_offset"] = np.isin(tn, subset)
        cref = json.loads(reference.read_text())
        cfolds = {key: [r["shared_minus_zero"] for r in cref["folds"][key]] for key in folds}
        label = f"CORAS_{len(seeds)}draws_r{rec['config']['radial']}_l{rec['config']['ell']}_fft{rec['config']['fft']}"
        if np.max(abs(mus[tn == "offset"] - nn_mu[models["offset_only"]])) > 1e-12:
            raise ValueError("offset-only components differ from R105 field-holdout offsets")
        scorers.append(Scorer(label, mus, choices, base, cfolds, 1e-7, contrasts={
            "coras_mean_offset_minus_offset_only": ("coras_mean_offset", "offset_only"),
            "coras_draws_offset_minus_offset_only": ("coras_draws_offset", "offset_only")}))
        coras_ctx[label] = dict(mean=mean, directory=directory, config=rec["config"], offsets=offsets, growth=growth,
                                sci=sci, z=z, ng=geom["ng"], ids=geom["ids"], old=old,
                                offset_mus=mus[tn == "offset"])
        log = directory / "generate.log"
        logline = log.read_text().splitlines()[0] if log.is_file() else None
        mlog = re.fullmatch(r"2MRS input=(\d+) selected=(\d+) sites=(\d+)", logline or "")
        coras_inputs_log = dict(pilot_log_line=logline, pilot_selected_including_zoa_clones=int(mlog.group(2)) if mlog else None,
                                reproduced_real_galaxies_after_cut_cmb=int(keep_cmb.sum()),
                                implied_zoa_clones=int(mlog.group(2)) - int(keep_cmb.sum()) if mlog else None)
        coras_inputs[label] = dict(directory=str(directory), run_json_sha256=sha(directory / "run.json"), **coras_inputs_log,
                                   reference=str(reference), reference_sha256=sha(reference), config=rec["config"],
                                   seeds=[seeds[0], seeds[-1]], n_components=int(len(mus)),
                                   binary_sha256=rec["binary_sha256"], mean_sha256=rec["output_sha256"]["mean.tsv"])

    scoring = {}
    replays = {}
    for sc in scorers:
        ts = time.time()
        replays[sc.name] = (sc.replay(), time.time() - ts)
    shares = {f"velocity_share_{fr}": window_summary[fr]["velocity_inverse_variance_share_attributable_to_6dfgsv"]
              for fr in ("CMB", "LG")}
    shares.update({f"mu_share_{fr}": window_summary[fr]["mu_inverse_variance_share_attributable_to_6dfgsv"]
                   for fr in ("CMB", "LG")})
    _POOL.update(scorers=scorers, exclusions=exclusions, args=args, strata_eps=strata_eps, coras_ctx=coras_ctx,
                 const=const, shares=shares, window_keep=~cal_any)
    tasks = []
    for si, sc in enumerate(scorers):
        for ename, X in exclusions.items():
            tasks.append((si, ename, "test_only"))
            for blk, sets in (("drop", args.drop_sets), ("drop_recentered", args.recenter_sets),
                              ("drop_recentered_czbin", args.czbin_sets),
                              ("drop_recentered_czbin_eps_strata", args.czbin_eps_sets)):
                if ename in sets:
                    tasks.append((si, ename, blk))
        if sc.name in coras_ctx:
            tasks.append((si, None, "coras_sensitivity"))
    def cost(t):   # rough relative cost, for load balancing only
        if t[2] in ("test_only", "coras_sensitivity"):
            return len(scorers[t[0]].mus) * (1 if t[2] == "test_only" else 40)
        return len(scorers[t[0]].mus) * (33 if exclusions[t[1]].any() else 1)

    tasks.sort(key=lambda t: -cost(t))
    if args.jobs > 1:
        with mp.get_context("fork").Pool(args.jobs) as pool:
            done = dict(zip(tasks, pool.map(_run_block, tasks, chunksize=1)))
    else:
        done = {t: _run_block(t) for t in tasks}
    for si, sc in enumerate(scorers):
        rep, rsec = replays[sc.name]
        res = dict(replay=rep, exclusions={})
        secs = rsec
        for ename, X in exclusions.items():
            mag = ename in MAGNITUDE_DEFINED
            rec = dict(n_excluded_parent=int(X.sum()), n_excluded_selected=int((X & inc).sum()),
                       apparent_magnitude_defined=mag, identical_exclusion_sets=identical_sets[ename])
            for blk in ("test_only", "drop", "drop_recentered", "drop_recentered_czbin", "drop_recentered_czbin_eps_strata"):
                r = done.get((si, ename, blk))
                if r is None:
                    rec[blk] = "not run"
                    continue
                rec[blk], sec = r
                secs += sec
            if mag:
                for blk in ("drop", "drop_recentered"):
                    if isinstance(rec[blk], dict) and not rec[blk]["degenerate"]:
                        rec[blk]["not_comparable_reason"] = (
                            "apparent-magnitude-defined exclusion: the kept set's mark zero point differs from the controls' "
                            "and falls with cz (mark_zero_point_confound); " +
                            ("a single constant cannot remove a cz-dependent zero point: comparable only for the "
                             "offset-marginalised contrasts (*_minus_offset_only), whose +/-300 km/s offsets absorb part of "
                             "the trend" if blk == "drop_recentered" else "no recentring") +
                            ". Control fractions are not overlap or leakage evidence.")
                        if blk == "drop_recentered":
                            rec[blk]["comparable_scope"] = "offset-marginalised contrasts only"
            rec["comparability"] = comparability_record(ename, mag, rec)
            res["exclusions"][ename] = rec
        if sc.name in coras_ctx:
            sens, sec = done[(si, None, "coras_sensitivity")]
            secs += sec
            res["coras_conditioning"] = coras_conditioning(sc, rep, sens, coras_ctx[sc.name], const, res["exclusions"])
        res["seconds_cpu_summed_over_blocks"] = secs
        scoring[sc.name] = res
    window_scope = window_scope_record(cal_any, inc, cz6, scoring)
    for sc in scorers:
        scoring[sc.name]["exclusions"]["CF3_calibration_window"]["scope_note"] = window_scope[sc.name]
        scoring[sc.name]["exclusions"]["CF3_member"]["scope_note"] = cf3_definition["by_construction"]

    # -- outputs (an earlier CF3_OVERLAP.json and its TSVs are archived under superseded/ before being replaced)
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    supersedes = None
    if (out / "CF3_OVERLAP.json").is_file():
        old_sha = sha(out / "CF3_OVERLAP.json")
        arch = out / "superseded" / old_sha[:12]
        arch.mkdir(parents=True, exist_ok=True)
        for nm_ in ("CF3_OVERLAP.json", "SIXDF_CF3_2MRS_CROSSTABLE.tsv", "CF4_R98_GROUP_CF3_MEMBERSHIP.tsv"):
            if (out / nm_).is_file() and not (arch / nm_).is_file():
                shutil.copy2(out / nm_, arch / nm_)
        prev = json.loads((out / "CF3_OVERLAP.json").read_text())
        supersedes = dict(sha256=old_sha, archived_to=str(arch), code_sha256=prev.get("code", {}).get("sha256"))
    cols = ["row", "sixdf_id", "ra_deg", "dec_deg", "cz_cmb_kms", "delta_d", "epsilon_d", "r105_selected",
            "fold_pgc", "fold_pgc1", "cf4_count", "cf4_pgc", "cf4_pgc1", "cf4_dmfp", "cf3_route", "cf3_pgc",
            "cf3_sep_arcsec", "cf3_dcz_kms", "cf3_mu", "cf3_emu", "cf3_group", "cf3_group_in_window_cmb",
            "cf3_group_in_window_lg", "cf3_group_6df_information_share", "twomrs_id", "twomrs_sep_arcsec",
            "twomrs_dcz_kms", "twomrs_ks", "twomrs_in_coras_input_cmb", "mu_6df_h75",
            "cf3_pos2_pgc", "cf3_pos2_sep_arcsec", "cf3_pos2_dcz_kms"]
    lines = ["\t".join(cols)]
    for i in range(N):
        r3, rm = cf3_row[i], mrs_row[i]
        g = grow[i]
        lines.append("\t".join(str(t) for t in (
            i + 1, names[i], s["ra"][i], s["dec"][i], int(cz6[i]), s["delta_d"][i], s["epsilon_d"][i], int(inc[i]),
            fold_of["pgc"][i], fold_of["pgc1"][i], cf4_count[i], int(pgc4[i]),
            int(t2["pgc1"][cl[i]]) if cl[i] >= 0 else -1, f"{fp4[i]:.3f}" if np.isfinite(fp4[i]) else "nan", route[i],
            int(cf3["pgc"][r3]) if r3 >= 0 else -1, f"{m3['sep_arcsec'][i]:.3f}", f"{m3['dv_kms'][i]:.1f}",
            f"{mu3[i]:.2f}", f"{e3[i]:.2f}", int(cf3["group"][r3]) if r3 >= 0 else -1,
            int(window["CMB"][g]) if g >= 0 else -1, int(window["LG"][g]) if g >= 0 else -1,
            f"{share[g]:.4f}" if g >= 0 else "nan", mrs["id"][rm] if rm >= 0 else "-",
            f"{mm['sep_arcsec'][i]:.3f}", f"{mm['dv_kms'][i]:.1f}", f"{mrs['ks'][rm]:.3f}" if rm >= 0 else "nan",
            int(in_coras[i]), f"{mu6[i]:.4f}",
            int(cf3["pgc"][via_tight[i]]) if via_tight[i] >= 0 else -1, f"{mt['sep_arcsec'][i]:.3f}",
            f"{mt['dv_kms'][i]:.1f}")))
    write(out / "SIXDF_CF3_2MRS_CROSSTABLE.tsv", "\n".join(lines) + "\n")
    gcols = ["group_1pgc", "field_covered", "n_members"] + [k for k in gstats if k != "members"]
    glines = ["\t".join(gcols)]
    for i in range(ng):
        glines.append("\t".join([str(int(gids[i])), str(int(covered[i])), str(int(gstats["members"][i]))] +
                                [str(int(gstats[k][i])) for k in gcols[3:]]))
    write(out / "CF4_R98_GROUP_CF3_MEMBERSHIP.tsv", "\n".join(glines) + "\n")

    inputs = {
        "sixdf_table1": r100.SIXDF_PATH, "sdss_pv_public": r100.SDSS_PATH, "cf4_table2": t2["path"],
        "cf4_table3": t2["path"].parent / "table3.dat", "cf4_table4": t2["path"].parent / "table4.dat",
        "coras_cf3_members": DONOR / "data/CF3_group_member_catalog.dat", "coras_cf3_groups": DONOR / "data/CF3_group_catalog.dat",
        "coras_2mrs_members": DONOR / "data/2MRS_group_member_catalog.dat",
        "coras_calibrated_parameters": DONOR / "data/calibrated_parameters_CR1-50.dat",
        "coras_configuration": DONOR / "configuration.hpp", "coras_transformations": DONOR / "src/transformations.cpp",
        "coras_survey": DONOR / "src/survey.cpp", "coras_cosmology": DONOR / "src/cosmology.cpp",
        "r105_field_holdout": R105 / "CF4_FIELD_HOLDOUT.json", "r105_coras_marks": R105 / "CF4_CORAS_MARKS.json",
        "r105_coras_draw_run": R105 / "CF4_CORAS_DRAW_RUN.json", "cf3_readme_local": CF3_README,
        **{f"coras_sites_{lab}": Path(rec_["directory"]) / "sites.tsv" for lab, rec_ in coras_inputs.items()},
        **{f"coras_run_json_{lab}": Path(rec_["directory"]) / "run.json" for lab, rec_ in coras_inputs.items()},
        **{f"coras_reference_{lab}": Path(rec_["reference"]) for lab, rec_ in coras_inputs.items()},
    }
    outputs = {nm_: sha(out / nm_) for nm_ in ("SIXDF_CF3_2MRS_CROSSTABLE.tsv", "CF4_R98_GROUP_CF3_MEMBERSHIP.tsv")}
    env = {k: os.environ.get(k) for k in ("PYTHONPATH", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                                          "PYTHONDONTWRITEBYTECODE")}
    command = ("cd " + shlex.quote(str(ROOT)) + " && " +
               " ".join(f"{k}={shlex.quote(v)}" for k, v in env.items() if v is not None) + " " +
               shlex.quote(sys.executable) + " -B " + " ".join(shlex.quote(a) for a in sys.argv))
    cf3_table3_present = Path(CF3_TABLE3_EXPECTED["recorded_path"]).is_file()
    payload = dict(
        schema="htt.r106.cf3_overlap/2",
        classification=dict(
            physical_attribution="none: no flow, Pi/G_F, H0-axis or Bianchi attribution; zero-point offsets of "
                                 "magnitude-selected subsets are selection effects, not velocities",
            conditional_prediction="working-model relative log predictive scores on R105 folds (exclusion folds, "
                                   "cz-binned recentring, CORAS bulk decomposition and parameter sensitivity); CORAS "
                                   "scores conditional on the CF3-calibrated fsigma8 and bulk; no calibrated p",
            numerical_reproduction="R105 fold scores replayed to stated tolerance before any exclusion; the sensitivity "
                                   "scorer reproduces the replayed coras_mean_offset/offset_only sums and the window-fold "
                                   "kept sums to 1e-8. This is reproduction, not numerical convergence: no resolution or "
                                   "draw-count convergence is claimed here",
            sample_lineage="catalogue cross-identification and calibration-window bookkeeping (no physical claim)",
            exclusion_folds="control fractions of apparent-magnitude-defined exclusion sets (test_only, drop, and "
                            "constant-recentred drop outside the offset-marginalised contrasts) are not comparable and "
                            "are not overlap or leakage evidence; see scoring.*.exclusions.*.comparability"),
        review_corrections=REVIEW_CORRECTIONS,
        commands=[dict(shell=command, argv=sys.argv, environment=env, jobs=args.jobs)],
        supersedes=supersedes,
        code=dict(path=str(Path(__file__).relative_to(ROOT)), sha256=sha(__file__), argv=sys.argv,
                  python=platform.python_version(), numpy=np.__version__),
        output_sha256=outputs,
        cf3_member_definition=cf3_definition,
        review_summary=review_summary(scoring, zp, cf3_definition),
        donor_commit=DONOR_COMMIT,
        input_sha256={k: sha(p) for k, p in inputs.items()}, input_paths={k: str(p) for k, p in inputs.items()},
        nn_field_sha256=field_sha, coras_runs=coras_inputs,
        cf3_source=dict(used="CF3 group-member and group catalogues distributed in the CORAS donor (17,647 galaxies, 11,500 "
                             "groups incl. singletons; columns pgc, glat, glon, czHelio, mu, muError, nest/group).",
                        cf3_table3_present=cf3_table3_present, missing_for_cf3_internal_method_attribution=None if cf3_table3_present else CF3_TABLE3_EXPECTED,
                        method_attribution_proxy="CF4 table2 per-method distance moduli of the same PGC",
                        member_group_mapping=cf3["mapping_check"]),
        coras_constants=const, coras_2mrs_input=twomrs_input, cf3_calibration_window=window_summary,
        sixdf=sixdf_counts, cf4_galaxies=gal_counts, cf4_r98_groups=groups, zero_points=zp,
        scoring=scoring,
        scoring_definitions=dict(
            test_only="R105 PGC/PGC1 folds; training rows, selection probit and component weights unchanged; "
                      "held-out sums restricted to rows not in the exclusion set (selected and unselected indicator terms)",
            drop="exclusion rows removed from train and test; probit and weights refit; R105 fold labels otherwise unchanged",
            drop_recentered="as drop, plus a mark zero point (inverse-variance mean delta_d of selected training rows) removed "
                            "from marks and probit covariate before fitting: a sensitivity beyond the R105 model set",
            drop_recentered_czbin=f"as drop_recentered with the zero point computed per {CZ_RECENTER_BIN:g} km/s cz_gal bin from "
                                  f"the selected training rows of that bin (bins with < {RECENTER_MIN_ROWS} such rows use the "
                                  "single constant); the probit (intercept + linear cz) does not absorb a per-bin shift "
                                  "exactly. Comparable statistic for apparent-magnitude-defined sets (review CF3-1)",
            drop_recentered_czbin_eps_strata="as drop_recentered_czbin with controls also stratified on the epsilon_d quintile "
                                             "inside each 2000 km/s cz bin (independent random stream)",
            controls="random keep-sets with identical counts per (cz_gal 500 km/s bin, R105 inclusion) stratum",
            control_fractions="fraction_control_le_observed = k_le/R; p_le_plus_one = (k_le+1)/(R+1); likewise ge; "
                              "resolution_1_over_R_plus_1; null when the block is degenerate (no selected kept row)",
            mark_zero_point_confound="inverse-variance mean raw delta_d of the selected kept rows vs the same control "
                                     "keep-sets, overall and per 2000 km/s cz bin, plus the mean epsilon_d",
            score="log predictive of held-out marks/indicators under equal prior on each declared component subset, minus 'zero'"),
        seeds=dict(seed=args.seed, test_only_replicates=args.replicates, drop_replicates=args.drop_replicates,
                   streams=dict(test_only="[seed, 0|1] per key", drop_cz_x_inclusion="[seed, 2] (shared by drop, "
                                "drop_recentered and drop_recentered_czbin: paired masks)", drop_eps_strata="[seed, 3]")),
        wall_seconds=time.time() - t0, peak_rss_kB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        peak_rss_children_kB=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    write(out / "CF3_OVERLAP.json", json.dumps(payload, indent=2, allow_nan=False, default=_json) + "\n")
    return payload


def _json(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(type(o))


def write(path, text):
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--coras", nargs="*", default=DEFAULT_CORAS,
                   help="CORAS draw directory=reference score JSON (fold replay); repeatable")
    p.add_argument("--replicates", type=int, default=2000)
    p.add_argument("--drop-replicates", type=int, default=64)
    p.add_argument("--drop-sets", nargs="*", default=["2MRS_coras_input", "complement_keep_only_2MRS_coras_input",
                                                      "CF3_calibration_window", "union_2MRS_coras_or_CF3_window"])
    p.add_argument("--recenter-sets", nargs="*", default=["none", "2MRS_coras_input", "complement_keep_only_2MRS_coras_input",
                                                          "CF3_calibration_window", "union_2MRS_coras_or_CF3_window"])
    p.add_argument("--czbin-sets", nargs="*", default=["none", "2MRS_coras_input", "complement_keep_only_2MRS_coras_input",
                                                       "union_2MRS_coras_or_CF3_window"],
                   help="exclusion sets for drop_recentered_czbin (cz x inclusion controls)")
    p.add_argument("--czbin-eps-sets", nargs="*", default=["2MRS_coras_input", "complement_keep_only_2MRS_coras_input",
                                                           "union_2MRS_coras_or_CF3_window"],
                   help="exclusion sets for drop_recentered_czbin_eps_strata (cz x inclusion x epsilon_d controls)")
    p.add_argument("--jobs", type=int, default=1, help="fork worker processes for the scoring blocks (results are "
                                                       "independent of the worker count)")
    p.add_argument("--seed", type=int, default=20261124)
    args = p.parse_args(argv)
    res = build(args)
    print(json.dumps(dict(output=str(args.output_dir / "CF3_OVERLAP.json"), wall_seconds=res["wall_seconds"],
                          peak_rss_kB=res["peak_rss_kB"]), indent=1))


if __name__ == "__main__":
    main()
