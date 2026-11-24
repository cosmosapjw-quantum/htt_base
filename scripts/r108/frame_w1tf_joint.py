"""R108 A8 (H05): CF4 W1 Tully-Fisher objects (Kourkchi+2020) - frame recovery and joint bulk + expansion-dipole fit.

Purpose
    The two literature W1 analyses (Boubel+2025, Stiskalek+2026; R105 CF4_LITERATURE_H05.md) use the CF4
    W1 Tully-Fisher galaxies. This script fetches that release with astroquery (VizieR J/ApJ/902/145
    tables 1 and 4, CfA mirror), records its frames in the R108 registry style (heliocentric HRV versus
    Vcmb and Vls; recovered frame velocities compared with the CF3/CF4 registry entries), and repeats the
    frame_cf4_joint.py window fit on the W1 distance moduli DM-W1: free window monopoles and STF
    quadrupoles, coherent bulk B, expansion dipole h, both; projections of h on the literature axes;
    leave-one-window-out. Same objects (after the cuts below), different estimator: no TF-relation
    refit, no selection function, no reconstructed velocity field. CONDITIONAL on the working covariance.

Inputs
    remote astroquery.vizier J/ApJ/902/145/table1 and /table4 (all rows), saved under
           ~/Downloads/htt_r108/frame/vizier_J_ApJ_902_145_table{1,4}/ with receipts in RECEIPTS.jsonl
    R108 FRAME/CATALOGUE_FRAME_REGISTRY.json, R105 CF4_H05_AXES.json,
    docs/.../H03_20261016/src/h03_tomography.py (window and fit operators)

Cuts (fixed before the fit)
    DM-W1 present, 3000 < Vcmb < 0.1 c (Boubel+2025 Sect. 2 CMB-frame cz > 3000 km/s lower cut),
    windows of H03 (z = 0.025/0.040/0.060/0.080, sigma_z 0.012) kept when the H03 design gate passes.

Units
    km/s; y = ln(f Vcmb / 74.6) - (ln10/5)(DM-W1 - 25) natural log; h dimensionless.

Usage
    PYTHONPATH=.:htt:htt/src .venv/bin/python -m scripts.r108.frame_w1tf_joint [--replay-receipts] \
        --output docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/FRAME/W1TF_BULK_HDIPOLE_JOINT.json
    Deterministic.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys
import time
import warnings
from pathlib import Path

import numpy as np

from obsstat.catalogue_frame_registry import C_KM_S, FrameRegistry
from scripts.r108.common import OUT_DIR, REPO, git_state, sha256_file, write_json
from scripts.r108.frame_cf4_joint import (H05_AXES, MAG, bulk_rows, f_curv, gls, hdipole_rows, icrs_to_gal_matrix,
                                          vector_summary)
from scripts.r108.frame_registry_build import Receipts, ReceiptReplay, best_fit, gal_n, vizier_votable

HREF = 74.6
REGISTRY_JSON = OUT_DIR / "FRAME/CATALOGUE_FRAME_REGISTRY.json"
OUTFILE = OUT_DIR / "FRAME/W1TF_BULK_HDIPOLE_JOINT.json"
CODE = ("scripts/r108/frame_w1tf_joint.py", "scripts/r108/frame_cf4_joint.py", "scripts/r108/frame_registry_build.py",
        "scripts/r108/common.py", "htt/obsstat/catalogue_frame_registry.py")


def _table(meta: dict):
    from astropy.io.votable import parse
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return parse(io.BytesIO(meta["votable_bytes"])).get_first_table().to_table()


def _col(t, name):
    c = t[name]
    return np.ma.filled(np.ma.asarray(c, dtype=float), np.nan) if c.dtype.kind in "fiu" else c


def run(downloads: Path, output: Path, replay: bool = False) -> dict:
    t0 = time.perf_counter()
    from scripts.r95 import sq_cf4_synthesis as r95
    H = r95._load_h03()
    rc = Receipts(downloads)
    if replay:  # re-parse the saved fetch results named by RECEIPTS.jsonl (SHA-256 verified; no network)
        rp = ReceiptReplay(rc.path)
        m1 = rp.vizier("J/ApJ/902/145/table1", columns=("PGC", "HRV", "QWflag", "_RA", "_DE"), row_limit=-1)
        m4 = rp.vizier("J/ApJ/902/145/table4", columns=("**",), row_limit=-1)
    else:
        m1 = vizier_votable(rc, downloads, "J/ApJ/902/145/table1", columns=("PGC", "HRV", "QWflag", "_RA", "_DE"), row_limit=-1)
        m4 = vizier_votable(rc, downloads, "J/ApJ/902/145/table4", columns=("**",), row_limit=-1)
    mode = ("replayed from RECEIPTS.jsonl (saved bytes, SHA-256 verified; no network)" if replay
            else "fetched (astroquery.vizier, CfA mirror)")
    if not (m1.get("ok") and m4.get("ok")):
        payload = {"schema": "htt.r108.frame.w1tf_joint/1", "status": "BLOCKED", "label": "BLOCKED",
                   "errors": {"table1": m1.get("errors"), "table4": m4.get("errors")}, "git": git_state(),
                   "command": " ".join(sys.argv), "code_sha256": {c: sha256_file(REPO / c) for c in CODE},
                   "remote_mode": mode, "receipts": str(rc.path),
                   "missing_input": "J/ApJ/902/145 table1 and table4 rows (CfA VizieR mirror Postgres connect error)"}
        write_json(output, payload)
        return payload
    t1, t4 = _table(m1), _table(m4)
    pgc1 = np.asarray(t1["PGC"], int); pgc4 = np.asarray(t4["PGC"], int)
    common, i1, i4 = np.intersect1d(pgc1, pgc4, return_indices=True)
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    ra, de = t1["_RA"][i1], t1["_DE"][i1]
    if np.asarray(ra).dtype.kind in "fiu":
        sc = SkyCoord(ra=np.asarray(ra, float) * u.deg, dec=np.asarray(de, float) * u.deg, frame="icrs")
    else:
        sc = SkyCoord([f"{a} {b}" for a, b in zip(ra, de)], unit=(u.hourangle, u.deg), frame="icrs")
    n_icrs = sc.cartesian.xyz.value.T
    g = sc.galactic
    n_gal = gal_n(g.l.deg, g.b.deg)
    hrv = _col(t1, "HRV")[i1]; vcmb = _col(t4, "Vcmb")[i4]; vls = _col(t4, "Vls")[i4]
    fcol = _col(t4, "f")[i4]
    dm = _col(t4, "DM-W1")[i4]; edm = _col(t4, "e_DM-W1")[i4]

    # ---- frames of this release ----
    ok = np.isfinite(hrv) & np.isfinite(vcmb) & np.isfinite(vls)
    rec = {"helio_to_cmb": best_fit(hrv[ok], vcmb[ok], n_gal[ok]),
           "helio_to_localsheet": best_fit(hrv[ok], vls[ok], n_gal[ok])}
    reg = FrameRegistry.from_json(REGISTRY_JSON)
    comp = {}
    for k, key in (("helio_to_cmb", "cf4_t4_helio_to_cmb"), ("helio_to_localsheet", "cf4_t4_helio_to_localsheet")):
        f = rec[k]["fits"][rec[k]["selected_formula"]]
        d = (np.asarray(f["beta_galactic"]) - reg.beta(key)) * C_KM_S
        comp[k] = {"registry_key": key, "minus_registry_kms": d.tolist(), "norm_kms": float(np.linalg.norm(d)),
                   "residual_rms_kms": f["residual_rms_kms"], "n_clipped": f["n_clipped"], "n_rows": f["n_rows"]}
    zc = vcmb / C_KM_S
    f_resid = fcol - f_curv(zc)

    # ---- W1 sample and window fit ----
    sel = np.isfinite(dm) & np.isfinite(edm) & (edm > 0) & np.isfinite(vcmb) & (vcmb > 3000.0) & (vcmb < 0.1 * C_KM_S)
    z = zc[sel]; n = n_icrs[sel]
    fv = f_curv(z) * vcmb[sel]
    y = np.log(fv / HREF) - MAG * (dm[sel] - 25.0)
    sig = np.hypot(MAG * edm[sel], 250.0 * (1.0 + fv / C_KM_S) / fv)
    X = H.velocity_design(np.ones(len(z)), n)
    fits, used = [], []
    window_log = {}
    for c in H.CENTERS:
        try:
            fobj = H.fit(X, y, H.window(z, sig, c), influence=True)
            fits.append(fobj); used.append(c)
            window_log[str(c)] = {"used": True, "cond": fobj["cond"], "weighted_n_eff": fobj["weighted_n_eff"]}
        except (ValueError, ArithmeticError) as exc:
            window_log[str(c)] = {"used": False, "reason": str(exc)}
    A = np.vstack([f["A"] for f in fits])
    theta = A @ y
    C, _ = H.joint_covariance(A, sig)
    nw = len(used)
    P = np.zeros((9 * nw, 6 * nw))
    for w in range(nw):
        for j, s in enumerate([0, 4, 5, 6, 7, 8]):
            P[9 * w + s, 6 * w + j] = 1.0
    JB, JH = A @ bulk_rows(z, n), A @ hdipole_rows(z, n)
    Mg = icrs_to_gal_matrix()
    axes = json.loads(H05_AXES.read_text())["axes"]
    designs = {"M0_none": P, "MB_bulk": np.hstack([P, JB]), "MH_expansion_dipole": np.hstack([P, JH]),
               "MBH_bulk_plus_expansion_dipole": np.hstack([P, JB, JH])}
    res = {}
    npar = P.shape[1]
    for mname, D in designs.items():
        beta, cb, chi2 = gls(theta, D, C)
        e = {"chi2": chi2, "dof": int(9 * nw - D.shape[1])}
        k = npar
        if "bulk" in mname:
            e["bulk_kms"] = vector_summary(beta[k:k + 3], cb[k:k + 3, k:k + 3], Mg); k += 3
        if "expansion" in mname:
            hs = vector_summary(beta[k:k + 3], cb[k:k + 3, k:k + 3], Mg)
            hs["projection_on_literature_axes"] = {
                ax: {"as_mag_zero_point": float(np.asarray(a["unit_icrs"]) @ beta[k:k + 3]) / MAG,
                     "as_mag_sd": float(math.sqrt(np.asarray(a["unit_icrs"]) @ cb[k:k + 3, k:k + 3] @ np.asarray(a["unit_icrs"]))) / MAG,
                     "literature_axis_galactic_lb_deg": a["galactic_lb_deg"]} for ax, a in axes.items()}
            e["expansion_dipole_h"] = hs
            if mname.startswith("MBH"):
                cbh = cb[npar:npar + 3, k:k + 3]
                e["corr_bulk_h_icrs_diag"] = (np.diag(cbh) / np.sqrt(np.diag(cb[npar:npar + 3, npar:npar + 3]) * np.diag(cb[k:k + 3, k:k + 3]))).tolist()
        res[mname] = e
    lowo = {}
    if nw > 2:
        for w in range(nw):
            keep = [i for i in range(9 * nw) if i // 9 != w]
            D = designs["MBH_bulk_plus_expansion_dipole"][keep]
            D = D[:, np.linalg.norm(D, axis=0) > 0]
            beta, cb, chi2 = gls(theta[keep], D, C[np.ix_(keep, keep)])
            k = D.shape[1] - 6
            lowo[f"drop_window_{used[w]}"] = {"bulk_kms": {q: vector_summary(beta[k:k + 3], cb[k:k + 3, k:k + 3], Mg)[q] for q in ("amplitude", "l_deg", "b_deg", "amplitude_sd_linear")},
                                              "h": {q: vector_summary(beta[k + 3:k + 6], cb[k + 3:k + 6, k + 3:k + 6], Mg)[q] for q in ("amplitude", "l_deg", "b_deg", "amplitude_sd_linear")},
                                              "chi2": chi2, "dof": int(len(keep) - D.shape[1])}
    payload = {
        "schema": "htt.r108.frame.w1tf_joint/1",
        "nodes": ["H05 (first executable step, same W1 objects)", "SQ-FRAME (release frame recovery)"],
        "label": ("CONDITIONAL: working covariance (independent DM-W1 error + 250 km/s), no TF refit, no selection function, "
                  "no reconstructed velocity field; same objects as the literature only up to the stated cuts"),
        "git": git_state(), "command": " ".join(sys.argv), "code_sha256": {c: sha256_file(REPO / c) for c in CODE},
        "remote_mode": mode,
        "inputs": {"registry": {"path": str(REGISTRY_JSON.relative_to(REPO)), "sha256": sha256_file(REGISTRY_JSON)},
                   "h05_axes": {"path": str(H05_AXES.relative_to(REPO)), "sha256": sha256_file(H05_AXES)},
                   "h03_module": {"path": str(r95.H03_PY.relative_to(REPO)), "sha256": sha256_file(r95.H03_PY)},
                   "vizier_table1": m1["receipt"], "vizier_table4": m4["receipt"]},
        "release_rows": {"table1": int(len(t1)), "table4": int(len(t4)), "joined_on_PGC": int(len(common))},
        "frames": {"position": "SIMBAD/SDSS-name positions (_RA/_DE, VizieR table1), parsed as ICRS",
                   "recovered": rec, "compared_with_registry_cf4": comp,
                   "f_column_minus_readme_note6": {"max_abs": float(np.nanmax(abs(f_resid))), "median": float(np.nanmedian(f_resid))}},
        "sample": {"n_selected": int(sel.sum()), "cuts": "DM-W1 present; 3000 < Vcmb < 0.1c", "windows": window_log},
        "results": res, "leave_one_window_out_MBH": lowo,
        "not_the_literature_estimand_because": ["TF relation (slope, zero point, scatter) not refitted jointly with the dipole",
                                                "no magnitude/linewidth selection function", "no reconstructed peculiar-velocity field (Carrick+2015 / Manticore)",
                                                "paper-specific quality and latitude cuts not reproduced (object lists not public in the repository)"],
        "runtime_s": time.perf_counter() - t0,
    }
    write_json(output, payload)
    return payload


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--downloads", type=Path, default=Path.home() / "Downloads/htt_r108/frame")
    ap.add_argument("--output", type=Path, default=OUTFILE)
    ap.add_argument("--replay-receipts", action="store_true",
                    help="re-parse the saved fetch results named by RECEIPTS.jsonl (no network)")
    a = ap.parse_args(argv)
    p = run(a.downloads.expanduser(), a.output, replay=a.replay_receipts)
    if p.get("status") == "BLOCKED":
        print(json.dumps(p, indent=1)); return 0
    out = {"rows": p["release_rows"], "frames": p["frames"]["compared_with_registry_cf4"], "f": p["frames"]["f_column_minus_readme_note6"],
           "sample": p["sample"]}
    for m, e in p["results"].items():
        out[m] = {"chi2": e["chi2"], "dof": e["dof"]}
        for q in ("bulk_kms", "expansion_dipole_h"):
            if q in e:
                out[m][q] = {k: e[q][k] for k in ("amplitude", "l_deg", "b_deg", "amplitude_sd_linear")}
                if "projection_on_literature_axes" in e[q]:
                    out[m][q]["proj"] = e[q]["projection_on_literature_axes"]
    out["lowo"] = p["leave_one_window_out_MBH"]
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
