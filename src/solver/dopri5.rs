// CL-08: Dormand-Prince 5(4) explicit stepper for linear systems y' = A(η)y.
//
// Used for the NON-STIFF regime (after recombination, κ̇ ≈ 0).
// Rodas5P handles the STIFF regime (during recombination).
// LSODA-like switching criterion: κ̇/aH < threshold → switch to Dopri5.
//
// Differentiability: Dopri5 is fully differentiable via "discretize-then-optimize"
// (Kidger 2021, Diffrax). Both forward-mode (jvp) and reverse-mode (vjp) AD work
// through the step internals. The step-size controller introduces branch points
// at rejection events, handled by checkpointed AD.

/// Dormand-Prince 5(4) Butcher tableau constants.
pub(crate) struct Dopri5Tableau {
    pub(crate) c: [f64; 7],
    pub(crate) a: [[f64; 7]; 7],
    pub(crate) b: [f64; 7],      // 5th order weights
    pub(crate) bhat: [f64; 7],   // 4th order weights (for error)
}

pub(crate) fn dopri5_tableau() -> Dopri5Tableau {
    Dopri5Tableau {
        c: [0.0, 1.0/5.0, 3.0/10.0, 4.0/5.0, 8.0/9.0, 1.0, 1.0],
        a: [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [1.0/5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [3.0/40.0, 9.0/40.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [44.0/45.0, -56.0/15.0, 32.0/9.0, 0.0, 0.0, 0.0, 0.0],
            [19372.0/6561.0, -25360.0/2187.0, 64448.0/6561.0, -212.0/729.0, 0.0, 0.0, 0.0],
            [9017.0/3168.0, -355.0/33.0, 46732.0/5247.0, 49.0/176.0, -5103.0/18656.0, 0.0, 0.0],
            [35.0/384.0, 0.0, 500.0/1113.0, 125.0/192.0, -2187.0/6784.0, 11.0/84.0, 0.0],
        ],
        b: [35.0/384.0, 0.0, 500.0/1113.0, 125.0/192.0, -2187.0/6784.0, 11.0/84.0, 0.0],
        bhat: [5179.0/57600.0, 0.0, 7571.0/16695.0, 393.0/640.0, -92097.0/339200.0, 187.0/2100.0, 1.0/40.0],
    }
}

/// One step of Dopri5 for a linear system y' = A·y.
///
/// Returns (y_new, err_norm, n_f_eval).
/// The matrix A is passed as a flat n×n array (row-major).
/// y has n_state components (no time component — caller manages time).
pub(crate) fn step_dopri5_linear(
    y: &[f64],
    a_mat: &[f64],
    n_state: usize,
    h: f64,
    tab: &Dopri5Tableau,
    rtol: f64,
    atol: f64,
) -> (Vec<f64>, f64, usize) {
    let n = n_state;
    // k_i = A · y_stage (for linear system, f(t,y) = A·y with A cached)
    let mut ks = vec![vec![0.0; n]; 7];

    // k1 = A · y
    matvec(a_mat, y, &mut ks[0], n);

    for s in 1..7 {
        // y_stage = y + h * sum_{j<s} a[s][j] * k_j
        let mut y_stage = y.to_vec();
        for j in 0..s {
            let asj = tab.a[s][j];
            if asj == 0.0 { continue; }
            for m in 0..n {
                y_stage[m] += h * asj * ks[j][m];
            }
        }
        matvec(a_mat, &y_stage, &mut ks[s], n);
    }

    // y_new (5th order) and error estimate
    let mut y_new = y.to_vec();
    let mut err_est = vec![0.0; n];
    for s in 0..7 {
        for m in 0..n {
            y_new[m] += h * tab.b[s] * ks[s][m];
            err_est[m] += h * (tab.b[s] - tab.bhat[s]) * ks[s][m];
        }
    }

    // Error norm (same as Rodas5P)
    let mut worst = 0.0_f64;
    for i in 0..n {
        let sc = atol + rtol * y_new[i].abs();
        worst = worst.max((err_est[i] / sc).abs());
    }

    (y_new, worst, 7)
}

/// Simple matrix-vector multiply: out = A · x  (A is n×n row-major).
#[inline]
fn matvec(a: &[f64], x: &[f64], out: &mut [f64], n: usize) {
    for i in 0..n {
        let mut acc = 0.0;
        let row = i * n;
        for j in 0..n {
            acc += a[row + j] * x[j];
        }
        out[i] = acc;
    }
}

/// Adaptive step-size controller for Dopri5.
/// Returns new step size.
#[inline]
pub(crate) fn dopri5_new_h(h: f64, err: f64, h_min: f64, h_max: f64) -> f64 {
    let safety = 0.9;
    let fac_min = 0.2;
    let fac_max = 5.0;
    if err <= 1e-30 {
        return (h * fac_max).min(h_max);
    }
    let fac = safety * err.powf(-1.0 / 5.0);
    let fac = fac.max(fac_min).min(fac_max);
    (h * fac).max(h_min).min(h_max)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dopri5_exponential_decay() {
        let n = 1_usize;
        let a_mat = vec![-1.0_f64];
        let y0 = vec![1.0_f64];
        let tab = dopri5_tableau();
        let t_end = 2.0_f64;
        let mut y = y0.clone();
        let mut t = 0.0_f64;
        let mut h = 0.01_f64;
        let mut steps = 0_u32;
        while t < t_end - 1e-14 {
            let h_try = h.min(t_end - t);
            let (y_new, err, _) = step_dopri5_linear(&y, &a_mat, n, h_try, &tab, 1e-8, 1e-10);
            if err > 1.0 {
                h = dopri5_new_h(h_try, err, 1e-10, 1.0);
                continue;
            }
            y = y_new;
            t += h_try;
            h = dopri5_new_h(h_try, err, 1e-10, 1.0);
            steps += 1;
        }
        let exact = (-t_end).exp();
        let rel_err = (y[0] - exact).abs() / exact;
        assert!(rel_err < 1e-6, "Dopri5 exp decay: rel_err = {:.4e}, steps = {}", rel_err, steps);
    }

    #[test]
    fn test_dopri5_oscillator() {
        let n = 2_usize;
        let a_mat = vec![0.0_f64, 1.0, -1.0, 0.0];
        let y0 = vec![1.0_f64, 0.0];
        let tab = dopri5_tableau();
        let t_end = 6.283185307_f64;
        let mut y = y0.clone();
        let mut t = 0.0_f64;
        let mut h = 0.1_f64;
        while t < t_end - 1e-14 {
            let h_try = h.min(t_end - t);
            let (y_new, err, _) = step_dopri5_linear(&y, &a_mat, n, h_try, &tab, 1e-10, 1e-12);
            if err > 1.0 {
                h = dopri5_new_h(h_try, err, 1e-10, 1.0);
                continue;
            }
            y = y_new;
            t += h_try;
            h = dopri5_new_h(h_try, err, 1e-10, 1.0);
        }
        assert!((y[0] - 1.0).abs() < 1e-8, "cos(2π) = {:.10}", y[0]);
        assert!(y[1].abs() < 1e-8, "sin(2π) = {:.10e}", y[1]);
    }
}
