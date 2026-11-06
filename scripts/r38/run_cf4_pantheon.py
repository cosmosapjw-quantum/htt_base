"""Execution script for CF4 and Pantheon+ directional distance/Hubble response (R38-07).

Phase D of HTT-R38 Observational Convergence.
Executes exact 2-axis row selection and covariance subsetting for Pantheon+ (490 and 705 rows),
evaluates directional Hubble response against CF4 (35,970 groups),
and exports directional distance results and row maps.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import numpy as np

from common.covariance_validator import validate_covariance
from common.row_selector import ExactRowSelector
from common.nuisance_projection import analyze_nuisance_projected_rank
from common.kinematic_response import STF_BASIS

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_R38 = REPO_ROOT / "docs/research_program/observational_publication_20261015/OBSERVATIONAL_CONVERGENCE_20261107"
OUT_DIR = DOCS_R38 / "CF4_PANTHEON_ROW_MAPS"

def main():
    print("Executing CF4 & Pantheon+ Directional Distance Analysis (R38-07)...")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Pantheon+ SH0ES exact row selection and GLS fit
    p_dat = Path("/mnt/extdrive/workdir/htt_open_data/pantheonplus/c447f0f/Pantheon_SH0ES.dat")
    p_cov = Path("/mnt/extdrive/workdir/htt_open_data/pantheonplus/c447f0f/Pantheon_SH0ES_STAT_SYS.cov")
    
    rows = np.genfromtxt(p_dat, names=True, dtype=None, encoding='utf-8')
    cov_raw = np.loadtxt(p_cov)
    n_cov = int(cov_raw[0])
    C_full = cov_raw[1:].reshape(n_cov, n_cov)
    
    source_ids = [f"{rows['CID'][i]}_{rows['IDSURVEY'][i]}" for i in range(len(rows))]
    selector = ExactRowSelector(
        source_ids=source_ids,
        data_vector=rows['m_b_corr'],
        covariance=C_full,
        allow_duplicates=False,
        name="pantheon_exact_selector",
    )
    
    # Selection 1: Primary 490 rows (zHD in [0.0233, 0.15], non-calibrators)
    names = ('CID IDSURVEY RA DEC zHD zHDERR zCMB zCMBERR zHEL zHELERR '
             'm_b_corr IS_CALIBRATOR USED_IN_SH0ES_HF VPEC VPECERR').split()
    mask_490 = (rows['IS_CALIBRATOR'] == 0) & (rows['zHD'] >= 0.0233) & (rows['zHD'] <= 0.15)
    for col in names[2:]:
        mask_490 &= np.isfinite(rows[col])
        
    res_490 = selector.select_by_mask(mask_490, selection_label="primary_490")
    print(f"  Pantheon+ primary selection: {res_490.selected_count} rows, PD: {res_490.covariance_audit.is_positive_definite}")
    
    # Selection 2: Sensitivity 705 rows (zHD in [0.010, 0.15])
    mask_705 = (rows['IS_CALIBRATOR'] == 0) & (rows['zHD'] >= 0.010) & (rows['zHD'] <= 0.15)
    for col in names[2:]:
        mask_705 &= np.isfinite(rows[col])
    res_705 = selector.select_by_mask(mask_705, selection_label="sensitivity_705")
    print(f"  Pantheon+ sensitivity selection: {res_705.selected_count} rows, PD: {res_705.covariance_audit.is_positive_definite}")
    
    # Build directional design matrix for 490 rows
    sub_rows = rows[res_490.selected_indices]
    r = np.deg2rad(sub_rows['RA'])
    d = np.deg2rad(sub_rows['DEC'])
    n_vecs = np.stack((np.cos(d)*np.cos(r), np.cos(d)*np.sin(r), np.sin(d)), axis=1)
    
    # Angular carrier: 3 dipole (acceleration) + 5 quadrupole (shear)
    stf_angular = np.einsum("ni,aij,nj->na", n_vecs, STF_BASIS, n_vecs, optimize=True)
    signal_490 = np.column_stack((n_vecs, stf_angular)) # 8 angular modes
    nuisance_490 = np.ones((len(sub_rows), 1)) # Monopole offset M_0
    
    # Background FLRW magnitude: reference Hubble law
    # mu_ref = 5 * log10( c * z / H0 ) + 25
    z_hd = sub_rows['zHD']
    mu_ref = 5.0 * np.log10(299792.458 * z_hd / 70.0) + 25.0
    y_490 = res_490.selected_vector - mu_ref
    
    fit_sn = analyze_nuisance_projected_rank(
        y=y_490,
        signal_matrix=signal_490,
        nuisance_matrix=nuisance_490,
        covariance=res_490.selected_covariance,
        rank_tol=1e-8,
        name="pantheon_490_directional_fit",
    )
    
    print(f"  Pantheon+ 490 Fit: rank={fit_sn.effective_rank}/8, chi2_null={fit_sn.chi2_null:.2f}, chi2_full={fit_sn.chi2_full:.2f}, delta_chi2={fit_sn.delta_chi2:.2f}")
    
    # 2. CF4 Directional Hubble response on 35,970 groups
    cf4_npz = REPO_ROOT / "docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz"
    with np.load(cf4_npz) as z:
        cf4_ids = z["group_id"]
        cf4_z = z["z_CMB"]
        cf4_dm = z["dmzp"]
        cf4_edm = z["e_dmzp"]
        cf4_n = z["n_J2000"]
        cf4_method = z["method_family"]
        
    n_cf4 = len(cf4_ids)
    print(f"  Loaded CF4 selected operator: {n_cf4:,} groups")
    
    # Compute CF4 distance d and velocity y
    cf4_d = 10.0 ** ((cf4_dm - 25.0) / 5.0)
    cf4_sigma = np.hypot(250.0, 70.0 * (np.log(10.0) / 5.0) * cf4_d * cf4_edm)
    cf4_y = 299792.458 * cf4_z
    cf4_stf = np.einsum("ni,aij,nj->na", cf4_n, STF_BASIS, cf4_n, optimize=True)
    
    # Signal: Hubble expansion dipole + quadrupole
    cf4_S = cf4_d[:, None] * np.column_stack((cf4_n, cf4_stf)) # (35970, 8)
    cf4_N = cf4_d[:, None] # Isotropic H_0
    
    # Diagonal weight solve for CF4 (standard survey operator)
    weights = 1.0 / (cf4_sigma ** 2)
    Sw = cf4_S * np.sqrt(weights)[:, None]
    Nw = cf4_N * np.sqrt(weights)[:, None]
    yw = cf4_y * np.sqrt(weights)
    
    Qn, Rn = np.linalg.qr(Nw, mode="reduced")
    yp = yw - Qn @ (Qn.T @ yw)
    Sp = Sw - Qn @ (Qn.T @ Sw)
    
    u, s, vh = np.linalg.svd(Sp, full_matrices=False)
    cf4_coeff = vh.T @ ((u.T @ yp) / s)
    cf4_cov = vh.T @ np.diag(1.0 / s**2) @ vh
    chi2_cf4_null = float(np.sum(yp ** 2))
    chi2_cf4_full = float(np.sum((yp - Sp @ cf4_coeff) ** 2))
    delta_chi2_cf4 = chi2_cf4_null - chi2_cf4_full
    
    print(f"  CF4 35,970 Fit: rank={len(s)}/8, chi2_null={chi2_cf4_null:.1f}, chi2_full={chi2_cf4_full:.1f}, delta_chi2={delta_chi2_cf4:.2f}")
    
    # Export row maps
    row_map_490 = {
        "selection_label": "pantheon_primary_490",
        "row_count": res_490.selected_count,
        "row_key_sha256": res_490.row_key_sha256,
        "selected_indices": res_490.selected_indices.tolist(),
        "selected_cids": [str(rows['CID'][i]) for i in res_490.selected_indices],
    }
    with open(OUT_DIR / "pantheon_490_row_map.json", "w", encoding="utf-8") as f:
        json.dump(row_map_490, f, indent=2)
        
    row_map_705 = {
        "selection_label": "pantheon_sensitivity_705",
        "row_count": res_705.selected_count,
        "row_key_sha256": res_705.row_key_sha256,
        "selected_indices": res_705.selected_indices.tolist(),
    }
    with open(OUT_DIR / "pantheon_705_row_map.json", "w", encoding="utf-8") as f:
        json.dump(row_map_705, f, indent=2)
        
    row_map_cf4 = {
        "selection_label": "cf4_selected_operator_35970",
        "group_count": n_cf4,
        "first_5_pgc": cf4_ids[:5].tolist(),
        "last_5_pgc": cf4_ids[-5].tolist(),
    }
    with open(OUT_DIR / "cf4_35970_row_map.json", "w", encoding="utf-8") as f:
        json.dump(row_map_cf4, f, indent=2)
        
    # Export structured DIRECTIONAL_DISTANCE_RESULT.json
    result = {
        "schema": "htt.r38_directional_distance_result/1",
        "program": "HTT-R38",
        "task_id": "R38-07-CF4-PANTHEON",
        "status": "QUALIFIED_EXACT_ROW_SUBSET_COVARIANCE",
        "claim_tier": "C0",
        "pantheon_plus": {
            "source_catalog": str(p_dat),
            "primary_selected_rows": res_490.selected_count,
            "primary_row_key_sha256": res_490.row_key_sha256,
            "sensitivity_selected_rows": res_705.selected_count,
            "covariance_min_eigenvalue": res_490.covariance_audit.min_eigenvalue,
            "covariance_condition_number": res_490.covariance_audit.condition_number,
            "is_positive_definite": res_490.covariance_audit.is_positive_definite,
            "chi2_null": fit_sn.chi2_null,
            "chi2_full": fit_sn.chi2_full,
            "delta_chi2": fit_sn.delta_chi2,
            "fitted_angular_coefficients": fit_sn.coefficients.tolist(),
            "parameter_covariance": fit_sn.parameter_covariance.tolist(),
        },
        "cosmicflows_4": {
            "source_operator": str(cf4_npz),
            "group_count": n_cf4,
            "chi2_null": chi2_cf4_null,
            "chi2_full": chi2_cf4_full,
            "delta_chi2": delta_chi2_cf4,
            "fitted_shear_coefficients": cf4_coeff[3:].tolist(),
            "parameter_covariance": cf4_cov[3:, 3:].tolist(),
        },
        "caveat": "Pantheon+ and CF4 angular anisotropy is dominated by survey sky geometry, galactic plane avoidance, and method pooling; cannot be claimed as cosmological Hubble anisotropy without native solver transfer.",
    }
    
    out_json = DOCS_R38 / "DIRECTIONAL_DISTANCE_RESULT.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Wrote {out_json}")
    print("CF4 & Pantheon+ Directional Distance Analysis COMPLETE.")

if __name__ == "__main__":
    main()

