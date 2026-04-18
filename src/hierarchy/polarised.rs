// Polarised hierarchy.

use crate::core::config::*;
use crate::core::constants::*;
use crate::hierarchy::coupling::*;
use crate::solver::rodas5p::*;
use crate::solver::block_diag::*;
use crate::solver::stacked::*;
use numpy::PyArray2;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::time::Instant;

pub(crate) fn build_polarised_real_block_matrix(
    ell_max_gamma: usize,
    ell_max_pol: usize,
    ell_max_nu: usize,
    k_over_s: f64,
    sigma_h: f64,
    tau_dot: f64,
    calh: f64,
    r_baryon: f64,
) -> Result<(Vec<f64>, usize, usize), String> {
    let n_g = ell_max_gamma + 1;
    let n_pol = ell_max_pol + 1;
    let n_nu = ell_max_nu + 1;
    let off_vb = n_g;
    let off_n = n_g + 1;
    let off_dc = n_g + 1 + n_nu;
    let off_vc = n_g + 1 + n_nu + 1;
    let off_e = n_g + 1 + n_nu + 2;
    let n_total = n_g + 1 + n_nu + 2 + n_pol;
    let n_real = 2 * n_total;
    let mut mat = vec![0.0; n_real * n_real];

    for i in 0..n_g {
        let ell = i;
        if i >= 2 {
            add_real_block_entry(&mut mat, n_total, i, i - 2, bp_shear_coupling_down(ell) * sigma_h, 0.0);
        }
        if i + 2 < n_g {
            add_real_block_entry(&mut mat, n_total, i, i + 2, bp_shear_coupling_up(ell) * sigma_h, 0.0);
        }
        if ell == 1 {
            add_real_block_entry(&mut mat, n_total, i, i, -tau_dot, 0.0);
            add_real_block_entry(&mut mat, n_total, i, off_vb, tau_dot / 3.0, 0.0);
        } else if ell == 2 {
            add_real_block_entry(&mut mat, n_total, i, i, -tau_dot + tau_dot / 10.0, 0.0);
            if n_pol > 0 {
                add_real_block_entry(&mut mat, n_total, i, off_e, tau_dot / 10.0, 0.0);
            }
            if n_pol > 2 {
                add_real_block_entry(&mut mat, n_total, i, off_e + 2, tau_dot / 10.0, 0.0);
            }
        } else if ell >= 3 {
            add_real_block_entry(&mut mat, n_total, i, i, -tau_dot, 0.0);
        }
    }

    add_real_block_entry(&mut mat, n_total, off_vb, off_vb, -calh, 0.0);
    if n_g > 1 && r_baryon > 0.0 {
        add_real_block_entry(&mut mat, n_total, off_vb, 1, 3.0 * tau_dot / r_baryon, 0.0);
        add_real_block_entry(&mut mat, n_total, off_vb, off_vb, -tau_dot / r_baryon, 0.0);
    }

    for i in 0..n_nu {
        let ell = i;
        let idx = off_n + i;
        if i >= 2 {
            add_real_block_entry(&mut mat, n_total, idx, off_n + i - 2, bp_shear_coupling_down(ell) * sigma_h, 0.0);
        }
        if i + 2 < n_nu {
            add_real_block_entry(&mut mat, n_total, idx, off_n + i + 2, bp_shear_coupling_up(ell) * sigma_h, 0.0);
        }
    }

    add_real_block_entry(&mut mat, n_total, off_dc, off_vc, -k_over_s, 0.0);
    add_real_block_entry(&mut mat, n_total, off_vc, off_vc, -calh, 0.0);

    for i in 0..n_pol {
        let ell = i;
        let idx = off_e + i;
        if i >= 2 {
            add_real_block_entry(&mut mat, n_total, idx, off_e + i - 2, bp_shear_coupling_down(ell) * sigma_h, 0.0);
        }
        if i + 2 < n_pol {
            add_real_block_entry(&mut mat, n_total, idx, off_e + i + 2, bp_shear_coupling_up(ell) * sigma_h, 0.0);
        }
        add_real_block_entry(&mut mat, n_total, idx, idx, -tau_dot, 0.0);
        if ell == 2 {
            if n_g > 2 {
                add_real_block_entry(&mut mat, n_total, idx, 2, tau_dot / 10.0, 0.0);
            }
            if n_pol > 0 {
                add_real_block_entry(&mut mat, n_total, idx, off_e, tau_dot / 10.0, 0.0);
            }
            add_real_block_entry(&mut mat, n_total, idx, idx, tau_dot / 10.0, 0.0);
        }
    }

    Ok((mat, 2 * n_total, n_total))
}

