// Generic linear profile solver pyfunction.

use crate::core::config::*;
use crate::core::constants::*;
use crate::solver::rodas5p::*;
use crate::solver::stacked::*;
use numpy::PyArray2;
use pyo3::prelude::*;
use pyo3::types::PyDict;

#[pyfunction]
#[pyo3(signature=(eta_profile, matrices_flat, n_state, y0, eta_eval, rtol=1e-8, atol=1e-10, h_init=None, h_min=1e-8, h_max=10.0, max_steps=200000))]
pub(crate) fn solve_linear_profile_rodas5p<'py>(
    py: Python<'py>,
    eta_profile: Vec<f64>,
    matrices_flat: Vec<f64>,
    n_state: usize,
    y0: Vec<f64>,
    eta_eval: Vec<f64>,
    rtol: f64,
    atol: f64,
    h_init: Option<f64>,
    h_min: f64,
    h_max: f64,
    max_steps: usize,
) -> PyResult<Bound<'py, PyDict>> {
    let cfg = Rodas5PConfig { rtol, atol, max_steps, h_init, h_min, h_max, f_safety: DEFAULT_F_SAFETY, f_min: DEFAULT_F_MIN, f_max: DEFAULT_F_MAX, beta: DEFAULT_BETA, use_analytic_jacobian: true, use_ft_term: false, use_blas_lu: false, use_block_diag: false, ell_max_gamma_hint: 0, ell_max_nu_hint: 0, ell_max_pol_hint: 0, include_pol_hint: false, use_sparse: false };
    let (out, stats, _cdiag) = integrate_linear_profile_rodas5p(&eta_profile, &matrices_flat, n_state, &y0, &eta_eval, &cfg)
        .map_err(pyo3::exceptions::PyRuntimeError::new_err)?;
    let arr = PyArray2::from_vec2_bound(py, &out)?;
    let out_dict = PyDict::new_bound(py);
    out_dict.set_item("y", arr)?;
    out_dict.set_item("n_steps", stats.n_steps)?;
    out_dict.set_item("n_rejected", stats.n_rejected)?;
    out_dict.set_item("n_jac", stats.n_jac)?;
    out_dict.set_item("n_f_eval", stats.n_f_eval)?;
    out_dict.set_item("h_final", stats.h_final)?;
    out_dict.set_item("method", "Rodas5P-Rust-linear-profile")?;
    out_dict.set_item("n_state", n_state)?;
    Ok(out_dict)
}



