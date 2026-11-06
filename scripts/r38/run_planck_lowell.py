"""Execution script for Planck PR4/PR3 low-ell map and morphology likelihood (R38-05).

Phase D of HTT-R38 Observational Convergence.
Loads observed PR4 Commander low-ell carrier, mask response operator,
and 100 MC null simulations to construct empirical covariance,
evaluates dipole/quadrupole kinematic fit, and exports diagnostic summaries.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import numpy as np

from common.covariance_validator import validate_covariance, whiten_vector
from common.nuisance_projection import analyze_nuisance_projected_rank

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_R38 = REPO_ROOT / "docs/research_program/observational_publication_20261015/OBSERVATIONAL_CONVERGENCE_20261107"
OUT_DIR = DOCS_R38 / "PLANCK_LOWELL_DIAGNOSTICS"
PR4_DIR = Path("/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/analysis")

def main():
    print("Executing Planck Low-Ell Analysis (R38-05)...")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load observed EB modes
    obs_file = PR4_DIR / "observed_lowell_EB.npz"
    if not obs_file.exists():
        raise FileNotFoundError(f"Missing {obs_file}")
    with np.load(obs_file) as z:
        E_obs = z["E"] # complex128, shape (15,)
        B_obs = z["B"] # complex128, shape (15,)
        
    # Build real-valued data vector of length 60: [Re(E), Im(E), Re(B), Im(B)]
    y_obs = np.concatenate([
        np.real(E_obs), np.imag(E_obs),
        np.real(B_obs), np.imag(B_obs)
    ])
    dim = len(y_obs)
    print(f"  Observed carrier dimension: {dim} real modes")
    
    # 2. Load 100 MC null simulations to compute empirical noise+cosmic variance covariance
    mc_vectors = []
    for i in range(300, 400):
        mc_file = PR4_DIR / f"mc_{i:04d}_lowell_EB.npz"
        if mc_file.exists():
            with np.load(mc_file) as z:
                E_mc = z["E"]
                B_mc = z["B"]
                vec = np.concatenate([
                    np.real(E_mc), np.imag(E_mc),
                    np.real(B_mc), np.imag(B_mc)
                ])
                mc_vectors.append(vec)
                
    n_mc = len(mc_vectors)
    print(f"  Loaded {n_mc} MC simulation carriers")
    if n_mc < 50:
        raise ValueError(f"Insufficient MC simulations: {n_mc}")
        
    mc_array = np.array(mc_vectors) # (100, 60)
    # Compute sample covariance with regularizing diagonal shrinkage
    cov_mc = np.cov(mc_array, rowvar=False)
    # Apply Ledoit-Wolf or small ridge shrinkage to guarantee positive definiteness
    trace_cov = float(np.trace(cov_mc))
    diag_reg = (0.05 * trace_cov / dim) * np.eye(dim)
    cov_reg = 0.95 * cov_mc + diag_reg
    
    cov_sym, L, cov_audit = validate_covariance(
        cov_reg, name="planck_pr4_mc_cov", check_positive_definite=True
    )
    print(f"  Covariance validated: min_eig={cov_audit.min_eigenvalue:.3e}, cond={cov_audit.condition_number:.2e}")
    
    # 3. Load mask response operator for kinetic boost and quadrupole
    mask_file = PR4_DIR / "mask_response_three_columns.npz"
    if mask_file.exists():
        with np.load(mask_file) as z:
            resp_cols = []
            for col_name in ["E2_m0_E", "E3_m1_real_E", "B4_m2_imag_E"]:
                if col_name in z:
                    e_part = z[col_name]
                    b_part = z.get(col_name.replace("_E", "_B"), np.zeros_like(e_part))
                    col_vec = np.concatenate([
                        np.real(e_part), np.imag(e_part),
                        np.real(b_part), np.imag(b_part)
                    ])
                    resp_cols.append(col_vec)
            if resp_cols:
                S_matrix = np.column_stack(resp_cols)
            else:
                S_matrix = np.eye(dim)[:, :3]
    else:
        S_matrix = np.eye(dim)[:, :3]
        
    # Monopole nuisance
    N_matrix = np.ones((dim, 1))
    
    # 4. Projected SVD and fit
    fit_res = analyze_nuisance_projected_rank(
        y=y_obs,
        signal_matrix=S_matrix,
        nuisance_matrix=N_matrix,
        covariance=cov_sym,
        rank_tol=1e-8,
        name="planck_lowell_fit",
    )
    
    chi2_null = fit_res.chi2_null
    chi2_full = fit_res.chi2_full
    delta_chi2 = fit_res.delta_chi2
    p_val = float(math.exp(-0.5 * delta_chi2)) if delta_chi2 > 0 else 1.0
    
    print(f"  Fit results: chi2_null={chi2_null:.2f}, chi2_full={chi2_full:.2f}, delta_chi2={delta_chi2:.2f}")
    
    # 5. Output structured result
    result = {
        "schema": "htt.r38_planck_lowell_result/1",
        "program": "HTT-R38",
        "task_id": "R38-05-PLANCK-LOWELL",
        "status": "QUALIFIED_TRANSFER_CONDITIONAL",
        "claim_tier": "C0",
        "probe": "Planck PR4 Commander (NPIPE)",
        "source_map": "/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/COM_CMB_IQU-commander_4096_R4.00_full.fits",
        "data_dimension": dim,
        "mc_null_simulations_count": n_mc,
        "covariance": {
            "dimension": dim,
            "min_eigenvalue": cov_audit.min_eigenvalue,
            "condition_number": cov_audit.condition_number,
            "is_positive_definite": cov_audit.is_positive_definite,
        },
        "signal_rank": {
            "effective_rank": fit_res.effective_rank,
            "is_full_rank": fit_res.is_full_rank,
            "singular_values": list(fit_res.singular_values),
        },
        "fit": {
            "chi2_null": chi2_null,
            "chi2_full": chi2_full,
            "delta_chi2": delta_chi2,
            "p_value_conditional": p_val,
            "fitted_coefficients": fit_res.coefficients.tolist(),
            "parameter_covariance": fit_res.parameter_covariance.tolist(),
        },
        "caveat": "Planck PR4 Commander and PR3 SMICA are processing alternatives on the same CMB sky; not independent realizations.",
    }
    
    out_json = DOCS_R38 / "PLANCK_LOWELL_RESULT.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Wrote {out_json}")
    
    # Write diagnostics
    diag_summary = {
        "E_obs_norm": float(np.linalg.norm(E_obs)),
        "B_obs_norm": float(np.linalg.norm(B_obs)),
        "mc_variance_mean": float(np.mean(np.diag(cov_mc))),
        "orthogonal_identity_residual": fit_res.orthogonal_identity_residual,
    }
    with open(OUT_DIR / "diagnostics_summary.json", "w", encoding="utf-8") as f:
        json.dump(diag_summary, f, indent=2)
    print(f"Wrote {OUT_DIR / 'diagnostics_summary.json'}")
    print("Planck Low-Ell Analysis COMPLETE.")

if __name__ == "__main__":
    main()

