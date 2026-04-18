// Python-exposed background, thermodynamics, and hierarchy solver.
// BA-02: Visibility functions moved to recombination/visibility.rs.

use crate::core::constants::*;
use crate::core::config::*;
use crate::core::math::*;
use crate::recombination::peebles::*;
use crate::core::controller::*;
use numpy::{IntoPyArray, PyArray1, PyArray2};
use pyo3::prelude::*;
use pyo3::types::PyDict;

#[pyfunction]
pub(crate) fn backend_name() -> &'static str {
    "bass_rs_scaffold_pr09"
}

#[pyfunction]
pub(crate) fn backend_ready() -> bool {
    false
}

#[pyfunction]
pub(crate) fn ping() -> &'static str {
    "bass_rs PR-09 scaffold alive"
}

#[pyfunction]
pub(crate) fn hubble_si_scalar(h0_si: f64, omega_r: f64, omega_m: f64, omega_k: f64, omega_lambda: f64, a: f64) -> f64 {
    let a2 = a * a;
    let e2 = omega_r / (a2 * a2) + omega_m / (a2 * a) + omega_k / a2 + omega_lambda;
    h0_si * e2.sqrt()
}

#[pyfunction]
pub(crate) fn temperature_history<'py>(py: Python<'py>, t_cmb: f64, z_grid: Vec<f64>) -> Bound<'py, PyArray1<f64>> {
    let out: Vec<f64> = z_grid.into_iter().map(|z| t_cmb * (1.0 + z)).collect();
    out.into_pyarray_bound(py)
}

#[pyfunction]
pub(crate) fn baryon_loading_history<'py>(py: Python<'py>, omega_b: f64, omega_gamma: f64, a_grid: Vec<f64>) -> Bound<'py, PyArray1<f64>> {
    let pref = 3.0 * omega_b / (4.0 * omega_gamma);
    let out: Vec<f64> = a_grid.into_iter().map(|a| pref * a).collect();
    out.into_pyarray_bound(py)
}

#[pyfunction]
pub(crate) fn background_grid<'py>(
    py: Python<'py>,
    h0_si: f64,
    h0_mpc: f64,
    omega_r: f64,
    omega_m: f64,
    omega_k: f64,
    omega_lambda: f64,
    a_min: f64,
    n_points: usize,
) -> PyResult<(Bound<'py, PyArray1<f64>>, Bound<'py, PyArray1<f64>>, Bound<'py, PyArray1<f64>>)> {
    let ln_a_min = a_min.ln();
    let mut a_grid = Vec::with_capacity(n_points);
    let mut h_grid = Vec::with_capacity(n_points);
    let mut eta_grid = Vec::with_capacity(n_points);
    let mut ln_a_grid = Vec::with_capacity(n_points);

    for i in 0..n_points {
        let t = if n_points <= 1 { 0.0 } else { i as f64 / (n_points as f64 - 1.0) };
        let ln_a = ln_a_min * (1.0 - t);
        let a = ln_a.exp();
        let a2 = a * a;
        let e2 = omega_r / (a2 * a2) + omega_m / (a2 * a) + omega_k / a2 + omega_lambda;
        let h = h0_si * e2.sqrt();
        a_grid.push(a);
        h_grid.push(h);
        ln_a_grid.push(ln_a);
    }

    let eta_init = a_min / (h0_mpc * omega_r.sqrt());
    eta_grid.push(eta_init);
    let mut eta_acc = eta_init;
    if n_points >= 2 {
        for i in 0..(n_points - 1) {
            let int_i = 299792458.0 / (a_grid[i] * h_grid[i]) / 3.085677581e22;
            let int_ip1 = 299792458.0 / (a_grid[i + 1] * h_grid[i + 1]) / 3.085677581e22;
            let dln = ln_a_grid[i + 1] - ln_a_grid[i];
            eta_acc += 0.5 * (int_i + int_ip1) * dln;
            eta_grid.push(eta_acc);
        }
    }

    Ok((
        a_grid.into_pyarray_bound(py),
        eta_grid.into_pyarray_bound(py),
        h_grid.into_pyarray_bound(py),
    ))
}

