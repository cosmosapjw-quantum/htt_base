"""R108 gaia lane: frame-leakage controls for the R106 Gaia/Quaia VSH curvature statistic.

Purpose
  (A) ICRF3 S/X minus Gaia DR3 position offsets of the matched radio-optical AGN: weighted 16-term
      VSH fit (glide-like dipole D, orientation epsilon, E2, B2; same templates as R69/R98), globally
      and in the four R106 Quaia redshift shells for the matched sources that carry a Quaia redshift;
      the R103 curvature rows applied to the shell fits; a proper-motion-equivalent scale obtained by
      dividing the offset curvature by the EDR3 baseline (a centroid offset that builds up linearly over
      the 34-month interval), quadratic form in the R106 jk1 covariance. This is a scale, not a bound: a
      static offset produces no proper motion and a varying centroid can move without a net offset, and the
      noise of the offset curvature is kept; Part A is reported as NON_CONSTRAINING whenever its Q exceeds the
      observed R106 spin6 Q. Only Part B constrains a (G, BP-RP)-dependent frame.
  (B) Gaia-CRF3 AGN proper motions: 16-term VSH of the R106-quality CRF3 complement (CRF3 sources not
      in the Quaia joins, G inside the Quaia range; scripts/r106 complement_sample), globally and in
      the R106 patch_gmag_colour strata (G quartiles x BP-RP quartiles of Quaia). The frame measured in
      each (G, BP-RP) cell is injected into every qualified Quaia source of that cell and pushed
      through the identical R106 estimator; constant frames are annihilated exactly, so only the
      cell-to-cell (magnitude/colour) frame variation leaks. The leak is reported as curvature vector,
      its quadratic forms in the observed R106 jk1 covariance, and the change of the observed R106
      statistics when the leak is added to the data. A bound propagates the cell-fit covariance
      (Gaussian draws of the cell frames, seed fixed). The same cell fit on Quaia itself (redshift
      ignored) is reported as an in-sample degeneracy diagnostic.
  (C) Exact-annihilation check: the global CRF3 frame injected into Quaia changes the curvature by
      round-off only.
Inputs (SHA-256 checked or recorded)
  ICRF3 S/X VizieR table10 VOTable (D08 receipt), Gaia DR3 astrometry of the gaia_crf3_xm.icrf3sx
  sources (D08G receipt: ra, dec, ra_error, dec_error, ra_dec_corr), optionally the D10 agn_cross_id x
  gaia_source FITS (consistency check against the pinned CRF3 FITS), the R106 pinned Quaia join / CRF3
  FITS / R98 cache (scripts.r108.gaia_estimator).
Units: offsets mas in, VSH coefficients microarcsec (A) or microarcsec/yr (B); curvature per unit z^2.
Usage: python -m scripts.r108.gaia_frame_leakage --icrf3 <vot> --flags <D08G fits> [--agn <fits>] --out <json>
       [--draws 1000 --seed 108201]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

from scripts.r69.gaia_e2_b2 import templates
from scripts.r103 import gaia_frame_curvature as g
from scripts.r106 import gaia_null_refit as r106
from scripts.r108 import gaia_estimator as est
from scripts.r108.common import maxrss_mb, sha256_file, write_json

EDR3_BASELINE_YR = (2457901.8652778 - 2456863.9375) / 365.25  # 2014-07-25T10:30 to 2017-05-28T08:46
MATCH_RADIUS_MAS = 100.0
CLIP_KAPPAS = (None, 5.0, 4.0)
PRIMARY_KAPPA = 5.0
SECTORS = g.SECTORS
SPIN6 = r106.STAT_SETS["spin6"]
CLAIM_CLASS = {
    "label": "CONDITIONAL",
    "A_icrf3_minus_gaia": ("NUMERICAL scale only (non-constraining when its Q exceeds the observed spin6 Q; see "
                           "A_icrf3_minus_gaia.constraint)"),
    "B_crf3_agn_pm_frames": ("CONDITIONAL on a Gaia frame systematic that depends on G and BP-RP only, measured on the "
                             "disjoint R106-quality CRF3 complement in the 16 R106 (G, BP-RP) quartile cells and transferred to "
                             "Quaia sources of the same cell; frame variation inside a cell, position dependence beyond 16 VSH "
                             "terms and redshift dependence at fixed (G, BP-RP) are not covered; Gaussian cell-fit draws"),
    "C_constant_frame_annihilation": "NUMERICAL (round-off check of the estimator)",
    "not_claimed": "no calibrated p, no physical Pi/G_F, no Bianchi family identification, no physical attribution"}


def sexa_to_deg(ra_str, dec_str):
    from astropy.coordinates import Angle

    ra = Angle(np.char.strip(np.asarray(ra_str, dtype=str)), unit="hourangle").deg
    dec = Angle(np.char.strip(np.asarray(dec_str, dtype=str)), unit="deg").deg
    return np.asarray(ra, float), np.asarray(dec, float)


def vsh_fit(ra, dec, y, e1, e2, rho, kappa=None, max_iter=20):
    """Weighted 16-term VSH fit of a 2-vector field (any unit u); returns coefficients in 1000*u.

    With kappa, sources with normalized residual X = sqrt(r^T C^-1 r) > kappa are removed iteratively."""
    X, Y = r106.whiten(ra, dec, y, e1, e2, rho)
    keep = np.ones(len(ra), bool)
    for _ in range(max_iter):
        F = np.einsum("nki,nkj->ij", X[keep], X[keep])
        s = np.einsum("nki,nk->i", X[keep], Y[keep])
        a = np.linalg.solve(F, s)
        r = Y - np.einsum("nki,i->nk", X, a)
        xnorm = np.sqrt((r ** 2).sum(axis=1))
        if kappa is None:
            break
        new = xnorm <= kappa
        if np.array_equal(new, keep):
            break
        keep = new
    cov = np.linalg.inv(F)
    chi2 = float((r[keep] ** 2).sum())
    return {"coef": a * 1000.0, "cov": cov * 1e6, "n_used": int(keep.sum()), "n_rejected": int((~keep).sum()),
            "chi2_per_dof": chi2 / max(1, 2 * int(keep.sum()) - 16), "keep": keep, "F": F, "s": s}


def summarize_fit(fit):
    a, c = fit["coef"], fit["cov"]
    se = np.sqrt(np.diag(c))
    out = {"n_used": fit["n_used"], "n_rejected": fit["n_rejected"], "chi2_per_dof": fit["chi2_per_dof"],
           "coef": a.tolist(), "se": se.tolist()}
    for name, sl in SECTORS.items():
        v, cc = a[sl], c[sl, sl]
        out[f"{name}_vector"] = v.tolist()
        out[f"{name}_norm"] = float(np.linalg.norm(v))
        out[f"{name}_chi2_vs_zero"] = float(v @ np.linalg.solve(cc, v))
        out[f"{name}_dof"] = int(len(v))
    return out


def icrf3_offsets(icrf3_path, flags_path, quaia, kappa_list=CLIP_KAPPAS):
    """(A) ICRF3 S/X - Gaia DR3 offsets, global and per Quaia shell."""
    from astropy.table import Table
    from scipy.spatial import cKDTree

    t = Table.read(icrf3_path)
    if len(t) != 4536:
        raise ValueError(f"ICRF3 S/X rows {len(t)} != 4536")
    ra_i, dec_i = sexa_to_deg(t["RAICRS"], t["DEICRS"])
    cosd = np.cos(np.deg2rad(dec_i))
    sig_ra_i = np.asarray(t["e_RAICRS"], float) * 15.0 * 1000.0 * cosd  # s of time -> mas on sky
    sig_de_i = np.asarray(t["e_DEICRS"], float) * 1000.0  # arcsec -> mas
    corr_i = np.asarray(t["Corr"], float)
    defining = np.asarray(t["Cat"]).astype(str) == "D"
    fl = Table.read(flags_path)
    gid = np.asarray(fl["source_id"], np.int64)
    gra = np.asarray(fl["ra"], float) if "ra" in fl.colnames else None
    if gra is None:
        raise KeyError("flags table lacks ra/dec")
    gdec = np.asarray(fl["dec"], float)

    def unit(ra, dec):
        r, d = np.deg2rad(ra), np.deg2rad(dec)
        return np.column_stack((np.cos(d) * np.cos(r), np.cos(d) * np.sin(r), np.sin(d)))

    tree = cKDTree(unit(gra, gdec))
    dist, idx = tree.query(unit(ra_i, dec_i), k=2)
    sep_mas = np.rad2deg(2 * np.arcsin(dist / 2)) * 3.6e6
    hit = sep_mas[:, 0] <= MATCH_RADIUS_MAS
    ambiguous = hit & (sep_mas[:, 1] <= MATCH_RADIUS_MAS)
    j = idx[:, 0]
    sel = hit & ~ambiguous
    flag_sx = np.asarray(fl["icrf3sx"]).astype(bool)
    census = {"icrf3_rows": int(len(t)), "defining": int(defining.sum()), "matched_within_100mas": int(hit.sum()),
              "ambiguous_second_within_100mas": int(ambiguous.sum()),
              "matched_flagged_icrf3sx_in_gaia_crf3_xm": int(flag_sx[j[sel]].sum()),
              "gaia_crf3_xm_icrf3sx_flags_total": int(flag_sx.sum())}
    jj = j[sel]
    ra_g, dec_g = gra[jj], gdec[jj]
    dra = (ra_i[sel] - ra_g)
    dra = (dra + 180.0) % 360.0 - 180.0
    off = np.column_stack((dra * np.cos(np.deg2rad(dec_g)) * 3.6e6, (dec_i[sel] - dec_g) * 3.6e6))  # mas
    sg_ra = np.asarray(fl["ra_error"], float)[jj]
    sg_de = np.asarray(fl["dec_error"], float)[jj]
    cg = np.asarray(fl["ra_dec_corr"], float)[jj]
    c00 = sig_ra_i[sel] ** 2 + sg_ra ** 2
    c11 = sig_de_i[sel] ** 2 + sg_de ** 2
    c01 = corr_i[sel] * sig_ra_i[sel] * sig_de_i[sel] + cg * sg_ra * sg_de
    e1, e2 = np.sqrt(c00), np.sqrt(c11)
    rho = c01 / (e1 * e2)
    good = np.isfinite(off).all(axis=1) & np.isfinite(e1) & np.isfinite(e2) & np.isfinite(rho) & (np.abs(rho) < .999)
    census["usable_offsets"] = int(good.sum())
    census["offset_mas_q50_q90_q99"] = np.quantile(np.hypot(*off[good].T), [.5, .9, .99]).tolist()
    ra_r, dec_r = np.deg2rad(ra_g[good]), np.deg2rad(dec_g[good])
    glob = {}
    for kap in kappa_list:
        fit = vsh_fit(ra_r, dec_r, off[good], e1[good], e2[good], rho[good], kap)
        glob["no_clip" if kap is None else f"clip_X_gt_{kap:g}"] = summarize_fit(fit)
    # Shells: matched sources that are in the qualified Quaia sample.
    sid = gid[jj][good]
    order = np.argsort(quaia["source_id"])
    pos = np.clip(np.searchsorted(quaia["source_id"][order], sid), 0, len(order) - 1)
    inq = quaia["source_id"][order][pos] == sid
    shell = np.full(len(sid), -1)
    shell[inq] = quaia["shell"][order][pos[inq]]
    shells = {"matched_in_quaia_qualified": int(inq.sum()),
              "per_shell_counts": [int((shell == k).sum()) for k in range(4)]}
    return {"census": census, "global": glob, "shells": shells,
            "arrays": {"ra": ra_r, "dec": dec_r, "off": off[good], "e1": e1[good], "e2": e2[good], "rho": rho[good],
                       "shell": shell}}


def shell_curvature(arr, w, kappa, cov_jk1, label):
    """VSH per shell -> curvature rows -> PM-equivalent quadratic form in the R106 jk1 covariance."""
    coef, covs, n = [], [], []
    for k in range(4):
        m = arr["shell"] == k
        if m.sum() < 40:
            return {"status": "BLOCKED", "reason": f"shell {k} has {int(m.sum())} matched sources (< 40)"}
        fit = vsh_fit(arr["ra"][m], arr["dec"][m], arr["off"][m], arr["e1"][m], arr["e2"][m], arr["rho"][m], kappa)
        coef.append(fit["coef"])
        covs.append(fit["cov"])
        n.append(fit["n_used"])
    coef = np.array(coef)
    curv = (w @ coef).reshape(-1)  # microarcsec per z^2
    # Covariance of the curvature from independent shell fits.
    C = np.zeros((32, 32))
    for r1 in range(2):
        for r2 in range(2):
            C[r1 * 16:(r1 + 1) * 16, r2 * 16:(r2 + 1) * 16] = sum(w[r1, s] * w[r2, s] * covs[s] for s in range(4))
    pm_equiv = curv / EDR3_BASELINE_YR
    out = {"label": label, "n_used_per_shell": n, "shell_coef_microas": coef.tolist(),
           "offset_curvature_microas_per_z2": curv.tolist(),
           "offset_curvature_spin6": curv[SPIN6].tolist(),
           "offset_curvature_spin6_chi2_vs_zero_own_cov": float(curv[SPIN6] @ np.linalg.solve(C[np.ix_(SPIN6, SPIN6)], curv[SPIN6])),
           "pm_equivalent_scale_microasyr_per_z2_spin6": pm_equiv[SPIN6].tolist(),
           "pm_equivalent_spin6_Q_in_R106_jk1_cov": float(pm_equiv[SPIN6] @ np.linalg.solve(
               cov_jk1[np.ix_(SPIN6, SPIN6)], pm_equiv[SPIN6]))}
    # The offset-curvature noise is not subtracted: the PM-equivalent number is a noise-inclusive scale, not a bound.
    return out


def part_a_constraint(shell_curv, observed_q):
    """Part A is informative only if its PM-equivalent spin6 Q is below the observed R106 spin6 Q (jk1, all 48 patches)."""
    qa = {lab: v["all48"].get("pm_equivalent_spin6_Q_in_R106_jk1_cov") for lab, v in shell_curv.items()}
    known = [q for q in qa.values() if q is not None]
    status = "NON_CONSTRAINING" if known and min(known) > observed_q else ("BLOCKED" if not known else "SCALE_BELOW_OBSERVED")
    return {"status": status, "pm_equivalent_spin6_Q_by_clip": qa, "observed_R106_spin6_Q_jk1_all48": observed_q,
            "statement": ("Part A (offset curvature / EDR3 baseline) is a scale, not a bound: a static radio-optical offset "
                          "produces no proper motion, a varying centroid can produce proper motion unrelated to the net "
                          "offset, and the noise of the offset curvature is kept. " +
                          ("Its Q exceeds the observed spin6 Q for every clip, so it cannot constrain frame leakage; only "
                           "Part B constrains a G/BP-RP-dependent frame." if status == "NON_CONSTRAINING" else
                           "Even where its Q is below the observed value it is not a bound (see above)."))}


def curvature_full(f, s, w, keep):
    """Curvature of the full (no-deletion) shell fits only; equals r106.curvature (checked at run time)."""
    F = f[:, keep].sum(axis=1)
    S = s[:, keep].sum(axis=1)
    coef = np.stack([np.linalg.solve(F[k], S[k]) for k in range(len(F))]) * 1000.0
    return (w @ coef).reshape(-1)


def cell_index(G, c, g4, c4):
    return r106.quantile_bins(G, g4) * 8 + r106.quantile_bins(c, c4)


def cell_frames(ra, dec, y, e1, e2, rho, cell, cells):
    out = {}
    for cc in cells:
        m = cell == cc
        if m.sum() < 200:
            continue
        out[int(cc)] = vsh_fit(ra[m], dec[m], y[m], e1[m], e2[m], rho[m])
    return out


def run(a):
    t0 = time.monotonic()
    ctx = est.load_context(with_colour=True)
    q, w, f, s_obs = ctx["q"], ctx["w"], ctx["f"], ctx["s_obs"]
    allp = np.arange(est.NPATCH)
    keep_ex = np.setdiff1d(allp, r106.EXCLUDE)
    y48, c1_48, _, _, _ = r106.refit_parts(f, s_obs, w, allp)
    yex, c1_ex, _ = r106.refit(f, s_obs, w, keep_ex)
    covs = {"all48": c1_48, "excl_8_47": c1_ex}
    obs_vec = {"all48": y48, "excl_8_47": yex}
    inputs = dict(ctx["inputs"])
    for k, p in (("icrf3_vot", a.icrf3), ("icrf3sx_gaia_counterparts_fits", a.flags), ("agn_cross_id_fits", a.agn)):
        if p is not None:
            inputs[k] = sha256_file(p)
    res = {"schema": "htt.r108.gaia_frame_leakage/1", "units": {
        "A": "offsets mas; VSH coefficients microarcsec; curvature microarcsec per z^2; PM equivalent microarcsec/yr per z^2",
        "B": "VSH coefficients microarcsec/yr; curvature microarcsec/yr per z^2; Q dimensionless"},
        "input_sha256": inputs, "estimator_replay": ctx["replay"], "edr3_baseline_yr": EDR3_BASELINE_YR,
        "claim_class": CLAIM_CLASS, "calibrated_p": None, "physical_Pi": None, "physical_GF": None}
    # D10 versus the pinned CRF3 FITS: same rows, same proper motions.
    from astropy.table import Table

    crf3 = ctx["crf3"]
    if a.agn is None:
        res["d10_vs_pinned_crf3_fits"] = {"status": "BLOCKED", "reason": "D10 (agn_cross_id x gaia_source) not acquired: "
                                          "the anonymous ESA async limit (60 s) aborted the single job and, after bisection, "
                                          "a source_id range in a dense region; part B uses the R106-pinned CRF3 FITS "
                                          "(gaia_crf3_xm x gaia_source, 1,614,173 rows) instead"}
    else:
        res["d10_vs_pinned_crf3_fits"] = d10_consistency(Table.read(a.agn), crf3)
    res.update(run_rest(a, ctx, res, inputs, covs, obs_vec, keep_ex, allp, t0))


def d10_consistency(agn, crf3):
    o1, o2 = np.argsort(np.asarray(agn["source_id"], np.int64)), np.argsort(crf3["source_id"])
    sid1, sid2 = np.asarray(agn["source_id"], np.int64)[o1], crf3["source_id"][o2]
    same = len(sid1) == len(sid2) and np.array_equal(sid1, sid2)
    cons = {"d10_rows": int(len(sid1)), "crf3_fits_rows": int(len(sid2)), "same_source_ids": bool(same)}
    if same:
        for col in ("pmra", "pmdec", "pmra_error", "pmdec_error", "pmra_pmdec_corr", "phot_g_mean_mag", "bp_rp"):
            x1 = np.asarray(agn[col], float)[o1]
            x2 = np.asarray(crf3[col], float)[o2]
            both = np.isfinite(x1) & np.isfinite(x2)
            cons[f"{col}_max_abs_diff"] = float(np.max(np.abs(x1[both] - x2[both]))) if both.any() else None
            cons[f"{col}_nan_pattern_equal"] = bool(np.array_equal(np.isfinite(x1), np.isfinite(x2)))
    cats, ncat = np.unique(np.asarray(agn["catalogue_name"]).astype(str), return_counts=True)
    cons["agn_cross_id_catalogue_name_counts"] = {str(k): int(v) for k, v in zip(cats, ncat)}
    return cons


def run_rest(a, ctx, res, inputs, covs, obs_vec, keep_ex, allp, t0):
    q, w, f, s_obs = ctx["q"], ctx["w"], ctx["f"], ctx["s_obs"]
    crf3 = ctx["crf3"]
    c1_48 = covs["all48"]
    # (A) ICRF3 offsets.
    A = icrf3_offsets(a.icrf3, a.flags, q)
    arr = A.pop("arrays")
    A["shell_curvature"] = {}
    for kap in (PRIMARY_KAPPA, None):
        lab = "no_clip" if kap is None else f"clip_X_gt_{kap:g}"
        A["shell_curvature"][lab] = {cfg: shell_curvature(arr, w, kap, covs[cfg], lab) for cfg in ("all48",)}
    A["observed_R106_spin6_curvature_microasyr_per_z2"] = obs_vec["all48"][SPIN6].tolist()
    obs_q = float(r106.qforms(obs_vec["all48"], c1_48)["spin6"])
    A["constraint"] = part_a_constraint(A["shell_curvature"], obs_q)
    A["scope"] = ("Static radio-optical offsets do not move; the PM-equivalent numbers assume the whole shell-wise offset "
                  "pattern built up linearly over the EDR3 baseline. They are a scale for a centroid-drift leak, not a "
                  "bound (see constraint). ICRF3 "
                  "positions are at epoch 2015.0 and Gaia DR3 at 2016.0; quasar PMs are not propagated (the 1 yr "
                  "difference times the ~5 microarcsec/yr secular-aberration glide is below the offset noise).")
    res["A_icrf3_minus_gaia"] = A
    # (B) CRF3 complement frames by (G, BP-RP) cell.
    strata, sinfo, (g4, c4) = r106.build_strata(q, crf3)
    comp, census = r106.complement_sample(q, crf3, g4, c4, match_g=True)
    order = np.argsort(crf3["source_id"])
    Gc, _ = r106.lookup(crf3["source_id"][order], crf3["phot_g_mean_mag"][order], comp["source_id"])
    Cc, _ = r106.lookup(crf3["source_id"][order], crf3["bp_rp"][order], comp["source_id"])
    cell_c = cell_index(Gc, Cc, g4, c4)
    cell_q = cell_index(q["G"], ctx["bp_rp"], g4, c4)
    cells = np.unique(cell_q)
    glob_c = vsh_fit(comp["ra"], comp["dec"], comp["y"], comp["e1"], comp["e2"], comp["rho"])
    glob_q = vsh_fit(q["ra"], q["dec"], q["y"], q["e1"], q["e2"], q["rho"])
    B = {"complement_census": census, "strata_edges": {"G4": g4.tolist(), "bp_rp4": c4.tolist()},
         "global_frame_crf3_complement": summarize_fit(glob_c), "global_frame_quaia_qualified": summarize_fit(glob_q)}
    # (C) exact annihilation of a constant frame.
    _, Bq = templates(q["ra"], q["dec"])
    const_field = np.einsum("nkj,j->nk", Bq, glob_c["coef"]) / 1000.0
    s_c = est.rhs(ctx["X"], est.whiten_field(ctx["L"], const_field), ctx["key"])
    curv_c = r106.curvature(f, s_c, w, allp)
    res["C_constant_frame_annihilation"] = {"injected": "global CRF3-complement 16-term frame (microarcsec/yr)",
                                            "curvature_max_abs_microasyr_per_z2": float(np.max(np.abs(curv_c)))}
    del const_field
    fr_c = cell_frames(comp["ra"], comp["dec"], comp["y"], comp["e1"], comp["e2"], comp["rho"], cell_c, cells)
    fr_q = cell_frames(q["ra"], q["dec"], q["y"], q["e1"], q["e2"], q["rho"], cell_q, cells)
    # Per-cell Quaia Fisher blocks per shell x patch (the injected rhs of a cell frame a is F_cell a).
    Fcell = {}
    for cc in cells:
        m = cell_q == cc
        Fcell[int(cc)], _ = r106.group_normal(ctx["X"][m], np.zeros((int(m.sum()), 2)), q["shell"][m], q["patch"][m])
    covered = [int(c) for c in cells if int(c) in fr_c]
    uncovered = [int(c) for c in cells if int(c) not in fr_c]
    B["cells"] = {"quaia_cells": int(len(cells)), "covered_by_complement": covered, "uncovered": uncovered,
                  "quaia_sources_in_uncovered_cells": int(np.isin(cell_q, uncovered).sum()),
                  "complement_sources_per_cell": {int(c): int((cell_c == c).sum()) for c in cells},
                  "complement_cell_frames": {int(c): summarize_fit(fr_c[c]) for c in covered}}

    def leak_from(frames, cellset):
        s_inj = np.zeros_like(s_obs)
        for cc in cellset:
            s_inj += np.einsum("spij,j->spi", Fcell[cc], frames[cc]) / 1000.0
        return s_inj

    def leak_report(s_inj, label):
        rep = {"label": label}
        for cfg, keep in (("all48", allp), ("excl_8_47", keep_ex)):
            v = r106.curvature(f, s_inj, w, keep)
            c1 = covs[cfg]
            qf = r106.qforms(v, c1)
            both = est.stats(f, s_obs + s_inj, w) if cfg == "all48" else None
            rep[cfg] = {"leak_curvature_spin6": v[SPIN6].tolist(),
                        "leak_Q_in_observed_jk1_cov": {k: qf[k] for k in ("spin6", "magnetic16", "joint32", "glide6")},
                        "leak_spin6_norm_over_observed_spin6_norm": float(np.linalg.norm(v[SPIN6]) / np.linalg.norm(obs_vec[cfg][SPIN6]))}
            if both is not None:
                rep[cfg]["observed_plus_leak_recomputed_jk1"] = {k: both["all48"]["jk1"][k] for k in ("spin6", "magnetic16", "joint32")}
                rep[cfg]["observed_jk1"] = {k: r106.qforms(obs_vec["all48"], c1_48)[k] for k in ("spin6", "magnetic16", "joint32")}
        return rep

    s_chk = leak_from({c: fr_c[c]["coef"] for c in covered}, covered)
    chk = float(np.max(np.abs(curvature_full(f, s_chk, w, allp) - r106.curvature(f, s_chk, w, allp))))
    if chk > 1e-9 * max(1.0, float(np.max(np.abs(r106.curvature(f, s_chk, w, allp))))):
        raise ArithmeticError(f"fast curvature differs from r106.curvature by {chk}")
    B["fast_curvature_check_max_abs"] = chk
    point = {c: fr_c[c]["coef"] for c in covered}
    B["leak_complement_cell_frames_point"] = leak_report(leak_from(point, covered), "complement (G,BP-RP) cell frames, point estimate")
    B["leak_quaia_in_sample_cell_frames_diagnostic"] = leak_report(
        leak_from({c: fr_q[c]["coef"] for c in fr_q}, list(fr_q)), "Quaia (G,BP-RP) cell frames ignoring z (in-sample degeneracy diagnostic)")
    # Bound: Gaussian draws of the complement cell frames.
    rng = np.random.default_rng(a.seed)
    chol = {c: np.linalg.cholesky(fr_c[c]["cov"]) for c in covered}
    qd = {"all48": [], "excl_8_47": []}
    qd0 = {"all48": [], "excl_8_47": []}
    for _ in range(a.draws):
        dr = {c: fr_c[c]["coef"] + chol[c] @ rng.standard_normal(16) for c in covered}
        d0 = {c: chol[c] @ rng.standard_normal(16) for c in covered}
        for cfg, keep in (("all48", allp), ("excl_8_47", keep_ex)):
            for frames, store in ((dr, qd), (d0, qd0)):
                v = curvature_full(f, leak_from(frames, covered), w, keep)
                store[cfg].append(float(v[SPIN6] @ np.linalg.solve(covs[cfg][np.ix_(SPIN6, SPIN6)], v[SPIN6])))
    obs_spin6 = {cfg: float(obs_vec[cfg][SPIN6] @ np.linalg.solve(covs[cfg][np.ix_(SPIN6, SPIN6)], obs_vec[cfg][SPIN6]))
                 for cfg in covs}
    B["bound_draws"] = {"draws": a.draws, "seed": a.seed,
                        "spin6_leak_Q_in_observed_jk1": {cfg: {"q50": float(np.quantile(qd[cfg], .5)),
                                                               "q95": float(np.quantile(qd[cfg], .95)),
                                                               "q99": float(np.quantile(qd[cfg], .99)),
                                                               "max": float(np.max(qd[cfg]))} for cfg in qd},
                        "spin6_leak_Q_noise_only_cell_frames": {cfg: {"q50": float(np.quantile(qd0[cfg], .5)),
                                                                      "q95": float(np.quantile(qd0[cfg], .95))} for cfg in qd0},
                        "observed_spin6_Q_jk1": obs_spin6,
                        "scope": "Cell frames drawn from N(complement fit, complement fit covariance); the noise-only row draws "
                                 "N(0, same covariance) and shows how much of the leak is fit noise."}
    res["B_crf3_agn_pm_frames"] = B
    res["constraint_summary"] = {
        "A_icrf3_minus_gaia": res["A_icrf3_minus_gaia"]["constraint"]["status"],
        "B_crf3_agn_pm_frames": "CONDITIONAL: spin6 leak Q from Gaussian cell-frame draws (bound_draws) versus observed_spin6_Q_jk1",
        "constraining_part": ("B only" if res["A_icrf3_minus_gaia"]["constraint"]["status"] == "NON_CONSTRAINING" else "A (scale) and B")}
    res["assumptions"] = [
        "(A) ICRF3 S/X matched to Gaia DR3 within 100 mas, unique nearest neighbour; combined covariance ICRF3 + Gaia; "
        "R106 shells from Quaia redshifts of the matched sources; PM equivalent = offset curvature / EDR3 baseline (a "
        "scale, not a bound; Part A is non-constraining when its Q exceeds the observed Q).",
        "(B) a Gaia frame systematic that depends on G and BP-RP only, measured on the disjoint CRF3 complement in the 16 "
        "R106 (G quartile x BP-RP quartile) cells, transfers to Quaia sources of the same cell; frame variation inside a "
        "cell, position dependence beyond the 16 VSH terms and redshift dependence at fixed (G, BP-RP) are not covered."]
    res["runtime_s"] = time.monotonic() - t0
    res["maxrss_mb"] = maxrss_mb()
    res["provenance"] = est.provenance()
    write_json(a.out, res)
    print(json.dumps({"out": str(a.out), "runtime_s": res["runtime_s"]}))
    return {}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--icrf3", type=Path, required=True)
    ap.add_argument("--flags", type=Path, required=True)
    ap.add_argument("--agn", type=Path, default=None, help="D10 FITS (optional; D10 is BLOCKED this round)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=108201)
    a = ap.parse_args(argv)
    for k in ("icrf3", "flags", "agn"):
        if getattr(a, k) is not None:
            setattr(a, k, getattr(a, k).expanduser())
    run(a)


if __name__ == "__main__":
    main()
