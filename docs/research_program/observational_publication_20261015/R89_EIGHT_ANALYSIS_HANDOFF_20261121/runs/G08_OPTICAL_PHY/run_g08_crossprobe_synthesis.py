#!/usr/bin/env python3
"""R89 G08_OPTICAL_PHY Phase-3 cross-probe synthesis & 60-node accounting (create-only).

Synthesizes the four deep Phase-3 deliverables (G02_CF4 SN+SDSS, G03_GAIA scanlaw+VLBA,
G04_RADIO_FRAME 5-survey ladder, G05_PLANCK 8-map + 50-MC) alongside Phase-1 R89 RESULT.json
files and R78 INTEGRATED_DAG.json in a consistent ICRS/Galactic frame without upgrading any
blocked science gates or claiming physical_Pi / physical_GF.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import resource
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docs.research_program.observational_publication_20261015.H03_20261016.src.h03_tomography import (
    quadrupole_matrix,
)
from scripts.r68.fiveview_geometry import stf_matrix

RUNS_DIR = ROOT / "docs/research_program/observational_publication_20261015/R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs"
DAG_JSON = ROOT / "docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
OUT_JSON = RUNS_DIR / "G08_OPTICAL_PHY/CROSSPROBE_SYNTHESIS_RESULT.json"

PHASE3_INPUTS = {
    "G02_CF4": RUNS_DIR / "G02_CF4/DEEP_MULTISURVEY_RESULT.json",
    "G03_GAIA": RUNS_DIR / "G03_GAIA/DEEP_SCANLAW_VLBA_RESULT.json",
    "G04_RADIO_FRAME": RUNS_DIR / "G04_RADIO_FRAME/DEEP_FIVE_SURVEY_RESULT.json",
    "G05_PLANCK": RUNS_DIR / "G05_PLANCK/DEEP_MULTIPIPELINE_CMB_RESULT.json",
}

GROUPS = [
    "G01_COMMON",
    "G02_CF4",
    "G03_GAIA",
    "G04_RADIO_FRAME",
    "G05_PLANCK",
    "G06_P1",
    "G07_BIANCHI",
    "G08_OPTICAL_PHY",
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _lb_to_gal_vec(l_deg: float, b_deg: float) -> np.ndarray:
    l = math.radians(l_deg)
    b = math.radians(b_deg)
    cb = math.cos(b)
    return np.array([cb * math.cos(l), cb * math.sin(l), math.sin(b)], dtype=np.float64)


def _icrs_to_gal_matrix() -> np.ndarray:
    sc = SkyCoord(ra=[0.0, 90.0, 0.0] * u.deg, dec=[0.0, 0.0, 90.0] * u.deg, frame="icrs").galactic
    cols = []
    for pt in sc:
        cols.append(_lb_to_gal_vec(float(pt.l.deg), float(pt.b.deg)))
    R = np.column_stack(cols)
    if np.max(np.abs(R.T @ R - np.eye(3))) > 1e-10:
        raise RuntimeError("ICRS->Galactic rotation matrix orthogonality check failed")
    return R


def _gal_vec_to_lb(v: np.ndarray) -> tuple[float, float]:
    uv = v / max(float(np.linalg.norm(v)), 1e-30)
    b_deg = math.degrees(math.asin(max(-1.0, min(1.0, float(uv[2])))))
    l_deg = math.degrees(math.atan2(float(uv[1]), float(uv[0]))) % 360.0
    return float(l_deg), float(b_deg)


def _ang_deg(u1: np.ndarray, u2: np.ndarray) -> float:
    dot = float(np.dot(u1, u2) / max(np.linalg.norm(u1) * np.linalg.norm(u2), 1e-30))
    return float(math.degrees(math.acos(max(-1.0, min(1.0, dot)))))


def _principal_axis_gal(q_stf5_icrs: np.ndarray, R_icrs_to_gal: np.ndarray, basis: str) -> tuple[np.ndarray, np.ndarray]:
    if basis == "h03":
        q_icrs = quadrupole_matrix(q_stf5_icrs)
    elif basis == "fiveview":
        q_icrs = stf_matrix(q_stf5_icrs)
    else:
        raise ValueError(f"Unknown STF basis: {basis}")
    q_gal = R_icrs_to_gal @ q_icrs @ R_icrs_to_gal.T
    evals, evecs = np.linalg.eigh(q_gal)
    idx = int(np.argmax(np.abs(evals)))
    axis = evecs[:, idx].copy()
    if axis[2] < 0.0:
        axis = -axis
    return axis, q_gal


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()

    R_ig = _icrs_to_gal_matrix()
    g2 = json.loads(PHASE3_INPUTS["G02_CF4"].read_text(encoding="utf-8"))
    g3 = json.loads(PHASE3_INPUTS["G03_GAIA"].read_text(encoding="utf-8"))
    g4 = json.loads(PHASE3_INPUTS["G04_RADIO_FRAME"].read_text(encoding="utf-8"))
    g5 = json.loads(PHASE3_INPUTS["G05_PLANCK"].read_text(encoding="utf-8"))
    dag = json.loads(DAG_JSON.read_text(encoding="utf-8"))

    # 1. Cross-probe dipole unit vectors in Galactic coordinates
    cmb_gal = _lb_to_gal_vec(264.021, 48.253)
    gc_gal = _lb_to_gal_vec(0.0, 0.0)

    des_4p = g2["des_dovekie_5yr"]["fits_mag"]["valid_sky_all_z_4p_stat_sys"]
    des_9p = g2["des_dovekie_5yr"]["fits_mag"]["valid_sky_all_z_9p_stat_sys"]
    pp_all = g2["pantheon_plus_shoes"]["base_fits_mag"]["all_sky_z_gt_0p01_stat_sys"]
    pp_lowz = g2["pantheon_plus_shoes"]["base_fits_mag"]["lowz_0p01_0p15_stat_sys"]

    gaia_qall = g3["gaia_crf3_slices"]["subsets"]["quality_all"]
    gaia_e1_gal = R_ig @ np.asarray(gaia_qall["coefs_microasyr"][:3], dtype=np.float64)
    vlba_clean = g3["vlba_233_3_vsh"]["subsets"]["clean_5sigma"]
    vlba_e1_gal = R_ig @ np.asarray(vlba_clean["coefs_microasyr"][:3], dtype=np.float64)

    dipole_vectors_gal = {
        "CMB_kinematic_ref": cmb_gal,
        "Galactic_Center_ref": gc_gal,
        "DES_Dovekie_4p_stat_sys": R_ig @ np.asarray(des_4p["dipole_vec"], dtype=np.float64),
        "PantheonPlus_allz_9p_stat_sys": R_ig @ np.asarray(pp_all["dipole_vec"], dtype=np.float64),
        "PantheonPlus_lowz_9p_stat_sys": R_ig @ np.asarray(pp_lowz["dipole_vec"], dtype=np.float64),
        "Gaia_CRF3_quality_all_E1": gaia_e1_gal,
        "VLBA_233_3_clean5sig_E1": vlba_e1_gal,
        "NVSS_S20": R_ig @ np.asarray(g4["surveys"]["NVSS_1400MHz"]["flux_ladder_mJy"]["20"]["dipole_icrs_vec"], dtype=np.float64),
        "NVSS_S50": R_ig @ np.asarray(g4["surveys"]["NVSS_1400MHz"]["flux_ladder_mJy"]["50"]["dipole_icrs_vec"], dtype=np.float64),
        "RACS_DR1_raw_S20": R_ig @ np.asarray(g4["surveys"]["RACS_low_DR1_888MHz"]["raw_footprint_ladder_mJy"]["20"]["dipole_icrs_vec"], dtype=np.float64),
        "SPICE_RACS_S20": R_ig @ np.asarray(g4["surveys"]["SPICE_RACS_DR2_944MHz"]["full_footprint_ladder_mJy"]["20"]["dipole_icrs_vec"], dtype=np.float64),
        "SPICE_RACS_S50": R_ig @ np.asarray(g4["surveys"]["SPICE_RACS_DR2_944MHz"]["full_footprint_ladder_mJy"]["50"]["dipole_icrs_vec"], dtype=np.float64),
        "SUMSS_S20": R_ig @ np.asarray(g4["surveys"]["SUMSS_v21_843MHz"]["flux_ladder_mJy"]["20"]["dipole_icrs_vec"], dtype=np.float64),
        "LoTSS_DR3_S50": R_ig @ np.asarray(g4["surveys"]["LoTSS_DR3_144MHz"]["flux_ladder_mJy"]["50"]["dipole_icrs_vec"], dtype=np.float64),
    }

    dipole_summary = {}
    probe_names = list(dipole_vectors_gal.keys())
    for k, vec in dipole_vectors_gal.items():
        l_d, b_d = _gal_vec_to_lb(vec)
        sep_cmb = _ang_deg(vec, cmb_gal)
        sep_gc = _ang_deg(vec, gc_gal)
        dipole_summary[k] = {
            "gal_l_deg": l_d,
            "gal_b_deg": b_d,
            "amp_native_units": float(np.linalg.norm(vec)),
            "sep_from_cmb_deg": sep_cmb,
            "antipodal_sep_from_cmb_deg": float(180.0 - sep_cmb),
            "acute_axis_sep_from_cmb_deg": float(min(sep_cmb, 180.0 - sep_cmb)),
            "sep_from_gal_center_deg": sep_gc,
        }

    sep_matrix_deg = {
        p1: {p2: round(_ang_deg(dipole_vectors_gal[p1], dipole_vectors_gal[p2]), 3) for p2 in probe_names}
        for p1 in probe_names
    }

    # 2. Cross-probe quadrupole principal axes & STF Frobenius alignments in Galactic frame
    smica_n2 = np.asarray(g5["eight_map_common_mask_lowell"]["PR3_SMICA"]["n2_gal_axis"], dtype=np.float64)
    if smica_n2[2] < 0.0:
        smica_n2 = -smica_n2
    comm_n2 = np.asarray(g5["eight_map_common_mask_lowell"]["PR3_Commander"]["n2_gal_axis"], dtype=np.float64)
    if comm_n2[2] < 0.0:
        comm_n2 = -comm_n2

    pp_ax, pp_qgal = _principal_axis_gal(np.asarray(pp_all["quad_vec"], dtype=np.float64), R_ig, "h03")
    gaia_ax, gaia_qgal = _principal_axis_gal(np.asarray(gaia_qall["coefs_microasyr"][6:11], dtype=np.float64), R_ig, "fiveview")
    scan_ax, scan_qgal = _principal_axis_gal(np.asarray(g3["gaia_scanning_law"]["delta_n_quad_stf5"], dtype=np.float64), R_ig, "h03")
    vlba_ax, vlba_qgal = _principal_axis_gal(np.asarray(vlba_clean["coefs_microasyr"][6:11], dtype=np.float64), R_ig, "fiveview")

    quad_axes = {
        "CMB_PR3_SMICA_T_n2": smica_n2,
        "CMB_PR3_Commander_T_n2": comm_n2,
        "PantheonPlus_allz_stat_sys_Q": pp_ax,
        "Gaia_CRF3_quality_all_E2": gaia_ax,
        "Gaia_ScanLaw_deltaN_Q": scan_ax,
        "VLBA_233_3_clean5sig_E2": vlba_ax,
    }
    quad_tensors = {
        "PantheonPlus_allz_stat_sys_Q": pp_qgal,
        "Gaia_CRF3_quality_all_E2": gaia_qgal,
        "Gaia_ScanLaw_deltaN_Q": scan_qgal,
        "VLBA_233_3_clean5sig_E2": vlba_qgal,
    }
    quad_names = list(quad_axes.keys())
    quad_acute_sep_deg = {
        q1: {
            q2: round(min(_ang_deg(quad_axes[q1], quad_axes[q2]), 180.0 - _ang_deg(quad_axes[q1], quad_axes[q2])), 3)
            for q2 in quad_names
        }
        for q1 in quad_names
    }
    qmat_names = list(quad_tensors.keys())
    quad_frob_cos = {
        q1: {
            q2: round(
                float(np.sum(quad_tensors[q1] * quad_tensors[q2]))
                / max(float(np.linalg.norm(quad_tensors[q1]) * np.linalg.norm(quad_tensors[q2])), 1e-30),
                4,
            )
            for q2 in qmat_names
        }
        for q1 in qmat_names
    }

    # 3. 60-node R78/R89 completeness accounting
    dag_nodes = {n["id"]: n for n in dag["nodes"]}
    if len(dag_nodes) != 60:
        raise RuntimeError(f"Expected 60 R78 DAG nodes, found {len(dag_nodes)}")
    verdicts_all: dict[str, str] = {}
    group_counts: dict[str, dict[str, int]] = {}
    duplicates: list[str] = []
    for grp in GROUPS:
        res = json.loads((RUNS_DIR / grp / "RESULT.json").read_text(encoding="utf-8"))
        nv = res["node_verdicts"]
        c = Counter(nv.values())
        group_counts[grp] = dict(c)
        for nid, st in nv.items():
            if nid in verdicts_all:
                duplicates.append(nid)
            verdicts_all[nid] = st
    missing_nodes = sorted(set(dag_nodes.keys()) - set(verdicts_all.keys()))
    extra_nodes = sorted(set(verdicts_all.keys()) - set(dag_nodes.keys()))
    if duplicates or missing_nodes or extra_nodes or len(verdicts_all) != 60:
        raise RuntimeError(
            f"60-node accounting mismatch: len={len(verdicts_all)}, dup={duplicates}, missing={missing_nodes}, extra={extra_nodes}"
        )

    status_totals = dict(Counter(verdicts_all.values()))

    # 4. Systematic-floor & cross-probe physical gate summary
    dt = time.perf_counter() - t0
    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    payload = {
        "artifact_id": "R89_G08_OPTICAL_PHY_CROSSPROBE_SYNTHESIS_V1",
        "group_id": "G08_OPTICAL_PHY",
        "create_only": True,
        "runtime_sec": round(dt, 3),
        "max_rss_mb": round(rss_mb, 2),
        "platform": platform.platform(),
        "input_sha256": {
            **{k: _sha256(p) for k, p in PHASE3_INPUTS.items()},
            "R78_INTEGRATED_DAG": _sha256(DAG_JSON),
        },
        "r78_r89_60_node_accounting": {
            "total_unique_nodes_covered": len(verdicts_all),
            "expected_dag_nodes": len(dag_nodes),
            "missing_nodes": missing_nodes,
            "extra_nodes": extra_nodes,
            "duplicate_nodes": duplicates,
            "status_totals": status_totals,
            "status_totals_note": "Aggregates Phase-1 R89 RESULT.json node_verdicts (where G02 SQ-CF4 method-contrast exploratory diagnostic was DIAGNOSTIC_COMPLETED_SCOPED); R87/R88/R89-Phase3 physical SQ-CF4 remains BLOCKED_INPUT.",
            "group_status_counts": group_counts,
            "r78_next_action_id": dag["next_action_id"],
            "g02_phase3_sq_cf4_status": g2["sq_cf4_status"],
            "g03_phase3_sq_gaia_status": g3["sq_gaia_status"],
            "sixty_of_sixty_science_pass": False,
        },
        "cross_probe_dipole_alignment_galactic": {
            "probes": dipole_summary,
            "pairwise_separation_deg": sep_matrix_deg,
            "des_9p_collinearity_warning": {
                "F_condition_9p": des_9p["F_condition"],
                "F_condition_4p": des_4p["F_condition"],
                "note": "DES-Dovekie ~30 sq deg footprint makes 9p [monopole, dipole, quadrupole] near-collinear (F_cond ~ 2e8); only 4p dipole is well-conditioned.",
            },
        },
        "cross_probe_quadrupole_alignment_galactic": {
            "principal_axes_gal": {k: [round(float(x), 6) for x in v] for k, v in quad_axes.items()},
            "acute_axis_separation_deg": quad_acute_sep_deg,
            "stf_frobenius_cosine": quad_frob_cos,
            "gaia_scanlaw_reported_stf_cosine": g3["gaia_crf3_slices"]["subsets"]["quality_all"]["E2_cosine_with_scanlaw_delta_n_quad"],
        },
        "systematic_floor_synthesis": {
            "supernovae_and_pv_mocks": {
                "pantheon_statonly_to_statsys_dip_mag": [
                    g2["pantheon_plus_shoes"]["base_fits_mag"]["all_sky_z_gt_0p01_statonly"]["dipole_dir"]["amp"],
                    pp_all["dipole_dir"]["amp"],
                ],
                "pantheon_grouping_delta_dip_range_mag": [
                    min(v["delta_dipole_vs_full_stat_sys_mag"] for v in g2["pantheon_plus_shoes"]["systematic_grouping_ablations"].values()),
                    max(v["delta_dipole_vs_full_stat_sys_mag"] for v in g2["pantheon_plus_shoes"]["systematic_grouping_ablations"].values()),
                ],
                "sdss_63mock_obs_dipole_median_km_s_per_mpc": g2["sdss_hamhod_63_mocks"]["apparent_expansion_dipole_km_s_per_mpc"]["obs_amp_median"],
                "sdss_63mock_diag_wald_p95": g2["sdss_hamhod_63_mocks"]["apparent_expansion_dipole_km_s_per_mpc"]["nominal_diag_wald_chi2_p95"],
            },
            "astrometry_gaia_and_vlba": {
                "gaia_ecliptic_E2_gradient_microasyr": {
                    "abs_beta_lt_20": g3["gaia_crf3_slices"]["subsets"]["ecl_abs_lt_20"]["E2_amp_microasyr"],
                    "abs_beta_20_to_45": g3["gaia_crf3_slices"]["subsets"]["ecl_abs_20_to_45"]["E2_amp_microasyr"],
                    "abs_beta_ge_45": g3["gaia_crf3_slices"]["subsets"]["ecl_abs_ge_45"]["E2_amp_microasyr"],
                },
                "gaia_scan_half_contrast_E2_wald": g3["gaia_crf3_slices"]["nominal_contrasts"]["scan_low_half_vs_high_half"]["contrasts"]["E2_5D"]["formal_wald_chi2"],
                "gaia_gal_cut_contrast_E2_wald": g3["gaia_crf3_slices"]["nominal_contrasts"]["quality_all_vs_gal_b20"]["contrasts"]["E2_5D"]["formal_wald_chi2"],
                "vlba_chi2_dof_all_vs_clean5sig": [
                    g3["vlba_233_3_vsh"]["subsets"]["all_valid"]["chi2_per_dof_working"],
                    vlba_clean["chi2_per_dof_working"],
                ],
            },
            "radio_surveys": {
                "racs_raw_vs_rms_unif_pixel_S20_amp": [
                    g4["surveys"]["RACS_low_DR1_888MHz"]["raw_footprint_ladder_mJy"]["20"]["dipole_amplitude"],
                    g4["surveys"]["RACS_low_DR1_888MHz"]["rms_uniform_footprint_ladder_mJy"]["20"]["dipole_amplitude"],
                ],
                "racs_source_level_rms_cut_0p45_biased_S20_amp": g4["surveys"]["RACS_low_DR1_888MHz"]["source_level_rms_cut_0p45_biased_selection_contrast_S20"]["dipole_amplitude"],
                "lotss_interior_S20_to_S100_overdispersion": [
                    g4["surveys"]["LoTSS_DR3_144MHz"]["flux_ladder_mJy"]["20"]["poisson_overdispersion"],
                    g4["surveys"]["LoTSS_DR3_144MHz"]["flux_ladder_mJy"]["50"]["poisson_overdispersion"],
                    g4["surveys"]["LoTSS_DR3_144MHz"]["flux_ladder_mJy"]["100"]["poisson_overdispersion"],
                ],
                "lotss_edge500_vs_interior1500_S50_overdispersion": [
                    g4["surveys"]["LoTSS_DR3_144MHz"]["edge500_sensitivity_S50"]["poisson_overdispersion"],
                    g4["surveys"]["LoTSS_DR3_144MHz"]["flux_ladder_mJy"]["50"]["poisson_overdispersion"],
                ],
            },
            "cmb_pipelines_and_pilot_mc": {
                "pr3_smica_vs_commander_T_corr": g5["cross_pipeline_T_comparison"]["pearson_corr_matrix"][0][1],
                "pr3_smica_vs_cosmoglobe_QU_corr": g5["cross_pipeline_QU_comparison"]["pearson_corr_matrix"][0][4],
                "cosmoglobe_vs_beyondplanck_QU_corr": g5["cross_pipeline_QU_comparison"]["pearson_corr_matrix"][4][5],
                "smica_50mc_pilot_c2_TT_rank": g5["raw_ffp10_smica_50mc_common_mask"]["smica_c2_TT_rank"]["rank_interval"],
                "smica_50mc_pilot_c2_EE_rank": g5["raw_ffp10_smica_50mc_common_mask"]["smica_c2_EE_rank"]["rank_interval"],
                "commander_ffp10_raw_census": g5["commander_ffp10_raw_census"],
            },
        },
        "claim_hygiene": {
            "physical_Pi": None,
            "physical_GF": None,
            "bianchi_family_identified": False,
            "release_matched_null_pass": False,
            "remaining_primary_blockers": {
                "SQ-CF4": "Absent upstream raw zero-point calibration posterior, physical S_PV, J_cal Sigma_cal J_cal^T, selection covariance, and upstream-independent heldout",
                "SQ-CMB-NULL": "FFP10 raw Commander simulations only 2 complete FITS (with incomplete partial files); end-to-end release-matched null blocked",
                "SQ-NATIVE_B02": "External native polarized all-m Bianchi Boltzmann solver intentionally absent/prohibited in htt_base",
                "SQ-PHOTON-FLUX_SQ-OPTICAL": "Physical photon-flux calibration and finite-redshift common-congruence optical response absent",
            },
            "statement": (
                "Cross-probe directional/systematic synthesis over R89 Phase-3 observational bundles; "
                "all science gates remain fail-closed (NEXT_ID=SQ-CF4, physical_Pi=None, physical_GF=None)."
            ),
        },
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSON} in {dt:.2f}s (max RSS {rss_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