pub(crate) fn integrate_polarised_native_rodas5p(
    eta_profile: &[f64],
    eta_eval: &[f64],
    ell_max_gamma: usize,
    ell_max_pol: usize,
    ell_max_nu: usize,
    k_over_s: f64,
    sigma_h_scale: f64,
    sigma_h_grid: &[f64],
    tau_dot_grid: &[f64],
    calh_grid: &[f64],
    r_grid: &[f64],
    y0: &[f64],
    cfg: &Rodas5PConfig,
) -> Result<(Vec<Vec<f64>>, Rodas5PStats, usize, NativeSolveTiming, ControllerDiagnostics), String> {
    let n_prof = eta_profile.len();
    if sigma_h_grid.len() != n_prof || tau_dot_grid.len() != n_prof || calh_grid.len() != n_prof || r_grid.len() != n_prof {
        return Err("polarised native solver profile arrays must all match eta_profile length".to_string());
    }
    let n_total = (ell_max_gamma + 1) + 1 + (ell_max_nu + 1) + 2 + (ell_max_pol + 1);
    let n_state = 2 * n_total;
    if y0.len() != n_state {
        return Err(format!("y0 must have length {} for ell_max_gamma={}, ell_max_pol={}, ell_max_nu={}", n_state, ell_max_gamma, ell_max_pol, ell_max_nu));
    }
    let t_build = Instant::now();
    let mut mats_flat: Vec<f64> = Vec::with_capacity(n_prof * n_state * n_state);
    for i in 0..n_prof {
        let (mat, n_state_local, _) = build_polarised_real_block_matrix(
            ell_max_gamma,
            ell_max_pol,
            ell_max_nu,
            k_over_s,
            sigma_h_grid[i] * sigma_h_scale,
            tau_dot_grid[i],
            calh_grid[i],
            r_grid[i],
        )?;
        if n_state_local != n_state {
            return Err("native polarised matrix state dimension mismatch".to_string());
        }
        mats_flat.extend_from_slice(&mat);
    }
    let build_s = t_build.elapsed().as_secs_f64();
    let t_integrate = Instant::now();
    let (out, stats, cdiag) = if cfg.use_block_diag {
        let decomp = BlockDecomp::from_ell_max(cfg.ell_max_gamma_hint, cfg.ell_max_nu_hint, cfg.ell_max_pol_hint, cfg.include_pol_hint);
        integrate_linear_profile_rodas5p_blockdiag(eta_profile, &mats_flat, n_state, y0, eta_eval, cfg, &decomp)?
    } else {
        integrate_linear_profile_rodas5p(eta_profile, &mats_flat, n_state, y0, eta_eval, cfg)?
    };
    let integrate_s = t_integrate.elapsed().as_secs_f64();
    Ok((out, stats, n_total, NativeSolveTiming { matrix_build_s: build_s, integrate_s }, cdiag))
}

