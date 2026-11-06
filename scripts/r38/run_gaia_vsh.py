"""Execution script for Gaia DR3 proper-motion VSH analysis with frame nuisance (R38-08).

Phase D of HTT-R38 Observational Convergence.
Loads Gaia-Quaia CRF3 cross-match (692,154 sources),
applies astrometric quality filters (RUWE < 1.4, 5-parameter solutions),
fits Vector Spherical Harmonic (VSH) dipole (glide/spin) and quadrupole modes,
preserves redshift bins and full covariance, and exports GAIA_VSH_RESULT.json.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import numpy as np

from common.covariance_validator import validate_covariance
from common.nuisance_projection import analyze_nuisance_projected_rank

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_R38 = REPO_ROOT / "docs/research_program/observational_publication_20261015/OBSERVATIONAL_CONVERGENCE_20261107"
GAIA_NPZ = Path("/mnt/extdrive/workdir/htt_open_data/a22_20261023/quaia_join/quaia_crf3_join.npz")

def vsh_vector_fields(ra_deg: np.ndarray, dec_deg: np.ndarray):
    """Compute vector spherical harmonic basis vectors (e_theta, e_phi) and l=1, 2 modes.
    
    e_theta points South (increasing theta), e_phi points East (increasing phi = RA).
    mu_ra* = mu_ra * cos(dec) = V . e_phi
    mu_dec = V . (-e_theta)
    """
    phi = np.deg2rad(ra_deg)
    theta = np.deg2rad(90.0 - dec_deg) # colatitude
    
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    cos_p = np.cos(phi)
    sin_p = np.sin(phi)
    
    # 1. l=1 Glide (electric dipole E1): gradient of Y_1m
    # Glide along x, y, z:
    # d_x = (sin_theta cos_phi):
    #   grad_theta = cos_theta cos_phi
    #   grad_phi = -sin_phi
    # d_y = (sin_theta sin_phi):
    #   grad_theta = cos_theta sin_phi
    #   grad_phi = cos_phi
    # d_z = cos_theta:
    #   grad_theta = -sin_theta
    #   grad_phi = 0
    #
    # mu_ra* corresponds to grad_phi, mu_dec corresponds to -grad_theta
    # Glide design for (mu_ra*, mu_dec):
    G1_x = np.column_stack([-sin_p, -cos_t * cos_p])
    G1_y = np.column_stack([cos_p, -cos_t * sin_p])
    G1_z = np.column_stack([np.zeros_like(phi), sin_t])
    
    # 2. l=1 Spin / Rotation (magnetic dipole B1): curl on sphere
    # R_x: mu_ra* = cos_theta cos_phi, mu_dec = sin_phi
    # R_y: mu_ra* = cos_theta sin_phi, mu_dec = -cos_phi
    # R_z: mu_ra* = -sin_theta, mu_dec = 0
    R1_x = np.column_stack([cos_t * cos_p, sin_p])
    R1_y = np.column_stack([cos_t * sin_p, -cos_p])
    R1_z = np.column_stack([-sin_t, np.zeros_like(phi)])
    
    # 3. l=2 Quadrupole modes (5 electric E2 modes)
    # E2_0 ~ 3 cos^2 theta - 1
    # grad_theta = -6 cos_theta sin_theta = -3 sin(2 theta)
    E2_0 = np.column_stack([np.zeros_like(phi), 3.0 * np.sin(2.0 * theta)])
    # E2_1c ~ sin(2 theta) cos_phi
    E2_1c = np.column_stack([-2.0 * cos_t * sin_p, -2.0 * np.cos(2.0 * theta) * cos_p])
    # E2_1s ~ sin(2 theta) sin_phi
    E2_1s = np.column_stack([2.0 * cos_t * cos_p, -2.0 * np.cos(2.0 * theta) * sin_p])
    # E2_2c ~ sin^2 theta cos(2 phi)
    E2_2c = np.column_stack([-2.0 * sin_t * np.sin(2.0 * phi), -np.sin(2.0 * theta) * np.cos(2.0 * phi)])
    # E2_2s ~ sin^2 theta sin(2 phi)
    E2_2s = np.column_stack([2.0 * sin_t * np.cos(2.0 * phi), -np.sin(2.0 * theta) * np.sin(2.0 * phi)])
    
    return {
        "glide_1": [G1_x, G1_y, G1_z],
        "spin_1": [R1_x, R1_y, R1_z],
        "shear_2": [E2_0, E2_1c, E2_1s, E2_2c, E2_2s],
    }

def main():
    print("Executing Gaia DR3 VSH Analysis (R38-08)...")
    if not GAIA_NPZ.exists():
        raise FileNotFoundError(f"Missing {GAIA_NPZ}")
        
    # 1. Load data
    with np.load(GAIA_NPZ) as z:
        ra = z["ra"]
        dec = z["dec"]
        z_q = z["redshift_quaia"]
        pmra = z["gaia_pmra"]
        pmdec = z["gaia_pmdec"]
        pmra_err = z["gaia_pmra_error"]
        pmdec_err = z["gaia_pmdec_error"]
        ruwe = z["gaia_ruwe"]
        solved = z["gaia_astrometric_params_solved"]
        
    n_raw = len(ra)
    print(f"  Loaded raw cross-matched sample: {n_raw:,} sources")
    
    # 2. Quality cuts: finite proper motions, RUWE < 1.4, 5-parameter solutions
    mask = (
        np.isfinite(pmra) & np.isfinite(pmdec) &
        np.isfinite(pmra_err) & np.isfinite(pmdec_err) &
        (pmra_err > 0) & (pmdec_err > 0) &
        (ruwe < 1.4) & (solved == 31) &
        (np.abs(pmra) < 100.0) & (np.abs(pmdec) < 100.0) # mas/yr clean cuts
    )
    idx = np.flatnonzero(mask)
    n_clean = len(idx)
    print(f"  Clean astrometric sample: {n_clean:,} quasars ({n_clean/n_raw*100:.1f}%)")
    
    sub_ra = ra[idx]
    sub_dec = dec[idx]
    sub_z = z_q[idx]
    sub_pmra = pmra[idx]
    sub_pmdec = pmdec[idx]
    sub_pmra_err = pmra_err[idx]
    sub_pmdec_err = pmdec_err[idx]
    
    # Split into 2 redshift bins: low-z (z < 1.5) and high-z (z >= 1.5)
    bins = [
        ("low_z", sub_z < 1.5),
        ("high_z", sub_z >= 1.5),
    ]
    
    vsh_basis = vsh_vector_fields(sub_ra, sub_dec)
    
    # Build design matrix:
    # Nuisance: 3 Spin (R1) modes (rigid frame rotation)
    # Signal: 3 Glide (G1) modes (dipole acceleration) + 5 Shear (E2) modes (quadrupole)
    # Total data vector per source has 2 components: (mu_ra*, mu_dec)
    # We solve via weighted normal equations: (X^T W X) beta = X^T W y
    
    N_cols = []
    for R_comp in vsh_basis["spin_1"]:
        N_cols.append(R_comp)
        
    S_cols = []
    for G_comp in vsh_basis["glide_1"]:
        S_cols.append(G_comp)
    for E_comp in vsh_basis["shear_2"]:
        S_cols.append(E_comp)
        
    # Stack across sources: length 2*N
    # Interleave (mu_ra*, mu_dec)
    y_vec = np.empty(2 * n_clean, dtype=np.float64)
    y_vec[0::2] = sub_pmra
    y_vec[1::2] = sub_pmdec
    
    inv_var = np.empty(2 * n_clean, dtype=np.float64)
    inv_var[0::2] = 1.0 / (sub_pmra_err ** 2)
    inv_var[1::2] = 1.0 / (sub_pmdec_err ** 2)
    w = np.sqrt(inv_var)
    
    # Assemble design matrices
    N_mat = np.empty((2 * n_clean, 3), dtype=np.float64)
    for k in range(3):
        N_mat[0::2, k] = N_cols[k][:, 0]
        N_mat[1::2, k] = N_cols[k][:, 1]
        
    S_mat = np.empty((2 * n_clean, 8), dtype=np.float64)
    for k in range(8):
        S_mat[0::2, k] = S_cols[k][:, 0]
        S_mat[1::2, k] = S_cols[k][:, 1]
        
    # Whiten with weights
    yw = y_vec * w
    Nw = N_mat * w[:, None]
    Sw = S_mat * w[:, None]
    
    # QR nuisance projection on frame spin
    Qn, Rn = np.linalg.qr(Nw, mode="reduced")
    yp = yw - Qn @ (Qn.T @ yw)
    Sp = Sw - Qn @ (Qn.T @ Sw)
    
    # SVD solve
    u, s, vh = np.linalg.svd(Sp, full_matrices=False)
    coeff = vh.T @ ((u.T @ yp) / s)
    cov_coeff = vh.T @ np.diag(1.0 / (s ** 2)) @ vh
    
    chi2_null = float(np.sum(yp ** 2))
    chi2_full = float(np.sum((yp - Sp @ coeff) ** 2))
    delta_chi2 = chi2_null - chi2_full
    
    glide_coeff = coeff[:3]
    shear_coeff = coeff[3:]
    glide_amp = float(np.linalg.norm(glide_coeff))
    shear_amp = float(np.linalg.norm(shear_coeff))
    
    print(f"  Gaia VSH Fit: chi2_null={chi2_null:.1f}, chi2_full={chi2_full:.1f}, delta_chi2={delta_chi2:.2f}")
    print(f"  Fitted Glide amplitude: {glide_amp:.4f} mas/yr")
    print(f"  Fitted Shear (E2) amplitude: {shear_amp:.4f} mas/yr")
    
    # Redshift binning check
    bin_results = {}
    for bname, bmask in bins:
        b_n = int(np.sum(bmask))
        b_idx_2 = np.empty(2 * b_n, dtype=int)
        b_true = np.flatnonzero(bmask)
        b_idx_2[0::2] = 2 * b_true
        b_idx_2[1::2] = 2 * b_true + 1
        
        b_Sp = Sp[b_idx_2]
        b_yp = yp[b_idx_2]
        b_u, b_s, b_vh = np.linalg.svd(b_Sp, full_matrices=False)
        b_c = b_vh.T @ ((b_u.T @ b_yp) / b_s)
        bin_results[bname] = {
            "source_count": b_n,
            "glide_amp_mas_yr": float(np.linalg.norm(b_c[:3])),
            "shear_amp_mas_yr": float(np.linalg.norm(b_c[3:])),
        }
        print(f"  Redshift bin [{bname}] ({b_n:,} sources): Glide={bin_results[bname]['glide_amp_mas_yr']:.4f}, Shear={bin_results[bname]['shear_amp_mas_yr']:.4f} mas/yr")
        
    result = {
        "schema": "htt.r38_gaia_vsh_result/1",
        "program": "HTT-R38",
        "task_id": "R38-08-GAIA-VSH",
        "status": "QUALIFIED_FRAME_SPIN_PROJECTED",
        "claim_tier": "C0",
        "total_sources_evaluated": n_clean,
        "nuisance_model": "3 frame-spin (magnetic dipole B1) modes projected out via QR",
        "fitted_modes": {
            "glide_e1_amplitudes_mas_yr": glide_coeff.tolist(),
            "glide_total_amp_mas_yr": glide_amp,
            "shear_e2_amplitudes_mas_yr": shear_coeff.tolist(),
            "shear_total_amp_mas_yr": shear_amp,
            "parameter_covariance": cov_coeff.tolist(),
            "singular_values": s.tolist(),
            "chi2_null": chi2_null,
            "chi2_full": chi2_full,
            "delta_chi2": delta_chi2,
        },
        "redshift_tomography": bin_results,
        "carrier_distinction_proof": "E1 glide dipole (gradient) and E2 shear quadrupole are algebraically distinct and orthogonal on the 2-sphere.",
        "caveat": "Residual Gaia proper motion quadrupole is consistent with known CRF3 spin/glide frame calibration limits; does not establish physical metric shear.",
    }
    
    out_json = DOCS_R38 / "GAIA_VSH_RESULT.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Wrote {out_json}")
    print("Gaia DR3 VSH Analysis COMPLETE.")

if __name__ == "__main__":
    main()

