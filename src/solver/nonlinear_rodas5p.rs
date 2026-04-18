//! Generic nonlinear Rodas5P solver for stiff ODE systems.
//!
//! Extends the existing linear-only Rodas5P infrastructure to handle:
//!   dy/dt = f(t, y)   (nonlinear, stiff)
//!
//! Two interfaces:
//!   1. ScalarOde: 1-DOF systems (no LU, just scalar division)
//!   2. SmallVectorOde<N>: N-DOF systems (N ≤ 16, stack-allocated)
//!
//! Physics from Hairer-Wanner II §IV.7: Rosenbrock stage equations
//!   (I/(γh) - J) k_i = f(t_n + α_i h, y_n + Σ a_{ij} k_j)
//!                      + J Σ_{j<i} (c_{ij}/h) k_j + γ h ft
//!
//! Key property: J evaluated ONCE at (t_n, y_n), stages are LINEAR solves.
//! For scalar: division. For 2×2: Cramer's rule. For N>2: LU.

use crate::core::config::{Rodas5PConfig, Rodas5PTableau, rodas5p_tableau};

// ═══════════════════════════════════════════════════════════════════
// Scalar ODE interface
// ═══════════════════════════════════════════════════════════════════

/// Trait for a scalar (1-DOF) ODE dy/dt = f(t, y).
pub(crate) trait ScalarOde {
    /// Right-hand side f(t, y).
    fn rhs(&self, t: f64, y: f64) -> f64;
    /// Jacobian df/dy at (t, y).
    fn jac(&self, t: f64, y: f64) -> f64;
    /// Time derivative df/dt at (t, y). Default: 0 (autonomous).
    fn dfdt(&self, _t: f64, _y: f64) -> f64 { 0.0 }
    /// Clip y to valid range. Default: no clipping.
    fn clip(&self, y: f64) -> f64 { y }
}

/// One Rodas5P step for a scalar ODE.
///
/// Returns (y_new, err_norm, ok, n_f_eval).
/// `h` is the signed step size (positive or negative depending on direction).
pub(crate) fn step_scalar_rodas5p<F: ScalarOde>(
    ode: &F, t: f64, y: f64, h: f64,
    cfg: &Rodas5PConfig, tab: &Rodas5PTableau,
) -> (f64, f64, bool, usize) {
    let j = ode.jac(t, y);
    let ft = if cfg.use_ft_term { ode.dfdt(t, y) } else { 0.0 };
    let w = 1.0 / (tab.gamma * h) - j;
    if !w.is_finite() || w.abs() < 1e-30 {
        return (y, f64::INFINITY, false, 0);
    }
    
    let mut k = [0.0_f64; 8];
    let mut n_f = 0usize;
    
    for i in 0..8 {
        let mut y_st = y;
        let mut c_sum = 0.0;
        for jj in 0..i {
            y_st += tab.a[i][jj] * k[jj];
            c_sum += tab.c[i][jj] * k[jj] / h;
        }
        let rhs = ode.rhs(t + h * alpha_i(i, tab), y_st) + c_sum + h * tab.gamma * ft;
        n_f += 1;
        let ki = rhs / w;
        if !ki.is_finite() {
            return (y, f64::INFINITY, false, n_f);
        }
        k[i] = ki;
    }
    
    let mut y_new = y;
    let mut err_raw = 0.0;
    for i in 0..8 {
        y_new += tab.b[i] * k[i];
        err_raw += tab.bhat[i] * k[i];
    }
    
    if !y_new.is_finite() {
        return (y, f64::INFINITY, false, n_f);
    }
    
    let y_clipped = ode.clip(y_new);
    let scale = cfg.atol + cfg.rtol * y_clipped.abs();
    let err = (err_raw / scale).abs();
    
    (y_clipped, err, true, n_f)
}

/// Compute α_i = Σ_j a_{ij} for stage i (fractional step).
fn alpha_i(i: usize, tab: &Rodas5PTableau) -> f64 {
    let mut s = 0.0;
    for j in 0..i { s += tab.a[i][j]; }
    s
}

// ═══════════════════════════════════════════════════════════════════
// Small-vector ODE interface (N ≤ 16)
// ═══════════════════════════════════════════════════════════════════