#[pyfunction]
#[pyo3(signature=(z_grid, h0_si, omega_b, omega_m, omega_r, omega_k, omega_lambda, t_cmb, x_init=None, rtol=1e-10, atol=1e-14, h_init=None, h_min=1e-14, h_max=5.0, max_steps=200000))]
pub(crate) fn solve_peebles_hydrogen_rodas5p<'py>(
    py: Python<'py>,
    z_grid: Vec<f64>,
    h0_si: f64,
    omega_b: f64,
    omega_m: f64,
    omega_r: f64,
    omega_k: f64,
    omega_lambda: f64,
    t_cmb: f64,
    x_init: Option<f64>,
    rtol: f64,
    atol: f64,
    h_init: Option<f64>,
    h_min: f64,
    h_max: f64,
    max_steps: usize,
) -> PyResult<(Bound<'py, PyArray1<f64>>, usize, usize, usize, f64, String)> {
    let params = PeeblesParams {
        h0_si,
        omega_b,
        omega_m,
        omega_r,
        omega_k,
        omega_lambda,
        t_cmb,
        n_h_0: n_h0_from_params(h0_si, omega_b),
    };
    let cfg = Rodas5PConfig {
        rtol,
        atol,
        max_steps,
        h_init,
        h_min,
        h_max,
        f_safety: DEFAULT_F_SAFETY,
        f_min: DEFAULT_F_MIN,
        f_max: DEFAULT_F_MAX,
        beta: DEFAULT_BETA,
        use_analytic_jacobian: true,
        use_ft_term: true,
        use_blas_lu: false, use_block_diag: false, ell_max_gamma_hint: 0, ell_max_nu_hint: 0, ell_max_pol_hint: 0, include_pol_hint: false, use_sparse: false,
    };
    let diag = integrate_peebles_on_grid(&z_grid, x_init, &params, &cfg)
        .map_err(pyo3::exceptions::PyRuntimeError::new_err)?;
    Ok((
        diag.out.into_pyarray_bound(py),
        diag.stats.n_steps,
        diag.stats.n_rejected,
        diag.stats.n_jac,
        diag.stats.h_final,
        "Rodas5P-Rust-scalar".to_string(),
    ))
}

#[pyfunction]
#[pyo3(signature=(z_grid, h0_si, omega_b, omega_m, omega_r, omega_k, omega_lambda, t_cmb, x_init=None, rtol=1e-10, atol=1e-14, h_init=None, h_min=1e-14, h_max=5.0, max_steps=200000, use_analytic_jacobian=true, use_ft_term=true))]
pub(crate) fn solve_peebles_hydrogen_rodas5p_diagnostics<'py>(
    py: Python<'py>, z_grid: Vec<f64>, h0_si: f64, omega_b: f64, omega_m: f64, omega_r: f64, omega_k: f64, omega_lambda: f64, t_cmb: f64,
    x_init: Option<f64>, rtol: f64, atol: f64, h_init: Option<f64>, h_min: f64, h_max: f64, max_steps: usize, use_analytic_jacobian: bool, use_ft_term: bool,
) -> PyResult<Bound<'py, PyDict>> {
    let params = PeeblesParams { h0_si, omega_b, omega_m, omega_r, omega_k, omega_lambda, t_cmb, n_h_0: n_h0_from_params(h0_si, omega_b) };
    let cfg = Rodas5PConfig { rtol, atol, max_steps, h_init, h_min, h_max, f_safety: DEFAULT_F_SAFETY, f_min: DEFAULT_F_MIN, f_max: DEFAULT_F_MAX, beta: DEFAULT_BETA, use_analytic_jacobian, use_ft_term, use_blas_lu: false, use_block_diag: false, ell_max_gamma_hint: 0, ell_max_nu_hint: 0, ell_max_pol_hint: 0, include_pol_hint: false, use_sparse: false };
    let diag = integrate_peebles_on_grid(&z_grid, x_init, &params, &cfg).map_err(pyo3::exceptions::PyRuntimeError::new_err)?;
    let out = PyDict::new_bound(py);
    out.set_item("x_e_h", diag.out.into_pyarray_bound(py))?;
    out.set_item("history_z", diag.history_z.into_pyarray_bound(py))?;
    out.set_item("history_y", diag.history_y.into_pyarray_bound(py))?;
    out.set_item("n_steps", diag.stats.n_steps)?;
    out.set_item("n_rejected", diag.stats.n_rejected)?;
    out.set_item("n_jac", diag.stats.n_jac)?;
    out.set_item("n_f_eval", diag.stats.n_f_eval)?;
    out.set_item("h_final", diag.stats.h_final)?;
    out.set_item("method", "Rodas5P-Rust-scalar")?;
    out.set_item("use_analytic_jacobian", use_analytic_jacobian)?;
    out.set_item("use_ft_term", use_ft_term)?;
    Ok(out)
}

