// Optical depth, visibility function, and reionisation postprocessing.
// BA-02: Split from thermo.rs (g, τ) + build_tau_and_g from peebles.rs.

use crate::core::constants::*;
use crate::core::math::clip;
use crate::recombination::peebles::{helium_contribution, reionization_fraction};
use numpy::{IntoPyArray, PyArray1};
use pyo3::prelude::*;

/// Compute optical depth τ(η) and normalised visibility function g(η)
/// from Thomson scattering rate τ̇ on a conformal-time grid.
///
/// τ is integrated backwards from the last grid point (τ(η_max) = 0).
/// g = τ̇ exp(−τ), then normalised so that ∫g dη = 1.
pub(crate) fn build_tau_and_g(eta_grid: &[f64], tau_dot: &[f64]) -> (Vec<f64>, Vec<f64>) {
    let n = eta_grid.len();
    let mut tau = vec![0.0; n];
    if n >= 2 {
        for i in (0..=(n - 2)).rev() {
            let deta = eta_grid[i + 1] - eta_grid[i];
            tau[i] = tau[i + 1] + 0.5 * (tau_dot[i] + tau_dot[i + 1]) * deta;
        }
    }

    let mut g: Vec<f64> = tau_dot.iter().zip(tau.iter()).map(|(td, t)| td * (-t).exp()).collect();
    let mut norm = 0.0;
    if n >= 2 {
        for i in 0..(n - 1) {
            norm += 0.5 * (g[i] + g[i + 1]) * (eta_grid[i + 1] - eta_grid[i]);
        }
    }
    if norm > 0.0 {
        for gi in g.iter_mut() {
            *gi /= norm;
        }
    }
    (tau, g)
}

#[pyfunction]
#[pyo3(signature=(t_cmb, n_h_0, z_grid, x_e_h, eta_grid, z_reio=7.67, dz_reio=0.5, z_heii=3.5, dz_heii=0.5))]
pub(crate) fn recombination_postprocess<'py>(
    py: Python<'py>, t_cmb: f64, n_h_0: f64, z_grid: Vec<f64>, x_e_h: Vec<f64>, eta_grid: Vec<f64>, z_reio: f64, dz_reio: f64, z_heii: f64, dz_heii: f64,
) -> PyResult<(Bound<'py, PyArray1<f64>>, f64, f64)> {
    let n = z_grid.len();
    if x_e_h.len() != n || eta_grid.len() != n { return Err(pyo3::exceptions::PyValueError::new_err("z_grid, x_e_h, eta_grid must have matching lengths")); }
    let f_he = Y_P / (4.0 * X_P);
    let mut x_e_total = Vec::with_capacity(n); let mut tau_dot_vec = Vec::with_capacity(n);
    for i in 0..n {
        let z = z_grid[i]; let xh = clip(x_e_h[i], 1e-15, 1.0); let xhe_pre = helium_contribution(t_cmb, n_h_0, z, xh); let x_pre = clip(xh + xhe_pre, 1e-15, X_E_MAX);
        let xh_reio = reionization_fraction(z, z_reio, dz_reio); let xheii_reio = reionization_fraction(z, z_heii, dz_heii); let x_reio_total = xh_reio + f_he * xh_reio + f_he * xheii_reio;
        let xt = clip(x_pre.max(x_reio_total), 1e-15, X_E_MAX); let a = 1.0 / (1.0 + z); let n_e = xt * n_h_0 * (1.0 + z).powi(3); let td = n_e * SIGMA_T * a * MPC; x_e_total.push(xt); tau_dot_vec.push(td);
    }
    let (_tau, g) = build_tau_and_g(&eta_grid, &tau_dot_vec); let mut i_peak = 0usize; let mut g_peak = -1.0f64;
    for i in 0..n { if g[i] > g_peak { g_peak = g[i]; i_peak = i; } }
    let z_star = z_grid[i_peak]; let g_half = 0.5 * g_peak; let mut first: Option<f64> = None; let mut last: Option<f64> = None;
    for i in 0..n { let z = z_grid[i]; if z > 800.0 && z < 1400.0 && g[i] >= g_half { if first.is_none() { first = Some(z); } last = Some(z); } }
    let delta_z = match (first, last) { (Some(f), Some(l)) if (f - l).abs() > 0.0 => f - l, _ => 80.0, };
    Ok((x_e_total.into_pyarray_bound(py), z_star, delta_z))
}