/// Trait for a small N-DOF ODE dy/dt = f(t, y).
pub(crate) trait SmallVectorOde {
    /// Dimension of the system.
    fn dim(&self) -> usize;
    /// Right-hand side f(t, y) → out.
    fn rhs(&self, t: f64, y: &[f64], out: &mut [f64]);
    /// Jacobian df/dy at (t, y) → out (row-major, n×n).
    fn jac(&self, t: f64, y: &[f64], out: &mut [f64]);
    /// Time derivative df/dt at (t, y) → out. Default: zero.
    fn dfdt(&self, _t: f64, _y: &[f64], out: &mut [f64]) {
        out.iter_mut().for_each(|v| *v = 0.0);
    }
    /// Clip y to valid range. Default: no clipping.
    fn clip(&self, y: &mut [f64]) {}
}

/// Scratch workspace for small-vector Rodas5P.
pub(crate) struct SmallRodas5PScratch {
    pub(crate) n: usize,
    k: Vec<[f64; 16]>,  // 8 stages × up to 16 DOF
    w_mat: [f64; 256],   // (I/γh - J), up to 16×16
    piv: [usize; 16],    // LU pivots
    f_buf: [f64; 16],
    ft_buf: [f64; 16],
    jac_buf: [f64; 256],
    y_st: [f64; 16],
    rhs_buf: [f64; 16],
}

impl SmallRodas5PScratch {
    pub(crate) fn new(n: usize) -> Self {
        assert!(n <= 16, "SmallRodas5PScratch: n must be ≤ 16");
        Self {
            n,
            k: vec![[0.0; 16]; 8],
            w_mat: [0.0; 256], piv: [0; 16],
            f_buf: [0.0; 16], ft_buf: [0.0; 16], jac_buf: [0.0; 256],
            y_st: [0.0; 16], rhs_buf: [0.0; 16],
        }
    }
}

/// One Rodas5P step for a small-vector ODE.
pub(crate) fn step_small_rodas5p<F: SmallVectorOde>(
    ode: &F, t: f64, y: &[f64], h: f64,
    cfg: &Rodas5PConfig, tab: &Rodas5PTableau, sc: &mut SmallRodas5PScratch,
) -> (Vec<f64>, f64, bool, usize) {
    let n = ode.dim();
    assert!(n <= 16 && n == sc.n);
    
    // Compute Jacobian and form W = I/(γh) - J
    ode.jac(t, y, &mut sc.jac_buf[..n*n]);
    let inv_gh = 1.0 / (tab.gamma * h);
    for i in 0..n {
        for j in 0..n {
            sc.w_mat[i * n + j] = -sc.jac_buf[i * n + j];
        }
        sc.w_mat[i * n + i] += inv_gh;
    }
    
    // LU factorize W
    if !lu_factor_small(&mut sc.w_mat, &mut sc.piv, n) {
        return (y.to_vec(), f64::INFINITY, false, 0);
    }
    
    // ft term
    if cfg.use_ft_term {
        ode.dfdt(t, y, &mut sc.ft_buf[..n]);
    } else {
        sc.ft_buf[..n].fill(0.0);
    }
    
    let mut n_f = 0usize;
    
    for i in 0..8 {
        // y_stage = y + Σ_{j<i} a[i][j] * k[j]
        sc.y_st[..n].copy_from_slice(&y[..n]);
        for jj in 0..i {
            for d in 0..n {
                sc.y_st[d] += tab.a[i][jj] * sc.k[jj][d];
            }
        }
        
        // RHS = f(t + α_i h, y_stage) + Σ_{j<i} c[i][j]/h * k[j] + γ h ft
        let t_stage = t + h * alpha_i(i, tab);
        ode.rhs(t_stage, &sc.y_st[..n], &mut sc.f_buf[..n]);
        n_f += 1;
        
        for d in 0..n {
            let mut c_sum = 0.0;
            for jj in 0..i {
                c_sum += tab.c[i][jj] * sc.k[jj][d] / h;
            }
            sc.rhs_buf[d] = sc.f_buf[d] + c_sum + h * tab.gamma * sc.ft_buf[d];
        }
        
        // Solve W * k_i = rhs
        lu_solve_small(&sc.w_mat, &sc.piv, &mut sc.rhs_buf, n);
        for d in 0..n { sc.k[i][d] = sc.rhs_buf[d]; }
    }
    
    // y_new = y + Σ b[i] * k[i]
    let mut y_new = y.to_vec();
    let mut err_raw = vec![0.0; n];
    for i in 0..8 {
        for d in 0..n {
            y_new[d] += tab.b[i] * sc.k[i][d];
            err_raw[d] += tab.bhat[i] * sc.k[i][d];
        }
    }
    
    ode.clip(&mut y_new);
    
    // Error norm (RMS)
    let mut err_sq = 0.0;
    for d in 0..n {
        let scale = cfg.atol + cfg.rtol * y_new[d].abs();
        err_sq += (err_raw[d] / scale).powi(2);
    }
    let err = (err_sq / n as f64).sqrt();
    
    let ok = y_new.iter().all(|v| v.is_finite());
    (y_new, err, ok, n_f)
}

