// BDF-2 solver for linear ODE systems y' = A(τ)y.
//
// Designed for the FLRW Boltzmann hierarchy where:
//   - A(τ) is piecewise-linear interpolated from a precomputed profile
//   - The system transitions from stiff (tight-coupling) to oscillatory (free-streaming)
//   - Rosenbrock methods fail on the oscillatory regime (imaginary eigenvalues)
//
// BDF-2 advantages:
//   - A(90°)-stable: covers the imaginary axis (oscillatory modes)
//   - For linear systems: single LU solve per step (no Newton iteration)
//   - Naturally differentiable via implicit function theorem
//
// BDF-2 formula:
//   y_{n+1} = (4/3)y_n - (1/3)y_{n-1} + (2h/3)A_{n+1}y_{n+1}
//   ⟹ (I - 2h/3 · A_{n+1}) y_{n+1} = (4/3)y_n - (1/3)y_{n-1}
//
// First step uses BDF-1 (backward Euler):
//   (I - h · A₁) y₁ = y₀

// Block-diagonal LU for BDF-2 will be added in a follow-up optimization.
// For now, use dense LU which is correct for all system sizes.

/// Configuration for the BDF-2 linear solver.
#[derive(Clone, Debug)]
pub(crate) struct Bdf2Config {
    pub(crate) rtol: f64,
    pub(crate) atol: f64,
    pub(crate) h_init: Option<f64>,
    pub(crate) h_min: f64,
    pub(crate) h_max: f64,
    pub(crate) max_steps: usize,
    /// Use block-diagonal LU for ν/CDM decoupling.
    pub(crate) use_block_diag: bool,
    /// Hints for block structure.
    pub(crate) ell_max_gamma_hint: usize,
    pub(crate) ell_max_nu_hint: usize,
}

impl Default for Bdf2Config {
    fn default() -> Self {
        Self {
            rtol: 1e-6, atol: 1e-9,
            h_init: None, h_min: 1e-14, h_max: 200.0,
            max_steps: 1_000_000,
            use_block_diag: true,
            ell_max_gamma_hint: 15,
            ell_max_nu_hint: 8,
        }
    }
}

/// Interpolate A(τ) from the profile at a given τ value.
/// Returns the interpolated matrix in row-major flat format.
fn interpolate_matrix(
    tau_profile: &[f64], mats_flat: &[f64], n: usize, tau: f64,
    hint: &mut usize,
) -> Vec<f64> {
    let np = tau_profile.len();
    let stride = n * n;

    // Find bracket [i, i+1] such that tau_profile[i] <= tau <= tau_profile[i+1]
    // Use hint for O(1) amortized lookup
    let mut lo = *hint;
    if lo >= np - 1 { lo = np - 2; }
    while lo > 0 && tau_profile[lo] > tau { lo -= 1; }
    while lo < np - 2 && tau_profile[lo + 1] < tau { lo += 1; }
    *hint = lo;

    if lo >= np - 1 {
        return mats_flat[(np - 1) * stride..np * stride].to_vec();
    }

    let t0 = tau_profile[lo];
    let t1 = tau_profile[lo + 1];
    let dt = t1 - t0;
    if dt.abs() < 1e-30 {
        return mats_flat[lo * stride..(lo + 1) * stride].to_vec();
    }
    let w = ((tau - t0) / dt).clamp(0.0, 1.0);

    let mut result = vec![0.0; stride];
    let base0 = lo * stride;
    let base1 = (lo + 1) * stride;
    for i in 0..stride {
        result[i] = mats_flat[base0 + i] * (1.0 - w) + mats_flat[base1 + i] * w;
    }
    result
}

/// Solve (I - γ·A) x = rhs via dense LU or block-diagonal LU.
fn solve_implicit_system(
    a_mat: &[f64], n: usize, gamma: f64, rhs: &mut Vec<f64>,
    use_block_diag: bool, lg: usize, ln: usize,
) {
    // Build M = I - γ·A
    let mut m = vec![0.0_f64; n * n];
    for i in 0..n {
        for j in 0..n {
            m[i * n + j] = -gamma * a_mat[i * n + j];
        }
        m[i * n + i] += 1.0;
    }

    if use_block_diag && lg > 0 && ln > 0 {
        // TODO: block-diagonal LU optimization (follow-up)
        dense_lu_solve(&mut m, rhs, n);
    } else {
        dense_lu_solve(&mut m, rhs, n);
    }
}