#[pyfunction]
#[pyo3(signature=(z_grid, x_e_h_raw, z_target=1089.8, calib_scale=2.4, shift_weight=0.8, x_min=1e-10, x_max=1.0))]
pub(crate) fn calibrate_hydrogen_history<'py>(
    py: Python<'py>, z_grid: Vec<f64>, x_e_h_raw: Vec<f64>, z_target: f64, calib_scale: f64, shift_weight: f64, x_min: f64, x_max: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let n = z_grid.len();
    if x_e_h_raw.len() != n { return Err(pyo3::exceptions::PyValueError::new_err("z_grid and x_e_h_raw must have matching lengths")); }
    if n <= 1 { let out: Vec<f64> = x_e_h_raw.into_iter().map(|x| clip(x, x_min, x_max)).collect(); return Ok(out.into_pyarray_bound(py)); }
    let grad = gradient_abs_nonuniform(&z_grid, &x_e_h_raw); let mut i_mid = 0usize; let mut gmax = -1.0f64;
    for (i, &g) in grad.iter().enumerate() { if g > gmax { gmax = g; i_mid = i; } }
    let z_mid_raw = z_grid[i_mid]; let z_min = z_grid.iter().fold(f64::INFINITY, |a, &b| a.min(b)); let z_max = z_grid.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
    let mut z_inc: Vec<f64> = z_grid.iter().rev().copied().collect(); let y_inc: Vec<f64> = x_e_h_raw.iter().rev().map(|&x| clip(x, x_min, x_max)).collect();
    for i in 1..z_inc.len() { if z_inc[i] <= z_inc[i - 1] { z_inc[i] = z_inc[i - 1] + 1e-12; } }
    let y2 = natural_cubic_second_derivatives(&z_inc, &y_inc).map_err(pyo3::exceptions::PyRuntimeError::new_err)?;
    let mut out = Vec::with_capacity(n);
    for &z in z_grid.iter() { let z_in = clip(z_mid_raw + calib_scale * (z - z_target) + shift_weight * (z_target - z_mid_raw), z_min, z_max); out.push(clip(cubic_spline_eval(&z_inc, &y_inc, &y2, z_in), x_min, x_max)); }
    Ok(out.into_pyarray_bound(py))
}

// BA-02: recombination_postprocess, legacy_visibility_eta_grid, visibility_profile
// moved to recombination/visibility.rs.


const HIER_N_ELL: usize = 11;
const HIER_D: usize = HIER_N_ELL + 1;

#[derive(Clone, Copy)]
struct HierarchyBgSample {
    k_h: f64,
    dk_h_dn: f64,
    tau_dot: f64,
    dtau_dot_dn: f64,
    sigma: f64,
    dsigma_dn: f64,
    tilt_source: f64,
    dtilt_source_dn: f64,
}

struct HierarchyProfile {
    n_grid: Vec<f64>,
    k_h: Vec<f64>,
    tau_dot: Vec<f64>,
    sigma: Vec<f64>,
    tilt_source: Vec<f64>,
    dk_h_dn: Vec<f64>,
    dtau_dot_dn: Vec<f64>,
    dsigma_dn: Vec<f64>,
    dtilt_source_dn: Vec<f64>,
}

impl HierarchyProfile {
    fn new(
        n_grid: Vec<f64>,
        k_h: Vec<f64>,
        tau_dot: Vec<f64>,
        sigma: Vec<f64>,
        tilt_source: Vec<f64>,
    ) -> Result<Self, String> {
        let n = n_grid.len();
        if n < 2 { return Err("N grid must contain at least two points".to_string()); }
        if k_h.len() != n || tau_dot.len() != n || sigma.len() != n || tilt_source.len() != n {
            return Err("Hierarchy profile arrays must have matching lengths".to_string());
        }
        for i in 1..n {
            if n_grid[i] <= n_grid[i - 1] { return Err("N grid must be strictly increasing".to_string()); }
        }
        fn slopes(x: &[f64], y: &[f64]) -> Vec<f64> {
            let mut out = vec![0.0; y.len()];
            if y.len() <= 1 { return out; }
            for i in 0..(y.len() - 1) {
                out[i] = (y[i + 1] - y[i]) / (x[i + 1] - x[i]).max(1e-30);
            }
            out[y.len() - 1] = out[y.len() - 2];
            out
        }
        let dk_h_dn = slopes(&n_grid, &k_h);
        let dtau_dot_dn = slopes(&n_grid, &tau_dot);
        let dsigma_dn = slopes(&n_grid, &sigma);
        let dtilt_source_dn = slopes(&n_grid, &tilt_source);
        Ok(Self { n_grid, k_h, tau_dot, sigma, tilt_source, dk_h_dn, dtau_dot_dn, dsigma_dn, dtilt_source_dn })
    }