// ═══════════════════════════════════════════════════════════════════
// Adaptive integration driver
// ═══════════════════════════════════════════════════════════════════

/// Result of adaptive integration.
pub(crate) struct AdaptiveResult {
    pub(crate) t_hist: Vec<f64>,
    pub(crate) y_hist: Vec<f64>,  // scalar history
    pub(crate) n_steps: usize,
    pub(crate) n_rejected: usize,
}

/// Integrate a scalar ODE from t0 to t_end with adaptive stepping.
pub(crate) fn integrate_scalar_adaptive<F: ScalarOde>(
    ode: &F, t0: f64, y0: f64, t_end: f64, cfg: &Rodas5PConfig,
) -> Result<AdaptiveResult, String> {
    let tab = rodas5p_tableau();
    let dir = if t_end > t0 { 1.0 } else { -1.0 };
    let mut t = t0;
    let mut y = ode.clip(y0);
    let mut h = dir * cfg.h_init.unwrap_or((t_end - t0).abs() * 1e-3);
    let mut prev_err = 1.0;
    let mut n_steps = 0usize;
    let mut n_rejected = 0usize;
    
    let mut t_hist = vec![t];
    let mut y_hist = vec![y];
    
    while (t_end - t) * dir > 1e-12 * (t_end - t0).abs() {
        if n_steps >= cfg.max_steps {
            return Err(format!("Max steps ({}) at t={:.6}", cfg.max_steps, t));
        }
        
        let remaining = (t_end - t).abs();
        let ht = h.abs().min(remaining).max(cfg.h_min);
        let h_signed = dir * ht;
        
        let (y_new, err, ok, _) = step_scalar_rodas5p(ode, t, y, h_signed, cfg, &tab);
        
        if !ok || err > 1.0 || !err.is_finite() {
            n_rejected += 1;
            let err_safe = if err.is_finite() { err.max(2.0) } else { 10.0 };
            h = pi_step_control(ht, err_safe, prev_err, cfg);
            if h < cfg.h_min * 1.001 {
                return Err(format!("h_min reached at t={:.6}", t));
            }
            continue;
        }
        
        t += h_signed;
        y = y_new;
        t_hist.push(t);
        y_hist.push(y);
        n_steps += 1;
        
        h = pi_step_control(ht, err, prev_err, cfg);
        prev_err = err;
    }
    
    Ok(AdaptiveResult { t_hist, y_hist, n_steps, n_rejected })
}

/// PI step-size controller (Gustafsson).
fn pi_step_control(h: f64, err: f64, prev_err: f64, cfg: &Rodas5PConfig) -> f64 {
    let order = 4.0_f64;
    let safe = 0.9;
    let fac_max = 5.0;
    let fac_min = 0.2;
    let fac = safe * err.powf(-0.7 / order) * prev_err.powf(0.4 / order);
    let fac = fac.clamp(fac_min, fac_max);
    (h * fac).max(cfg.h_min)
}

/// Result of small-vector adaptive integration.
pub(crate) struct SmallAdaptiveResult {
    pub(crate) t_hist: Vec<f64>,
    pub(crate) y_hist: Vec<Vec<f64>>,
    pub(crate) n_steps: usize,
    pub(crate) n_rejected: usize,
}