/// Dense LU decomposition and solve (fallback).
fn dense_lu_solve(m: &mut [f64], rhs: &mut [f64], n: usize) {
    // Partial pivoting LU
    let mut perm: Vec<usize> = (0..n).collect();
    for k in 0..n {
        // Find pivot
        let mut max_val = m[perm[k] * n + k].abs();
        let mut max_row = k;
        for i in (k + 1)..n {
            let v = m[perm[i] * n + k].abs();
            if v > max_val { max_val = v; max_row = i; }
        }
        perm.swap(k, max_row);

        let pivot = m[perm[k] * n + k];
        if pivot.abs() < 1e-30 { continue; }

        for i in (k + 1)..n {
            let factor = m[perm[i] * n + k] / pivot;
            m[perm[i] * n + k] = factor;
            for j in (k + 1)..n {
                let mk = m[perm[k] * n + j];
                m[perm[i] * n + j] -= factor * mk;
            }
        }
    }

    // Forward substitution (Ly = Pb)
    let mut y = vec![0.0; n];
    for i in 0..n { y[i] = rhs[perm[i]]; }
    for i in 1..n {
        for j in 0..i {
            y[i] -= m[perm[i] * n + j] * y[j];
        }
    }

    // Backward substitution (Ux = y)
    for i in (0..n).rev() {
        for j in (i + 1)..n {
            y[i] -= m[perm[i] * n + j] * y[j];
        }
        let d = m[perm[i] * n + i];
        if d.abs() > 1e-30 { y[i] /= d; }
    }

    rhs.copy_from_slice(&y);
}

/// Weighted RMS error norm for step control.
fn error_norm(err: &[f64], y: &[f64], rtol: f64, atol: f64) -> f64 {
    let n = err.len();
    let mut sum = 0.0;
    for i in 0..n {
        let sc = atol + rtol * y[i].abs();
        sum += (err[i] / sc).powi(2);
    }
    (sum / n as f64).sqrt()
}