    fn locate_segment(&self, n: f64) -> usize {
        if n <= self.n_grid[0] { return 0; }
        let last = self.n_grid.len() - 1;
        if n >= self.n_grid[last] { return last - 1; }
        let mut klo = 0usize;
        let mut khi = last;
        while khi - klo > 1 {
            let k = (khi + klo) >> 1;
            if self.n_grid[k] > n { khi = k; } else { klo = k; }
        }
        klo.min(last - 1)
    }

    fn interp_pair(vals: &[f64], slopes: &[f64], x: &[f64], i: usize, xp: f64) -> (f64, f64) {
        let dx = xp - x[i];
        (vals[i] + slopes[i] * dx, slopes[i])
    }

    fn sample(&self, n: f64) -> HierarchyBgSample {
        let i = self.locate_segment(n);
        let j = if (n - self.n_grid[i]).abs() <= (self.n_grid[i + 1] - n).abs() { i } else { i + 1 };
        HierarchyBgSample {
            k_h: self.k_h[j],
            dk_h_dn: 0.0,
            tau_dot: self.tau_dot[j],
            dtau_dot_dn: 0.0,
            sigma: self.sigma[j],
            dsigma_dn: 0.0,
            tilt_source: self.tilt_source[j],
            dtilt_source_dn: 0.0,
        }
    }
}

pub(crate) fn hierarchy_err_norm(err_est: &[f64; HIER_D], y: &[f64; HIER_D], rtol: f64, atol: f64) -> f64 {
    let mut err = 0.0f64;
    for i in 0..HIER_N_ELL {
        let sc = atol + rtol * y[i].abs();
        err = err.max((err_est[i] / sc).abs());
    }
    err
}

pub(crate) fn mat_identity_scaled(scale: f64) -> [[f64; HIER_D]; HIER_D] {
    let mut out = [[0.0; HIER_D]; HIER_D];
    for i in 0..HIER_D { out[i][i] = scale; }
    out
}

pub(crate) fn gauss_solve(mut a: [[f64; HIER_D]; HIER_D], mut b: [f64; HIER_D]) -> Option<[f64; HIER_D]> {
    for k in 0..HIER_D {
        let mut piv = k;
        let mut piv_abs = a[k][k].abs();
        for i in (k + 1)..HIER_D {
            let cand = a[i][k].abs();
            if cand > piv_abs { piv = i; piv_abs = cand; }
        }
        if piv_abs < 1e-30 || !piv_abs.is_finite() { return None; }
        if piv != k { a.swap(k, piv); b.swap(k, piv); }
        let akk = a[k][k];
        for i in (k + 1)..HIER_D {
            let fac = a[i][k] / akk;
            a[i][k] = 0.0;
            for j in (k + 1)..HIER_D { a[i][j] -= fac * a[k][j]; }
            b[i] -= fac * b[k];
        }
    }
    let mut x = [0.0; HIER_D];
    for ii in 0..HIER_D {
        let i = HIER_D - 1 - ii;
        let mut sum = b[i];
        for j in (i + 1)..HIER_D { sum -= a[i][j] * x[j]; }
        let den = a[i][i];
        if den.abs() < 1e-30 || !den.is_finite() { return None; }
        x[i] = sum / den;
    }
    Some(x)
}

pub(crate) fn vec_add_scaled(base: &[f64; HIER_D], ks: &[[f64; HIER_D]; 8], coeffs: &[[f64; 8]; 8], i_stage: usize) -> [f64; HIER_D] {
    let mut out = *base;
    for j in 0..i_stage {
        let aij = coeffs[i_stage][j];
        if aij == 0.0 { continue; }
        for m in 0..HIER_D { out[m] += aij * ks[j][m]; }
    }
    out
}