/// Integrate a small-vector ODE from t0 to t_end with adaptive stepping.
pub(crate) fn integrate_small_adaptive<F: SmallVectorOde>(
    ode: &F, t0: f64, y0: &[f64], t_end: f64, cfg: &Rodas5PConfig,
) -> Result<SmallAdaptiveResult, String> {
    let n = ode.dim();
    let tab = rodas5p_tableau();
    let mut sc = SmallRodas5PScratch::new(n);
    let dir = if t_end > t0 { 1.0 } else { -1.0 };
    let mut t = t0;
    let mut y = y0.to_vec();
    ode.clip(&mut y);
    let mut h = dir * cfg.h_init.unwrap_or((t_end - t0).abs() * 1e-3);
    let mut prev_err = 1.0;
    let mut n_steps = 0usize;
    let mut n_rejected = 0usize;
    
    let mut t_hist = vec![t];
    let mut y_hist = vec![y.clone()];
    
    while (t_end - t) * dir > 1e-12 * (t_end - t0).abs() {
        if n_steps >= cfg.max_steps {
            return Err(format!("Max steps ({}) at t={:.6}", cfg.max_steps, t));
        }
        let remaining = (t_end - t).abs();
        let ht = h.abs().min(remaining).max(cfg.h_min);
        let h_signed = dir * ht;
        
        let (y_new, err, ok, _) = step_small_rodas5p(ode, t, &y, h_signed, cfg, &tab, &mut sc);
        
        if !ok || err > 1.0 || !err.is_finite() {
            n_rejected += 1;
            let err_safe = if err.is_finite() { err.max(2.0) } else { 10.0 };
            h = pi_step_control(ht, err_safe, prev_err, cfg);
            if h < cfg.h_min * 1.001 {
                return Err(format!("h_min reached at t={:.6}", t));
            }
            continue;
        }
        
        t += h_signed;
        y = y_new;
        t_hist.push(t);
        y_hist.push(y.clone());
        n_steps += 1;
        
        h = pi_step_control(ht, err, prev_err, cfg);
        prev_err = err;
    }
    
    Ok(SmallAdaptiveResult { t_hist, y_hist, n_steps, n_rejected })
}

// ═══════════════════════════════════════════════════════════════════
// Small LU solver (N ≤ 16, no allocation)
// ═══════════════════════════════════════════════════════════════════

fn lu_factor_small(a: &mut [f64], piv: &mut [usize], n: usize) -> bool {
    for i in 0..n { piv[i] = i; }
    for k in 0..n {
        // Partial pivoting
        let mut max_val = a[k * n + k].abs();
        let mut max_row = k;
        for i in (k+1)..n {
            let v = a[i * n + k].abs();
            if v > max_val { max_val = v; max_row = i; }
        }
        if max_val < 1e-30 { return false; }
        if max_row != k {
            piv.swap(k, max_row);
            for j in 0..n { a.swap(k * n + j, max_row * n + j); }
        }
        let pivot = a[k * n + k];
        for i in (k+1)..n {
            a[i * n + k] /= pivot;
            for j in (k+1)..n {
                let lik = a[i * n + k];
                a[i * n + j] -= lik * a[k * n + j];
            }
        }
    }
    true
}

fn lu_solve_small(lu: &[f64], piv: &[usize], b: &mut [f64], n: usize) {
    // Apply permutation
    let mut tmp = [0.0_f64; 16];
    for i in 0..n { tmp[i] = b[piv[i]]; }
    b[..n].copy_from_slice(&tmp[..n]);
    // Forward substitution
    for i in 1..n {
        for j in 0..i {
            b[i] -= lu[i * n + j] * b[j];
        }
    }
    // Back substitution
    for i in (0..n).rev() {
        for j in (i+1)..n {
            b[i] -= lu[i * n + j] * b[j];
        }
        b[i] /= lu[i * n + i];
    }
}

