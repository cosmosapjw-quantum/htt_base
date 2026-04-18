// Baryon-photon hierarchy.

use crate::core::config::*;
use crate::core::constants::*;
use crate::hierarchy::coupling::*;
use crate::solver::rodas5p::*;
use crate::solver::stacked::*;
use numpy::PyArray2;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::time::Instant;

pub(crate) fn build_baryon_photon_real_block_matrix(
    ell_max: usize,
    m: i32,
    k_over_s: f64,
    sigma_h: f64,
    sqrt_h: f64,
    delta_n: f64,
    tau_dot: f64,
    calh: f64,
    r_baryon: f64,
    alpha_damp: f64,
    n_damp: usize,
) -> Result<(Vec<f64>, usize), String> {
    let abs_m = (m.abs()) as usize;
    if abs_m > ell_max { return Err(format!("|m|={} exceeds ell_max={}", abs_m, ell_max)); }
    let n_ell = ell_max - abs_m + 1;
    let n_total = n_ell + 1;
    let n_real = 2 * n_total;
    let mut mat = vec![0.0; n_real * n_real];

    for i in 0..n_ell {
        let ell = abs_m + i;
        if ell >= 2 && i >= 2 {
            add_real_block_entry(&mut mat, n_total, i, i - 2, bp_shear_coupling_down(ell) * sigma_h, 0.0);
        }
        if i + 2 < n_ell {
            add_real_block_entry(&mut mat, n_total, i, i + 2, bp_shear_coupling_up(ell) * sigma_h, 0.0);
        }
        if ell >= 1 && i >= 1 {
            add_real_block_entry(&mut mat, n_total, i, i - 1, bp_streaming_coupling_down(ell) * k_over_s, 0.0);
        }
        if i + 1 < n_ell {
            add_real_block_entry(&mut mat, n_total, i, i + 1, bp_streaming_coupling_up(ell) * k_over_s, 0.0);
        }
        if sqrt_h != 0.0 || delta_n != 0.0 {
            if ell >= 1 && i >= 1 {
                let (re, im) = bp_advection_coefficient(m, ell, ell - 1, sqrt_h, delta_n);
                add_real_block_entry(&mut mat, n_total, i, i - 1, re, im);
            }
            if i + 1 < n_ell {
                let (re, im) = bp_advection_coefficient(m, ell, ell + 1, sqrt_h, delta_n);
                add_real_block_entry(&mut mat, n_total, i, i + 1, re, im);
            }
        }
        if ell >= 1 {
            let mut diag = -tau_dot;
            if ell == 2 { diag += tau_dot / 10.0; }
            add_real_block_entry(&mut mat, n_total, i, i, diag, 0.0);
        }
    }

    bp_apply_damping(&mut mat, n_total, ell_max, abs_m, alpha_damp, n_damp);

    let idx_ell1 = if abs_m <= 1 { Some(1usize - abs_m) } else { None };
    let vb_idx = n_ell;
    if let Some(f1_idx) = idx_ell1 {
        if f1_idx < n_ell {
            add_real_block_entry(&mut mat, n_total, f1_idx, vb_idx, tau_dot / 3.0, 0.0);
            if r_baryon > 0.0 {
                add_real_block_entry(&mut mat, n_total, vb_idx, f1_idx, 3.0 * tau_dot / r_baryon, 0.0);
                add_real_block_entry(&mut mat, n_total, vb_idx, vb_idx, -calh - tau_dot / r_baryon, 0.0);
            } else {
                add_real_block_entry(&mut mat, n_total, vb_idx, vb_idx, -calh, 0.0);
            }
        } else {
            add_real_block_entry(&mut mat, n_total, vb_idx, vb_idx, -calh, 0.0);
        }
    } else {
        add_real_block_entry(&mut mat, n_total, vb_idx, vb_idx, -calh, 0.0);
    }
    Ok((mat, 2 * n_total))
}