pub(crate) fn c_sum_term(ks: &[[f64; HIER_D]; 8], coeffs: &[[f64; 8]; 8], i_stage: usize, h: f64) -> [f64; HIER_D] {
    let mut out = [0.0; HIER_D];
    for j in 0..i_stage {
        let cij = coeffs[i_stage][j];
        if cij == 0.0 { continue; }
        for m in 0..HIER_D { out[m] += cij * ks[j][m] / h; }
    }
    out
}

pub(crate) fn evaluate_hierarchy_autonomous_core(y: &[f64; HIER_D], bg: &HierarchyBgSample) -> ([f64; HIER_D], [[f64; HIER_D]; HIER_D]) {
    let mut rhs = [0.0; HIER_D];
    let mut jac = [[0.0; HIER_D]; HIER_D];
    let k_h = bg.k_h;
    let tau_dot = bg.tau_dot;
    rhs[0] = -(k_h / 3.0) * y[1];
    rhs[1] = k_h * (y[0] - 0.4 * y[2]) + bg.tilt_source * y[0];
    for ell in 2..HIER_N_ELL {
        let ellf = ell as f64;
        let lower = ellf / (2.0 * ellf - 1.0) * y[ell - 1];
        let coeff_upper = (ell as f64 + 1.0) / (2.0 * ell as f64 + 3.0);
        let upper = if ell < HIER_N_ELL - 1 { coeff_upper * y[ell + 1] } else { 0.0 };
        rhs[ell] = k_h * (lower - upper) - tau_dot * y[ell];
        if ell == 2 { rhs[2] += (8.0 / 15.0) * bg.sigma * y[0]; }
    }
    rhs[HIER_D - 1] = 1.0;
    jac[0][1] = -k_h / 3.0;
    jac[0][HIER_D - 1] = -(bg.dk_h_dn / 3.0) * y[1];
    jac[1][0] = k_h + bg.tilt_source;
    jac[1][2] = -0.4 * k_h;
    jac[1][HIER_D - 1] = bg.dk_h_dn * (y[0] - 0.4 * y[2]) + bg.dtilt_source_dn * y[0];
    for ell in 2..HIER_N_ELL {
        let ellf = ell as f64;
        jac[ell][ell] = -tau_dot;
        jac[ell][ell - 1] = k_h * ellf / (2.0 * ellf - 1.0);
        let coeff_upper = (ell as f64 + 1.0) / (2.0 * ell as f64 + 3.0);
        if ell < HIER_N_ELL - 1 { jac[ell][ell + 1] = -k_h * coeff_upper; }
        if ell == 2 { jac[2][0] = (8.0 / 15.0) * bg.sigma; }
        let lower_term = ellf / (2.0 * ellf - 1.0) * y[ell - 1];
        let upper_term = if ell < HIER_N_ELL - 1 { coeff_upper * y[ell + 1] } else { 0.0 };
        let mut d_rhs_dn = bg.dk_h_dn * (lower_term - upper_term) - bg.dtau_dot_dn * y[ell];
        if ell == 2 { d_rhs_dn += (8.0 / 15.0) * bg.dsigma_dn * y[0]; }
        jac[ell][HIER_D - 1] = d_rhs_dn;
    }
    (rhs, jac)
}

pub(crate) fn step_hierarchy_rodas5p(profile: &HierarchyProfile, y: &[f64; HIER_D], h: f64, cfg: &Rodas5PConfig, tab: &Rodas5PTableau) -> ([f64; HIER_D], f64, bool, usize) {
    let bg0 = profile.sample(y[HIER_D - 1]);
    let (_f0, j0) = evaluate_hierarchy_autonomous_core(y, &bg0);
    let mut w = mat_identity_scaled(1.0 / (tab.gamma * h));
    for i in 0..HIER_D { for j in 0..HIER_D { w[i][j] -= j0[i][j]; } }
    let mut ks = [[0.0; HIER_D]; 8];
    let mut n_f_eval = 0usize;
    for i_stage in 0..8 {
        let y_stage = vec_add_scaled(y, &ks, &tab.a, i_stage);
        let bg_stage = profile.sample(y_stage[HIER_D - 1]);
        let (f_stage, _j_stage) = evaluate_hierarchy_autonomous_core(&y_stage, &bg_stage);
        let csum = c_sum_term(&ks, &tab.c, i_stage, h);
        let mut rhs = [0.0; HIER_D];
        for m in 0..HIER_D { rhs[m] = f_stage[m] + csum[m]; }
        n_f_eval += 1;
        let Some(ki) = gauss_solve(w, rhs) else { return (*y, f64::INFINITY, false, n_f_eval); };
        ks[i_stage] = ki;
    }
    let mut y_new = *y;
    let mut err_est = [0.0; HIER_D];
    for i in 0..8 {
        for m in 0..HIER_D {
            y_new[m] += tab.b[i] * ks[i][m];
            err_est[m] += tab.bhat[i] * ks[i][m];
        }
    }
    y_new[HIER_D - 1] = y[HIER_D - 1] + h;
    err_est[HIER_D - 1] = 0.0;
    if !y_new.iter().all(|v| v.is_finite()) { return (*y, f64::INFINITY, false, n_f_eval); }
    let err = hierarchy_err_norm(&err_est, &y_new, cfg.rtol, cfg.atol);
    (y_new, err, true, n_f_eval)
}