// ═══════════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;
    
    /// Exponential decay: y' = -λy, exact: y = exp(-λt).
    struct ExpDecay { lambda: f64 }
    impl ScalarOde for ExpDecay {
        fn rhs(&self, _t: f64, y: f64) -> f64 { -self.lambda * y }
        fn jac(&self, _t: f64, _y: f64) -> f64 { -self.lambda }
    }
    
    #[test]
    fn test_exp_decay_order4() {
        let ode = ExpDecay { lambda: 100.0 };
        let cfg = Rodas5PConfig {
            rtol: 1e-12, atol: 1e-14,
            h_init: Some(0.001), h_min: 1e-10, max_steps: 100000,
            use_analytic_jacobian: true, use_ft_term: false,
            h_max: 100.0, f_safety: 0.9, f_min: 0.2, f_max: 5.0, beta: 0.04,
            use_blas_lu: false, use_block_diag: false,
            ell_max_gamma_hint: 0, ell_max_nu_hint: 0, ell_max_pol_hint: 0,
            include_pol_hint: false, use_sparse: false,
        };
        
        // Measure error at t=1 for different fixed step sizes
        let tab = rodas5p_tableau();
        let mut errors = Vec::new();
        let mut steps = Vec::new();
        
        for &n in &[10, 20, 40, 80] {
            let h = 1.0 / n as f64;
            let mut t = 0.0; let mut y = 1.0;
            for _ in 0..n {
                let (y_new, _, ok, _) = step_scalar_rodas5p(&ode, t, y, h, &cfg, &tab);
                assert!(ok);
                y = y_new; t += h;
            }
            let exact = (-100.0_f64).exp();
            let err = (y - exact).abs();
            errors.push(err);
            steps.push(n);
            eprintln!("  n={:4}: y={:.10e}, exact={:.10e}, err={:.4e}", n, y, exact, err);
        }
        
        // Check order ≥ 3 (expect 4)
        if errors.len() >= 2 && errors[0] > 1e-15 && errors[1] > 1e-15 {
            let order = (errors[0] / errors[1]).ln() / (steps[1] as f64 / steps[0] as f64).ln();
            eprintln!("  Estimated order: {:.1}", order);
            assert!(order > 3.0, "Order {} < 3", order);
        }
    }
    
    #[test]
    fn test_adaptive_exp_decay() {
        let ode = ExpDecay { lambda: 1000.0 };
        let cfg = Rodas5PConfig {
            rtol: 1e-8, atol: 1e-12,
            h_init: Some(1e-4), h_min: 1e-12, max_steps: 10000,
            use_analytic_jacobian: true, use_ft_term: false,
            h_max: 100.0, f_safety: 0.9, f_min: 0.2, f_max: 5.0, beta: 0.04,
            use_blas_lu: false, use_block_diag: false,
            ell_max_gamma_hint: 0, ell_max_nu_hint: 0, ell_max_pol_hint: 0,
            include_pol_hint: false, use_sparse: false,
        };
        
        let result = integrate_scalar_adaptive(&ode, 0.0, 1.0, 0.01, &cfg).unwrap();
        let exact = (-1000.0 * 0.01_f64).exp();
        let final_y = *result.y_hist.last().unwrap();
        let err = (final_y - exact).abs() / exact.abs().max(1e-30);
        
        eprintln!("  Stiff exp decay: y={:.6e}, exact={:.6e}, rel_err={:.2e}, steps={}, rejected={}",
                  final_y, exact, err, result.n_steps, result.n_rejected);
        assert!(err < 1e-4, "Error {} too large", err);
    }
    
    /// 2×2 test: coupled decay.
    struct CoupledDecay;
    impl SmallVectorOde for CoupledDecay {
        fn dim(&self) -> usize { 2 }
        fn rhs(&self, _t: f64, y: &[f64], out: &mut [f64]) {
            out[0] = -100.0 * y[0] + y[1];
            out[1] = y[0] - 100.0 * y[1];
        }
        fn jac(&self, _t: f64, _y: &[f64], out: &mut [f64]) {
            out[0] = -100.0; out[1] = 1.0;
            out[2] = 1.0;    out[3] = -100.0;
        }
    }
    
    #[test]
    fn test_2x2_coupled_decay() {
        let ode = CoupledDecay;
        let cfg = Rodas5PConfig {
            rtol: 1e-8, atol: 1e-12,
            h_init: Some(0.001), h_min: 1e-10, max_steps: 10000,
            use_analytic_jacobian: true, use_ft_term: false,
            h_max: 100.0, f_safety: 0.9, f_min: 0.2, f_max: 5.0, beta: 0.04,
            use_blas_lu: false, use_block_diag: false,
            ell_max_gamma_hint: 0, ell_max_nu_hint: 0, ell_max_pol_hint: 0,
            include_pol_hint: false, use_sparse: false,
        };
        let tab = rodas5p_tableau();
        let mut sc = SmallRodas5PScratch::new(2);
        
        let y0 = vec![1.0, 0.0];
        let h = 0.001;
        let mut t = 0.0;
        let mut y = y0.clone();
        for _ in 0..100 {
            let (y_new, err, ok, _) = step_small_rodas5p(&ode, t, &y, h, &cfg, &tab, &mut sc);
            assert!(ok, "Step failed at t={}", t);
            y = y_new; t += h;
        }
        // At t=0.1, both components should be near 0 (λ=99,101)
        eprintln!("  2×2 at t=0.1: y=[{:.6e}, {:.6e}]", y[0], y[1]);
        assert!(y[0].abs() < 1e-3, "y[0]={} too large", y[0]);
    }
}