#[pyfunction]
pub(crate) fn legacy_visibility_eta_grid<'py>(
    py: Python<'py>,
    z_grid: Vec<f64>,
    h0_mpc: f64,
    omega_m: f64,
    omega_r: f64,
    omega_k: f64,
    omega_lambda: f64,
) -> PyResult<(
    Bound<'py, numpy::PyArray1<f64>>,
    Bound<'py, numpy::PyArray1<f64>>,
)> {
    let n = z_grid.len();
    let mut h_grid = Vec::with_capacity(n);
    for &z in z_grid.iter() {
        let zp1 = 1.0 + z;
        let e2 = omega_r * zp1.powi(4) + omega_m * zp1.powi(3) + omega_k * zp1.powi(2) + omega_lambda;
        h_grid.push(h0_mpc * e2.max(1e-300).sqrt());
    }
    let mut lookback = vec![0.0; n];
    if n >= 2 {
        for i in 1..n {
            let dz = z_grid[i] - z_grid[i - 1];
            let deta_dz_im1 = 299792.458 / h_grid[i - 1].max(1e-300);
            let deta_dz_i = 299792.458 / h_grid[i].max(1e-300);
            lookback[i] = lookback[i - 1] + 0.5 * (deta_dz_im1 + deta_dz_i) * dz;
        }
    }
    let eta0 = if n > 0 { lookback[n - 1] } else { 0.0 };
    let eta_grid: Vec<f64> = lookback.into_iter().map(|x| eta0 - x).collect();
    Ok((
        h_grid.into_pyarray_bound(py),
        eta_grid.into_pyarray_bound(py),
    ))
}

#[pyfunction]
pub(crate) fn visibility_profile<'py>(
    py: Python<'py>,
    z_grid: Vec<f64>,
    eta_grid: Vec<f64>,
    x_e_peebles: Vec<f64>,
    n_h_0: f64,
    z_reio: f64,
    dz_reio: f64,
) -> PyResult<(
    Bound<'py, numpy::PyArray1<f64>>,
    Bound<'py, numpy::PyArray1<f64>>,
    Bound<'py, numpy::PyArray1<f64>>,
    Bound<'py, numpy::PyArray1<f64>>,
    f64,
    f64,
)> {
    let n = z_grid.len();
    if eta_grid.len() != n || x_e_peebles.len() != n {
        return Err(pyo3::exceptions::PyValueError::new_err("z_grid, eta_grid, x_e_peebles must have matching lengths"));
    }
    let mut x_e_total = Vec::with_capacity(n);
    let mut tau_dot_vec = Vec::with_capacity(n);
    for i in 0..n {
        let z = z_grid[i];
        let x_reio = 0.5 * (1.0 + ((z_reio - z) / dz_reio).tanh());
        let xt = x_e_peebles[i].max(x_reio);
        let a = 1.0 / (1.0 + z);
        let n_e = xt * n_h_0 * (1.0 + z).powi(3);
        let td = n_e * SIGMA_T * a * MPC;
        x_e_total.push(xt);
        tau_dot_vec.push(td);
    }
    let (tau, g) = build_tau_and_g(&eta_grid, &tau_dot_vec);
    let mut i_peak = 0usize;
    let mut g_peak = -1.0f64;
    for i in 0..n {
        if z_grid[i] > 500.0 && g[i] > g_peak {
            g_peak = g[i];
            i_peak = i;
        }
    }
    if g_peak < 0.0 {
        for (i, &gv) in g.iter().enumerate() {
            if gv > g_peak {
                g_peak = gv;
                i_peak = i;
            }
        }
    }
    Ok((
        tau_dot_vec.into_pyarray_bound(py),
        tau.into_pyarray_bound(py),
        g.into_pyarray_bound(py),
        x_e_total.into_pyarray_bound(py),
        eta_grid[i_peak],
        z_grid[i_peak],
    ))
}