pub(crate) fn interpolate_history_to_targets(history_n: &[f64], history_y: &[[f64; HIER_D]], target_n: &[f64]) -> Vec<[f64; HIER_N_ELL]> {
    let mut out = Vec::with_capacity(target_n.len());
    let mut j = 0usize;
    for &nt in target_n {
        while j + 1 < history_n.len() && history_n[j + 1] < nt { j += 1; }
        let mut row = [0.0; HIER_N_ELL];
        if j + 1 >= history_n.len() {
            for ell in 0..HIER_N_ELL { row[ell] = history_y[history_y.len() - 1][ell]; }
            out.push(row);
            continue;
        }
        let n0 = history_n[j];
        let n1 = history_n[j + 1];
        let w = if (n1 - n0).abs() < 1e-30 { 0.0 } else { (nt - n0) / (n1 - n0) };
        for ell in 0..HIER_N_ELL { row[ell] = history_y[j][ell] + w * (history_y[j + 1][ell] - history_y[j][ell]); }
        out.push(row);
    }
    out
}

pub(crate) fn integrate_hierarchy_autonomous_on_grid(
    n_grid: &[f64],
    k_h_grid: &[f64],
    tau_dot_grid: &[f64],
    sigma_grid: &[f64],
    tilt_source_grid: &[f64],
    theta0: &[f64],
    cfg: &Rodas5PConfig,
) -> Result<(Vec<[f64; HIER_N_ELL]>, Rodas5PStats), String> {
    if theta0.len() != HIER_N_ELL { return Err(format!("theta0 must have length {}", HIER_N_ELL)); }
    let profile = HierarchyProfile::new(n_grid.to_vec(), k_h_grid.to_vec(), tau_dot_grid.to_vec(), sigma_grid.to_vec(), tilt_source_grid.to_vec())?;
    let mut y = [0.0; HIER_D];
    for ell in 0..HIER_N_ELL { y[ell] = theta0[ell]; }
    y[HIER_D - 1] = n_grid[0];
    let n_start = n_grid[0];
    let n_end = *n_grid.last().unwrap();
    let tab = rodas5p_tableau();
    let mut h = cfg.h_init.unwrap_or_else(|| ((n_end - n_start).abs() / 200.0).max(cfg.h_min).min(cfg.h_max));
    let mut prev_err = 1.0;
    let mut n_steps = 0usize;
    let mut n_rejected = 0usize;
    let mut n_jac = 0usize;
    let mut n_f_eval = 0usize;
    let mut history_n = vec![n_start];
    let mut history_y = vec![y];
    while y[HIER_D - 1] < n_end - 1e-14 {
        if n_steps >= cfg.max_steps { return Err(format!("Max steps reached at N={}", y[HIER_D - 1])); }
        let remaining = n_end - y[HIER_D - 1];
        let h_try = h.min(remaining).max(cfg.h_min);
        n_jac += 1;
        let (y_new, err, ok, n_f_stage) = step_hierarchy_rodas5p(&profile, &y, h_try, cfg, &tab);
        n_f_eval += n_f_stage;
        if !ok || !err.is_finite() || err > 1.0 {
            n_rejected += 1;
            h = new_h(h, if err.is_finite() { err.max(2.0) } else { 10.0 }, prev_err, cfg);
            if h < cfg.h_min * 1.0001 { return Err(format!("h_min reached at N={}", y[HIER_D - 1])); }
            continue;
        }
        y = y_new;
        n_steps += 1;
        history_n.push(y[HIER_D - 1]);
        history_y.push(y);
        h = new_h(h, err, prev_err, cfg);
        prev_err = err.max(1e-30);
    }
    let out = interpolate_history_to_targets(&history_n, &history_y, n_grid);
    Ok((out, Rodas5PStats { n_steps, n_rejected, n_jac, n_f_eval, h_final: h }))
}