pub(crate) fn integrate_polarised_native_rodas5p_selected(
    eta_profile: &[f64], eta_eval: &[f64], ell_max_gamma: usize, ell_max_pol: usize, ell_max_nu: usize, k_over_s: f64, sigma_h_scale: f64, sigma_h_grid: &[f64], tau_dot_grid: &[f64], calh_grid: &[f64], r_grid: &[f64], y0: &[f64], selected_complex_indices: &[usize], cfg: &Rodas5PConfig,
) -> Result<(Vec<Vec<f64>>, Rodas5PStats, usize, NativeSolveTiming, ControllerDiagnostics), String> {
    let n_prof = eta_profile.len();
    if sigma_h_grid.len() != n_prof || tau_dot_grid.len() != n_prof || calh_grid.len() != n_prof || r_grid.len() != n_prof { return Err("polarised native solver profile arrays must all match eta_profile length".to_string()); }
    let n_total = (ell_max_gamma + 1) + 1 + (ell_max_nu + 1) + 2 + (ell_max_pol + 1);
    let n_state = 2 * n_total;
    if y0.len() != n_state { return Err(format!("y0 must have length {} for ell_max_gamma={}, ell_max_pol={}, ell_max_nu={}", n_state, ell_max_gamma, ell_max_pol, ell_max_nu)); }
    let t_build = Instant::now();
    let mut mats_flat: Vec<f64> = Vec::with_capacity(n_prof * n_state * n_state);
    for i in 0..n_prof {
        let (mat, n_state_local, _) = build_polarised_real_block_matrix(ell_max_gamma, ell_max_pol, ell_max_nu, k_over_s, sigma_h_grid[i] * sigma_h_scale, tau_dot_grid[i], calh_grid[i], r_grid[i])?;
        if n_state_local != n_state { return Err("native polarised matrix state dimension mismatch".to_string()); }
        mats_flat.extend_from_slice(&mat);
    }
    let build_s = t_build.elapsed().as_secs_f64();
    let mut selected_real_indices = Vec::with_capacity(2 * selected_complex_indices.len());
    for &idx in selected_complex_indices.iter() { selected_real_indices.push(idx); }
    for &idx in selected_complex_indices.iter() { selected_real_indices.push(idx + n_total); }
    let t_integrate = Instant::now();
    let (out, stats, cdiag) = if cfg.use_block_diag {
        let decomp = BlockDecomp::from_ell_max(cfg.ell_max_gamma_hint, cfg.ell_max_nu_hint, cfg.ell_max_pol_hint, cfg.include_pol_hint);
        integrate_linear_profile_rodas5p_selected_blockdiag(eta_profile, &mats_flat, n_state, y0, eta_eval, &selected_real_indices, cfg, &decomp)?
    } else {
        integrate_linear_profile_rodas5p_selected(eta_profile, &mats_flat, n_state, y0, eta_eval, &selected_real_indices, cfg)?
    };
    let integrate_s = t_integrate.elapsed().as_secs_f64();
    Ok((out, stats, n_total, NativeSolveTiming { matrix_build_s: build_s, integrate_s }, cdiag))
}

#[pyfunction]
#[pyo3(signature=(eta_profile, eta_eval, ell_max_gamma, ell_max_pol, ell_max_nu, k_over_s, sigma_h_scale, sigma_h_grid, tau_dot_grid, calh_grid, r_grid, y0, rtol=1e-8, atol=1e-10, h_init=None, h_min=1e-8, h_max=10.0, max_steps=200000))]
pub(crate) fn solve_polarised_native_rodas5p<'py>(
    py: Python<'py>,
    eta_profile: Vec<f64>,
    eta_eval: Vec<f64>,
    ell_max_gamma: usize,
    ell_max_pol: usize,
    ell_max_nu: usize,
    k_over_s: f64,
    sigma_h_scale: f64,
    sigma_h_grid: Vec<f64>,
    tau_dot_grid: Vec<f64>,
    calh_grid: Vec<f64>,
    r_grid: Vec<f64>,
    y0: Vec<f64>,
    rtol: f64,
    atol: f64,
    h_init: Option<f64>,
    h_min: f64,
    h_max: f64,
    max_steps: usize,
) -> PyResult<Bound<'py, PyDict>> {
    let cfg = Rodas5PConfig { rtol, atol, max_steps, h_init, h_min, h_max, f_safety: DEFAULT_F_SAFETY, f_min: DEFAULT_F_MIN, f_max: DEFAULT_F_MAX, beta: DEFAULT_BETA, use_analytic_jacobian: true, use_ft_term: false, use_blas_lu: false, use_block_diag: false, ell_max_gamma_hint: 0, ell_max_nu_hint: 0, ell_max_pol_hint: 0, include_pol_hint: false, use_sparse: false };
    let (out, stats, n_total, _timing, _cdiag) = integrate_polarised_native_rodas5p(
        &eta_profile,
        &eta_eval,
        ell_max_gamma,
        ell_max_pol,
        ell_max_nu,
        k_over_s,
        sigma_h_scale,
        &sigma_h_grid,
        &tau_dot_grid,
        &calh_grid,
        &r_grid,
        &y0,
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
    out_dict.set_item("method", "Rodas5P-Rust-polarised-native")?;
    out_dict.set_item("n_state", 2 * n_total)?;
    out_dict.set_item("n_complex_state", n_total)?;
    Ok(out_dict)
}

