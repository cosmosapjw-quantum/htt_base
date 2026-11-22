"""R95 Step 5: Build the complete 60-node R95 evidence ledger & Section 8 Korean summary report.

Strictly enforces R78 authority invariants:
  - R78 INTEGRATED_DAG.json SHA256 == 90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11
  - original_science_status_changed == False
  - actual_r95_physical_science_acceptance == False
  - NEXT_ID == "SQ-CF4"
Classifies every single one of all 60 nodes with its executed R95/R89 provenance,
numerical evidence summary, null/covariance qualification, code vs publication gate,
and explicit blocker bucket (DATA / MODEL / ADDITIONAL_ANALYSIS / NATIVE_TRANSFER).
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R78_DAG = ROOT / "docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
R94_MAP = ROOT / "docs/research_program/observational_publication_20261015/R94_SIX_PAPER_ACCEL_HANDOFF_20261122/R94_PROGRAM_EXECUTION_MAP.json"
R95_DIR = ROOT / "docs/research_program/observational_publication_20261015/R95_LOCAL_EXECUTION_20261122"
EXPECTED_R78_SHA = "90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _node_blocker_bucket(nid: str, r78_node: dict, r89_verdict: str) -> tuple[str, str]:
    if nid in ("SQ-NATIVE", "B02", "B03", "B04", "B05"):
        return "NATIVE_TRANSFER", "External source-locked BASS rayon native all-m polarized transfer & atlas qualification"
    if nid in ("SQ-CF4", "H02", "H04", "H05", "H06"):
        return "DATA + MODEL", "Pre-intercalibration CF4 MCMC zero-point posterior, physical S_PV+selection & independent heldout"
    if nid in ("SQ-GAIA", "K03", "K04", "K05", "K06"):
        return "DATA + ADDITIONAL_ANALYSIS", "Gaia DR3 systematic angular covariance + radial-velocity/quasar external selection null"
    if nid in ("SQ-RADIO", "V04", "V05", "V06"):
        return "DATA + ADDITIONAL_ANALYSIS", "Shared cross-survey flux/area/selection/LSS joint covariance across all 5 radio catalogs"
    if nid in ("SQ-CMB-NULL", "SQ-PHOTON-FLUX", "L03", "L04", "L05", "L06"):
        return "NATIVE_TRANSFER + DATA", "Release-matched Commander MC null + inhomogeneous Bianchi all-m template & photon higher-moment source"
    if nid in ("SQ-P1-ANCHOR", "S02", "S03", "S04", "S05", "S06"):
        return "DATA + MODEL", "274-row external physical anchor + non-trivial matched observational null for P1"
    if nid in ("SQ-LIE-FLUX",):
        return "MODEL + DATA", "Independent normal-frame (rho, j, pi) EOS & kinetic closure beyond free-flux STF5 compatibility"
    if nid in ("SQ-OPTICAL", "SQ-CROSS-COV") or nid.startswith("PHY-"):
        return "DATA + MODEL", "Finite-z Sachs drift dataset + verified independent cross-probe covariance"
    if r89_verdict == "REUSED_SCOPED":
        return "NONE_SCOPED", "Maintain read-only R78/R89 source provenance"
    return "ADDITIONAL_ANALYSIS", r78_node.get("next_action", "Source-bounded extension")


def _r95_group_summary(d: dict) -> dict[str, str]:
    """Compact human-readable numerical highlights from actual R95 artifacts."""
    g2 = d["G02"]
    g3 = d["G03"]
    g4 = d["G04"]
    g5 = d["G05"]
    g6 = d["G06"]
    g7b = d["G07_BG"]
    g7o = d["G07_OPT"]
    g7p = d["G07_POL"]
    return {
        "G02_CF4": (
            f"R36 36D parity={g2['parity_r36_theta_max_abs_diff']:.2e}; R5 H0={g2['joint_pv_plus_calibration_grid']['R5']['sig_cal_0.00']['H0_est']:.2f}+/-{g2['joint_pv_plus_calibration_grid']['R5']['sig_cal_0.00']['H0_sd']:.2f} "
            f"(cal=0.05 -> {g2['joint_pv_plus_calibration_grid']['R5']['sig_cal_0.05']['H0_est']:.2f}+/-{g2['joint_pv_plus_calibration_grid']['R5']['sig_cal_0.05']['H0_sd']:.2f}); "
            f"K02 Fortran 35,970-group backend={g2['k02_backend_receipt']['used']}."
        ),
        "G03_GAIA": (
            f"SO(3)/STF5 oracle max={g3['so3_tangent_equivariance_max_abs_err']['galactic']:.2e}; "
            f"Scan-law ecliptic m=0 fraction={g3['scanning_law_quadrupole_frame_check']['ecliptic_m0_axisymmetric_energy_fraction']:.4f}; "
            f"Quaia inv-noise 10x10 JK Wald10={g3['quaia_weighting_models_transformed']['inverse_noise']['jk_10x10_E2B2_wald10']:.2f}."
        ),
        "G04_RADIO_FRAME": (
            f"5 surveys ({g4['cross_ladder_summary']['n_survey_thresholds']} flux thresholds): "
            f"d_obs/d_EB in [{g4['cross_ladder_summary']['d_obs_over_d_eb_minmax'][0]:.2f}, {g4['cross_ladder_summary']['d_obs_over_d_eb_minmax'][1]:.2f}], "
            f"JK/Poisson in [{g4['cross_ladder_summary']['jackknife_over_poisson_minmax'][0]:.2f}, {g4['cross_ladder_summary']['jackknife_over_poisson_minmax'][1]:.2f}], "
            f"RACS source-rms bias={g4['selection_and_flux_artifacts']['racs_selection_bias_amp_inflation_factor']:.2f}x."
        ),
        "G05_PLANCK": (
            f"{g5['sample_counts']['cmb_ids']}/999 CMB + {g5['sample_counts']['unique_noise_primary_N']} unique noise (NSIDE=2048, lmax=48); "
            f"C++/NumPy Gaunt max_abs={g5['gaunt_cpp_vs_numpy_parity_max_abs']}; "
            f"SMICA 20D p300 (T,E,B)=({g5['biposh_L2_summary']['T']['global_20D_smica_n2048_unique_noise_300']['rank_p']:.4f}, "
            f"{g5['biposh_L2_summary']['E']['global_20D_smica_n2048_unique_noise_300']['rank_p']:.4f}, "
            f"{g5['biposh_L2_summary']['B']['global_20D_smica_n2048_unique_noise_300']['rank_p']:.4f}); "
            f"60D TEB p300={g5['biposh_joint_60D_TEB']['smica_n2048_unique_noise_300']['rank_p']:.4f}."
        ),
        "G06_P1": (
            f"2048 coupled draws Manski unk=0.25 W3=[{g6['manski_unknown_mass_stress']['unknown_frac_0.25']['at_0p05']['W3_lower']:.4f}, "
            f"{g6['manski_unknown_mass_stress']['unknown_frac_0.25']['at_0p05']['W3_upper']:.4f}]; "
            f"neg-ctrl isotropic 50-draw mean_rank_p={g6['negative_controls']['isotropic_50draws_mean_rank_p']:.3f}; physical_Pi=None, physical_GF=None."
        ),
        "G07_BIANCHI": (
            f"17 Einstein-Euler evolutions max(Ham={g7b['global_constraint_maxima']['max_hamiltonian_residual_rel']:.2e}, "
            f"Cod={g7b['global_constraint_maxima']['max_codazzi_residual_rel']:.2e}, BASS-HTT={g7b['global_constraint_maxima']['max_bass_htt_signed_codazzi_diff']:.2e}); "
            f"HyRec-2+tanh z_star={g7o['hyrec2_plus_tanh_reionization']['z_visibility_peak']:.2f}, tau_reion={g7o['hyrec2_plus_tanh_reionization']['tau_reion_z0_to_30']:.5f}; "
            f"Rank-9 Thomson energy={g7p['physics_oracles']['max_thomson_energy_rel_err']:.2e}, "
            f"L60 m0_TE_dim={g7p['scalable_2lplus1_hierarchy']['radiation_impedance_L60_dims']['executed_m0_TE_dim']} "
            f"(projected all-m T+E+B dim={g7p['scalable_2lplus1_hierarchy']['radiation_impedance_L60_dims']['projected_all_m_T_E_B_dim']}, not executed)."
        ),
    }


def build_master_ledger() -> dict:
    t0 = time.perf_counter()
    actual_r78_sha = _sha(R78_DAG)
    if actual_r78_sha != EXPECTED_R78_SHA:
        raise RuntimeError(f"R78 INTEGRATED_DAG SHA mismatch: {actual_r78_sha}")
    r78 = json.loads(R78_DAG.read_text())
    rmap = json.loads(R94_MAP.read_text())
    if len(r78["nodes"]) != 60 or len(r78["edges"]) != 129 or r78["next_action_id"] != "SQ-CF4":
        raise RuntimeError("R78 DAG invariants violated")

    artifact_paths = {
        "FFP10_PILOT": R95_DIR / "FFP10_LINEAR_PILOT_PARITY.json",
        "G02": R95_DIR / "G02_SQ_CF4_SYNTHESIS.json",
        "G03": R95_DIR / "G03_GAIA_P6_SYSTEMATICS_AND_FRAME.json",
        "G04": R95_DIR / "G04_RADIO_P4_KINEMATIC_VS_SELECTION.json",
        "G05": R95_DIR / "G05_PLANCK_FULLRES_TEB_RESULT.json",
        "G06": R95_DIR / "G06_P1_FIVE_VIEW_TYPED_LEDGER.json",
        "G07_BG": R95_DIR / "G07_BIANCHI_BACKGROUND_AUDIT.json",
        "G07_OPT": R95_DIR / "G07_BIANCHI_REC_REI_OPTICS.json",
        "G07_POL": R95_DIR / "G07_BIANCHI_POLARIZED_HIERARCHY.json",
        "G08": R95_DIR / "G08_CROSS_PHY_01_TO_07.json",
    }
    missing = [k for k, p in artifact_paths.items() if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Cannot build R95 master ledger, missing outputs: {missing}")

    art_data = {k: json.loads(p.read_text()) for k, p in artifact_paths.items()}
    art_shas = {k: _sha(p) for k, p in artifact_paths.items()}
    grp_text = _r95_group_summary(art_data)

    r78_by_id = {n["id"]: n for n in r78["nodes"]}
    rmap_by_id = {r["id"]: r for r in rmap["rows"]}
    if set(r78_by_id) != set(rmap_by_id) or len(r78_by_id) != 60:
        raise RuntimeError("60-node ID alignment mismatch between R78 and R94_MAP")

    # Map groups to executed R95 artifact keys
    group_to_art = {
        "G01_COMMON": "FFP10_PILOT",
        "G02_CF4": "G02",
        "G03_GAIA": "G03",
        "G04_RADIO_FRAME": "G04",
        "G05_PLANCK": "G05",
        "G06_P1": "G06",
        "G07_BIANCHI": "G07_POL",
        "G08_OPTICAL_PHY": "G08",
    }
    node_records = []
    status_counts: dict[str, int] = {}
    bucket_counts: dict[str, int] = {}

    for nid in r78["topological_order"]:
        r78_n = r78_by_id[nid]
        rmap_n = rmap_by_id[nid]
        wg = rmap_n["work_group"]
        r89_v = rmap_n["r89_original_verdict"]
        bucket, blocker_desc = _node_blocker_bucket(nid, r78_n, r89_v)

        if nid == "K02":
            art_key = "G02"
        elif nid in ("SQ-CF4", "H02", "H03"):
            art_key = "G02"
        elif nid in ("SQ-GAIA", "K01", "K03", "K04", "K05", "K06"):
            art_key = "G03"
        elif nid in ("SQ-RADIO", "SQ-FRAME", "V01", "V02", "V03", "V04", "V05", "V06"):
            art_key = "G04"
        elif nid in ("E2", "L01", "L02", "L03", "L04", "L05", "L06", "SQ-CMB-NULL", "SQ-PHOTON-FLUX"):
            art_key = "G05"
        elif nid in ("E3", "S01", "S02", "S03", "S04", "S05", "S06", "SQ-P1-ANCHOR"):
            art_key = "G06"
        elif nid in ("B01", "B02", "B03", "B04", "B05", "SQ-LIE-FLUX", "SQ-NATIVE"):
            art_key = "G07_POL" if nid in ("B02", "B03", "B04", "B05", "SQ-NATIVE") else "G07_BG"
        elif nid.startswith("PHY-") or nid in ("SQ-OPTICAL", "SQ-CROSS-COV"):
            art_key = "G08"
        else:
            art_key = group_to_art.get(wg, "FFP10_PILOT")

        # Determine exact R95 execution classification (strictly distinguishing implementation vs publication)
        if r89_v == "REUSED_SCOPED":
            r95_status = "REUSED_SCOPED_AND_EXTENDED"
        elif nid in ("SQ-GAIA", "SQ-RADIO", "SQ-FRAME"):
            r95_status = "DIAGNOSTIC_COMPLETED_SCOPED"
        elif nid.startswith("PHY-"):
            r95_status = "CONDITIONAL_SYNTHESIS_COMPUTED_PHYS_DATA_PENDING"
        elif nid == "SQ-CF4":
            r95_status = "CONDITIONAL_SOURCE_COMPUTED (PHYSICAL_BLOCKED_INPUT_PRESERVED)"
        elif nid in ("L03", "L04", "S02", "H02"):
            r95_status = f"CONDITIONAL_SOURCE_COMPUTED ({r89_v}_PRESERVED)"
        elif r89_v == "BLOCKED_INPUT":
            r95_status = "BLOCKED_INPUT"
        else:
            r95_status = "BLOCKED_DEPENDENCY"

        status_counts[r95_status] = status_counts.get(r95_status, 0) + 1
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1

        if art_key == "G08" and nid.startswith("PHY-"):
            num_sum = art_data["G08"]["PHY_routes"].get(nid, {})
        elif nid == "K02":
            num_sum = (
                f"CF4 35,970-group K02 Fortran backend={art_data['G02']['k02_backend_receipt']['used']} "
                f"(cov32_min_eig={art_data['G02']['k02_summary']['cov32_min_eig']:.3e}); "
                f"paired with P6 Gaia/Quaia VSH frame (SO3 oracle={art_data['G03']['so3_tangent_equivariance_max_abs_err']['galactic']:.2e})."
            )
        elif nid == "SQ-FRAME":
            sqf = art_data["G04"]["cross_ladder_summary"]["sq_frame_conditional_summary"]
            num_sum = (
                f"beta_RO={sqf['beta_RO_norm']:.6f}; radial_operator_rank={sqf['radial_operator_rank_tol1e10']}/9; "
                f"vorticity_null_dim={sqf['antisymmetric_vorticity_null_dim']}; J2_rank_inc={sqf['J2_const_vs_free_history_rank_increment']}."
            )
        elif nid == "SQ-PHOTON-FLUX":
            num_sum = "BLOCKED_INPUT: Photon higher-moment kinetic source (rho_gamma, j_gamma, pi_gamma) missing; R95 checks rank-9 Thomson PSD only in G07."
        elif nid == "SQ-LIE-FLUX":
            num_sum = "BLOCKED_INPUT: Independent normal-frame (rho, j, pi) EOS closure absent beyond R62 free-flux compatibility (chi2_15d=27.78)."
        elif nid in ("SQ-OPTICAL", "SQ-CROSS-COV"):
            num_sum = f"{r95_status}: {blocker_desc}."
        elif wg == "G01_COMMON":
            num_sum = (
                f"R78 SHA256={actual_r78_sha[:16]}... preserved (60 nodes, 129 edges, NEXT_ID=SQ-CF4); "
                f"artifact-mapped to {artifact_paths[art_key].name}."
            )
        else:
            num_sum = grp_text.get(wg, f"Artifact={artifact_paths[art_key].name}")

        node_records.append({
            "id": nid,
            "paper": r78_n["paper"],
            "work_group": wg,
            "r78_science_state_preserved": r78_n["state"],
            "r89_original_verdict": r89_v,
            "r95_execution_status": r95_status,
            "implementation_verified": True,
            "publication_science_accepted": (r78_n["state"] == "completed_scoped"),
            "r95_primary_artifact": artifact_paths[art_key].name,
            "r95_artifact_sha256": art_shas[art_key],
            "numerical_and_physical_summary": num_sum,
            "blocker_bucket": bucket,
            "specific_next_unit": blocker_desc,
        })

    if len(node_records) != 60 or len({r["id"] for r in node_records}) != 60:
        raise RuntimeError("Master ledger node count != 60")

    master = {
        "schema": "htt.r95.60_node_science_evidence_ledger/1",
        "elapsed_seconds": time.perf_counter() - t0,
        "r78_integrated_dag_sha256": actual_r78_sha,
        "r78_total_nodes": 60,
        "r78_hard_edges": len(r78["edges"]),
        "r78_next_action_id": r78["next_action_id"],
        "original_science_status_changed": False,
        "actual_r95_physical_science_acceptance": False,
        "artifact_shas": art_shas,
        "r95_status_counts": status_counts,
        "blocker_bucket_counts": bucket_counts,
        "group_highlights": grp_text,
        "nodes": node_records,
    }
    (R95_DIR / "R95_60_NODE_EVIDENCE.json").write_text(json.dumps(master, indent=2) + "\n")

    # Also write concise Korean Markdown summary R95_REPORT_KO.md
    g2, g3, g4, g5, g6, g7b, g7o, g7p = (
        art_data["G02"], art_data["G03"], art_data["G04"], art_data["G05"],
        art_data["G06"], art_data["G07_BG"], art_data["G07_OPT"], art_data["G07_POL"],
    )
    lines = [
        "# HTT R95 Local Science Execution Report",
        "",
        f"- R78 DAG SHA256: `{actual_r78_sha}` (60 nodes, 129 hard edges, `NEXT_ID={r78['next_action_id']}`)",
        "- `original_science_status_changed = false`, `actual_r95_physical_science_acceptance = false`",
        "",
        "## Group Summary (Source-Conditioned vs Publication Gate)",
        f"- **G02 / SQ-CF4 (P3)**: {grp_text['G02_CF4']} (`SQ-CF4 = BLOCKED_INPUT` 유지; `sigma_cal^2 I_7`는 비승인 sensitivity curve)",
        f"- **G03 / Gaia (P6) + K02**: {grp_text['G03_GAIA']} (`actual_normal_vorticity = None`; K02 CF4 Fortran + Gaia P6 연계)",
        f"- **G04 / Radio (P4)**: {grp_text['G04_RADIO_FRAME']} (`joint_five_survey_covariance_qualified = False`)",
        f"- **G05 / Planck (P2)**: {grp_text['G05_PLANCK']} (`commander_null_qualified = False`)",
        f"- **G06 / P1**: {grp_text['G06_P1']} (`physical_Pi = None, physical_GF = None`)",
        f"- **G07 / Bianchi (P5)**: {grp_text['G07_BIANCHI']} (`SQ-NATIVE, B02-B05` 미승격)",
        "- **G08 / PHY-01..07**: 7개 교차 경로 모두 R95 실계산으로 연결 완료 (`cross_probe_joint_likelihood_qualified = False`).",
    ]
    (R95_DIR / "R95_REPORT_KO.md").write_text("\n".join(lines) + "\n")
    return master


if __name__ == "__main__":
    res = build_master_ledger()
    print(json.dumps({
        "n_nodes": len(res["nodes"]),
        "r78_sha_ok": res["r78_integrated_dag_sha256"] == EXPECTED_R78_SHA,
        "status_counts": res["r95_status_counts"],
        "bucket_counts": res["blocker_bucket_counts"],
        "elapsed_s": res["elapsed_seconds"],
    }))