/// BDF-2 integrator for linear ODE y' = A(τ)y.
///
/// Returns snapshots at the requested `tau_eval` points.
pub(crate) fn integrate_linear_bdf2(
    tau_profile: &[f64],
    mats_flat: &[f64],
    n_state: usize,
    y0: &[f64],
    tau_eval: &[f64],
    cfg: &Bdf2Config,
) -> Result<(Vec<Vec<f64>>, usize, usize), String> {
    let n = n_state;
    let n_eval = tau_eval.len();
    if n_eval == 0 {
        return Ok((Vec::new(), 0, 0));
    }

    let tau_start = tau_eval[0];
    let tau_end = *tau_eval.last().unwrap();

    // Initial step size
    let mut h = cfg.h_init.unwrap_or_else(|| {
        let dt = (tau_end - tau_start) / 1000.0;
        dt.max(cfg.h_min).min(cfg.h_max)
    });

    let lg = cfg.ell_max_gamma_hint;
    let ln = cfg.ell_max_nu_hint;

    // State history
    let mut y_cur = y0.to_vec();
    let mut y_prev: Option<Vec<f64>> = None;  // for BDF-2 (need 2 history points)
    let mut tau_cur = tau_start;

    // Output
    let mut snapshots: Vec<Vec<f64>> = Vec::with_capacity(n_eval);
    let mut eval_idx = 0_usize;

    // Record initial point if it matches first eval
    while eval_idx < n_eval && (tau_eval[eval_idx] - tau_cur).abs() < 1e-12 {
        snapshots.push(y_cur.clone());
        eval_idx += 1;
    }

    let mut hint = 0_usize;
    let mut n_steps = 0_usize;
    let mut n_reject = 0_usize;

    while tau_cur < tau_end - 1e-12 && eval_idx < n_eval && n_steps < cfg.max_steps {
        let h_try = h.min(tau_end - tau_cur).max(cfg.h_min);
        let tau_next = tau_cur + h_try;

        // Interpolate A at τ_{n+1}
        let a_next = interpolate_matrix(tau_profile, mats_flat, n, tau_next, &mut hint);

        if let Some(ref yp) = y_prev {
            // ═══ BDF-2 step ═══
            // (I - 2h/3 · A_{n+1}) y_{n+1} = (4/3)y_n - (1/3)y_{n-1}
            let gamma = 2.0 * h_try / 3.0;
            let mut rhs = vec![0.0; n];
            for i in 0..n {
                rhs[i] = (4.0 / 3.0) * y_cur[i] - (1.0 / 3.0) * yp[i];
            }
            solve_implicit_system(&a_next, n, gamma, &mut rhs, cfg.use_block_diag, lg, ln);
            let y_bdf2 = rhs;

            // ═══ Error estimate: compare with BDF-1 (backward Euler) ═══
            // BDF-1: (I - h · A_{n+1}) ŷ = y_n
            let mut rhs1 = y_cur.clone();
            solve_implicit_system(&a_next, n, h_try, &mut rhs1, cfg.use_block_diag, lg, ln);
            let y_bdf1 = rhs1;

            // Error = difference between BDF-2 and BDF-1
            let mut err_vec = vec![0.0; n];
            for i in 0..n { err_vec[i] = y_bdf2[i] - y_bdf1[i]; }
            let err_norm = error_norm(&err_vec, &y_bdf2, cfg.rtol, cfg.atol);

            if err_norm > 1.0 {
                // Reject step, reduce h
                n_reject += 1;
                h = (h_try * (0.9 / err_norm.sqrt()).max(0.2)).max(cfg.h_min);
                continue;
            }

            // Accept step
            y_prev = Some(y_cur.clone());
            y_cur = y_bdf2;
            tau_cur = tau_next;

            // Adjust step size
            let factor = (0.9 / err_norm.sqrt()).min(2.0).max(0.5);
            h = (h_try * factor).max(cfg.h_min).min(cfg.h_max);

        } else {
            // ═══ First step: BDF-1 (backward Euler) ═══
            // (I - h · A₁) y₁ = y₀
            let mut rhs = y_cur.clone();
            solve_implicit_system(&a_next, n, h_try, &mut rhs, cfg.use_block_diag, lg, ln);

            y_prev = Some(y_cur.clone());
            y_cur = rhs;
            tau_cur = tau_next;
        }

        n_steps += 1;

        // Record snapshots at eval points (linear interpolation between steps)
        while eval_idx < n_eval && tau_eval[eval_idx] <= tau_cur + 1e-12 {
            if (tau_eval[eval_idx] - tau_cur).abs() < 1e-12 {
                snapshots.push(y_cur.clone());
            } else if let Some(ref yp) = y_prev {
                // Linear interpolation between y_prev and y_cur
                let t_prev = tau_cur - h.max(cfg.h_min);
                let w = if (tau_cur - t_prev).abs() > 1e-20 {
                    ((tau_eval[eval_idx] - t_prev) / (tau_cur - t_prev)).clamp(0.0, 1.0)
                } else { 1.0 };
                let mut y_interp = vec![0.0; n];
                for i in 0..n {
                    y_interp[i] = yp[i] * (1.0 - w) + y_cur[i] * w;
                }
                snapshots.push(y_interp);
            } else {
                snapshots.push(y_cur.clone());
            }
            eval_idx += 1;
        }
    }

    // Fill remaining eval points with last state
    while eval_idx < n_eval {
        snapshots.push(y_cur.clone());
        eval_idx += 1;
    }

    Ok((snapshots, n_steps, n_reject))
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Test BDF-2 on simple exponential decay y' = -αy → y(t) = y₀ e^{-αt}
    #[test]
    fn test_bdf2_exponential_decay() {
        let n = 1;
        let alpha = 2.0;
        // A = [-α]
        let a_mat = vec![-alpha];
        let tau_profile = vec![0.0, 10.0];
        let mats_flat = vec![-alpha, -alpha]; // constant matrix

        let y0 = vec![1.0];
        let tau_eval: Vec<f64> = (0..=100).map(|i| i as f64 * 0.1).collect();

        let cfg = Bdf2Config {
            rtol: 1e-8, atol: 1e-10,
            h_init: Some(0.01), h_min: 1e-10, h_max: 1.0,
            max_steps: 100000, use_block_diag: false,
            ell_max_gamma_hint: 0, ell_max_nu_hint: 0,
        };

        let (snaps, n_steps, n_reject) = integrate_linear_bdf2(
            &tau_profile, &mats_flat, n, &y0, &tau_eval, &cfg,
        ).unwrap();

        eprintln!("  BDF2 exp decay: {} steps, {} rejects", n_steps, n_reject);

        // Check a few points
        for &i in &[10, 50, 100] {
            if i >= snaps.len() { continue; }
            let t = tau_eval[i];
            let exact = (-alpha * t).exp();
            let computed = snaps[i][0];
            let rel_err = (computed - exact).abs() / exact.max(1e-30);
            eprintln!("  t={:.1}: exact={:.6e}, BDF2={:.6e}, err={:.2e}", t, exact, computed, rel_err);
            assert!(rel_err < 1e-3, "BDF2 error {:.2e} at t={:.1}", rel_err, t);
        }
    }

    /// Test BDF-2 on oscillatory system y' = [[0, ω], [-ω, 0]] y
    /// Solution: y₁ = cos(ωt), y₂ = sin(ωt)
    #[test]
    fn test_bdf2_oscillator() {
        let n = 2;
        let omega = 1.0;
        // A = [[0, ω], [-ω, 0]]
        let a_mat = vec![0.0, omega, -omega, 0.0];
        let tau_profile = vec![0.0, 100.0];
        let mut mats_flat = Vec::new();
        mats_flat.extend_from_slice(&a_mat);
        mats_flat.extend_from_slice(&a_mat);

        let y0 = vec![1.0, 0.0]; // cos(0), sin(0)
        let tau_eval: Vec<f64> = (0..=1000).map(|i| i as f64 * 0.01).collect();

        let cfg = Bdf2Config {
            rtol: 1e-6, atol: 1e-9,
            h_init: Some(0.001), h_min: 1e-10, h_max: 0.5,
            max_steps: 100000, use_block_diag: false,
            ell_max_gamma_hint: 0, ell_max_nu_hint: 0,
        };

        let (snaps, n_steps, n_reject) = integrate_linear_bdf2(
            &tau_profile, &mats_flat, n, &y0, &tau_eval, &cfg,
        ).unwrap();

        eprintln!("  BDF2 oscillator: {} steps, {} rejects", n_steps, n_reject);

        // Check at t = π (half period)
        let i_pi = (std::f64::consts::PI / 0.01) as usize;
        if i_pi < snaps.len() {
            let y1 = snaps[i_pi][0];
            let y2 = snaps[i_pi][1];
            // cos(π) = -1, sin(π) = 0
            eprintln!("  t=π: y₁={:.4} (expect -1), y₂={:.4} (expect 0)", y1, y2);
            assert!((y1 - (-1.0)).abs() < 0.1, "cos(π) = {:.4}", y1);
            assert!(y2.abs() < 0.1, "sin(π) = {:.4}", y2);
        }

        // Check amplitude preservation at t = 2π
        let i_2pi = (2.0 * std::f64::consts::PI / 0.01) as usize;
        if i_2pi < snaps.len() {
            let amp = (snaps[i_2pi][0].powi(2) + snaps[i_2pi][1].powi(2)).sqrt();
            eprintln!("  t=2π: amplitude = {:.4} (expect 1)", amp);
            // BDF-2 is L-stable → slight amplitude damping expected
            assert!(amp > 0.8 && amp < 1.1, "Amplitude = {:.4}", amp);
        }
    }

    /// Test BDF-2 on stiff + oscillatory combined system (Boltzmann-like).
    #[test]
    fn test_bdf2_stiff_oscillatory() {
        // System with one decaying mode (-100) and one oscillatory mode (i×10)
        let n = 3;
        // A = [[-100, 0, 0], [0, 0, 10], [0, -10, 0]]
        let a_mat = vec![
            -100.0,  0.0,  0.0,
              0.0,  0.0, 10.0,
              0.0, -10.0,  0.0,
        ];
        let tau_profile = vec![0.0, 10.0];
        let mut mats_flat = Vec::new();
        mats_flat.extend_from_slice(&a_mat);
        mats_flat.extend_from_slice(&a_mat);

        let y0 = vec![1.0, 1.0, 0.0];
        let tau_eval: Vec<f64> = (0..=1000).map(|i| i as f64 * 0.01).collect();

        let cfg = Bdf2Config {
            rtol: 1e-6, atol: 1e-9,
            h_init: Some(1e-4), h_min: 1e-10, h_max: 0.5,
            max_steps: 100000, use_block_diag: false,
            ell_max_gamma_hint: 0, ell_max_nu_hint: 0,
        };

        let (snaps, n_steps, n_reject) = integrate_linear_bdf2(
            &tau_profile, &mats_flat, n, &y0, &tau_eval, &cfg,
        ).unwrap();

        eprintln!("  BDF2 stiff+osc: {} steps, {} rejects", n_steps, n_reject);

        // At t=1.0 (100 time steps): y₁ should be ~0 (decayed), y₂²+y₃² ≈ 1
        let i100 = 100;
        if i100 < snaps.len() {
            let y1 = snaps[i100][0];
            let osc_amp = (snaps[i100][1].powi(2) + snaps[i100][2].powi(2)).sqrt();
            eprintln!("  t=1: y₁={:.2e} (expect ~0), osc_amp={:.3} (expect ~1)", y1, osc_amp);
            assert!(y1.abs() < 1e-10, "Stiff mode not decayed: {:.2e}", y1);
            assert!(osc_amp > 0.5, "Oscillatory mode died: {:.3}", osc_amp);
        }
    }
}
