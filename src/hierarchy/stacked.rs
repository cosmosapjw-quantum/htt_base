// Stacked native solver.

use crate::core::config::*;
use crate::core::constants::*;
use crate::hierarchy::coupling::*;
use crate::solver::rodas5p::*;
use crate::solver::block_diag::*;
use crate::solver::stacked::*;
use super::polarised::*;
use super::multispecies::*;
use numpy::{IntoPyArray, PyArray2};
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::time::Instant;

pub(crate) fn stacked_layout_offsets(ell_max_gamma: usize, ell_max_nu: usize, ell_max_pol: usize) -> (usize, usize, usize, usize, usize, usize, usize) {
    let n_gamma = ell_max_gamma + 1;
    let n_nu = ell_max_nu + 1;
    let n_e = ell_max_pol + 1;
    let off_f = 0usize;
    let off_vb = n_gamma;
    let off_n = off_vb + 1;
    let off_dc = off_n + n_nu;
    let off_vc = off_dc + 1;
    let off_e = off_vc + 1;
    let n_state = off_e + n_e;
    (off_f, off_vb, off_n, off_dc, off_vc, off_e, n_state)
}

pub(crate) fn build_toy_stacked_real_block_matrix(eta_now: f64, ell_max_gamma: usize, ell_max_nu: usize, ell_max_pol: usize, sigma_scale: f64, tau_base: f64) -> (Vec<f64>, usize, usize, usize, usize, usize, usize, usize) {
    let (_off_f, off_vb, off_n, off_dc, off_vc, off_e, n_state) = stacked_layout_offsets(ell_max_gamma, ell_max_nu, ell_max_pol);
    let n_real = 2 * n_state;
    let mut mat = vec![0.0; n_real * n_real];
    let damp = tau_base * (1.0 + 0.05 * eta_now);

    for i in 0..n_state {
        set_real_block_entry(&mut mat, n_state, i, i, -damp, 0.0);
    }

    // Photon ladder F_l <-> F_{l±2}
    for ell in 0..=ell_max_gamma {
        let idx = ell;
        if ell >= 2 {
            set_real_block_entry(&mut mat, n_state, idx, idx - 2, 0.03 * sigma_scale / 2.0, 0.0);
        }
        if ell + 2 <= ell_max_gamma {
            set_real_block_entry(&mut mat, n_state, idx, idx + 2, 0.03 * sigma_scale / 2.0, 0.0);
        }
    }

    // Baryon coupling to photon dipole
    if ell_max_gamma >= 1 {
        let f1 = 1usize;
        set_real_block_entry(&mut mat, n_state, f1, off_vb, 0.15 * sigma_scale, 0.0);
        set_real_block_entry(&mut mat, n_state, off_vb, f1, 0.12 * sigma_scale, 0.0);
    }

    // Neutrino ladder
    for ell in 0..=ell_max_nu {
        let idx = off_n + ell;
        if ell >= 2 {
            set_real_block_entry(&mut mat, n_state, idx, idx - 2, 0.02 * sigma_scale / 2.0, 0.0);
        }
        if ell + 2 <= ell_max_nu {
            set_real_block_entry(&mut mat, n_state, idx, idx + 2, 0.02 * sigma_scale / 2.0, 0.0);
        }
    }

    // CDM sector
    set_real_block_entry(&mut mat, n_state, off_dc, off_vc, -0.2, 0.0);
    set_real_block_entry(&mut mat, n_state, off_vc, off_dc, 0.05, 0.0);

    // Polarisation ladder and Thomson-like source couplings
    for ell in 0..=ell_max_pol {
        let idx = off_e + ell;
        if ell >= 2 {
            set_real_block_entry(&mut mat, n_state, idx, idx - 2, 0.025 * sigma_scale / 2.0, 0.0);
        }
        if ell + 2 <= ell_max_pol {
            set_real_block_entry(&mut mat, n_state, idx, idx + 2, 0.025 * sigma_scale / 2.0, 0.0);
        }
    }
    if ell_max_gamma >= 2 {
        let f2 = 2usize;
        let e0 = off_e;
        set_real_block_entry(&mut mat, n_state, f2, e0, 0.05 * sigma_scale, 0.0);
        set_real_block_entry(&mut mat, n_state, e0, f2, 0.05 * sigma_scale, 0.0);
        if ell_max_pol >= 2 {
            let e2 = off_e + 2;
            set_real_block_entry(&mut mat, n_state, f2, e2, 0.08 * sigma_scale, 0.0);
            set_real_block_entry(&mut mat, n_state, e2, f2, 0.08 * sigma_scale, 0.0);
            set_real_block_entry(&mut mat, n_state, e2, e0, 0.04 * sigma_scale, 0.0);
            set_real_block_entry(&mut mat, n_state, e0, e2, 0.04 * sigma_scale, 0.0);
        }
    }

    (mat, off_vb, off_n, off_dc, off_vc, off_e, n_state, n_real)
}