pub(crate) fn integrate_baryon_photon_native_rodas5p(
    eta_profile: &[f64],
    eta_eval: &[f64],
    ell_max: usize,
    m: i32,
    k_over_s: f64,
    sigma_h_scale: f64,
    sigma_h_grid: &[f64],
    sqrt_h_grid: &[f64],
    delta_n_grid: &[f64],
    tau_dot_grid: &[f64],
    calh_grid: &[f64],
    r_grid: &[f64],
    y0: &[f64],
    alpha_damp: f64,
    n_damp: usize,
    cfg: &Rodas5PConfig,
) -> Result<(Vec<Vec<f64>>, Rodas5PStats, usize), String> {
    let n_prof = eta_profile.len();
    if sigma_h_grid.len() != n_prof || sqrt_h_grid.len() != n_prof || delta_n_grid.len() != n_prof || tau_dot_grid.len() != n_prof || calh_grid.len() != n_prof || r_grid.len() != n_prof {
        return Err("baryon-photon native solver profile arrays must all match eta_profile length".to_string());
    }
    let abs_m = (m.abs()) as usize;
    if abs_m > ell_max { return Err(format!("|m|={} exceeds ell_max={}", abs_m, ell_max)); }
    let n_ell = ell_max - abs_m + 1;
    let n_total = n_ell + 1;
    let n_state = 2 * n_total;
    if y0.len() != n_state { return Err(format!("y0 must have length {} for ell_max={} and m={}", n_state, ell_max, m)); }

    let mut mats_flat: Vec<f64> = Vec::with_capacity(n_prof * n_state * n_state);
    for i in 0..n_prof {
        let (mat, n_state_local) = build_baryon_photon_real_block_matrix(
            ell_max,
            m,
            k_over_s,
            sigma_h_grid[i] * sigma_h_scale,
            sqrt_h_grid[i],
            delta_n_grid[i],
            tau_dot_grid[i],
            calh_grid[i],
            r_grid[i],
            alpha_damp,
            n_damp,
        )?;
        if n_state_local != n_state { return Err("native baryon-photon matrix state dimension mismatch".to_string()); }
        mats_flat.extend_from_slice(&mat);
    }
    let (out, stats, _cdiag) = integrate_linear_profile_rodas5p(eta_profile, &mats_flat, n_state, y0, eta_eval, cfg)?;
    Ok((out, stats, n_total))
}

#[pyfunction]
#[pyo3(signature=(eta_profile, eta_eval, ell_max, m, k_over_s, sigma_h_scale, sigma_h_grid, sqrt_h_grid, delta_n_grid, tau_dot_grid, calh_grid, r_grid, y0, alpha_damp=5.0, n_damp=5, rtol=1e-8, atol=1e-10, h_init=None, h_min=1e-8, h_max=10.0, max_steps=200000))]
pub(crate) fn solve_baryon_photon_native_rodas5p<'py>(
    py: Python<'py>,
    eta_profile: Vec<f64>,
    eta_eval: Vec<f64>,
    ell_max: usize,
    m: i32,
    k_over_s: f64,
    sigma_h_scale: f64,
    sigma_h_grid: Vec<f64>,
    sqrt_h_grid: Vec<f64>,
    delta_n_grid: Vec<f64>,
    tau_dot_grid: Vec<f64>,
    calh_grid: Vec<f64>,
    r_grid: Vec<f64>,
    y0: Vec<f64>,
    alpha_damp: f64,
    n_damp: usize,
    rtol: f64,
    atol: f64,
    h_init: Option<f64>,
    h_min: f64,
    h_max: f64,
    max_steps: usize,
) -> PyResult<Bound<'py, PyDict>> {
    let cfg = Rodas5PConfig { rtol, atol, max_steps, h_init, h_min, h_max, f_safety: DEFAULT_F_SAFETY, f_min: DEFAULT_F_MIN, f_max: DEFAULT_F_MAX, beta: DEFAULT_BETA, use_analytic_jacobian: true, use_ft_term: false, use_blas_lu: false, use_block_diag: false, ell_max_gamma_hint: 0, ell_max_nu_hint: 0, ell_max_pol_hint: 0, include_pol_hint: false, use_sparse: false };
    let (out, stats, n_total) = integrate_baryon_photon_native_rodas5p(
        &eta_profile,
        &eta_eval,
        ell_max,
        m,
        k_over_s,
        sigma_h_scale,
        &sigma_h_grid,
        &sqrt_h_grid,
        &delta_n_grid,
        &tau_dot_grid,
        &calh_grid,
        &r_grid,
        &y0,
        alpha_damp,
        n_damp,
        &cfg,
    ).map_err(pyo3::exceptions::PyRuntimeError::new_err)?;
    let arr = PyArray2::from_vec2_bound(py, &out)?;
    let out_dict = PyDict::new_bound(py);
    out_dict.set_item("y", arr)?;
    out_dict.set_item("n_steps", stats.n_steps)?;
    out_dict.set_item("n_rejected", stats.n_rejected)?;
    out_dict.set_item("n_jac", stats.n_jac)?;
    out_dict.set_item("n_f_eval", stats.n_f_eval)?;
    out_dict.set_item("h_final", stats.h_final)?;
    out_dict.set_item("method", "Rodas5P-Rust-baryon-photon-native")?;
    out_dict.set_item("n_state", 2 * n_total)?;
    out_dict.set_item("n_complex_state", n_total)?;
    Ok(out_dict)
}


