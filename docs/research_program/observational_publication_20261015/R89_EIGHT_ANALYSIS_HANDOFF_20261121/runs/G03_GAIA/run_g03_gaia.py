"""R89 G03_GAIA bounded source diagnostic for SQ-GAIA / K01 / K02 (K03/K04-K06 blocked).

Reuses:
- htt.obsstat.pre_dag_fast.accumulate_gaia (certified C++17/OpenMP 16D VSH normal eqs)
- htt.obsstat.phy_fast.gaia_eb_mask_alias (E2-B2 canonical correlation under mask)
- htt.obsstat.p5p6_fast.inspect_k03_cross_moments & observer_radial_kinematics
- scripts.r69.gaia_e2_b2 (prepare, templates, fit_case)

Write scope: create-only under R89/.../runs/G03_GAIA/.
No physical normal-frame shear/omega/beta or K03-K06 inference is claimed.
"""
from __future__ import annotations

import hashlib
import json
import platform
import resource
import sys
import time
from pathlib import Path

import healpy as hp
import numpy as np
from astropy.io import fits
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from htt.obsstat import p5p6_fast, phy_fast, pre_dag_fast
from scripts.r69.gaia_e2_b2 import fit_case, prepare, templates

GAIA_FULL = Path("/mnt/extdrive/workdir/raw/observational_bundles/Gaia_CRF3_astrometry/gaia_crf3_astrometry_full.fits")
GAIA_AIP = Path("/mnt/extdrive/workdir/raw/observational_bundles/Gaia_CRF3_astrometry/gaia_crf3_astrometry_aip.fits")
K03_PATH = Path("/mnt/extdrive/workdir/htt_open_data/k03_pm_20261023/cross_moments.npz")
R69_SAVED = ROOT / "docs/research_program/observational_publication_20261015/R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118/RESULTS/GAIA_E1B1E2B2.json"

PIN_FULL = "e69cfff82f762c00d1d6a259c6d003fd20f805f3b1fcd4acc81d847c485120c0"
PIN_AIP = "1a68f26a43b39b601e6b1e71f7ed7c2a19718d6537114b542070fdffdafff129"
PIN_K03 = "70fc2fee88803a7211c1c157ff87b4adb05b0807a00c03dc38d51f31b3842662"

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "RESULT.json"
CHUNK = 65536
THREADS = 8


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _rel(a, b) -> float:
    x = np.asarray(a, dtype=float)
    y = np.asarray(b, dtype=float)
    return float(np.linalg.norm(x - y) / max(np.linalg.norm(y), 1e-200))


def _empty_acc() -> dict:
    return {"F": np.zeros((16, 16)), "score": np.zeros(16), "chisq": 0.0, "N": 0}


def _add_acc(dst: dict, F: np.ndarray, score: np.ndarray, chisq: float, n: int) -> None:
    dst["F"] += F
    dst["score"] += score
    dst["chisq"] += chisq
    dst["N"] += n


def _summarize_fit(acc: dict) -> dict:
    fit = fit_case(acc)
    cov_micro2 = np.asarray(fit["formal_cov_microasyr2"], dtype=float)
    alias = phy_fast.gaia_eb_mask_alias(cov_micro2)
    return {
        "n_sources": fit["n_sources"],
        "rank": fit["rank"],
        "F_condition": fit["F_condition"],
        "coefs_microasyr": fit["coefs_microasyr"],
        "formal_errors_microasyr": fit["formal_errors_microasyr"],
        "groups_amplitude_microasyr": fit["groups_amplitude_microasyr"],
        "E2_shape_chi": fit["E2_shape_chi"],
        "chi2_per_dof_working": fit["chi2_per_dof_working"],
        "nominal_within_fixed_Gaussian": fit["nominal_within_fixed_Gaussian"],
        "E2_B2_mask_alias_canonical": alias["canonical"].tolist(),
        "E2_B2_mask_alias_maxcanonical": alias["maxcanonical"],
    }