pub(crate) fn select_complex_output(out: &[Vec<f64>], n_complex_state: usize, selected_complex_indices: &[usize]) -> Result<Vec<Vec<f64>>, String> {
    for &idx in selected_complex_indices.iter() {
        if idx >= n_complex_state {
            return Err(format!("selected complex index {} out of range 0..{}", idx, n_complex_state.saturating_sub(1)));
        }
    }
    let mut reduced = Vec::with_capacity(out.len());
    for row in out.iter() {
        let mut dst = Vec::with_capacity(2 * selected_complex_indices.len());
        for &idx in selected_complex_indices.iter() {
            dst.push(row[idx]);
        }
        for &idx in selected_complex_indices.iter() {
            dst.push(row[idx + n_complex_state]);
        }
        reduced.push(dst);
    }
    Ok(reduced)
}

#[pyfunction]
#[pyo3(signature=(eta_profile, eta_eval, ell_max_gamma, ell_max_nu, ell_max_pol, include_polarisation, k_over_s, sigma_h_scale, sigma_h_grid, sqrt_h_grid, delta_n_grid, tau_dot_grid, calh_grid, r_grid, y0, selected_complex_indices=Vec::new(), rtol=1e-8, atol=1e-10, h_init=None, h_min=1e-8, h_max=10.0, max_steps=200000, f_safety=STACKED_F_SAFETY, use_blas_lu=false, use_block_diag=true))]
pub(crate) fn solve_stacked_native_rodas5p<'py>(py: Python<'py>, eta_profile: Vec<f64>, eta_eval: Vec<f64>, ell_max_gamma: usize, ell_max_nu: usize, ell_max_pol: usize, include_polarisation: bool, k_over_s: f64, sigma_h_scale: f64, sigma_h_grid: Vec<f64>, sqrt_h_grid: Vec<f64>, delta_n_grid: Vec<f64>, tau_dot_grid: Vec<f64>, calh_grid: Vec<f64>, r_grid: Vec<f64>, y0: Vec<f64>, selected_complex_indices: Vec<usize>, rtol: f64, atol: f64, h_init: Option<f64>, h_min: f64, h_max: f64, max_steps: usize, f_safety: f64, use_blas_lu: bool, use_block_diag: bool) -> PyResult<Bound<'py, PyDict>> {
    let cfg = Rodas5PConfig { rtol, atol, max_steps, h_init, h_min, h_max, f_safety, f_min: DEFAULT_F_MIN, f_max: DEFAULT_F_MAX, beta: DEFAULT_BETA, use_analytic_jacobian: true, use_ft_term: false, use_blas_lu, use_block_diag: use_block_diag, ell_max_gamma_hint: ell_max_gamma, ell_max_nu_hint: ell_max_nu, ell_max_pol_hint: if include_polarisation { ell_max_pol } else { 0 }, include_pol_hint: include_polarisation, use_sparse: false };
    let t_total = Instant::now();
    let (out, stats, n_total, timing, method_name, cdiag) = if include_polarisation {
        if selected_complex_indices.is_empty() {
            let (out, stats, n_total, timing, cdiag) = integrate_polarised_native_rodas5p(&eta_profile, &eta_eval, ell_max_gamma, ell_max_pol, ell_max_nu, k_over_s, sigma_h_scale, &sigma_h_grid, &tau_dot_grid, &calh_grid, &r_grid, &y0, &cfg).map_err(pyo3::exceptions::PyRuntimeError::new_err)?;
            (out, stats, n_total, timing, "Rodas5P-Rust-stacked-native-polarised", cdiag)
        } else {
            let (out, stats, n_total, timing, cdiag) = integrate_polarised_native_rodas5p_selected(&eta_profile, &eta_eval, ell_max_gamma, ell_max_pol, ell_max_nu, k_over_s, sigma_h_scale, &sigma_h_grid, &tau_dot_grid, &calh_grid, &r_grid, &y0, &selected_complex_indices, &cfg).map_err(pyo3::exceptions::PyRuntimeError::new_err)?;
            (out, stats, n_total, timing, "Rodas5P-Rust-stacked-native-polarised", cdiag)
        }
    } else {
        if selected_complex_indices.is_empty() {
            let (out, stats, n_total, timing, cdiag) = integrate_multispecies_native_rodas5p(&eta_profile, &eta_eval, ell_max_gamma, ell_max_nu, k_over_s, sigma_h_scale, &sigma_h_grid, &sqrt_h_grid, &delta_n_grid, &tau_dot_grid, &calh_grid, &r_grid, &y0, &cfg).map_err(pyo3::exceptions::PyRuntimeError::new_err)?;
            (out, stats, n_total, timing, "Rodas5P-Rust-stacked-native", cdiag)
        } else {
            let (out, stats, n_total, timing, cdiag) = integrate_multispecies_native_rodas5p_selected(&eta_profile, &eta_eval, ell_max_gamma, ell_max_nu, k_over_s, sigma_h_scale, &sigma_h_grid, &sqrt_h_grid, &delta_n_grid, &tau_dot_grid, &calh_grid, &r_grid, &y0, &selected_complex_indices, &cfg).map_err(pyo3::exceptions::PyRuntimeError::new_err)?;
            (out, stats, n_total, timing, "Rodas5P-Rust-stacked-native", cdiag)
        }
    };
    let out_reduced = if selected_complex_indices.is_empty() { out } else { out };
    let arr = PyArray2::from_vec2_bound(py, &out_reduced)?;
    let out_dict = PyDict::new_bound(py);
    out_dict.set_item("y", arr)?;
    out_dict.set_item("n_steps", stats.n_steps)?;
    out_dict.set_item("n_rejected", stats.n_rejected)?;
    out_dict.set_item("n_jac", stats.n_jac)?;
    out_dict.set_item("n_f_eval", stats.n_f_eval)?;
    out_dict.set_item("h_final", stats.h_final)?;
    out_dict.set_item("matrix_build_s", timing.matrix_build_s)?;
    out_dict.set_item("integrate_s", timing.integrate_s)?;
    out_dict.set_item("rust_total_s", t_total.elapsed().as_secs_f64())?;
    out_dict.set_item("method", method_name)?;
    out_dict.set_item("n_state", 2 * n_total)?;
    out_dict.set_item("n_complex_state", n_total)?;
    out_dict.set_item("include_polarisation", include_polarisation)?;
    out_dict.set_item("selected_complex_indices", selected_complex_indices)?;
    out_dict.set_item("f_safety", f_safety)?;
    out_dict.set_item("use_blas_lu", use_blas_lu)?;
    out_dict.set_item("use_block_diag", use_block_diag)?;
    // PR-13A controller diagnostics
    out_dict.set_item("n_attempted", cdiag.n_attempted)?;
    out_dict.set_item("max_reject_streak", cdiag.max_reject_streak)?;
    out_dict.set_item("err_accepted_mean", cdiag.err_accepted_mean())?;
    out_dict.set_item("err_accepted_max", cdiag.err_accepted_max)?;
    out_dict.set_item("q_raw_mean", cdiag.q_raw_mean())?;
    out_dict.set_item("q_after_clip_mean", cdiag.q_after_clip_mean())?;
    out_dict.set_item("clip_fmin_count", cdiag.clip_fmin_count)?;
    out_dict.set_item("clip_fmax_count", cdiag.clip_fmax_count)?;
    out_dict.set_item("dt_accept_mean", cdiag.dt_accept_mean())?;
    out_dict.set_item("dt_reject_mean", cdiag.dt_reject_mean())?;
    Ok(out_dict)
}