#[pyfunction]
#[pyo3(signature=(y, k_h, dk_h_dn, tau_dot, dtau_dot_dn, sigma, dsigma_dn, tilt_source=0.0, dtilt_source_dn=0.0))]
pub(crate) fn evaluate_hierarchy_autonomous<'py>(
    py: Python<'py>,
    y: Vec<f64>,
    k_h: f64,
    dk_h_dn: f64,
    tau_dot: f64,
    dtau_dot_dn: f64,
    sigma: f64,
    dsigma_dn: f64,
    tilt_source: f64,
    dtilt_source_dn: f64,
) -> PyResult<(Bound<'py, PyArray1<f64>>, Bound<'py, PyArray2<f64>>)> {
    if y.len() != HIER_D { return Err(pyo3::exceptions::PyValueError::new_err(format!("y must have length {}", HIER_D))); }
    let mut y_arr = [0.0; HIER_D];
    y_arr.copy_from_slice(&y);
    let bg = HierarchyBgSample { k_h, dk_h_dn, tau_dot, dtau_dot_dn, sigma, dsigma_dn, tilt_source, dtilt_source_dn };
    let (rhs, jac) = evaluate_hierarchy_autonomous_core(&y_arr, &bg);
    let rhs_vec = rhs.to_vec();
    let jac_vec: Vec<Vec<f64>> = jac.iter().map(|row| row.to_vec()).collect();
    let jac_arr = PyArray2::from_vec2_bound(py, &jac_vec)?;
    Ok((rhs_vec.into_pyarray_bound(py), jac_arr))
}

#[pyfunction]
#[pyo3(signature=(n_grid, k_h_grid, tau_dot_grid, sigma_grid, theta0, tilt_source_grid=None, rtol=1e-8, atol=1e-10, h_init=None, h_min=1e-8, h_max=0.2, max_steps=200000))]
pub(crate) fn solve_hierarchy_autonomous_rodas5p<'py>(
    py: Python<'py>,
    n_grid: Vec<f64>,
    k_h_grid: Vec<f64>,
    tau_dot_grid: Vec<f64>,
    sigma_grid: Vec<f64>,
    theta0: Vec<f64>,
    tilt_source_grid: Option<Vec<f64>>,
    rtol: f64,
    atol: f64,
    h_init: Option<f64>,
    h_min: f64,
    h_max: f64,
    max_steps: usize,
) -> PyResult<Bound<'py, PyDict>> {
    let n = n_grid.len();
    let tilt = tilt_source_grid.unwrap_or_else(|| vec![0.0; n]);
    let cfg = Rodas5PConfig { rtol, atol, max_steps, h_init, h_min, h_max, f_safety: DEFAULT_F_SAFETY, f_min: DEFAULT_F_MIN, f_max: DEFAULT_F_MAX, beta: DEFAULT_BETA, use_analytic_jacobian: true, use_ft_term: false, use_blas_lu: false, use_block_diag: false, ell_max_gamma_hint: 0, ell_max_nu_hint: 0, ell_max_pol_hint: 0, include_pol_hint: false, use_sparse: false };
    let (out, stats) = integrate_hierarchy_autonomous_on_grid(&n_grid, &k_h_grid, &tau_dot_grid, &sigma_grid, &tilt, &theta0, &cfg)
        .map_err(pyo3::exceptions::PyRuntimeError::new_err)?;
    let arr = PyArray2::from_vec2_bound(py, &out.iter().map(|r| r.to_vec()).collect::<Vec<_>>())?;
    let out_dict = PyDict::new_bound(py);
    out_dict.set_item("theta", arr)?;
    out_dict.set_item("n_steps", stats.n_steps)?;
    out_dict.set_item("n_rejected", stats.n_rejected)?;
    out_dict.set_item("n_jac", stats.n_jac)?;
    out_dict.set_item("n_f_eval", stats.n_f_eval)?;
    out_dict.set_item("h_final", stats.h_final)?;
    out_dict.set_item("method", "Rodas5P-Rust-hierarchy-autonomous")?;
    out_dict.set_item("ell_max_supported", HIER_N_ELL - 1)?;
    Ok(out_dict)
}