def _disjoint_contrast(acc_a: dict, acc_b: dict, label_a: str, label_b: str) -> dict:
    """Formal working-noise Wald contrast between two disjoint Gaia source subsets."""
    fa = fit_case(acc_a)
    fb = fit_case(acc_b)
    ba = np.asarray(fa["coefs_microasyr"], dtype=float)
    bb = np.asarray(fb["coefs_microasyr"], dtype=float)
    ca = np.asarray(fa["formal_cov_microasyr2"], dtype=float)
    cb = np.asarray(fb["formal_cov_microasyr2"], dtype=float)
    delta = ba - bb
    cdiff = ca + cb
    slices = {"all_16D": slice(0, 16), "E1_3D": slice(0, 3), "B1_3D": slice(3, 6), "E2_5D": slice(6, 11), "B2_5D": slice(11, 16)}
    stats_by_group = {}
    for name, sl in slices.items():
        d_sub = delta[sl]
        c_sub = cdiff[sl, sl]
        w = float(d_sub @ np.linalg.solve(c_sub, d_sub))
        dof = len(d_sub)
        stats_by_group[name] = {
            "delta_norm_microasyr": float(np.linalg.norm(d_sub)),
            "formal_wald_chi2": w,
            "dof": dof,
            "formal_p_not_calibrated": float(chi2.sf(w, dof)),
        }
    return {
        "subset_a": label_a,
        "subset_b": label_b,
        "n_a": fa["n_sources"],
        "n_b": fb["n_sources"],
        "delta_coefs_a_minus_b_microasyr": delta.tolist(),
        "formal_contrasts": stats_by_group,
        "scope_note": "Working formal per-source astrometric error only; scanning-law and AGN systematics uncalibrated",
    }