#[pyfunction]
#[pyo3(signature=(eta_profile, ell_max_gamma, ell_max_nu, ell_max_pol, sigma_scale=1.0, tau_base=2.0))]
pub(crate) fn stacked_operator_toy_profile<'py>(
    py: Python<'py>,
    eta_profile: Vec<f64>,
    ell_max_gamma: usize,
    ell_max_nu: usize,
    ell_max_pol: usize,
    sigma_scale: f64,
    tau_base: f64,
) -> PyResult<Bound<'py, PyDict>> {
    if eta_profile.len() < 2 {
        return Err(pyo3::exceptions::PyValueError::new_err("eta_profile must contain at least two samples"));
    }
    let mut mats_flat = Vec::new();
    let mut off_vb = 0usize;
    let mut off_n = 0usize;
    let mut off_dc = 0usize;
    let mut off_vc = 0usize;
    let mut off_e = 0usize;
    let mut n_state = 0usize;
    let mut n_state_real = 0usize;
    for &eta_now in eta_profile.iter() {
        let (mat, ovb, on, odc, ovc, oe, ns, nsr) = build_toy_stacked_real_block_matrix(eta_now, ell_max_gamma, ell_max_nu, ell_max_pol, sigma_scale, tau_base);
        off_vb = ovb; off_n = on; off_dc = odc; off_vc = ovc; off_e = oe; n_state = ns; n_state_real = nsr;
        mats_flat.extend_from_slice(&mat);
    }
    let out = PyDict::new_bound(py);
    out.set_item("matrices_flat", mats_flat.into_pyarray_bound(py))?;
    out.set_item("n_state_complex", n_state)?;
    out.set_item("n_state_real", n_state_real)?;
    out.set_item("off_vb", off_vb)?;
    out.set_item("off_N", off_n)?;
    out.set_item("off_dc", off_dc)?;
    out.set_item("off_vc", off_vc)?;
    out.set_item("off_E", off_e)?;
    Ok(out)
}