def _heldout_eval(acc_train: dict, acc_test: dict, label: str) -> dict:
    """Exact out-of-sample weighted proper-motion chi2/dof using quadratic sufficient stats."""
    beta_tr = np.linalg.solve(acc_train["F"], acc_train["score"])
    beta_te = np.linalg.solve(acc_test["F"], acc_test["score"])
    cov_tr = np.linalg.inv(acc_train["F"])
    cov_te = np.linalg.inv(acc_test["F"])

    chi2_zero = float(acc_test["chisq"])
    chi2_tr_on_te = float(
        acc_test["chisq"] - 2.0 * float(beta_tr @ acc_test["score"]) + float(beta_tr @ acc_test["F"] @ beta_tr)
    )
    chi2_te_insample = float(acc_test["chisq"] - float(beta_te @ acc_test["score"]))
    dof_total = 2 * acc_test["N"]
    dof_insample = 2 * acc_test["N"] - 16
    delta_micro = (beta_tr - beta_te) * 1000.0
    cdiff_micro2 = (cov_tr + cov_te) * 1e6
    wald_16 = float(delta_micro @ np.linalg.solve(cdiff_micro2, delta_micro))
    return {
        "fold": label,
        "train_n": acc_train["N"],
        "test_n": acc_test["N"],
        "test_chi2_per_dof_zero": chi2_zero / dof_total,
        "test_chi2_per_dof_train_fit": chi2_tr_on_te / dof_total,
        "test_chi2_per_dof_insample_fit": chi2_te_insample / dof_insample,
        "delta_chi2_train_minus_zero_on_test": chi2_tr_on_te - chi2_zero,
        "delta_chi2_train_minus_insample_on_test": chi2_tr_on_te - chi2_te_insample,
        "train_vs_test_formal_16D_wald": wald_16,
    }


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {OUT_JSON}")

    t0 = time.perf_counter()
    sha_full = _sha256(GAIA_FULL)
    sha_aip = _sha256(GAIA_AIP)
    sha_k03 = _sha256(K03_PATH)
    if sha_full != PIN_FULL:
        raise ValueError(f"Gaia full SHA mismatch: {sha_full}")
    if sha_aip != PIN_AIP:
        raise ValueError(f"Gaia AIP SHA mismatch: {sha_aip}")
    if sha_k03 != PIN_K03:
        raise ValueError(f"K03 SHA mismatch: {sha_k03}")

    saved_r69 = json.loads(R69_SAVED.read_text(encoding="utf-8"))

    # Pass 1 on GAIA_FULL: accumulate all, quality, north, south, RA quadrants, and systematic subsets
    full_keys = (
        "all",
        "quality",
        "quality_north",
        "quality_south",
        "solved_31_5p",
        "solved_95_6p",
        "vis_lt_15",
        "vis_ge_15",
        "gmag_lt_19p5",
        "gmag_ge_19p5",
        "ra_q0_0_90",
        "ra_q1_90_180",
        "ra_q2_180_270",
        "ra_q3_270_360",
    )
    accum = {k: _empty_acc() for k in full_keys}
    nonfinite_gmag_qual = 0
    receipts = []

    with fits.open(GAIA_FULL, memmap=True) as f:
        tbl = f[1].data
        for start in range(0, len(tbl), CHUNK):
            chunk = tbl[start : start + CHUNK]
            ra, dec, y1, y2, e1, e2, rho, valid, qual = prepare(chunk)
            if not np.any(valid):
                continue
            _, B = templates(ra[valid], dec[valid])
            yy = np.column_stack([y1[valid], y2[valid]])
            e1v, e2v, rhov = e1[valid], e2[valid], rho[valid]
            qv = qual[valid]
            decv = dec[valid]
            rav_deg = np.rad2deg(ra[valid]) % 360.0
            solvedv = np.asarray(chunk["astrometric_params_solved"])[valid]
            visv = np.asarray(chunk["visibility_periods_used"])[valid]
            gmagv = np.asarray(chunk["phot_g_mean_mag"], dtype=float)[valid]
            fin_g = np.isfinite(gmagv)
            nonfinite_gmag_qual += int(np.sum(qv & (~fin_g)))

            masks = {
                "all": np.ones(int(np.sum(valid)), dtype=bool),
                "quality": qv,
                "quality_north": qv & (decv >= 0.0),
                "quality_south": qv & (decv < 0.0),
                "solved_31_5p": qv & (solvedv == 31),
                "solved_95_6p": qv & (solvedv == 95),
                "vis_lt_15": qv & (visv < 15),
                "vis_ge_15": qv & (visv >= 15),
                "gmag_lt_19p5": qv & fin_g & (gmagv < 19.5),
                "gmag_ge_19p5": qv & fin_g & (gmagv >= 19.5),
                "ra_q0_0_90": qv & (rav_deg >= 0.0) & (rav_deg < 90.0),
                "ra_q1_90_180": qv & (rav_deg >= 90.0) & (rav_deg < 180.0),
                "ra_q2_180_270": qv & (rav_deg >= 180.0) & (rav_deg < 270.0),
                "ra_q3_270_360": qv & (rav_deg >= 270.0) & (rav_deg < 360.0),
            }
            for key, m in masks.items():
                if not np.any(m):
                    continue
                Fi, sc, chi = pre_dag_fast.accumulate_gaia(
                    B[m], yy[m], e1v[m], e2v[m], rhov[m], threads=THREADS
                )
                receipts.append(pre_dag_fast.last_backend_receipt())
                _add_acc(accum[key], Fi, sc, chi, int(np.sum(m)))

    # Verify R69 exact replay parity on (all, quality, quality_north, quality_south)
    r69_parity = {}
    fits_full = {k: fit_case(v) for k, v in accum.items()}
    for key in ("all", "quality", "quality_north", "quality_south"):
        fresh = fits_full[key]
        saved = saved_r69["results"][key]
        assert fresh["n_sources"] == saved["n_sources"]
        errs = {
            "beta_coeff_relative": _rel(fresh["coefs_microasyr"], saved["coefs_microasyr"]),
            "formal_cov_relative": _rel(fresh["formal_cov_microasyr2"], saved["formal_cov_microasyr2"]),
            "chi2_per_dof_abs": abs(fresh["chi2_per_dof_working"] - saved["chi2_per_dof_working"]),
        }
        if max(errs.values()) > 2e-9:
            raise AssertionError(f"R69 parity failure on {key}: {errs}")
        r69_parity[key] = errs

    # Pass 2 on GAIA_FULL: 192-HEALPix-patch residual-score sandwich on quality subset
    cov_qual = np.linalg.inv(accum["quality"]["F"])
    beta_qual = np.asarray(fits_full["quality"]["coefs_microasyr"], dtype=float) / 1000.0
    score_patch = np.zeros((192, 16), dtype=float)
    with fits.open(GAIA_FULL, memmap=True) as f:
        tbl = f[1].data
        for start in range(0, len(tbl), CHUNK):
            chunk = tbl[start : start + CHUNK]
            ra, dec, y1, y2, e1, e2, rho, valid, qual = prepare(chunk)
            m = valid & qual
            if not np.any(m):
                continue
            _, B = templates(ra[m], dec[m])
            yy = np.column_stack([y1[m], y2[m]])
            resid = yy - np.einsum("nij,j->ni", B, beta_qual)
            e1m, e2m, rhom = e1[m], e2[m], rho[m]
            inv = 1.0 / (1.0 - rhom * rhom)
            w0 = inv * (resid[:, 0] / (e1m * e1m) - rhom * resid[:, 1] / (e1m * e2m))
            w1 = inv * (resid[:, 1] / (e2m * e2m) - rhom * resid[:, 0] / (e1m * e2m))
            ss = B[:, 0, :] * w0[:, None] + B[:, 1, :] * w1[:, None]
            pix = hp.ang2pix(4, np.pi / 2.0 - dec[m], ra[m] % (2.0 * np.pi))
            for j in range(16):
                score_patch[:, j] += np.bincount(pix, weights=ss[:, j], minlength=192)

    cpatch_micro2 = (cov_qual @ score_patch.T @ score_patch @ cov_qual) * 1e6
    saved_cpatch = np.asarray(saved_r69["results"]["quality"]["spatial_patch_192_cov_microasyr2"], dtype=float)
    patch_rel_err = _rel(cpatch_micro2, saved_cpatch)
    if patch_rel_err > 2e-8:
        raise AssertionError(f"R69 patch covariance mismatch: {patch_rel_err}")
    cformal_micro2 = np.asarray(fits_full["quality"]["formal_cov_microasyr2"], dtype=float)
    var_ratio = np.diag(cpatch_micro2) / np.diag(cformal_micro2)
    patch_alias = phy_fast.gaia_eb_mask_alias(cpatch_micro2)

    # AIP cross-check (gaia_crf3_astrometry_aip.fits: 1,612,202 rows)
    aip_acc = {"all": _empty_acc(), "quality": _empty_acc()}
    with fits.open(GAIA_AIP, memmap=True) as f:
        tbl = f[1].data
        for start in range(0, len(tbl), CHUNK):
            chunk = tbl[start : start + CHUNK]
            ra, dec, y1, y2, e1, e2, rho, valid, qual = prepare(chunk)
            if not np.any(valid):
                continue
            _, B = templates(ra[valid], dec[valid])
            yy = np.column_stack([y1[valid], y2[valid]])
            e1v, e2v, rhov = e1[valid], e2[valid], rho[valid]
            qv = qual[valid]
            Fi, sc, chi = pre_dag_fast.accumulate_gaia(B, yy, e1v, e2v, rhov, threads=THREADS)
            _add_acc(aip_acc["all"], Fi, sc, chi, int(np.sum(valid)))
            if np.any(qv):
                Fi_q, sc_q, chi_q = pre_dag_fast.accumulate_gaia(
                    B[qv], yy[qv], e1v[qv], e2v[qv], rhov[qv], threads=THREADS
                )
                _add_acc(aip_acc["quality"], Fi_q, sc_q, chi_q, int(np.sum(qv)))

    # Heldout evaluations: North<->South and 4 RA quadrants
    heldout_folds = [
        _heldout_eval(accum["quality_north"], accum["quality_south"], "train_north_test_south"),
        _heldout_eval(accum["quality_south"], accum["quality_north"], "train_south_test_north"),
    ]
    ra_keys = ("ra_q0_0_90", "ra_q1_90_180", "ra_q2_180_270", "ra_q3_270_360")
    assert sum(accum[k]["N"] for k in ra_keys) == accum["quality"]["N"]
    for k in ra_keys:
        acc_tr = {
            "F": accum["quality"]["F"] - accum[k]["F"],
            "score": accum["quality"]["score"] - accum[k]["score"],
            "chisq": accum["quality"]["chisq"] - accum[k]["chisq"],
            "N": accum["quality"]["N"] - accum[k]["N"],
        }
        heldout_folds.append(_heldout_eval(acc_tr, accum[k], f"leave_out_{k}"))

    # K03 & K01 checks
    k03_info = p5p6_fast.inspect_k03_cross_moments(K03_PATH)
    k01_check = p5p6_fast.observer_radial_kinematics(
        np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]),
        theta=6e-18,
        sigma=np.diag([1e-19, -0.5e-19, -0.5e-19]),
        acceleration_over_c=np.array([1e-19, 0.0, 0.0]),
        omega=np.array([1e-18, 2e-18, -1e-18]),
    )

    elapsed = time.perf_counter() - t0
    used_backends = sorted({r.get("used", "UNKNOWN") for r in receipts})

    out = {
        "schema": "htt.r89.g03_gaia_bounded_source_diagnostic/1",
        "group_id": "G03_GAIA",
        "node_ids": ["K01", "K02", "SQ-GAIA", "K03", "K04", "K05", "K06"],
        "source_sha256": {
            str(GAIA_FULL): sha_full,
            str(GAIA_AIP): sha_aip,
            str(K03_PATH): sha_k03,
            "R69_GAIA_E1B1E2B2": _sha256(R69_SAVED),
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "elapsed_seconds": float(elapsed),
            "maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            "chunk_rows": CHUNK,
            "threads": THREADS,
            "cpp_native_backends_observed": used_backends,
            "total_accumulate_calls": len(receipts),
        },
        "r69_exact_replay_parity": r69_parity,
        "patch_192_sandwich_diagnostics": {
            "relative_cov_error_vs_R69": patch_rel_err,
            "min_eigen_microasyr2": float(np.linalg.eigvalsh(cpatch_micro2)[0]),
            "variance_inflation_patch_over_formal": {
                "all_16_ratios": var_ratio.tolist(),
                "E1_minmax": [float(var_ratio[0:3].min()), float(var_ratio[0:3].max())],
                "B1_minmax": [float(var_ratio[3:6].min()), float(var_ratio[3:6].max())],
                "E2_minmax": [float(var_ratio[6:11].min()), float(var_ratio[6:11].max())],
                "B2_minmax": [float(var_ratio[11:16].min()), float(var_ratio[11:16].max())],
            },
            "E2_B2_mask_alias_under_patch_cov": {
                "canonical": patch_alias["canonical"].tolist(),
                "maxcanonical": patch_alias["maxcanonical"],
            },
        },
        "full_and_hemisphere_fits": {k: _summarize_fit(accum[k]) for k in ("all", "quality", "quality_north", "quality_south")},
        "aip_cross_check": {k: _summarize_fit(aip_acc[k]) for k in ("all", "quality")},
        "systematic_alias_subsets": {
            "nonfinite_phot_g_mean_mag_in_quality_count": nonfinite_gmag_qual,
            "fits": {
                k: _summarize_fit(accum[k])
                for k in ("solved_31_5p", "solved_95_6p", "vis_lt_15", "vis_ge_15", "gmag_lt_19p5", "gmag_ge_19p5")
            },
            "disjoint_contrasts": [
                _disjoint_contrast(accum["solved_31_5p"], accum["solved_95_6p"], "solved_31_5p", "solved_95_6p"),
                _disjoint_contrast(accum["vis_lt_15"], accum["vis_ge_15"], "vis_lt_15", "vis_ge_15"),
                _disjoint_contrast(accum["gmag_lt_19p5"], accum["gmag_ge_19p5"], "gmag_lt_19p5", "gmag_ge_19p5"),
                _disjoint_contrast(accum["quality_north"], accum["quality_south"], "quality_north", "quality_south"),
            ],
        },
        "spatial_heldout_forecasts": heldout_folds,
        "k03_cross_moments": k03_info,
        "k01_radial_omega_blindness_maxabs": k01_check["radial_omega_response_maxabs"],
        "physical_claim_gates": {
            "physical_shear_measured": False,
            "physical_vorticity_omega_measured": False,
            "physical_congruence_identified": False,
            "independent_redshift_AGN_scan_null": None,
            "K03_status": "BLOCKED_INPUT",
            "K04_K05_K06_status": "BLOCKED_DEPENDENCY",
        },
        "node_verdicts": {
            "K01": "REUSED_SCOPED",
            "K02": "REUSED_SCOPED",
            "SQ-GAIA": "DIAGNOSTIC_COMPLETED_SCOPED",
            "K03": "BLOCKED_INPUT",
            "K04": "BLOCKED_DEPENDENCY",
            "K05": "BLOCKED_DEPENDENCY",
            "K06": "BLOCKED_DEPENDENCY",
        },
        "missing_physics_and_next_action": {
            "missing": [
                "per-source AGN redshifts and radial-vs-angular lightcone optical transfer",
                "calibrated Gaia scanning-law / AL-AC time-series and AGN color/morphology selection covariance",
                "qualified nonradial astrophysical source null",
            ],
            "next_action": "Obtain per-source Gaia QSO redshifts, scanning-law covariance, and normal-frame optical transfer for SQ-GAIA -> K03; keep K04-K06 blocked and proceed independently to G04_RADIO_FRAME (SQ-FRAME, SQ-RADIO)",
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "group_id": "G03_GAIA",
        "elapsed_s": round(elapsed, 3),
        "maxrss_mib": round(out["runtime"]["maxrss_kib"] / 1024.0, 1),
        "backends": used_backends,
        "r69_max_err": max(max(v.values()) for v in r69_parity.values()),
        "patch_rel_err": patch_rel_err,
        "contrast_5p_6p_wald16": out["systematic_alias_subsets"]["disjoint_contrasts"][0]["formal_contrasts"]["all_16D"]["formal_wald_chi2"],
        "contrast_vis_wald16": out["systematic_alias_subsets"]["disjoint_contrasts"][1]["formal_contrasts"]["all_16D"]["formal_wald_chi2"],
        "contrast_gmag_wald16": out["systematic_alias_subsets"]["disjoint_contrasts"][2]["formal_contrasts"]["all_16D"]["formal_wald_chi2"],
        "contrast_ns_wald16": out["systematic_alias_subsets"]["disjoint_contrasts"][3]["formal_contrasts"]["all_16D"]["formal_wald_chi2"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
